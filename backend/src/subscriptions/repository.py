"""Subscription repositories with tenant-aware data access."""
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal

from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.orm import selectinload

from src.shared.repository import BaseRepository, UserScopedRepository
from src.subscriptions.models import (
    Subscription, SubscriptionInvoice, SubscriptionEvent, 
    PaymentMethod, SubscriptionUsage, SubscriptionDiscount
)
from src.subscriptions.schemas import (
    SubscriptionResponse, SubscriptionUpdate,
    SubscriptionInvoiceResponse, SubscriptionEventResponse,
    PaymentMethodResponse, SubscriptionUsageResponse
)
from src.exceptions import NotFoundError, ValidationError, DatabaseError


class SubscriptionRepository(UserScopedRepository[Subscription, None, SubscriptionUpdate]):
    """Repository for subscription management."""
    
    def __init__(self):
        super().__init__(Subscription, user_field="user_id")
    
    async def get_by_stripe_subscription_id(self, stripe_subscription_id: str) -> Optional[Subscription]:
        """Get subscription by Stripe subscription ID."""
        return await self.get_by_field("stripe_subscription_id", stripe_subscription_id, 
                                     load_relationships=["invoices", "events"])
    
    async def get_by_stripe_customer_id(self, stripe_customer_id: str) -> Optional[Subscription]:
        """Get subscription by Stripe customer ID."""
        return await self.get_by_field("stripe_customer_id", stripe_customer_id,
                                     load_relationships=["invoices", "events"])
    
    async def get_active_subscription_for_user(self, user_id: str) -> Optional[Subscription]:
        """Get active subscription for user."""
        async with await self.get_session() as session:
            try:
                query = select(self.model).where(
                    and_(
                        self.model.user_id == user_id,
                        self.model.status.in_(["active", "trialing"])
                    )
                ).options(
                    selectinload(self.model.invoices),
                    selectinload(self.model.events)
                ).order_by(desc(self.model.created_at))
                
                result = await session.execute(query)
                return result.scalar_one_or_none()
                
            except Exception as e:
                raise DatabaseError(f"Failed to get active subscription: {str(e)}")
    
    async def get_subscriptions_by_status(self, status: str, limit: int = 100) -> List[Subscription]:
        """Get subscriptions by status."""
        return await self.get_multi(filters={"status": status}, limit=limit)
    
    async def get_expiring_trials(self, days_ahead: int = 7) -> List[Subscription]:
        """Get subscriptions with trials expiring within specified days."""
        async with await self.get_session() as session:
            try:
                from datetime import timedelta
                expiry_date = datetime.utcnow() + timedelta(days=days_ahead)
                
                query = select(self.model).where(
                    and_(
                        self.model.status == "trialing",
                        self.model.trial_end <= expiry_date,
                        self.model.trial_end > datetime.utcnow()
                    )
                ).order_by(asc(self.model.trial_end))
                
                result = await session.execute(query)
                return list(result.scalars().all())
                
            except Exception as e:
                raise DatabaseError(f"Failed to get expiring trials: {str(e)}")
    
    async def get_subscriptions_for_cancellation(self) -> List[Subscription]:
        """Get subscriptions marked for cancellation at period end."""
        return await self.get_multi(filters={"cancel_at_period_end": True})
    
    async def update_usage_data(self, subscription_id: str, usage_data: Dict[str, Any]) -> Optional[Subscription]:
        """Update subscription usage data."""
        return await self.update(subscription_id, SubscriptionUpdate(
            metadata={"usage_updated_at": datetime.utcnow().isoformat()}
        ), usage_data=usage_data)
    
    async def get_subscription_summary_for_user(self, user_id: str) -> Dict[str, Any]:
        """Get subscription summary for user."""
        async with await self.get_session() as session:
            try:
                # Get active subscription
                active_sub = await self.get_active_subscription_for_user(user_id)
                
                # Get subscription history count
                total_query = select(func.count(self.model.id)).where(self.model.user_id == user_id)
                total_result = await session.execute(total_query)
                total_subscriptions = total_result.scalar() or 0
                
                # Calculate total spent (from invoices)
                if active_sub:
                    invoice_query = select(func.sum(SubscriptionInvoice.amount_paid)).where(
                        SubscriptionInvoice.user_id == user_id
                    )
                    invoice_result = await session.execute(invoice_query)
                    total_spent = invoice_result.scalar() or Decimal('0.00')
                else:
                    total_spent = Decimal('0.00')
                
                return {
                    "user_id": user_id,
                    "has_active_subscription": active_sub is not None,
                    "current_plan": active_sub.plan if active_sub else "free",
                    "current_status": active_sub.status if active_sub else "none",
                    "trial_end": active_sub.trial_end if active_sub and active_sub.trial_end else None,
                    "current_period_end": active_sub.current_period_end if active_sub else None,
                    "cancel_at_period_end": active_sub.cancel_at_period_end if active_sub else False,
                    "total_subscriptions": total_subscriptions,
                    "total_spent": total_spent,
                    "usage_data": active_sub.usage_data if active_sub else {},
                    "plan_limits": active_sub.plan_limits if active_sub else {}
                }
                
            except Exception as e:
                raise DatabaseError(f"Failed to get subscription summary: {str(e)}")


class SubscriptionInvoiceRepository(UserScopedRepository[SubscriptionInvoice, None, None]):
    """Repository for subscription invoice management."""
    
    def __init__(self):
        super().__init__(SubscriptionInvoice, user_field="user_id")
    
    async def get_by_stripe_invoice_id(self, stripe_invoice_id: str) -> Optional[SubscriptionInvoice]:
        """Get invoice by Stripe invoice ID."""
        return await self.get_by_field("stripe_invoice_id", stripe_invoice_id)
    
    async def get_invoices_for_subscription(
        self, 
        subscription_id: str, 
        limit: int = 50
    ) -> List[SubscriptionInvoice]:
        """Get invoices for a subscription."""
        return await self.get_multi(
            filters={"subscription_id": subscription_id},
            order_by="-created_at",
            limit=limit
        )
    
    async def get_unpaid_invoices_for_user(self, user_id: str) -> List[SubscriptionInvoice]:
        """Get unpaid invoices for user."""
        return await self.get_multi_for_user(
            user_id=user_id,
            filters={"status": "open"},
            order_by="-due_date"
        )
    
    async def get_overdue_invoices(self, days_overdue: int = 0) -> List[SubscriptionInvoice]:
        """Get overdue invoices."""
        async with await self.get_session() as session:
            try:
                from datetime import timedelta
                overdue_date = datetime.utcnow() - timedelta(days=days_overdue)
                
                query = select(self.model).where(
                    and_(
                        self.model.status == "open",
                        self.model.due_date < overdue_date
                    )
                ).order_by(asc(self.model.due_date))
                
                result = await session.execute(query)
                return list(result.scalars().all())
                
            except Exception as e:
                raise DatabaseError(f"Failed to get overdue invoices: {str(e)}")
    
    async def get_billing_history_for_user(
        self, 
        user_id: str, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[SubscriptionInvoice]:
        """Get billing history for user with date filtering."""
        filters = {}
        if start_date:
            filters["created_at"] = {"gte": start_date}
        if end_date:
            if "created_at" in filters:
                filters["created_at"]["lte"] = end_date
            else:
                filters["created_at"] = {"lte": end_date}
        
        return await self.get_multi_for_user(
            user_id=user_id,
            filters=filters,
            order_by="-created_at",
            limit=limit
        )
    
    async def get_revenue_summary(
        self, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get revenue summary for date range."""
        async with await self.get_session() as session:
            try:
                query = select(
                    func.count(self.model.id).label("total_invoices"),
                    func.sum(self.model.amount_due).label("total_due"),
                    func.sum(self.model.amount_paid).label("total_paid"),
                    func.sum(self.model.amount_remaining).label("total_remaining")
                )
                
                if start_date:
                    query = query.where(self.model.created_at >= start_date)
                if end_date:
                    query = query.where(self.model.created_at <= end_date)
                
                result = await session.execute(query)
                row = result.first()
                
                return {
                    "total_invoices": row.total_invoices or 0,
                    "total_due": row.total_due or Decimal('0.00'),
                    "total_paid": row.total_paid or Decimal('0.00'),
                    "total_remaining": row.total_remaining or Decimal('0.00'),
                    "collection_rate": float((row.total_paid or 0) / (row.total_due or 1)) * 100
                }
                
            except Exception as e:
                raise DatabaseError(f"Failed to get revenue summary: {str(e)}")


class SubscriptionEventRepository(BaseRepository[SubscriptionEvent, None, None]):
    """Repository for subscription event management."""
    
    def __init__(self):
        super().__init__(SubscriptionEvent)
    
    async def get_by_stripe_event_id(self, stripe_event_id: str) -> Optional[SubscriptionEvent]:
        """Get event by Stripe event ID."""
        return await self.get_by_field("stripe_event_id", stripe_event_id)
    
    async def get_events_for_subscription(
        self, 
        subscription_id: str, 
        limit: int = 100
    ) -> List[SubscriptionEvent]:
        """Get events for a subscription."""
        return await self.get_multi(
            filters={"subscription_id": subscription_id},
            order_by="-created_at",
            limit=limit
        )
    
    async def get_unprocessed_events(self, limit: int = 100) -> List[SubscriptionEvent]:
        """Get unprocessed events."""
        return await self.get_multi(
            filters={"processed": False},
            order_by="created_at",
            limit=limit
        )
    
    async def mark_event_processed(self, event_id: str, error_message: Optional[str] = None) -> bool:
        """Mark event as processed."""
        async with await self.get_session() as session:
            try:
                from sqlalchemy import update
                
                update_data = {
                    "processed": True,
                    "processed_at": datetime.utcnow()
                }
                
                if error_message:
                    update_data["error_message"] = error_message
                
                query = update(self.model).where(self.model.id == event_id).values(**update_data)
                result = await session.execute(query)
                await session.commit()
                
                return result.rowcount > 0
                
            except Exception as e:
                raise DatabaseError(f"Failed to mark event as processed: {str(e)}")
    
    async def get_events_by_type(self, event_type: str, limit: int = 100) -> List[SubscriptionEvent]:
        """Get events by type."""
        return await self.get_multi(
            filters={"event_type": event_type},
            order_by="-created_at",
            limit=limit
        )


class PaymentMethodRepository(UserScopedRepository[PaymentMethod, None, None]):
    """Repository for payment method management."""
    
    def __init__(self):
        super().__init__(PaymentMethod, user_field="user_id")
    
    async def get_by_stripe_payment_method_id(self, stripe_payment_method_id: str) -> Optional[PaymentMethod]:
        """Get payment method by Stripe payment method ID."""
        return await self.get_by_field("stripe_payment_method_id", stripe_payment_method_id)
    
    async def get_active_payment_methods_for_user(self, user_id: str) -> List[PaymentMethod]:
        """Get active payment methods for user."""
        return await self.get_multi_for_user(
            user_id=user_id,
            filters={"is_active": True},
            order_by="-is_default"
        )
    
    async def get_default_payment_method_for_user(self, user_id: str) -> Optional[PaymentMethod]:
        """Get default payment method for user."""
        async with await self.get_session() as session:
            try:
                query = select(self.model).where(
                    and_(
                        self.model.user_id == user_id,
                        self.model.is_default == True,
                        self.model.is_active == True
                    )
                )
                
                result = await session.execute(query)
                return result.scalar_one_or_none()
                
            except Exception as e:
                raise DatabaseError(f"Failed to get default payment method: {str(e)}")
    
    async def set_default_payment_method(self, user_id: str, payment_method_id: str) -> bool:
        """Set payment method as default for user."""
        async with await self.get_session() as session:
            try:
                from sqlalchemy import update
                
                # First, unset all other payment methods as default
                unset_query = update(self.model).where(
                    and_(
                        self.model.user_id == user_id,
                        self.model.id != payment_method_id
                    )
                ).values(is_default=False)
                
                await session.execute(unset_query)
                
                # Then set the specified payment method as default
                set_query = update(self.model).where(
                    and_(
                        self.model.user_id == user_id,
                        self.model.id == payment_method_id
                    )
                ).values(is_default=True)
                
                result = await session.execute(set_query)
                await session.commit()
                
                return result.rowcount > 0
                
            except Exception as e:
                await session.rollback()
                raise DatabaseError(f"Failed to set default payment method: {str(e)}")


class SubscriptionUsageRepository(UserScopedRepository[SubscriptionUsage, None, None]):
    """Repository for subscription usage tracking."""
    
    def __init__(self):
        super().__init__(SubscriptionUsage, user_field="user_id")
    
    async def get_current_usage_for_subscription(self, subscription_id: str) -> Optional[SubscriptionUsage]:
        """Get current period usage for subscription."""
        async with await self.get_session() as session:
            try:
                current_time = datetime.utcnow()
                
                query = select(self.model).where(
                    and_(
                        self.model.subscription_id == subscription_id,
                        self.model.period_start <= current_time,
                        self.model.period_end >= current_time
                    )
                )
                
                result = await session.execute(query)
                return result.scalar_one_or_none()
                
            except Exception as e:
                raise DatabaseError(f"Failed to get current usage: {str(e)}")
    
    async def get_usage_history_for_subscription(
        self, 
        subscription_id: str, 
        months_back: int = 12
    ) -> List[SubscriptionUsage]:
        """Get usage history for subscription."""
        async with await self.get_session() as session:
            try:
                from datetime import timedelta
                start_date = datetime.utcnow() - timedelta(days=months_back * 30)
                
                query = select(self.model).where(
                    and_(
                        self.model.subscription_id == subscription_id,
                        self.model.period_start >= start_date
                    )
                ).order_by(desc(self.model.period_start))
                
                result = await session.execute(query)
                return list(result.scalars().all())
                
            except Exception as e:
                raise DatabaseError(f"Failed to get usage history: {str(e)}")
    
    async def update_usage_metrics(
        self, 
        subscription_id: str, 
        usage_updates: Dict[str, Any]
    ) -> Optional[SubscriptionUsage]:
        """Update usage metrics for current period."""
        async with await self.get_session() as session:
            try:
                from sqlalchemy import update
                
                current_time = datetime.utcnow()
                
                query = update(self.model).where(
                    and_(
                        self.model.subscription_id == subscription_id,
                        self.model.period_start <= current_time,
                        self.model.period_end >= current_time
                    )
                ).values(**usage_updates)
                
                result = await session.execute(query)
                await session.commit()
                
                if result.rowcount > 0:
                    return await self.get_current_usage_for_subscription(subscription_id)
                else:
                    return None
                
            except Exception as e:
                await session.rollback()
                raise DatabaseError(f"Failed to update usage metrics: {str(e)}")


class SubscriptionDiscountRepository(BaseRepository[SubscriptionDiscount, None, None]):
    """Repository for subscription discount management."""
    
    def __init__(self):
        super().__init__(SubscriptionDiscount)
    
    async def get_active_discounts_for_subscription(self, subscription_id: str) -> List[SubscriptionDiscount]:
        """Get active discounts for subscription."""
        async with await self.get_session() as session:
            try:
                current_time = datetime.utcnow()
                
                query = select(self.model).where(
                    and_(
                        self.model.subscription_id == subscription_id,
                        self.model.is_active == True,
                        self.model.start_date <= current_time,
                        or_(
                            self.model.end_date.is_(None),
                            self.model.end_date >= current_time
                        )
                    )
                )
                
                result = await session.execute(query)
                return list(result.scalars().all())
                
            except Exception as e:
                raise DatabaseError(f"Failed to get active discounts: {str(e)}")
    
    async def get_by_stripe_coupon_id(self, stripe_coupon_id: str) -> Optional[SubscriptionDiscount]:
        """Get discount by Stripe coupon ID."""
        return await self.get_by_field("stripe_coupon_id", stripe_coupon_id)
    
    async def increment_redemption_count(self, discount_id: str) -> bool:
        """Increment redemption count for discount."""
        async with await self.get_session() as session:
            try:
                from sqlalchemy import update
                
                query = update(self.model).where(self.model.id == discount_id).values(
                    times_redeemed=self.model.times_redeemed + 1
                )
                
                result = await session.execute(query)
                await session.commit()
                
                return result.rowcount > 0
                
            except Exception as e:
                await session.rollback()
                raise DatabaseError(f"Failed to increment redemption count: {str(e)}")
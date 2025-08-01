"""Subscription business logic service."""
import asyncio
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import structlog

from src.subscriptions.repository import (
    SubscriptionRepository, SubscriptionInvoiceRepository, SubscriptionEventRepository,
    PaymentMethodRepository, SubscriptionUsageRepository, SubscriptionDiscountRepository
)
from src.subscriptions.models import (
    Subscription, SubscriptionInvoice, SubscriptionEvent, 
    PaymentMethod, SubscriptionUsage, SubscriptionDiscount
)
from src.subscriptions.schemas import (
    SubscriptionResponse, SubscriptionUpdate, SubscriptionInvoiceResponse,
    SubscriptionEventResponse, PaymentMethodResponse, SubscriptionUsageResponse,
    PlanComparisonResponse, BillingPortalResponse, CheckoutSessionResponse,
    SubscriptionPlan, SubscriptionStatus
)
from src.services.stripe.subscription import SubscriptionService as StripeSubscriptionService, PlanType
from src.services.stripe.client import get_stripe_client
from src.services.redis.rate_limiter import RateLimiter, RateLimitStrategy
from src.exceptions import (
    NotFoundError, ValidationError, BusinessLogicError, 
    StripeError, RateLimitExceededError
)

logger = structlog.get_logger(__name__)


class SubscriptionService:
    """Service for subscription management with Stripe integration."""
    
    def __init__(self):
        self.subscription_repo = SubscriptionRepository()
        self.invoice_repo = SubscriptionInvoiceRepository()
        self.event_repo = SubscriptionEventRepository()
        self.payment_method_repo = PaymentMethodRepository()
        self.usage_repo = SubscriptionUsageRepository()
        self.discount_repo = SubscriptionDiscountRepository()
        self.stripe_service = StripeSubscriptionService()
        self.rate_limiter = RateLimiter()
    
    # Plan configuration matching Stripe service
    PLAN_CONFIGS = {
        SubscriptionPlan.FREE: {
            "name": "Free Plan",
            "price": Decimal("0.00"),
            "interval": "month",
            "features": {
                "max_accounts": 2,
                "max_transactions": 100,
                "max_family_members": 1,
                "basic_budgeting": True,
                "advanced_analytics": False,
                "priority_support": False,
                "data_export": False
            }
        },
        SubscriptionPlan.PREMIUM_INDIVIDUAL: {
            "name": "Premium Individual",
            "price": Decimal("9.99"),
            "interval": "month",
            "stripe_price_id": "price_premium_individual_monthly",
            "features": {
                "max_accounts": 10,
                "max_transactions": 1000,
                "max_family_members": 1,
                "basic_budgeting": True,
                "advanced_analytics": True,
                "priority_support": True,
                "data_export": True,
                "goal_tracking": True
            }
        },
        SubscriptionPlan.PREMIUM_FAMILY: {
            "name": "Premium Family",
            "price": Decimal("19.99"),
            "interval": "month",
            "stripe_price_id": "price_premium_family_monthly",
            "features": {
                "max_accounts": 999,
                "max_transactions": 999999,
                "max_family_members": 6,
                "basic_budgeting": True,
                "advanced_analytics": True,
                "priority_support": True,
                "data_export": True,
                "goal_tracking": True,
                "family_sharing": True,
                "custom_categories": True
            }
        }
    }
    
    async def get_subscription_for_user(self, user_id: str) -> Optional[SubscriptionResponse]:
        """Get active subscription for user."""
        try:
            subscription = await self.subscription_repo.get_active_subscription_for_user(user_id)
            if not subscription:
                return None
            
            return SubscriptionResponse.model_validate(subscription)
            
        except Exception as e:
            logger.error("Failed to get subscription for user", user_id=user_id, error=str(e))
            raise BusinessLogicError(f"Failed to get subscription: {str(e)}")
    
    async def create_subscription(
        self,
        user_id: str,
        user_email: str,
        user_name: str,
        plan: SubscriptionPlan,
        payment_method_id: str = None,
        trial_days: int = None
    ) -> SubscriptionResponse:
        """Create new subscription via Stripe."""
        try:
            # Check rate limiting
            await self._check_rate_limit(user_id, "subscription_create")
            
            # Validate plan
            if plan not in self.PLAN_CONFIGS:
                raise ValidationError(f"Invalid plan: {plan}")
            
            # Check if user already has active subscription
            existing = await self.subscription_repo.get_active_subscription_for_user(user_id)
            if existing:
                raise BusinessLogicError("User already has an active subscription")
            
            # Convert to Stripe plan type
            stripe_plan_type = self._convert_to_stripe_plan_type(plan)
            
            # Create subscription in Stripe
            stripe_result = await self.stripe_service.create_customer_and_subscription(
                tenant_id=user_id,  # Using user_id as tenant_id for now
                user_email=user_email,
                user_name=user_name,
                plan_type=stripe_plan_type,
                payment_method_id=payment_method_id,
                trial_days=trial_days
            )
            
            # Create local subscription record
            plan_config = self.PLAN_CONFIGS[plan]
            subscription_data = {
                "id": str(uuid4()),
                "user_id": user_id,
                "stripe_subscription_id": stripe_result["subscription_id"],
                "stripe_customer_id": stripe_result["customer_id"],
                "stripe_price_id": plan_config.get("stripe_price_id", ""),
                "plan": plan.value,
                "plan_name": plan_config["name"],
                "status": stripe_result["status"],
                "current_period_start": datetime.fromtimestamp(stripe_result["current_period_start"]),
                "current_period_end": datetime.fromtimestamp(stripe_result["current_period_end"]),
                "trial_start": datetime.fromtimestamp(stripe_result.get("trial_start", 0)) if stripe_result.get("trial_start") else None,
                "trial_end": datetime.fromtimestamp(stripe_result["trial_end"]) if stripe_result.get("trial_end") else None,
                "cancel_at_period_end": stripe_result["cancel_at_period_end"],
                "amount": plan_config["price"],
                "currency": "USD",
                "interval": plan_config["interval"],
                "interval_count": 1,
                "default_payment_method": payment_method_id,
                "plan_limits": plan_config["features"],
                "metadata": {
                    "created_via": "api",
                    "stripe_customer_id": stripe_result["customer_id"]
                }
            }
            
            subscription = Subscription(**subscription_data)
            
            # Save to database
            async with await self.subscription_repo.get_session() as session:
                session.add(subscription)
                await session.commit()
                await session.refresh(subscription)
            
            logger.info("Subscription created successfully", 
                       user_id=user_id, 
                       subscription_id=subscription.id,
                       plan=plan.value)
            
            return SubscriptionResponse.model_validate(subscription)
            
        except (StripeError, ValidationError, BusinessLogicError) as e:
            raise e
        except Exception as e:
            logger.error("Failed to create subscription", user_id=user_id, error=str(e))
            raise BusinessLogicError(f"Failed to create subscription: {str(e)}")
    
    async def update_subscription(
        self,
        subscription_id: str,
        user_id: str,
        update_data: SubscriptionUpdate
    ) -> SubscriptionResponse:
        """Update subscription."""
        try:
            # Get existing subscription
            subscription = await self.subscription_repo.get_by_id_for_user(subscription_id, user_id)
            if not subscription:
                raise NotFoundError("Subscription not found")
            
            # Update in database
            updated_subscription = await self.subscription_repo.update(subscription_id, update_data)
            if not updated_subscription:
                raise NotFoundError("Subscription not found")
            
            # Sync with Stripe if needed
            if update_data.cancel_at_period_end is not None:
                try:
                    if update_data.cancel_at_period_end:
                        await self.stripe_service.cancel_subscription(
                            tenant_id=user_id,
                            subscription_id=subscription.stripe_subscription_id,
                            at_period_end=True,
                            cancellation_reason=update_data.cancellation_reason
                        )
                    else:
                        await self.stripe_service.reactivate_subscription(
                            tenant_id=user_id,
                            subscription_id=subscription.stripe_subscription_id
                        )
                except StripeError as e:
                    logger.warning("Failed to sync subscription with Stripe", error=str(e))
            
            logger.info("Subscription updated", subscription_id=subscription_id, user_id=user_id)
            
            return SubscriptionResponse.model_validate(updated_subscription)
            
        except (NotFoundError, ValidationError) as e:
            raise e
        except Exception as e:
            logger.error("Failed to update subscription", subscription_id=subscription_id, error=str(e))
            raise BusinessLogicError(f"Failed to update subscription: {str(e)}")
    
    async def change_subscription_plan(
        self,
        subscription_id: str,
        user_id: str,
        new_plan: SubscriptionPlan,
        prorate: bool = True
    ) -> SubscriptionResponse:
        """Change subscription plan."""
        try:
            # Check rate limiting
            await self._check_rate_limit(user_id, "plan_change")
            
            # Get existing subscription
            subscription = await self.subscription_repo.get_by_id_for_user(subscription_id, user_id)
            if not subscription:
                raise NotFoundError("Subscription not found")
            
            if subscription.plan == new_plan.value:
                raise ValidationError("Subscription is already on this plan")
            
            # Validate new plan
            if new_plan not in self.PLAN_CONFIGS:
                raise ValidationError(f"Invalid plan: {new_plan}")
            
            # Convert to Stripe plan type
            stripe_plan_type = self._convert_to_stripe_plan_type(new_plan)
            
            # Change plan in Stripe
            stripe_result = await self.stripe_service.change_subscription_plan(
                tenant_id=user_id,
                subscription_id=subscription.stripe_subscription_id,
                new_plan_type=stripe_plan_type,
                prorate=prorate
            )
            
            # Update local subscription
            plan_config = self.PLAN_CONFIGS[new_plan]
            update_data = SubscriptionUpdate(
                metadata={
                    **subscription.metadata,
                    "plan_changed_at": datetime.utcnow().isoformat(),
                    "previous_plan": subscription.plan
                }
            )
            
            updated_subscription = await self.subscription_repo.update(
                subscription_id, 
                update_data,
                plan=new_plan.value,
                plan_name=plan_config["name"],
                amount=plan_config["price"],
                plan_limits=plan_config["features"],
                stripe_price_id=plan_config.get("stripe_price_id", "")
            )
            
            logger.info("Subscription plan changed", 
                       subscription_id=subscription_id,
                       old_plan=subscription.plan,
                       new_plan=new_plan.value)
            
            return SubscriptionResponse.model_validate(updated_subscription)
            
        except (NotFoundError, ValidationError, StripeError) as e:
            raise e
        except Exception as e:
            logger.error("Failed to change subscription plan", error=str(e))
            raise BusinessLogicError(f"Failed to change plan: {str(e)}")
    
    async def cancel_subscription(
        self,
        subscription_id: str,
        user_id: str,
        at_period_end: bool = True,
        cancellation_reason: str = None
    ) -> SubscriptionResponse:
        """Cancel subscription."""
        try:
            # Get existing subscription
            subscription = await self.subscription_repo.get_by_id_for_user(subscription_id, user_id)
            if not subscription:
                raise NotFoundError("Subscription not found")
            
            # Cancel in Stripe
            stripe_result = await self.stripe_service.cancel_subscription(
                tenant_id=user_id,
                subscription_id=subscription.stripe_subscription_id,
                at_period_end=at_period_end,
                cancellation_reason=cancellation_reason
            )
            
            # Update local subscription
            update_data = SubscriptionUpdate(
                cancel_at_period_end=at_period_end,
                cancellation_reason=cancellation_reason
            )
            
            if not at_period_end:
                # Immediate cancellation
                update_data = SubscriptionUpdate(
                    cancellation_reason=cancellation_reason,
                    metadata={
                        **subscription.metadata,
                        "canceled_immediately": True,
                        "canceled_at": datetime.utcnow().isoformat()
                    }
                )
                await self.subscription_repo.update(
                    subscription_id,
                    update_data,
                    status="cancelled",
                    canceled_at=datetime.utcnow()
                )
            else:
                await self.subscription_repo.update(subscription_id, update_data)
            
            updated_subscription = await self.subscription_repo.get_by_id(subscription_id)
            
            logger.info("Subscription canceled", 
                       subscription_id=subscription_id,
                       at_period_end=at_period_end)
            
            return SubscriptionResponse.model_validate(updated_subscription)
            
        except (NotFoundError, StripeError) as e:
            raise e
        except Exception as e:
            logger.error("Failed to cancel subscription", error=str(e))
            raise BusinessLogicError(f"Failed to cancel subscription: {str(e)}")
    
    async def reactivate_subscription(
        self,
        subscription_id: str,
        user_id: str
    ) -> SubscriptionResponse:
        """Reactivate a canceled subscription."""
        try:
            # Get existing subscription
            subscription = await self.subscription_repo.get_by_id_for_user(subscription_id, user_id)
            if not subscription:
                raise NotFoundError("Subscription not found")
            
            if not subscription.cancel_at_period_end:
                raise ValidationError("Subscription is not set to cancel")
            
            # Reactivate in Stripe
            await self.stripe_service.reactivate_subscription(
                tenant_id=user_id,
                subscription_id=subscription.stripe_subscription_id
            )
            
            # Update local subscription
            update_data = SubscriptionUpdate(
                cancel_at_period_end=False,
                cancellation_reason=None,
                metadata={
                    **subscription.metadata,
                    "reactivated_at": datetime.utcnow().isoformat()
                }
            )
            
            updated_subscription = await self.subscription_repo.update(subscription_id, update_data)
            
            logger.info("Subscription reactivated", subscription_id=subscription_id)
            
            return SubscriptionResponse.model_validate(updated_subscription)
            
        except (NotFoundError, ValidationError, StripeError) as e:
            raise e
        except Exception as e:
            logger.error("Failed to reactivate subscription", error=str(e))
            raise BusinessLogicError(f"Failed to reactivate subscription: {str(e)}")
    
    async def get_billing_history(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50
    ) -> List[SubscriptionInvoiceResponse]:
        """Get billing history for user."""
        try:
            invoices = await self.invoice_repo.get_billing_history_for_user(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )
            
            return [SubscriptionInvoiceResponse.model_validate(invoice) for invoice in invoices]
            
        except Exception as e:
            logger.error("Failed to get billing history", user_id=user_id, error=str(e))
            raise BusinessLogicError(f"Failed to get billing history: {str(e)}")
    
    async def get_subscription_usage(
        self,
        subscription_id: str,
        user_id: str
    ) -> Optional[SubscriptionUsageResponse]:
        """Get current usage for subscription."""
        try:
            # Verify subscription ownership
            subscription = await self.subscription_repo.get_by_id_for_user(subscription_id, user_id)
            if not subscription:
                raise NotFoundError("Subscription not found")
            
            usage = await self.usage_repo.get_current_usage_for_subscription(subscription_id)
            if not usage:
                return None
            
            return SubscriptionUsageResponse.model_validate(usage)
            
        except NotFoundError as e:
            raise e
        except Exception as e:
            logger.error("Failed to get subscription usage", error=str(e))
            raise BusinessLogicError(f"Failed to get usage: {str(e)}")
    
    async def update_usage_metrics(
        self,
        user_id: str,
        metrics: Dict[str, Any]
    ) -> bool:
        """Update usage metrics for user's active subscription."""
        try:
            # Get active subscription
            subscription = await self.subscription_repo.get_active_subscription_for_user(user_id)
            if not subscription:
                return False
            
            # Update usage
            updated_usage = await self.usage_repo.update_usage_metrics(
                subscription.id,
                metrics
            )
            
            return updated_usage is not None
            
        except Exception as e:
            logger.error("Failed to update usage metrics", error=str(e))
            return False
    
    async def get_plan_comparison(self, user_id: str) -> PlanComparisonResponse:
        """Get plan comparison with current user's plan."""
        try:
            # Get current subscription
            current_subscription = await self.subscription_repo.get_active_subscription_for_user(user_id)
            current_plan = current_subscription.plan if current_subscription else "free"
            
            # Build plan comparison
            plans = []
            for plan, config in self.PLAN_CONFIGS.items():
                plans.append({
                    "id": plan.value,
                    "name": config["name"],
                    "price": str(config["price"]),
                    "interval": config["interval"],
                    "features": config["features"],
                    "is_current": plan.value == current_plan
                })
            
            # Generate recommendations
            recommendations = self._generate_plan_recommendations(current_plan, current_subscription)
            
            return PlanComparisonResponse(
                plans=plans,
                current_plan=current_plan,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error("Failed to get plan comparison", error=str(e))
            raise BusinessLogicError(f"Failed to get plan comparison: {str(e)}")
    
    async def create_billing_portal_session(
        self,
        user_id: str,
        return_url: str
    ) -> BillingPortalResponse:
        """Create Stripe billing portal session."""
        try:
            # Get active subscription
            subscription = await self.subscription_repo.get_active_subscription_for_user(user_id)
            if not subscription:
                raise ValidationError("No active subscription found")
            
            # Create portal session
            portal_session = await self.stripe_service.create_billing_portal_session(
                tenant_id=user_id,
                customer_id=subscription.stripe_customer_id,
                return_url=return_url
            )
            
            return BillingPortalResponse(url=portal_session["portal_url"])
            
        except (ValidationError, StripeError) as e:
            raise e
        except Exception as e:
            logger.error("Failed to create billing portal session", error=str(e))
            raise BusinessLogicError(f"Failed to create billing portal: {str(e)}")
    
    async def validate_plan_limits(
        self,
        user_id: str,
        usage_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate current usage against plan limits."""
        try:
            # Get active subscription
            subscription = await self.subscription_repo.get_active_subscription_for_user(user_id)
            if not subscription:
                # User is on free plan
                plan_limits = self.PLAN_CONFIGS[SubscriptionPlan.FREE]["features"]
            else:
                plan_limits = subscription.plan_limits
            
            violations = []
            
            # Check each limit
            for metric, limit in plan_limits.items():
                if metric.startswith("max_") and metric.replace("max_", "") in usage_metrics:
                    current_value = usage_metrics[metric.replace("max_", "")]
                    if isinstance(limit, int) and current_value > limit:
                        violations.append({
                            "metric": metric,
                            "current": current_value,
                            "limit": limit,
                            "message": f"Exceeded {metric.replace('max_', '').replace('_', ' ')} limit"
                        })
            
            return {
                "valid": len(violations) == 0,
                "violations": violations,
                "plan_limits": plan_limits,
                "current_usage": usage_metrics
            }
            
        except Exception as e:
            logger.error("Failed to validate plan limits", error=str(e))
            raise BusinessLogicError(f"Failed to validate limits: {str(e)}")
    
    async def process_webhook_event(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        stripe_event_id: str = None
    ) -> bool:
        """Process Stripe webhook event."""
        try:
            # Check if event already processed
            if stripe_event_id:
                existing_event = await self.event_repo.get_by_stripe_event_id(stripe_event_id)
                if existing_event and existing_event.processed:
                    logger.info("Event already processed", stripe_event_id=stripe_event_id)
                    return True
            
            # Create event record
            event_record = SubscriptionEvent(
                id=str(uuid4()),
                subscription_id=event_data.get("object", {}).get("id", ""),
                event_type=event_type,
                event_source="stripe",
                stripe_event_id=stripe_event_id,
                event_data=event_data,
                processed=False
            )
            
            async with await self.event_repo.get_session() as session:
                session.add(event_record)
                await session.commit()
                await session.refresh(event_record)
            
            # Process event based on type
            success = await self._process_webhook_event_by_type(event_type, event_data)
            
            # Mark as processed
            await self.event_repo.mark_event_processed(
                event_record.id,
                error_message=None if success else "Processing failed"
            )
            
            return success
            
        except Exception as e:
            logger.error("Failed to process webhook event", event_type=event_type, error=str(e))
            return False
    
    async def get_subscription_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get subscription analytics and metrics."""
        try:
            # Get subscription metrics
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()
            
            # Get active subscriptions by plan
            active_subscriptions = await self.subscription_repo.get_subscriptions_by_status("active")
            plan_distribution = {}
            for sub in active_subscriptions:
                plan = sub.plan
                plan_distribution[plan] = plan_distribution.get(plan, 0) + 1
            
            # Get revenue summary
            revenue_summary = await self.invoice_repo.get_revenue_summary(start_date, end_date)
            
            # Get trial conversions
            trial_subs = await self.subscription_repo.get_subscriptions_by_status("trialing")
            
            # Get churn metrics
            canceled_subs = await self.subscription_repo.get_subscriptions_by_status("cancelled")
            
            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "subscriptions": {
                    "total_active": len(active_subscriptions),
                    "plan_distribution": plan_distribution,
                    "trials_active": len(trial_subs),
                    "canceled_total": len(canceled_subs)
                },
                "revenue": revenue_summary,
                "metrics": {
                    "average_revenue_per_user": float(revenue_summary["total_paid"]) / max(len(active_subscriptions), 1),
                    "collection_rate": revenue_summary["collection_rate"]
                }
            }
            
        except Exception as e:
            logger.error("Failed to get subscription analytics", error=str(e))
            raise BusinessLogicError(f"Failed to get analytics: {str(e)}")
    
    # Private helper methods
    async def _check_rate_limit(self, user_id: str, operation: str):
        """Check rate limiting for subscription operations."""
        try:
            allowed, info = await self.rate_limiter.check_rate_limit(
                tenant_id=user_id,
                identifier=user_id,
                rate_type=f"subscription_{operation}",
                strategy=RateLimitStrategy.SLIDING_WINDOW,
                limit=5,
                window=3600  # 5 operations per hour
            )
            
            if not allowed:
                raise RateLimitExceededError(
                    f"Rate limit exceeded for {operation}",
                    retry_after=info.get("retry_after", 3600)
                )
                
        except RateLimitExceededError:
            raise
        except Exception as e:
            logger.warning("Rate limit check failed", error=str(e))
            # Don't fail the operation due to rate limit issues
    
    def _convert_to_stripe_plan_type(self, plan: SubscriptionPlan) -> PlanType:
        """Convert internal plan to Stripe plan type."""
        mapping = {
            SubscriptionPlan.PREMIUM_INDIVIDUAL: PlanType.PERSONAL,
            SubscriptionPlan.PREMIUM_FAMILY: PlanType.FAMILY
        }
        return mapping.get(plan, PlanType.PERSONAL)
    
    def _generate_plan_recommendations(
        self, 
        current_plan: str, 
        subscription: Optional[Subscription]
    ) -> List[str]:
        """Generate plan recommendations based on current plan and usage."""
        recommendations = []
        
        if current_plan == "free":
            recommendations.append("Upgrade to Premium Individual for advanced budgeting and analytics")
            recommendations.append("Consider Premium Family if you need family sharing features")
        elif current_plan == "premium_individual":
            recommendations.append("Upgrade to Premium Family for family sharing and unlimited accounts")
        elif current_plan == "premium_family":
            recommendations.append("You're on our most comprehensive plan!")
        
        # Add usage-based recommendations
        if subscription and subscription.usage_data:
            usage = subscription.usage_data
            limits = subscription.plan_limits
            
            # Check if approaching limits
            for metric, limit in limits.items():
                if metric.startswith("max_") and isinstance(limit, int):
                    usage_key = metric.replace("max_", "")
                    current_usage = usage.get(usage_key, 0)
                    
                    if current_usage > limit * 0.8:  # 80% of limit
                        recommendations.append(f"Consider upgrading - you're using {current_usage}/{limit} {usage_key.replace('_', ' ')}")
        
        return recommendations
    
    async def _process_webhook_event_by_type(self, event_type: str, event_data: Dict[str, Any]) -> bool:
        """Process webhook event based on type."""
        try:
            stripe_subscription = event_data.get("object", {})
            stripe_subscription_id = stripe_subscription.get("id")
            
            if not stripe_subscription_id:
                logger.warning("No subscription ID in webhook event", event_type=event_type)
                return False
            
            # Get local subscription
            subscription = await self.subscription_repo.get_by_stripe_subscription_id(stripe_subscription_id)
            if not subscription:
                logger.warning("Subscription not found for webhook", 
                             stripe_subscription_id=stripe_subscription_id)
                return False
            
            if event_type == "customer.subscription.updated":
                # Update subscription status and details
                await self.subscription_repo.update(
                    subscription.id,
                    SubscriptionUpdate(metadata={"last_webhook_update": datetime.utcnow().isoformat()}),
                    status=stripe_subscription.get("status", subscription.status),
                    cancel_at_period_end=stripe_subscription.get("cancel_at_period_end", subscription.cancel_at_period_end),
                    current_period_start=datetime.fromtimestamp(stripe_subscription.get("current_period_start", 0)),
                    current_period_end=datetime.fromtimestamp(stripe_subscription.get("current_period_end", 0))
                )
                
            elif event_type == "customer.subscription.deleted":
                # Mark subscription as cancelled
                await self.subscription_repo.update(
                    subscription.id,
                    SubscriptionUpdate(metadata={"canceled_via_webhook": True}),
                    status="cancelled",
                    canceled_at=datetime.utcnow()
                )
                
            elif event_type == "invoice.payment_succeeded":
                # Create/update invoice record
                await self._handle_invoice_webhook(event_data, "paid")
                
            elif event_type == "invoice.payment_failed":
                # Update invoice and subscription status
                await self._handle_invoice_webhook(event_data, "open")
                # Potentially update subscription status to past_due
                await self.subscription_repo.update(
                    subscription.id,
                    SubscriptionUpdate(metadata={"payment_failed": datetime.utcnow().isoformat()}),
                    status="past_due"
                )
            
            return True
            
        except Exception as e:
            logger.error("Failed to process webhook event by type", 
                        event_type=event_type, 
                        error=str(e))
            return False
    
    async def _handle_invoice_webhook(self, event_data: Dict[str, Any], status: str) -> bool:
        """Handle invoice-related webhook events."""
        try:
            stripe_invoice = event_data.get("object", {})
            stripe_invoice_id = stripe_invoice.get("id")
            
            if not stripe_invoice_id:
                return False
            
            # Check if invoice already exists
            existing_invoice = await self.invoice_repo.get_by_stripe_invoice_id(stripe_invoice_id)
            
            if existing_invoice:
                # Update existing invoice
                await self.invoice_repo.update(
                    existing_invoice.id,
                    None,  # No update schema for invoices
                    status=status,
                    amount_paid=Decimal(str(stripe_invoice.get("amount_paid", 0) / 100)),
                    amount_remaining=Decimal(str(stripe_invoice.get("amount_remaining", 0) / 100)),
                    paid_at=datetime.fromtimestamp(stripe_invoice.get("status_transitions", {}).get("paid_at", 0)) if status == "paid" else None
                )
            else:
                # Create new invoice record
                subscription = await self.subscription_repo.get_by_stripe_subscription_id(
                    stripe_invoice.get("subscription")
                )
                
                if subscription:
                    invoice_data = {
                        "id": str(uuid4()),
                        "subscription_id": subscription.id,
                        "user_id": subscription.user_id,
                        "stripe_invoice_id": stripe_invoice_id,
                        "stripe_payment_intent_id": stripe_invoice.get("payment_intent"),
                        "invoice_number": stripe_invoice.get("number", ""),
                        "amount_due": Decimal(str(stripe_invoice.get("amount_due", 0) / 100)),
                        "amount_paid": Decimal(str(stripe_invoice.get("amount_paid", 0) / 100)),
                        "amount_remaining": Decimal(str(stripe_invoice.get("amount_remaining", 0) / 100)),
                        "status": status,
                        "period_start": datetime.fromtimestamp(stripe_invoice.get("period_start", 0)),
                        "period_end": datetime.fromtimestamp(stripe_invoice.get("period_end", 0)),
                        "due_date": datetime.fromtimestamp(stripe_invoice.get("due_date", 0)) if stripe_invoice.get("due_date") else None,
                        "paid_at": datetime.fromtimestamp(stripe_invoice.get("status_transitions", {}).get("paid_at", 0)) if status == "paid" else None,
                        "currency": stripe_invoice.get("currency", "usd").upper(),
                        "hosted_invoice_url": stripe_invoice.get("hosted_invoice_url"),
                        "invoice_pdf": stripe_invoice.get("invoice_pdf"),
                        "line_items": stripe_invoice.get("lines", {}).get("data", []),
                        "metadata": stripe_invoice.get("metadata", {})
                    }
                    
                    invoice = SubscriptionInvoice(**invoice_data)
                    
                    async with await self.invoice_repo.get_session() as session:
                        session.add(invoice)
                        await session.commit()
            
            return True
            
        except Exception as e:
            logger.error("Failed to handle invoice webhook", error=str(e))
            return False
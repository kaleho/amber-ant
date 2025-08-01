"""Stripe subscription management service."""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from enum import Enum

import stripe
import structlog

from .client import StripeClient, get_stripe_client
from src.exceptions import StripeError, ValidationError

logger = structlog.get_logger(__name__)


class SubscriptionStatus(Enum):
    """Subscription status enum."""
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"


class PlanType(Enum):
    """Subscription plan types."""
    PERSONAL = "personal"
    FAMILY = "family"
    PREMIUM = "premium"


class SubscriptionService:
    """Service for managing Stripe subscriptions with tenant isolation."""
    
    def __init__(self, stripe_client: Optional[StripeClient] = None):
        self.stripe_client = stripe_client or get_stripe_client()
        
        # Plan configuration - should match your Stripe dashboard
        self.plan_configs = {
            PlanType.PERSONAL: {
                "name": "Personal Plan",
                "price_id": "price_personal_monthly",  # Replace with actual Stripe price ID
                "features": ["Basic budgeting", "Expense tracking", "1 bank account"],
                "max_family_members": 1,
                "max_accounts": 3
            },
            PlanType.FAMILY: {
                "name": "Family Plan", 
                "price_id": "price_family_monthly",  # Replace with actual Stripe price ID
                "features": ["All Personal features", "Family sharing", "Up to 6 members", "Unlimited accounts"],
                "max_family_members": 6,
                "max_accounts": 999
            },
            PlanType.PREMIUM: {
                "name": "Premium Plan",
                "price_id": "price_premium_monthly",  # Replace with actual Stripe price ID
                "features": ["All Family features", "Advanced analytics", "Export data", "Priority support"],
                "max_family_members": 10,
                "max_accounts": 999
            }
        }
    
    async def create_customer_and_subscription(
        self,
        tenant_id: str,
        user_email: str,
        user_name: str,
        plan_type: PlanType,
        payment_method_id: str = None,
        trial_days: int = None
    ) -> Dict[str, Any]:
        """Create Stripe customer and subscription for new tenant."""
        try:
            # Create Stripe customer
            customer = await self.stripe_client.create_customer(
                email=user_email,
                name=user_name,
                metadata={
                    "tenant_id": tenant_id,
                    "plan_type": plan_type.value,
                    "created_via": "api"
                }
            )
            
            logger.info("Stripe customer created", 
                       tenant_id=tenant_id, 
                       customer_id=customer.id,
                       plan_type=plan_type.value)
            
            # Get plan configuration
            plan_config = self.plan_configs[plan_type]
            
            # Create subscription
            subscription_params = {
                "customer_id": customer.id,
                "price_id": plan_config["price_id"],
                "metadata": {
                    "tenant_id": tenant_id,
                    "plan_type": plan_type.value,
                    "created_via": "api"
                }
            }
            
            if trial_days:
                subscription_params["trial_period_days"] = trial_days
            
            if payment_method_id:
                subscription_params["default_payment_method"] = payment_method_id
            
            subscription = await self.stripe_client.create_subscription(**subscription_params)
            
            logger.info("Stripe subscription created",
                       tenant_id=tenant_id,
                       subscription_id=subscription.id,
                       status=subscription.status)
            
            return {
                "customer_id": customer.id,
                "subscription_id": subscription.id,
                "status": subscription.status,
                "plan_type": plan_type.value,
                "plan_config": plan_config,
                "current_period_start": subscription.current_period_start,
                "current_period_end": subscription.current_period_end,
                "trial_end": subscription.trial_end,
                "cancel_at_period_end": subscription.cancel_at_period_end
            }
            
        except stripe.error.StripeError as e:
            logger.error("Failed to create customer and subscription",
                        tenant_id=tenant_id,
                        error=str(e))
            raise StripeError(f"Failed to create subscription: {str(e)}")
    
    async def get_subscription_details(
        self,
        tenant_id: str,
        subscription_id: str
    ) -> Dict[str, Any]:
        """Get detailed subscription information."""
        try:
            subscription = await self.stripe_client.get_subscription(subscription_id)
            
            # Verify tenant ownership
            if subscription.metadata.get("tenant_id") != tenant_id:
                raise ValidationError("Subscription does not belong to tenant")
            
            # Get customer details
            customer = await self.stripe_client.get_customer(subscription.customer)
            
            # Get plan details
            price = subscription.items.data[0].price
            plan_type = PlanType(subscription.metadata.get("plan_type", "personal"))
            plan_config = self.plan_configs.get(plan_type, {})
            
            return {
                "subscription_id": subscription.id,
                "customer_id": customer.id,
                "customer_email": customer.email,
                "customer_name": customer.name,
                "status": subscription.status,
                "plan_type": plan_type.value,
                "plan_name": plan_config.get("name"),
                "plan_features": plan_config.get("features", []),
                "current_period_start": subscription.current_period_start,
                "current_period_end": subscription.current_period_end,
                "trial_start": subscription.trial_start,
                "trial_end": subscription.trial_end,
                "cancel_at_period_end": subscription.cancel_at_period_end,
                "canceled_at": subscription.canceled_at,
                "amount": price.unit_amount,
                "currency": price.currency,
                "interval": price.recurring.interval,
                "created": subscription.created,
                "latest_invoice": subscription.latest_invoice
            }
            
        except stripe.error.StripeError as e:
            logger.error("Failed to get subscription details",
                        tenant_id=tenant_id,
                        subscription_id=subscription_id,
                        error=str(e))
            raise StripeError(f"Failed to get subscription: {str(e)}")
    
    async def change_subscription_plan(
        self,
        tenant_id: str,
        subscription_id: str,
        new_plan_type: PlanType,
        prorate: bool = True
    ) -> Dict[str, Any]:
        """Change subscription plan."""
        try:
            subscription = await self.stripe_client.get_subscription(subscription_id)
            
            # Verify tenant ownership
            if subscription.metadata.get("tenant_id") != tenant_id:
                raise ValidationError("Subscription does not belong to tenant")
            
            # Get new plan configuration
            new_plan_config = self.plan_configs[new_plan_type]
            
            # Update subscription
            updated_subscription = await self.stripe_client.update_subscription(
                subscription_id,
                items=[{
                    "id": subscription.items.data[0].id,
                    "price": new_plan_config["price_id"]
                }],
                proration_behavior="create_prorations" if prorate else "none",
                metadata={
                    **subscription.metadata,
                    "plan_type": new_plan_type.value,
                    "plan_changed_at": str(int(datetime.now(timezone.utc).timestamp()))
                }
            )
            
            logger.info("Subscription plan changed",
                       tenant_id=tenant_id,
                       subscription_id=subscription_id,
                       old_plan=subscription.metadata.get("plan_type"),
                       new_plan=new_plan_type.value)
            
            return {
                "subscription_id": updated_subscription.id,
                "status": updated_subscription.status,
                "old_plan_type": subscription.metadata.get("plan_type"),
                "new_plan_type": new_plan_type.value,
                "new_plan_config": new_plan_config,
                "proration_created": prorate,
                "current_period_start": updated_subscription.current_period_start,
                "current_period_end": updated_subscription.current_period_end
            }
            
        except stripe.error.StripeError as e:
            logger.error("Failed to change subscription plan",
                        tenant_id=tenant_id,
                        subscription_id=subscription_id,
                        new_plan=new_plan_type.value,
                        error=str(e))
            raise StripeError(f"Failed to change plan: {str(e)}")
    
    async def cancel_subscription(
        self,
        tenant_id: str,
        subscription_id: str,
        at_period_end: bool = True,
        cancellation_reason: str = None
    ) -> Dict[str, Any]:
        """Cancel subscription."""
        try:
            subscription = await self.stripe_client.get_subscription(subscription_id)
            
            # Verify tenant ownership
            if subscription.metadata.get("tenant_id") != tenant_id:
                raise ValidationError("Subscription does not belong to tenant")
            
            # Update metadata with cancellation reason
            metadata_update = {
                **subscription.metadata,
                "canceled_via": "api",
                "canceled_at": str(int(datetime.now(timezone.utc).timestamp()))
            }
            
            if cancellation_reason:
                metadata_update["cancellation_reason"] = cancellation_reason
            
            # Cancel subscription
            canceled_subscription = await self.stripe_client.cancel_subscription(
                subscription_id,
                at_period_end=at_period_end
            )
            
            # Update metadata
            await self.stripe_client.update_subscription(
                subscription_id,
                metadata=metadata_update
            )
            
            logger.info("Subscription canceled",
                       tenant_id=tenant_id,
                       subscription_id=subscription_id,
                       at_period_end=at_period_end,
                       reason=cancellation_reason)
            
            return {
                "subscription_id": canceled_subscription.id,
                "status": canceled_subscription.status,
                "canceled_at": canceled_subscription.canceled_at,
                "cancel_at_period_end": canceled_subscription.cancel_at_period_end,
                "current_period_end": canceled_subscription.current_period_end,
                "at_period_end": at_period_end,
                "cancellation_reason": cancellation_reason
            }
            
        except stripe.error.StripeError as e:
            logger.error("Failed to cancel subscription",
                        tenant_id=tenant_id,
                        subscription_id=subscription_id,
                        error=str(e))
            raise StripeError(f"Failed to cancel subscription: {str(e)}")
    
    async def reactivate_subscription(
        self,
        tenant_id: str,
        subscription_id: str
    ) -> Dict[str, Any]:
        """Reactivate a canceled subscription (if still in current period)."""
        try:
            subscription = await self.stripe_client.get_subscription(subscription_id)
            
            # Verify tenant ownership
            if subscription.metadata.get("tenant_id") != tenant_id:
                raise ValidationError("Subscription does not belong to tenant")
            
            # Check if subscription can be reactivated
            if not subscription.cancel_at_period_end:
                raise ValidationError("Subscription is not set to cancel at period end")
            
            # Reactivate by removing the cancellation
            reactivated_subscription = await self.stripe_client.update_subscription(
                subscription_id,
                cancel_at_period_end=False,
                metadata={
                    **subscription.metadata,
                    "reactivated_via": "api",
                    "reactivated_at": str(int(datetime.now(timezone.utc).timestamp()))
                }
            )
            
            logger.info("Subscription reactivated",
                       tenant_id=tenant_id,
                       subscription_id=subscription_id)
            
            return {
                "subscription_id": reactivated_subscription.id,
                "status": reactivated_subscription.status,
                "cancel_at_period_end": reactivated_subscription.cancel_at_period_end,
                "current_period_end": reactivated_subscription.current_period_end
            }
            
        except stripe.error.StripeError as e:
            logger.error("Failed to reactivate subscription",
                        tenant_id=tenant_id,
                        subscription_id=subscription_id,
                        error=str(e))
            raise StripeError(f"Failed to reactivate subscription: {str(e)}")
    
    async def get_upcoming_invoice(
        self,
        tenant_id: str,
        customer_id: str
    ) -> Dict[str, Any]:
        """Get upcoming invoice preview."""
        try:
            # Verify customer belongs to tenant
            customer = await self.stripe_client.get_customer(customer_id)
            if customer.metadata.get("tenant_id") != tenant_id:
                raise ValidationError("Customer does not belong to tenant")
            
            upcoming_invoice = await self.stripe_client.get_upcoming_invoice(customer_id)
            
            return {
                "amount_due": upcoming_invoice.amount_due,
                "amount_paid": upcoming_invoice.amount_paid,
                "amount_remaining": upcoming_invoice.amount_remaining,
                "currency": upcoming_invoice.currency,
                "period_start": upcoming_invoice.period_start,
                "period_end": upcoming_invoice.period_end,
                "subtotal": upcoming_invoice.subtotal,
                "tax": upcoming_invoice.tax,
                "total": upcoming_invoice.total,
                "lines": [
                    {
                        "description": line.description,
                        "amount": line.amount,
                        "currency": line.currency,
                        "period": {
                            "start": line.period.start,
                            "end": line.period.end
                        } if line.period else None
                    }
                    for line in upcoming_invoice.lines.data
                ]
            }
            
        except stripe.error.StripeError as e:
            logger.error("Failed to get upcoming invoice",
                        tenant_id=tenant_id,
                        customer_id=customer_id,
                        error=str(e))
            raise StripeError(f"Failed to get upcoming invoice: {str(e)}")
    
    async def get_billing_history(
        self,
        tenant_id: str,
        customer_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get billing history for customer."""
        try:
            # Verify customer belongs to tenant
            customer = await self.stripe_client.get_customer(customer_id)
            if customer.metadata.get("tenant_id") != tenant_id:
                raise ValidationError("Customer does not belong to tenant")
            
            invoices = await self.stripe_client.list_invoices(customer_id, limit=limit)
            
            billing_history = []
            for invoice in invoices.data:
                billing_history.append({
                    "invoice_id": invoice.id,
                    "number": invoice.number,
                    "status": invoice.status,
                    "amount_due": invoice.amount_due,
                    "amount_paid": invoice.amount_paid,
                    "currency": invoice.currency,
                    "created": invoice.created,
                    "due_date": invoice.due_date,
                    "period_start": invoice.period_start,
                    "period_end": invoice.period_end,
                    "hosted_invoice_url": invoice.hosted_invoice_url,
                    "invoice_pdf": invoice.invoice_pdf,
                    "paid": invoice.paid,
                    "total": invoice.total
                })
            
            return billing_history
            
        except stripe.error.StripeError as e:
            logger.error("Failed to get billing history",
                        tenant_id=tenant_id,
                        customer_id=customer_id,
                        error=str(e))
            raise StripeError(f"Failed to get billing history: {str(e)}")
    
    async def create_billing_portal_session(
        self,
        tenant_id: str,
        customer_id: str,
        return_url: str
    ) -> Dict[str, Any]:
        """Create billing portal session for customer self-service."""
        try:
            # Verify customer belongs to tenant
            customer = await self.stripe_client.get_customer(customer_id)
            if customer.metadata.get("tenant_id") != tenant_id:
                raise ValidationError("Customer does not belong to tenant")
            
            session = await self.stripe_client.create_billing_portal_session(
                customer_id,
                return_url
            )
            
            logger.info("Billing portal session created",
                       tenant_id=tenant_id,
                       customer_id=customer_id)
            
            return {
                "portal_url": session.url,
                "return_url": session.return_url,
                "created": session.created
            }
            
        except stripe.error.StripeError as e:
            logger.error("Failed to create billing portal session",
                        tenant_id=tenant_id,
                        customer_id=customer_id,
                        error=str(e))
            raise StripeError(f"Failed to create billing portal: {str(e)}")
    
    def get_plan_config(self, plan_type: PlanType) -> Dict[str, Any]:
        """Get plan configuration."""
        return self.plan_configs.get(plan_type, {})
    
    def get_all_plans(self) -> Dict[str, Dict[str, Any]]:
        """Get all available plans."""
        return {plan.value: config for plan, config in self.plan_configs.items()}
    
    async def validate_plan_limits(
        self,
        tenant_id: str,
        plan_type: PlanType,
        current_family_members: int,
        current_accounts: int
    ) -> Dict[str, Any]:
        """Validate if current usage fits within plan limits."""
        plan_config = self.plan_configs[plan_type]
        
        validation_result = {
            "valid": True,
            "violations": [],
            "plan_type": plan_type.value,
            "plan_config": plan_config
        }
        
        # Check family member limits
        max_family_members = plan_config.get("max_family_members", 999)
        if current_family_members > max_family_members:
            validation_result["valid"] = False
            validation_result["violations"].append({
                "type": "family_members",
                "current": current_family_members,
                "limit": max_family_members,
                "message": f"Plan allows maximum {max_family_members} family members"
            })
        
        # Check account limits
        max_accounts = plan_config.get("max_accounts", 999)
        if current_accounts > max_accounts:
            validation_result["valid"] = False
            validation_result["violations"].append({
                "type": "accounts",
                "current": current_accounts,
                "limit": max_accounts,
                "message": f"Plan allows maximum {max_accounts} accounts"
            })
        
        return validation_result
"""Subscriptions domain Pydantic schemas."""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal
from enum import Enum


class SubscriptionPlan(str, Enum):
    """Subscription plan enumeration."""
    FREE = "free"
    PREMIUM_INDIVIDUAL = "premium_individual"
    PREMIUM_FAMILY = "premium_family"


class SubscriptionStatus(str, Enum):
    """Subscription status enumeration."""
    ACTIVE = "active"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"
    TRIALING = "trialing"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"


class PaymentMethodType(str, Enum):
    """Payment method type enumeration."""
    CARD = "card"
    BANK_ACCOUNT = "bank_account"
    PAYPAL = "paypal"
    OTHER = "other"


class InvoiceStatus(str, Enum):
    """Invoice status enumeration."""
    DRAFT = "draft"
    OPEN = "open"
    PAID = "paid"
    VOID = "void"
    UNCOLLECTIBLE = "uncollectible"


class EventSource(str, Enum):
    """Event source enumeration."""
    STRIPE = "stripe"
    MANUAL = "manual"
    SYSTEM = "system"


class SubscriptionResponse(BaseModel):
    """Schema for subscription responses."""
    id: str = Field(..., description="Subscription unique identifier")
    user_id: str = Field(..., description="Associated user ID")
    stripe_subscription_id: str = Field(..., description="Stripe subscription ID")
    stripe_customer_id: str = Field(..., description="Stripe customer ID")
    stripe_price_id: str = Field(..., description="Stripe price ID")
    plan: SubscriptionPlan = Field(..., description="Subscription plan")
    plan_name: str = Field(..., description="Human-readable plan name")
    status: SubscriptionStatus = Field(..., description="Subscription status")
    current_period_start: datetime = Field(..., description="Current period start")
    current_period_end: datetime = Field(..., description="Current period end")
    trial_start: Optional[datetime] = Field(None, description="Trial start timestamp")
    trial_end: Optional[datetime] = Field(None, description="Trial end timestamp")
    cancel_at_period_end: bool = Field(..., description="Whether subscription cancels at period end")
    canceled_at: Optional[datetime] = Field(None, description="Cancellation timestamp")
    cancellation_reason: Optional[str] = Field(None, description="Cancellation reason")
    amount: Decimal = Field(..., description="Subscription amount")
    currency: str = Field(..., description="Subscription currency")
    interval: str = Field(..., description="Billing interval")
    interval_count: int = Field(..., description="Billing interval count")
    default_payment_method: Optional[str] = Field(None, description="Default payment method ID")
    usage_data: Dict[str, Any] = Field(default_factory=dict, description="Usage data")
    plan_limits: Dict[str, Any] = Field(default_factory=dict, description="Plan limits")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(..., description="Subscription creation timestamp")
    updated_at: datetime = Field(..., description="Subscription last update timestamp")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174021",
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "stripe_subscription_id": "sub_123abc456def",
                "stripe_customer_id": "cus_123abc456def",
                "stripe_price_id": "price_123abc456def",
                "plan": "premium_individual",
                "plan_name": "Premium Individual",
                "status": "active",
                "current_period_start": "2024-01-01T00:00:00Z",
                "current_period_end": "2024-02-01T00:00:00Z",
                "trial_start": "2023-12-25T00:00:00Z",
                "trial_end": "2024-01-01T00:00:00Z",
                "cancel_at_period_end": False,
                "amount": "9.99",
                "currency": "USD",
                "interval": "month",
                "interval_count": 1,
                "usage_data": {
                    "accounts_connected": 5,
                    "transactions_synced": 150,
                    "api_calls_used": 2500
                },
                "plan_limits": {
                    "max_accounts": 10,
                    "max_transactions": 1000,
                    "max_api_calls": 10000
                },
                "created_at": "2023-12-25T00:00:00Z",
                "updated_at": "2024-01-15T12:00:00Z"
            }
        }
    )


class SubscriptionUpdate(BaseModel):
    """Schema for updating subscription."""
    cancel_at_period_end: Optional[bool] = Field(None, description="Update cancellation setting")
    cancellation_reason: Optional[str] = Field(None, description="Cancellation reason")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Updated metadata")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "cancel_at_period_end": True,
                "cancellation_reason": "Switching to family plan"
            }
        }
    )


class SubscriptionInvoiceResponse(BaseModel):
    """Schema for subscription invoice responses."""
    id: str = Field(..., description="Invoice unique identifier")
    subscription_id: str = Field(..., description="Associated subscription ID")
    user_id: str = Field(..., description="Associated user ID")
    stripe_invoice_id: str = Field(..., description="Stripe invoice ID")
    stripe_payment_intent_id: Optional[str] = Field(None, description="Stripe payment intent ID")
    invoice_number: str = Field(..., description="Invoice number")
    amount_due: Decimal = Field(..., description="Amount due")
    amount_paid: Decimal = Field(..., description="Amount paid")
    amount_remaining: Decimal = Field(..., description="Amount remaining")
    status: InvoiceStatus = Field(..., description="Invoice status")
    period_start: datetime = Field(..., description="Billing period start")
    period_end: datetime = Field(..., description="Billing period end")
    due_date: Optional[datetime] = Field(None, description="Invoice due date")
    paid_at: Optional[datetime] = Field(None, description="Payment timestamp")
    currency: str = Field(..., description="Invoice currency")
    hosted_invoice_url: Optional[str] = Field(None, description="Hosted invoice URL")
    invoice_pdf: Optional[str] = Field(None, description="Invoice PDF URL")
    line_items: List[Dict[str, Any]] = Field(default_factory=list, description="Invoice line items")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(..., description="Invoice creation timestamp")
    updated_at: datetime = Field(..., description="Invoice last update timestamp")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174022",
                "subscription_id": "123e4567-e89b-12d3-a456-426614174021",
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "stripe_invoice_id": "in_123abc456def",
                "invoice_number": "FAITHFUL-001",
                "amount_due": "9.99",
                "amount_paid": "9.99",
                "amount_remaining": "0.00",
                "status": "paid",
                "period_start": "2024-01-01T00:00:00Z",
                "period_end": "2024-02-01T00:00:00Z",
                "due_date": "2024-01-01T00:00:00Z",
                "paid_at": "2024-01-01T00:05:00Z",
                "currency": "USD",
                "hosted_invoice_url": "https://invoice.stripe.com/i/123",
                "line_items": [
                    {
                        "description": "Premium Individual Plan",
                        "amount": "9.99",
                        "quantity": 1
                    }
                ],
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:05:00Z"
            }
        }
    )


class SubscriptionEventResponse(BaseModel):
    """Schema for subscription event responses."""
    id: str = Field(..., description="Event unique identifier")
    subscription_id: str = Field(..., description="Associated subscription ID")
    event_type: str = Field(..., description="Event type")
    event_source: EventSource = Field(..., description="Event source")
    stripe_event_id: Optional[str] = Field(None, description="Stripe event ID")
    event_data: Dict[str, Any] = Field(default_factory=dict, description="Event data")
    processed: bool = Field(..., description="Whether event has been processed")
    processed_at: Optional[datetime] = Field(None, description="Processing timestamp")
    error_message: Optional[str] = Field(None, description="Processing error message")
    created_at: datetime = Field(..., description="Event creation timestamp")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174023",
                "subscription_id": "123e4567-e89b-12d3-a456-426614174021",
                "event_type": "customer.subscription.updated",
                "event_source": "stripe",
                "stripe_event_id": "evt_123abc456def",
                "event_data": {
                    "status": "active",
                    "cancel_at_period_end": False
                },
                "processed": True,
                "processed_at": "2024-01-01T00:01:00Z",
                "created_at": "2024-01-01T00:00:00Z"
            }
        }
    )


class PaymentMethodResponse(BaseModel):
    """Schema for payment method responses."""
    id: str = Field(..., description="Payment method unique identifier")
    user_id: str = Field(..., description="Associated user ID")
    stripe_payment_method_id: str = Field(..., description="Stripe payment method ID")
    stripe_customer_id: str = Field(..., description="Stripe customer ID")
    type: PaymentMethodType = Field(..., description="Payment method type")
    card_brand: Optional[str] = Field(None, description="Card brand (if card)")
    card_last4: Optional[str] = Field(None, description="Card last 4 digits (if card)")
    card_exp_month: Optional[int] = Field(None, description="Card expiration month (if card)")
    card_exp_year: Optional[int] = Field(None, description="Card expiration year (if card)")
    bank_name: Optional[str] = Field(None, description="Bank name (if bank account)")
    bank_last4: Optional[str] = Field(None, description="Bank account last 4 digits (if bank account)")
    is_default: bool = Field(..., description="Whether this is the default payment method")
    is_active: bool = Field(..., description="Whether payment method is active")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(..., description="Payment method creation timestamp")
    updated_at: datetime = Field(..., description="Payment method last update timestamp")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174024",
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "stripe_payment_method_id": "pm_123abc456def",
                "stripe_customer_id": "cus_123abc456def",
                "type": "card",
                "card_brand": "visa",
                "card_last4": "4242",
                "card_exp_month": 12,
                "card_exp_year": 2025,
                "is_default": True,
                "is_active": True,
                "created_at": "2023-12-25T00:00:00Z",
                "updated_at": "2023-12-25T00:00:00Z"
            }
        }
    )


class SubscriptionUsageResponse(BaseModel):
    """Schema for subscription usage responses."""
    id: str = Field(..., description="Usage record unique identifier")
    subscription_id: str = Field(..., description="Associated subscription ID")
    user_id: str = Field(..., description="Associated user ID")
    period_start: datetime = Field(..., description="Usage period start")
    period_end: datetime = Field(..., description="Usage period end")
    api_calls: int = Field(..., description="API calls made")
    storage_gb: Decimal = Field(..., description="Storage used in GB")
    transactions_synced: int = Field(..., description="Transactions synced")
    family_members: int = Field(..., description="Family members")
    plaid_connections: int = Field(..., description="Plaid connections")
    budget_count: int = Field(..., description="Number of budgets")
    goal_count: int = Field(..., description="Number of goals")
    usage_data: Dict[str, Any] = Field(default_factory=dict, description="Additional usage data")
    overage_charges: Decimal = Field(..., description="Overage charges")
    created_at: datetime = Field(..., description="Usage record creation timestamp")
    updated_at: datetime = Field(..., description="Usage record last update timestamp")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174025",
                "subscription_id": "123e4567-e89b-12d3-a456-426614174021",
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "period_start": "2024-01-01T00:00:00Z",
                "period_end": "2024-02-01T00:00:00Z",
                "api_calls": 2500,
                "storage_gb": "0.15",
                "transactions_synced": 150,
                "family_members": 1,
                "plaid_connections": 3,
                "budget_count": 2,
                "goal_count": 1,
                "usage_data": {
                    "email_notifications_sent": 5,
                    "reports_generated": 3
                },
                "overage_charges": "0.00",
                "created_at": "2024-02-01T00:00:00Z",
                "updated_at": "2024-02-01T00:00:00Z"
            }
        }
    )


class PlanComparisonResponse(BaseModel):
    """Schema for plan comparison responses."""
    plans: List[Dict[str, Any]] = Field(..., description="Available plans with features")
    current_plan: Optional[str] = Field(None, description="User's current plan")
    recommendations: List[str] = Field(..., description="Plan recommendations")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "plans": [
                    {
                        "id": "free",
                        "name": "Free",
                        "price": "0.00",
                        "interval": "month",
                        "features": {
                            "max_accounts": 2,
                            "max_transactions": 100,
                            "basic_budgeting": True,
                            "family_sharing": False,
                            "priority_support": False
                        }
                    },
                    {
                        "id": "premium_individual",
                        "name": "Premium Individual",
                        "price": "9.99",
                        "interval": "month",
                        "features": {
                            "max_accounts": 10,
                            "max_transactions": 1000,
                            "advanced_budgeting": True,
                            "goals_tracking": True,
                            "family_sharing": False,
                            "priority_support": True
                        }
                    }
                ],
                "current_plan": "free",
                "recommendations": [
                    "Upgrade to Premium Individual for advanced budgeting features",
                    "Consider Premium Family if you have multiple family members"
                ]
            }
        }
    )


class BillingPortalRequest(BaseModel):
    """Schema for billing portal requests."""
    return_url: Optional[str] = Field(None, description="URL to return to after portal session")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "return_url": "https://app.faithfulfinances.com/settings/billing"
            }
        }
    )


class BillingPortalResponse(BaseModel):
    """Schema for billing portal responses."""
    url: str = Field(..., description="Billing portal URL")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "url": "https://billing.stripe.com/p/session_123abc456def"
            }
        }
    )


class CheckoutSessionRequest(BaseModel):
    """Schema for checkout session requests."""
    price_id: str = Field(..., description="Stripe price ID for the plan")
    success_url: str = Field(..., description="URL to redirect on success")
    cancel_url: str = Field(..., description="URL to redirect on cancellation")
    trial_period_days: Optional[int] = Field(None, description="Trial period in days")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "price_id": "price_123abc456def",
                "success_url": "https://app.faithfulfinances.com/welcome",
                "cancel_url": "https://app.faithfulfinances.com/pricing",
                "trial_period_days": 7
            }
        }
    )


class CheckoutSessionResponse(BaseModel):
    """Schema for checkout session responses."""
    session_id: str = Field(..., description="Stripe checkout session ID")
    url: str = Field(..., description="Checkout session URL")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": "cs_123abc456def",
                "url": "https://checkout.stripe.com/pay/cs_123abc456def"
            }
        }
    )


class WebhookEventRequest(BaseModel):
    """Schema for webhook event requests."""
    type: str = Field(..., description="Webhook event type")
    data: Dict[str, Any] = Field(..., description="Webhook event data")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "customer.subscription.updated",
                "data": {
                    "object": {
                        "id": "sub_123abc456def",
                        "status": "active",
                        "cancel_at_period_end": False
                    }
                }
            }
        }
    )
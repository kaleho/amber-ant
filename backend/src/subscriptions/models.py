"""Subscription models for tenant database."""
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Boolean, JSON, Numeric, ForeignKey, Index, Text
from datetime import datetime
from typing import Dict, Any, Optional, TYPE_CHECKING
from decimal import Decimal

from src.database import TenantBase

if TYPE_CHECKING:
    from src.users.models import User


class Subscription(TenantBase):
    """User subscription model for premium plans."""
    __tablename__ = "subscriptions"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    
    # Stripe information
    stripe_subscription_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    stripe_customer_id: Mapped[str] = mapped_column(String(255), index=True)
    stripe_price_id: Mapped[str] = mapped_column(String(255), index=True)
    
    # Subscription plan
    plan: Mapped[str] = mapped_column(String(50), index=True)  # free, premium_individual, premium_family
    plan_name: Mapped[str] = mapped_column(String(100))
    
    # Subscription status
    status: Mapped[str] = mapped_column(String(20), index=True)  # active, cancelled, past_due, unpaid, trialing
    
    # Billing period
    current_period_start: Mapped[datetime] = mapped_column(DateTime, index=True)
    current_period_end: Mapped[datetime] = mapped_column(DateTime, index=True)
    
    # Trial information
    trial_start: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    trial_end: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    
    # Cancellation
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    canceled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Pricing
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))  # Amount in dollars
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    interval: Mapped[str] = mapped_column(String(20))  # month, year
    interval_count: Mapped[int] = mapped_column(default=1)
    
    # Payment method
    default_payment_method: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Usage and limits
    usage_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    plan_limits: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Metadata
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="subscriptions")
    invoices: Mapped[list["SubscriptionInvoice"]] = relationship(
        "SubscriptionInvoice", 
        back_populates="subscription",
        cascade="all, delete-orphan"
    )
    events: Mapped[list["SubscriptionEvent"]] = relationship(
        "SubscriptionEvent", 
        back_populates="subscription",
        cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_subscriptions_user_id", "user_id"),
        Index("idx_subscriptions_stripe_subscription", "stripe_subscription_id"),
        Index("idx_subscriptions_stripe_customer", "stripe_customer_id"),
        Index("idx_subscriptions_plan", "plan"),
        Index("idx_subscriptions_status", "status"),
        Index("idx_subscriptions_current_period_start", "current_period_start"),
        Index("idx_subscriptions_current_period_end", "current_period_end"),
        Index("idx_subscriptions_trial_end", "trial_end"),
        Index("idx_subscriptions_cancel_at_period_end", "cancel_at_period_end"),
        Index("idx_subscriptions_created_at", "created_at"),
    )


class SubscriptionInvoice(TenantBase):
    """Subscription invoice records."""
    __tablename__ = "subscription_invoices"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    subscription_id: Mapped[str] = mapped_column(String(36), ForeignKey("subscriptions.id"), index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    
    # Stripe information
    stripe_invoice_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    stripe_payment_intent_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Invoice details
    invoice_number: Mapped[str] = mapped_column(String(100), index=True)
    amount_due: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    amount_remaining: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    
    # Invoice status
    status: Mapped[str] = mapped_column(String(20), index=True)  # draft, open, paid, void, uncollectible
    
    # Billing period
    period_start: Mapped[datetime] = mapped_column(DateTime)
    period_end: Mapped[datetime] = mapped_column(DateTime)
    
    # Due date and payment
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Currency
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    
    # Invoice URL
    hosted_invoice_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    invoice_pdf: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Line items
    line_items: Mapped[list[Dict[str, Any]]] = mapped_column(JSON, default=list)
    
    # Metadata
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Relationships
    subscription: Mapped["Subscription"] = relationship("Subscription", back_populates="invoices")
    
    # Indexes
    __table_args__ = (
        Index("idx_subscription_invoices_subscription_id", "subscription_id"),
        Index("idx_subscription_invoices_user_id", "user_id"),
        Index("idx_subscription_invoices_stripe_invoice", "stripe_invoice_id"),
        Index("idx_subscription_invoices_number", "invoice_number"),
        Index("idx_subscription_invoices_status", "status"),
        Index("idx_subscription_invoices_due_date", "due_date"),
        Index("idx_subscription_invoices_paid_at", "paid_at"),
        Index("idx_subscription_invoices_created", "created_at"),
    )


class SubscriptionEvent(TenantBase):
    """Subscription lifecycle events and webhooks."""
    __tablename__ = "subscription_events"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    subscription_id: Mapped[str] = mapped_column(String(36), ForeignKey("subscriptions.id"), index=True)
    
    # Event information
    event_type: Mapped[str] = mapped_column(String(50), index=True)
    event_source: Mapped[str] = mapped_column(String(20), default="stripe")  # stripe, manual, system
    
    # Stripe webhook information
    stripe_event_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True)
    
    # Event data
    event_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Processing status
    processed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    subscription: Mapped["Subscription"] = relationship("Subscription", back_populates="events")
    
    # Indexes
    __table_args__ = (
        Index("idx_subscription_events_subscription_id", "subscription_id"),
        Index("idx_subscription_events_type", "event_type"),
        Index("idx_subscription_events_source", "event_source"),
        Index("idx_subscription_events_stripe_event", "stripe_event_id"),
        Index("idx_subscription_events_processed", "processed"),
        Index("idx_subscription_events_created", "created_at"),
    )


class PaymentMethod(TenantBase):
    """User payment methods."""
    __tablename__ = "payment_methods"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    
    # Stripe information
    stripe_payment_method_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    stripe_customer_id: Mapped[str] = mapped_column(String(255), index=True)
    
    # Payment method details
    type: Mapped[str] = mapped_column(String(20), index=True)  # card, bank_account, etc.
    
    # Card information (if applicable)
    card_brand: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    card_last4: Mapped[Optional[str]] = mapped_column(String(4), nullable=True)
    card_exp_month: Mapped[Optional[int]] = mapped_column(nullable=True)
    card_exp_year: Mapped[Optional[int]] = mapped_column(nullable=True)
    
    # Bank account information (if applicable)
    bank_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bank_last4: Mapped[Optional[str]] = mapped_column(String(4), nullable=True)
    
    # Status
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    
    # Metadata
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_payment_methods_user_id", "user_id"),
        Index("idx_payment_methods_stripe_payment_method", "stripe_payment_method_id"),
        Index("idx_payment_methods_stripe_customer", "stripe_customer_id"),
        Index("idx_payment_methods_type", "type"),
        Index("idx_payment_methods_default", "is_default"),
        Index("idx_payment_methods_active", "is_active"),
    )


class SubscriptionUsage(TenantBase):
    """Track usage-based subscription metrics."""
    __tablename__ = "subscription_usage"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    subscription_id: Mapped[str] = mapped_column(String(36), ForeignKey("subscriptions.id"), index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    
    # Usage period
    period_start: Mapped[datetime] = mapped_column(DateTime, index=True)
    period_end: Mapped[datetime] = mapped_column(DateTime, index=True)
    
    # Usage metrics
    api_calls: Mapped[int] = mapped_column(default=0)
    storage_gb: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    transactions_synced: Mapped[int] = mapped_column(default=0)
    family_members: Mapped[int] = mapped_column(default=1)
    
    # Feature usage
    plaid_connections: Mapped[int] = mapped_column(default=0)
    budget_count: Mapped[int] = mapped_column(default=0)
    goal_count: Mapped[int] = mapped_column(default=0)
    
    # Usage limits and overages
    usage_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    overage_charges: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Relationships
    subscription: Mapped["Subscription"] = relationship("Subscription")
    
    # Indexes
    __table_args__ = (
        Index("idx_subscription_usage_subscription_id", "subscription_id"),
        Index("idx_subscription_usage_user_id", "user_id"),
        Index("idx_subscription_usage_period_start", "period_start"),
        Index("idx_subscription_usage_period_end", "period_end"),
        # Composite indexes
        Index("idx_subscription_usage_subscription_period", "subscription_id", "period_start", "period_end"),
    )


class SubscriptionDiscount(TenantBase):
    """Subscription discounts and promotions."""
    __tablename__ = "subscription_discounts"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    subscription_id: Mapped[str] = mapped_column(String(36), ForeignKey("subscriptions.id"), index=True)
    
    # Stripe information
    stripe_coupon_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    stripe_promotion_code: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Discount information
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Discount type and amount
    discount_type: Mapped[str] = mapped_column(String(20))  # percentage, amount
    discount_value: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    
    # Validity period
    start_date: Mapped[datetime] = mapped_column(DateTime)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Usage limits
    max_redemptions: Mapped[Optional[int]] = mapped_column(nullable=True)
    times_redeemed: Mapped[int] = mapped_column(default=0)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    subscription: Mapped["Subscription"] = relationship("Subscription")
    
    # Indexes
    __table_args__ = (
        Index("idx_subscription_discounts_subscription_id", "subscription_id"),
        Index("idx_subscription_discounts_coupon", "stripe_coupon_id"),
        Index("idx_subscription_discounts_promo_code", "stripe_promotion_code"),
        Index("idx_subscription_discounts_active", "is_active"),
        Index("idx_subscription_discounts_start_date", "start_date"),
        Index("idx_subscription_discounts_end_date", "end_date"),
    )
"""Tithing models for tenant database."""
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Boolean, JSON, Numeric, ForeignKey, Index, Text, Date
from datetime import datetime, date
from typing import Dict, Any, Optional, TYPE_CHECKING
from decimal import Decimal

from src.database import TenantBase

if TYPE_CHECKING:
    from src.users.models import User


class TithingPayment(TenantBase):
    """Tithing payment records."""
    __tablename__ = "tithing_payments"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    
    # Payment details
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    date: Mapped[date] = mapped_column(Date, index=True)
    
    # Payment method and recipient
    method: Mapped[str] = mapped_column(String(20), index=True)  # cash, check, online, auto_transfer, other
    recipient: Mapped[str] = mapped_column(String(100), index=True)  # Church or organization name
    recipient_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Payment reference
    reference_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    transaction_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    
    # Notes and metadata
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    purpose: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # regular_tithe, special_offering, etc.
    
    # Currency
    iso_currency_code: Mapped[str] = mapped_column(String(3), default="USD")
    
    # Verification status
    is_verified: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    verification_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Tax information
    is_tax_deductible: Mapped[bool] = mapped_column(Boolean, default=True)
    receipt_issued: Mapped[bool] = mapped_column(Boolean, default=False)
    receipt_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Metadata
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="tithing_payments")
    
    # Indexes
    __table_args__ = (
        Index("idx_tithing_payments_user_id", "user_id"),
        Index("idx_tithing_payments_date", "date"),
        Index("idx_tithing_payments_method", "method"),
        Index("idx_tithing_payments_recipient", "recipient"),
        Index("idx_tithing_payments_transaction", "transaction_id"),
        Index("idx_tithing_payments_verified", "is_verified"),
        Index("idx_tithing_payments_tax_deductible", "is_tax_deductible"),
        # Composite indexes
        Index("idx_tithing_payments_user_date", "user_id", "date"),
        Index("idx_tithing_payments_user_recipient", "user_id", "recipient"),
    )


class TithingSchedule(TenantBase):
    """Scheduled/recurring tithing payments."""
    __tablename__ = "tithing_schedules"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    
    # Schedule information
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Payment details
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    percentage: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)  # If percentage-based
    
    # Schedule configuration
    frequency: Mapped[str] = mapped_column(String(20), index=True)  # weekly, biweekly, monthly, yearly
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Payment method and recipient
    method: Mapped[str] = mapped_column(String(20))
    recipient: Mapped[str] = mapped_column(String(100))
    source_account_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    # Schedule status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    auto_process: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Execution tracking
    last_executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    next_execution_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    execution_count: Mapped[int] = mapped_column(default=0)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_tithing_schedules_user_id", "user_id"),
        Index("idx_tithing_schedules_frequency", "frequency"),
        Index("idx_tithing_schedules_active", "is_active"),
        Index("idx_tithing_schedules_next_execution", "next_execution_date"),
        Index("idx_tithing_schedules_auto_process", "auto_process"),
    )


class TithingSummary(TenantBase):
    """Annual tithing summaries and calculations."""
    __tablename__ = "tithing_summaries"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    
    # Summary period
    year: Mapped[int] = mapped_column(index=True)
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)
    
    # Income calculations
    total_income: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    tithing_eligible_income: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    
    # Tithing calculations
    total_tithe_due: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    total_tithe_paid: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    balance: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)  # paid - due
    
    # Percentages
    current_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)  # actual %
    target_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=10)  # target %
    
    # Payment statistics
    payment_count: Mapped[int] = mapped_column(default=0)
    average_payment: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    largest_payment: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    
    # Income source breakdown
    income_sources: Mapped[Dict[str, Decimal]] = mapped_column(JSON, default=dict)
    payment_methods: Mapped[Dict[str, Decimal]] = mapped_column(JSON, default=dict)
    recipients: Mapped[Dict[str, Decimal]] = mapped_column(JSON, default=dict)
    
    # Summary status
    is_final: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    last_calculated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
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
        Index("idx_tithing_summaries_user_id", "user_id"),
        Index("idx_tithing_summaries_year", "year"),
        Index("idx_tithing_summaries_final", "is_final"),
        Index("idx_tithing_summaries_calculated", "last_calculated_at"),
        # Composite indexes
        Index("idx_tithing_summaries_user_year", "user_id", "year"),
        # Ensure unique user-year combinations
        Index("idx_tithing_summaries_unique", "user_id", "year", unique=True),
    )


class TithingGoal(TenantBase):
    """Tithing goals and commitments."""
    __tablename__ = "tithing_goals"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    
    # Goal information
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Goal period
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    
    # Goal targets
    target_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=10)
    target_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    
    # Goal progress
    current_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    current_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    
    # Goal status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Goal reminders
    reminder_frequency: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    last_reminder_sent: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_tithing_goals_user_id", "user_id"),
        Index("idx_tithing_goals_active", "is_active"),
        Index("idx_tithing_goals_completed", "is_completed"),
        Index("idx_tithing_goals_start_date", "start_date"),
        Index("idx_tithing_goals_end_date", "end_date"),
    )
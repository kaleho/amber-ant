"""Account models for tenant database."""
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Boolean, JSON, Numeric, ForeignKey, Index, Text
from datetime import datetime
from typing import Dict, Any, Optional, TYPE_CHECKING
from decimal import Decimal

from src.database import TenantBase

if TYPE_CHECKING:
    from src.users.models import User
    from src.transactions.models import Transaction
    from src.plaid.models import PlaidItem, PlaidAccount


class Account(TenantBase):
    """Financial account model."""
    __tablename__ = "accounts"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    
    # Plaid information
    plaid_account_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True, index=True)
    plaid_item_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    
    # Account information
    name: Mapped[str] = mapped_column(String(255))
    official_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    type: Mapped[str] = mapped_column(String(50), index=True)  # depository, credit, loan, investment, other
    subtype: Mapped[str] = mapped_column(String(50), index=True)  # checking, savings, credit card, etc.
    
    # Account identifiers
    mask: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    institution_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    institution_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Balance information (stored as JSON for flexibility)
    balance_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Computed balances (for easier querying)
    current_balance: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    available_balance: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    credit_limit: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    
    # Currency and locale
    iso_currency_code: Mapped[str] = mapped_column(String(3), default="USD")
    
    # Account status and metadata
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_manual: Mapped[bool] = mapped_column(Boolean, default=False)  # Manual vs Plaid account
    sync_status: Mapped[str] = mapped_column(String(20), default="active")  # active, error, stopped
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    sync_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Additional metadata
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="accounts")
    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction", 
        back_populates="account",
        cascade="all, delete-orphan"
    )
    balance_history: Mapped[list["AccountBalanceHistory"]] = relationship(
        "AccountBalanceHistory", 
        back_populates="account",
        cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_accounts_user_id", "user_id"),
        Index("idx_accounts_plaid_account_id", "plaid_account_id"),
        Index("idx_accounts_plaid_item_id", "plaid_item_id"),
        Index("idx_accounts_type", "type"),
        Index("idx_accounts_subtype", "subtype"),
        Index("idx_accounts_active", "is_active"),
        Index("idx_accounts_sync_status", "sync_status"),
        Index("idx_accounts_last_sync", "last_sync_at"),
    )


class AccountBalanceHistory(TenantBase):
    """Historical account balance tracking."""
    __tablename__ = "account_balance_history"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), index=True)
    
    # Balance information
    current_balance: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    available_balance: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    credit_limit: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    
    # Balance details
    balance_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    iso_currency_code: Mapped[str] = mapped_column(String(3), default="USD")
    
    # Timestamp and source
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    source: Mapped[str] = mapped_column(String(20), default="plaid")  # plaid, manual, system
    
    # Relationships
    account: Mapped["Account"] = relationship("Account", back_populates="balance_history")
    
    # Indexes
    __table_args__ = (
        Index("idx_account_balance_history_account_id", "account_id"),
        Index("idx_account_balance_history_recorded_at", "recorded_at"),
        Index("idx_account_balance_history_source", "source"),
        Index("idx_account_balance_history_composite", "account_id", "recorded_at"),
    )


class AccountCategory(TenantBase):
    """Custom account categories and tags."""
    __tablename__ = "account_categories"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    
    # Category information
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)  # Hex color
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Category metadata
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_account_categories_user_id", "user_id"),
        Index("idx_account_categories_name", "name"),
        Index("idx_account_categories_system", "is_system"),
    )


class AccountAlert(TenantBase):
    """Account-based alerts and notifications."""
    __tablename__ = "account_alerts"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    
    # Alert configuration
    alert_type: Mapped[str] = mapped_column(String(50), index=True)  # low_balance, high_spending, etc.
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Alert conditions
    conditions: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    threshold_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    
    # Alert status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_triggered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    trigger_count: Mapped[int] = mapped_column(default=0)
    
    # Notification preferences
    notify_email: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_push: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_sms: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_account_alerts_account_id", "account_id"),
        Index("idx_account_alerts_user_id", "user_id"),
        Index("idx_account_alerts_type", "alert_type"),
        Index("idx_account_alerts_active", "is_active"),
    )


class AccountSyncLog(TenantBase):
    """Account synchronization logs."""
    __tablename__ = "account_sync_logs"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), index=True)
    
    # Sync information
    sync_type: Mapped[str] = mapped_column(String(20), index=True)  # full, incremental, balance_only
    status: Mapped[str] = mapped_column(String(20), index=True)  # success, error, partial
    
    # Sync results
    transactions_added: Mapped[int] = mapped_column(default=0)
    transactions_updated: Mapped[int] = mapped_column(default=0)
    balance_updated: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Error information
    error_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timing information
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(nullable=True)
    
    # Additional data
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Relationships
    account: Mapped["Account"] = relationship("Account")
    
    # Indexes
    __table_args__ = (
        Index("idx_account_sync_logs_account_id", "account_id"),
        Index("idx_account_sync_logs_status", "status"),
        Index("idx_account_sync_logs_started_at", "started_at"),
        Index("idx_account_sync_logs_sync_type", "sync_type"),
    )
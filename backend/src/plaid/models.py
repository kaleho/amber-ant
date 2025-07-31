"""Plaid integration models for tenant database."""
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Boolean, JSON, Text, ForeignKey, Index
from datetime import datetime
from typing import Dict, Any, Optional, TYPE_CHECKING

from src.database import TenantBase

if TYPE_CHECKING:
    from src.users.models import User
    from src.accounts.models import Account


class PlaidItem(TenantBase):
    """Plaid Item represents a user's connection to a financial institution."""
    __tablename__ = "plaid_items"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    
    # Plaid identifiers
    plaid_item_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    plaid_access_token: Mapped[str] = mapped_column(Text)  # Encrypted
    
    # Institution information
    institution_id: Mapped[str] = mapped_column(String(255), index=True)
    institution_name: Mapped[str] = mapped_column(String(255))
    institution_color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    institution_logo: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    institution_website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Connection status
    status: Mapped[str] = mapped_column(String(20), default="good", index=True)  # good, bad, requires_update
    error_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Plaid products enabled
    products: Mapped[list[str]] = mapped_column(JSON, default=list)
    available_products: Mapped[list[str]] = mapped_column(JSON, default=list)
    billed_products: Mapped[list[str]] = mapped_column(JSON, default=list)
    
    # Webhook configuration
    webhook_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Connection metadata
    consent_expiration_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    update_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Sync information
    last_successful_sync: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_sync_attempt: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    consecutive_failed_syncs: Mapped[int] = mapped_column(default=0)
    
    # Item metadata
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User")
    accounts: Mapped[list["PlaidAccount"]] = relationship(
        "PlaidAccount", 
        back_populates="item",
        cascade="all, delete-orphan"
    )
    webhooks: Mapped[list["PlaidWebhook"]] = relationship(
        "PlaidWebhook", 
        back_populates="item",
        cascade="all, delete-orphan"
    )
    sync_logs: Mapped[list["PlaidSyncLog"]] = relationship(
        "PlaidSyncLog", 
        back_populates="item",
        cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_plaid_items_user_id", "user_id"),
        Index("idx_plaid_items_plaid_item_id", "plaid_item_id"),
        Index("idx_plaid_items_institution_id", "institution_id"),
        Index("idx_plaid_items_status", "status"),
        Index("idx_plaid_items_last_sync", "last_successful_sync"),
        Index("idx_plaid_items_created", "created_at"),
    )


class PlaidAccount(TenantBase):
    """Plaid Account information linked to our Account model."""
    __tablename__ = "plaid_accounts"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    item_id: Mapped[str] = mapped_column(String(36), ForeignKey("plaid_items.id"), index=True)
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), index=True)
    
    # Plaid identifiers
    plaid_account_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    
    # Account information from Plaid
    name: Mapped[str] = mapped_column(String(255))
    official_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    type: Mapped[str] = mapped_column(String(50))
    subtype: Mapped[str] = mapped_column(String(50))
    
    # Account verification
    verification_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Balance information
    balance_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Account metadata
    plaid_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Sync configuration
    sync_transactions: Mapped[bool] = mapped_column(Boolean, default=True)
    sync_balance: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Relationships
    item: Mapped["PlaidItem"] = relationship("PlaidItem", back_populates="accounts")
    account: Mapped["Account"] = relationship("Account")
    
    # Indexes
    __table_args__ = (
        Index("idx_plaid_accounts_item_id", "item_id"),
        Index("idx_plaid_accounts_account_id", "account_id"),
        Index("idx_plaid_accounts_plaid_account_id", "plaid_account_id"),
        Index("idx_plaid_accounts_active", "is_active"),
        # Ensure unique plaid_account_id per item
        Index("idx_plaid_accounts_unique", "item_id", "plaid_account_id", unique=True),
    )


class PlaidWebhook(TenantBase):
    """Plaid webhook events and processing."""
    __tablename__ = "plaid_webhooks"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    item_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("plaid_items.id"), nullable=True, index=True)
    
    # Webhook information
    webhook_type: Mapped[str] = mapped_column(String(50), index=True)
    webhook_code: Mapped[str] = mapped_column(String(50), index=True)
    
    # Plaid identifiers
    plaid_item_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    
    # Webhook payload
    payload: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    headers: Mapped[Dict[str, str]] = mapped_column(JSON, default=dict)
    
    # Processing status
    processed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    processing_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(default=0)
    
    # Webhook verification
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    verification_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    item: Mapped[Optional["PlaidItem"]] = relationship("PlaidItem", back_populates="webhooks")
    
    # Indexes
    __table_args__ = (
        Index("idx_plaid_webhooks_item_id", "item_id"),
        Index("idx_plaid_webhooks_type", "webhook_type"),
        Index("idx_plaid_webhooks_code", "webhook_code"),
        Index("idx_plaid_webhooks_plaid_item_id", "plaid_item_id"),
        Index("idx_plaid_webhooks_processed", "processed"),
        Index("idx_plaid_webhooks_verified", "is_verified"),
        Index("idx_plaid_webhooks_received", "received_at"),
        # Composite index for common queries
        Index("idx_plaid_webhooks_type_code", "webhook_type", "webhook_code"),
    )


class PlaidSyncLog(TenantBase):
    """Plaid synchronization logs and history."""
    __tablename__ = "plaid_sync_logs"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    item_id: Mapped[str] = mapped_column(String(36), ForeignKey("plaid_items.id"), index=True)
    
    # Sync information
    sync_type: Mapped[str] = mapped_column(String(20), index=True)  # transactions, accounts, balance
    sync_status: Mapped[str] = mapped_column(String(20), index=True)  # success, error, partial
    
    # Sync results
    records_processed: Mapped[int] = mapped_column(default=0)
    records_added: Mapped[int] = mapped_column(default=0)
    records_updated: Mapped[int] = mapped_column(default=0)
    records_removed: Mapped[int] = mapped_column(default=0)
    
    # Error information
    error_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    error_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timing information
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(nullable=True)
    
    # Sync details
    cursor: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    has_more: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Additional metadata
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    plaid_request_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Relationships
    item: Mapped["PlaidItem"] = relationship("PlaidItem", back_populates="sync_logs")
    
    # Indexes
    __table_args__ = (
        Index("idx_plaid_sync_logs_item_id", "item_id"),
        Index("idx_plaid_sync_logs_type", "sync_type"),
        Index("idx_plaid_sync_logs_status", "sync_status"),
        Index("idx_plaid_sync_logs_started", "started_at"),
        Index("idx_plaid_sync_logs_completed", "completed_at"),
        # Composite indexes
        Index("idx_plaid_sync_logs_item_type", "item_id", "sync_type"),
        Index("idx_plaid_sync_logs_item_started", "item_id", "started_at"),
    )


class PlaidLinkToken(TenantBase):
    """Plaid Link tokens for account connection."""
    __tablename__ = "plaid_link_tokens"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    
    # Link token information
    link_token: Mapped[str] = mapped_column(Text)  # The actual token (encrypted)
    request_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    
    # Token configuration
    products: Mapped[list[str]] = mapped_column(JSON, default=list)
    country_codes: Mapped[list[str]] = mapped_column(JSON, default=list)
    
    # Token status
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Token expiration
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    
    # Update mode (for reconnection)
    update_mode: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    account_filters: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Result tracking
    public_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    item_id_created: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    # Metadata
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index("idx_plaid_link_tokens_user_id", "user_id"),
        Index("idx_plaid_link_tokens_request_id", "request_id"),
        Index("idx_plaid_link_tokens_used", "is_used"),
        Index("idx_plaid_link_tokens_expires", "expires_at"),
        Index("idx_plaid_link_tokens_created", "created_at"),
    )


class PlaidError(TenantBase):
    """Plaid API errors and handling."""
    __tablename__ = "plaid_errors"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    item_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("plaid_items.id"), nullable=True, index=True)
    
    # Error classification
    error_type: Mapped[str] = mapped_column(String(50), index=True)  # ITEM_ERROR, INVALID_REQUEST, etc.
    error_code: Mapped[str] = mapped_column(String(50), index=True)
    error_message: Mapped[str] = mapped_column(Text)
    
    # Error context
    endpoint: Mapped[str] = mapped_column(String(100), index=True)
    request_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Error resolution
    suggested_action: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    requires_user_action: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Error frequency
    occurrence_count: Mapped[int] = mapped_column(default=1)
    first_occurred_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_occurred_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Additional data
    error_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Indexes
    __table_args__ = (
        Index("idx_plaid_errors_user_id", "user_id"),
        Index("idx_plaid_errors_item_id", "item_id"),
        Index("idx_plaid_errors_type", "error_type"),
        Index("idx_plaid_errors_code", "error_code"),
        Index("idx_plaid_errors_endpoint", "endpoint"),
        Index("idx_plaid_errors_requires_action", "requires_user_action"),
        Index("idx_plaid_errors_resolved", "is_resolved"),
        Index("idx_plaid_errors_first_occurred", "first_occurred_at"),
        Index("idx_plaid_errors_last_occurred", "last_occurred_at"),
    )
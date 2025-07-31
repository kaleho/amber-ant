"""Transaction models for tenant database."""
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Boolean, JSON, Numeric, ForeignKey, Index, Text, Date
from datetime import datetime, date
from typing import Dict, Any, Optional, TYPE_CHECKING
from decimal import Decimal

from src.database import TenantBase

if TYPE_CHECKING:
    from src.users.models import User
    from src.accounts.models import Account


class Transaction(TenantBase):
    """Transaction model with dual categorization system."""
    __tablename__ = "transactions"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), index=True)
    
    # Plaid information
    plaid_transaction_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True, index=True)
    
    # Transaction basics
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2))  # Positive for debits/expenses
    iso_currency_code: Mapped[str] = mapped_column(String(3), default="USD")
    
    # Transaction dates
    date: Mapped[date] = mapped_column(Date, index=True)
    authorized_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    datetime: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Transaction description
    name: Mapped[str] = mapped_column(String(255), index=True)
    merchant_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    original_description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Plaid categorization
    plaid_category: Mapped[str] = mapped_column(String(100), index=True)
    plaid_category_detailed: Mapped[list[str]] = mapped_column(JSON, default=list)
    plaid_category_confidence: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Dual categorization system (Biblical stewardship focus)
    app_expense_type: Mapped[str] = mapped_column(String(20), index=True)  # fixed, discretionary, split
    custom_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    
    # Transaction splitting
    is_split: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    parent_transaction_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    split_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Location information
    location_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # User annotations
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    
    # Tithing and stewardship
    is_tithing_income: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_charitable_giving: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    
    # Transaction status
    is_pending: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_manual: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_transfer: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    
    # Account information (denormalized for performance)
    account_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    account_subtype: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Additional metadata
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    sync_source: Mapped[str] = mapped_column(String(20), default="plaid")  # plaid, manual, import
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User")
    account: Mapped["Account"] = relationship("Account", back_populates="transactions")
    split_transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction",
        primaryjoin="Transaction.id == Transaction.parent_transaction_id",
        remote_side="Transaction.parent_transaction_id",
        cascade="all, delete-orphan"
    )
    enrichment: Mapped[Optional["TransactionEnrichment"]] = relationship(
        "TransactionEnrichment",
        back_populates="transaction",
        uselist=False,
        cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_transactions_user_id", "user_id"),
        Index("idx_transactions_account_id", "account_id"),
        Index("idx_transactions_plaid_id", "plaid_transaction_id"),
        Index("idx_transactions_date", "date"),
        Index("idx_transactions_amount", "amount"),
        Index("idx_transactions_merchant", "merchant_name"),
        Index("idx_transactions_plaid_category", "plaid_category"),
        Index("idx_transactions_expense_type", "app_expense_type"),
        Index("idx_transactions_custom_category", "custom_category"),
        Index("idx_transactions_is_split", "is_split"),
        Index("idx_transactions_parent_id", "parent_transaction_id"),
        Index("idx_transactions_tithing_income", "is_tithing_income"),
        Index("idx_transactions_charitable", "is_charitable_giving"),
        Index("idx_transactions_pending", "is_pending"),
        Index("idx_transactions_manual", "is_manual"),
        Index("idx_transactions_hidden", "is_hidden"),
        Index("idx_transactions_transfer", "is_transfer"),
        Index("idx_transactions_created_at", "created_at"),
        # Composite indexes for common queries
        Index("idx_transactions_user_date", "user_id", "date"),
        Index("idx_transactions_account_date", "account_id", "date"),
        Index("idx_transactions_user_category", "user_id", "plaid_category"),
        Index("idx_transactions_user_expense_type", "user_id", "app_expense_type"),
    )


class TransactionEnrichment(TenantBase):
    """Enhanced transaction information from external sources."""
    __tablename__ = "transaction_enrichments"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    transaction_id: Mapped[str] = mapped_column(String(36), ForeignKey("transactions.id"), unique=True, index=True)
    
    # Merchant enrichment
    merchant_logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    merchant_website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    merchant_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Location enrichment
    location_address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    location_city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    location_region: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    location_postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    location_country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    location_coordinates: Mapped[Optional[Dict[str, float]]] = mapped_column(JSON, nullable=True)
    
    # Category enrichment
    suggested_categories: Mapped[list[str]] = mapped_column(JSON, default=list)
    category_confidence: Mapped[Optional[float]] = mapped_column(nullable=True)
    
    # Receipt and document attachments
    receipt_urls: Mapped[list[str]] = mapped_column(JSON, default=list)
    document_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    
    # External IDs and references
    external_ids: Mapped[Dict[str, str]] = mapped_column(JSON, default=dict)
    
    # Enrichment metadata
    enrichment_source: Mapped[str] = mapped_column(String(50), default="system")
    enrichment_confidence: Mapped[Optional[float]] = mapped_column(nullable=True)
    last_enriched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Relationships
    transaction: Mapped["Transaction"] = relationship("Transaction", back_populates="enrichment")
    
    # Indexes
    __table_args__ = (
        Index("idx_transaction_enrichments_transaction_id", "transaction_id"),
        Index("idx_transaction_enrichments_source", "enrichment_source"),
        Index("idx_transaction_enrichments_last_enriched", "last_enriched_at"),
    )


class TransactionRule(TenantBase):
    """Rules for automatic transaction categorization."""
    __tablename__ = "transaction_rules"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    
    # Rule information
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Rule conditions
    conditions: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    match_type: Mapped[str] = mapped_column(String(10), default="all")  # all, any
    
    # Rule actions
    actions: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Rule metadata
    priority: Mapped[int] = mapped_column(default=0, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    apply_to_existing: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Usage statistics  
    match_count: Mapped[int] = mapped_column(default=0)
    last_matched_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_transaction_rules_user_id", "user_id"),
        Index("idx_transaction_rules_priority", "priority"),
        Index("idx_transaction_rules_active", "is_active"),
        Index("idx_transaction_rules_last_matched", "last_matched_at"),
    )


class TransactionReceipt(TenantBase):
    """Receipt and document attachments for transactions."""
    __tablename__ = "transaction_receipts"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    transaction_id: Mapped[str] = mapped_column(String(36), ForeignKey("transactions.id"), index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    
    # File information
    filename: Mapped[str] = mapped_column(String(255))
    original_filename: Mapped[str] = mapped_column(String(255))
    file_size: Mapped[int] = mapped_column()
    file_type: Mapped[str] = mapped_column(String(50))
    mime_type: Mapped[str] = mapped_column(String(100))
    
    # Storage information
    storage_path: Mapped[str] = mapped_column(String(500))
    storage_provider: Mapped[str] = mapped_column(String(50), default="local")
    
    # Receipt processing
    ocr_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extracted_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    processing_status: Mapped[str] = mapped_column(String(20), default="pending")
    
    # Metadata
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Relationships
    transaction: Mapped["Transaction"] = relationship("Transaction")
    
    # Indexes
    __table_args__ = (
        Index("idx_transaction_receipts_transaction_id", "transaction_id"),
        Index("idx_transaction_receipts_user_id", "user_id"),
        Index("idx_transaction_receipts_status", "processing_status"),
        Index("idx_transaction_receipts_created_at", "created_at"),
    )
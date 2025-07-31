"""Budget models for tenant database."""
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Boolean, JSON, Numeric, ForeignKey, Index, Text, Date
from datetime import datetime, date
from typing import Dict, Any, Optional, TYPE_CHECKING
from decimal import Decimal

from src.database import TenantBase

if TYPE_CHECKING:
    from src.users.models import User


class Budget(TenantBase):
    """Budget model with persona-appropriate categories."""
    __tablename__ = "budgets"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    
    # Budget basics
    name: Mapped[str] = mapped_column(String(100), index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Budget period
    period: Mapped[str] = mapped_column(String(20), default="monthly", index=True)  # monthly, weekly, semester
    start_date: Mapped[date] = mapped_column(Date, index=True)
    end_date: Mapped[date] = mapped_column(Date, index=True)
    
    # Budget totals (computed from categories)
    total_budget: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    total_spent: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    total_remaining: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    
    # Budget status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_template: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    
    # Auto-update settings
    auto_rollover: Mapped[bool] = mapped_column(Boolean, default=True)
    rollover_unused: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Persona-specific settings
    persona_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    
    # Metadata
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="budgets")
    categories: Mapped[list["BudgetCategory"]] = relationship(
        "BudgetCategory", 
        back_populates="budget",
        cascade="all, delete-orphan"
    )
    alerts: Mapped[list["BudgetAlert"]] = relationship(
        "BudgetAlert", 
        back_populates="budget",
        cascade="all, delete-orphan"
    )
    snapshots: Mapped[list["BudgetSnapshot"]] = relationship(
        "BudgetSnapshot", 
        back_populates="budget",
        cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_budgets_user_id", "user_id"),
        Index("idx_budgets_name", "name"),
        Index("idx_budgets_period", "period"),
        Index("idx_budgets_start_date", "start_date"),
        Index("idx_budgets_end_date", "end_date"),
        Index("idx_budgets_active", "is_active"),
        Index("idx_budgets_template", "is_template"),
        Index("idx_budgets_persona", "persona_type"),
        # Composite indexes
        Index("idx_budgets_user_period", "user_id", "period"),
        Index("idx_budgets_user_dates", "user_id", "start_date", "end_date"),
    )


class BudgetCategory(TenantBase):
    """Budget category with dual expense type classification."""
    __tablename__ = "budget_categories"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    budget_id: Mapped[str] = mapped_column(String(36), ForeignKey("budgets.id"), index=True)
    
    # Category information
    category: Mapped[str] = mapped_column(String(100), index=True)  # Plaid category
    custom_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Dual expense type (Biblical stewardship)
    expense_type: Mapped[str] = mapped_column(String(20), index=True)  # fixed, discretionary
    
    # Budget amounts
    budgeted_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    spent_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    remaining_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    
    # Category settings
    rollover_from_previous: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    alert_threshold: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)  # Percentage
    
    # Visual and organizational
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)  # Hex color
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sort_order: Mapped[int] = mapped_column(default=0)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Relationships
    budget: Mapped["Budget"] = relationship("Budget", back_populates="categories")
    
    # Indexes
    __table_args__ = (
        Index("idx_budget_categories_budget_id", "budget_id"),
        Index("idx_budget_categories_category", "category"),
        Index("idx_budget_categories_expense_type", "expense_type"),
        Index("idx_budget_categories_sort_order", "sort_order"),
        # Composite indexes
        Index("idx_budget_categories_budget_category", "budget_id", "category"),
        Index("idx_budget_categories_budget_expense_type", "budget_id", "expense_type"),
    )


class BudgetAlert(TenantBase):
    """Budget alerts and notifications."""
    __tablename__ = "budget_alerts"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    budget_id: Mapped[str] = mapped_column(String(36), ForeignKey("budgets.id"), index=True)
    category_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    
    # Alert configuration
    alert_type: Mapped[str] = mapped_column(String(50), index=True)  # overspend, approaching_limit, etc.
    name: Mapped[str] = mapped_column(String(100))
    
    # Alert conditions
    threshold_type: Mapped[str] = mapped_column(String(20))  # percentage, amount
    threshold_value: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    
    # Alert status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
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
    
    # Relationships
    budget: Mapped["Budget"] = relationship("Budget", back_populates="alerts")
    
    # Indexes
    __table_args__ = (
        Index("idx_budget_alerts_budget_id", "budget_id"),
        Index("idx_budget_alerts_category_id", "category_id"),
        Index("idx_budget_alerts_type", "alert_type"),
        Index("idx_budget_alerts_active", "is_active"),
        Index("idx_budget_alerts_last_triggered", "last_triggered_at"),
    )


class BudgetSnapshot(TenantBase):
    """Daily snapshots of budget progress."""
    __tablename__ = "budget_snapshots"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    budget_id: Mapped[str] = mapped_column(String(36), ForeignKey("budgets.id"), index=True)
    
    # Snapshot date
    snapshot_date: Mapped[date] = mapped_column(Date, index=True)
    
    # Budget totals at snapshot time
    total_budget: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    total_spent: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    total_remaining: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    
    # Category-level data
    category_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    budget: Mapped["Budget"] = relationship("Budget", back_populates="snapshots")
    
    # Indexes
    __table_args__ = (
        Index("idx_budget_snapshots_budget_id", "budget_id"),
        Index("idx_budget_snapshots_date", "snapshot_date"),
        Index("idx_budget_snapshots_created", "created_at"),
        # Composite indexes
        Index("idx_budget_snapshots_budget_date", "budget_id", "snapshot_date"),
    )


class BudgetTemplate(TenantBase):
    """Budget templates for quick budget creation."""
    __tablename__ = "budget_templates"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    
    # Template information
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Template configuration
    persona_types: Mapped[list[str]] = mapped_column(JSON, default=list)
    period: Mapped[str] = mapped_column(String(20), default="monthly")
    
    # Template data
    template_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Usage statistics
    use_count: Mapped[int] = mapped_column(default=0)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Template metadata
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_budget_templates_user_id", "user_id"),
        Index("idx_budget_templates_name", "name"),
        Index("idx_budget_templates_system", "is_system"),
        Index("idx_budget_templates_public", "is_public"),
        Index("idx_budget_templates_use_count", "use_count"),
    )
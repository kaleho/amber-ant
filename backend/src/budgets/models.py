"""Budget management models."""
from datetime import datetime, date
from typing import Optional
from decimal import Decimal
from sqlalchemy import String, Boolean, DateTime, Date, Numeric, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum

from src.database import TenantBase


class BudgetPeriod(str, enum.Enum):
    """Budget period types."""
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class BudgetStatus(str, enum.Enum):
    """Budget status types."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    COMPLETED = "completed"
    PAUSED = "paused"


class AlertType(str, enum.Enum):
    """Budget alert types."""
    WARNING = "warning"
    CRITICAL = "critical"
    EXCEEDED = "exceeded"


class Budget(TenantBase):
    """Main budget model."""
    
    __tablename__ = "budgets"
    
    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    
    # Basic information
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Budget amounts
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    spent_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    remaining_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    
    # Time period
    period_type: Mapped[BudgetPeriod] = mapped_column(SQLEnum(BudgetPeriod), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Status and settings
    status: Mapped[BudgetStatus] = mapped_column(SQLEnum(BudgetStatus), default=BudgetStatus.ACTIVE)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    auto_rollover: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Alert thresholds (percentages)
    warning_threshold: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=75, nullable=False)
    critical_threshold: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=90, nullable=False)
    
    # Ownership
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    created_by: Mapped[str] = mapped_column(String(36), nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
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
    
    def __repr__(self):
        return f"<Budget(id={self.id}, name={self.name}, total_amount={self.total_amount})>"
    
    @property
    def utilization_percentage(self) -> Decimal:
        """Calculate budget utilization as percentage."""
        if self.total_amount == 0:
            return Decimal(0)
        return (self.spent_amount / self.total_amount) * 100
    
    @property
    def is_over_budget(self) -> bool:
        """Check if budget is exceeded."""
        return self.spent_amount > self.total_amount
    
    @property
    def is_warning_threshold_reached(self) -> bool:
        """Check if warning threshold is reached."""
        return self.utilization_percentage >= self.warning_threshold
    
    @property
    def is_critical_threshold_reached(self) -> bool:
        """Check if critical threshold is reached."""
        return self.utilization_percentage >= self.critical_threshold
    
    @property
    def days_remaining(self) -> int:
        """Calculate days remaining in budget period."""
        from datetime import date
        today = date.today()
        if today > self.end_date:
            return 0
        return (self.end_date - today).days
    
    @property
    def is_active_period(self) -> bool:
        """Check if budget is in active period."""
        from datetime import date
        today = date.today()
        return self.start_date <= today <= self.end_date
    
    def update_spent_amount(self, new_spent: Decimal):
        """Update spent amount and recalculate remaining."""
        self.spent_amount = new_spent
        self.remaining_amount = self.total_amount - self.spent_amount


class BudgetCategory(TenantBase):
    """Budget category allocations."""
    
    __tablename__ = "budget_categories"
    
    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    
    # References
    budget_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("budgets.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Category information
    category_name: Mapped[str] = mapped_column(String(100), nullable=False)
    category_id: Mapped[Optional[str]] = mapped_column(String(36))  # Reference to transaction categories
    
    # Amounts
    allocated_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    spent_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    remaining_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    
    # Settings
    is_essential: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    priority: Mapped[int] = mapped_column(default=1, nullable=False)  # 1-5, 1 being highest
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    budget: Mapped["Budget"] = relationship("Budget", back_populates="categories")
    
    def __repr__(self):
        return f"<BudgetCategory(id={self.id}, category_name={self.category_name}, allocated_amount={self.allocated_amount})>"
    
    @property
    def utilization_percentage(self) -> Decimal:
        """Calculate category utilization as percentage."""
        if self.allocated_amount == 0:
            return Decimal(0)
        return (self.spent_amount / self.allocated_amount) * 100
    
    @property
    def is_over_budget(self) -> bool:
        """Check if category is over budget."""
        return self.spent_amount > self.allocated_amount
    
    def update_spent_amount(self, new_spent: Decimal):
        """Update spent amount and recalculate remaining."""
        self.spent_amount = new_spent
        self.remaining_amount = self.allocated_amount - self.spent_amount


class BudgetAlert(TenantBase):
    """Budget alerts and notifications."""
    
    __tablename__ = "budget_alerts"
    
    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    
    # References
    budget_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("budgets.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Alert information
    alert_type: Mapped[AlertType] = mapped_column(SQLEnum(AlertType), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Alert context
    threshold_percentage: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    amount_at_alert: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    category_id: Mapped[Optional[str]] = mapped_column(String(36))  # If alert is for specific category
    
    # Status
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_dismissed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    dismissed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    budget: Mapped["Budget"] = relationship("Budget", back_populates="alerts")
    
    def __repr__(self):
        return f"<BudgetAlert(id={self.id}, alert_type={self.alert_type}, title={self.title})>"
    
    def mark_as_read(self):
        """Mark alert as read."""
        self.is_read = True
        self.read_at = func.now()
    
    def dismiss(self):
        """Dismiss the alert."""
        self.is_dismissed = True
        self.dismissed_at = func.now()


class BudgetTemplate(TenantBase):
    """Budget templates for recurring budgets."""
    
    __tablename__ = "budget_templates"
    
    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    
    # Template information
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Template settings
    period_type: Mapped[BudgetPeriod] = mapped_column(SQLEnum(BudgetPeriod), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    
    # Alert settings
    warning_threshold: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=75, nullable=False)
    critical_threshold: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=90, nullable=False)
    
    # Template metadata
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    use_count: Mapped[int] = mapped_column(default=0, nullable=False)
    
    # Ownership
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    created_by: Mapped[str] = mapped_column(String(36), nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    template_categories: Mapped[list["BudgetTemplateCategory"]] = relationship(
        "BudgetTemplateCategory",
        back_populates="template",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<BudgetTemplate(id={self.id}, name={self.name}, total_amount={self.total_amount})>"
    
    def increment_use_count(self):
        """Increment template usage count."""
        self.use_count += 1
        self.last_used_at = func.now()


class BudgetTemplateCategory(TenantBase):
    """Template category allocations."""
    
    __tablename__ = "budget_template_categories"
    
    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    
    # References
    template_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("budget_templates.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Category information
    category_name: Mapped[str] = mapped_column(String(100), nullable=False)
    category_id: Mapped[Optional[str]] = mapped_column(String(36))
    
    # Allocation
    allocated_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    percentage_of_total: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    
    # Settings
    is_essential: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    priority: Mapped[int] = mapped_column(default=1, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    template: Mapped["BudgetTemplate"] = relationship("BudgetTemplate", back_populates="template_categories")
    
    def __repr__(self):
        return f"<BudgetTemplateCategory(id={self.id}, category_name={self.category_name}, allocated_amount={self.allocated_amount})>"
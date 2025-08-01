"""Financial goals and milestone tracking models."""
from datetime import datetime, date
from typing import Optional
from decimal import Decimal
from sqlalchemy import String, Boolean, DateTime, Date, Numeric, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum

from src.database import TenantBase


class GoalType(str, enum.Enum):
    """Types of financial goals."""
    SAVINGS = "savings"
    DEBT_PAYOFF = "debt_payoff"
    INVESTMENT = "investment"
    EMERGENCY_FUND = "emergency_fund"
    MAJOR_PURCHASE = "major_purchase"
    RETIREMENT = "retirement"
    EDUCATION = "education"
    TRAVEL = "travel"
    CUSTOM = "custom"


class GoalStatus(str, enum.Enum):
    """Goal status types."""
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class GoalPriority(str, enum.Enum):
    """Goal priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MilestoneStatus(str, enum.Enum):
    """Milestone status types."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"


class Goal(TenantBase):
    """Financial goal model."""
    
    __tablename__ = "goals"
    
    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    
    # Basic information
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    goal_type: Mapped[GoalType] = mapped_column(SQLEnum(GoalType), nullable=False)
    
    # Financial details
    target_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    current_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    monthly_contribution: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    
    # Timeline
    target_date: Mapped[Optional[date]] = mapped_column(Date)
    start_date: Mapped[date] = mapped_column(Date, default=func.current_date(), nullable=False)
    
    # Status and priority
    status: Mapped[GoalStatus] = mapped_column(SQLEnum(GoalStatus), default=GoalStatus.ACTIVE)
    priority: Mapped[GoalPriority] = mapped_column(SQLEnum(GoalPriority), default=GoalPriority.MEDIUM)
    
    # Settings
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    auto_contribute: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notify_milestones: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Linked accounts
    linked_account_id: Mapped[Optional[str]] = mapped_column(String(36))  # Reference to account
    
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
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    milestones: Mapped[list["GoalMilestone"]] = relationship(
        "GoalMilestone",
        back_populates="goal",
        cascade="all, delete-orphan",
        order_by="GoalMilestone.target_date"
    )
    contributions: Mapped[list["GoalContribution"]] = relationship(
        "GoalContribution",
        back_populates="goal",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<Goal(id={self.id}, name={self.name}, target_amount={self.target_amount})>"
    
    @property
    def progress_percentage(self) -> Decimal:
        """Calculate goal progress as percentage."""
        if self.target_amount == 0:
            return Decimal(100)
        return min(Decimal(100), (self.current_amount / self.target_amount) * 100)
    
    @property
    def remaining_amount(self) -> Decimal:
        """Calculate remaining amount to reach goal."""
        return max(Decimal(0), self.target_amount - self.current_amount)
    
    @property
    def is_completed(self) -> bool:
        """Check if goal is completed."""
        return self.current_amount >= self.target_amount or self.status == GoalStatus.COMPLETED
    
    @property
    def days_remaining(self) -> Optional[int]:
        """Calculate days remaining to target date."""
        if not self.target_date:
            return None
        
        today = date.today()
        if today > self.target_date:
            return 0
        return (self.target_date - today).days
    
    @property
    def months_to_goal(self) -> Optional[Decimal]:
        """Calculate months needed to reach goal with current contribution."""
        if not self.monthly_contribution or self.monthly_contribution <= 0:
            return None
        
        remaining = self.remaining_amount
        if remaining <= 0:
            return Decimal(0)
        
        return remaining / self.monthly_contribution
    
    @property
    def is_on_track(self) -> Optional[bool]:
        """Check if goal is on track based on timeline and progress."""
        if not self.target_date:
            return None
        
        total_days = (self.target_date - self.start_date).days
        elapsed_days = (date.today() - self.start_date).days
        
        if total_days <= 0:
            return True
        
        expected_progress = (elapsed_days / total_days) * 100
        actual_progress = float(self.progress_percentage)
        
        # Allow 10% tolerance
        return actual_progress >= (expected_progress - 10)
    
    def add_contribution(self, amount: Decimal):
        """Add contribution to goal."""
        self.current_amount += amount
        if self.current_amount >= self.target_amount and self.status == GoalStatus.ACTIVE:
            self.status = GoalStatus.COMPLETED
            self.completed_at = func.now()


class GoalMilestone(TenantBase):
    """Goal milestone tracking."""
    
    __tablename__ = "goal_milestones"
    
    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    
    # References
    goal_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("goals.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Milestone details
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    target_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    target_date: Mapped[Optional[date]] = mapped_column(Date)
    
    # Status
    status: Mapped[MilestoneStatus] = mapped_column(SQLEnum(MilestoneStatus), default=MilestoneStatus.PENDING)
    is_automatic: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Completion
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    actual_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    
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
    goal: Mapped["Goal"] = relationship("Goal", back_populates="milestones")
    
    def __repr__(self):
        return f"<GoalMilestone(id={self.id}, name={self.name}, target_amount={self.target_amount})>"
    
    @property
    def is_overdue(self) -> bool:
        """Check if milestone is overdue."""
        if not self.target_date or self.status == MilestoneStatus.COMPLETED:
            return False
        return date.today() > self.target_date
    
    @property
    def days_until_due(self) -> Optional[int]:
        """Calculate days until milestone is due."""
        if not self.target_date:
            return None
        
        today = date.today()
        if today > self.target_date:
            return 0
        return (self.target_date - today).days
    
    def complete(self, actual_amount: Optional[Decimal] = None):
        """Mark milestone as completed."""
        self.status = MilestoneStatus.COMPLETED
        self.completed_at = func.now()
        if actual_amount is not None:
            self.actual_amount = actual_amount


class GoalContribution(TenantBase):
    """Individual contributions to goals."""
    
    __tablename__ = "goal_contributions"
    
    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    
    # References
    goal_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("goals.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Contribution details
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    contribution_date: Mapped[date] = mapped_column(Date, default=func.current_date(), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Source information
    source_type: Mapped[str] = mapped_column(String(50), default="manual", nullable=False)  # manual, automatic, transfer
    source_account_id: Mapped[Optional[str]] = mapped_column(String(36))
    transaction_id: Mapped[Optional[str]] = mapped_column(String(36))  # Link to transaction if from account
    
    # Contribution metadata
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    recurring_frequency: Mapped[Optional[str]] = mapped_column(String(20))  # monthly, weekly, etc.
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    goal: Mapped["Goal"] = relationship("Goal", back_populates="contributions")
    
    def __repr__(self):
        return f"<GoalContribution(id={self.id}, amount={self.amount}, goal_id={self.goal_id})>"


class GoalCategory(TenantBase):
    """Custom goal categories for organization."""
    
    __tablename__ = "goal_categories"
    
    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    
    # Category details
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    color: Mapped[str] = mapped_column(String(7), default="#007bff", nullable=False)  # Hex color
    icon: Mapped[Optional[str]] = mapped_column(String(50))  # Icon name or Unicode
    
    # Settings
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(default=0, nullable=False)
    
    # Ownership
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    
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
    
    def __repr__(self):
        return f"<GoalCategory(id={self.id}, name={self.name})>"


class GoalTemplate(TenantBase):
    """Templates for creating common goals."""
    
    __tablename__ = "goal_templates"
    
    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    
    # Template details
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    goal_type: Mapped[GoalType] = mapped_column(SQLEnum(GoalType), nullable=False)
    
    # Default values
    default_target_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    default_monthly_contribution: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    default_timeline_months: Mapped[Optional[int]] = mapped_column()
    
    # Template settings
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    use_count: Mapped[int] = mapped_column(default=0, nullable=False)
    
    # Ownership
    created_by: Mapped[Optional[str]] = mapped_column(String(36))  # NULL for system templates
    
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
    
    def __repr__(self):
        return f"<GoalTemplate(id={self.id}, name={self.name}, goal_type={self.goal_type})>"
    
    def increment_use_count(self):
        """Increment template usage count."""
        self.use_count += 1
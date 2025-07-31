"""Savings goals models for tenant database."""
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Boolean, JSON, Numeric, ForeignKey, Index, Text, Date
from datetime import datetime, date
from typing import Dict, Any, Optional, TYPE_CHECKING
from decimal import Decimal

from src.database import TenantBase

if TYPE_CHECKING:
    from src.users.models import User


class SavingsGoal(TenantBase):
    """Savings goal model (typically emergency fund)."""
    __tablename__ = "savings_goals"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    
    # Goal information
    name: Mapped[str] = mapped_column(String(100), index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Goal amounts
    target_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    current_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    
    # Calculated progress
    progress_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)  # 0-100
    
    # Goal timeline
    target_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    created_date: Mapped[date] = mapped_column(Date, default=date.today)
    
    # Goal status
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    
    # Goal settings
    auto_save_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_save_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    auto_save_frequency: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # weekly, monthly
    
    # Linked account for automatic savings
    linked_account_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    
    # Goal type and category
    goal_type: Mapped[str] = mapped_column(String(50), default="emergency_fund", index=True)
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    priority: Mapped[int] = mapped_column(default=1, index=True)  # 1=highest
    
    # Visual and organizational
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)  # Hex color
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Metadata
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="savings_goals")
    contributions: Mapped[list["GoalContribution"]] = relationship(
        "GoalContribution", 
        back_populates="goal",
        cascade="all, delete-orphan"
    )
    milestones: Mapped[list["GoalMilestone"]] = relationship(
        "GoalMilestone", 
        back_populates="goal",
        cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_savings_goals_user_id", "user_id"),
        Index("idx_savings_goals_name", "name"),
        Index("idx_savings_goals_target_date", "target_date"),
        Index("idx_savings_goals_completed", "is_completed"),
        Index("idx_savings_goals_active", "is_active"),
        Index("idx_savings_goals_type", "goal_type"),
        Index("idx_savings_goals_category", "category"),
        Index("idx_savings_goals_priority", "priority"),
        Index("idx_savings_goals_linked_account", "linked_account_id"),
        # Composite indexes
        Index("idx_savings_goals_user_active", "user_id", "is_active"),
        Index("idx_savings_goals_user_type", "user_id", "goal_type"),
    )


class GoalContribution(TenantBase):
    """Individual contributions toward savings goals."""
    __tablename__ = "goal_contributions"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    goal_id: Mapped[str] = mapped_column(String(36), ForeignKey("savings_goals.id"), index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    
    # Contribution details
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    contribution_date: Mapped[date] = mapped_column(Date, default=date.today, index=True)
    
    # Contribution source
    source_type: Mapped[str] = mapped_column(String(20), index=True)  # manual, automatic, transfer
    source_account_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    transaction_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    
    # Contribution metadata
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reference_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(String(20), default="completed", index=True)  # pending, completed, failed
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    goal: Mapped["SavingsGoal"] = relationship("SavingsGoal", back_populates="contributions")
    
    # Indexes
    __table_args__ = (
        Index("idx_goal_contributions_goal_id", "goal_id"),
        Index("idx_goal_contributions_user_id", "user_id"),
        Index("idx_goal_contributions_date", "contribution_date"),
        Index("idx_goal_contributions_source_type", "source_type"),
        Index("idx_goal_contributions_transaction", "transaction_id"),
        Index("idx_goal_contributions_status", "status"),
        # Composite indexes
        Index("idx_goal_contributions_goal_date", "goal_id", "contribution_date"),
        Index("idx_goal_contributions_user_date", "user_id", "contribution_date"),
    )


class GoalMilestone(TenantBase):
    """Milestones and progress markers for savings goals."""
    __tablename__ = "goal_milestones"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    goal_id: Mapped[str] = mapped_column(String(36), ForeignKey("savings_goals.id"), index=True)
    
    # Milestone information
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Milestone target
    target_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    target_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2))  # 0-100
    target_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Milestone status
    is_achieved: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    achieved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    achieved_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    
    # Milestone rewards/notifications
    reward_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notify_on_achievement: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Ordering
    sort_order: Mapped[int] = mapped_column(default=0)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Relationships
    goal: Mapped["SavingsGoal"] = relationship("SavingsGoal", back_populates="milestones")
    
    # Indexes
    __table_args__ = (
        Index("idx_goal_milestones_goal_id", "goal_id"),
        Index("idx_goal_milestones_achieved", "is_achieved"),
        Index("idx_goal_milestones_target_date", "target_date"),
        Index("idx_goal_milestones_sort_order", "sort_order"),
        # Composite indexes
        Index("idx_goal_milestones_goal_order", "goal_id", "sort_order"),
    )


class GoalInsight(TenantBase):
    """AI-generated insights and recommendations for savings goals."""
    __tablename__ = "goal_insights"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    goal_id: Mapped[str] = mapped_column(String(36), ForeignKey("savings_goals.id"), index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    
    # Insight information
    insight_type: Mapped[str] = mapped_column(String(50), index=True)  # recommendation, warning, celebration
    title: Mapped[str] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(Text)
    
    # Insight data and analysis
    data_source: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    confidence_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2), nullable=True)  # 0-1
    
    # Insight actions
    suggested_actions: Mapped[list[str]] = mapped_column(JSON, default=list)
    action_taken: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Insight status
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_dismissed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_actionable: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    
    # Priority and relevance
    priority: Mapped[str] = mapped_column(String(20), default="medium", index=True)  # low, medium, high
    relevance_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    goal: Mapped["SavingsGoal"] = relationship("SavingsGoal")
    
    # Indexes
    __table_args__ = (
        Index("idx_goal_insights_goal_id", "goal_id"),
        Index("idx_goal_insights_user_id", "user_id"),
        Index("idx_goal_insights_type", "insight_type"),
        Index("idx_goal_insights_read", "is_read"),
        Index("idx_goal_insights_dismissed", "is_dismissed"),
        Index("idx_goal_insights_actionable", "is_actionable"),
        Index("idx_goal_insights_priority", "priority"),
        Index("idx_goal_insights_created", "created_at"),
        Index("idx_goal_insights_expires", "expires_at"),
    )
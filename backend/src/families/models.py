"""Family management models for tenant database."""
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Boolean, JSON, Numeric, ForeignKey, Index, Text
from datetime import datetime
from typing import Dict, Any, Optional, TYPE_CHECKING
from decimal import Decimal

from src.database import TenantBase

if TYPE_CHECKING:
    from src.users.models import User


class Family(TenantBase):
    """Family plan model for collaborative financial management."""
    __tablename__ = "families"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    
    # Family information
    name: Mapped[str] = mapped_column(String(100), index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Family administration
    administrator_id: Mapped[str] = mapped_column(String(36), index=True)  # User ID of admin
    
    # Family settings
    settings: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Family status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    max_members: Mapped[int] = mapped_column(default=10)
    current_member_count: Mapped[int] = mapped_column(default=1)
    
    # Family plan type
    plan_type: Mapped[str] = mapped_column(String(50), default="basic", index=True)
    
    # Metadata
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Relationships
    members: Mapped[list["FamilyMember"]] = relationship(
        "FamilyMember", 
        back_populates="family",
        cascade="all, delete-orphan"
    )
    invitations: Mapped[list["FamilyInvitation"]] = relationship(
        "FamilyInvitation", 
        back_populates="family",
        cascade="all, delete-orphan"
    )
    shared_budgets: Mapped[list["FamilyBudget"]] = relationship(
        "FamilyBudget", 
        back_populates="family",
        cascade="all, delete-orphan"
    )
    shared_goals: Mapped[list["FamilySavingsGoal"]] = relationship(
        "FamilySavingsGoal", 
        back_populates="family",
        cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_families_name", "name"),
        Index("idx_families_administrator", "administrator_id"),
        Index("idx_families_active", "is_active"),
        Index("idx_families_plan_type", "plan_type"),
        Index("idx_families_created_at", "created_at"),
    )


class FamilyMember(TenantBase):
    """Family member with roles and permissions."""
    __tablename__ = "family_members"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    family_id: Mapped[str] = mapped_column(String(36), ForeignKey("families.id"), index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    
    # Member information (denormalized for performance)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255))
    
    # Family role
    role: Mapped[str] = mapped_column(String(50), index=True)  # administrator, spouse, teen, pre_teen, support, agent
    
    # Permissions
    permissions: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Member status
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)  # active, invited, suspended
    
    # Financial oversight settings
    spending_limit: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    requires_approval_over: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    approved_categories: Mapped[list[str]] = mapped_column(JSON, default=list)
    
    # Member activity
    last_active_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    family: Mapped["Family"] = relationship("Family", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="family_membership")
    approval_requests: Mapped[list["SpendingApprovalRequest"]] = relationship(
        "SpendingApprovalRequest", 
        back_populates="member",
        cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_family_members_family_id", "family_id"),
        Index("idx_family_members_user_id", "user_id"),
        Index("idx_family_members_role", "role"),
        Index("idx_family_members_status", "status"),
        Index("idx_family_members_joined_at", "joined_at"),
        # Ensure unique family-user combinations
        Index("idx_family_members_unique", "family_id", "user_id", unique=True),
    )


class FamilyInvitation(TenantBase):
    """Family invitation management."""
    __tablename__ = "family_invitations"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    family_id: Mapped[str] = mapped_column(String(36), ForeignKey("families.id"), index=True)
    
    # Invitation details
    inviter_id: Mapped[str] = mapped_column(String(36), index=True)  # User ID who sent invitation
    email: Mapped[str] = mapped_column(String(255), index=True)
    
    # Invited role and permissions
    role: Mapped[str] = mapped_column(String(50))
    permissions: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Invitation message
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Invitation status
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)  # pending, accepted, expired, cancelled
    
    # Token and security
    invitation_token: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    
    # Expiration
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    
    # Response tracking
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    accepted_by_user_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    family: Mapped["Family"] = relationship("Family", back_populates="invitations")
    
    # Indexes
    __table_args__ = (
        Index("idx_family_invitations_family_id", "family_id"),
        Index("idx_family_invitations_inviter", "inviter_id"),
        Index("idx_family_invitations_email", "email"),
        Index("idx_family_invitations_status", "status"),
        Index("idx_family_invitations_token", "invitation_token"),
        Index("idx_family_invitations_expires", "expires_at"),
        Index("idx_family_invitations_created", "created_at"),
    )


class FamilyBudget(TenantBase):
    """Shared family budgets."""
    __tablename__ = "family_budgets"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    family_id: Mapped[str] = mapped_column(String(36), ForeignKey("families.id"), index=True)
    created_by: Mapped[str] = mapped_column(String(36), index=True)  # User ID
    
    # Budget information
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Budget configuration
    budget_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Member access control
    accessible_by: Mapped[list[str]] = mapped_column(JSON, default=list)  # User IDs
    editable_by: Mapped[list[str]] = mapped_column(JSON, default=list)  # User IDs
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Relationships
    family: Mapped["Family"] = relationship("Family", back_populates="shared_budgets")
    
    # Indexes
    __table_args__ = (
        Index("idx_family_budgets_family_id", "family_id"),
        Index("idx_family_budgets_created_by", "created_by"),
        Index("idx_family_budgets_active", "is_active"),
    )


class FamilySavingsGoal(TenantBase):
    """Shared family savings goals."""
    __tablename__ = "family_savings_goals"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    family_id: Mapped[str] = mapped_column(String(36), ForeignKey("families.id"), index=True)
    created_by: Mapped[str] = mapped_column(String(36), index=True)  # User ID
    
    # Goal information
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Goal configuration
    goal_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Member participation
    contributors: Mapped[list[str]] = mapped_column(JSON, default=list)  # User IDs
    contribution_rules: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Relationships
    family: Mapped["Family"] = relationship("Family", back_populates="shared_goals")
    
    # Indexes
    __table_args__ = (
        Index("idx_family_savings_goals_family_id", "family_id"),
        Index("idx_family_savings_goals_created_by", "created_by"),
        Index("idx_family_savings_goals_active", "is_active"),
    )


class SpendingApprovalRequest(TenantBase):
    """Spending approval requests for family members."""
    __tablename__ = "spending_approval_requests"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    family_id: Mapped[str] = mapped_column(String(36), ForeignKey("families.id"), index=True)
    member_id: Mapped[str] = mapped_column(String(36), ForeignKey("family_members.id"), index=True)
    
    # Request details
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    merchant: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Request context
    transaction_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    account_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    # Approval status
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)  # pending, approved, denied, expired
    
    # Approval details
    approved_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)  # User ID
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    approval_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Expiration
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    family: Mapped["Family"] = relationship("Family")
    member: Mapped["FamilyMember"] = relationship("FamilyMember", back_populates="approval_requests")
    
    # Indexes
    __table_args__ = (
        Index("idx_spending_approvals_family_id", "family_id"),
        Index("idx_spending_approvals_member_id", "member_id"),
        Index("idx_spending_approvals_status", "status"),
        Index("idx_spending_approvals_approved_by", "approved_by"),
        Index("idx_spending_approvals_expires", "expires_at"),
        Index("idx_spending_approvals_created", "created_at"),
    )
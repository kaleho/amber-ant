"""User models for tenant database."""
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Boolean, JSON, Text, Index
from datetime import datetime
from typing import Dict, Any, Optional, TYPE_CHECKING

from src.database import TenantBase

if TYPE_CHECKING:
    from src.families.models import FamilyMember
    from src.accounts.models import Account
    from src.budgets.models import Budget
    from src.goals.models import SavingsGoal
    from src.tithing.models import TithingPayment
    from src.subscriptions.models import Subscription


class User(TenantBase):
    """User model for tenant database."""
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    auth0_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    picture: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Persona and preferences
    persona: Mapped[str] = mapped_column(String(50), default="single_adult")
    preferences: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Family information
    family_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    family_role: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Status and metadata
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Relationships
    profile: Mapped[Optional["UserProfile"]] = relationship(
        "UserProfile", 
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    sessions: Mapped[list["UserSession"]] = relationship(
        "UserSession", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    accounts: Mapped[list["Account"]] = relationship(
        "Account", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    budgets: Mapped[list["Budget"]] = relationship(
        "Budget", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    savings_goals: Mapped[list["SavingsGoal"]] = relationship(
        "SavingsGoal", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    tithing_payments: Mapped[list["TithingPayment"]] = relationship(
        "TithingPayment", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    subscriptions: Mapped[list["Subscription"]] = relationship(
        "Subscription", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    family_membership: Mapped[Optional["FamilyMember"]] = relationship(
        "FamilyMember", 
        back_populates="user",
        uselist=False
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_users_auth0_id", "auth0_id"),
        Index("idx_users_email", "email"),
        Index("idx_users_persona", "persona"),
        Index("idx_users_family_id", "family_id"),
        Index("idx_users_active", "is_active"),
        Index("idx_users_created_at", "created_at"),
    )


class UserProfile(TenantBase):
    """Extended user profile information."""
    __tablename__ = "user_profiles"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    
    # Personal information
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    date_of_birth: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Address information
    address_line1: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    country: Mapped[str] = mapped_column(String(100), default="US")
    
    # Financial information
    annual_income: Mapped[Optional[float]] = mapped_column(nullable=True)
    employment_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    employer: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Religious/tithing information
    church_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    tithing_percentage: Mapped[float] = mapped_column(default=10.0)
    
    # Additional metadata
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="profile")
    
    # Indexes
    __table_args__ = (
        Index("idx_user_profiles_user_id", "user_id"),
    )


class UserSession(TenantBase):
    """User session tracking."""
    __tablename__ = "user_sessions"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    session_token: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    
    # Session information
    ip_address: Mapped[str] = mapped_column(String(45))  # IPv6 compatible
    user_agent: Mapped[str] = mapped_column(Text)
    device_info: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Session lifecycle
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    last_activity: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sessions")
    
    # Indexes
    __table_args__ = (
        Index("idx_user_sessions_user_id", "user_id"),
        Index("idx_user_sessions_token", "session_token"),
        Index("idx_user_sessions_active", "is_active"),
        Index("idx_user_sessions_expires", "expires_at"),
    )


class UserActivity(TenantBase):
    """User activity and audit log."""
    __tablename__ = "user_activities"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    
    # Activity information
    activity_type: Mapped[str] = mapped_column(String(50), index=True)
    description: Mapped[str] = mapped_column(Text)
    entity_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    entity_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    # Request context
    ip_address: Mapped[str] = mapped_column(String(45))
    user_agent: Mapped[str] = mapped_column(Text)
    
    # Additional data
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index("idx_user_activities_user_id", "user_id"),
        Index("idx_user_activities_type", "activity_type"),
        Index("idx_user_activities_entity", "entity_type", "entity_id"),
        Index("idx_user_activities_created", "created_at"),
    )


class UserPreference(TenantBase):
    """Individual user preferences (normalized)."""
    __tablename__ = "user_preferences"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    
    # Preference details
    category: Mapped[str] = mapped_column(String(50), index=True)
    key: Mapped[str] = mapped_column(String(100))
    value: Mapped[str] = mapped_column(Text)
    value_type: Mapped[str] = mapped_column(String(20), default="string")  # string, number, boolean, json
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_user_preferences_user_id", "user_id"),
        Index("idx_user_preferences_category", "category"),
        Index("idx_user_preferences_key", "key"),
        Index("idx_user_preferences_composite", "user_id", "category", "key"),
    )
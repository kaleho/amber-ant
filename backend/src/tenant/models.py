"""Database models for tenant management."""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.database import GlobalBase


class TenantRegistry(GlobalBase):
    """Central registry of all tenants in the system."""
    
    __tablename__ = "tenant_registry"
    
    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    
    # Tenant identification
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Database connection info
    database_url: Mapped[str] = mapped_column(String(500), nullable=False)
    database_auth_token: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    subscription_status: Mapped[str] = mapped_column(
        String(20), 
        default="active", 
        nullable=False
    )  # active, suspended, cancelled, trial
    subscription_tier: Mapped[str] = mapped_column(
        String(20), 
        default="free", 
        nullable=False
    )  # free, premium, enterprise
    
    # Ownership
    owner_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    
    # Resource limits (based on subscription tier)
    max_users: Mapped[int] = mapped_column(Integer, default=5)
    max_accounts: Mapped[int] = mapped_column(Integer, default=10)
    max_monthly_transactions: Mapped[int] = mapped_column(Integer, default=1000)
    
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
    tenant_users: Mapped[list["TenantUser"]] = relationship(
        "TenantUser",
        back_populates="tenant",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<TenantRegistry(id={self.id}, slug={self.slug}, name={self.name})>"
    
    @property
    def is_premium(self) -> bool:
        """Check if tenant has premium features."""
        return self.subscription_tier in ["premium", "enterprise"]
    
    @property
    def is_enterprise(self) -> bool:
        """Check if tenant has enterprise features."""
        return self.subscription_tier == "enterprise"
    
    def can_add_user(self, current_user_count: int) -> bool:
        """Check if tenant can add another user."""
        return current_user_count < self.max_users
    
    def can_add_account(self, current_account_count: int) -> bool:
        """Check if tenant can add another account."""
        return current_account_count < self.max_accounts
    
    def can_add_transaction(self, monthly_transaction_count: int) -> bool:
        """Check if tenant can add another transaction this month."""
        return monthly_transaction_count < self.max_monthly_transactions


class TenantUser(GlobalBase):
    """Association between users and tenants with role information."""
    
    __tablename__ = "tenant_users"
    
    # Composite primary key
    tenant_id: Mapped[str] = mapped_column(
        String(36), 
        ForeignKey("tenant_registry.id", ondelete="CASCADE"),
        primary_key=True
    )
    user_id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    
    # Role and permissions
    role: Mapped[str] = mapped_column(
        String(20), 
        default="member", 
        nullable=False
    )  # owner, admin, member, viewer
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    invitation_status: Mapped[str] = mapped_column(
        String(20), 
        default="accepted", 
        nullable=False
    )  # pending, accepted, declined, expired
    
    # Metadata
    invited_by: Mapped[Optional[str]] = mapped_column(String(36))
    invitation_token: Mapped[Optional[str]] = mapped_column(String(100), unique=True)
    invitation_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
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
    tenant: Mapped["TenantRegistry"] = relationship(
        "TenantRegistry",
        back_populates="tenant_users"
    )
    
    def __repr__(self):
        return f"<TenantUser(tenant_id={self.tenant_id}, user_id={self.user_id}, role={self.role})>"
    
    @property
    def is_owner(self) -> bool:
        """Check if user is the tenant owner."""
        return self.role == "owner"
    
    @property
    def is_admin(self) -> bool:
        """Check if user has admin privileges."""
        return self.role in ["owner", "admin"]
    
    @property
    def can_manage_users(self) -> bool:
        """Check if user can manage other users."""
        return self.role in ["owner", "admin"]
    
    @property
    def can_modify_settings(self) -> bool:
        """Check if user can modify tenant settings."""
        return self.role == "owner"
    
    @property
    def can_view_finances(self) -> bool:
        """Check if user can view financial data."""
        return self.role in ["owner", "admin", "member"]
    
    @property
    def can_edit_finances(self) -> bool:
        """Check if user can edit financial data."""
        return self.role in ["owner", "admin", "member"]
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        permissions = {
            "owner": [
                "manage_users", "modify_settings", "view_finances", 
                "edit_finances", "delete_tenant", "manage_billing"
            ],
            "admin": [
                "manage_users", "view_finances", "edit_finances", 
                "manage_categories", "export_data"
            ],
            "member": [
                "view_finances", "edit_finances", "add_transactions", 
                "manage_own_goals"
            ],
            "viewer": [
                "view_finances", "view_reports"
            ]
        }
        
        return permission in permissions.get(self.role, [])


class TenantInvitation(GlobalBase):
    """Pending invitations for users to join tenants."""
    
    __tablename__ = "tenant_invitations"
    
    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    
    # Invitation details
    tenant_id: Mapped[str] = mapped_column(
        String(36), 
        ForeignKey("tenant_registry.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), default="member", nullable=False)
    
    # Invitation metadata
    invitation_token: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    invited_by: Mapped[str] = mapped_column(String(36), nullable=False)
    message: Mapped[Optional[str]] = mapped_column(Text)
    
    # Status and expiration
    status: Mapped[str] = mapped_column(
        String(20), 
        default="pending", 
        nullable=False
    )  # pending, accepted, declined, expired, cancelled
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
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
        return f"<TenantInvitation(id={self.id}, email={self.email}, status={self.status})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if invitation has expired."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc) > self.expires_at
    
    @property
    def is_pending(self) -> bool:
        """Check if invitation is still pending."""
        return self.status == "pending" and not self.is_expired
    
    def expire(self):
        """Mark invitation as expired."""
        self.status = "expired"
        self.updated_at = func.now()
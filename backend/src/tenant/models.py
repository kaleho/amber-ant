"""Global database models for tenant registry."""
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Boolean, Text, JSON, Index
from datetime import datetime
from typing import Dict, Any, Optional

from src.database import GlobalBase


class TenantRegistry(GlobalBase):
    """Global registry of all tenants."""
    __tablename__ = "tenant_registry"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    database_url: Mapped[str] = mapped_column(String(500))
    auth_token: Mapped[str] = mapped_column(Text)  # Encrypted
    plan: Mapped[str] = mapped_column(String(50), default="basic")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    features: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Relationships
    tenant_users: Mapped[list["TenantUser"]] = relationship(
        "TenantUser", 
        back_populates="tenant",
        cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_tenant_registry_slug", "slug"),
        Index("idx_tenant_registry_active", "is_active"),
        Index("idx_tenant_registry_plan", "plan"),
    )


class TenantUser(GlobalBase):
    """Global mapping of users to tenants (for multi-tenant users)."""
    __tablename__ = "tenant_users"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    auth0_id: Mapped[str] = mapped_column(String(255), index=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    role: Mapped[str] = mapped_column(String(50), default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    permissions: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_accessed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    tenant: Mapped["TenantRegistry"] = relationship("TenantRegistry", back_populates="tenant_users")
    
    # Indexes
    __table_args__ = (
        Index("idx_tenant_users_auth0_id", "auth0_id"),
        Index("idx_tenant_users_tenant_id", "tenant_id"),
        Index("idx_tenant_users_role", "role"),
        Index("idx_tenant_users_active", "is_active"),
        Index("idx_tenant_users_composite", "auth0_id", "tenant_id"),  # Composite index
    )


class TenantApiKey(GlobalBase):
    """API keys for tenant-specific access."""
    __tablename__ = "tenant_api_keys"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    key_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    permissions: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by: Mapped[str] = mapped_column(String(255))  # Auth0 user ID
    
    # Indexes
    __table_args__ = (
        Index("idx_tenant_api_keys_tenant_id", "tenant_id"),
        Index("idx_tenant_api_keys_active", "is_active"),
        Index("idx_tenant_api_keys_expires", "expires_at"),
    )


class TenantSettings(GlobalBase):
    """Global tenant settings and configuration."""
    __tablename__ = "tenant_settings"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    settings: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_tenant_settings_tenant_id", "tenant_id"),
    )
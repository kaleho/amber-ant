"""Tenant Pydantic schemas."""
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator


class TenantBase(BaseModel):
    """Base tenant schema."""
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=3, max_length=50, pattern=r'^[a-z0-9-]+$')
    plan: str = Field(default="basic")
    
    @validator('slug')
    def validate_slug(cls, v):
        """Validate tenant slug format."""
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Slug must contain only alphanumeric characters and hyphens')
        if v.startswith('-') or v.endswith('-'):
            raise ValueError('Slug cannot start or end with a hyphen')
        return v.lower()


class CreateTenantRequest(TenantBase):
    """Request schema for creating a tenant."""
    features: Optional[List[str]] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class UpdateTenantRequest(BaseModel):
    """Request schema for updating a tenant."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    plan: Optional[str] = None
    is_active: Optional[bool] = None
    features: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class TenantResponse(BaseModel):
    """Response schema for tenant information."""
    id: str
    name: str
    slug: str
    plan: str
    is_active: bool
    features: List[str]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TenantUserBase(BaseModel):
    """Base tenant user schema."""
    auth0_id: str = Field(..., pattern=r'^auth0\|[a-zA-Z0-9]{24}$')
    role: str = Field(default="user")
    permissions: Optional[Dict[str, Any]] = Field(default_factory=dict)


class CreateTenantUserRequest(TenantUserBase):
    """Request schema for adding user to tenant."""
    pass


class UpdateTenantUserRequest(BaseModel):
    """Request schema for updating tenant user."""
    role: Optional[str] = None
    is_active: Optional[bool] = None
    permissions: Optional[Dict[str, Any]] = None


class TenantUserResponse(BaseModel):
    """Response schema for tenant user information."""
    id: str
    auth0_id: str
    tenant_id: str
    role: str
    is_active: bool
    permissions: Dict[str, Any]
    joined_at: datetime
    last_accessed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class TenantContextResponse(BaseModel):
    """Response schema for tenant context."""
    tenant_id: str
    tenant_slug: str
    plan: str
    is_active: bool
    features: List[str]
    metadata: Dict[str, Any]


class TenantApiKeyBase(BaseModel):
    """Base API key schema."""
    name: str = Field(..., min_length=1, max_length=100)
    permissions: Optional[Dict[str, Any]] = Field(default_factory=dict)
    expires_at: Optional[datetime] = None


class CreateTenantApiKeyRequest(TenantApiKeyBase):
    """Request schema for creating API key."""
    pass


class TenantApiKeyResponse(BaseModel):
    """Response schema for API key information."""
    id: str
    tenant_id: str
    name: str
    permissions: Dict[str, Any]
    is_active: bool
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    created_at: datetime
    created_by: str
    
    class Config:
        from_attributes = True


class TenantApiKeyWithSecret(TenantApiKeyResponse):
    """API key response including the secret (only returned on creation)."""
    api_key: str = Field(..., description="The actual API key - store this securely!")


class TenantStatsResponse(BaseModel):
    """Response schema for tenant statistics."""
    tenant_id: str
    total_users: int
    active_users: int
    total_accounts: int
    total_transactions: int
    total_budgets: int
    total_goals: int
    plan: str
    created_at: datetime
    last_activity: Optional[datetime]


class TenantHealthResponse(BaseModel):
    """Response schema for tenant health check."""
    tenant_id: str
    database_healthy: bool
    connection_count: int
    last_migration: Optional[datetime]
    status: str = Field(..., description="healthy, degraded, or unhealthy")
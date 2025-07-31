"""Authentication Pydantic schemas."""
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    """Response schema for token information."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    scope: Optional[str] = None


class UserClaims(BaseModel):
    """Schema for JWT user claims."""
    sub: str = Field(..., description="Auth0 user ID")
    email: str = Field(..., description="User email address")
    email_verified: bool = Field(default=False)
    name: Optional[str] = Field(None, description="User display name")
    nickname: Optional[str] = None
    picture: Optional[str] = Field(None, description="User profile picture URL")
    iss: str = Field(..., description="Token issuer")
    aud: str = Field(..., description="Token audience")
    iat: int = Field(..., description="Issued at timestamp")
    exp: int = Field(..., description="Expiry timestamp")
    tenant_id: Optional[str] = Field(None, alias="https://faithfulfinances.com/tenant_id")
    permissions: List[str] = Field(default_factory=list)
    roles: List[str] = Field(default_factory=list)
    
    class Config:
        allow_population_by_field_name = True


class LoginRequest(BaseModel):
    """Request schema for login."""
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")
    tenant_slug: Optional[str] = Field(None, description="Tenant slug for multi-tenant login")


class LoginResponse(BaseModel):
    """Response schema for successful login."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]
    tenant: Optional[Dict[str, Any]] = None


class RefreshTokenRequest(BaseModel):
    """Request schema for token refresh."""
    refresh_token: str


class LogoutRequest(BaseModel):
    """Request schema for logout."""
    return_to: Optional[str] = Field(None, description="URL to redirect after logout")


class PasswordResetRequest(BaseModel):
    """Request schema for password reset."""
    email: str = Field(..., description="User email address")
    client_id: Optional[str] = Field(None, description="Auth0 client ID")


class PasswordChangeRequest(BaseModel):
    """Request schema for password change."""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")


class UserPermissions(BaseModel):
    """Schema for user permissions."""
    permissions: List[str]
    roles: List[str]
    tenant_role: Optional[str] = None
    is_global_admin: bool = False
    is_tenant_admin: bool = False
    is_family_admin: bool = False


class AuthContextResponse(BaseModel):
    """Response schema for authentication context."""
    user_id: str
    email: str
    name: Optional[str]
    tenant_id: Optional[str]
    tenant_slug: Optional[str]
    permissions: UserPermissions
    subscription_plan: Optional[str]
    features: List[str]


class ApiKeyCreateRequest(BaseModel):
    """Request schema for creating API key."""
    name: str = Field(..., min_length=1, max_length=100)
    permissions: List[str] = Field(default_factory=list)
    expires_days: Optional[int] = Field(None, ge=1, le=365, description="Days until expiry")


class ApiKeyResponse(BaseModel):
    """Response schema for API key information."""
    id: str
    name: str
    permissions: List[str]
    is_active: bool
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    created_at: datetime
    created_by: str


class ApiKeyWithSecret(ApiKeyResponse):
    """API key response with secret (only on creation)."""
    api_key: str = Field(..., description="The API key - store securely!")


class TwoFactorSetupRequest(BaseModel):
    """Request schema for 2FA setup."""
    phone_number: Optional[str] = Field(None, description="Phone number for SMS 2FA")
    
    
class TwoFactorVerifyRequest(BaseModel):
    """Request schema for 2FA verification."""
    code: str = Field(..., min_length=6, max_length=6, description="2FA verification code")


class SessionInfo(BaseModel):
    """Schema for session information."""
    session_id: str
    user_id: str
    tenant_id: Optional[str]
    ip_address: str
    user_agent: str
    created_at: datetime
    last_active: datetime
    expires_at: datetime
    is_active: bool


class SecurityEvent(BaseModel):
    """Schema for security events."""
    event_type: str = Field(..., description="Type of security event")
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    ip_address: str
    user_agent: str
    success: bool
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class RateLimitInfo(BaseModel):
    """Schema for rate limit information."""
    limit: int = Field(..., description="Rate limit per window")
    remaining: int = Field(..., description="Remaining requests in window")
    reset: int = Field(..., description="Timestamp when window resets")
    retry_after: int = Field(default=0, description="Seconds to wait before retry")
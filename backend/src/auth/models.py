"""Authentication models for storing user auth data."""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from src.database import TenantBase


class AuthUser(TenantBase):
    """User authentication information stored per tenant."""
    
    __tablename__ = "auth_users"
    
    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    
    # Auth0 user information
    auth0_user_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Profile information from Auth0
    name: Mapped[Optional[str]] = mapped_column(String(255))
    nickname: Mapped[Optional[str]] = mapped_column(String(100))
    picture: Mapped[Optional[str]] = mapped_column(String(500))
    
    # User status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Authentication metadata
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    login_count: Mapped[int] = mapped_column(default=0, nullable=False)
    
    # User preferences
    locale: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)
    
    # Auth0 user metadata (stored as JSON)
    user_metadata: Mapped[Optional[dict]] = mapped_column(JSON)
    app_metadata: Mapped[Optional[dict]] = mapped_column(JSON)
    
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
        return f"<AuthUser(id={self.id}, email={self.email}, auth0_user_id={self.auth0_user_id})>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JWT claims."""
        return {
            "sub": self.auth0_user_id,
            "email": self.email,
            "email_verified": self.email_verified,
            "name": self.name,
            "nickname": self.nickname,
            "picture": self.picture,
            "locale": self.locale,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class RefreshToken(TenantBase):
    """Refresh tokens for JWT authentication."""
    
    __tablename__ = "refresh_tokens"
    
    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    
    # Token information
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    
    # Token metadata
    device_id: Mapped[Optional[str]] = mapped_column(String(100))
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    
    # Token status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Expiration
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
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc) > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if token is valid (active, not revoked, not expired)."""
        return self.is_active and not self.is_revoked and not self.is_expired
    
    def revoke(self):
        """Revoke the refresh token."""
        self.is_revoked = True
        self.is_active = False
        self.updated_at = func.now()


class LoginAttempt(TenantBase):
    """Track login attempts for security monitoring."""
    
    __tablename__ = "login_attempts"
    
    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    
    # Attempt information
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False, index=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Attempt result
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    failure_reason: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Geolocation (if available)
    country: Mapped[Optional[str]] = mapped_column(String(100))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Timestamp
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    
    def __repr__(self):
        return f"<LoginAttempt(id={self.id}, email={self.email}, success={self.success})>"


class PasswordReset(TenantBase):
    """Password reset tokens (for local auth if implemented)."""
    
    __tablename__ = "password_resets"
    
    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    
    # Reset information
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    
    # Status
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Expiration
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    def __repr__(self):
        return f"<PasswordReset(id={self.id}, email={self.email}, is_used={self.is_used})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if reset token is expired."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc) > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if reset token is valid."""
        return not self.is_used and not self.is_expired
    
    def use(self):
        """Mark reset token as used."""
        self.is_used = True
        self.used_at = func.now()


class UserSession(TenantBase):
    """Track user sessions for security monitoring."""
    
    __tablename__ = "user_sessions"
    
    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    
    # Session information
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    session_token: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    
    # Session metadata
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    device_id: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Geolocation (if available)
    country: Mapped[Optional[str]] = mapped_column(String(100))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Session status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Session timing
    last_activity: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, is_active={self.is_active})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if session is expired."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc) > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if session is valid."""
        return self.is_active and not self.is_expired
    
    def end_session(self):
        """End the session."""
        self.is_active = False
        self.ended_at = func.now()
"""Repository for authentication data."""
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.repository import BaseRepository
from src.auth.models import AuthUser, RefreshToken, LoginAttempt, PasswordReset, UserSession
from src.auth.schemas import (
    AuthUserCreate, AuthUserUpdate,
    RefreshTokenCreate,
    LoginAttemptCreate,
    PasswordResetCreate,
    UserSessionCreate
)
from src.exceptions import NotFoundError, DatabaseError


class AuthUserRepository(BaseRepository[AuthUser, AuthUserCreate, AuthUserUpdate]):
    """Repository for managing auth users."""
    
    def __init__(self):
        super().__init__(AuthUser)
    
    async def get_by_auth0_user_id(self, auth0_user_id: str) -> Optional[AuthUser]:
        """Get user by Auth0 user ID."""
        return await self.get_by_field("auth0_user_id", auth0_user_id)
    
    async def get_by_email(self, email: str) -> Optional[AuthUser]:
        """Get user by email."""
        return await self.get_by_field("email", email)
    
    async def update_last_login(self, user_id: str) -> Optional[AuthUser]:
        """Update user's last login timestamp and increment login count."""
        async with await self.get_session() as session:
            try:
                query = (
                    update(AuthUser)
                    .where(AuthUser.id == user_id)
                    .values(
                        last_login=func.now(),
                        login_count=AuthUser.login_count + 1,
                        updated_at=func.now()
                    )
                    .returning(AuthUser)
                )
                
                result = await session.execute(query)
                user = result.scalar_one_or_none()
                
                if user:
                    await session.commit()
                    await session.refresh(user)
                else:
                    await session.rollback()
                
                return user
                
            except Exception as e:
                await session.rollback()
                raise DatabaseError(f"Failed to update last login: {str(e)}")
    
    async def block_user(self, user_id: str) -> bool:
        """Block a user."""
        async with await self.get_session() as session:
            try:
                query = (
                    update(AuthUser)
                    .where(AuthUser.id == user_id)
                    .values(is_blocked=True, updated_at=func.now())
                )
                
                result = await session.execute(query)
                await session.commit()
                
                return result.rowcount > 0
                
            except Exception as e:
                await session.rollback()
                raise DatabaseError(f"Failed to block user: {str(e)}")
    
    async def unblock_user(self, user_id: str) -> bool:
        """Unblock a user."""
        async with await self.get_session() as session:
            try:
                query = (
                    update(AuthUser)
                    .where(AuthUser.id == user_id)
                    .values(is_blocked=False, updated_at=func.now())
                )
                
                result = await session.execute(query)
                await session.commit()
                
                return result.rowcount > 0
                
            except Exception as e:
                await session.rollback()
                raise DatabaseError(f"Failed to unblock user: {str(e)}")


class RefreshTokenRepository(BaseRepository[RefreshToken, RefreshTokenCreate, dict]):
    """Repository for managing refresh tokens."""
    
    def __init__(self):
        super().__init__(RefreshToken)
    
    async def get_by_token_hash(self, token_hash: str) -> Optional[RefreshToken]:
        """Get refresh token by hash."""
        return await self.get_by_field("token_hash", token_hash)
    
    async def get_active_tokens_for_user(self, user_id: str) -> List[RefreshToken]:
        """Get all active refresh tokens for a user."""
        return await self.get_multi(
            filters={
                "user_id": user_id,
                "is_active": True,
                "is_revoked": False
            }
        )
    
    async def revoke_token(self, token_id: str) -> bool:
        """Revoke a refresh token."""
        async with await self.get_session() as session:
            try:
                query = (
                    update(RefreshToken)
                    .where(RefreshToken.id == token_id)
                    .values(
                        is_revoked=True,
                        is_active=False,
                        updated_at=func.now()
                    )
                )
                
                result = await session.execute(query)
                await session.commit()
                
                return result.rowcount > 0
                
            except Exception as e:
                await session.rollback()
                raise DatabaseError(f"Failed to revoke token: {str(e)}")
    
    async def revoke_all_user_tokens(self, user_id: str) -> int:
        """Revoke all refresh tokens for a user."""
        async with await self.get_session() as session:
            try:
                query = (
                    update(RefreshToken)
                    .where(RefreshToken.user_id == user_id)
                    .values(
                        is_revoked=True,
                        is_active=False,
                        updated_at=func.now()
                    )
                )
                
                result = await session.execute(query)
                await session.commit()
                
                return result.rowcount
                
            except Exception as e:
                await session.rollback()
                raise DatabaseError(f"Failed to revoke user tokens: {str(e)}")
    
    async def cleanup_expired_tokens(self) -> int:
        """Remove expired refresh tokens."""
        async with await self.get_session() as session:
            try:
                now = datetime.now()
                query = delete(RefreshToken).where(RefreshToken.expires_at < now)
                
                result = await session.execute(query)
                await session.commit()
                
                return result.rowcount
                
            except Exception as e:
                await session.rollback()
                raise DatabaseError(f"Failed to cleanup expired tokens: {str(e)}")


class LoginAttemptRepository(BaseRepository[LoginAttempt, LoginAttemptCreate, dict]):
    """Repository for managing login attempts."""
    
    def __init__(self):
        super().__init__(LoginAttempt)
    
    async def get_recent_attempts_by_email(
        self, 
        email: str, 
        minutes: int = 15
    ) -> List[LoginAttempt]:
        """Get recent login attempts by email."""
        since = datetime.now() - timedelta(minutes=minutes)
        return await self.get_multi(
            filters={
                "email": email,
                "attempted_at": {"gte": since}
            },
            order_by="-attempted_at"
        )
    
    async def get_recent_attempts_by_ip(
        self, 
        ip_address: str, 
        minutes: int = 15
    ) -> List[LoginAttempt]:
        """Get recent login attempts by IP address."""
        since = datetime.now() - timedelta(minutes=minutes)
        return await self.get_multi(
            filters={
                "ip_address": ip_address,
                "attempted_at": {"gte": since}
            },
            order_by="-attempted_at"
        )
    
    async def count_failed_attempts(self, email: str, minutes: int = 15) -> int:
        """Count failed login attempts for email in time window."""
        async with await self.get_session() as session:
            try:
                since = datetime.now() - timedelta(minutes=minutes)
                query = (
                    select(func.count(LoginAttempt.id))
                    .where(
                        and_(
                            LoginAttempt.email == email,
                            LoginAttempt.success == False,
                            LoginAttempt.attempted_at >= since
                        )
                    )
                )
                
                result = await session.execute(query)
                return result.scalar() or 0
                
            except Exception as e:
                raise DatabaseError(f"Failed to count failed attempts: {str(e)}")


class PasswordResetRepository(BaseRepository[PasswordReset, PasswordResetCreate, dict]):
    """Repository for managing password reset tokens."""
    
    def __init__(self):
        super().__init__(PasswordReset)
    
    async def get_by_token_hash(self, token_hash: str) -> Optional[PasswordReset]:
        """Get password reset by token hash."""
        return await self.get_by_field("token_hash", token_hash)
    
    async def get_valid_reset_for_email(self, email: str) -> Optional[PasswordReset]:
        """Get valid (unused, unexpired) password reset for email."""
        async with await self.get_session() as session:
            try:
                now = datetime.now()
                query = (
                    select(PasswordReset)
                    .where(
                        and_(
                            PasswordReset.email == email,
                            PasswordReset.is_used == False,
                            PasswordReset.expires_at > now
                        )
                    )
                    .order_by(PasswordReset.created_at.desc())
                )
                
                result = await session.execute(query)
                return result.scalar_one_or_none()
                
            except Exception as e:
                raise DatabaseError(f"Failed to get valid reset: {str(e)}")
    
    async def mark_as_used(self, reset_id: str) -> bool:
        """Mark password reset as used."""
        async with await self.get_session() as session:
            try:
                query = (
                    update(PasswordReset)
                    .where(PasswordReset.id == reset_id)
                    .values(is_used=True, used_at=func.now())
                )
                
                result = await session.execute(query)
                await session.commit()
                
                return result.rowcount > 0
                
            except Exception as e:
                await session.rollback()
                raise DatabaseError(f"Failed to mark reset as used: {str(e)}")


class UserSessionRepository(BaseRepository[UserSession, UserSessionCreate, dict]):
    """Repository for managing user sessions."""
    
    def __init__(self):
        super().__init__(UserSession)
    
    async def get_by_session_token(self, session_token: str) -> Optional[UserSession]:
        """Get session by token."""
        return await self.get_by_field("session_token", session_token)
    
    async def get_active_sessions_for_user(self, user_id: str) -> List[UserSession]:
        """Get all active sessions for a user."""
        return await self.get_multi(
            filters={"user_id": user_id, "is_active": True},
            order_by="-last_activity"
        )
    
    async def update_activity(self, session_id: str) -> Optional[UserSession]:
        """Update session last activity."""
        async with await self.get_session() as session:
            try:
                query = (
                    update(UserSession)
                    .where(UserSession.id == session_id)
                    .values(last_activity=func.now())
                    .returning(UserSession)
                )
                
                result = await session.execute(query)
                user_session = result.scalar_one_or_none()
                
                if user_session:
                    await session.commit()
                    await session.refresh(user_session)
                else:
                    await session.rollback()
                
                return user_session
                
            except Exception as e:
                await session.rollback()
                raise DatabaseError(f"Failed to update session activity: {str(e)}")
    
    async def end_session(self, session_id: str) -> bool:
        """End a user session."""
        async with await self.get_session() as session:
            try:
                query = (
                    update(UserSession)
                    .where(UserSession.id == session_id)
                    .values(is_active=False, ended_at=func.now())
                )
                
                result = await session.execute(query)
                await session.commit()
                
                return result.rowcount > 0
                
            except Exception as e:
                await session.rollback()
                raise DatabaseError(f"Failed to end session: {str(e)}")
    
    async def end_all_user_sessions(self, user_id: str) -> int:
        """End all sessions for a user."""
        async with await self.get_session() as session:
            try:
                query = (
                    update(UserSession)
                    .where(UserSession.user_id == user_id)
                    .values(is_active=False, ended_at=func.now())
                )
                
                result = await session.execute(query)
                await session.commit()
                
                return result.rowcount
                
            except Exception as e:
                await session.rollback()
                raise DatabaseError(f"Failed to end user sessions: {str(e)}")
    
    async def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions."""
        async with await self.get_session() as session:
            try:
                now = datetime.now()
                query = delete(UserSession).where(UserSession.expires_at < now)
                
                result = await session.execute(query)
                await session.commit()
                
                return result.rowcount
                
            except Exception as e:
                await session.rollback()
                raise DatabaseError(f"Failed to cleanup expired sessions: {str(e)}")
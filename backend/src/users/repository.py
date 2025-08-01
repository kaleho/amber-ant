"""User repository for database operations."""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_, or_, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.repository import BaseRepository
from src.users.models import User, UserProfile, UserSession
from src.users.schemas import UserCreate, UserUpdate, UserProfileCreate, UserProfileUpdate
from src.exceptions import DatabaseError


class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    """Repository for User operations."""
    
    def __init__(self):
        super().__init__(User)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        return await self.get_by_field("email", email)
    
    async def get_by_auth0_id(self, auth0_user_id: str) -> Optional[User]:
        """Get user by Auth0 user ID."""
        return await self.get_by_field("auth0_user_id", auth0_user_id)
    
    async def get_with_profile(self, user_id: str) -> Optional[User]:
        """Get user with profile data."""
        return await self.get_by_id(user_id, load_relationships=["profile"])
    
    async def get_user_stats(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user statistics."""
        async with await self.get_session() as session:
            try:
                # This is a placeholder - in a real implementation,
                # you would join with other tables to get actual stats
                user = await self.get_by_id(user_id)
                if not user:
                    return None
                
                # TODO: Implement actual statistics queries
                # This would involve joining with accounts, transactions, budgets, etc.
                return {
                    "total_accounts": 0,
                    "total_transactions": 0,
                    "total_budgets": 0,
                    "total_goals": 0,
                    "net_worth": 0.0,
                    "monthly_income": 0.0,
                    "monthly_expenses": 0.0,
                    "savings_rate": 0.0,
                    "last_transaction_date": None
                }
                
            except Exception as e:
                raise DatabaseError(f"Failed to get user stats: {str(e)}")
    
    async def search_users(
        self, 
        query: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[User]:
        """Search users by name or email."""
        async with await self.get_session() as session:
            try:
                search_query = select(User).where(
                    or_(
                        User.name.ilike(f"%{query}%"),
                        User.email.ilike(f"%{query}%")
                    )
                ).offset(skip).limit(limit)
                
                result = await session.execute(search_query)
                return list(result.scalars().all())
                
            except Exception as e:
                raise DatabaseError(f"Failed to search users: {str(e)}")


class UserProfileRepository(BaseRepository[UserProfile, UserProfileCreate, UserProfileUpdate]):
    """Repository for UserProfile operations."""
    
    def __init__(self):
        super().__init__(UserProfile)
    
    async def get_by_user_id(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile by user ID."""
        return await self.get_by_field("user_id", user_id)
    
    async def create_for_user(self, user_id: str, data: UserProfileCreate) -> UserProfile:
        """Create profile for specific user."""
        return await self.create(data, user_id=user_id)
    
    async def update_preferences(
        self, 
        user_id: str, 
        preferences: Dict[str, Any]
    ) -> Optional[UserProfile]:
        """Update user preferences."""
        async with await self.get_session() as session:
            try:
                profile = await self.get_by_user_id(user_id)
                if not profile:
                    return None
                
                # Merge new preferences with existing ones
                updated_preferences = profile.preferences.copy()
                updated_preferences.update(preferences)
                
                # Update profile
                update_data = UserProfileUpdate(preferences=updated_preferences)
                return await self.update(profile.id, update_data)
                
            except Exception as e:
                raise DatabaseError(f"Failed to update user preferences: {str(e)}")


class UserSessionRepository(BaseRepository[UserSession, None, None]):
    """Repository for UserSession operations."""
    
    def __init__(self):
        super().__init__(UserSession)
    
    async def get_by_token(self, session_token: str) -> Optional[UserSession]:
        """Get session by token."""
        return await self.get_by_field("session_token", session_token)
    
    async def get_active_sessions(self, user_id: str) -> List[UserSession]:
        """Get all active sessions for user."""
        return await self.get_multi(
            filters={
                "user_id": user_id,
                "is_active": True
            },
            order_by="-created_at"
        )
    
    async def create_session(
        self, 
        user_id: str, 
        session_token: str,
        expires_at,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> UserSession:
        """Create new user session."""
        async with await self.get_session() as session:
            try:
                user_session = UserSession(
                    user_id=user_id,
                    session_token=session_token,
                    expires_at=expires_at,
                    user_agent=user_agent,
                    ip_address=ip_address,
                    is_active=True
                )
                
                session.add(user_session)
                await session.commit()
                await session.refresh(user_session)
                
                return user_session
                
            except Exception as e:
                await session.rollback()
                raise DatabaseError(f"Failed to create user session: {str(e)}")
    
    async def deactivate_session(self, session_token: str) -> bool:
        """Deactivate a session."""
        async with await self.get_session() as session:
            try:
                user_session = await self.get_by_token(session_token)
                if not user_session:
                    return False
                
                user_session.is_active = False
                await session.commit()
                return True
                
            except Exception as e:
                await session.rollback()
                raise DatabaseError(f"Failed to deactivate session: {str(e)}")
    
    async def deactivate_all_user_sessions(self, user_id: str) -> int:
        """Deactivate all sessions for a user."""
        async with await self.get_session() as session:
            try:
                query = (
                    update(UserSession)
                    .where(
                        and_(
                            UserSession.user_id == user_id,
                            UserSession.is_active == True
                        )
                    )
                    .values(is_active=False)
                )
                
                result = await session.execute(query)
                await session.commit()
                
                return result.rowcount
                
            except Exception as e:
                await session.rollback()
                raise DatabaseError(f"Failed to deactivate user sessions: {str(e)}")
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        from datetime import datetime
        
        async with await self.get_session() as session:
            try:
                query = delete(UserSession).where(
                    UserSession.expires_at < datetime.utcnow()
                )
                
                result = await session.execute(query)
                await session.commit()
                
                return result.rowcount
                
            except Exception as e:
                await session.rollback()
                raise DatabaseError(f"Failed to cleanup expired sessions: {str(e)}")
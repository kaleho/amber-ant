"""User service for business logic."""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import secrets

from src.users.repository import UserRepository, UserProfileRepository, UserSessionRepository
from src.users.models import User, UserProfile, UserSession
from src.users.schemas import (
    UserCreate, UserUpdate, UserResponse, UserListResponse, UserStatsResponse,
    UserProfileCreate, UserProfileUpdate, UserProfileResponse,
    UserPreferencesUpdate
)
from src.exceptions import NotFoundError, ValidationError, AuthenticationError
from src.tenant.context import get_tenant_context


class UserService:
    """Service for user business logic."""
    
    def __init__(self):
        self.user_repo = UserRepository()
        self.profile_repo = UserProfileRepository()
        self.session_repo = UserSessionRepository()
    
    async def create_user(self, user_data: UserCreate, auth0_user_id: str) -> UserResponse:
        """Create a new user."""
        # Check if user already exists
        existing_user = await self.user_repo.get_by_email(user_data.email)
        if existing_user:
            raise ValidationError("User with this email already exists")
        
        existing_auth0_user = await self.user_repo.get_by_auth0_id(auth0_user_id)
        if existing_auth0_user:
            raise ValidationError("User with this Auth0 ID already exists")
        
        # Create user
        user = await self.user_repo.create(user_data, auth0_user_id=auth0_user_id)
        
        # Create default profile
        profile_data = UserProfileCreate()
        profile = await self.profile_repo.create_for_user(user.id, profile_data)
        
        return UserResponse.model_validate(user)
    
    async def get_user(self, user_id: str) -> Optional[UserResponse]:
        """Get user by ID."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return None
        
        return UserResponse.model_validate(user)
    
    async def get_user_by_email(self, email: str) -> Optional[UserResponse]:
        """Get user by email."""
        user = await self.user_repo.get_by_email(email)
        if not user:
            return None
        
        return UserResponse.model_validate(user)
    
    async def get_user_by_auth0_id(self, auth0_user_id: str) -> Optional[UserResponse]:
        """Get user by Auth0 ID."""
        user = await self.user_repo.get_by_auth0_id(auth0_user_id)
        if not user:
            return None
        
        return UserResponse.model_validate(user)
    
    async def update_user(self, user_id: str, user_data: UserUpdate) -> Optional[UserResponse]:
        """Update user."""
        user = await self.user_repo.update(user_id, user_data)
        if not user:
            return None
        
        return UserResponse.model_validate(user)
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user."""
        # TODO: Implement soft delete or cascading delete logic
        # This should also clean up related data (accounts, transactions, etc.)
        return await self.user_repo.delete(user_id)
    
    async def get_users(
        self, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None
    ) -> UserListResponse:
        """Get list of users with pagination."""
        if search:
            users = await self.user_repo.search_users(search, skip, limit)
            total = len(users)  # Simplified - should implement proper search count
        else:
            users = await self.user_repo.get_multi(skip=skip, limit=limit, order_by="-created_at")
            total = await self.user_repo.count()
        
        user_responses = [UserResponse.model_validate(user) for user in users]
        
        return UserListResponse(
            users=user_responses,
            total=total,
            page=(skip // limit) + 1,
            per_page=limit,
            total_pages=(total + limit - 1) // limit
        )
    
    async def get_user_stats(self, user_id: str) -> Optional[UserStatsResponse]:
        """Get user statistics."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return None
        
        stats = await self.user_repo.get_user_stats(user_id)
        if not stats:
            return None
        
        return UserStatsResponse(**stats)
    
    async def get_user_profile(self, user_id: str) -> Optional[UserProfileResponse]:
        """Get user profile."""
        profile = await self.profile_repo.get_by_user_id(user_id)
        if not profile:
            return None
        
        return UserProfileResponse.model_validate(profile)
    
    async def update_user_profile(
        self, 
        user_id: str, 
        profile_data: UserProfileUpdate
    ) -> Optional[UserProfileResponse]:
        """Update user profile."""
        profile = await self.profile_repo.get_by_user_id(user_id)
        if not profile:
            # Create profile if it doesn't exist
            create_data = UserProfileCreate()
            profile = await self.profile_repo.create_for_user(user_id, create_data)
        
        updated_profile = await self.profile_repo.update(profile.id, profile_data)
        if not updated_profile:
            return None
        
        return UserProfileResponse.model_validate(updated_profile)
    
    async def update_user_preferences(
        self, 
        user_id: str, 
        preferences_data: UserPreferencesUpdate
    ) -> Optional[UserProfileResponse]:
        """Update user preferences."""
        # Convert preferences to dict
        preferences = preferences_data.model_dump(exclude_unset=True, exclude_none=True)
        
        updated_profile = await self.profile_repo.update_preferences(user_id, preferences)
        if not updated_profile:
            return None
        
        return UserProfileResponse.model_validate(updated_profile)
    
    async def create_user_session(
        self, 
        user_id: str,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        expires_in_hours: int = 24
    ) -> str:
        """Create a new user session."""
        # Generate secure session token
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        
        await self.session_repo.create_session(
            user_id=user_id,
            session_token=session_token,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address
        )
        
        return session_token
    
    async def validate_user_session(self, session_token: str) -> Optional[User]:
        """Validate user session and return user."""
        session = await self.session_repo.get_by_token(session_token)
        
        if not session:
            return None
        
        if not session.is_active:
            return None
        
        if session.expires_at < datetime.utcnow():
            # Deactivate expired session
            await self.session_repo.deactivate_session(session_token)
            return None
        
        # Update last accessed time
        session.last_accessed_at = datetime.utcnow()
        
        # Get user
        user = await self.user_repo.get_by_id(session.user_id)
        return user
    
    async def logout_user(self, session_token: str) -> bool:
        """Logout user by deactivating session."""
        return await self.session_repo.deactivate_session(session_token)
    
    async def logout_all_user_sessions(self, user_id: str) -> int:
        """Logout all user sessions."""
        return await self.session_repo.deactivate_all_user_sessions(user_id)
    
    async def get_user_sessions(self, user_id: str) -> List[UserSession]:
        """Get all active sessions for user."""
        return await self.session_repo.get_active_sessions(user_id)
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        return await self.session_repo.cleanup_expired_sessions()
    
    async def is_user_in_tenant(self, user_id: str) -> bool:
        """Check if user belongs to current tenant."""
        tenant_context = get_tenant_context()
        
        # TODO: Implement proper tenant membership check
        # This would involve checking tenant_users table or similar
        
        user = await self.user_repo.get_by_id(user_id)
        return user is not None
"""User API router."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer

from src.users.service import UserService
from src.users.schemas import (
    UserCreate, UserUpdate, UserResponse, UserListResponse, UserStatsResponse,
    UserProfileUpdate, UserProfileResponse, UserPreferencesUpdate
)
from src.auth.dependencies import get_current_user, get_current_active_user
from src.exceptions import NotFoundError, ValidationError

router = APIRouter()
security = HTTPBearer()

# Initialize service
user_service = UserService()


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: dict = Depends(get_current_active_user)
):
    """Get current user profile."""
    user = await user_service.get_user(current_user["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user: dict = Depends(get_current_active_user)
):
    """Update current user."""
    try:
        user = await user_service.update_user(current_user["user_id"], user_data)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return user
        
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.delete("/me")
async def delete_current_user(
    current_user: dict = Depends(get_current_active_user)
):
    """Delete current user account."""
    success = await user_service.delete_user(current_user["user_id"])
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User account deleted successfully"}


@router.get("/me/stats", response_model=UserStatsResponse)
async def get_current_user_stats(
    current_user: dict = Depends(get_current_active_user)
):
    """Get current user statistics."""
    stats = await user_service.get_user_stats(current_user["user_id"])
    if not stats:
        raise HTTPException(status_code=404, detail="User stats not found")
    
    return stats


@router.get("/me/profile", response_model=UserProfileResponse)
async def get_current_user_profile_details(
    current_user: dict = Depends(get_current_active_user)
):
    """Get current user profile details."""
    profile = await user_service.get_user_profile(current_user["user_id"])
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    
    return profile


@router.put("/me/profile", response_model=UserProfileResponse)
async def update_current_user_profile(
    profile_data: UserProfileUpdate,
    current_user: dict = Depends(get_current_active_user)
):
    """Update current user profile."""
    try:
        profile = await user_service.update_user_profile(current_user["user_id"], profile_data)
        if not profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        return profile
        
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.put("/me/preferences", response_model=UserProfileResponse)
async def update_current_user_preferences(
    preferences_data: UserPreferencesUpdate,
    current_user: dict = Depends(get_current_active_user)
):
    """Update current user preferences."""
    try:
        profile = await user_service.update_user_preferences(current_user["user_id"], preferences_data)
        if not profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        return profile
        
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/me/logout")
async def logout_current_user(
    current_user: dict = Depends(get_current_user)
):
    """Logout current user (invalidate session)."""
    # TODO: Get session token from request and invalidate it
    # This requires proper session management implementation
    
    return {"message": "Logged out successfully"}


@router.post("/me/logout-all")
async def logout_all_user_sessions(
    current_user: dict = Depends(get_current_active_user)
):
    """Logout all user sessions."""
    count = await user_service.logout_all_user_sessions(current_user["user_id"])
    
    return {"message": f"Logged out {count} sessions successfully"}


# Admin endpoints (would typically require admin permissions)
@router.get("", response_model=UserListResponse)
async def get_users(
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of users to return"),
    search: Optional[str] = Query(None, description="Search users by name or email"),
    current_user: dict = Depends(get_current_active_user)
):
    """Get list of users (admin only)."""
    # TODO: Add admin permission check
    
    try:
        return await user_service.get_users(skip=skip, limit=limit, search=search)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve users")


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Get user by ID (admin only)."""
    # TODO: Add admin permission check or allow users to view their own profile
    
    user = await user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: dict = Depends(get_current_active_user)
):
    """Update user by ID (admin only)."""
    # TODO: Add admin permission check
    
    try:
        user = await user_service.update_user(user_id, user_data)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return user
        
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Delete user by ID (admin only)."""
    # TODO: Add admin permission check
    
    success = await user_service.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User deleted successfully"}


@router.get("/{user_id}/stats", response_model=UserStatsResponse)
async def get_user_stats(
    user_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Get user statistics (admin only)."""
    # TODO: Add admin permission check
    
    stats = await user_service.get_user_stats(user_id)
    if not stats:
        raise HTTPException(status_code=404, detail="User stats not found")
    
    return stats
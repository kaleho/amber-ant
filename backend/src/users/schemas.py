"""User domain Pydantic schemas."""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal


class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr = Field(..., description="User email address")
    name: str = Field(..., min_length=1, max_length=100, description="User full name")
    is_active: bool = Field(default=True, description="Whether user account is active")


class UserCreate(UserBase):
    """Schema for creating a new user."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "john.doe@example.com",
                "name": "John Doe",
                "is_active": True
            }
        }
    )


class UserUpdate(BaseModel):
    """Schema for updating user information."""
    email: Optional[EmailStr] = Field(None, description="Updated email address")
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Updated name")
    is_active: Optional[bool] = Field(None, description="Updated active status")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "John Updated Doe",
                "is_active": True
            }
        }
    )


class UserResponse(UserBase):
    """Schema for user responses."""
    id: str = Field(..., description="User unique identifier")
    auth0_user_id: str = Field(..., description="Auth0 user identifier")
    created_at: datetime = Field(..., description="User creation timestamp")
    updated_at: datetime = Field(..., description="User last update timestamp")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "john.doe@example.com",
                "name": "John Doe",
                "auth0_user_id": "auth0|123456789",
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }
    )


class UserProfileBase(BaseModel):
    """Base user profile schema."""
    first_name: Optional[str] = Field(None, max_length=50, description="User first name")
    last_name: Optional[str] = Field(None, max_length=50, description="User last name")
    phone_number: Optional[str] = Field(None, max_length=20, description="User phone number")
    timezone: str = Field(default="UTC", max_length=50, description="User timezone")
    locale: str = Field(default="en-US", max_length=10, description="User locale")
    currency: str = Field(default="USD", max_length=3, description="User preferred currency")


class UserProfileCreate(UserProfileBase):
    """Schema for creating user profile."""
    pass


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile."""
    first_name: Optional[str] = Field(None, max_length=50, description="Updated first name")
    last_name: Optional[str] = Field(None, max_length=50, description="Updated last name")
    phone_number: Optional[str] = Field(None, max_length=20, description="Updated phone number")
    timezone: Optional[str] = Field(None, max_length=50, description="Updated timezone")
    locale: Optional[str] = Field(None, max_length=10, description="Updated locale")
    currency: Optional[str] = Field(None, max_length=3, description="Updated currency")
    avatar_url: Optional[str] = Field(None, description="Updated avatar URL")
    preferences: Optional[Dict[str, Any]] = Field(None, description="Updated user preferences")
    onboarding_completed: Optional[bool] = Field(None, description="Onboarding completion status")


class UserProfileResponse(UserProfileBase):
    """Schema for user profile responses."""
    id: str = Field(..., description="Profile unique identifier")
    user_id: str = Field(..., description="Associated user ID")
    avatar_url: Optional[str] = Field(None, description="User avatar URL")
    date_of_birth: Optional[datetime] = Field(None, description="User date of birth")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences")
    onboarding_completed: bool = Field(default=False, description="Onboarding completion status")
    onboarding_step: Optional[str] = Field(None, description="Current onboarding step")
    created_at: datetime = Field(..., description="Profile creation timestamp")
    updated_at: datetime = Field(..., description="Profile last update timestamp")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174001",
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "first_name": "John",
                "last_name": "Doe",
                "phone_number": "+1234567890",
                "timezone": "America/New_York",
                "locale": "en-US",
                "currency": "USD",
                "avatar_url": "https://example.com/avatar.jpg",
                "preferences": {"theme": "light", "notifications": True},
                "onboarding_completed": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }
    )


class UserSessionBase(BaseModel):
    """Base user session schema."""
    session_token: str = Field(..., description="Session token")
    expires_at: datetime = Field(..., description="Session expiration time")


class UserSessionCreate(UserSessionBase):
    """Schema for creating user session."""
    user_agent: Optional[str] = Field(None, description="User agent string")
    ip_address: Optional[str] = Field(None, description="User IP address")


class UserSessionResponse(UserSessionBase):
    """Schema for user session responses."""
    id: str = Field(..., description="Session unique identifier")
    user_id: str = Field(..., description="Associated user ID")
    user_agent: Optional[str] = Field(None, description="User agent string")
    ip_address: Optional[str] = Field(None, description="User IP address")
    is_active: bool = Field(default=True, description="Session active status")
    last_accessed_at: Optional[datetime] = Field(None, description="Last access timestamp")
    created_at: datetime = Field(..., description="Session creation timestamp")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174002",
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "session_token": "session_abc123",
                "expires_at": "2024-01-08T00:00:00Z",
                "user_agent": "Mozilla/5.0...",
                "ip_address": "192.168.1.1",
                "is_active": True,
                "last_accessed_at": "2024-01-01T12:00:00Z",
                "created_at": "2024-01-01T00:00:00Z"
            }
        }
    )


class UserListResponse(BaseModel):
    """Schema for paginated user list responses."""
    users: List[UserResponse] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "users": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "email": "john.doe@example.com",
                        "name": "John Doe",
                        "auth0_user_id": "auth0|123456789",
                        "is_active": True,
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z"
                    }
                ],
                "total": 50,
                "page": 1,
                "per_page": 10,
                "total_pages": 5
            }
        }
    )


class UserStatsResponse(BaseModel):
    """Schema for user statistics responses."""
    total_accounts: int = Field(..., description="Total number of accounts")
    total_transactions: int = Field(..., description="Total number of transactions")
    total_budgets: int = Field(..., description="Total number of budgets")
    total_goals: int = Field(..., description="Total number of savings goals")
    net_worth: Decimal = Field(..., description="User net worth")
    monthly_income: Decimal = Field(..., description="Monthly income")
    monthly_expenses: Decimal = Field(..., description="Monthly expenses")
    savings_rate: Decimal = Field(..., description="Savings rate percentage")
    last_transaction_date: Optional[datetime] = Field(None, description="Last transaction date")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_accounts": 5,
                "total_transactions": 150,
                "total_budgets": 3,
                "total_goals": 2,
                "net_worth": "25000.00",
                "monthly_income": "5000.00",
                "monthly_expenses": "3500.00",
                "savings_rate": "30.00",
                "last_transaction_date": "2024-01-15T00:00:00Z"
            }
        }
    )


class UserPreferencesUpdate(BaseModel):
    """Schema for updating user preferences."""
    theme: Optional[str] = Field(None, description="UI theme preference")
    notifications_enabled: Optional[bool] = Field(None, description="Notifications preference")
    email_notifications: Optional[bool] = Field(None, description="Email notifications preference")
    push_notifications: Optional[bool] = Field(None, description="Push notifications preference")
    budget_alerts: Optional[bool] = Field(None, description="Budget alerts preference")
    goal_reminders: Optional[bool] = Field(None, description="Goal reminders preference")
    weekly_reports: Optional[bool] = Field(None, description="Weekly reports preference")
    monthly_reports: Optional[bool] = Field(None, description="Monthly reports preference")
    data_retention_days: Optional[int] = Field(None, description="Data retention preference")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "theme": "dark",
                "notifications_enabled": True,
                "email_notifications": True,
                "push_notifications": False,
                "budget_alerts": True,
                "goal_reminders": True,
                "weekly_reports": True,
                "monthly_reports": True,
                "data_retention_days": 365
            }
        }
    )
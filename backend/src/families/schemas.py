"""Families domain Pydantic schemas."""
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class FamilyRole(str, Enum):
    """Family member role enumeration."""
    ADMINISTRATOR = "administrator"
    SPOUSE = "spouse"
    TEEN = "teen"
    PRE_TEEN = "pre_teen"
    SUPPORT = "support"
    AGENT = "agent"


class FamilyMemberStatus(str, Enum):
    """Family member status enumeration."""
    ACTIVE = "active"
    INVITED = "invited"
    SUSPENDED = "suspended"


class InvitationStatus(str, Enum):
    """Family invitation status enumeration."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class ApprovalStatus(str, Enum):
    """Spending approval status enumeration."""
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"


class FamilyBase(BaseModel):
    """Base family schema with common fields."""
    name: str = Field(..., min_length=1, max_length=100, description="Family name")
    description: Optional[str] = Field(None, description="Family description")
    max_members: int = Field(default=10, ge=2, le=50, description="Maximum number of family members")
    plan_type: str = Field(default="basic", max_length=50, description="Family plan type")


class FamilyCreate(FamilyBase):
    """Schema for creating a new family."""
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Family settings")
    is_active: bool = Field(default=True, description="Family active status")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "The Smith Family",
                "description": "Family financial management for the Smith household",
                "max_members": 6,
                "plan_type": "premium",
                "settings": {
                    "allow_teen_transactions": True,
                    "require_approval_over": "100.00",
                    "weekly_allowance": True
                },
                "is_active": True
            }
        }
    )


class FamilyUpdate(BaseModel):
    """Schema for updating family information."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Updated family name")
    description: Optional[str] = Field(None, description="Updated family description")
    max_members: Optional[int] = Field(None, ge=2, le=50, description="Updated max members")
    plan_type: Optional[str] = Field(None, max_length=50, description="Updated plan type")
    settings: Optional[Dict[str, Any]] = Field(None, description="Updated family settings")
    is_active: Optional[bool] = Field(None, description="Updated active status")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Updated Family Name",
                "max_members": 8,
                "settings": {
                    "allow_teen_transactions": True,
                    "require_approval_over": "150.00"
                }
            }
        }
    )


class FamilyResponse(FamilyBase):
    """Schema for family responses."""
    id: str = Field(..., description="Family unique identifier")
    administrator_id: str = Field(..., description="Family administrator user ID")
    current_member_count: int = Field(..., description="Current number of family members")
    is_active: bool = Field(default=True, description="Family active status")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Family settings")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(..., description="Family creation timestamp")
    updated_at: datetime = Field(..., description="Family last update timestamp")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174016",
                "name": "The Smith Family",
                "description": "Family financial management for the Smith household",
                "administrator_id": "123e4567-e89b-12d3-a456-426614174001",
                "max_members": 6,
                "current_member_count": 4,
                "plan_type": "premium",
                "is_active": True,
                "settings": {
                    "allow_teen_transactions": True,
                    "require_approval_over": "100.00"
                },
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-15T12:00:00Z"
            }
        }
    )


class FamilyMemberBase(BaseModel):
    """Base family member schema."""
    name: str = Field(..., min_length=1, max_length=100, description="Member name")
    email: EmailStr = Field(..., description="Member email address")
    role: FamilyRole = Field(..., description="Member role in family")
    spending_limit: Optional[Decimal] = Field(None, ge=0, description="Member spending limit")
    requires_approval_over: Optional[Decimal] = Field(None, ge=0, description="Amount requiring approval")
    approved_categories: Optional[List[str]] = Field(default_factory=list, description="Pre-approved categories")


class FamilyMemberCreate(FamilyMemberBase):
    """Schema for creating family member."""
    permissions: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Member permissions")
    status: FamilyMemberStatus = Field(default=FamilyMemberStatus.ACTIVE, description="Member status")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Jane Smith",
                "email": "jane.smith@example.com",
                "role": "spouse",
                "spending_limit": "1000.00",
                "requires_approval_over": "500.00",
                "approved_categories": ["Food & Dining", "Transportation", "Personal Care"],
                "permissions": {
                    "can_view_budgets": True,
                    "can_edit_budgets": False,
                    "can_create_goals": True
                },
                "status": "active"
            }
        }
    )


class FamilyMemberUpdate(BaseModel):
    """Schema for updating family member."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Updated member name")
    role: Optional[FamilyRole] = Field(None, description="Updated member role")
    spending_limit: Optional[Decimal] = Field(None, ge=0, description="Updated spending limit")
    requires_approval_over: Optional[Decimal] = Field(None, ge=0, description="Updated approval threshold")
    approved_categories: Optional[List[str]] = Field(None, description="Updated approved categories")
    permissions: Optional[Dict[str, Any]] = Field(None, description="Updated permissions")
    status: Optional[FamilyMemberStatus] = Field(None, description="Updated status")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "role": "teen",
                "spending_limit": "200.00",
                "requires_approval_over": "50.00",
                "approved_categories": ["Food & Dining", "School Supplies"]
            }
        }
    )


class FamilyMemberResponse(FamilyMemberBase):
    """Schema for family member responses."""
    id: str = Field(..., description="Member unique identifier")
    family_id: str = Field(..., description="Associated family ID")
    user_id: str = Field(..., description="Associated user ID")
    status: FamilyMemberStatus = Field(..., description="Member status")
    permissions: Dict[str, Any] = Field(default_factory=dict, description="Member permissions")
    last_active_at: Optional[datetime] = Field(None, description="Last activity timestamp")
    joined_at: datetime = Field(..., description="Member join timestamp")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174017",
                "family_id": "123e4567-e89b-12d3-a456-426614174016",
                "user_id": "123e4567-e89b-12d3-a456-426614174002",
                "name": "Jane Smith",
                "email": "jane.smith@example.com",
                "role": "spouse",
                "status": "active",
                "spending_limit": "1000.00",
                "requires_approval_over": "500.00",
                "approved_categories": ["Food & Dining", "Transportation"],
                "permissions": {
                    "can_view_budgets": True,
                    "can_edit_budgets": False
                },
                "last_active_at": "2024-01-15T14:30:00Z",
                "joined_at": "2024-01-01T00:00:00Z"
            }
        }
    )


class FamilyInvitationBase(BaseModel):
    """Base family invitation schema."""
    email: EmailStr = Field(..., description="Invitee email address")
    role: FamilyRole = Field(..., description="Invited role")
    message: Optional[str] = Field(None, description="Invitation message")


class FamilyInvitationCreate(FamilyInvitationBase):
    """Schema for creating family invitation."""
    permissions: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Invited member permissions")
    expires_in_days: int = Field(default=7, ge=1, le=30, description="Invitation expiration days")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "teen@example.com",
                "role": "teen",
                "message": "Welcome to our family financial planning!",
                "permissions": {
                    "can_view_budgets": True,
                    "can_create_goals": True,
                    "spending_limit": "100.00"
                },
                "expires_in_days": 7
            }
        }
    )


class FamilyInvitationResponse(FamilyInvitationBase):
    """Schema for family invitation responses."""
    id: str = Field(..., description="Invitation unique identifier")
    family_id: str = Field(..., description="Associated family ID")
    inviter_id: str = Field(..., description="Inviter user ID")
    permissions: Dict[str, Any] = Field(default_factory=dict, description="Invited permissions")
    status: InvitationStatus = Field(..., description="Invitation status")
    invitation_token: str = Field(..., description="Invitation token")
    expires_at: datetime = Field(..., description="Invitation expiration timestamp")
    accepted_at: Optional[datetime] = Field(None, description="Acceptance timestamp")
    accepted_by_user_id: Optional[str] = Field(None, description="Accepting user ID")
    created_at: datetime = Field(..., description="Invitation creation timestamp")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174018",
                "family_id": "123e4567-e89b-12d3-a456-426614174016",
                "inviter_id": "123e4567-e89b-12d3-a456-426614174001",
                "email": "teen@example.com",
                "role": "teen",
                "message": "Welcome to our family financial planning!",
                "permissions": {
                    "can_view_budgets": True,
                    "spending_limit": "100.00"
                },
                "status": "pending",
                "invitation_token": "inv_abc123def456",
                "expires_at": "2024-01-08T00:00:00Z",
                "created_at": "2024-01-01T00:00:00Z"
            }
        }
    )


class FamilyBudgetBase(BaseModel):
    """Base family budget schema."""
    name: str = Field(..., min_length=1, max_length=100, description="Budget name")
    description: Optional[str] = Field(None, description="Budget description")
    budget_data: Dict[str, Any] = Field(..., description="Budget configuration data")
    accessible_by: List[str] = Field(default_factory=list, description="User IDs with access")
    editable_by: List[str] = Field(default_factory=list, description="User IDs with edit permission")


class FamilyBudgetCreate(FamilyBudgetBase):
    """Schema for creating family budget."""
    is_active: bool = Field(default=True, description="Budget active status")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Family Monthly Budget",
                "description": "Shared monthly budget for family expenses",
                "budget_data": {
                    "total_amount": "4000.00",
                    "categories": [
                        {"name": "Groceries", "amount": "800.00"},
                        {"name": "Utilities", "amount": "300.00"}
                    ]
                },
                "accessible_by": ["user1", "user2", "user3"],
                "editable_by": ["user1", "user2"],
                "is_active": True
            }
        }
    )


class FamilyBudgetResponse(FamilyBudgetBase):
    """Schema for family budget responses."""
    id: str = Field(..., description="Budget unique identifier")
    family_id: str = Field(..., description="Associated family ID")
    created_by: str = Field(..., description="Creator user ID")
    is_active: bool = Field(default=True, description="Budget active status")
    created_at: datetime = Field(..., description="Budget creation timestamp")
    updated_at: datetime = Field(..., description="Budget last update timestamp")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174019",
                "family_id": "123e4567-e89b-12d3-a456-426614174016",
                "created_by": "123e4567-e89b-12d3-a456-426614174001",
                "name": "Family Monthly Budget",
                "description": "Shared monthly budget for family expenses",
                "budget_data": {
                    "total_amount": "4000.00",
                    "spent_amount": "1500.00"
                },
                "accessible_by": ["user1", "user2", "user3"],
                "editable_by": ["user1", "user2"],
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-15T12:00:00Z"
            }
        }
    )


class SpendingApprovalRequestBase(BaseModel):
    """Base spending approval request schema."""
    amount: Decimal = Field(..., gt=0, description="Requested spending amount")
    description: str = Field(..., min_length=1, description="Spending description")
    category: Optional[str] = Field(None, max_length=100, description="Spending category")
    merchant: Optional[str] = Field(None, max_length=255, description="Merchant name")


class SpendingApprovalRequestCreate(SpendingApprovalRequestBase):
    """Schema for creating spending approval request."""
    transaction_id: Optional[str] = Field(None, description="Associated transaction ID")
    account_id: Optional[str] = Field(None, description="Associated account ID")
    expires_in_hours: int = Field(default=24, ge=1, le=168, description="Request expiration hours")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "amount": "75.00",
                "description": "New video game purchase",
                "category": "Entertainment",
                "merchant": "GameStop",
                "expires_in_hours": 48
            }
        }
    )


class SpendingApprovalRequestResponse(SpendingApprovalRequestBase):
    """Schema for spending approval request responses."""
    id: str = Field(..., description="Request unique identifier")
    family_id: str = Field(..., description="Associated family ID")
    member_id: str = Field(..., description="Requesting member ID")
    transaction_id: Optional[str] = Field(None, description="Associated transaction ID")
    account_id: Optional[str] = Field(None, description="Associated account ID")
    status: ApprovalStatus = Field(..., description="Request status")
    approved_by: Optional[str] = Field(None, description="Approver user ID")
    approved_at: Optional[datetime] = Field(None, description="Approval timestamp")
    approval_notes: Optional[str] = Field(None, description="Approval notes")
    expires_at: datetime = Field(..., description="Request expiration timestamp")
    created_at: datetime = Field(..., description="Request creation timestamp")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174020",
                "family_id": "123e4567-e89b-12d3-a456-426614174016",
                "member_id": "123e4567-e89b-12d3-a456-426614174017",
                "amount": "75.00",
                "description": "New video game purchase",
                "category": "Entertainment",
                "merchant": "GameStop",
                "status": "pending",
                "expires_at": "2024-01-03T10:00:00Z",
                "created_at": "2024-01-01T10:00:00Z"
            }
        }
    )


class SpendingApprovalDecision(BaseModel):
    """Schema for spending approval decision."""
    decision: ApprovalStatus = Field(..., description="Approval decision")
    notes: Optional[str] = Field(None, description="Decision notes")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "decision": "approved",
                "notes": "Approved for good grades this month"
            }
        }
    )


class FamilyListResponse(BaseModel):
    """Schema for paginated family list responses."""
    families: List[FamilyResponse] = Field(..., description="List of families")
    total: int = Field(..., description="Total number of families")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "families": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174016",
                        "name": "The Smith Family",
                        "administrator_id": "123e4567-e89b-12d3-a456-426614174001",
                        "max_members": 6,
                        "current_member_count": 4,
                        "plan_type": "premium",
                        "is_active": True,
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-15T12:00:00Z"
                    }
                ],
                "total": 1,
                "page": 1,
                "per_page": 10,
                "total_pages": 1
            }
        }
    )


class FamilyDashboardResponse(BaseModel):
    """Schema for family dashboard responses."""
    family_id: str = Field(..., description="Family ID")
    member_count: int = Field(..., description="Current member count")
    pending_invitations: int = Field(..., description="Number of pending invitations")
    pending_approvals: int = Field(..., description="Number of pending approval requests")
    shared_budgets: int = Field(..., description="Number of shared budgets")
    shared_goals: int = Field(..., description="Number of shared goals")
    total_family_spending: Decimal = Field(..., description="Total family spending this month")
    recent_activities: List[Dict[str, Any]] = Field(..., description="Recent family activities")
    upcoming_approvals: List[SpendingApprovalRequestResponse] = Field(..., description="Upcoming approval deadlines")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "family_id": "123e4567-e89b-12d3-a456-426614174016",
                "member_count": 4,
                "pending_invitations": 1,
                "pending_approvals": 2,
                "shared_budgets": 3,
                "shared_goals": 2,
                "total_family_spending": "2500.00",
                "recent_activities": [
                    {
                        "type": "spending_request",
                        "member": "Jane Smith",
                        "amount": "75.00",
                        "description": "Video game purchase",
                        "timestamp": "2024-01-15T10:00:00Z"
                    }
                ],
                "upcoming_approvals": []
            }
        }
    )
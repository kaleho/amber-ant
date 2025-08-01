"""Family management API endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from src.families.service import FamilyService
from src.families.schemas import (
    FamilyCreate, FamilyUpdate, FamilyResponse,
    FamilyMemberCreate, FamilyMemberUpdate, FamilyMemberResponse,
    FamilyInvitationCreate, FamilyInvitationResponse,
    FamilyBudgetCreate, FamilyBudgetResponse,
    SpendingApprovalRequestCreate, SpendingApprovalRequestResponse,
    SpendingApprovalDecision, FamilyDashboardResponse,
    FamilyListResponse
)
from src.auth.dependencies import get_current_user
from src.exceptions import NotFoundError, ValidationError, BusinessLogicError

router = APIRouter()


# Family CRUD operations
@router.post("/", response_model=FamilyResponse, status_code=status.HTTP_201_CREATED)
async def create_family(
    family_data: FamilyCreate,
    current_user: dict = Depends(get_current_user),
    family_service: FamilyService = Depends()
):
    """Create a new family."""
    try:
        family = await family_service.create_family(
            family_data=family_data,
            administrator_id=current_user["sub"]
        )
        return family
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/", response_model=List[FamilyResponse])
async def get_user_families(
    include_inactive: bool = Query(False, description="Include inactive families"),
    current_user: dict = Depends(get_current_user),
    family_service: FamilyService = Depends()
):
    """Get families where the current user is a member."""
    families = await family_service.get_user_families(
        user_id=current_user["sub"],
        include_inactive=include_inactive
    )
    return families


@router.get("/{family_id}", response_model=FamilyResponse)
async def get_family(
    family_id: str,
    current_user: dict = Depends(get_current_user),
    family_service: FamilyService = Depends()
):
    """Get family by ID."""
    family = await family_service.get_family(family_id, current_user["sub"])
    if not family:
        raise HTTPException(status_code=404, detail="Family not found")
    return family


@router.put("/{family_id}", response_model=FamilyResponse)
async def update_family(
    family_id: str,
    family_data: FamilyUpdate,
    current_user: dict = Depends(get_current_user),
    family_service: FamilyService = Depends()
):
    """Update family (administrator only)."""
    try:
        family = await family_service.update_family(
            family_id=family_id,
            family_data=family_data,
            user_id=current_user["sub"]
        )
        if not family:
            raise HTTPException(status_code=404, detail="Family not found or insufficient permissions")
        return family
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{family_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_family(
    family_id: str,
    current_user: dict = Depends(get_current_user),
    family_service: FamilyService = Depends()
):
    """Delete family (administrator only)."""
    success = await family_service.delete_family(family_id, current_user["sub"])
    if not success:
        raise HTTPException(status_code=404, detail="Family not found or insufficient permissions")


# Family member operations
@router.get("/{family_id}/members", response_model=List[FamilyMemberResponse])
async def get_family_members(
    family_id: str,
    include_inactive: bool = Query(False, description="Include inactive members"),
    current_user: dict = Depends(get_current_user),
    family_service: FamilyService = Depends()
):
    """Get family members."""
    members = await family_service.get_family_members(
        family_id=family_id,
        user_id=current_user["sub"],
        include_inactive=include_inactive
    )
    return members


@router.post("/{family_id}/members", response_model=FamilyMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_family_member(
    family_id: str,
    member_data: FamilyMemberCreate,
    current_user: dict = Depends(get_current_user),
    family_service: FamilyService = Depends()
):
    """Add member to family (administrator only)."""
    try:
        member = await family_service.add_family_member(
            family_id=family_id,
            member_data=member_data,
            added_by_user_id=current_user["sub"]
        )
        if not member:
            raise HTTPException(status_code=403, detail="Insufficient permissions or family is full")
        return member
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/members/{member_id}", response_model=FamilyMemberResponse)
async def update_family_member(
    member_id: str,
    member_data: FamilyMemberUpdate,
    current_user: dict = Depends(get_current_user),
    family_service: FamilyService = Depends()
):
    """Update family member."""
    try:
        member = await family_service.update_family_member(
            member_id=member_id,
            member_data=member_data,
            updated_by_user_id=current_user["sub"]
        )
        if not member:
            raise HTTPException(status_code=404, detail="Member not found or insufficient permissions")
        return member
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_family_member(
    member_id: str,
    current_user: dict = Depends(get_current_user),
    family_service: FamilyService = Depends()
):
    """Remove member from family."""
    success = await family_service.remove_family_member(member_id, current_user["sub"])
    if not success:
        raise HTTPException(status_code=404, detail="Member not found or insufficient permissions")


# Family invitation operations
@router.post("/{family_id}/invitations", response_model=FamilyInvitationResponse, status_code=status.HTTP_201_CREATED)
async def create_invitation(
    family_id: str,
    invitation_data: FamilyInvitationCreate,
    current_user: dict = Depends(get_current_user),
    family_service: FamilyService = Depends()
):
    """Create family invitation (administrator only)."""
    try:
        invitation = await family_service.create_invitation(
            family_id=family_id,
            invitation_data=invitation_data,
            inviter_id=current_user["sub"]
        )
        return invitation
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{family_id}/invitations", response_model=List[FamilyInvitationResponse])
async def get_family_invitations(
    family_id: str,
    include_expired: bool = Query(False, description="Include expired invitations"),
    current_user: dict = Depends(get_current_user),
    family_service: FamilyService = Depends()
):
    """Get family invitations (administrator only)."""
    invitations = await family_service.get_family_invitations(
        family_id=family_id,
        user_id=current_user["sub"],
        include_expired=include_expired
    )
    return invitations


@router.get("/invitations/{token}")
async def get_invitation_details(
    token: str,
    family_service: FamilyService = Depends()
):
    """Get invitation details by token (for accepting invitations)."""
    invitation = await family_service.get_invitation_by_token(token)
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found or expired")
    
    return {
        "family_name": invitation.family.name,
        "role": invitation.role,
        "inviter_email": invitation.email,
        "message": invitation.message,
        "expires_at": invitation.expires_at
    }


@router.post("/invitations/{token}/accept", response_model=FamilyMemberResponse)
async def accept_invitation(
    token: str,
    current_user: dict = Depends(get_current_user),
    family_service: FamilyService = Depends()
):
    """Accept family invitation."""
    try:
        member = await family_service.accept_invitation(token, current_user["sub"])
        return member
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/invitations/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_invitation(
    invitation_id: str,
    current_user: dict = Depends(get_current_user),
    family_service: FamilyService = Depends()
):
    """Cancel invitation."""
    success = await family_service.cancel_invitation(invitation_id, current_user["sub"])
    if not success:
        raise HTTPException(status_code=404, detail="Invitation not found or insufficient permissions")


# Spending approval operations
@router.post("/{family_id}/spending-requests", response_model=SpendingApprovalRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_spending_request(
    family_id: str,
    request_data: SpendingApprovalRequestCreate,
    current_user: dict = Depends(get_current_user),
    family_service: FamilyService = Depends()
):
    """Create spending approval request."""
    try:
        # Get member ID for current user in this family
        members = await family_service.get_family_members(family_id, current_user["sub"])
        user_member = next((m for m in members if m.user_id == current_user["sub"]), None)
        
        if not user_member:
            raise HTTPException(status_code=403, detail="Not a member of this family")
        
        request = await family_service.create_spending_request(
            family_id=family_id,
            member_id=user_member.id,
            request_data=request_data
        )
        return request
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{family_id}/spending-requests", response_model=List[SpendingApprovalRequestResponse])
async def get_pending_spending_requests(
    family_id: str,
    current_user: dict = Depends(get_current_user),
    family_service: FamilyService = Depends()
):
    """Get pending spending approval requests for family."""
    requests = await family_service.get_pending_approvals(family_id, current_user["sub"])
    return requests


@router.post("/spending-requests/{request_id}/decision", response_model=SpendingApprovalRequestResponse)
async def process_spending_approval(
    request_id: str,
    decision: SpendingApprovalDecision,
    current_user: dict = Depends(get_current_user),
    family_service: FamilyService = Depends()
):
    """Process spending approval decision."""
    try:
        request = await family_service.process_spending_approval(
            request_id=request_id,
            decision=decision,
            approver_id=current_user["sub"]
        )
        if not request:
            raise HTTPException(status_code=404, detail="Request not found or insufficient permissions")
        return request
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/members/{member_id}/spending-requests", response_model=List[SpendingApprovalRequestResponse])
async def get_member_spending_requests(
    member_id: str,
    include_processed: bool = Query(False, description="Include processed requests"),
    current_user: dict = Depends(get_current_user),
    family_service: FamilyService = Depends()
):
    """Get spending requests for a member."""
    requests = await family_service.get_member_spending_requests(
        member_id=member_id,
        include_processed=include_processed
    )
    return requests


# Dashboard and analytics
@router.get("/{family_id}/dashboard", response_model=FamilyDashboardResponse)
async def get_family_dashboard(
    family_id: str,
    current_user: dict = Depends(get_current_user),
    family_service: FamilyService = Depends()
):
    """Get family dashboard data."""
    try:
        dashboard = await family_service.get_family_dashboard(family_id, current_user["sub"])
        return dashboard
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# Maintenance operations (for background tasks)
@router.post("/maintenance/cleanup-invitations")
async def cleanup_expired_invitations(
    current_user: dict = Depends(get_current_user),
    family_service: FamilyService = Depends()
):
    """Cleanup expired invitations (admin only)."""
    # This would typically be restricted to admin users or run as a background task
    count = await family_service.cleanup_expired_invitations()
    return {"cleaned_up": count}


@router.post("/maintenance/cleanup-approvals")
async def cleanup_expired_approvals(
    current_user: dict = Depends(get_current_user),
    family_service: FamilyService = Depends()
):
    """Cleanup expired approval requests (admin only)."""
    count = await family_service.cleanup_expired_approval_requests()
    return {"cleaned_up": count}
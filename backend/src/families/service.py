"""Families service for business logic."""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
import secrets
import string
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db_session
from src.families.repository import (
    FamilyRepository,
    FamilyMemberRepository,
    FamilyInvitationRepository,
    SpendingApprovalRepository
)
from src.families.models import (
    Family,
    FamilyMember,
    FamilyInvitation,
    SpendingApprovalRequest
)
from src.families.schemas import (
    FamilyCreate,
    FamilyUpdate,
    FamilyMemberCreate,
    FamilyMemberUpdate,
    FamilyInvitationCreate,
    FamilyBudgetCreate,
    SpendingApprovalRequestCreate,
    SpendingApprovalDecision,
    FamilyDashboardResponse
)
from src.exceptions import NotFoundError, ValidationError, BusinessLogicError


class FamilyService:
    """Service for family operations."""
    
    def __init__(self, session: AsyncSession = Depends(get_db_session)):
        self.session = session
        self.family_repo = FamilyRepository(session)
        self.member_repo = FamilyMemberRepository(session)
        self.invitation_repo = FamilyInvitationRepository(session)
        self.approval_repo = SpendingApprovalRepository(session)
    
    # Family operations
    async def create_family(
        self,
        family_data: FamilyCreate,
        administrator_id: str
    ) -> Family:
        """Create a new family."""
        # Validate family data
        if not family_data.name.strip():
            raise ValidationError("Family name is required")
        
        if family_data.max_members < 2:
            raise ValidationError("Family must allow at least 2 members")
        
        return await self.family_repo.create_family(family_data, administrator_id)
    
    async def get_user_families(
        self,
        user_id: str,
        include_inactive: bool = False
    ) -> List[Family]:
        """Get families where user is a member."""
        return await self.family_repo.get_families_for_user(user_id, include_inactive)
    
    async def get_family(
        self,
        family_id: str,
        user_id: str
    ) -> Optional[Family]:
        """Get family by ID (only if user is a member)."""
        return await self.family_repo.get_family_with_members(family_id, user_id)
    
    async def update_family(
        self,
        family_id: str,
        family_data: FamilyUpdate,
        user_id: str
    ) -> Optional[Family]:
        """Update family (only by administrator)."""
        # Validate update data
        if family_data.name is not None and not family_data.name.strip():
            raise ValidationError("Family name cannot be empty")
        
        if family_data.max_members is not None and family_data.max_members < 2:
            raise ValidationError("Family must allow at least 2 members")
        
        return await self.family_repo.update_family(family_id, family_data, user_id)
    
    async def delete_family(
        self,
        family_id: str,
        user_id: str
    ) -> bool:
        """Delete family (only by administrator)."""
        return await self.family_repo.delete_family(family_id, user_id)
    
    # Member operations
    async def get_family_members(
        self,
        family_id: str,
        user_id: str,
        include_inactive: bool = False
    ) -> List[FamilyMember]:
        """Get family members."""
        return await self.member_repo.get_family_members(family_id, user_id, include_inactive)
    
    async def add_family_member(
        self,
        family_id: str,
        member_data: FamilyMemberCreate,
        added_by_user_id: str
    ) -> Optional[FamilyMember]:
        """Add member to family."""
        # Validate member data
        if not member_data.name.strip():
            raise ValidationError("Member name is required")
        
        if member_data.spending_limit and member_data.spending_limit < 0:
            raise ValidationError("Spending limit cannot be negative")
        
        if member_data.requires_approval_over and member_data.requires_approval_over < 0:
            raise ValidationError("Approval threshold cannot be negative")
        
        return await self.member_repo.add_member_to_family(family_id, member_data, added_by_user_id)
    
    async def update_family_member(
        self,
        member_id: str,
        member_data: FamilyMemberUpdate,
        updated_by_user_id: str
    ) -> Optional[FamilyMember]:
        """Update family member."""
        # Validate update data
        if member_data.name is not None and not member_data.name.strip():
            raise ValidationError("Member name cannot be empty")
        
        if member_data.spending_limit is not None and member_data.spending_limit < 0:
            raise ValidationError("Spending limit cannot be negative")
        
        if member_data.requires_approval_over is not None and member_data.requires_approval_over < 0:
            raise ValidationError("Approval threshold cannot be negative")
        
        return await self.member_repo.update_member(member_id, member_data, updated_by_user_id)
    
    async def remove_family_member(
        self,
        member_id: str,
        removed_by_user_id: str
    ) -> bool:
        """Remove member from family."""
        return await self.member_repo.remove_member(member_id, removed_by_user_id)
    
    # Invitation operations
    async def create_invitation(
        self,
        family_id: str,
        invitation_data: FamilyInvitationCreate,
        inviter_id: str
    ) -> FamilyInvitation:
        """Create family invitation."""
        # Validate invitation data
        if invitation_data.expires_in_days < 1 or invitation_data.expires_in_days > 30:
            raise ValidationError("Invitation expiration must be between 1 and 30 days")
        
        # Generate secure invitation token
        token = self._generate_invitation_token()
        
        return await self.invitation_repo.create_invitation(
            family_id, invitation_data, inviter_id, token
        )
    
    async def get_family_invitations(
        self,
        family_id: str,
        user_id: str,
        include_expired: bool = False
    ) -> List[FamilyInvitation]:
        """Get invitations for a family."""
        return await self.invitation_repo.get_family_invitations(family_id, user_id, include_expired)
    
    async def accept_invitation(
        self,
        token: str,
        user_id: str
    ) -> Optional[FamilyMember]:
        """Accept family invitation."""
        member = await self.invitation_repo.accept_invitation(token, user_id)
        if not member:
            raise ValidationError("Invalid or expired invitation")
        
        return member
    
    async def get_invitation_by_token(
        self,
        token: str
    ) -> Optional[FamilyInvitation]:
        """Get invitation by token for validation."""
        invitation = await self.invitation_repo.get_invitation_by_token(token)
        
        if not invitation:
            return None
        
        # Check if expired
        if invitation.expires_at <= datetime.utcnow():
            return None
        
        return invitation
    
    async def cancel_invitation(
        self,
        invitation_id: str,
        user_id: str
    ) -> bool:
        """Cancel invitation."""
        return await self.invitation_repo.cancel_invitation(invitation_id, user_id)
    
    # Spending approval operations
    async def create_spending_request(
        self,
        family_id: str,
        member_id: str,
        request_data: SpendingApprovalRequestCreate
    ) -> SpendingApprovalRequest:
        """Create spending approval request."""
        # Validate request data
        if request_data.amount <= 0:
            raise ValidationError("Spending amount must be greater than zero")
        
        if not request_data.description.strip():
            raise ValidationError("Spending description is required")
        
        if request_data.expires_in_hours < 1 or request_data.expires_in_hours > 168:
            raise ValidationError("Request expiration must be between 1 hour and 1 week")
        
        return await self.approval_repo.create_approval_request(family_id, member_id, request_data)
    
    async def get_pending_approvals(
        self,
        family_id: str,
        user_id: str
    ) -> List[SpendingApprovalRequest]:
        """Get pending approval requests for family."""
        return await self.approval_repo.get_pending_approvals_for_family(family_id, user_id)
    
    async def process_spending_approval(
        self,
        request_id: str,
        decision: SpendingApprovalDecision,
        approver_id: str
    ) -> Optional[SpendingApprovalRequest]:
        """Process spending approval decision."""
        if decision.decision not in ["approved", "denied"]:
            raise ValidationError("Decision must be 'approved' or 'denied'")
        
        return await self.approval_repo.process_approval_decision(request_id, decision, approver_id)
    
    async def get_member_spending_requests(
        self,
        member_id: str,
        include_processed: bool = False
    ) -> List[SpendingApprovalRequest]:
        """Get spending requests for a member."""
        return await self.approval_repo.get_member_approval_requests(member_id, include_processed)
    
    # Dashboard and analytics
    async def get_family_dashboard(
        self,
        family_id: str,
        user_id: str
    ) -> FamilyDashboardResponse:
        """Get family dashboard data."""
        family = await self.get_family(family_id, user_id)
        if not family:
            raise NotFoundError("Family not found")
        
        # Get dashboard data
        members = await self.get_family_members(family_id, user_id)
        invitations = await self.get_family_invitations(family_id, user_id)
        pending_approvals = await self.get_pending_approvals(family_id, user_id)
        
        # Calculate metrics
        pending_invitations_count = len([inv for inv in invitations if inv.status == "pending"])
        
        # Mock data for now - would be calculated from actual transactions
        total_spending = Decimal("2500.00")
        
        recent_activities = [
            {
                "type": "spending_request",
                "member": "Jane Smith",
                "amount": "75.00",
                "description": "Video game purchase",
                "timestamp": datetime.utcnow().isoformat()
            }
        ]
        
        upcoming_approvals = [req for req in pending_approvals if req.expires_at <= datetime.utcnow() + timedelta(hours=24)]
        
        return FamilyDashboardResponse(
            family_id=family_id,
            member_count=len(members),
            pending_invitations=pending_invitations_count,
            pending_approvals=len(pending_approvals),
            shared_budgets=len(family.shared_budgets),
            shared_goals=len(family.shared_goals),
            total_family_spending=total_spending,
            recent_activities=recent_activities,
            upcoming_approvals=upcoming_approvals
        )
    
    # Helper methods
    def _generate_invitation_token(self) -> str:
        """Generate secure invitation token."""
        alphabet = string.ascii_letters + string.digits
        return "inv_" + "".join(secrets.choice(alphabet) for _ in range(32))
    
    async def _check_member_permissions(
        self,
        user_id: str,
        family_id: str,
        required_permission: str
    ) -> bool:
        """Check if user has required permission in family."""
        members = await self.member_repo.get_family_members(family_id, user_id)
        user_member = next((m for m in members if m.user_id == user_id), None)
        
        if not user_member:
            return False
        
        # Administrator has all permissions
        if user_member.role == "administrator":
            return True
        
        return user_member.permissions.get(required_permission, False)
    
    async def _validate_spending_request(
        self,
        member: FamilyMember,
        amount: Decimal
    ) -> bool:
        """Validate if spending request is within member's limits."""
        # Check spending limit
        if member.spending_limit and amount > member.spending_limit:
            return False
        
        # Check if approval is required
        if member.requires_approval_over and amount > member.requires_approval_over:
            return True  # Requires approval but is valid request
        
        return True
    
    async def cleanup_expired_invitations(self) -> int:
        """Cleanup expired invitations (background task)."""
        # This would typically be called by a background job
        from sqlalchemy import update
        
        query = update(FamilyInvitation).where(
            and_(
                FamilyInvitation.status == "pending",
                FamilyInvitation.expires_at <= datetime.utcnow()
            )
        ).values(status="expired")
        
        result = await self.session.execute(query)
        await self.session.commit()
        
        return result.rowcount
    
    async def cleanup_expired_approval_requests(self) -> int:
        """Cleanup expired approval requests (background task)."""
        from sqlalchemy import update
        
        query = update(SpendingApprovalRequest).where(
            and_(
                SpendingApprovalRequest.status == "pending",
                SpendingApprovalRequest.expires_at <= datetime.utcnow()
            )
        ).values(status="expired")
        
        result = await self.session.execute(query)
        await self.session.commit()
        
        return result.rowcount
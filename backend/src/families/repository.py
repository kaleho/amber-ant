"""Families repository for database operations."""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.shared.repository import UserScopedRepository
from src.families.models import (
    Family,
    FamilyMember,
    FamilyInvitation,
    FamilyBudget,
    FamilySavingsGoal,
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
    SpendingApprovalDecision
)


class FamilyRepository(UserScopedRepository[Family]):
    """Repository for family operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Family)
    
    async def create_family(
        self,
        family_data: FamilyCreate,
        administrator_id: str
    ) -> Family:
        """Create a new family."""
        family = Family(
            administrator_id=administrator_id,
            current_member_count=1,
            **family_data.model_dump()
        )
        
        self.session.add(family)
        await self.session.commit()
        await self.session.refresh(family)
        
        # Create the administrator as first member
        member = FamilyMember(
            family_id=family.id,
            user_id=administrator_id,
            name="Administrator",  # Will be updated with user's actual name
            email="admin@family.com",  # Will be updated with user's actual email
            role="administrator",
            status="active",
            permissions={
                "can_view_budgets": True,
                "can_edit_budgets": True,
                "can_create_goals": True,
                "can_invite_members": True,
                "can_manage_members": True,
                "can_approve_spending": True
            }
        )
        
        self.session.add(member)
        await self.session.commit()
        
        return family
    
    async def get_families_for_user(
        self,
        user_id: str,
        include_inactive: bool = False
    ) -> List[Family]:
        """Get families where user is a member."""
        query = select(Family).join(FamilyMember).where(
            FamilyMember.user_id == user_id
        )
        
        if not include_inactive:
            query = query.where(Family.is_active == True)
        
        query = query.options(
            selectinload(Family.members),
            selectinload(Family.invitations)
        ).order_by(desc(Family.created_at))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_family_with_members(
        self,
        family_id: str,
        user_id: str
    ) -> Optional[Family]:
        """Get family with all members (only if user is a member)."""
        # First check if user is a member
        member_query = select(FamilyMember).where(
            and_(
                FamilyMember.family_id == family_id,
                FamilyMember.user_id == user_id,
                FamilyMember.status == "active"
            )
        )
        
        member_result = await self.session.execute(member_query)
        if not member_result.scalar_one_or_none():
            return None
        
        # Get family with relationships
        query = select(Family).where(Family.id == family_id).options(
            selectinload(Family.members),
            selectinload(Family.invitations),
            selectinload(Family.shared_budgets),
            selectinload(Family.shared_goals)
        )
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def update_family(
        self,
        family_id: str,
        family_data: FamilyUpdate,
        user_id: str
    ) -> Optional[Family]:
        """Update family (only by administrator)."""
        family = await self.get_family_with_members(family_id, user_id)
        if not family or family.administrator_id != user_id:
            return None
        
        update_dict = family_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(family, field, value)
        
        family.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(family)
        return family
    
    async def delete_family(
        self,
        family_id: str,
        user_id: str
    ) -> bool:
        """Delete family (only by administrator)."""
        family = await self.get_family_with_members(family_id, user_id)
        if not family or family.administrator_id != user_id:
            return False
        
        await self.session.delete(family)
        await self.session.commit()
        return True


class FamilyMemberRepository:
    """Repository for family member operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, member_id: str) -> Optional[FamilyMember]:
        """Get member by ID."""
        query = select(FamilyMember).where(FamilyMember.id == member_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_family_members(
        self,
        family_id: str,
        user_id: str,
        include_inactive: bool = False
    ) -> List[FamilyMember]:
        """Get all members of a family (if user is a member)."""
        # First verify user is a member
        verification_query = select(FamilyMember).where(
            and_(
                FamilyMember.family_id == family_id,
                FamilyMember.user_id == user_id,
                FamilyMember.status == "active"
            )
        )
        
        verification_result = await self.session.execute(verification_query)
        if not verification_result.scalar_one_or_none():
            return []
        
        # Get all members
        query = select(FamilyMember).where(FamilyMember.family_id == family_id)
        
        if not include_inactive:
            query = query.where(FamilyMember.status == "active")
        
        query = query.order_by(FamilyMember.joined_at)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def add_member_to_family(
        self,
        family_id: str,
        member_data: FamilyMemberCreate,
        added_by_user_id: str
    ) -> Optional[FamilyMember]:
        """Add member to family (requires administrator permission)."""
        # Verify user can add members
        admin_query = select(Family).where(
            and_(
                Family.id == family_id,
                Family.administrator_id == added_by_user_id
            )
        )
        
        admin_result = await self.session.execute(admin_query)
        family = admin_result.scalar_one_or_none()
        if not family:
            return None
        
        # Check member limit
        if family.current_member_count >= family.max_members:
            return None
        
        # Create member
        member = FamilyMember(
            family_id=family_id,
            user_id="",  # Will be set when user accepts invitation or is directly added
            **member_data.model_dump()
        )
        
        self.session.add(member)
        
        # Update family member count
        family.current_member_count += 1
        
        await self.session.commit()
        await self.session.refresh(member)
        return member
    
    async def update_member(
        self,
        member_id: str,
        member_data: FamilyMemberUpdate,
        updated_by_user_id: str
    ) -> Optional[FamilyMember]:
        """Update family member."""
        member = await self.get_by_id(member_id)
        if not member:
            return None
        
        # Verify user can update member (administrator or self)
        family_query = select(Family).where(Family.id == member.family_id)
        family_result = await self.session.execute(family_query)
        family = family_result.scalar_one_or_none()
        
        if not family or (family.administrator_id != updated_by_user_id and member.user_id != updated_by_user_id):
            return None
        
        update_dict = member_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(member, field, value)
        
        await self.session.commit()
        await self.session.refresh(member)
        return member
    
    async def remove_member(
        self,
        member_id: str,
        removed_by_user_id: str
    ) -> bool:
        """Remove member from family."""
        member = await self.get_by_id(member_id)
        if not member:
            return False
        
        # Verify user can remove member (administrator or self)
        family_query = select(Family).where(Family.id == member.family_id)
        family_result = await self.session.execute(family_query)
        family = family_result.scalar_one_or_none()
        
        if not family or (family.administrator_id != removed_by_user_id and member.user_id != removed_by_user_id):
            return False
        
        # Cannot remove administrator
        if member.role == "administrator":
            return False
        
        await self.session.delete(member)
        
        # Update family member count
        family.current_member_count -= 1
        
        await self.session.commit()
        return True


class FamilyInvitationRepository:
    """Repository for family invitation operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_invitation(
        self,
        family_id: str,
        invitation_data: FamilyInvitationCreate,
        inviter_id: str,
        invitation_token: str
    ) -> FamilyInvitation:
        """Create family invitation."""
        expires_at = datetime.utcnow() + timedelta(days=invitation_data.expires_in_days)
        
        invitation = FamilyInvitation(
            family_id=family_id,
            inviter_id=inviter_id,
            invitation_token=invitation_token,
            expires_at=expires_at,
            **invitation_data.model_dump(exclude={"expires_in_days"})
        )
        
        self.session.add(invitation)
        await self.session.commit()
        await self.session.refresh(invitation)
        return invitation
    
    async def get_invitation_by_token(
        self,
        token: str
    ) -> Optional[FamilyInvitation]:
        """Get invitation by token."""
        query = select(FamilyInvitation).where(
            FamilyInvitation.invitation_token == token
        ).options(selectinload(FamilyInvitation.family))
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_family_invitations(
        self,
        family_id: str,
        user_id: str,
        include_expired: bool = False
    ) -> List[FamilyInvitation]:
        """Get invitations for a family."""
        # Verify user can view invitations (administrator)
        family_query = select(Family).where(
            and_(
                Family.id == family_id,
                Family.administrator_id == user_id
            )
        )
        
        family_result = await self.session.execute(family_query)
        if not family_result.scalar_one_or_none():
            return []
        
        query = select(FamilyInvitation).where(FamilyInvitation.family_id == family_id)
        
        if not include_expired:
            query = query.where(
                and_(
                    FamilyInvitation.status == "pending",
                    FamilyInvitation.expires_at > datetime.utcnow()
                )
            )
        
        query = query.order_by(desc(FamilyInvitation.created_at))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def accept_invitation(
        self,
        token: str,
        user_id: str
    ) -> Optional[FamilyMember]:
        """Accept family invitation."""
        invitation = await self.get_invitation_by_token(token)
        if not invitation or invitation.status != "pending" or invitation.expires_at <= datetime.utcnow():
            return None
        
        # Check if family has space
        family = invitation.family
        if family.current_member_count >= family.max_members:
            return None
        
        # Create family member
        member = FamilyMember(
            family_id=invitation.family_id,
            user_id=user_id,
            name="New Member",  # Will be updated with user's actual name
            email=invitation.email,
            role=invitation.role,
            permissions=invitation.permissions,
            status="active"
        )
        
        self.session.add(member)
        
        # Update invitation
        invitation.status = "accepted"
        invitation.accepted_at = datetime.utcnow()
        invitation.accepted_by_user_id = user_id
        
        # Update family member count
        family.current_member_count += 1
        
        await self.session.commit()
        await self.session.refresh(member)
        return member
    
    async def cancel_invitation(
        self,
        invitation_id: str,
        user_id: str
    ) -> bool:
        """Cancel invitation."""
        query = select(FamilyInvitation).where(FamilyInvitation.id == invitation_id)
        result = await self.session.execute(query)
        invitation = result.scalar_one_or_none()
        
        if not invitation or invitation.inviter_id != user_id:
            return False
        
        invitation.status = "cancelled"
        await self.session.commit()
        return True


class SpendingApprovalRepository:
    """Repository for spending approval operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_approval_request(
        self,
        family_id: str,
        member_id: str,
        request_data: SpendingApprovalRequestCreate
    ) -> SpendingApprovalRequest:
        """Create spending approval request."""
        expires_at = datetime.utcnow() + timedelta(hours=request_data.expires_in_hours)
        
        request = SpendingApprovalRequest(
            family_id=family_id,
            member_id=member_id,
            expires_at=expires_at,
            **request_data.model_dump(exclude={"expires_in_hours"})
        )
        
        self.session.add(request)
        await self.session.commit()
        await self.session.refresh(request)
        return request
    
    async def get_pending_approvals_for_family(
        self,
        family_id: str,
        user_id: str
    ) -> List[SpendingApprovalRequest]:
        """Get pending approval requests for family."""
        # Verify user can view approvals (administrator or member with approval permissions)
        member_query = select(FamilyMember).where(
            and_(
                FamilyMember.family_id == family_id,
                FamilyMember.user_id == user_id,
                FamilyMember.status == "active"
            )
        )
        
        member_result = await self.session.execute(member_query)
        member = member_result.scalar_one_or_none()
        
        if not member:
            return []
        
        # Check if user can approve spending
        family_query = select(Family).where(Family.id == family_id)
        family_result = await self.session.execute(family_query)
        family = family_result.scalar_one_or_none()
        
        if not family or (family.administrator_id != user_id and 
                         not member.permissions.get("can_approve_spending", False)):
            return []
        
        query = select(SpendingApprovalRequest).where(
            and_(
                SpendingApprovalRequest.family_id == family_id,
                SpendingApprovalRequest.status == "pending",
                SpendingApprovalRequest.expires_at > datetime.utcnow()
            )
        ).order_by(SpendingApprovalRequest.created_at)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def process_approval_decision(
        self,
        request_id: str,
        decision: SpendingApprovalDecision,
        approver_id: str
    ) -> Optional[SpendingApprovalRequest]:
        """Process approval decision."""
        query = select(SpendingApprovalRequest).where(
            SpendingApprovalRequest.id == request_id
        )
        
        result = await self.session.execute(query)
        request = result.scalar_one_or_none()
        
        if not request or request.status != "pending" or request.expires_at <= datetime.utcnow():
            return None
        
        # Verify user can approve
        family_query = select(Family).where(Family.id == request.family_id)
        family_result = await self.session.execute(family_query)
        family = family_result.scalar_one_or_none()
        
        if not family or family.administrator_id != approver_id:
            # Check if user has approval permissions
            member_query = select(FamilyMember).where(
                and_(
                    FamilyMember.family_id == request.family_id,
                    FamilyMember.user_id == approver_id,
                    FamilyMember.status == "active"
                )
            )
            
            member_result = await self.session.execute(member_query)
            member = member_result.scalar_one_or_none()
            
            if not member or not member.permissions.get("can_approve_spending", False):
                return None
        
        # Update request
        request.status = decision.decision
        request.approved_by = approver_id
        request.approved_at = datetime.utcnow()
        request.approval_notes = decision.notes
        
        await self.session.commit()
        await self.session.refresh(request)
        return request
    
    async def get_member_approval_requests(
        self,
        member_id: str,
        include_processed: bool = False
    ) -> List[SpendingApprovalRequest]:
        """Get approval requests for a specific member."""
        query = select(SpendingApprovalRequest).where(
            SpendingApprovalRequest.member_id == member_id
        )
        
        if not include_processed:
            query = query.where(SpendingApprovalRequest.status == "pending")
        
        query = query.order_by(desc(SpendingApprovalRequest.created_at))
        
        result = await self.session.execute(query)
        return result.scalars().all()
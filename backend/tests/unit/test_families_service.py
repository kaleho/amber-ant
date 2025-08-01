"""Unit tests for families service."""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from src.families.service import FamilyService
from src.families.schemas import (
    FamilyCreate, FamilyUpdate, FamilyMemberCreate, FamilyMemberUpdate,
    FamilyInvitationCreate, SpendingApprovalRequestCreate, SpendingApprovalDecision,
    FamilyRole, FamilyMemberStatus, InvitationStatus, ApprovalStatus
)
from src.families.models import Family, FamilyMember, FamilyInvitation, SpendingApprovalRequest
from src.exceptions import NotFoundError, ValidationError, BusinessLogicError


class TestFamilyService:
    """Test family service business logic."""
    
    @pytest.fixture
    def family_service(self):
        """Create family service with mocked repositories."""
        service = FamilyService.__new__(FamilyService)
        service.session = AsyncMock()
        service.family_repo = AsyncMock()
        service.member_repo = AsyncMock()
        service.invitation_repo = AsyncMock()
        service.approval_repo = AsyncMock()
        return service
    
    @pytest.fixture
    def sample_family_data(self):
        """Sample family creation data."""
        return FamilyCreate(
            name="The Smith Family",
            description="Family financial management",
            max_members=6,
            plan_type="premium",
            settings={
                "allow_teen_transactions": True,
                "require_approval_over": "100.00"
            }
        )
    
    @pytest.fixture
    def sample_member_data(self):
        """Sample family member data."""
        return FamilyMemberCreate(
            name="Jane Smith",
            email="jane@example.com",
            role=FamilyRole.SPOUSE,
            spending_limit=Decimal("1000.00"),
            requires_approval_over=Decimal("500.00"),
            approved_categories=["Food & Dining", "Transportation"],
            permissions={
                "can_view_budgets": True,
                "can_edit_budgets": False,
                "can_create_goals": True
            }
        )
    
    @pytest.fixture
    def sample_invitation_data(self):
        """Sample invitation data."""
        return FamilyInvitationCreate(
            email="teen@example.com",
            role=FamilyRole.TEEN,
            message="Welcome to our family financial planning!",
            permissions={
                "can_view_budgets": True,
                "spending_limit": "100.00"
            },
            expires_in_days=7
        )
    
    @pytest.fixture
    def sample_spending_request_data(self):
        """Sample spending approval request data."""
        return SpendingApprovalRequestCreate(
            amount=Decimal("75.00"),
            description="New video game purchase",
            category="Entertainment",
            merchant="GameStop",
            expires_in_hours=24
        )

    # Family operations tests
    @pytest.mark.asyncio
    async def test_create_family_success(self, family_service, sample_family_data):
        """Test successful family creation."""
        administrator_id = str(uuid4())
        created_family = Mock(
            id=str(uuid4()),
            administrator_id=administrator_id,
            **sample_family_data.model_dump()
        )
        family_service.family_repo.create_family.return_value = created_family
        
        result = await family_service.create_family(sample_family_data, administrator_id)
        
        family_service.family_repo.create_family.assert_called_once_with(
            sample_family_data, administrator_id
        )
        assert result == created_family
    
    @pytest.mark.asyncio
    async def test_create_family_validation_error_empty_name(self, family_service, sample_family_data):
        """Test family creation with empty name."""
        sample_family_data.name = "   "
        administrator_id = str(uuid4())
        
        with pytest.raises(ValidationError, match="Family name is required"):
            await family_service.create_family(sample_family_data, administrator_id)
    
    @pytest.mark.asyncio
    async def test_create_family_validation_error_min_members(self, family_service, sample_family_data):
        """Test family creation with invalid max members."""
        sample_family_data.max_members = 1
        administrator_id = str(uuid4())
        
        with pytest.raises(ValidationError, match="Family must allow at least 2 members"):
            await family_service.create_family(sample_family_data, administrator_id)
    
    @pytest.mark.asyncio
    async def test_get_user_families(self, family_service):
        """Test getting user families."""
        user_id = str(uuid4())
        expected_families = [Mock(), Mock()]
        family_service.family_repo.get_families_for_user.return_value = expected_families
        
        result = await family_service.get_user_families(user_id)
        
        family_service.family_repo.get_families_for_user.assert_called_once_with(
            user_id, False
        )
        assert result == expected_families
    
    @pytest.mark.asyncio
    async def test_get_family_success(self, family_service):
        """Test getting family by ID."""
        family_id = str(uuid4())
        user_id = str(uuid4())
        expected_family = Mock()
        family_service.family_repo.get_family_with_members.return_value = expected_family
        
        result = await family_service.get_family(family_id, user_id)
        
        family_service.family_repo.get_family_with_members.assert_called_once_with(
            family_id, user_id
        )
        assert result == expected_family
    
    @pytest.mark.asyncio
    async def test_update_family_success(self, family_service):
        """Test successful family update."""
        family_id = str(uuid4())
        user_id = str(uuid4())
        update_data = FamilyUpdate(name="Updated Family Name", max_members=8)
        updated_family = Mock()
        family_service.family_repo.update_family.return_value = updated_family
        
        result = await family_service.update_family(family_id, update_data, user_id)
        
        family_service.family_repo.update_family.assert_called_once_with(
            family_id, update_data, user_id
        )
        assert result == updated_family
    
    @pytest.mark.asyncio
    async def test_update_family_validation_error_empty_name(self, family_service):
        """Test family update with empty name."""
        family_id = str(uuid4())
        user_id = str(uuid4())
        update_data = FamilyUpdate(name="   ")
        
        with pytest.raises(ValidationError, match="Family name cannot be empty"):
            await family_service.update_family(family_id, update_data, user_id)
    
    @pytest.mark.asyncio
    async def test_delete_family_success(self, family_service):
        """Test successful family deletion."""
        family_id = str(uuid4())
        user_id = str(uuid4())
        family_service.family_repo.delete_family.return_value = True
        
        result = await family_service.delete_family(family_id, user_id)
        
        family_service.family_repo.delete_family.assert_called_once_with(
            family_id, user_id
        )
        assert result is True

    # Member operations tests
    @pytest.mark.asyncio
    async def test_get_family_members(self, family_service):
        """Test getting family members."""
        family_id = str(uuid4())
        user_id = str(uuid4())
        expected_members = [Mock(), Mock()]
        family_service.member_repo.get_family_members.return_value = expected_members
        
        result = await family_service.get_family_members(family_id, user_id)
        
        family_service.member_repo.get_family_members.assert_called_once_with(
            family_id, user_id, False
        )
        assert result == expected_members
    
    @pytest.mark.asyncio
    async def test_add_family_member_success(self, family_service, sample_member_data):
        """Test successful member addition."""
        family_id = str(uuid4())
        added_by_user_id = str(uuid4())
        created_member = Mock()
        family_service.member_repo.add_member_to_family.return_value = created_member
        
        result = await family_service.add_family_member(
            family_id, sample_member_data, added_by_user_id
        )
        
        family_service.member_repo.add_member_to_family.assert_called_once_with(
            family_id, sample_member_data, added_by_user_id
        )
        assert result == created_member
    
    @pytest.mark.asyncio
    async def test_add_family_member_validation_errors(self, family_service, sample_member_data):
        """Test member addition validation errors."""
        family_id = str(uuid4())
        added_by_user_id = str(uuid4())
        
        # Test empty name
        sample_member_data.name = "   "
        with pytest.raises(ValidationError, match="Member name is required"):
            await family_service.add_family_member(family_id, sample_member_data, added_by_user_id)
        
        # Reset name and test negative spending limit
        sample_member_data.name = "Jane Smith"
        sample_member_data.spending_limit = Decimal("-100.00")
        with pytest.raises(ValidationError, match="Spending limit cannot be negative"):
            await family_service.add_family_member(family_id, sample_member_data, added_by_user_id)
        
        # Reset spending limit and test negative approval threshold
        sample_member_data.spending_limit = Decimal("1000.00")
        sample_member_data.requires_approval_over = Decimal("-50.00")
        with pytest.raises(ValidationError, match="Approval threshold cannot be negative"):
            await family_service.add_family_member(family_id, sample_member_data, added_by_user_id)
    
    @pytest.mark.asyncio
    async def test_update_family_member_success(self, family_service):
        """Test successful member update."""
        member_id = str(uuid4())
        updated_by_user_id = str(uuid4())
        update_data = FamilyMemberUpdate(role=FamilyRole.TEEN, spending_limit=Decimal("200.00"))
        updated_member = Mock()
        family_service.member_repo.update_member.return_value = updated_member
        
        result = await family_service.update_family_member(
            member_id, update_data, updated_by_user_id
        )
        
        family_service.member_repo.update_member.assert_called_once_with(
            member_id, update_data, updated_by_user_id
        )
        assert result == updated_member
    
    @pytest.mark.asyncio
    async def test_remove_family_member_success(self, family_service):
        """Test successful member removal."""
        member_id = str(uuid4())
        removed_by_user_id = str(uuid4())
        family_service.member_repo.remove_member.return_value = True
        
        result = await family_service.remove_family_member(member_id, removed_by_user_id)
        
        family_service.member_repo.remove_member.assert_called_once_with(
            member_id, removed_by_user_id
        )
        assert result is True

    # Invitation operations tests
    @pytest.mark.asyncio
    async def test_generate_invitation_token(self, family_service):
        """Test invitation token generation."""
        token = family_service._generate_invitation_token()
        
        assert token.startswith("inv_")
        assert len(token) == 36  # "inv_" + 32 characters
        assert all(c.isalnum() for c in token[4:])  # Only alphanumeric after prefix
    
    @pytest.mark.asyncio
    async def test_create_invitation_success(self, family_service, sample_invitation_data):
        """Test successful invitation creation."""
        family_id = str(uuid4())
        inviter_id = str(uuid4())
        created_invitation = Mock()
        family_service.invitation_repo.create_invitation.return_value = created_invitation
        
        with patch.object(family_service, '_generate_invitation_token', return_value="inv_test123"):
            result = await family_service.create_invitation(
                family_id, sample_invitation_data, inviter_id
            )
        
        family_service.invitation_repo.create_invitation.assert_called_once_with(
            family_id, sample_invitation_data, inviter_id, "inv_test123"
        )
        assert result == created_invitation
    
    @pytest.mark.asyncio
    async def test_create_invitation_validation_error_expires_in_days(self, family_service, sample_invitation_data):
        """Test invitation creation with invalid expiration days."""
        family_id = str(uuid4())
        inviter_id = str(uuid4())
        
        # Test too short expiration
        sample_invitation_data.expires_in_days = 0
        with pytest.raises(ValidationError, match="Invitation expiration must be between 1 and 30 days"):
            await family_service.create_invitation(family_id, sample_invitation_data, inviter_id)
        
        # Test too long expiration
        sample_invitation_data.expires_in_days = 31
        with pytest.raises(ValidationError, match="Invitation expiration must be between 1 and 30 days"):
            await family_service.create_invitation(family_id, sample_invitation_data, inviter_id)
    
    @pytest.mark.asyncio
    async def test_get_family_invitations(self, family_service):
        """Test getting family invitations."""
        family_id = str(uuid4())
        user_id = str(uuid4())
        expected_invitations = [Mock(), Mock()]
        family_service.invitation_repo.get_family_invitations.return_value = expected_invitations
        
        result = await family_service.get_family_invitations(family_id, user_id)
        
        family_service.invitation_repo.get_family_invitations.assert_called_once_with(
            family_id, user_id, False
        )
        assert result == expected_invitations
    
    @pytest.mark.asyncio
    async def test_accept_invitation_success(self, family_service):
        """Test successful invitation acceptance."""
        token = "inv_test123"
        user_id = str(uuid4())
        created_member = Mock()
        family_service.invitation_repo.accept_invitation.return_value = created_member
        
        result = await family_service.accept_invitation(token, user_id)
        
        family_service.invitation_repo.accept_invitation.assert_called_once_with(
            token, user_id
        )
        assert result == created_member
    
    @pytest.mark.asyncio
    async def test_accept_invitation_validation_error(self, family_service):
        """Test invitation acceptance validation error."""
        token = "inv_invalid"
        user_id = str(uuid4())
        family_service.invitation_repo.accept_invitation.return_value = None
        
        with pytest.raises(ValidationError, match="Invalid or expired invitation"):
            await family_service.accept_invitation(token, user_id)
    
    @pytest.mark.asyncio
    async def test_get_invitation_by_token_success(self, family_service):
        """Test getting invitation by token."""
        token = "inv_test123"
        invitation = Mock()
        invitation.expires_at = datetime.utcnow() + timedelta(days=1)  # Not expired
        family_service.invitation_repo.get_invitation_by_token.return_value = invitation
        
        result = await family_service.get_invitation_by_token(token)
        
        family_service.invitation_repo.get_invitation_by_token.assert_called_once_with(token)
        assert result == invitation
    
    @pytest.mark.asyncio
    async def test_get_invitation_by_token_expired(self, family_service):
        """Test getting expired invitation by token."""
        token = "inv_test123"
        invitation = Mock()
        invitation.expires_at = datetime.utcnow() - timedelta(hours=1)  # Expired
        family_service.invitation_repo.get_invitation_by_token.return_value = invitation
        
        result = await family_service.get_invitation_by_token(token)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cancel_invitation_success(self, family_service):
        """Test successful invitation cancellation."""
        invitation_id = str(uuid4())
        user_id = str(uuid4())
        family_service.invitation_repo.cancel_invitation.return_value = True
        
        result = await family_service.cancel_invitation(invitation_id, user_id)
        
        family_service.invitation_repo.cancel_invitation.assert_called_once_with(
            invitation_id, user_id
        )
        assert result is True

    # Spending approval operations tests
    @pytest.mark.asyncio
    async def test_create_spending_request_success(self, family_service, sample_spending_request_data):
        """Test successful spending request creation."""
        family_id = str(uuid4())
        member_id = str(uuid4())
        created_request = Mock()
        family_service.approval_repo.create_approval_request.return_value = created_request
        
        result = await family_service.create_spending_request(
            family_id, member_id, sample_spending_request_data
        )
        
        family_service.approval_repo.create_approval_request.assert_called_once_with(
            family_id, member_id, sample_spending_request_data
        )
        assert result == created_request
    
    @pytest.mark.asyncio
    async def test_create_spending_request_validation_errors(self, family_service, sample_spending_request_data):
        """Test spending request creation validation errors."""
        family_id = str(uuid4())
        member_id = str(uuid4())
        
        # Test zero amount
        sample_spending_request_data.amount = Decimal("0")
        with pytest.raises(ValidationError, match="Spending amount must be greater than zero"):
            await family_service.create_spending_request(family_id, member_id, sample_spending_request_data)
        
        # Reset amount and test empty description
        sample_spending_request_data.amount = Decimal("75.00")
        sample_spending_request_data.description = "   "
        with pytest.raises(ValidationError, match="Spending description is required"):
            await family_service.create_spending_request(family_id, member_id, sample_spending_request_data)
        
        # Reset description and test invalid expiration hours
        sample_spending_request_data.description = "Valid description"
        sample_spending_request_data.expires_in_hours = 0
        with pytest.raises(ValidationError, match="Request expiration must be between 1 hour and 1 week"):
            await family_service.create_spending_request(family_id, member_id, sample_spending_request_data)
        
        sample_spending_request_data.expires_in_hours = 169  # More than 1 week
        with pytest.raises(ValidationError, match="Request expiration must be between 1 hour and 1 week"):
            await family_service.create_spending_request(family_id, member_id, sample_spending_request_data)
    
    @pytest.mark.asyncio
    async def test_get_pending_approvals(self, family_service):
        """Test getting pending approval requests."""
        family_id = str(uuid4())
        user_id = str(uuid4())
        expected_requests = [Mock(), Mock()]
        family_service.approval_repo.get_pending_approvals_for_family.return_value = expected_requests
        
        result = await family_service.get_pending_approvals(family_id, user_id)
        
        family_service.approval_repo.get_pending_approvals_for_family.assert_called_once_with(
            family_id, user_id
        )
        assert result == expected_requests
    
    @pytest.mark.asyncio
    async def test_process_spending_approval_success(self, family_service):
        """Test successful spending approval processing."""
        request_id = str(uuid4())
        approver_id = str(uuid4())
        decision = SpendingApprovalDecision(
            decision=ApprovalStatus.APPROVED,
            notes="Approved for good grades"
        )
        processed_request = Mock()
        family_service.approval_repo.process_approval_decision.return_value = processed_request
        
        result = await family_service.process_spending_approval(
            request_id, decision, approver_id
        )
        
        family_service.approval_repo.process_approval_decision.assert_called_once_with(
            request_id, decision, approver_id
        )
        assert result == processed_request
    
    @pytest.mark.asyncio
    async def test_process_spending_approval_validation_error(self, family_service):
        """Test spending approval processing validation error."""
        request_id = str(uuid4())
        approver_id = str(uuid4())
        decision = SpendingApprovalDecision(
            decision="invalid_decision",
            notes="Invalid decision"
        )
        
        with pytest.raises(ValidationError, match="Decision must be 'approved' or 'denied'"):
            await family_service.process_spending_approval(request_id, decision, approver_id)
    
    @pytest.mark.asyncio
    async def test_get_member_spending_requests(self, family_service):
        """Test getting member spending requests."""
        member_id = str(uuid4())
        expected_requests = [Mock(), Mock()]
        family_service.approval_repo.get_member_approval_requests.return_value = expected_requests
        
        result = await family_service.get_member_spending_requests(member_id)
        
        family_service.approval_repo.get_member_approval_requests.assert_called_once_with(
            member_id, False
        )
        assert result == expected_requests

    # Dashboard and analytics tests
    @pytest.mark.asyncio
    async def test_get_family_dashboard_success(self, family_service):
        """Test successful family dashboard retrieval."""
        family_id = str(uuid4())
        user_id = str(uuid4())
        
        # Mock family
        mock_family = Mock()
        mock_family.shared_budgets = [Mock(), Mock()]
        mock_family.shared_goals = [Mock()]
        family_service.get_family = AsyncMock(return_value=mock_family)
        
        # Mock members
        mock_members = [Mock(), Mock(), Mock()]
        family_service.get_family_members = AsyncMock(return_value=mock_members)
        
        # Mock invitations
        mock_invitations = [
            Mock(status="pending"),
            Mock(status="accepted"),
            Mock(status="pending")
        ]
        family_service.get_family_invitations = AsyncMock(return_value=mock_invitations)
        
        # Mock pending approvals
        mock_approvals = [Mock(), Mock()]
        family_service.get_pending_approvals = AsyncMock(return_value=mock_approvals)
        
        result = await family_service.get_family_dashboard(family_id, user_id)
        
        assert result.family_id == family_id
        assert result.member_count == 3
        assert result.pending_invitations == 2  # Only pending invitations
        assert result.pending_approvals == 2
        assert result.shared_budgets == 2
        assert result.shared_goals == 1
        assert result.total_family_spending == Decimal("2500.00")
        assert len(result.recent_activities) > 0
    
    @pytest.mark.asyncio
    async def test_get_family_dashboard_not_found(self, family_service):
        """Test family dashboard with non-existent family."""
        family_id = str(uuid4())
        user_id = str(uuid4())
        family_service.get_family = AsyncMock(return_value=None)
        
        with pytest.raises(NotFoundError, match="Family not found"):
            await family_service.get_family_dashboard(family_id, user_id)

    # Helper methods tests
    @pytest.mark.asyncio
    async def test_check_member_permissions_administrator(self, family_service):
        """Test permission check for administrator."""
        user_id = str(uuid4())
        family_id = str(uuid4())
        required_permission = "can_approve_spending"
        
        # Mock administrator member
        admin_member = Mock()
        admin_member.user_id = user_id
        admin_member.role = "administrator"
        admin_member.permissions = {}
        
        family_service.member_repo.get_family_members.return_value = [admin_member]
        
        result = await family_service._check_member_permissions(
            user_id, family_id, required_permission
        )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_check_member_permissions_with_permission(self, family_service):
        """Test permission check for member with specific permission."""
        user_id = str(uuid4())
        family_id = str(uuid4())
        required_permission = "can_approve_spending"
        
        # Mock member with permission
        member = Mock()
        member.user_id = user_id
        member.role = "spouse"
        member.permissions = {"can_approve_spending": True}
        
        family_service.member_repo.get_family_members.return_value = [member]
        
        result = await family_service._check_member_permissions(
            user_id, family_id, required_permission
        )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_check_member_permissions_without_permission(self, family_service):
        """Test permission check for member without specific permission."""
        user_id = str(uuid4())
        family_id = str(uuid4())
        required_permission = "can_approve_spending"
        
        # Mock member without permission
        member = Mock()
        member.user_id = user_id
        member.role = "teen"
        member.permissions = {"can_view_budgets": True}
        
        family_service.member_repo.get_family_members.return_value = [member]
        
        result = await family_service._check_member_permissions(
            user_id, family_id, required_permission
        )
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_check_member_permissions_not_member(self, family_service):
        """Test permission check for non-member."""
        user_id = str(uuid4())
        family_id = str(uuid4())
        required_permission = "can_approve_spending"
        
        # Mock empty member list
        family_service.member_repo.get_family_members.return_value = []
        
        result = await family_service._check_member_permissions(
            user_id, family_id, required_permission
        )
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_validate_spending_request_within_limit(self, family_service):
        """Test spending request validation within limits."""
        member = Mock()
        member.spending_limit = Decimal("1000.00")
        member.requires_approval_over = Decimal("500.00")
        
        amount = Decimal("300.00")  # Within both limits
        
        result = await family_service._validate_spending_request(member, amount)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_validate_spending_request_exceeds_limit(self, family_service):
        """Test spending request validation exceeding spending limit."""
        member = Mock()
        member.spending_limit = Decimal("1000.00")
        member.requires_approval_over = Decimal("500.00")
        
        amount = Decimal("1200.00")  # Exceeds spending limit
        
        result = await family_service._validate_spending_request(member, amount)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_validate_spending_request_requires_approval(self, family_service):
        """Test spending request validation requiring approval."""
        member = Mock()
        member.spending_limit = Decimal("1000.00")
        member.requires_approval_over = Decimal("500.00")
        
        amount = Decimal("750.00")  # Within spending limit but requires approval
        
        result = await family_service._validate_spending_request(member, amount)
        
        assert result is True  # Valid request but requires approval

    # Cleanup operations tests
    @pytest.mark.asyncio
    async def test_cleanup_expired_invitations(self, family_service):
        """Test cleanup of expired invitations."""
        mock_result = Mock()
        mock_result.rowcount = 5
        family_service.session.execute.return_value = mock_result
        
        result = await family_service.cleanup_expired_invitations()
        
        assert result == 5
        family_service.session.execute.assert_called_once()
        family_service.session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_approval_requests(self, family_service):
        """Test cleanup of expired approval requests."""
        mock_result = Mock()
        mock_result.rowcount = 3
        family_service.session.execute.return_value = mock_result
        
        result = await family_service.cleanup_expired_approval_requests()
        
        assert result == 3
        family_service.session.execute.assert_called_once()
        family_service.session.commit.assert_called_once()


class TestFamilyServiceEdgeCases:
    """Test edge cases and error scenarios."""
    
    @pytest.fixture
    def family_service(self):
        """Create family service with mocked repositories."""
        service = FamilyService.__new__(FamilyService)
        service.session = AsyncMock()
        service.family_repo = AsyncMock()
        service.member_repo = AsyncMock()
        service.invitation_repo = AsyncMock()
        service.approval_repo = AsyncMock()
        return service
    
    @pytest.mark.asyncio
    async def test_token_generation_uniqueness(self, family_service):
        """Test that invitation tokens are unique."""
        tokens = set()
        for _ in range(100):
            token = family_service._generate_invitation_token()
            assert token not in tokens
            tokens.add(token)
    
    @pytest.mark.asyncio
    async def test_concurrent_member_addition_edge_case(self, family_service):
        """Test edge case for concurrent member additions."""
        family_id = str(uuid4())
        added_by_user_id = str(uuid4())
        member_data = FamilyMemberCreate(
            name="Test Member",
            email="test@example.com",
            role=FamilyRole.TEEN
        )
        
        # Simulate race condition where family becomes full between check and add
        family_service.member_repo.add_member_to_family.return_value = None
        
        result = await family_service.add_family_member(
            family_id, member_data, added_by_user_id
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_invitation_acceptance_race_condition(self, family_service):
        """Test invitation acceptance race condition."""
        token = "inv_test123"
        user_id = str(uuid4())
        
        # Simulate invitation being accepted by someone else
        family_service.invitation_repo.accept_invitation.return_value = None
        
        with pytest.raises(ValidationError, match="Invalid or expired invitation"):
            await family_service.accept_invitation(token, user_id)
    
    @pytest.mark.asyncio
    async def test_spending_approval_timeout_edge_case(self, family_service):
        """Test spending approval that times out during processing."""
        request_id = str(uuid4())
        approver_id = str(uuid4())
        decision = SpendingApprovalDecision(
            decision=ApprovalStatus.APPROVED,
            notes="Late approval"
        )
        
        # Simulate request expiring during processing
        family_service.approval_repo.process_approval_decision.return_value = None
        
        result = await family_service.process_spending_approval(
            request_id, decision, approver_id
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_member_limit_boundary_conditions(self, family_service):
        """Test member limit boundary conditions."""
        sample_data = FamilyCreate(
            name="Test Family",
            max_members=2  # Minimum allowed
        )
        administrator_id = str(uuid4())
        created_family = Mock()
        family_service.family_repo.create_family.return_value = created_family
        
        result = await family_service.create_family(sample_data, administrator_id)
        
        assert result == created_family
        
        # Test with maximum members
        sample_data.max_members = 50  # Maximum typically allowed
        result = await family_service.create_family(sample_data, administrator_id)
        assert result == created_family
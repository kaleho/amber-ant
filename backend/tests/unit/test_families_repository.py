"""Unit tests for families repository."""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from sqlalchemy.exc import IntegrityError

from src.families.repository import (
    FamilyRepository, FamilyMemberRepository, 
    FamilyInvitationRepository, SpendingApprovalRepository
)
from src.families.models import Family, FamilyMember, FamilyInvitation, SpendingApprovalRequest
from src.families.schemas import (
    FamilyCreate, FamilyUpdate, FamilyMemberCreate, FamilyMemberUpdate,
    FamilyInvitationCreate, SpendingApprovalRequestCreate, SpendingApprovalDecision,
    FamilyRole, FamilyMemberStatus, InvitationStatus, ApprovalStatus
)


class TestFamilyRepository:
    """Test family repository database operations."""
    
    @pytest.fixture
    def mock_session(self):
        """Mock database session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.delete = AsyncMock()
        session.add = Mock()
        return session
    
    @pytest.fixture
    def family_repo(self, mock_session):
        """Family repository with mocked session."""
        return FamilyRepository(mock_session)
    
    @pytest.fixture
    def sample_family_data(self):
        """Sample family creation data."""
        return FamilyCreate(
            name="Test Family",
            description="A test family",
            max_members=6,
            plan_type="premium",
            settings={"test": True}
        )
    
    @pytest.mark.asyncio
    async def test_create_family_success(self, family_repo, mock_session, sample_family_data):
        """Test successful family creation."""
        administrator_id = str(uuid4())
        
        # Mock family creation
        mock_family = Mock()
        mock_family.id = str(uuid4())
        mock_session.add.side_effect = lambda obj: setattr(obj, 'id', mock_family.id)
        
        result = await family_repo.create_family(sample_family_data, administrator_id)
        
        # Verify family was added to session
        assert mock_session.add.call_count == 2  # Family + administrator member
        mock_session.commit.assert_called()
        mock_session.refresh.assert_called()
        
        # Verify family data
        family_call = mock_session.add.call_args_list[0][0][0]
        assert isinstance(family_call, Family)
        assert family_call.name == sample_family_data.name
        assert family_call.administrator_id == administrator_id
        assert family_call.current_member_count == 1
        
        # Verify administrator member was created
        member_call = mock_session.add.call_args_list[1][0][0]
        assert isinstance(member_call, FamilyMember)
        assert member_call.role == "administrator"
        assert member_call.status == "active"
        assert member_call.permissions["can_invite_members"] is True
    
    @pytest.mark.asyncio
    async def test_get_families_for_user(self, family_repo, mock_session):
        """Test getting families for a user."""
        user_id = str(uuid4())
        mock_families = [Mock(), Mock()]
        
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_families
        mock_session.execute.return_value = mock_result
        
        result = await family_repo.get_families_for_user(user_id)
        
        mock_session.execute.assert_called_once()
        assert result == mock_families
    
    @pytest.mark.asyncio
    async def test_get_families_for_user_include_inactive(self, family_repo, mock_session):
        """Test getting families including inactive ones."""
        user_id = str(uuid4())
        mock_families = [Mock(), Mock(), Mock()]  # Including inactive
        
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_families
        mock_session.execute.return_value = mock_result
        
        result = await family_repo.get_families_for_user(user_id, include_inactive=True)
        
        mock_session.execute.assert_called_once()
        assert result == mock_families
    
    @pytest.mark.asyncio
    async def test_get_family_with_members_success(self, family_repo, mock_session):
        """Test getting family with members when user is a member."""
        family_id = str(uuid4())
        user_id = str(uuid4())
        
        # Mock member verification (user is a member)
        mock_member_result = Mock()
        mock_member_result.scalar_one_or_none.return_value = Mock()  # Member exists
        
        # Mock family retrieval
        mock_family = Mock()
        mock_family_result = Mock()
        mock_family_result.scalar_one_or_none.return_value = mock_family
        
        mock_session.execute.side_effect = [mock_member_result, mock_family_result]
        
        result = await family_repo.get_family_with_members(family_id, user_id)
        
        assert mock_session.execute.call_count == 2
        assert result == mock_family
    
    @pytest.mark.asyncio
    async def test_get_family_with_members_not_member(self, family_repo, mock_session):
        """Test getting family when user is not a member."""
        family_id = str(uuid4())
        user_id = str(uuid4())
        
        # Mock member verification (user is not a member)
        mock_member_result = Mock()
        mock_member_result.scalar_one_or_none.return_value = None  # No member found
        
        mock_session.execute.return_value = mock_member_result
        
        result = await family_repo.get_family_with_members(family_id, user_id)
        
        assert mock_session.execute.call_count == 1  # Only member check
        assert result is None
    
    @pytest.mark.asyncio
    async def test_update_family_success(self, family_repo, mock_session, sample_family_data):
        """Test successful family update."""
        family_id = str(uuid4())
        user_id = str(uuid4())
        update_data = FamilyUpdate(name="Updated Family", max_members=8)
        
        # Mock existing family retrieval
        mock_family = Mock()
        mock_family.administrator_id = user_id  # User is administrator
        family_repo.get_family_with_members = AsyncMock(return_value=mock_family)
        
        result = await family_repo.update_family(family_id, update_data, user_id)
        
        # Verify family was updated
        assert mock_family.name == update_data.name
        assert mock_family.max_members == update_data.max_members
        assert hasattr(mock_family, 'updated_at')
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_family)
        assert result == mock_family
    
    @pytest.mark.asyncio
    async def test_update_family_not_administrator(self, family_repo, mock_session):
        """Test family update by non-administrator."""
        family_id = str(uuid4())
        user_id = str(uuid4())
        update_data = FamilyUpdate(name="Updated Family")
        
        # Mock existing family with different administrator
        mock_family = Mock()
        mock_family.administrator_id = str(uuid4())  # Different user
        family_repo.get_family_with_members = AsyncMock(return_value=mock_family)
        
        result = await family_repo.update_family(family_id, update_data, user_id)
        
        assert result is None
        mock_session.commit.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_delete_family_success(self, family_repo, mock_session):
        """Test successful family deletion."""
        family_id = str(uuid4())
        user_id = str(uuid4())
        
        # Mock existing family with user as administrator
        mock_family = Mock()
        mock_family.administrator_id = user_id
        family_repo.get_family_with_members = AsyncMock(return_value=mock_family)
        
        result = await family_repo.delete_family(family_id, user_id)
        
        mock_session.delete.assert_called_once_with(mock_family)
        mock_session.commit.assert_called_once()
        assert result is True
    
    @pytest.mark.asyncio
    async def test_delete_family_not_found(self, family_repo):
        """Test deleting non-existent family."""
        family_id = str(uuid4())
        user_id = str(uuid4())
        
        family_repo.get_family_with_members = AsyncMock(return_value=None)
        
        result = await family_repo.delete_family(family_id, user_id)
        
        assert result is False


class TestFamilyMemberRepository:
    """Test family member repository operations."""
    
    @pytest.fixture
    def mock_session(self):
        """Mock database session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.delete = AsyncMock()
        session.add = Mock()
        return session
    
    @pytest.fixture
    def member_repo(self, mock_session):
        """Member repository with mocked session."""
        return FamilyMemberRepository(mock_session)
    
    @pytest.fixture
    def sample_member_data(self):
        """Sample member creation data."""
        return FamilyMemberCreate(
            name="Test Member",
            email="member@example.com",
            role=FamilyRole.SPOUSE,
            spending_limit=Decimal("1000.00"),
            requires_approval_over=Decimal("500.00"),
            approved_categories=["Food", "Transport"]
        )
    
    @pytest.mark.asyncio
    async def test_get_by_id_success(self, member_repo, mock_session):
        """Test getting member by ID."""
        member_id = str(uuid4())
        mock_member = Mock()
        
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_member
        mock_session.execute.return_value = mock_result
        
        result = await member_repo.get_by_id(member_id)
        
        mock_session.execute.assert_called_once()
        assert result == mock_member
    
    @pytest.mark.asyncio
    async def test_get_family_members_success(self, member_repo, mock_session):
        """Test getting family members when user is authorized."""
        family_id = str(uuid4())
        user_id = str(uuid4())
        
        # Mock user verification (user is a member)
        mock_verification_result = Mock()
        mock_verification_result.scalar_one_or_none.return_value = Mock()
        
        # Mock members retrieval
        mock_members = [Mock(), Mock()]
        mock_members_result = Mock()
        mock_members_result.scalars.return_value.all.return_value = mock_members
        
        mock_session.execute.side_effect = [mock_verification_result, mock_members_result]
        
        result = await member_repo.get_family_members(family_id, user_id)
        
        assert mock_session.execute.call_count == 2
        assert result == mock_members
    
    @pytest.mark.asyncio
    async def test_get_family_members_unauthorized(self, member_repo, mock_session):
        """Test getting family members when user is not authorized."""
        family_id = str(uuid4())
        user_id = str(uuid4())
        
        # Mock user verification (user is not a member)
        mock_verification_result = Mock()
        mock_verification_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_verification_result
        
        result = await member_repo.get_family_members(family_id, user_id)
        
        assert mock_session.execute.call_count == 1  # Only verification query
        assert result == []
    
    @pytest.mark.asyncio
    async def test_add_member_to_family_success(self, member_repo, mock_session, sample_member_data):
        """Test successful member addition to family."""
        family_id = str(uuid4())
        added_by_user_id = str(uuid4())
        
        # Mock family verification (user is administrator)
        mock_family = Mock()
        mock_family.current_member_count = 3
        mock_family.max_members = 6
        
        mock_admin_result = Mock()
        mock_admin_result.scalar_one_or_none.return_value = mock_family
        mock_session.execute.return_value = mock_admin_result
        
        # Mock member creation
        mock_member = Mock()
        mock_session.add.side_effect = lambda obj: setattr(obj, 'id', str(uuid4()))
        
        result = await member_repo.add_member_to_family(
            family_id, sample_member_data, added_by_user_id
        )
        
        # Verify member was added
        mock_session.add.assert_called_once()
        member_arg = mock_session.add.call_args[0][0]
        assert isinstance(member_arg, FamilyMember)
        assert member_arg.name == sample_member_data.name
        assert member_arg.email == sample_member_data.email
        assert member_arg.role == sample_member_data.role
        
        # Verify family member count was updated
        assert mock_family.current_member_count == 4
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_member_family_full(self, member_repo, mock_session, sample_member_data):
        """Test adding member to full family."""
        family_id = str(uuid4())
        added_by_user_id = str(uuid4())
        
        # Mock family at capacity
        mock_family = Mock()
        mock_family.current_member_count = 6
        mock_family.max_members = 6
        
        mock_admin_result = Mock()
        mock_admin_result.scalar_one_or_none.return_value = mock_family
        mock_session.execute.return_value = mock_admin_result
        
        result = await member_repo.add_member_to_family(
            family_id, sample_member_data, added_by_user_id
        )
        
        assert result is None
        mock_session.add.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_add_member_not_administrator(self, member_repo, mock_session, sample_member_data):
        """Test adding member by non-administrator."""
        family_id = str(uuid4())
        added_by_user_id = str(uuid4())
        
        # Mock family not found (user is not administrator)
        mock_admin_result = Mock()
        mock_admin_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_admin_result
        
        result = await member_repo.add_member_to_family(
            family_id, sample_member_data, added_by_user_id
        )
        
        assert result is None
        mock_session.add.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_update_member_success(self, member_repo, mock_session):
        """Test successful member update."""
        member_id = str(uuid4())
        updated_by_user_id = str(uuid4())
        update_data = FamilyMemberUpdate(role=FamilyRole.TEEN, spending_limit=Decimal("200.00"))
        
        # Mock existing member
        mock_member = Mock()
        mock_member.user_id = updated_by_user_id  # User can update themselves
        member_repo.get_by_id = AsyncMock(return_value=mock_member)
        
        # Mock family verification
        mock_family = Mock()
        mock_family.administrator_id = str(uuid4())  # Different admin
        mock_family_result = Mock()
        mock_family_result.scalar_one_or_none.return_value = mock_family
        mock_session.execute.return_value = mock_family_result
        
        result = await member_repo.update_member(member_id, update_data, updated_by_user_id)
        
        # Verify member was updated
        assert mock_member.role == update_data.role
        assert mock_member.spending_limit == update_data.spending_limit
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_member)
        assert result == mock_member
    
    @pytest.mark.asyncio
    async def test_update_member_unauthorized(self, member_repo, mock_session):
        """Test member update by unauthorized user."""
        member_id = str(uuid4())
        updated_by_user_id = str(uuid4())
        update_data = FamilyMemberUpdate(role=FamilyRole.TEEN)
        
        # Mock existing member with different user ID
        mock_member = Mock()
        mock_member.user_id = str(uuid4())  # Different user
        member_repo.get_by_id = AsyncMock(return_value=mock_member)
        
        # Mock family with different administrator
        mock_family = Mock()
        mock_family.administrator_id = str(uuid4())  # Different admin
        mock_family_result = Mock()
        mock_family_result.scalar_one_or_none.return_value = mock_family
        mock_session.execute.return_value = mock_family_result
        
        result = await member_repo.update_member(member_id, update_data, updated_by_user_id)
        
        assert result is None
        mock_session.commit.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_remove_member_success(self, member_repo, mock_session):
        """Test successful member removal."""
        member_id = str(uuid4())
        removed_by_user_id = str(uuid4())
        
        # Mock existing member (not administrator)
        mock_member = Mock()
        mock_member.role = "spouse"
        member_repo.get_by_id = AsyncMock(return_value=mock_member)
        
        # Mock family with user as administrator
        mock_family = Mock()
        mock_family.administrator_id = removed_by_user_id
        mock_family.current_member_count = 3
        mock_family_result = Mock()
        mock_family_result.scalar_one_or_none.return_value = mock_family
        mock_session.execute.return_value = mock_family_result
        
        result = await member_repo.remove_member(member_id, removed_by_user_id)
        
        mock_session.delete.assert_called_once_with(mock_member)
        assert mock_family.current_member_count == 2
        mock_session.commit.assert_called_once()
        assert result is True
    
    @pytest.mark.asyncio
    async def test_remove_administrator_member(self, member_repo, mock_session):
        """Test attempting to remove administrator member."""
        member_id = str(uuid4())
        removed_by_user_id = str(uuid4())
        
        # Mock administrator member
        mock_member = Mock()
        mock_member.role = "administrator"
        member_repo.get_by_id = AsyncMock(return_value=mock_member)
        
        # Mock family
        mock_family = Mock()
        mock_family.administrator_id = removed_by_user_id
        mock_family_result = Mock()
        mock_family_result.scalar_one_or_none.return_value = mock_family
        mock_session.execute.return_value = mock_family_result
        
        result = await member_repo.remove_member(member_id, removed_by_user_id)
        
        assert result is False
        mock_session.delete.assert_not_called()


class TestFamilyInvitationRepository:
    """Test family invitation repository operations."""
    
    @pytest.fixture
    def mock_session(self):
        """Mock database session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.add = Mock()
        return session
    
    @pytest.fixture
    def invitation_repo(self, mock_session):
        """Invitation repository with mocked session."""
        return FamilyInvitationRepository(mock_session)
    
    @pytest.fixture
    def sample_invitation_data(self):
        """Sample invitation creation data."""
        return FamilyInvitationCreate(
            email="invite@example.com",
            role=FamilyRole.TEEN,
            message="Welcome!",
            permissions={"can_view_budgets": True},
            expires_in_days=7
        )
    
    @pytest.mark.asyncio
    async def test_create_invitation_success(self, invitation_repo, mock_session, sample_invitation_data):
        """Test successful invitation creation."""
        family_id = str(uuid4())
        inviter_id = str(uuid4())
        invitation_token = "inv_test123"
        
        result = await invitation_repo.create_invitation(
            family_id, sample_invitation_data, inviter_id, invitation_token
        )
        
        # Verify invitation was added
        mock_session.add.assert_called_once()
        invitation_arg = mock_session.add.call_args[0][0]
        assert isinstance(invitation_arg, FamilyInvitation)
        assert invitation_arg.family_id == family_id
        assert invitation_arg.inviter_id == inviter_id
        assert invitation_arg.email == sample_invitation_data.email
        assert invitation_arg.invitation_token == invitation_token
        
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_invitation_by_token_success(self, invitation_repo, mock_session):
        """Test getting invitation by token."""
        token = "inv_test123"
        mock_invitation = Mock()
        
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_invitation
        mock_session.execute.return_value = mock_result
        
        result = await invitation_repo.get_invitation_by_token(token)
        
        mock_session.execute.assert_called_once()
        assert result == mock_invitation
    
    @pytest.mark.asyncio
    async def test_get_family_invitations_authorized(self, invitation_repo, mock_session):
        """Test getting family invitations by administrator."""
        family_id = str(uuid4())
        user_id = str(uuid4())
        
        # Mock administrator verification
        mock_family_result = Mock()
        mock_family_result.scalar_one_or_none.return_value = Mock()  # Family found
        
        # Mock invitations retrieval
        mock_invitations = [Mock(), Mock()]
        mock_invitations_result = Mock()
        mock_invitations_result.scalars.return_value.all.return_value = mock_invitations
        
        mock_session.execute.side_effect = [mock_family_result, mock_invitations_result]
        
        result = await invitation_repo.get_family_invitations(family_id, user_id)
        
        assert mock_session.execute.call_count == 2
        assert result == mock_invitations
    
    @pytest.mark.asyncio
    async def test_get_family_invitations_unauthorized(self, invitation_repo, mock_session):
        """Test getting family invitations by non-administrator."""
        family_id = str(uuid4())
        user_id = str(uuid4())
        
        # Mock administrator verification (user is not administrator)
        mock_family_result = Mock()
        mock_family_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_family_result
        
        result = await invitation_repo.get_family_invitations(family_id, user_id)
        
        assert mock_session.execute.call_count == 1  # Only verification
        assert result == []
    
    @pytest.mark.asyncio
    async def test_accept_invitation_success(self, invitation_repo, mock_session):
        """Test successful invitation acceptance."""
        token = "inv_test123"
        user_id = str(uuid4())
        
        # Mock valid invitation
        mock_invitation = Mock()
        mock_invitation.status = "pending"
        mock_invitation.expires_at = datetime.utcnow() + timedelta(days=1)
        mock_invitation.family_id = str(uuid4())
        mock_invitation.email = "test@example.com"
        mock_invitation.role = "teen"
        mock_invitation.permissions = {"can_view_budgets": True}
        
        # Mock family with space
        mock_family = Mock()
        mock_family.current_member_count = 3
        mock_family.max_members = 6
        mock_invitation.family = mock_family
        
        invitation_repo.get_invitation_by_token = AsyncMock(return_value=mock_invitation)
        
        result = await invitation_repo.accept_invitation(token, user_id)
        
        # Verify member was created
        mock_session.add.assert_called_once()
        member_arg = mock_session.add.call_args[0][0]
        assert isinstance(member_arg, FamilyMember)
        assert member_arg.user_id == user_id
        assert member_arg.email == mock_invitation.email
        assert member_arg.role == mock_invitation.role
        
        # Verify invitation was updated
        assert mock_invitation.status == "accepted"
        assert mock_invitation.accepted_by_user_id == user_id
        assert hasattr(mock_invitation, 'accepted_at')
        
        # Verify family member count was updated
        assert mock_family.current_member_count == 4
        
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_accept_invitation_expired(self, invitation_repo, mock_session):
        """Test accepting expired invitation."""
        token = "inv_expired123"
        user_id = str(uuid4())
        
        # Mock expired invitation
        mock_invitation = Mock()
        mock_invitation.status = "pending"
        mock_invitation.expires_at = datetime.utcnow() - timedelta(hours=1)  # Expired
        
        invitation_repo.get_invitation_by_token = AsyncMock(return_value=mock_invitation)
        
        result = await invitation_repo.accept_invitation(token, user_id)
        
        assert result is None
        mock_session.add.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_accept_invitation_family_full(self, invitation_repo, mock_session):
        """Test accepting invitation when family is full."""
        token = "inv_test123"
        user_id = str(uuid4())
        
        # Mock valid invitation but full family
        mock_invitation = Mock()
        mock_invitation.status = "pending"
        mock_invitation.expires_at = datetime.utcnow() + timedelta(days=1)
        
        mock_family = Mock()
        mock_family.current_member_count = 6
        mock_family.max_members = 6  # Full
        mock_invitation.family = mock_family
        
        invitation_repo.get_invitation_by_token = AsyncMock(return_value=mock_invitation)
        
        result = await invitation_repo.accept_invitation(token, user_id)
        
        assert result is None
        mock_session.add.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_cancel_invitation_success(self, invitation_repo, mock_session):
        """Test successful invitation cancellation."""
        invitation_id = str(uuid4())
        user_id = str(uuid4())
        
        # Mock invitation by inviter
        mock_invitation = Mock()
        mock_invitation.inviter_id = user_id
        
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_invitation
        mock_session.execute.return_value = mock_result
        
        result = await invitation_repo.cancel_invitation(invitation_id, user_id)
        
        assert mock_invitation.status == "cancelled"
        mock_session.commit.assert_called_once()
        assert result is True
    
    @pytest.mark.asyncio
    async def test_cancel_invitation_unauthorized(self, invitation_repo, mock_session):
        """Test cancelling invitation by non-inviter."""
        invitation_id = str(uuid4())
        user_id = str(uuid4())
        
        # Mock invitation by different user
        mock_invitation = Mock()
        mock_invitation.inviter_id = str(uuid4())  # Different inviter
        
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_invitation
        mock_session.execute.return_value = mock_result
        
        result = await invitation_repo.cancel_invitation(invitation_id, user_id)
        
        assert result is False
        mock_session.commit.assert_not_called()


class TestSpendingApprovalRepository:
    """Test spending approval repository operations."""
    
    @pytest.fixture
    def mock_session(self):
        """Mock database session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.add = Mock()
        return session
    
    @pytest.fixture
    def approval_repo(self, mock_session):
        """Approval repository with mocked session."""
        return SpendingApprovalRepository(mock_session)
    
    @pytest.fixture
    def sample_request_data(self):
        """Sample spending request creation data."""
        return SpendingApprovalRequestCreate(
            amount=Decimal("75.00"),
            description="Game purchase",
            category="Entertainment",
            merchant="GameStore",
            expires_in_hours=24
        )
    
    @pytest.mark.asyncio
    async def test_create_approval_request_success(self, approval_repo, mock_session, sample_request_data):
        """Test successful approval request creation."""
        family_id = str(uuid4())
        member_id = str(uuid4())
        
        result = await approval_repo.create_approval_request(
            family_id, member_id, sample_request_data
        )
        
        # Verify request was added
        mock_session.add.assert_called_once()
        request_arg = mock_session.add.call_args[0][0]
        assert isinstance(request_arg, SpendingApprovalRequest)
        assert request_arg.family_id == family_id
        assert request_arg.member_id == member_id
        assert request_arg.amount == sample_request_data.amount
        assert request_arg.description == sample_request_data.description
        
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_pending_approvals_for_family_admin(self, approval_repo, mock_session):
        """Test getting pending approvals by administrator."""
        family_id = str(uuid4())
        user_id = str(uuid4())
        
        # Mock member verification
        mock_member = Mock()
        mock_member_result = Mock()
        mock_member_result.scalar_one_or_none.return_value = mock_member
        
        # Mock family verification (user is administrator)
        mock_family = Mock()
        mock_family.administrator_id = user_id
        mock_family_result = Mock()
        mock_family_result.scalar_one_or_none.return_value = mock_family
        
        # Mock pending approvals
        mock_requests = [Mock(), Mock()]
        mock_requests_result = Mock()
        mock_requests_result.scalars.return_value.all.return_value = mock_requests
        
        mock_session.execute.side_effect = [mock_member_result, mock_family_result, mock_requests_result]
        
        result = await approval_repo.get_pending_approvals_for_family(family_id, user_id)
        
        assert mock_session.execute.call_count == 3
        assert result == mock_requests
    
    @pytest.mark.asyncio
    async def test_get_pending_approvals_with_permission(self, approval_repo, mock_session):
        """Test getting pending approvals by member with permission."""
        family_id = str(uuid4())
        user_id = str(uuid4())
        
        # Mock member with approval permission
        mock_member = Mock()
        mock_member.permissions = {"can_approve_spending": True}
        mock_member_result = Mock()
        mock_member_result.scalar_one_or_none.return_value = mock_member
        
        # Mock family (user is not administrator)
        mock_family = Mock()
        mock_family.administrator_id = str(uuid4())  # Different user
        mock_family_result = Mock()
        mock_family_result.scalar_one_or_none.return_value = mock_family
        
        # Mock pending approvals
        mock_requests = [Mock()]
        mock_requests_result = Mock()
        mock_requests_result.scalars.return_value.all.return_value = mock_requests
        
        mock_session.execute.side_effect = [mock_member_result, mock_family_result, mock_requests_result]
        
        result = await approval_repo.get_pending_approvals_for_family(family_id, user_id)
        
        assert result == mock_requests
    
    @pytest.mark.asyncio
    async def test_get_pending_approvals_unauthorized(self, approval_repo, mock_session):
        """Test getting pending approvals by unauthorized user."""
        family_id = str(uuid4())
        user_id = str(uuid4())
        
        # Mock member without approval permission
        mock_member = Mock()
        mock_member.permissions = {"can_view_budgets": True}  # No approval permission
        mock_member_result = Mock()
        mock_member_result.scalar_one_or_none.return_value = mock_member
        
        # Mock family (user is not administrator)
        mock_family = Mock()
        mock_family.administrator_id = str(uuid4())
        mock_family_result = Mock()
        mock_family_result.scalar_one_or_none.return_value = mock_family
        
        mock_session.execute.side_effect = [mock_member_result, mock_family_result]
        
        result = await approval_repo.get_pending_approvals_for_family(family_id, user_id)
        
        assert result == []
        assert mock_session.execute.call_count == 2  # No requests query
    
    @pytest.mark.asyncio
    async def test_process_approval_decision_success(self, approval_repo, mock_session):
        """Test successful approval decision processing."""
        request_id = str(uuid4())
        approver_id = str(uuid4())
        decision = SpendingApprovalDecision(
            decision=ApprovalStatus.APPROVED,
            notes="Approved for good grades"
        )
        
        # Mock pending request
        mock_request = Mock()
        mock_request.status = "pending"
        mock_request.expires_at = datetime.utcnow() + timedelta(hours=1)
        mock_request.family_id = str(uuid4())
        
        mock_request_result = Mock()
        mock_request_result.scalar_one_or_none.return_value = mock_request
        
        # Mock family verification (user is administrator)
        mock_family = Mock()
        mock_family.administrator_id = approver_id
        mock_family_result = Mock()
        mock_family_result.scalar_one_or_none.return_value = mock_family
        
        mock_session.execute.side_effect = [mock_request_result, mock_family_result]
        
        result = await approval_repo.process_approval_decision(request_id, decision, approver_id)
        
        # Verify request was updated
        assert mock_request.status == decision.decision
        assert mock_request.approved_by == approver_id
        assert mock_request.approval_notes == decision.notes
        assert hasattr(mock_request, 'approved_at')
        
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_request)
        assert result == mock_request
    
    @pytest.mark.asyncio
    async def test_process_approval_decision_expired(self, approval_repo, mock_session):
        """Test processing expired approval request."""
        request_id = str(uuid4())
        approver_id = str(uuid4())
        decision = SpendingApprovalDecision(decision=ApprovalStatus.APPROVED)
        
        # Mock expired request
        mock_request = Mock()
        mock_request.status = "pending"
        mock_request.expires_at = datetime.utcnow() - timedelta(hours=1)  # Expired
        
        mock_request_result = Mock()
        mock_request_result.scalar_one_or_none.return_value = mock_request
        mock_session.execute.return_value = mock_request_result
        
        result = await approval_repo.process_approval_decision(request_id, decision, approver_id)
        
        assert result is None
        mock_session.commit.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_member_approval_requests(self, approval_repo, mock_session):
        """Test getting approval requests for a member."""
        member_id = str(uuid4())
        
        # Mock member requests
        mock_requests = [Mock(), Mock()]
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_requests
        mock_session.execute.return_value = mock_result
        
        result = await approval_repo.get_member_approval_requests(member_id)
        
        mock_session.execute.assert_called_once()
        assert result == mock_requests
    
    @pytest.mark.asyncio
    async def test_get_member_approval_requests_include_processed(self, approval_repo, mock_session):
        """Test getting all approval requests for a member including processed ones."""
        member_id = str(uuid4())
        
        # Mock all member requests (including processed)
        mock_requests = [Mock(), Mock(), Mock()]
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_requests
        mock_session.execute.return_value = mock_result
        
        result = await approval_repo.get_member_approval_requests(member_id, include_processed=True)
        
        mock_session.execute.assert_called_once()
        assert result == mock_requests
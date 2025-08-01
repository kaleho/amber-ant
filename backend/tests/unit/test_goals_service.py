"""Comprehensive unit tests for goals service module."""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import uuid4

from src.goals.service import GoalService
from src.goals.models import GoalStatus, GoalType, GoalPriority, MilestoneStatus
from src.goals.schemas import (
    SavingsGoalCreate, SavingsGoalUpdate, SavingsGoalResponse,
    GoalContributionCreate, GoalMilestoneCreate
)
from src.exceptions import NotFoundError, ValidationError, BusinessLogicError


@pytest.fixture
def goal_service():
    """Create goal service with mocked repositories."""
    service = GoalService()
    service.goal_repo = AsyncMock()
    service.milestone_repo = AsyncMock()
    service.contribution_repo = AsyncMock()
    service.category_repo = AsyncMock()
    service.template_repo = AsyncMock()
    return service


@pytest.fixture
def sample_goal():
    """Sample goal for testing."""
    return Mock(
        id=str(uuid4()),
        user_id=str(uuid4()),
        name="Emergency Fund",
        description="6 months of expenses",
        goal_type=GoalType.EMERGENCY_FUND,
        target_amount=Decimal("15000.00"),
        current_amount=Decimal("7500.00"),
        monthly_contribution=Decimal("500.00"),
        target_date=date.today() + timedelta(days=180),
        status=GoalStatus.ACTIVE,
        priority=GoalPriority.HIGH,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        progress_percentage=Decimal("50.00"),
        remaining_amount=Decimal("7500.00"),
        is_completed=False,
        days_remaining=180
    )


@pytest.fixture
def sample_goal_data():
    """Sample goal creation data."""
    return SavingsGoalCreate(
        name="Vacation Fund",
        description="Trip to Europe",
        target_amount=Decimal("5000.00"),
        target_date=date.today() + timedelta(days=365),
        goal_type=GoalType.VACATION,
        priority=GoalPriority.MEDIUM,
        initial_contribution=Decimal("100.00")
    )


@pytest.fixture
def sample_contribution():
    """Sample goal contribution for testing."""
    return Mock(
        id=str(uuid4()),
        goal_id=str(uuid4()),
        amount=Decimal("500.00"),
        contribution_date=date.today(),
        source_type="manual",
        description="Monthly contribution",
        created_at=datetime.utcnow()
    )


@pytest.fixture
def sample_milestone():
    """Sample goal milestone for testing."""
    return Mock(
        id=str(uuid4()),
        goal_id=str(uuid4()),
        name="First Quarter",
        description="25% milestone",
        target_amount=Decimal("3750.00"),
        target_date=date.today() + timedelta(days=90),
        status=MilestoneStatus.PENDING,
        is_automatic=True,
        created_at=datetime.utcnow()
    )


class TestGoalServiceCRUD:
    """Test basic CRUD operations for goals."""

    @pytest.mark.asyncio
    async def test_get_goals_success(self, goal_service, sample_goal):
        """Test successful retrieval of goals with pagination."""
        # Arrange
        user_id = str(uuid4())
        goal_service.goal_repo.get_multi_for_user.return_value = [sample_goal]
        
        # Act
        result = await goal_service.get_goals(user_id, page=1, per_page=10)
        
        # Assert
        assert len(result) == 1
        assert result[0].name == "Emergency Fund"
        goal_service.goal_repo.get_multi_for_user.assert_called_once_with(
            user_id=user_id,
            filters={},
            offset=0,
            limit=10,
            order_by="-created_at",
            load_relationships=["milestones", "contributions"]
        )

    @pytest.mark.asyncio
    async def test_get_goals_with_filters(self, goal_service, sample_goal):
        """Test goals retrieval with filters."""
        # Arrange
        user_id = str(uuid4())
        filters = {
            "status": "active",
            "goal_type": "emergency_fund",
            "name_contains": "Emergency"
        }
        goal_service.goal_repo.get_multi_for_user.return_value = [sample_goal]
        
        # Act
        result = await goal_service.get_goals(user_id, filters=filters)
        
        # Assert
        expected_filters = {
            "status": "active",
            "goal_type": "emergency_fund",
            "name_ilike": "%Emergency%"
        }
        goal_service.goal_repo.get_multi_for_user.assert_called_once()
        call_args = goal_service.goal_repo.get_multi_for_user.call_args
        assert call_args[1]["filters"] == expected_filters

    @pytest.mark.asyncio
    async def test_get_goals_database_error(self, goal_service):
        """Test goals retrieval with database error."""
        # Arrange
        user_id = str(uuid4())
        goal_service.goal_repo.get_multi_for_user.side_effect = Exception("Database error")
        
        # Act & Assert
        with pytest.raises(BusinessLogicError, match="Failed to get goals"):
            await goal_service.get_goals(user_id)

    @pytest.mark.asyncio
    async def test_get_goal_success(self, goal_service, sample_goal):
        """Test successful retrieval of single goal."""
        # Arrange
        goal_id = str(uuid4())
        user_id = str(uuid4())
        goal_service.goal_repo.get_by_id_for_user.return_value = sample_goal
        
        # Act
        result = await goal_service.get_goal(goal_id, user_id)
        
        # Assert
        assert result.name == "Emergency Fund"
        goal_service.goal_repo.get_by_id_for_user.assert_called_once_with(
            goal_id, user_id, load_relationships=["milestones", "contributions"]
        )

    @pytest.mark.asyncio
    async def test_get_goal_not_found(self, goal_service):
        """Test goal retrieval when goal not found."""
        # Arrange
        goal_id = str(uuid4())
        user_id = str(uuid4())
        goal_service.goal_repo.get_by_id_for_user.return_value = None
        
        # Act & Assert
        with pytest.raises(NotFoundError, match="Goal not found"):
            await goal_service.get_goal(goal_id, user_id)

    @pytest.mark.asyncio
    async def test_create_goal_success(self, goal_service, sample_goal_data):
        """Test successful goal creation."""
        # Arrange
        user_id = str(uuid4())
        created_goal = Mock(id=str(uuid4()))
        goal_service.goal_repo.create.return_value = created_goal
        goal_service.goal_repo.get_by_id.return_value = created_goal
        
        # Act
        result = await goal_service.create_goal(user_id, sample_goal_data)
        
        # Assert
        goal_service.goal_repo.create.assert_called_once()
        created_data = goal_service.goal_repo.create.call_args[0][0]
        assert created_data["user_id"] == user_id
        assert created_data["name"] == "Vacation Fund"
        assert created_data["target_amount"] == Decimal("5000.00")
        assert created_data["current_amount"] == Decimal("0")
        assert created_data["status"] == GoalStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_create_goal_invalid_target_amount(self, goal_service):
        """Test goal creation with invalid target amount."""
        # Arrange
        user_id = str(uuid4())
        invalid_data = SavingsGoalCreate(
            name="Invalid Goal",
            target_amount=Decimal("-100.00"),
            goal_type=GoalType.GENERAL_SAVINGS
        )
        
        # Act & Assert
        with pytest.raises(ValidationError, match="Target amount must be positive"):
            await goal_service.create_goal(user_id, invalid_data)

    @pytest.mark.asyncio
    async def test_create_goal_past_target_date(self, goal_service):
        """Test goal creation with past target date."""
        # Arrange
        user_id = str(uuid4())
        invalid_data = SavingsGoalCreate(
            name="Invalid Goal",
            target_amount=Decimal("1000.00"),
            target_date=date.today() - timedelta(days=1),
            goal_type=GoalType.GENERAL_SAVINGS
        )
        
        # Act & Assert
        with pytest.raises(ValidationError, match="Target date must be in the future"):
            await goal_service.create_goal(user_id, invalid_data)

    @pytest.mark.asyncio
    async def test_create_goal_with_initial_contribution(self, goal_service, sample_goal_data):
        """Test goal creation with initial contribution."""
        # Arrange
        user_id = str(uuid4())
        created_goal = Mock(id=str(uuid4()))
        goal_service.goal_repo.create.return_value = created_goal
        goal_service.goal_repo.get_by_id.return_value = created_goal
        goal_service.create_contribution = AsyncMock()
        
        # Act
        await goal_service.create_goal(user_id, sample_goal_data)
        
        # Assert
        goal_service.create_contribution.assert_called_once()
        contribution_call = goal_service.create_contribution.call_args
        assert contribution_call[1]["contribution_data"].amount == Decimal("100.00")
        assert contribution_call[1]["contribution_data"].description == "Initial contribution"

    @pytest.mark.asyncio
    async def test_update_goal_success(self, goal_service, sample_goal):
        """Test successful goal update."""
        # Arrange
        goal_id = str(uuid4())
        user_id = str(uuid4())
        update_data = SavingsGoalUpdate(
            name="Updated Emergency Fund",
            target_amount=Decimal("18000.00")
        )
        
        goal_service.goal_repo.get_by_id_for_user.return_value = sample_goal
        goal_service.goal_repo.update.return_value = sample_goal
        goal_service.goal_repo.get_by_id.return_value = sample_goal
        
        # Act
        result = await goal_service.update_goal(goal_id, user_id, update_data)
        
        # Assert
        goal_service.goal_repo.update.assert_called_once()
        update_call = goal_service.goal_repo.update.call_args[0][1]
        assert "updated_at" in update_call
        assert update_call["remaining_amount"] == Decimal("10500.00")  # 18000 - 7500

    @pytest.mark.asyncio
    async def test_update_goal_not_found(self, goal_service):
        """Test goal update when goal not found."""
        # Arrange
        goal_id = str(uuid4())
        user_id = str(uuid4())
        update_data = SavingsGoalUpdate(name="Updated Name")
        goal_service.goal_repo.get_by_id_for_user.return_value = None
        
        # Act & Assert
        with pytest.raises(NotFoundError, match="Goal not found"):
            await goal_service.update_goal(goal_id, user_id, update_data)

    @pytest.mark.asyncio
    async def test_delete_goal_success(self, goal_service, sample_goal):
        """Test successful goal deletion (soft delete)."""
        # Arrange
        goal_id = str(uuid4())
        user_id = str(uuid4())
        goal_service.goal_repo.get_by_id_for_user.return_value = sample_goal
        goal_service.goal_repo.update.return_value = True
        
        # Act
        result = await goal_service.delete_goal(goal_id, user_id)
        
        # Assert
        assert result is True
        goal_service.goal_repo.update.assert_called_once_with(
            goal_id, {"status": GoalStatus.CANCELLED, "updated_at": pytest.approx(datetime.utcnow(), abs=timedelta(seconds=5))}
        )

    @pytest.mark.asyncio
    async def test_delete_goal_not_found(self, goal_service):
        """Test goal deletion when goal not found."""
        # Arrange
        goal_id = str(uuid4())
        user_id = str(uuid4())
        goal_service.goal_repo.get_by_id_for_user.return_value = None
        
        # Act & Assert
        with pytest.raises(NotFoundError, match="Goal not found"):
            await goal_service.delete_goal(goal_id, user_id)


class TestGoalServiceContributions:
    """Test goal contribution management."""

    @pytest.mark.asyncio
    async def test_get_goal_contributions_success(self, goal_service, sample_goal, sample_contribution):
        """Test successful retrieval of goal contributions."""
        # Arrange
        goal_id = str(uuid4())
        user_id = str(uuid4())
        goal_service.goal_repo.get_by_id_for_user.return_value = sample_goal
        goal_service.contribution_repo.get_contributions_for_goal.return_value = [sample_contribution]
        
        # Act
        result = await goal_service.get_goal_contributions(goal_id, user_id)
        
        # Assert
        assert len(result) == 1
        assert result[0].amount == Decimal("500.00")
        goal_service.contribution_repo.get_contributions_for_goal.assert_called_once_with(goal_id, 50)

    @pytest.mark.asyncio
    async def test_create_contribution_success(self, goal_service, sample_goal):
        """Test successful contribution creation."""
        # Arrange
        goal_id = str(uuid4())
        user_id = str(uuid4())
        contribution_data = GoalContributionCreate(
            amount=Decimal("250.00"),
            description="Bonus contribution",
            source_type="manual"
        )
        
        sample_goal.current_amount = Decimal("7500.00")
        sample_goal.target_amount = Decimal("15000.00")
        
        goal_service.goal_repo.get_by_id_for_user.return_value = sample_goal
        goal_service.contribution_repo.create.return_value = Mock(
            id=str(uuid4()),
            amount=Decimal("250.00")
        )
        goal_service._check_and_complete_milestones = AsyncMock()
        
        # Act
        result = await goal_service.create_contribution(goal_id, user_id, contribution_data)
        
        # Assert
        goal_service.contribution_repo.create.assert_called_once()
        goal_service.goal_repo.update.assert_called_once()
        
        # Check goal update values
        update_call = goal_service.goal_repo.update.call_args[0][1]
        assert update_call["current_amount"] == Decimal("7750.00")  # 7500 + 250
        assert update_call["remaining_amount"] == Decimal("7250.00")  # 15000 - 7750
        assert update_call["status"] == GoalStatus.ACTIVE  # Not yet completed

    @pytest.mark.asyncio
    async def test_create_contribution_completes_goal(self, goal_service, sample_goal):
        """Test contribution that completes the goal."""
        # Arrange
        goal_id = str(uuid4())
        user_id = str(uuid4())
        contribution_data = GoalContributionCreate(
            amount=Decimal("10000.00"),  # Large contribution to complete goal
            description="Final contribution",
            source_type="manual"
        )
        
        sample_goal.current_amount = Decimal("7500.00")
        sample_goal.target_amount = Decimal("15000.00")
        sample_goal.status = GoalStatus.ACTIVE
        
        goal_service.goal_repo.get_by_id_for_user.return_value = sample_goal
        goal_service.contribution_repo.create.return_value = Mock(id=str(uuid4()))
        goal_service._check_and_complete_milestones = AsyncMock()
        
        # Act
        await goal_service.create_contribution(goal_id, user_id, contribution_data)
        
        # Assert
        update_call = goal_service.goal_repo.update.call_args[0][1]
        assert update_call["current_amount"] == Decimal("17500.00")  # 7500 + 10000
        assert update_call["remaining_amount"] == Decimal("0")  # Capped at 0
        assert update_call["status"] == GoalStatus.COMPLETED
        assert update_call["completed_at"] is not None

    @pytest.mark.asyncio
    async def test_create_contribution_invalid_amount(self, goal_service, sample_goal):
        """Test contribution creation with invalid amount."""
        # Arrange
        goal_id = str(uuid4())
        user_id = str(uuid4())
        contribution_data = GoalContributionCreate(
            amount=Decimal("-100.00"),  # Negative amount
            source_type="manual"
        )
        
        goal_service.goal_repo.get_by_id_for_user.return_value = sample_goal
        
        # Act & Assert
        with pytest.raises(ValidationError, match="Contribution amount must be positive"):
            await goal_service.create_contribution(goal_id, user_id, contribution_data)

    @pytest.mark.asyncio
    async def test_create_contribution_goal_not_found(self, goal_service):
        """Test contribution creation when goal not found."""
        # Arrange
        goal_id = str(uuid4())
        user_id = str(uuid4())
        contribution_data = GoalContributionCreate(
            amount=Decimal("100.00"),
            source_type="manual"
        )
        goal_service.goal_repo.get_by_id_for_user.return_value = None
        
        # Act & Assert
        with pytest.raises(NotFoundError, match="Goal not found"):
            await goal_service.create_contribution(goal_id, user_id, contribution_data)


class TestGoalServiceMilestones:
    """Test goal milestone management."""

    @pytest.mark.asyncio
    async def test_get_goal_milestones_success(self, goal_service, sample_goal, sample_milestone):
        """Test successful retrieval of goal milestones."""
        # Arrange
        goal_id = str(uuid4())
        user_id = str(uuid4())
        goal_service.goal_repo.get_by_id_for_user.return_value = sample_goal
        goal_service.milestone_repo.get_milestones_for_goal.return_value = [sample_milestone]
        
        # Act
        result = await goal_service.get_goal_milestones(goal_id, user_id)
        
        # Assert
        assert len(result) == 1
        assert result[0].name == "First Quarter"
        goal_service.milestone_repo.get_milestones_for_goal.assert_called_once_with(goal_id)

    @pytest.mark.asyncio
    async def test_create_milestone_success(self, goal_service, sample_goal):
        """Test successful milestone creation."""
        # Arrange
        goal_id = str(uuid4())
        user_id = str(uuid4())
        milestone_data = GoalMilestoneCreate(
            name="Halfway There",
            description="50% milestone",
            target_amount=Decimal("7500.00"),
            target_percentage=Decimal("50.00"),
            target_date=date.today() + timedelta(days=120)
        )
        
        sample_goal.target_amount = Decimal("15000.00")
        goal_service.goal_repo.get_by_id_for_user.return_value = sample_goal
        goal_service.milestone_repo.create.return_value = Mock(id=str(uuid4()))
        
        # Act
        result = await goal_service.create_milestone(goal_id, user_id, milestone_data)
        
        # Assert
        goal_service.milestone_repo.create.assert_called_once()
        created_data = goal_service.milestone_repo.create.call_args[0][0]
        assert created_data["goal_id"] == goal_id
        assert created_data["status"] == MilestoneStatus.PENDING

    @pytest.mark.asyncio
    async def test_create_milestone_invalid_amount(self, goal_service, sample_goal):
        """Test milestone creation with invalid target amount."""
        # Arrange
        goal_id = str(uuid4())
        user_id = str(uuid4())
        milestone_data = GoalMilestoneCreate(
            name="Invalid Milestone",
            target_amount=Decimal("-100.00"),
            target_percentage=Decimal("50.00")
        )
        
        goal_service.goal_repo.get_by_id_for_user.return_value = sample_goal
        
        # Act & Assert
        with pytest.raises(ValidationError, match="Milestone target amount must be positive"):
            await goal_service.create_milestone(goal_id, user_id, milestone_data)

    @pytest.mark.asyncio
    async def test_create_milestone_exceeds_goal_target(self, goal_service, sample_goal):
        """Test milestone creation that exceeds goal target."""
        # Arrange
        goal_id = str(uuid4())
        user_id = str(uuid4())
        milestone_data = GoalMilestoneCreate(
            name="Impossible Milestone",
            target_amount=Decimal("20000.00"),  # Exceeds goal target of 15000
            target_percentage=Decimal("100.00")
        )
        
        sample_goal.target_amount = Decimal("15000.00")
        goal_service.goal_repo.get_by_id_for_user.return_value = sample_goal
        
        # Act & Assert
        with pytest.raises(ValidationError, match="Milestone target cannot exceed goal target"):
            await goal_service.create_milestone(goal_id, user_id, milestone_data)

    @pytest.mark.asyncio
    async def test_update_milestone_success(self, goal_service, sample_goal, sample_milestone):
        """Test successful milestone update."""
        # Arrange
        milestone_id = str(uuid4())
        user_id = str(uuid4())
        update_data = {"name": "Updated Milestone"}
        
        sample_milestone.goal_id = str(uuid4())
        goal_service.milestone_repo.get_by_id.return_value = sample_milestone
        goal_service.goal_repo.get_by_id_for_user.return_value = sample_goal
        goal_service.milestone_repo.update.return_value = sample_milestone
        
        # Act
        result = await goal_service.update_milestone(milestone_id, user_id, update_data)
        
        # Assert
        goal_service.milestone_repo.update.assert_called_once()
        update_call = goal_service.milestone_repo.update.call_args[0][1]
        assert "updated_at" in update_call

    @pytest.mark.asyncio
    async def test_delete_milestone_success(self, goal_service, sample_goal, sample_milestone):
        """Test successful milestone deletion."""
        # Arrange
        milestone_id = str(uuid4())
        user_id = str(uuid4())
        
        sample_milestone.goal_id = str(uuid4())
        goal_service.milestone_repo.get_by_id.return_value = sample_milestone
        goal_service.goal_repo.get_by_id_for_user.return_value = sample_goal
        goal_service.milestone_repo.delete.return_value = True
        
        # Act
        result = await goal_service.delete_milestone(milestone_id, user_id)
        
        # Assert
        assert result is True
        goal_service.milestone_repo.delete.assert_called_once_with(milestone_id)


class TestGoalServiceStatusManagement:
    """Test goal status management operations."""

    @pytest.mark.asyncio
    async def test_pause_goal_success(self, goal_service, sample_goal):
        """Test successful goal pausing."""
        # Arrange
        goal_id = str(uuid4())
        user_id = str(uuid4())
        goal_service.goal_repo.get_by_id_for_user.return_value = sample_goal
        goal_service.goal_repo.update.return_value = sample_goal
        goal_service.goal_repo.get_by_id.return_value = sample_goal
        
        # Act
        result = await goal_service.pause_goal(goal_id, user_id)
        
        # Assert
        goal_service.goal_repo.update.assert_called_once()
        update_call = goal_service.goal_repo.update.call_args[0][1]
        assert update_call["status"] == GoalStatus.PAUSED

    @pytest.mark.asyncio
    async def test_resume_goal_success(self, goal_service, sample_goal):
        """Test successful goal resuming."""
        # Arrange
        goal_id = str(uuid4())
        user_id = str(uuid4())
        goal_service.goal_repo.get_by_id_for_user.return_value = sample_goal
        goal_service.goal_repo.update.return_value = sample_goal
        goal_service.goal_repo.get_by_id.return_value = sample_goal
        
        # Act
        result = await goal_service.resume_goal(goal_id, user_id)
        
        # Assert
        goal_service.goal_repo.update.assert_called_once()
        update_call = goal_service.goal_repo.update.call_args[0][1]
        assert update_call["status"] == GoalStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_complete_goal_success(self, goal_service, sample_goal):
        """Test successful goal completion."""
        # Arrange
        goal_id = str(uuid4())
        user_id = str(uuid4())
        goal_service.goal_repo.get_by_id_for_user.return_value = sample_goal
        goal_service.goal_repo.update.return_value = sample_goal
        goal_service.goal_repo.get_by_id.return_value = sample_goal
        
        # Act
        result = await goal_service.complete_goal(goal_id, user_id)
        
        # Assert
        goal_service.goal_repo.update.assert_called_once()
        update_call = goal_service.goal_repo.update.call_args[0][1]
        assert update_call["status"] == GoalStatus.COMPLETED
        assert update_call["completed_at"] is not None


class TestGoalServiceAnalytics:
    """Test goal analytics and insights."""

    @pytest.mark.asyncio
    async def test_get_goals_summary_success(self, goal_service):
        """Test successful goals summary retrieval."""
        # Arrange
        user_id = str(uuid4())
        analytics_data = {
            "total_goals": 5,
            "active_goals": 3,
            "completed_goals": 2,
            "total_target_amount": Decimal("50000.00"),
            "total_current_amount": Decimal("25000.00"),
            "total_progress_percentage": Decimal("50.00"),
            "average_monthly_contribution": Decimal("833.33")
        }
        
        goal_service.goal_repo.get_goal_analytics.return_value = analytics_data
        goal_service.goal_repo.get_goals_due_soon.return_value = []
        
        # Act
        result = await goal_service.get_goals_summary(user_id)
        
        # Assert
        assert result.total_goals == 5
        assert result.active_goals == 3
        assert result.completed_goals == 2
        assert result.completion_rate == 40.0  # 2/5 * 100

    @pytest.mark.asyncio
    async def test_get_goal_analysis_success(self, goal_service, sample_goal):
        """Test successful goal analysis."""
        # Arrange
        goal_id = str(uuid4())
        user_id = str(uuid4())
        sample_goal.target_amount = Decimal("15000.00")
        sample_goal.current_amount = Decimal("7500.00")
        sample_goal.monthly_contribution = Decimal("500.00")
        
        goal_service.goal_repo.get_by_id_for_user.return_value = sample_goal
        goal_service.contribution_repo.get_contributions_by_date_range.return_value = [
            Mock(amount=Decimal("500.00")) for _ in range(6)  # 6 contributions
        ]
        
        # Act
        result = await goal_service.get_goal_analysis(goal_id, user_id)
        
        # Assert
        assert result.goal_id == goal_id
        assert result.current_progress == 50.0  # 7500/15000 * 100
        assert result.total_contributions_period == 3000.0  # 6 * 500
        assert result.contribution_frequency == 6
        assert result.is_on_track is True  # Monthly average equals target

    @pytest.mark.asyncio
    async def test_get_goal_insights_success(self, goal_service, sample_goal):
        """Test successful goal insights generation."""
        # Arrange
        user_id = str(uuid4())
        sample_goal.target_amount = Decimal("15000.00")
        sample_goal.current_amount = Decimal("3750.00")  # 25% progress
        sample_goal.target_date = date.today() + timedelta(days=20)  # Due soon
        
        goal_service.goal_repo.get_active_goals_for_user.return_value = [sample_goal]
        
        # Act
        result = await goal_service.get_goal_insights(user_id)
        
        # Assert
        assert len(result) == 1
        insight = result[0]
        assert insight.goal_id == sample_goal.id
        assert insight.insight_type == "warning"  # Low progress with approaching deadline
        assert "deadline" in insight.title.lower()
        assert insight.action_required is True


class TestGoalServiceTemplates:
    """Test goal template functionality."""

    @pytest.mark.asyncio
    async def test_get_goal_templates_success(self, goal_service):
        """Test successful template retrieval."""
        # Arrange
        user_id = str(uuid4())
        template_mock = Mock(
            id=str(uuid4()),
            name="Emergency Fund Template",
            description="Standard emergency fund",
            goal_type=GoalType.EMERGENCY_FUND,
            default_target_amount=Decimal("10000.00"),
            default_monthly_contribution=Decimal("500.00"),
            use_count=15
        )
        goal_service.template_repo.get_public_templates.return_value = [template_mock]
        
        # Act
        result = await goal_service.get_goal_templates(user_id)
        
        # Assert
        assert len(result) == 1
        template = result[0]
        assert template["name"] == "Emergency Fund Template"
        assert template["default_target_amount"] == 10000.0
        assert template["use_count"] == 15

    @pytest.mark.asyncio
    async def test_apply_goal_template_success(self, goal_service):
        """Test successful template application."""
        # Arrange
        template_id = str(uuid4())
        user_id = str(uuid4())
        template_data = {
            "name": "My Emergency Fund",
            "target_amount": "15000.00",
            "monthly_contribution": "600.00",
            "initial_contribution": "1000.00"
        }
        
        template_mock = Mock(
            id=template_id,
            name="Emergency Fund Template",
            description="Standard emergency fund",
            goal_type=GoalType.EMERGENCY_FUND,
            default_target_amount=Decimal("10000.00"),
            default_monthly_contribution=Decimal("500.00")
        )
        
        goal_service.template_repo.get_by_id.return_value = template_mock
        goal_service.create_goal = AsyncMock(return_value=Mock(id=str(uuid4())))
        goal_service.template_repo.increment_use_count = AsyncMock()
        
        # Act
        result = await goal_service.apply_goal_template(template_id, user_id, template_data)
        
        # Assert
        goal_service.create_goal.assert_called_once()
        goal_data = goal_service.create_goal.call_args[0][1]
        assert goal_data.name == "My Emergency Fund"
        assert goal_data.target_amount == Decimal("15000.00")
        assert goal_data.initial_contribution == Decimal("1000.00")
        
        goal_service.template_repo.increment_use_count.assert_called_once_with(template_id)


class TestGoalServiceUtilities:
    """Test utility and helper functions."""

    @pytest.mark.asyncio
    async def test_get_service_health_success(self, goal_service):
        """Test service health check success."""
        # Arrange
        goal_service.goal_repo.get_multi.return_value = [Mock()]
        
        # Act
        result = await goal_service.get_service_health()
        
        # Assert
        assert result["database_connected"] is True
        assert result["repositories_count"] == 5
        assert "last_check" in result

    @pytest.mark.asyncio
    async def test_get_service_health_failure(self, goal_service):
        """Test service health check failure."""
        # Arrange
        goal_service.goal_repo.get_multi.side_effect = Exception("Database down")
        
        # Act
        result = await goal_service.get_service_health()
        
        # Assert
        assert result["database_connected"] is False
        assert "Database down" in result["error"]

    @pytest.mark.asyncio
    async def test_recalculate_goal_progress_success(self, goal_service, sample_goal):
        """Test successful goal progress recalculation."""
        # Arrange
        goal_id = str(uuid4())
        user_id = str(uuid4())
        
        sample_goal.target_amount = Decimal("15000.00")
        sample_goal.status = GoalStatus.ACTIVE
        sample_goal.completed_at = None
        
        goal_service.goal_repo.get_by_id_for_user.return_value = sample_goal
        goal_service.contribution_repo.get_total_contributions_for_goal.return_value = Decimal("16000.00")  # Over target
        goal_service._check_and_complete_milestones = AsyncMock()
        goal_service.goal_repo.update.return_value = sample_goal
        goal_service.goal_repo.get_by_id.return_value = sample_goal
        
        # Act
        result = await goal_service.recalculate_goal_progress(goal_id, user_id)
        
        # Assert
        goal_service.goal_repo.update.assert_called_once()
        update_call = goal_service.goal_repo.update.call_args[0][1]
        assert update_call["current_amount"] == Decimal("16000.00")
        assert update_call["remaining_amount"] == Decimal("0")  # Capped at 0
        assert update_call["status"] == GoalStatus.COMPLETED
        assert update_call["completed_at"] is not None

    @pytest.mark.asyncio
    async def test_check_and_complete_milestones(self, goal_service, sample_milestone):
        """Test milestone auto-completion logic."""
        # Arrange
        goal_id = str(uuid4())
        current_amount = Decimal("5000.00")
        
        sample_milestone.target_amount = Decimal("3750.00")  # Should be completed
        sample_milestone.is_automatic = True
        sample_milestone.status = MilestoneStatus.PENDING
        
        goal_service.milestone_repo.get_milestones_for_goal.return_value = [sample_milestone]
        goal_service.milestone_repo.complete_milestone = AsyncMock()
        
        # Act
        await goal_service._check_and_complete_milestones(goal_id, current_amount)
        
        # Assert
        goal_service.milestone_repo.complete_milestone.assert_called_once_with(
            sample_milestone.id, current_amount
        )

    @pytest.mark.asyncio
    async def test_get_goal_category_suggestions_success(self, goal_service):
        """Test goal category suggestions."""
        # Arrange
        user_id = str(uuid4())
        
        # Act
        result = await goal_service.get_goal_category_suggestions(user_id)
        
        # Assert
        assert isinstance(result, list)
        assert len(result) > 0
        assert "Emergency Fund" in result
        assert "Vacation" in result
        assert "Home Down Payment" in result


class TestGoalServiceAutoSave:
    """Test auto-save functionality."""

    @pytest.mark.asyncio
    async def test_enable_auto_save_success(self, goal_service, sample_goal):
        """Test successful auto-save enablement."""
        # Arrange
        goal_id = str(uuid4())
        user_id = str(uuid4())
        config = {
            "amount": 250.00,
            "frequency": "weekly",
            "start_date": "2024-02-01"
        }
        
        goal_service.goal_repo.get_by_id_for_user.return_value = sample_goal
        goal_service.goal_repo.update.return_value = True
        
        # Act
        result = await goal_service.enable_auto_save(goal_id, user_id, config)
        
        # Assert
        assert result["message"] == "Auto-save enabled successfully"
        assert result["settings"]["enabled"] is True
        assert result["settings"]["amount"] == 250.00
        assert result["settings"]["frequency"] == "weekly"

    @pytest.mark.asyncio
    async def test_enable_auto_save_invalid_config(self, goal_service, sample_goal):
        """Test auto-save enablement with invalid configuration."""
        # Arrange
        goal_id = str(uuid4())
        user_id = str(uuid4())
        config = {"amount": -100.00}  # Invalid amount
        
        goal_service.goal_repo.get_by_id_for_user.return_value = sample_goal
        
        # Act & Assert
        with pytest.raises(ValidationError, match="Auto-save amount must be positive"):
            await goal_service.enable_auto_save(goal_id, user_id, config)

    @pytest.mark.asyncio
    async def test_disable_auto_save_success(self, goal_service, sample_goal):
        """Test successful auto-save disabling."""
        # Arrange
        goal_id = str(uuid4())
        user_id = str(uuid4())
        
        goal_service.goal_repo.get_by_id_for_user.return_value = sample_goal
        goal_service.goal_repo.update.return_value = True
        
        # Act
        result = await goal_service.disable_auto_save(goal_id, user_id)
        
        # Assert
        assert result["message"] == "Auto-save disabled successfully"
        goal_service.goal_repo.update.assert_called_once()
        update_call = goal_service.goal_repo.update.call_args[0][1]
        assert update_call["auto_save_settings"]["enabled"] is False
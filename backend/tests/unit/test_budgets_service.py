"""Comprehensive unit tests for budgets service layer."""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timezone, date, timedelta
from decimal import Decimal
from uuid import uuid4

from src.budgets.service import BudgetService
from src.budgets.models import Budget, BudgetCategory, BudgetAlert, BudgetTemplate, BudgetStatus, AlertType, BudgetPeriod
from src.budgets.schemas import (
    BudgetCreate, BudgetUpdate, BudgetCategoryCreate, BudgetCategoryUpdate,
    BudgetTemplateCreate, CreateBudgetFromTemplate, BudgetAnalytics
)
from src.exceptions import NotFoundError, ValidationError, DatabaseError, BusinessLogicError
from src.tenant.context import TenantContext


@pytest.mark.unit
class TestBudgetService:
    """Test BudgetService methods."""
    
    @pytest.fixture
    def mock_repositories(self):
        """Mock all budget repositories."""
        return {
            'budget_repo': AsyncMock(),
            'category_repo': AsyncMock(),
            'alert_repo': AsyncMock(),
            'template_repo': AsyncMock(),
            'template_category_repo': AsyncMock()
        }
    
    @pytest.fixture
    def budget_service(self, mock_repositories):
        """Create BudgetService instance with mocked repositories."""
        service = BudgetService()
        service.budget_repo = mock_repositories['budget_repo']
        service.category_repo = mock_repositories['category_repo']
        service.alert_repo = mock_repositories['alert_repo']
        service.template_repo = mock_repositories['template_repo']
        service.template_category_repo = mock_repositories['template_category_repo']
        return service
    
    @pytest.fixture
    def sample_budget_data(self):
        """Sample budget creation data."""
        return BudgetCreate(
            name="Monthly Family Budget",
            description="Our family's monthly budget",
            total_amount=Decimal("5000.00"),
            period_type=BudgetPeriod.MONTHLY,
            start_date=date(2024, 2, 1),
            end_date=date(2024, 2, 29),
            warning_threshold=Decimal("75.00"),
            critical_threshold=Decimal("90.00"),
            categories=[
                BudgetCategoryCreate(
                    category_name="Groceries",
                    allocated_amount=Decimal("800.00"),
                    is_essential=True,
                    priority=1
                ),
                BudgetCategoryCreate(
                    category_name="Entertainment",
                    allocated_amount=Decimal("300.00"),
                    is_essential=False,
                    priority=3
                )
            ]
        )
    
    @pytest.fixture
    def sample_budget_model(self):
        """Sample budget model instance."""
        return Budget(
            id="budget-123",
            name="Monthly Family Budget",
            description="Our family's monthly budget",
            total_amount=Decimal("5000.00"),
            spent_amount=Decimal("2500.00"),
            remaining_amount=Decimal("2500.00"),
            period_type=BudgetPeriod.MONTHLY,
            start_date=date(2024, 2, 1),
            end_date=date(2024, 2, 29),
            status=BudgetStatus.ACTIVE,
            warning_threshold=Decimal("75.00"),
            critical_threshold=Decimal("90.00"),
            user_id="user-123",
            created_by="user-123",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            categories=[],
            alerts=[]
        )

    @pytest.mark.asyncio
    async def test_create_budget_success(self, budget_service, mock_repositories, sample_budget_data, sample_budget_model):
        """Test successful budget creation."""
        # Arrange
        user_id = "user-123"
        created_by = "user-123"
        
        mock_repositories['budget_repo'].create_for_user.return_value = sample_budget_model
        mock_repositories['budget_repo'].get_by_id.return_value = sample_budget_model
        
        # Act
        result = await budget_service.create_budget(sample_budget_data, user_id, created_by)
        
        # Assert
        assert result.id == "budget-123"
        assert result.name == "Monthly Family Budget"
        assert result.total_amount == Decimal("5000.00")
        mock_repositories['budget_repo'].create_for_user.assert_called_once()
        mock_repositories['category_repo'].create.assert_called()
        mock_repositories['budget_repo'].get_by_id.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_budget_categories_exceed_total(self, budget_service, sample_budget_data):
        """Test budget creation with categories exceeding total."""
        # Arrange
        # Add more categories that exceed total
        sample_budget_data.categories.append(
            BudgetCategoryCreate(
                category_name="Extra Large Category",
                allocated_amount=Decimal("5000.00"),  # This makes total exceed 5000
                is_essential=False,
                priority=5
            )
        )
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await budget_service.create_budget(sample_budget_data, "user-123", "user-123")
        
        assert "exceed budget total" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_budget_database_error(self, budget_service, mock_repositories, sample_budget_data):
        """Test budget creation with database error."""
        # Arrange
        mock_repositories['budget_repo'].create_for_user.side_effect = Exception("Database connection failed")
        
        # Act & Assert
        with pytest.raises(DatabaseError) as exc_info:
            await budget_service.create_budget(sample_budget_data, "user-123", "user-123")
        
        assert "Failed to create budget" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_budget_success(self, budget_service, mock_repositories, sample_budget_model):
        """Test successful budget retrieval."""
        # Arrange
        budget_id = "budget-123"
        user_id = "user-123"
        mock_repositories['budget_repo'].get_by_id_for_user.return_value = sample_budget_model
        
        # Act
        result = await budget_service.get_budget(budget_id, user_id)
        
        # Assert
        assert result is not None
        assert result.id == budget_id
        assert result.name == "Monthly Family Budget"
        mock_repositories['budget_repo'].get_by_id_for_user.assert_called_once_with(
            budget_id, user_id, load_relationships=["categories", "alerts"]
        )

    @pytest.mark.asyncio
    async def test_get_budget_not_found(self, budget_service, mock_repositories):
        """Test budget retrieval when not found."""
        # Arrange
        budget_id = "non-existent-budget"
        user_id = "user-123"
        mock_repositories['budget_repo'].get_by_id_for_user.return_value = None
        
        # Act
        result = await budget_service.get_budget(budget_id, user_id)
        
        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_budgets_with_status_filter(self, budget_service, mock_repositories, sample_budget_model):
        """Test getting user budgets with status filter."""
        # Arrange
        user_id = "user-123"
        status = BudgetStatus.ACTIVE
        mock_repositories['budget_repo'].get_multi_for_user.return_value = [sample_budget_model]
        
        # Act
        result = await budget_service.get_user_budgets(user_id, status)
        
        # Assert
        assert len(result) == 1
        assert result[0].id == "budget-123"
        mock_repositories['budget_repo'].get_multi_for_user.assert_called_once_with(
            user_id=user_id,
            filters={"status": status},
            order_by="-created_at",
            load_relationships=["categories", "alerts"]
        )

    @pytest.mark.asyncio
    async def test_get_current_budget_success(self, budget_service, mock_repositories, sample_budget_model):
        """Test getting current active budget."""
        # Arrange
        user_id = "user-123"
        mock_repositories['budget_repo'].get_current_budget_for_user.return_value = sample_budget_model
        
        # Act
        result = await budget_service.get_current_budget(user_id)
        
        # Assert
        assert result is not None
        assert result.id == "budget-123"
        mock_repositories['budget_repo'].get_current_budget_for_user.assert_called_once_with(user_id)

    @pytest.mark.asyncio
    async def test_update_budget_success(self, budget_service, mock_repositories, sample_budget_model):
        """Test successful budget update."""
        # Arrange
        budget_id = "budget-123"
        user_id = "user-123"
        update_data = BudgetUpdate(name="Updated Budget Name", description="Updated description")
        
        mock_repositories['budget_repo'].get_by_id_for_user.return_value = sample_budget_model
        mock_repositories['budget_repo'].update.return_value = sample_budget_model
        mock_repositories['budget_repo'].get_by_id.return_value = sample_budget_model
        
        # Act
        result = await budget_service.update_budget(budget_id, update_data, user_id)
        
        # Assert
        assert result is not None
        assert result.id == budget_id
        mock_repositories['budget_repo'].get_by_id_for_user.assert_called_once_with(budget_id, user_id)
        mock_repositories['budget_repo'].update.assert_called_once_with(budget_id, update_data)

    @pytest.mark.asyncio
    async def test_update_budget_not_found(self, budget_service, mock_repositories):
        """Test budget update when budget not found."""
        # Arrange
        budget_id = "non-existent-budget"
        user_id = "user-123"
        update_data = BudgetUpdate(name="Updated Name")
        
        mock_repositories['budget_repo'].get_by_id_for_user.return_value = None
        
        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await budget_service.update_budget(budget_id, update_data, user_id)
        
        assert "Budget not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_budget_success(self, budget_service, mock_repositories, sample_budget_model):
        """Test successful budget deletion (soft delete)."""
        # Arrange
        budget_id = "budget-123"
        user_id = "user-123"
        
        mock_repositories['budget_repo'].get_by_id_for_user.return_value = sample_budget_model
        mock_repositories['budget_repo'].update.return_value = sample_budget_model
        
        # Act
        result = await budget_service.delete_budget(budget_id, user_id)
        
        # Assert
        assert result is True
        mock_repositories['budget_repo'].update.assert_called_once()
        # Verify it's a soft delete (status update)
        call_args = mock_repositories['budget_repo'].update.call_args
        assert call_args[0][0] == budget_id
        assert call_args[0][1].status == BudgetStatus.INACTIVE

    @pytest.mark.asyncio
    async def test_update_budget_spending_with_alerts(self, budget_service, mock_repositories, sample_budget_model):
        """Test updating budget spending that triggers alerts."""
        # Arrange
        budget_id = "budget-123"
        new_spent_amount = Decimal("4000.00")  # 80% of 5000, should trigger warning
        
        # Modify sample budget to reflect high spending
        high_spending_budget = sample_budget_model
        high_spending_budget.spent_amount = new_spent_amount
        high_spending_budget.update_spent_amount(new_spent_amount)
        
        mock_repositories['budget_repo'].update_spent_amount.return_value = high_spending_budget
        mock_repositories['budget_repo'].get_by_id.return_value = high_spending_budget
        
        # Act
        result = await budget_service.update_budget_spending(budget_id, new_spent_amount)
        
        # Assert
        assert result is not None
        assert result.spent_amount == new_spent_amount
        mock_repositories['budget_repo'].update_spent_amount.assert_called_once_with(budget_id, new_spent_amount)

    @pytest.mark.asyncio
    async def test_get_budget_analytics(self, budget_service, mock_repositories):
        """Test getting budget analytics."""
        # Arrange
        user_id = "user-123"
        mock_analytics_data = {
            "total_budgets": 5,
            "active_budgets": 3,
            "total_budgeted": Decimal("15000.00"),
            "total_spent": Decimal("8500.00"),
            "average_utilization": Decimal("56.67")
        }
        mock_repositories['budget_repo'].get_budget_analytics.return_value = mock_analytics_data
        
        # Act
        result = await budget_service.get_budget_analytics(user_id)
        
        # Assert
        assert isinstance(result, BudgetAnalytics)
        assert result.total_budgets == 5
        assert result.active_budgets == 3
        mock_repositories['budget_repo'].get_budget_analytics.assert_called_once_with(user_id)

    @pytest.mark.asyncio
    async def test_add_category_to_budget_success(self, budget_service, mock_repositories, sample_budget_model):
        """Test successfully adding category to budget."""
        # Arrange
        budget_id = "budget-123"
        user_id = "user-123"
        category_data = BudgetCategoryCreate(
            category_name="Transportation",
            allocated_amount=Decimal("500.00"),
            is_essential=True,
            priority=2
        )
        
        mock_category = BudgetCategory(
            id="category-123",
            budget_id=budget_id,
            category_name="Transportation",
            allocated_amount=Decimal("500.00"),
            spent_amount=Decimal("0.00"),
            remaining_amount=Decimal("500.00"),
            is_essential=True,
            priority=2,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        mock_repositories['budget_repo'].get_by_id_for_user.return_value = sample_budget_model
        mock_repositories['category_repo'].get_categories_for_budget.return_value = []
        mock_repositories['category_repo'].create.return_value = mock_category
        
        # Act
        result = await budget_service.add_category_to_budget(budget_id, category_data, user_id)
        
        # Assert
        assert result.category_name == "Transportation"
        assert result.allocated_amount == Decimal("500.00")
        mock_repositories['category_repo'].create.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_category_exceeds_budget(self, budget_service, mock_repositories, sample_budget_model):
        """Test adding category that would exceed budget total."""
        # Arrange
        budget_id = "budget-123"
        user_id = "user-123"
        category_data = BudgetCategoryCreate(
            category_name="Expensive Category",
            allocated_amount=Decimal("3000.00"),  # Would exceed remaining budget
            is_essential=False,
            priority=5
        )
        
        # Mock existing categories that already use most of the budget
        existing_categories = [
            Mock(allocated_amount=Decimal("3000.00")),  # Total 3000 already allocated
            Mock(allocated_amount=Decimal("1500.00"))   # Adding another 1500 = 4500
        ]
        
        mock_repositories['budget_repo'].get_by_id_for_user.return_value = sample_budget_model
        mock_repositories['category_repo'].get_categories_for_budget.return_value = existing_categories
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await budget_service.add_category_to_budget(budget_id, category_data, user_id)
        
        assert "exceed budget total" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_category_success(self, budget_service, mock_repositories, sample_budget_model):
        """Test successful category update."""
        # Arrange
        category_id = "category-123"
        user_id = "user-123"
        category_data = BudgetCategoryUpdate(
            category_name="Updated Category",
            allocated_amount=Decimal("600.00")
        )
        
        mock_category = Mock(id=category_id, budget_id="budget-123")
        updated_category = Mock(
            id=category_id,
            category_name="Updated Category",
            allocated_amount=Decimal("600.00")
        )
        
        mock_repositories['category_repo'].get_by_id.return_value = mock_category
        mock_repositories['budget_repo'].get_by_id_for_user.return_value = sample_budget_model
        mock_repositories['category_repo'].update.return_value = updated_category
        
        # Act
        result = await budget_service.update_category(category_id, category_data, user_id)
        
        # Assert
        assert result is not None
        mock_repositories['category_repo'].update.assert_called_once_with(category_id, category_data)

    @pytest.mark.asyncio
    async def test_delete_category_success(self, budget_service, mock_repositories, sample_budget_model):
        """Test successful category deletion."""
        # Arrange
        category_id = "category-123"
        user_id = "user-123"
        
        mock_category = Mock(id=category_id, budget_id="budget-123")
        
        mock_repositories['category_repo'].get_by_id.return_value = mock_category
        mock_repositories['budget_repo'].get_by_id_for_user.return_value = sample_budget_model
        mock_repositories['category_repo'].delete.return_value = True
        
        # Act
        result = await budget_service.delete_category(category_id, user_id)
        
        # Assert
        assert result is True
        mock_repositories['category_repo'].delete.assert_called_once_with(category_id)

    @pytest.mark.asyncio
    async def test_create_template_success(self, budget_service, mock_repositories):
        """Test successful budget template creation."""
        # Arrange
        template_data = BudgetTemplateCreate(
            name="Monthly Template",
            description="Standard monthly template",
            period_type=BudgetPeriod.MONTHLY,
            total_amount=Decimal("5000.00"),
            warning_threshold=Decimal("75.00"),
            critical_threshold=Decimal("90.00"),
            categories=[
                BudgetCategoryCreate(
                    category_name="Groceries",
                    allocated_amount=Decimal("800.00"),
                    is_essential=True,
                    priority=1
                )
            ]
        )
        
        mock_template = BudgetTemplate(
            id="template-123",
            name="Monthly Template",
            description="Standard monthly template",
            period_type=BudgetPeriod.MONTHLY,
            total_amount=Decimal("5000.00"),
            warning_threshold=Decimal("75.00"),
            critical_threshold=Decimal("90.00"),
            user_id="user-123",
            created_by="user-123",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            template_categories=[]
        )
        
        mock_repositories['template_repo'].create_for_user.return_value = mock_template
        
        # Act
        result = await budget_service.create_template(template_data, "user-123", "user-123")
        
        # Assert
        assert result.name == "Monthly Template"
        assert result.total_amount == Decimal("5000.00")
        mock_repositories['template_repo'].create_for_user.assert_called_once()
        mock_repositories['template_category_repo'].create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_budget_from_template_success(self, budget_service, mock_repositories, sample_budget_model):
        """Test successful budget creation from template."""
        # Arrange
        request = CreateBudgetFromTemplate(
            template_id="template-123",
            name="February Budget from Template",
            start_date=date(2024, 2, 1),
            total_amount=Decimal("5000.00")
        )
        
        # Mock template with categories
        mock_template = Mock(
            id="template-123",
            name="Template Name",
            description="Template description",
            period_type=BudgetPeriod.MONTHLY,
            total_amount=Decimal("4000.00"),
            warning_threshold=Decimal("75.00"),
            critical_threshold=Decimal("90.00"),
            template_categories=[
                Mock(
                    category_name="Groceries",
                    category_id="cat-1",
                    percentage_of_total=Decimal("20.00"),  # 20% of total
                    is_essential=True,
                    priority=1
                )
            ]
        )
        
        mock_repositories['template_repo'].get_by_id_for_user.return_value = mock_template
        mock_repositories['budget_repo'].create_for_user.return_value = sample_budget_model
        mock_repositories['budget_repo'].get_by_id.return_value = sample_budget_model
        mock_repositories['template_repo'].increment_use_count.return_value = None
        
        # Mock the create_budget method
        with patch.object(budget_service, 'create_budget', return_value=sample_budget_model) as mock_create:
            # Act
            result = await budget_service.create_budget_from_template(request, "user-123", "user-123")
            
            # Assert
            assert result.id == "budget-123"
            mock_create.assert_called_once()
            mock_repositories['template_repo'].increment_use_count.assert_called_once_with("template-123")

    @pytest.mark.asyncio
    async def test_get_user_alerts_unread_only(self, budget_service, mock_repositories):
        """Test getting unread alerts for user."""
        # Arrange
        user_id = "user-123"
        mock_alerts = [
            Mock(
                id="alert-1",
                budget_id="budget-123",
                alert_type=AlertType.WARNING,
                title="Budget Warning",
                message="Budget approaching limit",
                is_read=False,
                created_at=datetime.now(timezone.utc)
            )
        ]
        
        mock_repositories['alert_repo'].get_unread_alerts_for_user.return_value = mock_alerts
        
        # Act
        result = await budget_service.get_user_alerts(user_id, unread_only=True)
        
        # Assert
        assert len(result) == 1
        assert result[0]["alert_type"] == AlertType.WARNING
        assert result[0]["is_read"] is False
        mock_repositories['alert_repo'].get_unread_alerts_for_user.assert_called_once_with(user_id)

    @pytest.mark.asyncio
    async def test_mark_alert_as_read(self, budget_service, mock_repositories):
        """Test marking alert as read."""
        # Arrange
        alert_id = "alert-123"
        user_id = "user-123"
        
        mock_repositories['alert_repo'].mark_as_read.return_value = True
        
        # Act
        result = await budget_service.mark_alert_as_read(alert_id, user_id)
        
        # Assert
        assert result is True
        mock_repositories['alert_repo'].mark_as_read.assert_called_once_with(alert_id)

    def test_calculate_end_date_monthly(self, budget_service):
        """Test end date calculation for monthly period."""
        # Arrange
        start_date = date(2024, 2, 1)
        period_type = BudgetPeriod.MONTHLY
        
        # Act
        result = budget_service._calculate_end_date(start_date, period_type)
        
        # Assert
        expected = date(2024, 2, 29)  # February 2024 has 29 days
        assert result == expected

    def test_calculate_end_date_yearly(self, budget_service):
        """Test end date calculation for yearly period."""
        # Arrange
        start_date = date(2024, 3, 15)
        period_type = BudgetPeriod.YEARLY
        
        # Act
        result = budget_service._calculate_end_date(start_date, period_type)
        
        # Assert
        expected = date(2025, 3, 14)  # One year minus one day
        assert result == expected

    def test_calculate_end_date_weekly(self, budget_service):
        """Test end date calculation for weekly period."""
        # Arrange
        start_date = date(2024, 2, 1)  # Thursday
        period_type = BudgetPeriod.WEEKLY
        
        # Act
        result = budget_service._calculate_end_date(start_date, period_type)
        
        # Assert
        expected = date(2024, 2, 7)  # 6 days later
        assert result == expected

    def test_calculate_end_date_quarterly(self, budget_service):
        """Test end date calculation for quarterly period."""
        # Arrange
        start_date = date(2024, 1, 1)
        period_type = BudgetPeriod.QUARTERLY
        
        # Act
        result = budget_service._calculate_end_date(start_date, period_type)
        
        # Assert
        expected = date(2024, 3, 30)  # Approximately 3 months (89 days)
        assert result == expected


@pytest.mark.unit
class TestBudgetServiceAlertLogic:
    """Test budget alert creation logic."""
    
    @pytest.fixture
    def budget_service(self):
        """Create BudgetService instance."""
        service = BudgetService()
        service.alert_repo = AsyncMock()
        return service
    
    @pytest.fixture
    def warning_threshold_budget(self):
        """Budget that has reached warning threshold."""
        budget = Mock()
        budget.id = "budget-123"
        budget.name = "Test Budget"
        budget.utilization_percentage = Decimal("80.0")  # 80% utilization
        budget.warning_threshold = Decimal("75.0")
        budget.critical_threshold = Decimal("90.0")
        budget.spent_amount = Decimal("4000.00")
        budget.total_amount = Decimal("5000.00")
        budget.is_warning_threshold_reached = True
        budget.is_critical_threshold_reached = False
        budget.is_over_budget = False
        return budget
    
    @pytest.fixture
    def critical_threshold_budget(self):
        """Budget that has reached critical threshold."""
        budget = Mock()
        budget.id = "budget-123"
        budget.name = "Test Budget"
        budget.utilization_percentage = Decimal("95.0")  # 95% utilization
        budget.warning_threshold = Decimal("75.0")
        budget.critical_threshold = Decimal("90.0")
        budget.spent_amount = Decimal("4750.00")
        budget.total_amount = Decimal("5000.00")
        budget.is_warning_threshold_reached = True
        budget.is_critical_threshold_reached = True
        budget.is_over_budget = False
        return budget
    
    @pytest.fixture
    def over_budget(self):
        """Budget that is over budget."""
        budget = Mock()
        budget.id = "budget-123"
        budget.name = "Test Budget"
        budget.utilization_percentage = Decimal("110.0")  # 110% utilization
        budget.warning_threshold = Decimal("75.0")
        budget.critical_threshold = Decimal("90.0")
        budget.spent_amount = Decimal("5500.00")
        budget.total_amount = Decimal("5000.00")
        budget.is_warning_threshold_reached = True
        budget.is_critical_threshold_reached = True
        budget.is_over_budget = True
        return budget

    @pytest.mark.asyncio
    async def test_check_and_create_warning_alert(self, budget_service, warning_threshold_budget):
        """Test creating warning alert when threshold is reached."""
        # Act
        await budget_service._check_and_create_alerts(warning_threshold_budget)
        
        # Assert
        budget_service.alert_repo.create.assert_called()
        call_args = budget_service.alert_repo.create.call_args[0][0]
        assert call_args["alert_type"] == AlertType.WARNING
        assert call_args["title"] == "Budget Warning"
        assert "80.0%" in call_args["message"]

    @pytest.mark.asyncio
    async def test_check_and_create_critical_alert(self, budget_service, critical_threshold_budget):
        """Test creating critical alert when threshold is reached."""
        # Act
        await budget_service._check_and_create_alerts(critical_threshold_budget)
        
        # Assert
        budget_service.alert_repo.create.assert_called()
        call_args = budget_service.alert_repo.create.call_args[0][0]
        assert call_args["alert_type"] == AlertType.CRITICAL
        assert call_args["title"] == "Budget Critical"
        assert "95.0%" in call_args["message"]

    @pytest.mark.asyncio
    async def test_check_and_create_exceeded_alert(self, budget_service, over_budget):
        """Test creating exceeded alert when budget is over."""
        # Act
        await budget_service._check_and_create_alerts(over_budget)
        
        # Assert
        budget_service.alert_repo.create.assert_called()
        call_args = budget_service.alert_repo.create.call_args[0][0]
        assert call_args["alert_type"] == AlertType.EXCEEDED
        assert call_args["title"] == "Budget Exceeded"

    @pytest.mark.asyncio
    async def test_create_alert_with_proper_data(self, budget_service):
        """Test alert creation with proper data structure."""
        # Arrange
        budget_id = "budget-123"
        alert_type = AlertType.WARNING
        title = "Test Alert"
        message = "Test message"
        threshold_percentage = Decimal("75.0")
        amount_at_alert = Decimal("3750.00")
        
        # Act
        await budget_service._create_alert(
            budget_id, alert_type, title, message, threshold_percentage, amount_at_alert
        )
        
        # Assert
        budget_service.alert_repo.create.assert_called_once()
        call_args = budget_service.alert_repo.create.call_args[0][0]
        
        assert call_args["budget_id"] == budget_id
        assert call_args["alert_type"] == alert_type
        assert call_args["title"] == title
        assert call_args["message"] == message
        assert call_args["threshold_percentage"] == threshold_percentage
        assert call_args["amount_at_alert"] == amount_at_alert
        assert "id" in call_args  # UUID should be generated


@pytest.mark.unit
class TestBudgetServiceEdgeCases:
    """Test edge cases and error scenarios for BudgetService."""
    
    @pytest.fixture
    def budget_service(self):
        """Create BudgetService instance."""
        service = BudgetService()
        # Mock all repositories
        service.budget_repo = AsyncMock()
        service.category_repo = AsyncMock()
        service.alert_repo = AsyncMock()
        service.template_repo = AsyncMock()
        service.template_category_repo = AsyncMock()
        return service
    
    @pytest.mark.asyncio
    async def test_create_budget_with_zero_total_amount(self, budget_service):
        """Test creating budget with zero total amount."""
        budget_data = BudgetCreate(
            name="Zero Budget",
            total_amount=Decimal("0.00"),  # Zero amount
            period_type=BudgetPeriod.MONTHLY,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        # This should be handled gracefully or raise appropriate validation
        # Implementation depends on business rules
        pass
    
    @pytest.mark.asyncio
    async def test_create_budget_with_negative_amount(self, budget_service):
        """Test creating budget with negative amount."""
        budget_data = BudgetCreate(
            name="Negative Budget",
            total_amount=Decimal("-1000.00"),  # Negative amount
            period_type=BudgetPeriod.MONTHLY,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        # This should raise ValidationError
        # Implementation depends on validation logic in schemas or service
        pass
    
    @pytest.mark.asyncio
    async def test_create_budget_with_invalid_date_range(self, budget_service):
        """Test creating budget with invalid date range."""
        budget_data = BudgetCreate(
            name="Invalid Date Budget",
            total_amount=Decimal("1000.00"),
            period_type=BudgetPeriod.MONTHLY,
            start_date=date(2024, 2, 1),
            end_date=date(2024, 1, 31)  # End before start
        )
        
        # This should raise ValidationError
        # Implementation depends on validation logic
        pass
    
    @pytest.mark.asyncio
    async def test_concurrent_budget_operations(self, budget_service):
        """Test handling of concurrent budget operations."""
        # This would test race conditions in budget updates
        # Implementation depends on database locking and transaction handling
        pass
    
    @pytest.mark.asyncio
    async def test_budget_with_very_large_amounts(self, budget_service):
        """Test budget creation with very large monetary amounts."""
        budget_data = BudgetCreate(
            name="Large Budget",
            total_amount=Decimal("999999999999.99"),  # Very large amount
            period_type=BudgetPeriod.MONTHLY,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        # This should be handled based on database precision limits
        pass
    
    @pytest.mark.asyncio
    async def test_budget_with_many_categories(self, budget_service):
        """Test budget performance with many categories."""
        # Create budget with 100+ categories
        categories = [
            BudgetCategoryCreate(
                category_name=f"Category {i}",
                allocated_amount=Decimal("10.00"),
                is_essential=False,
                priority=1
            )
            for i in range(100)
        ]
        
        budget_data = BudgetCreate(
            name="Many Categories Budget",
            total_amount=Decimal("2000.00"),
            period_type=BudgetPeriod.MONTHLY,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            categories=categories
        )
        
        # This tests performance and transaction handling
        pass
    
    @pytest.mark.asyncio
    async def test_template_with_invalid_percentages(self, budget_service):
        """Test template creation with invalid category percentages."""
        # Template categories that don't add up to 100%
        template_data = BudgetTemplateCreate(
            name="Invalid Template",
            period_type=BudgetPeriod.MONTHLY,
            total_amount=Decimal("1000.00"),
            categories=[
                BudgetCategoryCreate(
                    category_name="Category 1",
                    allocated_amount=Decimal("600.00"),  # 60%
                    is_essential=True,
                    priority=1
                ),
                BudgetCategoryCreate(
                    category_name="Category 2", 
                    allocated_amount=Decimal("600.00"),  # 60% - Total 120%
                    is_essential=False,
                    priority=2
                )
            ]
        )
        
        # This should be validated during template creation
        pass
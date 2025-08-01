"""Comprehensive unit tests for tithing service."""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import uuid4

from src.tithing.service import TithingService
from src.tithing.models import TithingPayment, TithingSchedule, TithingSummary, TithingGoal
from src.tithing.schemas import (
    TithingPaymentCreate, 
    TithingPaymentUpdate,
    TithingScheduleCreate,
    TithingGoalCreate,
    TithingFrequency
)
from src.exceptions import NotFoundError, ValidationError, BusinessLogicError


@pytest.fixture
def mock_session():
    """Mock database session."""
    return AsyncMock()


@pytest.fixture
def tithing_service(mock_session):
    """Create tithing service with mocked repositories."""
    service = TithingService(mock_session)
    service.payment_repo = AsyncMock()
    service.schedule_repo = AsyncMock()
    service.summary_repo = AsyncMock()
    service.goal_repo = AsyncMock()
    return service


@pytest.fixture
def sample_user_id():
    """Sample user ID."""
    return str(uuid4())


@pytest.fixture
def sample_payment_data():
    """Sample tithing payment data."""
    return TithingPaymentCreate(
        amount=Decimal("150.00"),
        date=date.today(),
        method="online",
        recipient="First Baptist Church",
        recipient_address="123 Church St, City, State 12345",
        reference_number="TXN-123456",
        notes="Monthly tithe payment",
        purpose="regular_tithe",
        is_tax_deductible=True
    )


@pytest.fixture
def sample_payment():
    """Sample tithing payment model."""
    return TithingPayment(
        id=str(uuid4()),
        user_id=str(uuid4()),
        amount=Decimal("150.00"),
        date=date.today(),
        method="online",
        recipient="First Baptist Church",
        recipient_address="123 Church St, City, State 12345",
        reference_number="TXN-123456",
        notes="Monthly tithe payment",
        purpose="regular_tithe",
        iso_currency_code="USD",
        is_verified=True,
        is_tax_deductible=True,
        receipt_issued=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.fixture
def sample_schedule_data():
    """Sample tithing schedule data."""
    return TithingScheduleCreate(
        name="Monthly Tithe",
        amount=Decimal("200.00"),
        frequency=TithingFrequency.MONTHLY,
        recipient="First Baptist Church",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=365),
        is_active=True,
        auto_execute=False
    )


@pytest.fixture
def sample_goal_data():
    """Sample tithing goal data."""
    return TithingGoalCreate(
        name="Annual Tithe Goal",
        target_amount=Decimal("2400.00"),
        target_percentage=Decimal("10.0"),
        year=2024,
        description="10% of annual income goal"
    )


class TestTithingPaymentOperations:
    """Test tithing payment operations."""

    @pytest.mark.asyncio
    async def test_create_payment_success(self, tithing_service, sample_payment_data, sample_user_id, sample_payment):
        """Test successful payment creation."""
        # Arrange
        tithing_service.payment_repo.create.return_value = sample_payment
        
        # Act
        result = await tithing_service.create_payment(sample_payment_data, sample_user_id)
        
        # Assert
        assert result == sample_payment
        tithing_service.payment_repo.create.assert_called_once()
        create_args = tithing_service.payment_repo.create.call_args[0][0]
        assert create_args.amount == sample_payment_data.amount
        assert create_args.recipient == sample_payment_data.recipient
        assert create_args.user_id == sample_user_id

    @pytest.mark.asyncio
    async def test_create_payment_validation_error(self, tithing_service, sample_user_id):
        """Test payment creation with validation errors."""
        # Arrange
        invalid_payment_data = TithingPaymentCreate(
            amount=Decimal("-50.00"),  # Negative amount
            date=date.today(),
            method="invalid_method",  # Invalid method
            recipient="",  # Empty recipient
        )
        
        # Act & Assert
        with pytest.raises(ValidationError):
            await tithing_service.create_payment(invalid_payment_data, sample_user_id)

    @pytest.mark.asyncio
    async def test_get_payment_success(self, tithing_service, sample_payment):
        """Test successful payment retrieval."""
        # Arrange
        payment_id = sample_payment.id
        tithing_service.payment_repo.get_by_id.return_value = sample_payment
        
        # Act
        result = await tithing_service.get_payment(payment_id)
        
        # Assert
        assert result == sample_payment
        tithing_service.payment_repo.get_by_id.assert_called_once_with(payment_id)

    @pytest.mark.asyncio
    async def test_get_payment_not_found(self, tithing_service):
        """Test payment retrieval when payment not found."""
        # Arrange
        payment_id = str(uuid4())
        tithing_service.payment_repo.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(NotFoundError, match="Tithing payment not found"):
            await tithing_service.get_payment(payment_id)

    @pytest.mark.asyncio
    async def test_update_payment_success(self, tithing_service, sample_payment):
        """Test successful payment update."""
        # Arrange
        payment_id = sample_payment.id
        update_data = TithingPaymentUpdate(
            amount=Decimal("175.00"),
            notes="Updated monthly tithe payment",
            is_verified=True
        )
        
        updated_payment = TithingPayment(**{**sample_payment.__dict__, "amount": Decimal("175.00")})
        tithing_service.payment_repo.get_by_id.return_value = sample_payment
        tithing_service.payment_repo.update.return_value = updated_payment
        
        # Act
        result = await tithing_service.update_payment(payment_id, update_data)
        
        # Assert
        assert result.amount == Decimal("175.00")
        tithing_service.payment_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_payment_success(self, tithing_service, sample_payment):
        """Test successful payment deletion."""
        # Arrange
        payment_id = sample_payment.id
        tithing_service.payment_repo.get_by_id.return_value = sample_payment
        tithing_service.payment_repo.delete.return_value = True
        
        # Act
        result = await tithing_service.delete_payment(payment_id)
        
        # Assert
        assert result is True
        tithing_service.payment_repo.delete.assert_called_once_with(payment_id)

    @pytest.mark.asyncio
    async def test_list_payments_with_filters(self, tithing_service, sample_user_id):
        """Test listing payments with filters."""
        # Arrange
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        payments = [Mock() for _ in range(5)]
        
        tithing_service.payment_repo.get_by_user_and_date_range.return_value = payments
        
        # Act
        result = await tithing_service.list_payments(
            user_id=sample_user_id,
            start_date=start_date,
            end_date=end_date,
            method="online",
            recipient="First Baptist Church"
        )
        
        # Assert
        assert len(result) == 5
        tithing_service.payment_repo.get_by_user_and_date_range.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_payment_analytics(self, tithing_service, sample_user_id):
        """Test payment analytics calculation."""
        # Arrange
        year = 2024
        mock_analytics = {
            "total_amount": Decimal("1800.00"),
            "payment_count": 12,
            "average_payment": Decimal("150.00"),
            "monthly_breakdown": {
                "January": Decimal("150.00"),
                "February": Decimal("150.00"),
                # ... other months
            },
            "method_breakdown": {
                "online": Decimal("1200.00"),
                "check": Decimal("600.00")
            },
            "recipient_breakdown": {
                "First Baptist Church": Decimal("1800.00")
            }
        }
        
        tithing_service.payment_repo.get_annual_analytics.return_value = mock_analytics
        
        # Act
        result = await tithing_service.get_payment_analytics(sample_user_id, year)
        
        # Assert
        assert result["total_amount"] == Decimal("1800.00")
        assert result["payment_count"] == 12
        assert result["average_payment"] == Decimal("150.00")
        tithing_service.payment_repo.get_annual_analytics.assert_called_once_with(sample_user_id, year)


class TestTithingScheduleOperations:
    """Test tithing schedule operations."""

    @pytest.mark.asyncio
    async def test_create_schedule_success(self, tithing_service, sample_schedule_data, sample_user_id):
        """Test successful schedule creation."""
        # Arrange
        mock_schedule = Mock()
        mock_schedule.id = str(uuid4())
        tithing_service.schedule_repo.create.return_value = mock_schedule
        
        # Act
        result = await tithing_service.create_schedule(sample_schedule_data, sample_user_id)
        
        # Assert
        assert result == mock_schedule
        tithing_service.schedule_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_schedule_validation_error(self, tithing_service, sample_user_id):
        """Test schedule creation with invalid data."""
        # Arrange
        invalid_schedule_data = TithingScheduleCreate(
            name="",  # Empty name
            amount=Decimal("-100.00"),  # Negative amount
            frequency=TithingFrequency.MONTHLY,
            recipient="Church",
            start_date=date.today() + timedelta(days=1),
            end_date=date.today(),  # End date before start date
            is_active=True
        )
        
        # Act & Assert
        with pytest.raises(ValidationError):
            await tithing_service.create_schedule(invalid_schedule_data, sample_user_id)

    @pytest.mark.asyncio
    async def test_update_schedule_success(self, tithing_service):
        """Test successful schedule update."""
        # Arrange
        schedule_id = str(uuid4())
        existing_schedule = Mock()
        updated_schedule = Mock()
        
        tithing_service.schedule_repo.get_by_id.return_value = existing_schedule
        tithing_service.schedule_repo.update.return_value = updated_schedule
        
        update_data = {
            "amount": Decimal("250.00"),
            "is_active": False
        }
        
        # Act
        result = await tithing_service.update_schedule(schedule_id, update_data)
        
        # Assert
        assert result == updated_schedule
        tithing_service.schedule_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_schedule_payments(self, tithing_service):
        """Test generating payments from schedule."""
        # Arrange
        schedule_id = str(uuid4())
        start_date = date(2024, 1, 1)
        end_date = date(2024, 3, 31)
        
        mock_schedule = Mock()
        mock_schedule.amount = Decimal("200.00")
        mock_schedule.frequency = TithingFrequency.MONTHLY
        mock_schedule.recipient = "Church"
        
        tithing_service.schedule_repo.get_by_id.return_value = mock_schedule
        
        # Act
        result = await tithing_service.generate_schedule_payments(schedule_id, start_date, end_date)
        
        # Assert
        assert len(result) == 3  # 3 months
        for payment in result:
            assert payment.amount == Decimal("200.00")
            assert payment.recipient == "Church"

    @pytest.mark.asyncio
    async def test_execute_due_schedules(self, tithing_service):
        """Test executing due scheduled payments."""
        # Arrange
        due_schedules = [Mock() for _ in range(3)]
        created_payments = [Mock() for _ in range(3)]
        
        tithing_service.schedule_repo.get_due_schedules.return_value = due_schedules
        tithing_service.payment_repo.create_bulk.return_value = created_payments
        
        # Act
        result = await tithing_service.execute_due_schedules()
        
        # Assert
        assert len(result) == 3
        tithing_service.schedule_repo.get_due_schedules.assert_called_once()
        tithing_service.payment_repo.create_bulk.assert_called_once()


class TestTithingGoalOperations:
    """Test tithing goal operations."""

    @pytest.mark.asyncio
    async def test_create_goal_success(self, tithing_service, sample_goal_data, sample_user_id):
        """Test successful goal creation."""
        # Arrange
        mock_goal = Mock()
        mock_goal.id = str(uuid4())
        tithing_service.goal_repo.create.return_value = mock_goal
        
        # Act
        result = await tithing_service.create_goal(sample_goal_data, sample_user_id)
        
        # Assert
        assert result == mock_goal
        tithing_service.goal_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_goal_duplicate_year(self, tithing_service, sample_goal_data, sample_user_id):
        """Test goal creation with duplicate year."""
        # Arrange
        existing_goal = Mock()
        tithing_service.goal_repo.get_by_user_and_year.return_value = existing_goal
        
        # Act & Assert
        with pytest.raises(BusinessLogicError, match="Goal already exists for this year"):
            await tithing_service.create_goal(sample_goal_data, sample_user_id)

    @pytest.mark.asyncio
    async def test_calculate_goal_progress(self, tithing_service, sample_user_id):
        """Test goal progress calculation."""
        # Arrange
        year = 2024
        mock_goal = Mock()
        mock_goal.target_amount = Decimal("2400.00")
        mock_goal.target_percentage = Decimal("10.0")
        
        total_payments = Decimal("1200.00")
        
        tithing_service.goal_repo.get_by_user_and_year.return_value = mock_goal
        tithing_service.payment_repo.get_total_by_user_and_year.return_value = total_payments
        
        # Act
        result = await tithing_service.calculate_goal_progress(sample_user_id, year)
        
        # Assert
        assert result["goal"] == mock_goal
        assert result["total_paid"] == total_payments
        assert result["remaining_amount"] == Decimal("1200.00")
        assert result["progress_percentage"] == Decimal("50.0")
        assert result["is_on_track"] is False  # Behind schedule mid-year

    @pytest.mark.asyncio
    async def test_get_goal_recommendations(self, tithing_service, sample_user_id):
        """Test goal recommendations based on income and payment history."""
        # Arrange
        annual_income = Decimal("60000.00")
        payment_history = [
            {"year": 2023, "total": Decimal("3000.00")},
            {"year": 2022, "total": Decimal("2800.00")},
            {"year": 2021, "total": Decimal("2500.00")}
        ]
        
        tithing_service.payment_repo.get_annual_totals_by_user.return_value = payment_history
        
        # Act
        result = await tithing_service.get_goal_recommendations(sample_user_id, annual_income)
        
        # Assert
        assert "recommended_percentage" in result
        assert "recommended_amount" in result
        assert "suggested_monthly_amount" in result
        assert "historical_average" in result
        assert result["recommended_percentage"] >= Decimal("5.0")  # Biblical minimum
        assert result["recommended_percentage"] <= Decimal("15.0")  # Generous giving


class TestTithingAnalytics:
    """Test tithing analytics and reporting."""

    @pytest.mark.asyncio
    async def test_generate_annual_summary(self, tithing_service, sample_user_id):
        """Test annual summary generation."""
        # Arrange
        year = 2024
        mock_summary_data = {
            "total_amount": Decimal("3600.00"),
            "payment_count": 12,
            "average_payment": Decimal("300.00"),
            "largest_payment": Decimal("500.00"),
            "smallest_payment": Decimal("200.00"),
            "most_frequent_method": "online",
            "most_frequent_recipient": "First Baptist Church",
            "tax_deductible_total": Decimal("3600.00"),
            "monthly_consistency_score": Decimal("95.0")
        }
        
        tithing_service.summary_repo.generate_annual_summary.return_value = mock_summary_data
        
        # Act
        result = await tithing_service.generate_annual_summary(sample_user_id, year)
        
        # Assert
        assert result["total_amount"] == Decimal("3600.00")
        assert result["payment_count"] == 12
        assert result["monthly_consistency_score"] == Decimal("95.0")
        tithing_service.summary_repo.generate_annual_summary.assert_called_once_with(sample_user_id, year)

    @pytest.mark.asyncio
    async def test_get_giving_trends(self, tithing_service, sample_user_id):
        """Test giving trends analysis."""
        # Arrange
        years = [2022, 2023, 2024]
        mock_trends = {
            "yearly_totals": {
                2022: Decimal("2400.00"),
                2023: Decimal("3000.00"),
                2024: Decimal("3600.00")
            },
            "growth_rate": Decimal("25.0"),  # 25% year-over-year growth
            "trend_direction": "increasing",
            "consistency_improvement": True,
            "average_growth_rate": Decimal("20.0")
        }
        
        tithing_service.summary_repo.calculate_giving_trends.return_value = mock_trends
        
        # Act
        result = await tithing_service.get_giving_trends(sample_user_id, years)
        
        # Assert
        assert result["growth_rate"] == Decimal("25.0")
        assert result["trend_direction"] == "increasing"
        assert result["consistency_improvement"] is True

    @pytest.mark.asyncio
    async def test_calculate_tax_summary(self, tithing_service, sample_user_id):
        """Test tax summary calculation for tax-deductible donations."""
        # Arrange
        tax_year = 2024
        mock_tax_summary = {
            "total_deductible": Decimal("3400.00"),
            "total_non_deductible": Decimal("200.00"),
            "payment_count": 12,
            "receipts_issued": 12,
            "receipts_pending": 0,
            "organizations": [
                {
                    "name": "First Baptist Church",
                    "total": Decimal("3000.00"),
                    "payment_count": 10
                },
                {
                    "name": "Salvation Army",
                    "total": Decimal("400.00"),
                    "payment_count": 2
                }
            ]
        }
        
        tithing_service.payment_repo.calculate_tax_summary.return_value = mock_tax_summary
        
        # Act
        result = await tithing_service.calculate_tax_summary(sample_user_id, tax_year)
        
        # Assert
        assert result["total_deductible"] == Decimal("3400.00")
        assert result["total_non_deductible"] == Decimal("200.00")
        assert len(result["organizations"]) == 2
        tithing_service.payment_repo.calculate_tax_summary.assert_called_once_with(sample_user_id, tax_year)


class TestTithingValidation:
    """Test tithing validation logic."""

    @pytest.mark.asyncio
    async def test_validate_payment_amount(self, tithing_service):
        """Test payment amount validation."""
        # Valid amounts
        valid_amounts = [Decimal("0.01"), Decimal("100.00"), Decimal("9999.99")]
        for amount in valid_amounts:
            result = await tithing_service._validate_payment_amount(amount)
            assert result is True
        
        # Invalid amounts
        invalid_amounts = [Decimal("0.00"), Decimal("-10.00"), Decimal("100000.00")]
        for amount in invalid_amounts:
            with pytest.raises(ValidationError):
                await tithing_service._validate_payment_amount(amount)

    @pytest.mark.asyncio
    async def test_validate_recipient(self, tithing_service):
        """Test recipient validation."""
        # Valid recipients
        valid_recipients = ["First Baptist Church", "Salvation Army", "Local Food Bank"]
        for recipient in valid_recipients:
            result = await tithing_service._validate_recipient(recipient)
            assert result is True
        
        # Invalid recipients
        invalid_recipients = ["", "   ", "A" * 200]  # Empty, whitespace, too long
        for recipient in invalid_recipients:
            with pytest.raises(ValidationError):
                await tithing_service._validate_recipient(recipient)

    @pytest.mark.asyncio
    async def test_validate_date_range(self, tithing_service):
        """Test date range validation."""
        # Valid date ranges
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        result = await tithing_service._validate_date_range(start_date, end_date)
        assert result is True
        
        # Invalid date ranges
        with pytest.raises(ValidationError):
            await tithing_service._validate_date_range(end_date, start_date)  # End before start


class TestTithingBusinessLogic:
    """Test complex business logic scenarios."""

    @pytest.mark.asyncio
    async def test_calculate_tithe_recommendation(self, tithing_service):
        """Test tithe recommendation calculation based on biblical principles."""
        # Test different income scenarios
        income_scenarios = [
            (Decimal("50000.00"), Decimal("5000.00")),  # 10% of $50k
            (Decimal("100000.00"), Decimal("10000.00")),  # 10% of $100k
            (Decimal("25000.00"), Decimal("2500.00"))  # 10% of $25k
        ]
        
        for annual_income, expected_tithe in income_scenarios:
            result = await tithing_service.calculate_tithe_recommendation(annual_income)
            assert result["recommended_annual"] == expected_tithe
            assert result["recommended_monthly"] == expected_tithe / 12
            assert result["recommended_percentage"] == Decimal("10.0")

    @pytest.mark.asyncio
    async def test_process_recurring_payments(self, tithing_service):
        """Test processing of recurring scheduled payments."""
        # This would test the background task processing
        # Mock the scheduled payment processor
        mock_processor_result = {
            "processed_count": 5,
            "failed_count": 0,
            "total_amount": Decimal("1000.00"),
            "processed_schedules": [str(uuid4()) for _ in range(5)]
        }
        
        with patch.object(tithing_service, '_process_scheduled_payments', return_value=mock_processor_result):
            result = await tithing_service.process_recurring_payments()
            
            assert result["processed_count"] == 5
            assert result["failed_count"] == 0
            assert result["total_amount"] == Decimal("1000.00")

    @pytest.mark.asyncio
    async def test_generate_giving_receipt(self, tithing_service, sample_user_id):
        """Test generating tax-deductible giving receipts."""
        # Arrange
        year = 2024
        mock_receipt_data = {
            "user_id": sample_user_id,
            "year": year,
            "total_deductible": Decimal("3600.00"),
            "payment_count": 12,
            "receipt_number": f"RECEIPT-{year}-{sample_user_id[:8].upper()}",
            "generated_date": datetime.utcnow(),
            "organizations": [
                {
                    "name": "First Baptist Church",
                    "address": "123 Church St, City, State 12345",
                    "total": Decimal("3600.00"),
                    "payments": 12
                }
            ]
        }
        
        tithing_service.payment_repo.generate_annual_receipt.return_value = mock_receipt_data
        
        # Act
        result = await tithing_service.generate_giving_receipt(sample_user_id, year)
        
        # Assert
        assert result["total_deductible"] == Decimal("3600.00")
        assert result["payment_count"] == 12
        assert result["receipt_number"].startswith(f"RECEIPT-{year}")
        tithing_service.payment_repo.generate_annual_receipt.assert_called_once_with(sample_user_id, year)
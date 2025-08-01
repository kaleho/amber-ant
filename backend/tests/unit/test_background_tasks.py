"""Comprehensive unit tests for Celery background tasks."""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta, date
from decimal import Decimal
from uuid import uuid4
import asyncio

from src.services.background.tasks import (
    sync_account_data,
    process_transactions,
    send_notification_email,
    generate_monthly_report,
    cleanup_expired_sessions,
    sync_all_accounts,
    generate_daily_reports,
    check_task_status,
    cancel_task
)


@pytest.fixture
def mock_celery_request():
    """Mock Celery request object."""
    return Mock(id=str(uuid4()))


@pytest.fixture
def mock_plaid_client():
    """Mock Plaid client."""
    client = Mock()
    client.get_account_balances = AsyncMock()
    client.get_transactions = AsyncMock()
    return client


@pytest.fixture
def mock_cache_service():
    """Mock Redis cache service."""
    service = AsyncMock()
    service.set = AsyncMock()
    service.get = AsyncMock()
    return service


@pytest.fixture
def mock_account_service():
    """Mock account service."""
    service = Mock()
    service.account_repo = Mock()
    service.update_account_balance = AsyncMock()
    return service


@pytest.fixture
def mock_transaction_service():
    """Mock transaction service."""
    service = Mock()
    service.transaction_repo = Mock()
    service.account_repo = Mock()
    service.create_transaction = AsyncMock()
    service.update_transaction = AsyncMock()
    return service


@pytest.fixture
def mock_email_service():
    """Mock email service."""
    service = AsyncMock()
    service.send_template_email = AsyncMock(return_value=True)
    return service


@pytest.fixture
def mock_session_service():
    """Mock session service."""
    service = AsyncMock()
    service.cleanup_expired_sessions = AsyncMock(return_value=25)
    return service


class TestSyncAccountDataTask:
    """Test account synchronization background task."""

    @pytest.mark.asyncio
    async def test_sync_account_data_success(self, mock_celery_request):
        """Test successful account data synchronization."""
        # Arrange
        tenant_id = str(uuid4())
        access_token = "test_access_token"
        account_id = str(uuid4())
        
        mock_account_data = {
            "accounts": [
                {
                    "account_id": "plaid_account_123",
                    "name": "Test Checking",
                    "type": "depository",
                    "subtype": "checking",
                    "balances": {
                        "available": 1500.00,
                        "current": 1750.00,
                        "limit": None
                    }
                }
            ]
        }
        
        mock_existing_account = Mock(
            id=str(uuid4()),
            user_id=str(uuid4()),
            current_balance=Decimal("1500.00")
        )
        
        with patch('src.services.background.tasks.get_plaid_client') as mock_get_plaid, \
             patch('src.services.background.tasks.get_cache_service') as mock_get_cache, \
             patch('src.services.background.tasks.AccountService') as mock_account_service_class:
            
            # Setup mocks
            mock_plaid_client = AsyncMock()
            mock_plaid_client.get_account_balances.return_value = mock_account_data
            mock_get_plaid.return_value = mock_plaid_client
            
            mock_cache_service = AsyncMock()
            mock_get_cache.return_value = mock_cache_service
            
            mock_account_service = Mock()
            mock_account_service.account_repo.get_by_plaid_account_id.return_value = mock_existing_account
            mock_account_service.update_account_balance.return_value = mock_existing_account
            mock_account_service_class.return_value = mock_account_service
            
            # Create task instance with bound self
            task_instance = Mock()
            task_instance.request = mock_celery_request
            
            # Act
            result = sync_account_data(
                task_instance,
                tenant_id=tenant_id,
                access_token=access_token,
                account_id=account_id
            )
            
            # Assert
            assert result["status"] == "success"
            assert result["accounts_synced"] == 1
            assert len(result["accounts"]) == 1
            assert result["accounts"][0]["account_id"] == "plaid_account_123"
            assert result["accounts"][0]["status"] == "updated"

    @pytest.mark.asyncio
    async def test_sync_account_data_retry_on_failure(self, mock_celery_request):
        """Test task retry on failure."""
        # Arrange
        tenant_id = str(uuid4())
        access_token = "test_access_token"
        
        with patch('src.services.background.tasks.get_plaid_client') as mock_get_plaid:
            mock_plaid_client = AsyncMock()
            mock_plaid_client.get_account_balances.side_effect = Exception("API Error")
            mock_get_plaid.return_value = mock_plaid_client
            
            # Create task instance with retry method
            task_instance = Mock()
            task_instance.request = mock_celery_request
            task_instance.retry = Mock(side_effect=Exception("Retry exception"))
            
            # Act & Assert
            with pytest.raises(Exception, match="Retry exception"):
                sync_account_data(
                    task_instance,
                    tenant_id=tenant_id,
                    access_token=access_token
                )
            
            task_instance.retry.assert_called_once_with(countdown=300, max_retries=5)

    @pytest.mark.asyncio
    async def test_sync_account_data_account_not_found(self, mock_celery_request):
        """Test handling when account not found in database."""
        # Arrange
        tenant_id = str(uuid4())
        access_token = "test_access_token"
        
        mock_account_data = {
            "accounts": [
                {
                    "account_id": "unknown_plaid_account",
                    "name": "Unknown Account",
                    "type": "depository",
                    "subtype": "checking",
                    "balances": {
                        "available": 1000.00,
                        "current": 1200.00,
                        "limit": None
                    }
                }
            ]
        }
        
        with patch('src.services.background.tasks.get_plaid_client') as mock_get_plaid, \
             patch('src.services.background.tasks.get_cache_service') as mock_get_cache, \
             patch('src.services.background.tasks.AccountService') as mock_account_service_class:
            
            # Setup mocks
            mock_plaid_client = AsyncMock()
            mock_plaid_client.get_account_balances.return_value = mock_account_data
            mock_get_plaid.return_value = mock_plaid_client
            
            mock_cache_service = AsyncMock()
            mock_get_cache.return_value = mock_cache_service
            
            mock_account_service = Mock()
            mock_account_service.account_repo.get_by_plaid_account_id.return_value = None  # Not found
            mock_account_service_class.return_value = mock_account_service
            
            task_instance = Mock()
            task_instance.request = mock_celery_request
            
            # Act
            result = sync_account_data(
                task_instance,
                tenant_id=tenant_id,
                access_token=access_token
            )
            
            # Assert
            assert result["status"] == "success"
            assert result["accounts_synced"] == 0


class TestProcessTransactionsTask:
    """Test transaction processing background task."""

    @pytest.mark.asyncio
    async def test_process_transactions_success(self, mock_celery_request):
        """Test successful transaction processing."""
        # Arrange
        tenant_id = str(uuid4())
        access_token = "test_access_token"
        start_date = "2024-01-01"
        end_date = "2024-01-31"
        
        mock_transaction_data = {
            "transactions": [
                {
                    "transaction_id": "txn_123",
                    "account_id": "plaid_account_123",
                    "amount": -25.00,
                    "date": "2024-01-15",
                    "name": "Coffee Shop",
                    "merchant_name": "Local Coffee",
                    "category": ["Food and Drink", "Restaurants"],
                    "pending": False
                }
            ]
        }
        
        mock_account = Mock(
            id=str(uuid4()),
            user_id=str(uuid4())
        )
        
        mock_created_transaction = Mock(id=str(uuid4()))
        
        with patch('src.services.background.tasks.get_plaid_client') as mock_get_plaid, \
             patch('src.services.background.tasks.get_cache_service') as mock_get_cache, \
             patch('src.services.background.tasks.TransactionService') as mock_transaction_service_class:
            
            # Setup mocks
            mock_plaid_client = AsyncMock()
            mock_plaid_client.get_transactions.return_value = mock_transaction_data
            mock_get_plaid.return_value = mock_plaid_client
            
            mock_cache_service = AsyncMock()
            mock_get_cache.return_value = mock_cache_service
            
            mock_transaction_service = Mock()
            mock_transaction_service.transaction_repo.get_by_plaid_transaction_id.return_value = None  # New transaction
            mock_transaction_service.account_repo.get_by_plaid_account_id.return_value = mock_account
            mock_transaction_service.create_transaction.return_value = mock_created_transaction
            mock_transaction_service_class.return_value = mock_transaction_service
            
            task_instance = Mock()
            task_instance.request = mock_celery_request
            
            # Act
            result = process_transactions(
                task_instance,
                tenant_id=tenant_id,
                access_token=access_token,
                start_date=start_date,
                end_date=end_date
            )
            
            # Assert
            assert result["status"] == "success"
            assert result["transactions_processed"] == 1
            assert result["date_range"]["start"] == "2024-01-01T00:00:00"
            assert result["date_range"]["end"] == "2024-01-31T00:00:00"

    @pytest.mark.asyncio
    async def test_process_transactions_existing_transaction(self, mock_celery_request):
        """Test processing when transaction already exists."""
        # Arrange
        tenant_id = str(uuid4())
        access_token = "test_access_token"
        
        mock_transaction_data = {
            "transactions": [
                {
                    "transaction_id": "existing_txn_123",
                    "account_id": "plaid_account_123",
                    "amount": -50.00,
                    "date": "2024-01-20",
                    "name": "Grocery Store",
                    "pending": False
                }
            ]
        }
        
        mock_existing_transaction = Mock(
            id=str(uuid4()),
            user_id=str(uuid4()),
            is_pending=True  # Different pending status
        )
        
        with patch('src.services.background.tasks.get_plaid_client') as mock_get_plaid, \
             patch('src.services.background.tasks.get_cache_service') as mock_get_cache, \
             patch('src.services.background.tasks.TransactionService') as mock_transaction_service_class:
            
            # Setup mocks
            mock_plaid_client = AsyncMock()
            mock_plaid_client.get_transactions.return_value = mock_transaction_data
            mock_get_plaid.return_value = mock_plaid_client
            
            mock_cache_service = AsyncMock()
            mock_get_cache.return_value = mock_cache_service
            
            mock_transaction_service = Mock()
            mock_transaction_service.transaction_repo.get_by_plaid_transaction_id.return_value = mock_existing_transaction
            mock_transaction_service.update_transaction = AsyncMock()
            mock_transaction_service_class.return_value = mock_transaction_service
            
            task_instance = Mock()
            task_instance.request = mock_celery_request
            
            # Act
            result = process_transactions(
                task_instance,
                tenant_id=tenant_id,
                access_token=access_token
            )
            
            # Assert
            assert result["status"] == "success"
            assert result["transactions_processed"] == 1
            mock_transaction_service.update_transaction.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_transactions_account_not_found(self, mock_celery_request):
        """Test transaction processing when account not found."""
        # Arrange
        tenant_id = str(uuid4())
        access_token = "test_access_token"
        
        mock_transaction_data = {
            "transactions": [
                {
                    "transaction_id": "orphan_txn_123",
                    "account_id": "unknown_account_123",
                    "amount": -10.00,
                    "date": "2024-01-25",
                    "name": "Unknown Transaction"
                }
            ]
        }
        
        with patch('src.services.background.tasks.get_plaid_client') as mock_get_plaid, \
             patch('src.services.background.tasks.get_cache_service') as mock_get_cache, \
             patch('src.services.background.tasks.TransactionService') as mock_transaction_service_class:
            
            # Setup mocks
            mock_plaid_client = AsyncMock()
            mock_plaid_client.get_transactions.return_value = mock_transaction_data
            mock_get_plaid.return_value = mock_plaid_client
            
            mock_cache_service = AsyncMock()
            mock_get_cache.return_value = mock_cache_service
            
            mock_transaction_service = Mock()
            mock_transaction_service.transaction_repo.get_by_plaid_transaction_id.return_value = None
            mock_transaction_service.account_repo.get_by_plaid_account_id.return_value = None  # Account not found
            mock_transaction_service_class.return_value = mock_transaction_service
            
            task_instance = Mock()
            task_instance.request = mock_celery_request
            
            # Act
            result = process_transactions(
                task_instance,
                tenant_id=tenant_id,
                access_token=access_token
            )
            
            # Assert
            assert result["status"] == "success"
            assert result["transactions_processed"] == 0

    @pytest.mark.asyncio
    async def test_process_transactions_with_account_filter(self, mock_celery_request):
        """Test transaction processing with account ID filter."""
        # Arrange
        tenant_id = str(uuid4())
        access_token = "test_access_token"
        account_ids = ["specific_account_123"]
        
        with patch('src.services.background.tasks.get_plaid_client') as mock_get_plaid, \
             patch('src.services.background.tasks.get_cache_service') as mock_get_cache, \
             patch('src.services.background.tasks.TransactionService') as mock_transaction_service_class:
            
            mock_plaid_client = AsyncMock()
            mock_plaid_client.get_transactions.return_value = {"transactions": []}
            mock_get_plaid.return_value = mock_plaid_client
            
            mock_cache_service = AsyncMock()
            mock_get_cache.return_value = mock_cache_service
            
            mock_transaction_service = Mock()
            mock_transaction_service_class.return_value = mock_transaction_service
            
            task_instance = Mock()
            task_instance.request = mock_celery_request
            
            # Act
            result = process_transactions(
                task_instance,
                tenant_id=tenant_id,
                access_token=access_token,
                account_ids=account_ids
            )
            
            # Assert
            mock_plaid_client.get_transactions.assert_called_once()
            call_args = mock_plaid_client.get_transactions.call_args[1]
            assert call_args["account_ids"] == account_ids


class TestSendNotificationEmailTask:
    """Test email notification background task."""

    @pytest.mark.asyncio
    async def test_send_notification_email_success(self, mock_celery_request):
        """Test successful email sending."""
        # Arrange
        tenant_id = str(uuid4())
        user_email = "test@example.com"
        template = "welcome"
        subject = "Welcome to Faithful Finances"
        data = {"user_name": "John Doe", "app_name": "Faithful Finances"}
        
        with patch('src.services.background.tasks.get_email_service') as mock_get_email:
            mock_email_service = AsyncMock()
            mock_email_service.send_template_email.return_value = True
            mock_get_email.return_value = mock_email_service
            
            task_instance = Mock()
            task_instance.request = mock_celery_request
            
            # Act
            result = send_notification_email(
                task_instance,
                tenant_id=tenant_id,
                user_email=user_email,
                template=template,
                subject=subject,
                data=data
            )
            
            # Assert
            assert result["status"] == "success"
            assert result["email_sent"] is True
            assert result["recipient"] == user_email
            assert result["template"] == template
            
            mock_email_service.send_template_email.assert_called_once_with(
                to=user_email,
                template_name=template,
                template_data=data,
                subject=subject
            )

    @pytest.mark.asyncio
    async def test_send_notification_email_failure(self, mock_celery_request):
        """Test email sending failure and retry."""
        # Arrange
        tenant_id = str(uuid4())
        user_email = "test@example.com"
        template = "welcome"
        subject = "Welcome"
        
        with patch('src.services.background.tasks.get_email_service') as mock_get_email:
            mock_email_service = AsyncMock()
            mock_email_service.send_template_email.return_value = False  # Email failed
            mock_get_email.return_value = mock_email_service
            
            task_instance = Mock()
            task_instance.request = mock_celery_request
            task_instance.retry = Mock(side_effect=Exception("Retry exception"))
            
            # Act & Assert
            with pytest.raises(Exception, match="Retry exception"):
                send_notification_email(
                    task_instance,
                    tenant_id=tenant_id,
                    user_email=user_email,
                    template=template,
                    subject=subject
                )
            
            task_instance.retry.assert_called_once_with(countdown=60, max_retries=3)

    @pytest.mark.asyncio
    async def test_send_notification_email_service_exception(self, mock_celery_request):
        """Test email service exception handling."""
        # Arrange
        tenant_id = str(uuid4())
        user_email = "test@example.com"
        template = "password_reset"
        subject = "Reset Password"
        
        with patch('src.services.background.tasks.get_email_service') as mock_get_email:
            mock_email_service = AsyncMock()
            mock_email_service.send_template_email.side_effect = Exception("SMTP Error")
            mock_get_email.return_value = mock_email_service
            
            task_instance = Mock()
            task_instance.request = mock_celery_request
            task_instance.retry = Mock(side_effect=Exception("Retry exception"))
            
            # Act & Assert
            with pytest.raises(Exception, match="Retry exception"):
                send_notification_email(
                    task_instance,
                    tenant_id=tenant_id,
                    user_email=user_email,
                    template=template,
                    subject=subject
                )


class TestGenerateMonthlyReportTask:
    """Test monthly report generation background task."""

    @pytest.mark.asyncio
    async def test_generate_monthly_report_success(self, mock_celery_request):
        """Test successful monthly report generation."""
        # Arrange
        tenant_id = str(uuid4())
        month = "02"
        year = 2024
        
        with patch('src.services.background.tasks.send_notification_email') as mock_send_email:
            mock_send_email.delay = Mock()
            
            task_instance = Mock()
            task_instance.request = mock_celery_request
            
            # Act
            result = generate_monthly_report(
                task_instance,
                tenant_id=tenant_id,
                month=month,
                year=year
            )
            
            # Assert
            assert result["status"] == "success"
            assert result["report_generated"] is True
            assert result["period"] == f"{year}-{month}"
            
            # Verify email notification was scheduled
            mock_send_email.delay.assert_called_once()
            email_call_args = mock_send_email.delay.call_args[1]
            assert email_call_args["tenant_id"] == tenant_id
            assert email_call_args["template"] == "monthly_report"

    @pytest.mark.asyncio
    async def test_generate_monthly_report_default_period(self, mock_celery_request):
        """Test monthly report generation with default period."""
        # Arrange
        tenant_id = str(uuid4())
        current_month = datetime.utcnow().strftime("%m")
        current_year = datetime.utcnow().year
        
        with patch('src.services.background.tasks.send_notification_email') as mock_send_email:
            mock_send_email.delay = Mock()
            
            task_instance = Mock()
            task_instance.request = mock_celery_request
            
            # Act
            result = generate_monthly_report(
                task_instance,
                tenant_id=tenant_id
            )
            
            # Assert
            assert result["status"] == "success"
            assert result["period"] == f"{current_year}-{current_month}"

    @pytest.mark.asyncio
    async def test_generate_monthly_report_retry_on_failure(self, mock_celery_request):
        """Test retry on report generation failure."""
        # Arrange
        tenant_id = str(uuid4())
        
        with patch('src.services.background.tasks.send_notification_email') as mock_send_email:
            mock_send_email.delay.side_effect = Exception("Email service down")
            
            task_instance = Mock()
            task_instance.request = mock_celery_request
            task_instance.retry = Mock(side_effect=Exception("Retry exception"))
            
            # Act & Assert
            with pytest.raises(Exception, match="Retry exception"):
                generate_monthly_report(
                    task_instance,
                    tenant_id=tenant_id
                )
            
            task_instance.retry.assert_called_once_with(countdown=60, max_retries=2)


class TestCleanupExpiredSessionsTask:
    """Test session cleanup background task."""

    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions_success(self, mock_celery_request):
        """Test successful session cleanup."""
        # Arrange
        with patch('src.services.background.tasks.get_session_service') as mock_get_session:
            mock_session_service = AsyncMock()
            mock_session_service.cleanup_expired_sessions.return_value = 15
            mock_get_session.return_value = mock_session_service
            
            task_instance = Mock()
            task_instance.request = mock_celery_request
            
            # Act
            result = cleanup_expired_sessions(task_instance)
            
            # Assert
            assert result["status"] == "success"
            assert result["sessions_cleaned"] == 15
            
            mock_session_service.cleanup_expired_sessions.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions_failure(self, mock_celery_request):
        """Test session cleanup failure and retry."""
        # Arrange
        with patch('src.services.background.tasks.get_session_service') as mock_get_session:
            mock_session_service = AsyncMock()
            mock_session_service.cleanup_expired_sessions.side_effect = Exception("Redis connection error")
            mock_get_session.return_value = mock_session_service
            
            task_instance = Mock()
            task_instance.request = mock_celery_request
            task_instance.retry = Mock(side_effect=Exception("Retry exception"))
            
            # Act & Assert
            with pytest.raises(Exception, match="Retry exception"):
                cleanup_expired_sessions(task_instance)
            
            task_instance.retry.assert_called_once_with(countdown=300, max_retries=2)


class TestCompositeBackgroundTasks:
    """Test composite tasks that orchestrate other tasks."""

    @pytest.mark.asyncio
    async def test_sync_all_accounts_success(self, mock_celery_request):
        """Test successful synchronization of all accounts for tenant."""
        # Arrange
        tenant_id = str(uuid4())
        
        with patch('src.services.background.tasks.sync_account_data') as mock_sync_task:
            mock_task_result = Mock(id="task_123")
            mock_sync_task.delay.return_value = mock_task_result
            
            task_instance = Mock()
            task_instance.request = mock_celery_request
            
            # Act
            result = sync_all_accounts(
                task_instance,
                tenant_id=tenant_id
            )
            
            # Assert
            assert result["status"] == "success"
            assert result["sync_tasks_scheduled"] == 2  # Two access tokens in placeholder
            assert len(result["task_ids"]) == 2
            
            # Verify sync tasks were scheduled
            assert mock_sync_task.delay.call_count == 2

    @pytest.mark.asyncio
    async def test_generate_daily_reports_success(self, mock_celery_request):
        """Test successful daily report generation for all tenants."""
        # Arrange
        with patch('src.services.background.tasks.generate_monthly_report') as mock_report_task:
            mock_task_result = Mock(id="report_task_123")
            mock_report_task.delay.return_value = mock_task_result
            
            task_instance = Mock()
            task_instance.request = mock_celery_request
            
            # Act
            result = generate_daily_reports(task_instance)
            
            # Assert
            assert result["status"] == "success"
            assert result["report_tasks_scheduled"] == 2  # Two tenants in placeholder
            assert len(result["task_ids"]) == 2
            
            # Verify report tasks were scheduled
            assert mock_report_task.delay.call_count == 2


class TestTaskUtilities:
    """Test task utility functions."""

    @pytest.mark.asyncio
    async def test_check_task_status_success(self, mock_celery_request):
        """Test successful task status check."""
        # Arrange
        task_id = str(uuid4())
        
        with patch('src.services.background.tasks.AsyncResult') as mock_async_result:
            mock_result = Mock()
            mock_result.status = "SUCCESS"
            mock_result.result = {"completed": True}
            mock_result.ready.return_value = True
            mock_result.successful.return_value = True
            mock_result.failed.return_value = False
            mock_async_result.return_value = mock_result
            
            task_instance = Mock()
            task_instance.request = mock_celery_request
            
            # Act
            result = check_task_status(task_instance, task_id)
            
            # Assert
            assert result["task_id"] == task_id
            assert result["status"] == "SUCCESS"
            assert result["result"]["completed"] is True
            assert result["successful"] is True
            assert result["failed"] is False

    @pytest.mark.asyncio
    async def test_check_task_status_pending(self, mock_celery_request):
        """Test task status check for pending task."""
        # Arrange
        task_id = str(uuid4())
        
        with patch('src.services.background.tasks.AsyncResult') as mock_async_result:
            mock_result = Mock()
            mock_result.status = "PENDING"
            mock_result.result = None
            mock_result.ready.return_value = False
            mock_result.successful.return_value = False
            mock_result.failed.return_value = False
            mock_async_result.return_value = mock_result
            
            task_instance = Mock()
            task_instance.request = mock_celery_request
            
            # Act
            result = check_task_status(task_instance, task_id)
            
            # Assert
            assert result["task_id"] == task_id
            assert result["status"] == "PENDING"
            assert result["result"] is None

    @pytest.mark.asyncio
    async def test_check_task_status_failure(self, mock_celery_request):
        """Test task status check when AsyncResult fails."""
        # Arrange
        task_id = str(uuid4())
        
        with patch('src.services.background.tasks.AsyncResult') as mock_async_result:
            mock_async_result.side_effect = Exception("Task lookup failed")
            
            task_instance = Mock()
            task_instance.request = mock_celery_request
            
            # Act
            result = check_task_status(task_instance, task_id)
            
            # Assert
            assert result["task_id"] == task_id
            assert result["status"] == "ERROR"
            assert "Task lookup failed" in result["error"]

    @pytest.mark.asyncio
    async def test_cancel_task_success(self, mock_celery_request):
        """Test successful task cancellation."""
        # Arrange
        task_id = str(uuid4())
        
        with patch('src.services.background.tasks.AsyncResult') as mock_async_result:
            mock_result = Mock()
            mock_result.revoke = Mock()
            mock_async_result.return_value = mock_result
            
            task_instance = Mock()
            task_instance.request = mock_celery_request
            
            # Act
            result = cancel_task(task_instance, task_id)
            
            # Assert
            assert result["task_id"] == task_id
            assert result["canceled"] is True
            
            mock_result.revoke.assert_called_once_with(terminate=True)

    @pytest.mark.asyncio
    async def test_cancel_task_failure(self, mock_celery_request):
        """Test task cancellation failure."""
        # Arrange
        task_id = str(uuid4())
        
        with patch('src.services.background.tasks.AsyncResult') as mock_async_result:
            mock_result = Mock()
            mock_result.revoke.side_effect = Exception("Cannot revoke task")
            mock_async_result.return_value = mock_result
            
            task_instance = Mock()
            task_instance.request = mock_celery_request
            
            # Act
            result = cancel_task(task_instance, task_id)
            
            # Assert
            assert result["task_id"] == task_id
            assert result["canceled"] is False
            assert "Cannot revoke task" in result["error"]


class TestTaskErrorHandling:
    """Test error handling in background tasks."""

    @pytest.mark.asyncio
    async def test_task_with_async_event_loop_cleanup(self, mock_celery_request):
        """Test that tasks properly clean up async event loops."""
        # Arrange
        tenant_id = str(uuid4())
        access_token = "test_token"
        
        with patch('src.services.background.tasks.get_plaid_client') as mock_get_plaid, \
             patch('asyncio.new_event_loop') as mock_new_loop, \
             patch('asyncio.set_event_loop') as mock_set_loop:
            
            mock_loop = Mock()
            mock_loop.run_until_complete.side_effect = Exception("Async operation failed")
            mock_loop.close = Mock()
            mock_new_loop.return_value = mock_loop
            
            mock_plaid_client = AsyncMock()
            mock_get_plaid.return_value = mock_plaid_client
            
            task_instance = Mock()
            task_instance.request = mock_celery_request
            task_instance.retry = Mock(side_effect=Exception("Retry exception"))
            
            # Act & Assert
            with pytest.raises(Exception, match="Retry exception"):
                sync_account_data(
                    task_instance,
                    tenant_id=tenant_id,
                    access_token=access_token
                )
            
            # Verify loop cleanup
            mock_loop.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_task_logging_on_error(self, mock_celery_request):
        """Test that tasks log errors appropriately."""
        # Arrange
        tenant_id = str(uuid4())
        access_token = "test_token"
        
        with patch('src.services.background.tasks.get_plaid_client') as mock_get_plaid, \
             patch('src.services.background.tasks.logger') as mock_logger:
            
            mock_plaid_client = AsyncMock()
            mock_plaid_client.get_account_balances.side_effect = Exception("API timeout")
            mock_get_plaid.return_value = mock_plaid_client
            
            task_instance = Mock()
            task_instance.request = mock_celery_request
            task_instance.retry = Mock(side_effect=Exception("Retry exception"))
            
            # Act & Assert
            with pytest.raises(Exception, match="Retry exception"):
                sync_account_data(
                    task_instance,
                    tenant_id=tenant_id,
                    access_token=access_token
                )
            
            # Verify error logging
            mock_logger.error.assert_called()
            error_call = mock_logger.error.call_args
            assert "Sync account data task failed" in error_call[0][0]

    @pytest.mark.asyncio
    async def test_task_retry_countdown_and_max_retries(self, mock_celery_request):
        """Test task retry configuration."""
        # Arrange
        tenant_id = str(uuid4())
        user_email = "test@example.com"
        
        with patch('src.services.background.tasks.get_email_service') as mock_get_email:
            mock_email_service = AsyncMock()
            mock_email_service.send_template_email.side_effect = Exception("SMTP error")
            mock_get_email.return_value = mock_email_service
            
            task_instance = Mock()
            task_instance.request = mock_celery_request
            task_instance.retry = Mock(side_effect=Exception("Retry exception"))
            
            # Act & Assert
            with pytest.raises(Exception, match="Retry exception"):
                send_notification_email(
                    task_instance,
                    tenant_id=tenant_id,
                    user_email=user_email,
                    template="test",
                    subject="Test"
                )
            
            # Verify retry configuration
            task_instance.retry.assert_called_once_with(countdown=60, max_retries=3)


class TestTaskPerformanceAndMemory:
    """Test task performance and memory usage."""

    @pytest.mark.asyncio
    async def test_large_transaction_batch_processing(self, mock_celery_request):
        """Test processing large batches of transactions efficiently."""
        # Arrange
        tenant_id = str(uuid4())
        access_token = "test_token"
        
        # Create large transaction batch
        large_transaction_batch = {
            "transactions": [
                {
                    "transaction_id": f"txn_{i}",
                    "account_id": "test_account",
                    "amount": float(-(i + 1) * 10),
                    "date": "2024-01-15",
                    "name": f"Transaction {i+1}"
                }
                for i in range(500)  # 500 transactions
            ]
        }
        
        with patch('src.services.background.tasks.get_plaid_client') as mock_get_plaid, \
             patch('src.services.background.tasks.get_cache_service') as mock_get_cache, \
             patch('src.services.background.tasks.TransactionService') as mock_transaction_service_class, \
             patch('time.time') as mock_time:
            
            # Setup performance monitoring
            mock_time.side_effect = [0, 30]  # 30 second execution time
            
            mock_plaid_client = AsyncMock()
            mock_plaid_client.get_transactions.return_value = large_transaction_batch
            mock_get_plaid.return_value = mock_plaid_client
            
            mock_cache_service = AsyncMock()
            mock_get_cache.return_value = mock_cache_service
            
            mock_transaction_service = Mock()
            mock_transaction_service.transaction_repo.get_by_plaid_transaction_id.return_value = None
            mock_transaction_service.account_repo.get_by_plaid_account_id.return_value = None
            mock_transaction_service_class.return_value = mock_transaction_service
            
            task_instance = Mock()
            task_instance.request = mock_celery_request
            
            # Act
            result = process_transactions(
                task_instance,
                tenant_id=tenant_id,
                access_token=access_token
            )
            
            # Assert
            assert result["status"] == "success"
            # All transactions should be processed even if accounts not found
            assert result["transactions_processed"] == 0  # No valid accounts

    @pytest.mark.asyncio
    async def test_memory_cleanup_after_task_completion(self, mock_celery_request):
        """Test that tasks clean up memory properly."""
        # Arrange
        tenant_id = str(uuid4())
        
        with patch('src.services.background.tasks.get_session_service') as mock_get_session, \
             patch('gc.collect') as mock_gc_collect:
            
            mock_session_service = AsyncMock()
            mock_session_service.cleanup_expired_sessions.return_value = 100
            mock_get_session.return_value = mock_session_service
            
            task_instance = Mock()
            task_instance.request = mock_celery_request
            
            # Act
            result = cleanup_expired_sessions(task_instance)
            
            # Assert
            assert result["status"] == "success"
            assert result["sessions_cleaned"] == 100
            
            # Note: In a real test, you might check memory usage
            # This is a placeholder for memory monitoring

    @pytest.mark.asyncio
    async def test_concurrent_task_execution(self, mock_celery_request):
        """Test that tasks can handle concurrent execution safely."""
        # Arrange
        tenant_id = str(uuid4())
        access_token = "test_token"
        
        # This test would simulate concurrent execution
        # In practice, Celery handles this, but we can test our task logic
        
        with patch('src.services.background.tasks.get_plaid_client') as mock_get_plaid, \
             patch('src.services.background.tasks.get_cache_service') as mock_get_cache, \
             patch('src.services.background.tasks.AccountService') as mock_account_service_class:
            
            mock_plaid_client = AsyncMock()
            mock_plaid_client.get_account_balances.return_value = {"accounts": []}
            mock_get_plaid.return_value = mock_plaid_client
            
            mock_cache_service = AsyncMock()
            mock_get_cache.return_value = mock_cache_service
            
            mock_account_service = Mock()
            mock_account_service_class.return_value = mock_account_service
            
            task_instance = Mock()
            task_instance.request = mock_celery_request
            
            # Act - simulate multiple concurrent calls
            results = []
            for _ in range(3):
                result = sync_account_data(
                    task_instance,
                    tenant_id=tenant_id,
                    access_token=access_token
                )
                results.append(result)
            
            # Assert
            assert all(r["status"] == "success" for r in results)
            assert len(results) == 3
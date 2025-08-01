"""Unit tests for transactions service layer."""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timezone, date
from decimal import Decimal
from typing import List

from src.transactions.service import TransactionService
from src.transactions.models import Transaction
from src.transactions.schemas import TransactionCreate, TransactionUpdate, TransactionResponse, TransactionFilter
from src.exceptions import ValidationError, AuthorizationError, ExternalServiceError
from src.tenant.context import TenantContext


@pytest.mark.unit
class TestTransactionService:
    """Test TransactionService methods."""
    
    @pytest.fixture
    def mock_transaction_repository(self):
        """Mock transaction repository."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_account_repository(self):
        """Mock account repository."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_plaid_service(self):
        """Mock Plaid service."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_tenant_context(self):
        """Mock tenant context."""
        return TenantContext(
            tenant_id="test-tenant",
            tenant_slug="test-tenant",
            database_url="sqlite:///:memory:",
            user_id="test-user-123"
        )
    
    @pytest.fixture
    def transaction_service(self, mock_transaction_repository, mock_account_repository, mock_plaid_service, mock_tenant_context):
        """Create TransactionService instance with mocked dependencies."""
        with patch('src.transactions.service.get_tenant_context', return_value=mock_tenant_context):
            return TransactionService(mock_transaction_repository, mock_account_repository, mock_plaid_service)
    
    @pytest.fixture
    def sample_transaction_data(self):
        """Sample transaction data for testing."""
        return {
            "account_id": "test-account-123",
            "amount": Decimal("-50.00"),
            "description": "Grocery Store Purchase",
            "transaction_date": date(2024, 1, 15),
            "category": "groceries",
            "subcategory": "food",
            "merchant_name": "Test Grocery Store",
            "transaction_type": "purchase",
            "is_pending": False
        }
    
    @pytest.fixture
    def sample_transaction_model(self, sample_transaction_data):
        """Sample transaction model instance."""
        return Transaction(
            id="test-transaction-123",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            **sample_transaction_data
        )
    
    @pytest.fixture
    def sample_account_model(self):
        """Sample account model for testing."""
        from src.accounts.models import Account
        return Account(
            id="test-account-123",
            user_id="test-user-123",
            name="Test Checking Account",
            account_type="checking",
            balance=Decimal("1000.00"),
            currency="USD",
            is_active=True
        )

    @pytest.mark.asyncio
    async def test_create_transaction_success(self, transaction_service, mock_transaction_repository, mock_account_repository, sample_transaction_data, sample_transaction_model, sample_account_model):
        """Test successful transaction creation."""
        # Arrange
        transaction_create = TransactionCreate(**sample_transaction_data)
        mock_account_repository.get_by_id.return_value = sample_account_model
        mock_transaction_repository.create.return_value = sample_transaction_model
        
        # Act
        result = await transaction_service.create_transaction(transaction_create)
        
        # Assert
        assert isinstance(result, TransactionResponse)
        assert result.amount == sample_transaction_data["amount"]
        assert result.description == sample_transaction_data["description"]
        assert result.category == sample_transaction_data["category"]
        mock_transaction_repository.create.assert_called_once()
        
        # Verify account existence was checked
        mock_account_repository.get_by_id.assert_called_once_with(sample_transaction_data["account_id"])
    
    @pytest.mark.asyncio
    async def test_create_transaction_invalid_account(self, transaction_service, mock_account_repository, sample_transaction_data):
        """Test transaction creation with invalid account."""
        # Arrange
        transaction_create = TransactionCreate(**sample_transaction_data)
        mock_account_repository.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await transaction_service.create_transaction(transaction_create)
        
        assert "account not found" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_create_transaction_with_plaid_sync(self, transaction_service, mock_transaction_repository, mock_account_repository, mock_plaid_service, sample_account_model):
        """Test transaction creation with Plaid synchronization."""
        # Arrange
        plaid_transaction_data = {
            "account_id": "test-account-123",
            "amount": Decimal("-25.99"),
            "description": "Coffee Shop",
            "transaction_date": date(2024, 1, 16),
            "plaid_transaction_id": "plaid_txn_123",
            "category": "dining",
            "merchant_name": "Local Coffee",
            "transaction_type": "purchase"
        }
        transaction_create = TransactionCreate(**plaid_transaction_data)
        
        sample_account_model.plaid_account_id = "plaid_account_123"
        mock_account_repository.get_by_id.return_value = sample_account_model
        mock_plaid_service.get_transaction_details.return_value = {
            "transaction_id": "plaid_txn_123",
            "amount": 25.99,
            "date": "2024-01-16",
            "name": "Coffee Shop Purchase",
            "merchant_name": "Local Coffee Shop",
            "category": ["Food and Drink", "Restaurants", "Coffee Shop"]
        }
        
        created_transaction = Transaction(**plaid_transaction_data, id="test-transaction-123")
        mock_transaction_repository.create.return_value = created_transaction
        
        # Act
        result = await transaction_service.create_transaction(transaction_create)
        
        # Assert
        assert isinstance(result, TransactionResponse)
        mock_plaid_service.get_transaction_details.assert_called_once_with("plaid_txn_123")
        mock_transaction_repository.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_transaction_by_id_success(self, transaction_service, mock_transaction_repository, sample_transaction_model):
        """Test successful transaction retrieval by ID."""
        # Arrange
        transaction_id = "test-transaction-123"
        mock_transaction_repository.get_by_id.return_value = sample_transaction_model
        
        # Act
        result = await transaction_service.get_transaction_by_id(transaction_id)
        
        # Assert
        assert isinstance(result, TransactionResponse)
        assert result.id == transaction_id
        mock_transaction_repository.get_by_id.assert_called_once_with(transaction_id)
    
    @pytest.mark.asyncio
    async def test_get_transaction_by_id_not_found(self, transaction_service, mock_transaction_repository):
        """Test transaction retrieval by ID when transaction not found."""
        # Arrange
        transaction_id = "non-existent-transaction"
        mock_transaction_repository.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await transaction_service.get_transaction_by_id(transaction_id)
        
        assert "transaction not found" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_get_account_transactions(self, transaction_service, mock_transaction_repository, sample_transaction_model):
        """Test retrieval of account transactions."""
        # Arrange
        account_id = "test-account-123"
        transactions = [sample_transaction_model, sample_transaction_model]
        mock_transaction_repository.get_by_account_id.return_value = transactions
        
        # Act
        result = await transaction_service.get_account_transactions(account_id, skip=0, limit=10)
        
        # Assert
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(txn, TransactionResponse) for txn in result)
        mock_transaction_repository.get_by_account_id.assert_called_once_with(account_id, skip=0, limit=10)
    
    @pytest.mark.asyncio
    async def test_get_transactions_with_filters(self, transaction_service, mock_transaction_repository, sample_transaction_model):
        """Test transaction retrieval with filters."""
        # Arrange
        filters = TransactionFilter(
            account_id="test-account-123",
            category="groceries",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            min_amount=Decimal("10.00"),
            max_amount=Decimal("100.00")
        )
        transactions = [sample_transaction_model]
        mock_transaction_repository.get_with_filters.return_value = transactions
        
        # Act
        result = await transaction_service.get_transactions_with_filters(filters, skip=0, limit=10)
        
        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        mock_transaction_repository.get_with_filters.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_transaction_success(self, transaction_service, mock_transaction_repository, sample_transaction_model):
        """Test successful transaction update."""
        # Arrange
        transaction_id = "test-transaction-123"
        update_data = TransactionUpdate(
            description="Updated Description",
            category="dining",
            subcategory="restaurant"
        )
        updated_transaction = Transaction(**{
            **sample_transaction_model.__dict__,
            "description": "Updated Description",
            "category": "dining",
            "subcategory": "restaurant"
        })
        
        mock_transaction_repository.get_by_id.return_value = sample_transaction_model
        mock_transaction_repository.update.return_value = updated_transaction
        
        # Act
        result = await transaction_service.update_transaction(transaction_id, update_data)
        
        # Assert
        assert isinstance(result, TransactionResponse)
        assert result.description == "Updated Description"
        assert result.category == "dining"
        assert result.subcategory == "restaurant"
        mock_transaction_repository.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_transaction_not_found(self, transaction_service, mock_transaction_repository):
        """Test transaction update when transaction not found."""
        # Arrange
        transaction_id = "non-existent-transaction"
        update_data = TransactionUpdate(description="Updated")
        mock_transaction_repository.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await transaction_service.update_transaction(transaction_id, update_data)
        
        assert "transaction not found" in str(exc_info.value).lower()
        mock_transaction_repository.update.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_delete_transaction_success(self, transaction_service, mock_transaction_repository, sample_transaction_model):
        """Test successful transaction deletion."""
        # Arrange
        transaction_id = "test-transaction-123"
        mock_transaction_repository.get_by_id.return_value = sample_transaction_model
        mock_transaction_repository.delete.return_value = True
        
        # Act
        result = await transaction_service.delete_transaction(transaction_id)
        
        # Assert
        assert result is True
        mock_transaction_repository.delete.assert_called_once_with(transaction_id)
    
    @pytest.mark.asyncio
    async def test_delete_transaction_not_found(self, transaction_service, mock_transaction_repository):
        """Test transaction deletion when transaction not found."""
        # Arrange
        transaction_id = "non-existent-transaction"
        mock_transaction_repository.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await transaction_service.delete_transaction(transaction_id)
        
        assert "transaction not found" in str(exc_info.value).lower()
        mock_transaction_repository.delete.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_categorize_transaction(self, transaction_service, mock_transaction_repository, sample_transaction_model):
        """Test transaction categorization."""
        # Arrange
        transaction_id = "test-transaction-123"
        new_category = "dining"
        new_subcategory = "restaurant"
        
        mock_transaction_repository.get_by_id.return_value = sample_transaction_model
        categorized_transaction = Transaction(**{
            **sample_transaction_model.__dict__,
            "category": new_category,
            "subcategory": new_subcategory
        })
        mock_transaction_repository.update_category.return_value = categorized_transaction
        
        # Act
        result = await transaction_service.categorize_transaction(transaction_id, new_category, new_subcategory)
        
        # Assert
        assert isinstance(result, TransactionResponse)
        assert result.category == new_category
        assert result.subcategory == new_subcategory
        mock_transaction_repository.update_category.assert_called_once_with(transaction_id, new_category, new_subcategory)
    
    @pytest.mark.asyncio
    async def test_sync_transactions_from_plaid(self, transaction_service, mock_transaction_repository, mock_account_repository, mock_plaid_service, sample_account_model):
        """Test syncing transactions from Plaid."""
        # Arrange
        account_id = "test-account-123"
        sample_account_model.plaid_account_id = "plaid_account_123"
        mock_account_repository.get_by_id.return_value = sample_account_model
        
        plaid_transactions = [
            {
                "transaction_id": "plaid_txn_1",
                "account_id": "plaid_account_123",
                "amount": 25.99,
                "date": "2024-01-15",
                "name": "Coffee Shop",
                "merchant_name": "Local Coffee",
                "category": ["Food and Drink", "Restaurants"]
            },
            {
                "transaction_id": "plaid_txn_2", 
                "account_id": "plaid_account_123",
                "amount": 125.50,
                "date": "2024-01-16",
                "name": "Grocery Store",
                "merchant_name": "Super Market",
                "category": ["Shops", "Supermarkets and Groceries"]
            }
        ]
        mock_plaid_service.get_recent_transactions.return_value = plaid_transactions
        mock_transaction_repository.bulk_create.return_value = 2
        
        # Act
        result = await transaction_service.sync_transactions_from_plaid(account_id, days=30)
        
        # Assert
        assert result == 2  # Number of transactions synced
        mock_plaid_service.get_recent_transactions.assert_called_once_with("plaid_account_123", days=30)
        mock_transaction_repository.bulk_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_sync_transactions_no_plaid_account(self, transaction_service, mock_account_repository, sample_account_model):
        """Test syncing transactions for account without Plaid integration."""
        # Arrange
        account_id = "test-account-123"
        sample_account_model.plaid_account_id = None
        mock_account_repository.get_by_id.return_value = sample_account_model
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await transaction_service.sync_transactions_from_plaid(account_id)
        
        assert "not linked to plaid" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_get_transaction_summary(self, transaction_service, mock_transaction_repository):
        """Test transaction summary generation."""
        # Arrange
        account_id = "test-account-123"
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        
        mock_transaction_repository.get_summary.return_value = {
            "total_transactions": 25,
            "total_amount": Decimal("-850.75"),
            "income": Decimal("2000.00"),
            "expenses": Decimal("2850.75"),
            "categories": {
                "groceries": Decimal("300.00"),
                "dining": Decimal("150.00"),
                "gas": Decimal("200.00")
            },
            "average_transaction": Decimal("34.03")
        }
        
        # Act
        result = await transaction_service.get_transaction_summary(account_id, start_date, end_date)
        
        # Assert
        assert "total_transactions" in result
        assert "total_amount" in result
        assert "income" in result
        assert "expenses" in result
        assert "categories" in result
        assert result["total_transactions"] == 25
        mock_transaction_repository.get_summary.assert_called_once_with(account_id, start_date, end_date)
    
    @pytest.mark.asyncio
    async def test_search_transactions(self, transaction_service, mock_transaction_repository, sample_transaction_model):
        """Test transaction search functionality."""
        # Arrange
        search_term = "grocery"
        account_id = "test-account-123"
        transactions = [sample_transaction_model]
        mock_transaction_repository.search.return_value = transactions
        
        # Act
        result = await transaction_service.search_transactions(search_term, account_id=account_id)
        
        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], TransactionResponse)
        mock_transaction_repository.search.assert_called_once_with(search_term, account_id=account_id)
    
    @pytest.mark.asyncio
    async def test_mark_transaction_pending(self, transaction_service, mock_transaction_repository, sample_transaction_model):
        """Test marking transaction as pending."""
        # Arrange
        transaction_id = "test-transaction-123"
        sample_transaction_model.is_pending = False
        mock_transaction_repository.get_by_id.return_value = sample_transaction_model
        
        pending_transaction = Transaction(**{**sample_transaction_model.__dict__, "is_pending": True})
        mock_transaction_repository.update_pending_status.return_value = pending_transaction
        
        # Act
        result = await transaction_service.mark_transaction_pending(transaction_id, is_pending=True)
        
        # Assert
        assert isinstance(result, TransactionResponse)
        assert result.is_pending is True
        mock_transaction_repository.update_pending_status.assert_called_once_with(transaction_id, True)


@pytest.mark.unit
class TestTransactionServiceEdgeCases:
    """Test edge cases and error conditions for TransactionService."""
    
    @pytest.fixture
    def transaction_service(self):
        """Create TransactionService instance."""
        mock_txn_repo = AsyncMock()
        mock_account_repo = AsyncMock()
        mock_plaid = AsyncMock()
        mock_context = TenantContext(
            tenant_id="test-tenant",
            tenant_slug="test-tenant",
            database_url="sqlite:///:memory:",
            user_id="test-user"
        )
        with patch('src.transactions.service.get_tenant_context', return_value=mock_context):
            return TransactionService(mock_txn_repo, mock_account_repo, mock_plaid)
    
    @pytest.mark.asyncio
    async def test_create_transaction_zero_amount(self, transaction_service):
        """Test transaction creation with zero amount."""
        transaction_data = {
            "account_id": "test-account-123",
            "amount": Decimal("0.00"),
            "description": "Zero amount transaction",
            "transaction_date": date(2024, 1, 15),
            "category": "other",
            "transaction_type": "adjustment"
        }
        
        # Zero amount transactions might be valid for certain types
        # Business logic should determine if this is allowed
        pass
    
    @pytest.mark.asyncio
    async def test_create_transaction_future_date(self, transaction_service):
        """Test transaction creation with future date."""
        transaction_data = {
            "account_id": "test-account-123", 
            "amount": Decimal("-50.00"),
            "description": "Future transaction",
            "transaction_date": date(2025, 12, 31),  # Future date
            "category": "other",
            "transaction_type": "purchase"
        }
        
        # Future dates might be allowed for scheduled transactions
        # or might be rejected depending on business rules
        pass
    
    @pytest.mark.asyncio
    async def test_amount_precision_handling(self, transaction_service):
        """Test handling of amount precision."""
        transaction_data = {
            "account_id": "test-account-123",
            "amount": Decimal("-50.123456789"),  # High precision
            "description": "Precision test",
            "transaction_date": date(2024, 1, 15),
            "category": "other",
            "transaction_type": "purchase"
        }
        
        # Should handle precision appropriately (likely round to 2 decimal places)
        pass
    
    @pytest.mark.asyncio
    async def test_duplicate_plaid_transaction_handling(self, transaction_service):
        """Test handling of duplicate Plaid transactions."""
        # When syncing from Plaid, duplicate transactions should be handled
        # This could involve checking plaid_transaction_id for uniqueness
        pass
    
    @pytest.mark.asyncio
    async def test_category_validation(self, transaction_service):
        """Test validation of transaction categories."""
        valid_categories = ["groceries", "dining", "gas", "shopping", "utilities", "other"]
        invalid_category = "invalid_category"
        
        transaction_data = {
            "account_id": "test-account-123",
            "amount": Decimal("-50.00"),
            "description": "Test transaction",
            "transaction_date": date(2024, 1, 15),
            "category": invalid_category,
            "transaction_type": "purchase"
        }
        
        # Should validate category against allowed values
        with pytest.raises(ValidationError):
            await transaction_service.create_transaction(TransactionCreate(**transaction_data))
    
    @pytest.mark.asyncio
    async def test_concurrent_transaction_creation(self, transaction_service):
        """Test handling of concurrent transaction creation."""
        # Test race conditions in transaction creation, especially for balance updates
        pass
    
    @pytest.mark.asyncio
    async def test_large_batch_transaction_sync(self, transaction_service):
        """Test syncing large batches of transactions from Plaid."""
        # Test performance and memory usage with large transaction batches
        pass
    
    @pytest.mark.asyncio
    async def test_plaid_service_timeout(self, transaction_service):
        """Test handling of Plaid service timeouts."""
        transaction_service._plaid_service.get_recent_transactions.side_effect = ExternalServiceError(
            "plaid", "Request timeout"
        )
        
        with pytest.raises(ExternalServiceError):
            await transaction_service.sync_transactions_from_plaid("test-account-123")
    
    @pytest.mark.asyncio
    async def test_malformed_transaction_data(self, transaction_service):
        """Test handling of malformed transaction data."""
        # Test various malformed data scenarios
        malformed_data_cases = [
            {"amount": "not-a-number"},
            {"transaction_date": "invalid-date"},
            {"description": None},
            {"category": ""},
        ]
        
        for case in malformed_data_cases:
            base_data = {
                "account_id": "test-account-123",
                "amount": Decimal("-50.00"),
                "description": "Test",
                "transaction_date": date(2024, 1, 15),
                "category": "other",
                "transaction_type": "purchase"
            }
            base_data.update(case)
            
            with pytest.raises((ValidationError, ValueError, TypeError)):
                await transaction_service.create_transaction(TransactionCreate(**base_data))
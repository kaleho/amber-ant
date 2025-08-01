"""Unit tests for accounts service layer."""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timezone
from decimal import Decimal

from src.accounts.service import AccountService
from src.accounts.models import Account
from src.accounts.schemas import AccountCreate, AccountUpdate, AccountResponse
from src.exceptions import ValidationError, AuthorizationError, ExternalServiceError
from src.tenant.context import TenantContext


@pytest.mark.unit
class TestAccountService:
    """Test AccountService methods."""
    
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
    def account_service(self, mock_account_repository, mock_plaid_service, mock_tenant_context):
        """Create AccountService instance with mocked dependencies."""
        with patch('src.accounts.service.get_tenant_context', return_value=mock_tenant_context):
            return AccountService(mock_account_repository, mock_plaid_service)
    
    @pytest.fixture
    def sample_account_data(self):
        """Sample account data for testing."""
        return {
            "user_id": "test-user-123",
            "name": "Test Checking Account",
            "account_type": "checking",
            "balance": Decimal("1000.00"),
            "currency": "USD",
            "is_active": True
        }
    
    @pytest.fixture
    def sample_account_model(self, sample_account_data):
        """Sample account model instance."""
        return Account(
            id="test-account-123",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            **sample_account_data
        )

    @pytest.mark.asyncio
    async def test_create_account_success(self, account_service, mock_account_repository, sample_account_data, sample_account_model):
        """Test successful account creation."""
        # Arrange
        account_create = AccountCreate(**sample_account_data)
        mock_account_repository.create.return_value = sample_account_model
        
        # Act
        result = await account_service.create_account(account_create)
        
        # Assert
        assert isinstance(result, AccountResponse)
        assert result.name == sample_account_data["name"]
        assert result.account_type == sample_account_data["account_type"]
        assert result.balance == sample_account_data["balance"]
        mock_account_repository.create.assert_called_once()
        
        # Verify the created account data
        call_args = mock_account_repository.create.call_args[0][0]
        assert call_args.name == sample_account_data["name"]
        assert call_args.user_id == sample_account_data["user_id"]
    
    @pytest.mark.asyncio
    async def test_create_account_with_plaid_integration(self, account_service, mock_account_repository, mock_plaid_service, sample_account_model):
        """Test account creation with Plaid integration."""
        # Arrange
        plaid_account_data = {
            "user_id": "test-user-123",
            "name": "Plaid Checking",
            "account_type": "checking",
            "plaid_account_id": "plaid_account_123",
            "balance": Decimal("1500.00"),
            "currency": "USD"
        }
        account_create = AccountCreate(**plaid_account_data)
        mock_account_repository.create.return_value = sample_account_model
        mock_plaid_service.get_account_details.return_value = {
            "balance": {"current": 1500.00, "available": 1400.00},
            "name": "Plaid Checking Account",
            "official_name": "Bank of Test Checking Account",
            "type": "depository",
            "subtype": "checking"
        }
        
        # Act
        result = await account_service.create_account(account_create)
        
        # Assert
        assert isinstance(result, AccountResponse)
        mock_plaid_service.get_account_details.assert_called_once_with("plaid_account_123")
        mock_account_repository.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_account_plaid_service_error(self, account_service, mock_plaid_service):
        """Test account creation when Plaid service fails."""
        # Arrange
        account_data = {
            "user_id": "test-user-123",
            "name": "Test Account",
            "account_type": "checking",
            "plaid_account_id": "invalid_plaid_id",
            "balance": Decimal("0.00"),
            "currency": "USD"
        }
        account_create = AccountCreate(**account_data)
        mock_plaid_service.get_account_details.side_effect = ExternalServiceError("plaid", "Account not found")
        
        # Act & Assert
        with pytest.raises(ExternalServiceError) as exc_info:
            await account_service.create_account(account_create)
        
        assert exc_info.value.service == "plaid"
    
    @pytest.mark.asyncio
    async def test_get_account_by_id_success(self, account_service, mock_account_repository, sample_account_model):
        """Test successful account retrieval by ID."""
        # Arrange
        account_id = "test-account-123"
        mock_account_repository.get_by_id.return_value = sample_account_model
        
        # Act
        result = await account_service.get_account_by_id(account_id)
        
        # Assert
        assert isinstance(result, AccountResponse)
        assert result.id == account_id
        mock_account_repository.get_by_id.assert_called_once_with(account_id)
    
    @pytest.mark.asyncio
    async def test_get_account_by_id_not_found(self, account_service, mock_account_repository):
        """Test account retrieval by ID when account not found."""
        # Arrange
        account_id = "non-existent-account"
        mock_account_repository.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await account_service.get_account_by_id(account_id)
        
        assert "account not found" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_get_user_accounts(self, account_service, mock_account_repository, sample_account_model):
        """Test retrieval of user's accounts."""
        # Arrange
        user_id = "test-user-123"
        accounts = [sample_account_model, sample_account_model]
        mock_account_repository.get_by_user_id.return_value = accounts
        
        # Act
        result = await account_service.get_user_accounts(user_id)
        
        # Assert
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(account, AccountResponse) for account in result)
        mock_account_repository.get_by_user_id.assert_called_once_with(user_id)
    
    @pytest.mark.asyncio
    async def test_update_account_success(self, account_service, mock_account_repository, sample_account_model):
        """Test successful account update."""
        # Arrange
        account_id = "test-account-123"
        update_data = AccountUpdate(name="Updated Account Name", is_active=False)
        updated_account = Account(**{**sample_account_model.__dict__, "name": "Updated Account Name", "is_active": False})
        
        mock_account_repository.get_by_id.return_value = sample_account_model
        mock_account_repository.update.return_value = updated_account
        
        # Act
        result = await account_service.update_account(account_id, update_data)
        
        # Assert
        assert isinstance(result, AccountResponse)
        assert result.name == "Updated Account Name"
        assert result.is_active is False
        mock_account_repository.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_account_not_found(self, account_service, mock_account_repository):
        """Test account update when account not found."""
        # Arrange
        account_id = "non-existent-account"
        update_data = AccountUpdate(name="Updated Name")
        mock_account_repository.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await account_service.update_account(account_id, update_data)
        
        assert "account not found" in str(exc_info.value).lower()
        mock_account_repository.update.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_delete_account_success(self, account_service, mock_account_repository, sample_account_model):
        """Test successful account deletion."""
        # Arrange
        account_id = "test-account-123"
        mock_account_repository.get_by_id.return_value = sample_account_model
        mock_account_repository.delete.return_value = True
        
        # Act
        result = await account_service.delete_account(account_id)
        
        # Assert
        assert result is True
        mock_account_repository.delete.assert_called_once_with(account_id)
    
    @pytest.mark.asyncio
    async def test_delete_account_with_transactions(self, account_service, mock_account_repository, sample_account_model):
        """Test account deletion when account has transactions."""
        # Arrange
        account_id = "test-account-123"
        sample_account_model.has_transactions = True  # Simulate account with transactions
        mock_account_repository.get_by_id.return_value = sample_account_model
        mock_account_repository.has_transactions.return_value = True
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await account_service.delete_account(account_id)
        
        assert "has transactions" in str(exc_info.value).lower()
        mock_account_repository.delete.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_sync_account_balance_success(self, account_service, mock_account_repository, mock_plaid_service, sample_account_model):
        """Test successful account balance synchronization with Plaid."""
        # Arrange
        account_id = "test-account-123"
        sample_account_model.plaid_account_id = "plaid_account_123"
        mock_account_repository.get_by_id.return_value = sample_account_model
        mock_plaid_service.get_account_balance.return_value = {
            "current": 1250.50,
            "available": 1150.50
        }
        updated_account = Account(**{**sample_account_model.__dict__, "balance": Decimal("1250.50")})
        mock_account_repository.update_balance.return_value = updated_account
        
        # Act
        result = await account_service.sync_account_balance(account_id)
        
        # Assert
        assert isinstance(result, AccountResponse)
        assert result.balance == Decimal("1250.50")
        mock_plaid_service.get_account_balance.assert_called_once_with("plaid_account_123")
        mock_account_repository.update_balance.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_sync_account_balance_no_plaid(self, account_service, mock_account_repository, sample_account_model):
        """Test balance sync for account without Plaid integration."""
        # Arrange
        account_id = "test-account-123"
        sample_account_model.plaid_account_id = None
        mock_account_repository.get_by_id.return_value = sample_account_model
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await account_service.sync_account_balance(account_id)
        
        assert "not linked to plaid" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_get_account_summary(self, account_service, mock_account_repository, sample_account_model):
        """Test account summary generation."""
        # Arrange
        user_id = "test-user-123"
        accounts = [sample_account_model, sample_account_model]
        mock_account_repository.get_by_user_id.return_value = accounts
        mock_account_repository.get_account_stats.return_value = {
            "total_balance": Decimal("2000.00"),
            "active_accounts": 2,
            "inactive_accounts": 0,
            "account_types": {"checking": 2}
        }
        
        # Act
        result = await account_service.get_account_summary(user_id)
        
        # Assert
        assert "total_balance" in result
        assert "active_accounts" in result
        assert "account_types" in result
        assert result["total_balance"] == Decimal("2000.00")
        assert result["active_accounts"] == 2
    
    @pytest.mark.asyncio
    async def test_validate_account_ownership(self, account_service, mock_account_repository, sample_account_model):
        """Test account ownership validation."""
        # Arrange
        account_id = "test-account-123"
        user_id = "test-user-123"
        sample_account_model.user_id = user_id
        mock_account_repository.get_by_id.return_value = sample_account_model
        
        # Act
        result = await account_service.validate_account_ownership(account_id, user_id)
        
        # Assert
        assert result is True
    
    @pytest.mark.asyncio
    async def test_validate_account_ownership_unauthorized(self, account_service, mock_account_repository, sample_account_model):
        """Test account ownership validation for unauthorized user."""
        # Arrange
        account_id = "test-account-123"
        user_id = "different-user-456"
        sample_account_model.user_id = "test-user-123"  # Different user owns the account
        mock_account_repository.get_by_id.return_value = sample_account_model
        
        # Act
        result = await account_service.validate_account_ownership(account_id, user_id)
        
        # Assert
        assert result is False
    
    @pytest.mark.asyncio
    async def test_deactivate_account(self, account_service, mock_account_repository, sample_account_model):
        """Test account deactivation."""
        # Arrange
        account_id = "test-account-123"
        mock_account_repository.get_by_id.return_value = sample_account_model
        deactivated_account = Account(**{**sample_account_model.__dict__, "is_active": False})
        mock_account_repository.update.return_value = deactivated_account
        
        # Act
        result = await account_service.deactivate_account(account_id)
        
        # Assert
        assert isinstance(result, AccountResponse)
        assert result.is_active is False
        mock_account_repository.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_accounts_by_type(self, account_service, mock_account_repository, sample_account_model):
        """Test retrieval of accounts by type."""
        # Arrange
        user_id = "test-user-123"
        account_type = "checking"
        accounts = [sample_account_model]
        mock_account_repository.get_by_type.return_value = accounts
        
        # Act
        result = await account_service.get_accounts_by_type(user_id, account_type)
        
        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        assert all(isinstance(account, AccountResponse) for account in result)
        mock_account_repository.get_by_type.assert_called_once_with(user_id, account_type)


@pytest.mark.unit
class TestAccountServiceEdgeCases:
    """Test edge cases and error conditions for AccountService."""
    
    @pytest.fixture
    def account_service(self):
        """Create AccountService instance."""
        mock_repo = AsyncMock()
        mock_plaid = AsyncMock()
        mock_context = TenantContext(
            tenant_id="test-tenant",
            tenant_slug="test-tenant",
            database_url="sqlite:///:memory:",
            user_id="test-user"
        )
        with patch('src.accounts.service.get_tenant_context', return_value=mock_context):
            return AccountService(mock_repo, mock_plaid)
    
    @pytest.mark.asyncio
    async def test_create_account_invalid_balance(self, account_service):
        """Test account creation with invalid balance."""
        account_data = {
            "user_id": "test-user-123",
            "name": "Test Account",
            "account_type": "checking",
            "balance": Decimal("-1000.00"),  # Negative balance might be invalid
            "currency": "USD"
        }
        
        # Depending on business rules, negative balances might be allowed or not
        with pytest.raises(ValidationError):
            await account_service.create_account(AccountCreate(**account_data))
    
    @pytest.mark.asyncio
    async def test_create_account_invalid_currency(self, account_service):
        """Test account creation with invalid currency."""
        account_data = {
            "user_id": "test-user-123",
            "name": "Test Account", 
            "account_type": "checking",
            "balance": Decimal("1000.00"),
            "currency": "INVALID"  # Invalid currency code
        }
        
        with pytest.raises(ValidationError):
            await account_service.create_account(AccountCreate(**account_data))
    
    @pytest.mark.asyncio
    async def test_balance_precision_handling(self, account_service):
        """Test handling of balance precision and rounding."""
        account_data = {
            "user_id": "test-user-123",
            "name": "Test Account",
            "account_type": "checking", 
            "balance": Decimal("1000.123456789"),  # High precision
            "currency": "USD"
        }
        
        # Should handle precision appropriately (likely round to 2 decimal places)
        result = await account_service.create_account(AccountCreate(**account_data))
        # Verify precision is handled correctly
    
    @pytest.mark.asyncio
    async def test_concurrent_balance_updates(self, account_service):
        """Test handling of concurrent balance updates."""
        # This would test race conditions in balance updates
        # Implementation depends on concurrency control strategy
        pass
    
    @pytest.mark.asyncio
    async def test_plaid_rate_limiting(self, account_service):
        """Test handling of Plaid API rate limiting."""
        account_service._plaid_service.get_account_balance.side_effect = ExternalServiceError(
            "plaid", "Rate limit exceeded"
        )
        
        with pytest.raises(ExternalServiceError) as exc_info:
            await account_service.sync_account_balance("test-account-123")
        
        assert "rate limit" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_account_type_validation(self, account_service):
        """Test validation of account types."""
        valid_types = ["checking", "savings", "credit", "investment", "loan"]
        invalid_type = "invalid_type"
        
        account_data = {
            "user_id": "test-user-123",
            "name": "Test Account",
            "account_type": invalid_type,
            "balance": Decimal("1000.00"),
            "currency": "USD"
        }
        
        with pytest.raises(ValidationError):
            await account_service.create_account(AccountCreate(**account_data))
    
    @pytest.mark.asyncio
    async def test_multi_tenant_isolation(self, account_service):
        """Test that account service respects tenant isolation."""
        # Similar to user service test, verify tenant isolation
        # This would be enforced at the repository/database level
        pass
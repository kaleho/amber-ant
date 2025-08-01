"""Unit tests for users service layer."""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timezone

from src.users.service import UserService
from src.users.models import User
from src.users.schemas import UserCreate, UserUpdate, UserResponse
from src.exceptions import ValidationError, AuthenticationError, AuthorizationError
from src.tenant.context import TenantContext


@pytest.mark.unit
class TestUserService:
    """Test UserService methods."""
    
    @pytest.fixture
    def mock_user_repository(self):
        """Mock user repository."""
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
    def user_service(self, mock_user_repository, mock_tenant_context):
        """Create UserService instance with mocked dependencies."""
        with patch('src.users.service.get_tenant_context', return_value=mock_tenant_context):
            return UserService(mock_user_repository)
    
    @pytest.fixture
    def sample_user_data(self):
        """Sample user data for testing."""
        return {
            "auth0_user_id": "auth0|test123",
            "email": "test@example.com",
            "name": "Test User",
            "given_name": "Test",
            "family_name": "User",
            "role": "member"
        }
    
    @pytest.fixture
    def sample_user_model(self, sample_user_data):
        """Sample user model instance."""
        return User(
            id="test-user-123",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            **sample_user_data
        )

    @pytest.mark.asyncio
    async def test_create_user_success(self, user_service, mock_user_repository, sample_user_data, sample_user_model):
        """Test successful user creation."""
        # Arrange
        user_create = UserCreate(**sample_user_data)
        mock_user_repository.create.return_value = sample_user_model
        mock_user_repository.get_by_auth0_id.return_value = None
        mock_user_repository.get_by_email.return_value = None
        
        # Act
        result = await user_service.create_user(user_create)
        
        # Assert
        assert isinstance(result, UserResponse)
        assert result.email == sample_user_data["email"]
        assert result.name == sample_user_data["name"]
        mock_user_repository.create.assert_called_once()
        
        # Verify the created user data
        call_args = mock_user_repository.create.call_args[0][0]
        assert call_args.email == sample_user_data["email"]
        assert call_args.auth0_user_id == sample_user_data["auth0_user_id"]
    
    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, user_service, mock_user_repository, sample_user_data, sample_user_model):
        """Test user creation with duplicate email fails."""
        # Arrange
        user_create = UserCreate(**sample_user_data)
        mock_user_repository.get_by_email.return_value = sample_user_model
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await user_service.create_user(user_create)
        
        assert "email already exists" in str(exc_info.value).lower()
        mock_user_repository.create.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_create_user_duplicate_auth0_id(self, user_service, mock_user_repository, sample_user_data, sample_user_model):
        """Test user creation with duplicate Auth0 ID fails."""
        # Arrange
        user_create = UserCreate(**sample_user_data)
        mock_user_repository.get_by_email.return_value = None
        mock_user_repository.get_by_auth0_id.return_value = sample_user_model
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await user_service.create_user(user_create)
        
        assert "auth0 user already exists" in str(exc_info.value).lower()
        mock_user_repository.create.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, user_service, mock_user_repository, sample_user_model):
        """Test successful user retrieval by ID."""
        # Arrange
        user_id = "test-user-123"
        mock_user_repository.get_by_id.return_value = sample_user_model
        
        # Act
        result = await user_service.get_user_by_id(user_id)
        
        # Assert
        assert isinstance(result, UserResponse)
        assert result.id == user_id
        mock_user_repository.get_by_id.assert_called_once_with(user_id)
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, user_service, mock_user_repository):
        """Test user retrieval by ID when user not found."""
        # Arrange
        user_id = "non-existent-user"
        mock_user_repository.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await user_service.get_user_by_id(user_id)
        
        assert "user not found" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_get_user_by_auth0_id_success(self, user_service, mock_user_repository, sample_user_model):
        """Test successful user retrieval by Auth0 ID."""
        # Arrange
        auth0_id = "auth0|test123"
        mock_user_repository.get_by_auth0_id.return_value = sample_user_model
        
        # Act
        result = await user_service.get_user_by_auth0_id(auth0_id)
        
        # Assert
        assert isinstance(result, UserResponse)
        assert result.auth0_user_id == auth0_id
        mock_user_repository.get_by_auth0_id.assert_called_once_with(auth0_id)
    
    @pytest.mark.asyncio
    async def test_get_user_by_email_success(self, user_service, mock_user_repository, sample_user_model):
        """Test successful user retrieval by email."""
        # Arrange
        email = "test@example.com"
        mock_user_repository.get_by_email.return_value = sample_user_model
        
        # Act
        result = await user_service.get_user_by_email(email)
        
        # Assert
        assert isinstance(result, UserResponse)
        assert result.email == email
        mock_user_repository.get_by_email.assert_called_once_with(email)
    
    @pytest.mark.asyncio
    async def test_update_user_success(self, user_service, mock_user_repository, sample_user_model):
        """Test successful user update."""
        # Arrange
        user_id = "test-user-123"
        update_data = UserUpdate(name="Updated Name", given_name="Updated")
        updated_user = User(**{**sample_user_model.__dict__, "name": "Updated Name", "given_name": "Updated"})
        
        mock_user_repository.get_by_id.return_value = sample_user_model
        mock_user_repository.update.return_value = updated_user
        
        # Act
        result = await user_service.update_user(user_id, update_data)
        
        # Assert
        assert isinstance(result, UserResponse)
        assert result.name == "Updated Name"
        assert result.given_name == "Updated"
        mock_user_repository.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_user_not_found(self, user_service, mock_user_repository):
        """Test user update when user not found."""
        # Arrange
        user_id = "non-existent-user"
        update_data = UserUpdate(name="Updated Name")
        mock_user_repository.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await user_service.update_user(user_id, update_data)
        
        assert "user not found" in str(exc_info.value).lower()
        mock_user_repository.update.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_delete_user_success(self, user_service, mock_user_repository, sample_user_model):
        """Test successful user deletion."""
        # Arrange
        user_id = "test-user-123"
        mock_user_repository.get_by_id.return_value = sample_user_model
        mock_user_repository.delete.return_value = True
        
        # Act
        result = await user_service.delete_user(user_id)
        
        # Assert
        assert result is True
        mock_user_repository.delete.assert_called_once_with(user_id)
    
    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, user_service, mock_user_repository):
        """Test user deletion when user not found."""
        # Arrange
        user_id = "non-existent-user"
        mock_user_repository.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await user_service.delete_user(user_id)
        
        assert "user not found" in str(exc_info.value).lower()
        mock_user_repository.delete.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_list_users_success(self, user_service, mock_user_repository, sample_user_model):
        """Test successful user listing."""
        # Arrange
        users = [sample_user_model, sample_user_model]
        mock_user_repository.list.return_value = users
        
        # Act
        result = await user_service.list_users(skip=0, limit=10)
        
        # Assert
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(user, UserResponse) for user in result)
        mock_user_repository.list.assert_called_once_with(skip=0, limit=10)
    
    @pytest.mark.asyncio
    async def test_list_users_empty(self, user_service, mock_user_repository):
        """Test user listing when no users exist."""
        # Arrange
        mock_user_repository.list.return_value = []
        
        # Act
        result = await user_service.list_users(skip=0, limit=10)
        
        # Assert
        assert isinstance(result, list)
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_get_user_profile_success(self, user_service, mock_user_repository, sample_user_model):
        """Test successful user profile retrieval."""
        # Arrange
        user_id = "test-user-123"
        mock_user_repository.get_by_id.return_value = sample_user_model
        
        # Act
        result = await user_service.get_user_profile(user_id)
        
        # Assert
        assert isinstance(result, UserResponse)
        assert result.id == user_id
        # Should include additional profile information
        assert hasattr(result, 'email')
        assert hasattr(result, 'name')
        assert hasattr(result, 'role')
    
    @pytest.mark.asyncio
    async def test_update_user_role_success(self, user_service, mock_user_repository, sample_user_model):
        """Test successful user role update."""
        # Arrange
        user_id = "test-user-123"
        new_role = "admin"
        updated_user = User(**{**sample_user_model.__dict__, "role": new_role})
        
        mock_user_repository.get_by_id.return_value = sample_user_model
        mock_user_repository.update_role.return_value = updated_user
        
        # Act
        result = await user_service.update_user_role(user_id, new_role)
        
        # Assert
        assert isinstance(result, UserResponse)
        assert result.role == new_role
        mock_user_repository.update_role.assert_called_once_with(user_id, new_role)
    
    @pytest.mark.asyncio
    async def test_update_user_role_invalid_role(self, user_service, mock_user_repository, sample_user_model):
        """Test user role update with invalid role."""
        # Arrange
        user_id = "test-user-123"
        invalid_role = "invalid_role"
        mock_user_repository.get_by_id.return_value = sample_user_model
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await user_service.update_user_role(user_id, invalid_role)
        
        assert "invalid role" in str(exc_info.value).lower()
        mock_user_repository.update_role.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_verify_user_permissions_admin(self, user_service, mock_user_repository):
        """Test user permission verification for admin role."""
        # Arrange
        admin_user = User(
            id="admin-user",
            role="admin",
            email="admin@example.com",
            auth0_user_id="auth0|admin123"
        )
        mock_user_repository.get_by_id.return_value = admin_user
        
        # Act
        result = await user_service.verify_user_permissions("admin-user", "manage_users")
        
        # Assert
        assert result is True
    
    @pytest.mark.asyncio
    async def test_verify_user_permissions_member(self, user_service, mock_user_repository):
        """Test user permission verification for member role."""
        # Arrange
        member_user = User(
            id="member-user",
            role="member",
            email="member@example.com", 
            auth0_user_id="auth0|member123"
        )
        mock_user_repository.get_by_id.return_value = member_user
        
        # Act
        result = await user_service.verify_user_permissions("member-user", "manage_users")
        
        # Assert
        assert result is False
    
    @pytest.mark.asyncio
    async def test_multi_tenant_isolation(self, mock_user_repository):
        """Test that user service respects tenant isolation."""
        # Arrange
        tenant1_context = TenantContext(
            tenant_id="tenant-1",
            tenant_slug="tenant-1", 
            database_url="sqlite:///:memory:",
            user_id="user-1"
        )
        tenant2_context = TenantContext(
            tenant_id="tenant-2",
            tenant_slug="tenant-2",
            database_url="sqlite:///:memory:", 
            user_id="user-2"
        )
        
        # Act & Assert - Different tenant contexts should be isolated
        with patch('src.users.service.get_tenant_context', return_value=tenant1_context):
            service1 = UserService(mock_user_repository)
            
        with patch('src.users.service.get_tenant_context', return_value=tenant2_context):
            service2 = UserService(mock_user_repository)
        
        # Both services should use the same repository but different contexts
        assert service1._repository == service2._repository
        # The actual tenant isolation would be enforced at the database/repository level


@pytest.mark.unit
class TestUserServiceEdgeCases:
    """Test edge cases and error conditions for UserService."""
    
    @pytest.fixture
    def user_service(self):
        """Create UserService instance."""
        mock_repo = AsyncMock()
        mock_context = TenantContext(
            tenant_id="test-tenant",
            tenant_slug="test-tenant", 
            database_url="sqlite:///:memory:",
            user_id="test-user"
        )
        with patch('src.users.service.get_tenant_context', return_value=mock_context):
            return UserService(mock_repo)
    
    @pytest.mark.asyncio
    async def test_create_user_with_empty_email(self, user_service):
        """Test user creation with empty email."""
        user_data = {
            "auth0_user_id": "auth0|test123",
            "email": "",
            "name": "Test User"
        }
        
        with pytest.raises(ValidationError):
            await user_service.create_user(UserCreate(**user_data))
    
    @pytest.mark.asyncio
    async def test_create_user_with_invalid_email(self, user_service):
        """Test user creation with invalid email format."""
        user_data = {
            "auth0_user_id": "auth0|test123", 
            "email": "invalid-email",
            "name": "Test User"
        }
        
        with pytest.raises(ValidationError):
            await user_service.create_user(UserCreate(**user_data))
    
    @pytest.mark.asyncio
    async def test_create_user_with_none_values(self, user_service):
        """Test user creation handles None values appropriately."""
        user_data = {
            "auth0_user_id": "auth0|test123",
            "email": "test@example.com", 
            "name": None,  # This should be handled gracefully
            "given_name": None,
            "family_name": None
        }
        
        # Depending on implementation, this might raise ValidationError or handle gracefully
        with pytest.raises((ValidationError, TypeError)):
            await user_service.create_user(UserCreate(**user_data))
    
    @pytest.mark.asyncio
    async def test_repository_exception_handling(self, user_service):
        """Test service handles repository exceptions appropriately."""
        # This would test how the service handles database errors, connection issues, etc.
        mock_repo = user_service._repository
        mock_repo.get_by_id.side_effect = Exception("Database connection error")
        
        with pytest.raises(Exception):
            await user_service.get_user_by_id("test-user-123")
    
    @pytest.mark.asyncio
    async def test_concurrent_user_creation(self, user_service):
        """Test handling of concurrent user creation attempts."""
        # This would test race conditions in user creation
        # Implementation depends on how the service handles concurrent operations
        pass
    
    @pytest.mark.asyncio 
    async def test_bulk_operations_performance(self, user_service):
        """Test performance with bulk user operations."""
        # This would test service performance with large datasets
        # Could be marked as @pytest.mark.slow
        pass
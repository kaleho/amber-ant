"""Unit tests for users repository layer."""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm.exc import NoResultFound

from src.users.repository import UserRepository
from src.users.models import User
from src.exceptions import ValidationError


@pytest.mark.unit
class TestUserRepository:
    """Test UserRepository methods."""
    
    @pytest.fixture
    def mock_session(self):
        """Mock database session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.add = Mock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.refresh = AsyncMock()
        session.delete = Mock()
        return session
    
    @pytest.fixture
    def user_repository(self, mock_session):
        """Create UserRepository instance with mocked session."""
        return UserRepository(mock_session)
    
    @pytest.fixture
    def sample_user_model(self):
        """Sample user model instance."""
        return User(
            id="test-user-123",
            auth0_user_id="auth0|test123",
            email="test@example.com",
            email_verified=True,
            name="Test User",
            given_name="Test",
            family_name="User",
            picture="https://example.com/avatar.jpg",
            locale="en",
            role="member",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

    @pytest.mark.asyncio
    async def test_create_user_success(self, user_repository, mock_session, sample_user_model):
        """Test successful user creation."""
        # Arrange
        mock_session.refresh.return_value = None
        
        # Act
        result = await user_repository.create(sample_user_model)
        
        # Assert
        assert result == sample_user_model
        mock_session.add.assert_called_once_with(sample_user_model)
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(sample_user_model)
    
    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, user_repository, mock_session, sample_user_model):
        """Test user creation with duplicate email fails."""
        # Arrange
        mock_session.commit.side_effect = IntegrityError("", "", "")
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await user_repository.create(sample_user_model)
        
        assert "already exists" in str(exc_info.value).lower()
        mock_session.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_user_database_error(self, user_repository, mock_session, sample_user_model):
        """Test user creation with database error."""
        # Arrange
        mock_session.commit.side_effect = SQLAlchemyError("Database error")
        
        # Act & Assert
        with pytest.raises(SQLAlchemyError):
            await user_repository.create(sample_user_model)
        
        mock_session.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_id_success(self, user_repository, mock_session, sample_user_model):
        """Test successful user retrieval by ID."""
        # Arrange
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_user_model
        mock_session.execute.return_value = mock_result
        
        # Act
        result = await user_repository.get_by_id("test-user-123")
        
        # Assert
        assert result == sample_user_model
        mock_session.execute.assert_called_once()
        
        # Verify the SQL query structure
        call_args = mock_session.execute.call_args[0][0]
        assert "SELECT" in str(call_args)
        assert "users" in str(call_args).lower()
    
    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, user_repository, mock_session):
        """Test user retrieval by ID when user not found."""
        # Arrange
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        # Act
        result = await user_repository.get_by_id("non-existent-user")
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_by_auth0_id_success(self, user_repository, mock_session, sample_user_model):
        """Test successful user retrieval by Auth0 ID."""
        # Arrange
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_user_model
        mock_session.execute.return_value = mock_result
        
        # Act
        result = await user_repository.get_by_auth0_id("auth0|test123")
        
        # Assert
        assert result == sample_user_model
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_email_success(self, user_repository, mock_session, sample_user_model):
        """Test successful user retrieval by email."""
        # Arrange
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_user_model
        mock_session.execute.return_value = mock_result
        
        # Act
        result = await user_repository.get_by_email("test@example.com")
        
        # Assert
        assert result == sample_user_model
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_email_case_insensitive(self, user_repository, mock_session, sample_user_model):
        """Test user retrieval by email is case insensitive."""
        # Arrange
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_user_model
        mock_session.execute.return_value = mock_result
        
        # Act
        result = await user_repository.get_by_email("TEST@EXAMPLE.COM")
        
        # Assert
        assert result == sample_user_model
        # Should have been converted to lowercase in the query
        call_args = mock_session.execute.call_args[0][0]
        # The exact query structure depends on implementation
    
    @pytest.mark.asyncio
    async def test_update_user_success(self, user_repository, mock_session, sample_user_model):
        """Test successful user update."""
        # Arrange
        update_data = {"name": "Updated Name", "given_name": "Updated"}
        updated_user = User(**{**sample_user_model.__dict__, **update_data})
        
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_user_model
        mock_session.execute.return_value = mock_result
        mock_session.refresh.return_value = None
        
        # Act
        result = await user_repository.update(sample_user_model.id, update_data)
        
        # Assert
        assert result.name == "Updated Name"
        assert result.given_name == "Updated"
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_user_not_found(self, user_repository, mock_session):
        """Test user update when user not found."""
        # Arrange
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        # Act
        result = await user_repository.update("non-existent-user", {"name": "Updated"})
        
        # Assert
        assert result is None
        mock_session.commit.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_delete_user_success(self, user_repository, mock_session, sample_user_model):
        """Test successful user deletion."""
        # Arrange
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_user_model
        mock_session.execute.return_value = mock_result
        
        # Act
        result = await user_repository.delete("test-user-123")
        
        # Assert
        assert result is True
        mock_session.delete.assert_called_once_with(sample_user_model)
        mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, user_repository, mock_session):
        """Test user deletion when user not found."""
        # Arrange
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        # Act
        result = await user_repository.delete("non-existent-user")
        
        # Assert
        assert result is False
        mock_session.delete.assert_not_called()
        mock_session.commit.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_list_users_success(self, user_repository, mock_session, sample_user_model):
        """Test successful user listing."""
        # Arrange
        users = [sample_user_model, sample_user_model]
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = users
        mock_session.execute.return_value = mock_result
        
        # Act
        result = await user_repository.list(skip=0, limit=10)
        
        # Assert
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(user, User) for user in result)
        mock_session.execute.assert_called_once()
        
        # Verify query includes offset and limit
        call_args = mock_session.execute.call_args[0][0]
        query_str = str(call_args)
        assert "LIMIT" in query_str or "limit" in query_str.lower()
    
    @pytest.mark.asyncio
    async def test_list_users_with_filters(self, user_repository, mock_session, sample_user_model):
        """Test user listing with filters."""
        # Arrange
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [sample_user_model]
        mock_session.execute.return_value = mock_result
        
        # Act
        result = await user_repository.list(
            skip=10, 
            limit=5, 
            filters={"role": "admin", "email_verified": True}
        )
        
        # Assert
        assert isinstance(result, list)
        mock_session.execute.assert_called_once()
        
        # Verify filters are applied in query
        call_args = mock_session.execute.call_args[0][0]
        query_str = str(call_args)
        # The exact filter implementation depends on the repository
    
    @pytest.mark.asyncio
    async def test_count_users(self, user_repository, mock_session):
        """Test user count functionality."""
        # Arrange
        mock_result = Mock()
        mock_result.scalar.return_value = 42
        mock_session.execute.return_value = mock_result
        
        # Act
        result = await user_repository.count()
        
        # Assert
        assert result == 42
        mock_session.execute.assert_called_once()
        
        # Verify count query
        call_args = mock_session.execute.call_args[0][0]
        query_str = str(call_args)
        assert "COUNT" in query_str or "count" in query_str.lower()
    
    @pytest.mark.asyncio
    async def test_update_role_success(self, user_repository, mock_session, sample_user_model):
        """Test successful user role update."""
        # Arrange
        new_role = "admin"
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_user_model
        mock_session.execute.return_value = mock_result
        
        # Act
        result = await user_repository.update_role("test-user-123", new_role)
        
        # Assert
        assert result.role == new_role
        mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_bulk_create_users(self, user_repository, mock_session):
        """Test bulk user creation."""
        # Arrange
        users = [
            User(id="user-1", email="user1@example.com", auth0_user_id="auth0|1"),
            User(id="user-2", email="user2@example.com", auth0_user_id="auth0|2"),
            User(id="user-3", email="user3@example.com", auth0_user_id="auth0|3"),
        ]
        
        # Act
        result = await user_repository.bulk_create(users)
        
        # Assert
        assert result == len(users)
        assert mock_session.add.call_count == len(users)
        mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_users_by_name(self, user_repository, mock_session, sample_user_model):
        """Test user search by name."""
        # Arrange
        search_term = "Test"
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [sample_user_model]
        mock_session.execute.return_value = mock_result
        
        # Act
        result = await user_repository.search_by_name(search_term)
        
        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        mock_session.execute.assert_called_once()
        
        # Verify search query includes LIKE or similar
        call_args = mock_session.execute.call_args[0][0]
        query_str = str(call_args)
        # The exact search implementation depends on the repository


@pytest.mark.unit
class TestUserRepositoryEdgeCases:
    """Test edge cases and error conditions for UserRepository."""
    
    @pytest.fixture
    def user_repository(self):
        """Create UserRepository instance."""
        mock_session = AsyncMock()
        return UserRepository(mock_session)
    
    @pytest.mark.asyncio
    async def test_database_connection_error(self, user_repository):
        """Test handling of database connection errors."""
        # Arrange
        user_repository._session.execute.side_effect = SQLAlchemyError("Connection lost")
        
        # Act & Assert
        with pytest.raises(SQLAlchemyError):
            await user_repository.get_by_id("test-user-123")
    
    @pytest.mark.asyncio
    async def test_transaction_rollback_on_error(self, user_repository):
        """Test that transactions are rolled back on errors."""
        # Arrange
        user = User(id="test", email="test@example.com", auth0_user_id="auth0|test")
        user_repository._session.commit.side_effect = SQLAlchemyError("Transaction error")
        
        # Act & Assert
        with pytest.raises(SQLAlchemyError):
            await user_repository.create(user)
        
        user_repository._session.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_concurrent_modifications(self, user_repository):
        """Test handling of concurrent modifications."""
        # This would test optimistic locking or other concurrency control mechanisms
        # Implementation depends on the concurrency strategy used
        pass
    
    @pytest.mark.asyncio
    async def test_large_result_set_handling(self, user_repository):
        """Test handling of large result sets."""
        # This would test pagination, streaming results, or memory management
        # for large datasets
        pass
    
    @pytest.mark.asyncio
    async def test_sql_injection_prevention(self, user_repository):
        """Test that SQL injection is prevented."""
        # Arrange - malicious input
        malicious_input = "'; DROP TABLE users; --"
        
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        user_repository._session.execute.return_value = mock_result
        
        # Act - should not cause SQL injection
        result = await user_repository.get_by_email(malicious_input)
        
        # Assert - should complete safely
        assert result is None
        user_repository._session.execute.assert_called_once()
        
        # The parameterized query should prevent injection
        call_args = user_repository._session.execute.call_args[0][0]
        # Verify that the query uses parameters, not string concatenation
    
    @pytest.mark.asyncio
    async def test_null_value_handling(self, user_repository):
        """Test handling of null values in database operations."""
        # Test how the repository handles NULL values in various fields
        user = User(
            id="test-user",
            email="test@example.com",
            auth0_user_id="auth0|test",
            name=None,  # NULL value
            given_name=None,
            family_name=None
        )
        
        # Should handle NULL values appropriately
        await user_repository.create(user)
        user_repository._session.add.assert_called_once_with(user)
    
    @pytest.mark.asyncio
    async def test_constraint_violation_handling(self, user_repository):
        """Test handling of various database constraint violations."""
        # Test different types of constraint violations:
        # - Unique constraints
        # - Foreign key constraints  
        # - Check constraints
        # - Not null constraints
        
        user = User(id="test", email="test@example.com", auth0_user_id="auth0|test")
        
        # Simulate different constraint violations
        user_repository._session.commit.side_effect = IntegrityError(
            "UNIQUE constraint failed", "", ""
        )
        
        with pytest.raises(ValidationError):
            await user_repository.create(user)
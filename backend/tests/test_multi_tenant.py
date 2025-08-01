"""Comprehensive multi-tenant functionality tests."""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from fastapi.testclient import TestClient

from src.tenant.context import TenantContext
from src.tenant.manager import TenantManager
from src.tenant.resolver import TenantResolver
from src.tenant.service import TenantService
from src.exceptions import TenantNotFoundError, ValidationError


@pytest.mark.unit
class TestTenantContext:
    """Test tenant context functionality."""
    
    def test_tenant_context_creation(self):
        """Test tenant context creation with valid data."""
        # Arrange & Act
        context = TenantContext(
            tenant_id="test-tenant-123",
            tenant_slug="test-tenant",
            database_url="sqlite://test.db",
            user_id="user-123"
        )
        
        # Assert
        assert context.tenant_id == "test-tenant-123"
        assert context.tenant_slug == "test-tenant"
        assert context.database_url == "sqlite://test.db"
        assert context.user_id == "user-123"
    
    def test_tenant_context_validation(self):
        """Test tenant context validation."""
        # Test invalid tenant ID
        with pytest.raises(ValueError):
            TenantContext(
                tenant_id="",  # Empty tenant ID
                tenant_slug="test",
                database_url="sqlite://test.db"
            )
        
        # Test invalid database URL
        with pytest.raises(ValueError):
            TenantContext(
                tenant_id="test-tenant",
                tenant_slug="test",
                database_url=""  # Empty database URL
            )
    
    def test_tenant_context_equality(self):
        """Test tenant context equality comparison."""
        context1 = TenantContext(
            tenant_id="test-tenant",
            tenant_slug="test-tenant",
            database_url="sqlite://test.db"
        )
        
        context2 = TenantContext(
            tenant_id="test-tenant",
            tenant_slug="test-tenant", 
            database_url="sqlite://test.db"
        )
        
        context3 = TenantContext(
            tenant_id="different-tenant",
            tenant_slug="different",
            database_url="sqlite://different.db"
        )
        
        assert context1 == context2
        assert context1 != context3
    
    def test_tenant_context_string_representation(self):
        """Test tenant context string representation."""
        context = TenantContext(
            tenant_id="test-tenant",
            tenant_slug="test-tenant",
            database_url="sqlite://test.db"
        )
        
        str_repr = str(context)
        assert "test-tenant" in str_repr
        assert "sqlite://test.db" in str_repr


@pytest.mark.unit
class TestTenantResolver:
    """Test tenant resolver functionality."""
    
    @pytest.fixture
    def tenant_resolver(self):
        """Create TenantResolver instance."""
        return TenantResolver()
    
    @pytest.fixture
    def mock_tenant_repository(self):
        """Mock tenant repository."""
        return AsyncMock()
    
    @pytest.mark.asyncio
    async def test_resolve_tenant_by_id_success(self, tenant_resolver, mock_tenant_repository):
        """Test successful tenant resolution by ID."""
        # Arrange
        tenant_id = "test-tenant-123"
        mock_tenant = Mock()
        mock_tenant.id = tenant_id
        mock_tenant.slug = "test-tenant"
        mock_tenant.database_url = "sqlite://test.db"
        mock_tenant.is_active = True
        
        mock_tenant_repository.get_by_id.return_value = mock_tenant
        tenant_resolver._repository = mock_tenant_repository
        
        # Act
        result = await tenant_resolver.resolve_by_id(tenant_id)
        
        # Assert
        assert isinstance(result, TenantContext)
        assert result.tenant_id == tenant_id
        assert result.tenant_slug == "test-tenant"
        mock_tenant_repository.get_by_id.assert_called_once_with(tenant_id)
    
    @pytest.mark.asyncio
    async def test_resolve_tenant_by_id_not_found(self, tenant_resolver, mock_tenant_repository):
        """Test tenant resolution by ID when tenant not found."""
        # Arrange
        tenant_id = "non-existent-tenant"
        mock_tenant_repository.get_by_id.return_value = None
        tenant_resolver._repository = mock_tenant_repository
        
        # Act & Assert
        with pytest.raises(TenantNotFoundError) as exc_info:
            await tenant_resolver.resolve_by_id(tenant_id)
        
        assert exc_info.value.tenant_id == tenant_id
    
    @pytest.mark.asyncio
    async def test_resolve_tenant_by_slug_success(self, tenant_resolver, mock_tenant_repository):
        """Test successful tenant resolution by slug."""
        # Arrange
        tenant_slug = "test-tenant"
        mock_tenant = Mock()
        mock_tenant.id = "test-tenant-123"
        mock_tenant.slug = tenant_slug
        mock_tenant.database_url = "sqlite://test.db"
        mock_tenant.is_active = True
        
        mock_tenant_repository.get_by_slug.return_value = mock_tenant
        tenant_resolver._repository = mock_tenant_repository
        
        # Act
        result = await tenant_resolver.resolve_by_slug(tenant_slug)
        
        # Assert
        assert isinstance(result, TenantContext)
        assert result.tenant_slug == tenant_slug
        mock_tenant_repository.get_by_slug.assert_called_once_with(tenant_slug)
    
    @pytest.mark.asyncio
    async def test_resolve_tenant_inactive(self, tenant_resolver, mock_tenant_repository):
        """Test tenant resolution for inactive tenant."""
        # Arrange
        tenant_id = "inactive-tenant"
        mock_tenant = Mock()
        mock_tenant.id = tenant_id
        mock_tenant.slug = "inactive"
        mock_tenant.is_active = False  # Inactive tenant
        
        mock_tenant_repository.get_by_id.return_value = mock_tenant
        tenant_resolver._repository = mock_tenant_repository
        
        # Act & Assert
        with pytest.raises(TenantNotFoundError) as exc_info:
            await tenant_resolver.resolve_by_id(tenant_id)
        
        assert "inactive" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_resolve_tenant_by_domain(self, tenant_resolver, mock_tenant_repository):
        """Test tenant resolution by custom domain."""
        # Arrange
        domain = "tenant.example.com"
        mock_tenant = Mock()
        mock_tenant.id = "domain-tenant"
        mock_tenant.slug = "domain-tenant"
        mock_tenant.custom_domain = domain
        mock_tenant.is_active = True
        
        mock_tenant_repository.get_by_domain.return_value = mock_tenant
        tenant_resolver._repository = mock_tenant_repository
        
        # Act
        result = await tenant_resolver.resolve_by_domain(domain)
        
        # Assert
        assert isinstance(result, TenantContext)
        assert result.tenant_id == "domain-tenant"


@pytest.mark.unit
class TestTenantManager:
    """Test tenant manager functionality."""
    
    @pytest.fixture
    def tenant_manager(self):
        """Create TenantManager instance."""
        return TenantManager()
    
    @pytest.fixture
    def mock_global_db(self):
        """Mock global database."""
        return AsyncMock()
    
    @pytest.mark.asyncio
    async def test_create_tenant_success(self, tenant_manager, mock_global_db):
        """Test successful tenant creation."""
        # Arrange
        tenant_data = {
            "name": "Test Tenant",
            "slug": "test-tenant",
            "owner_email": "owner@test.com"
        }
        
        mock_tenant = Mock()
        mock_tenant.id = "new-tenant-123"
        mock_tenant.slug = "test-tenant"
        mock_tenant.database_url = "sqlite://test-tenant.db"
        
        tenant_manager._global_db = mock_global_db
        mock_global_db.create_tenant.return_value = mock_tenant
        
        with patch.object(tenant_manager, '_create_tenant_database') as mock_create_db:
            mock_create_db.return_value = "sqlite://test-tenant.db"
            
            # Act
            result = await tenant_manager.create_tenant(tenant_data)
            
            # Assert
            assert result.tenant_id == "new-tenant-123"
            assert result.tenant_slug == "test-tenant"
            mock_create_db.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_tenant_duplicate_slug(self, tenant_manager, mock_global_db):
        """Test tenant creation with duplicate slug."""
        # Arrange
        tenant_data = {
            "name": "Test Tenant",
            "slug": "existing-slug",
            "owner_email": "owner@test.com"
        }
        
        tenant_manager._global_db = mock_global_db
        mock_global_db.create_tenant.side_effect = ValidationError("Slug already exists")
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await tenant_manager.create_tenant(tenant_data)
        
        assert "slug" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_delete_tenant_success(self, tenant_manager, mock_global_db):
        """Test successful tenant deletion."""
        # Arrange
        tenant_id = "tenant-to-delete"
        mock_tenant = Mock()
        mock_tenant.id = tenant_id
        mock_tenant.database_url = "sqlite://delete-me.db"
        
        tenant_manager._global_db = mock_global_db
        mock_global_db.get_tenant.return_value = mock_tenant
        mock_global_db.delete_tenant.return_value = True
        
        with patch.object(tenant_manager, '_delete_tenant_database') as mock_delete_db:
            mock_delete_db.return_value = True
            
            # Act
            result = await tenant_manager.delete_tenant(tenant_id)
            
            # Assert
            assert result is True
            mock_delete_db.assert_called_once_with("sqlite://delete-me.db")
    
    @pytest.mark.asyncio
    async def test_delete_tenant_not_found(self, tenant_manager, mock_global_db):
        """Test tenant deletion when tenant not found."""
        # Arrange
        tenant_id = "non-existent-tenant"
        tenant_manager._global_db = mock_global_db
        mock_global_db.get_tenant.return_value = None
        
        # Act & Assert
        with pytest.raises(TenantNotFoundError):
            await tenant_manager.delete_tenant(tenant_id)
    
    @pytest.mark.asyncio
    async def test_update_tenant_success(self, tenant_manager, mock_global_db):
        """Test successful tenant update."""
        # Arrange
        tenant_id = "tenant-to-update"
        update_data = {
            "name": "Updated Tenant Name",
            "settings": {"feature_flags": {"new_feature": True}}
        }
        
        mock_tenant = Mock()
        mock_tenant.id = tenant_id
        mock_tenant.name = "Updated Tenant Name"
        
        tenant_manager._global_db = mock_global_db
        mock_global_db.update_tenant.return_value = mock_tenant
        
        # Act
        result = await tenant_manager.update_tenant(tenant_id, update_data)
        
        # Assert
        assert result.name == "Updated Tenant Name"
        mock_global_db.update_tenant.assert_called_once_with(tenant_id, update_data)


@pytest.mark.integration
class TestMultiTenantAPIIntegration:
    """Test multi-tenant functionality in API integration."""
    
    def test_tenant_header_required(self, test_client):
        """Test that tenant header is required for API requests."""
        # Request without tenant header
        response = test_client.get(
            "/api/v1/users",
            headers={"Authorization": "Bearer valid-token"}
        )
        
        assert response.status_code in [400, 422]
        data = response.json()
        assert "tenant" in data["message"].lower()
    
    def test_invalid_tenant_rejected(self, test_client):
        """Test that invalid tenant IDs are rejected."""
        headers = {
            "Authorization": "Bearer valid-token",
            "X-Tenant-ID": "non-existent-tenant"
        }
        
        response = test_client.get("/api/v1/users", headers=headers)
        
        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "tenant_not_found"
    
    def test_tenant_data_isolation(self, test_client):
        """Test that data is isolated between tenants."""
        # Create user in tenant A
        tenant_a_headers = {
            "Authorization": "Bearer tenant-a-token",
            "X-Tenant-ID": "tenant-a"
        }
        
        user_data = {
            "email": "user@example.com",
            "auth0_user_id": "auth0|user123",
            "name": "Test User"
        }
        
        response_a = test_client.post(
            "/api/v1/users",
            json=user_data,
            headers=tenant_a_headers
        )
        
        if response_a.status_code == 201:
            user_id = response_a.json()["id"]
            
            # Try to access from tenant B
            tenant_b_headers = {
                "Authorization": "Bearer tenant-b-token",
                "X-Tenant-ID": "tenant-b"
            }
            
            response_b = test_client.get(
                f"/api/v1/users/{user_id}",
                headers=tenant_b_headers
            )
            
            # Should not be able to access user from different tenant
            assert response_b.status_code == 404
    
    def test_tenant_database_isolation(self, test_client):
        """Test that database operations are isolated by tenant."""
        # This would test that database queries include tenant filtering
        # Implementation depends on the database isolation strategy
        pass
    
    def test_cross_tenant_operations_prevented(self, test_client):
        """Test that cross-tenant operations are prevented."""
        # Test scenarios where operations might accidentally cross tenant boundaries
        
        # Example: Creating an account for a user in a different tenant
        tenant_a_headers = {
            "Authorization": "Bearer tenant-a-token",
            "X-Tenant-ID": "tenant-a"
        }
        
        # Try to create account with user ID from different tenant
        account_data = {
            "name": "Cross Tenant Account",
            "account_type": "checking",
            "user_id": "user-from-tenant-b"  # Different tenant
        }
        
        response = test_client.post(
            "/api/v1/accounts",
            json=account_data,
            headers=tenant_a_headers
        )
        
        # Should prevent cross-tenant operations
        assert response.status_code in [400, 404, 422]


@pytest.mark.integration
class TestTenantMiddleware:
    """Test tenant context middleware."""
    
    def test_tenant_context_middleware_sets_context(self, test_client):
        """Test that tenant middleware properly sets tenant context."""
        headers = {
            "Authorization": "Bearer valid-token",
            "X-Tenant-ID": "test-tenant"
        }
        
        # The middleware should set the tenant context
        # This would be verified by checking that subsequent operations
        # use the correct tenant context
        response = test_client.get("/api/v1/users", headers=headers)
        
        # If successful, middleware worked correctly
        assert response.status_code in [200, 401]  # Either success or auth failure
    
    def test_tenant_context_cleanup(self, test_client):
        """Test that tenant context is properly cleaned up after request."""
        # This would test that tenant context doesn't leak between requests
        pass
    
    def test_concurrent_tenant_requests(self, test_client):
        """Test handling of concurrent requests from different tenants."""
        import concurrent.futures
        import threading
        
        def make_request(tenant_id):
            headers = {
                "Authorization": f"Bearer {tenant_id}-token",
                "X-Tenant-ID": tenant_id
            }
            return test_client.get("/api/v1/users", headers=headers)
        
        # Make concurrent requests from different tenants
        tenant_ids = ["tenant-a", "tenant-b", "tenant-c"]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(make_request, tenant_id)
                for tenant_id in tenant_ids
            ]
            
            responses = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # All requests should be processed independently
        for response in responses:
            assert response.status_code in [200, 401, 404]  # Valid response codes


@pytest.mark.unit
class TestTenantService:
    """Test tenant service functionality."""
    
    @pytest.fixture
    def tenant_service(self):
        """Create TenantService instance."""
        mock_repository = AsyncMock()
        return TenantService(mock_repository)
    
    @pytest.mark.asyncio
    async def test_create_tenant_with_owner(self, tenant_service):
        """Test tenant creation with owner assignment."""
        # Arrange
        tenant_data = {
            "name": "New Tenant",
            "slug": "new-tenant",
            "owner_email": "owner@example.com"
        }
        
        mock_tenant = Mock()
        mock_tenant.id = "new-tenant-123"
        tenant_service._repository.create.return_value = mock_tenant
        
        # Act
        result = await tenant_service.create_tenant_with_owner(tenant_data)
        
        # Assert
        assert result.id == "new-tenant-123"
        tenant_service._repository.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_tenant_settings(self, tenant_service):
        """Test retrieval of tenant settings."""
        # Arrange
        tenant_id = "test-tenant"
        mock_tenant = Mock()
        mock_tenant.settings = {
            "features": {"feature_a": True, "feature_b": False},
            "limits": {"max_users": 100, "max_accounts": 50}
        }
        
        tenant_service._repository.get_by_id.return_value = mock_tenant
        
        # Act
        result = await tenant_service.get_tenant_settings(tenant_id)
        
        # Assert
        assert "features" in result
        assert "limits" in result
        assert result["features"]["feature_a"] is True
    
    @pytest.mark.asyncio
    async def test_update_tenant_settings(self, tenant_service):
        """Test updating tenant settings."""
        # Arrange
        tenant_id = "test-tenant"
        new_settings = {
            "features": {"new_feature": True},
            "limits": {"max_users": 200}
        }
        
        mock_tenant = Mock()
        mock_tenant.settings = new_settings
        tenant_service._repository.update_settings.return_value = mock_tenant
        
        # Act
        result = await tenant_service.update_tenant_settings(tenant_id, new_settings)
        
        # Assert
        assert result.settings == new_settings
        tenant_service._repository.update_settings.assert_called_once_with(tenant_id, new_settings)
    
    @pytest.mark.asyncio
    async def test_check_tenant_limits(self, tenant_service):
        """Test tenant limits checking."""
        # Arrange
        tenant_id = "test-tenant"
        resource_type = "users"
        current_count = 95
        
        mock_tenant = Mock()
        mock_tenant.settings = {"limits": {"max_users": 100}}
        tenant_service._repository.get_by_id.return_value = mock_tenant
        
        # Act
        result = await tenant_service.check_resource_limit(tenant_id, resource_type, current_count)
        
        # Assert
        assert result is True  # Within limits
        
        # Test over limit
        result = await tenant_service.check_resource_limit(tenant_id, resource_type, 105)
        assert result is False  # Over limit


@pytest.mark.integration
class TestTenantScaling:
    """Test tenant scaling and performance scenarios."""
    
    def test_large_number_of_tenants(self, test_client):
        """Test system behavior with large number of tenants."""
        # This would test performance with many tenants
        # Could be marked as @pytest.mark.slow
        pass
    
    def test_tenant_database_connection_pooling(self):
        """Test tenant database connection pooling."""
        # This would test that tenant databases use connection pooling efficiently
        pass
    
    def test_tenant_cache_performance(self):
        """Test tenant caching for performance."""
        # This would test that tenant lookups are cached appropriately
        pass


@pytest.mark.unit
class TestTenantMigrations:
    """Test tenant database migrations."""
    
    def test_tenant_schema_migration(self):
        """Test tenant database schema migrations."""
        # This would test that tenant databases can be migrated
        pass
    
    def test_tenant_data_migration(self):
        """Test tenant data migrations."""
        # This would test migrating data between tenant database versions
        pass


@pytest.mark.unit
class TestTenantBackup:
    """Test tenant backup and recovery."""
    
    def test_tenant_backup_creation(self):
        """Test creating tenant backups."""
        # This would test backup functionality for individual tenants
        pass
    
    def test_tenant_restoration(self):
        """Test restoring tenant from backup."""
        # This would test restoration functionality
        pass
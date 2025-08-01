"""Integration tests for users API endpoints."""
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
import json

from tests.conftest import assert_response_structure, assert_datetime_field, assert_uuid_field


@pytest.mark.integration
class TestUsersAPI:
    """Test users API endpoints integration."""
    
    def test_create_user_success(self, test_client, auth_headers, test_data_generator):
        """Test successful user creation via API."""
        # Arrange
        user_data = test_data_generator.user_data({
            "email": "newuser@example.com",
            "auth0_user_id": "auth0|newuser123"
        })
        
        # Act
        response = test_client.post(
            "/api/v1/users",
            json=user_data,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        
        assert_response_structure(data, [
            "id", "email", "name", "auth0_user_id", "role", 
            "created_at", "updated_at"
        ])
        assert data["email"] == user_data["email"]
        assert data["auth0_user_id"] == user_data["auth0_user_id"]
        assert data["role"] == "member"  # Default role
        assert_uuid_field(data["id"])
        assert_datetime_field(data["created_at"])
        assert_datetime_field(data["updated_at"])
    
    def test_create_user_duplicate_email(self, test_client, auth_headers, test_data_generator):
        """Test user creation with duplicate email fails."""
        # Arrange
        user_data = test_data_generator.user_data({
            "email": "duplicate@example.com",
            "auth0_user_id": "auth0|user1"
        })
        
        # Create first user
        response1 = test_client.post(
            "/api/v1/users",
            json=user_data,
            headers=auth_headers
        )
        assert response1.status_code == 201
        
        # Try to create duplicate
        duplicate_data = test_data_generator.user_data({
            "email": "duplicate@example.com",  # Same email
            "auth0_user_id": "auth0|user2"     # Different Auth0 ID
        })
        
        # Act
        response2 = test_client.post(
            "/api/v1/users", 
            json=duplicate_data,
            headers=auth_headers
        )
        
        # Assert
        assert response2.status_code == 422
        data = response2.json()
        assert "error" in data
        assert "email" in data["message"].lower()
    
    def test_create_user_invalid_data(self, test_client, auth_headers):
        """Test user creation with invalid data."""
        # Test cases for various invalid data
        invalid_cases = [
            # Missing required fields
            {"email": "test@example.com"},  # Missing auth0_user_id
            {"auth0_user_id": "auth0|test"},  # Missing email
            
            # Invalid email format
            {
                "email": "invalid-email",
                "auth0_user_id": "auth0|test",
                "name": "Test User"
            },
            
            # Empty values
            {
                "email": "",
                "auth0_user_id": "auth0|test",
                "name": "Test User"
            }
        ]
        
        for invalid_data in invalid_cases:
            response = test_client.post(
                "/api/v1/users",
                json=invalid_data,
                headers=auth_headers
            )
            
            assert response.status_code == 422
            data = response.json()
            assert "error" in data
    
    def test_get_user_by_id_success(self, test_client, auth_headers, test_user):
        """Test successful user retrieval by ID."""
        # Act
        response = test_client.get(
            f"/api/v1/users/{test_user.id}",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert_response_structure(data, [
            "id", "email", "name", "auth0_user_id", "role",
            "created_at", "updated_at"
        ])
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email
        assert data["name"] == test_user.name
    
    def test_get_user_by_id_not_found(self, test_client, auth_headers):
        """Test user retrieval with non-existent ID."""
        # Act
        response = test_client.get(
            "/api/v1/users/non-existent-id",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
    
    def test_get_current_user(self, test_client, auth_headers, test_user):
        """Test getting current authenticated user."""
        # Act
        response = test_client.get(
            "/api/v1/users/me",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert_response_structure(data, [
            "id", "email", "name", "auth0_user_id", "role",
            "created_at", "updated_at"
        ])
        # Should return the authenticated user's data
    
    def test_update_user_success(self, test_client, auth_headers, test_user):
        """Test successful user update."""
        # Arrange
        update_data = {
            "name": "Updated Name",
            "given_name": "Updated",
            "family_name": "Name"
        }
        
        # Act
        response = test_client.patch(
            f"/api/v1/users/{test_user.id}",
            json=update_data,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == update_data["name"]
        assert data["given_name"] == update_data["given_name"]
        assert data["family_name"] == update_data["family_name"]
        assert data["id"] == test_user.id
    
    def test_update_user_not_found(self, test_client, auth_headers):
        """Test user update with non-existent ID."""
        # Arrange
        update_data = {"name": "Updated Name"}
        
        # Act
        response = test_client.patch(
            "/api/v1/users/non-existent-id",
            json=update_data,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
    
    def test_delete_user_success(self, test_client, auth_headers, test_user):
        """Test successful user deletion."""
        # Act
        response = test_client.delete(
            f"/api/v1/users/{test_user.id}",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 204
        
        # Verify user is deleted
        get_response = test_client.get(
            f"/api/v1/users/{test_user.id}",
            headers=auth_headers
        )
        assert get_response.status_code == 404
    
    def test_delete_user_not_found(self, test_client, auth_headers):
        """Test user deletion with non-existent ID."""
        # Act
        response = test_client.delete(
            "/api/v1/users/non-existent-id",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 404
    
    def test_list_users_success(self, test_client, auth_headers):
        """Test successful user listing."""
        # Act
        response = test_client.get(
            "/api/v1/users",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert "users" in data or isinstance(data, list)
        if "users" in data:
            users = data["users"]
            assert "total" in data
            assert "skip" in data
            assert "limit" in data
        else:
            users = data
        
        assert isinstance(users, list)
        for user in users:
            assert_response_structure(user, [
                "id", "email", "name", "role", "created_at"
            ])
    
    def test_list_users_pagination(self, test_client, auth_headers):
        """Test user listing with pagination."""
        # Act
        response = test_client.get(
            "/api/v1/users?skip=0&limit=5",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Should respect pagination parameters
        if "users" in data:
            assert len(data["users"]) <= 5
        else:
            assert len(data) <= 5
    
    def test_update_user_role_admin_only(self, test_client, auth_headers, admin_headers, test_user):
        """Test user role update requires admin permissions."""
        # Arrange
        role_update = {"role": "admin"}
        
        # Act with regular user permissions
        response = test_client.patch(
            f"/api/v1/users/{test_user.id}/role",
            json=role_update,
            headers=auth_headers
        )
        
        # Assert - should be forbidden for regular users
        assert response.status_code == 403
        
        # Act with admin permissions
        response = test_client.patch(
            f"/api/v1/users/{test_user.id}/role",
            json=role_update,
            headers=admin_headers
        )
        
        # Assert - should succeed for admin users
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "admin"


@pytest.mark.integration
class TestUsersAPIAuthentication:
    """Test users API authentication and authorization."""
    
    def test_unauthorized_access(self, test_client):
        """Test API access without authentication."""
        endpoints = [
            ("GET", "/api/v1/users"),
            ("POST", "/api/v1/users"),
            ("GET", "/api/v1/users/me"),
            ("GET", "/api/v1/users/test-id"),
            ("PATCH", "/api/v1/users/test-id"),
            ("DELETE", "/api/v1/users/test-id"),
        ]
        
        for method, endpoint in endpoints:
            response = test_client.request(method, endpoint)
            
            # Should require authentication
            assert response.status_code in [401, 403, 422]
    
    def test_invalid_tenant_header(self, test_client):
        """Test API access with invalid tenant header."""
        headers = {
            "Authorization": "Bearer valid-token",
            "X-Tenant-ID": "invalid-tenant"
        }
        
        response = test_client.get("/api/v1/users", headers=headers)
        
        # Should reject invalid tenant
        assert response.status_code == 404  # Tenant not found
    
    def test_missing_tenant_header(self, test_client):
        """Test API access without tenant header."""
        headers = {"Authorization": "Bearer valid-token"}
        
        response = test_client.get("/api/v1/users", headers=headers)
        
        # Should require tenant identification
        assert response.status_code in [400, 422]
    
    def test_expired_token(self, test_client):
        """Test API access with expired token."""
        headers = {
            "Authorization": "Bearer expired-token",
            "X-Tenant-ID": "test-tenant"
        }
        
        response = test_client.get("/api/v1/users", headers=headers)
        
        # Should reject expired token
        assert response.status_code == 401


@pytest.mark.integration
class TestUsersAPIMultiTenant:
    """Test users API multi-tenant isolation."""
    
    def test_tenant_isolation(self, test_client):
        """Test that users are isolated between tenants."""
        # This test would require creating users in different tenants
        # and verifying they can't access each other's data
        
        tenant1_headers = {
            "Authorization": "Bearer tenant1-token",
            "X-Tenant-ID": "tenant-1"
        }
        
        tenant2_headers = {
            "Authorization": "Bearer tenant2-token", 
            "X-Tenant-ID": "tenant-2"
        }
        
        # Create user in tenant 1
        user_data = {
            "email": "user@tenant1.com",
            "auth0_user_id": "auth0|tenant1user",
            "name": "Tenant 1 User"
        }
        
        response1 = test_client.post(
            "/api/v1/users",
            json=user_data,
            headers=tenant1_headers
        )
        
        if response1.status_code == 201:
            user_id = response1.json()["id"]
            
            # Try to access from tenant 2
            response2 = test_client.get(
                f"/api/v1/users/{user_id}",
                headers=tenant2_headers
            )
            
            # Should not be able to access user from different tenant
            assert response2.status_code == 404
    
    def test_cross_tenant_user_creation(self, test_client):
        """Test user creation doesn't leak between tenants."""
        # Create same email in different tenants - should be allowed
        user_data = {
            "email": "same@example.com",
            "auth0_user_id": "auth0|tenant1",
            "name": "User"
        }
        
        tenant1_headers = {
            "Authorization": "Bearer tenant1-token",
            "X-Tenant-ID": "tenant-1"
        }
        
        tenant2_headers = {
            "Authorization": "Bearer tenant2-token",
            "X-Tenant-ID": "tenant-2"
        }
        
        # Create in tenant 1
        response1 = test_client.post(
            "/api/v1/users",
            json=user_data,
            headers=tenant1_headers
        )
        
        # Create same email in tenant 2 (different Auth0 ID)
        user_data["auth0_user_id"] = "auth0|tenant2"
        response2 = test_client.post(
            "/api/v1/users",
            json=user_data,
            headers=tenant2_headers
        )
        
        # Both should succeed due to tenant isolation
        assert response1.status_code == 201
        assert response2.status_code == 201


@pytest.mark.integration
@pytest.mark.asyncio
class TestUsersAPIAsync:
    """Test users API endpoints using async client."""
    
    async def test_create_user_async(self, async_client, auth_headers, test_data_generator):
        """Test async user creation."""
        # Arrange
        user_data = test_data_generator.user_data({
            "email": "async@example.com",
            "auth0_user_id": "auth0|async123"
        })
        
        # Act
        response = await async_client.post(
            "/api/v1/users",
            json=user_data,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
    
    async def test_concurrent_user_operations(self, async_client, auth_headers, test_data_generator):
        """Test concurrent user operations."""
        import asyncio
        
        # Create multiple users concurrently
        user_data_list = [
            test_data_generator.user_data({
                "email": f"concurrent{i}@example.com",
                "auth0_user_id": f"auth0|concurrent{i}"
            })
            for i in range(5)
        ]
        
        # Create users concurrently
        tasks = [
            async_client.post(
                "/api/v1/users",
                json=user_data,
                headers=auth_headers
            )
            for user_data in user_data_list
        ]
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should succeed
        successful_responses = [r for r in responses if not isinstance(r, Exception)]
        assert len(successful_responses) >= 4  # Allow for some potential conflicts
        
        for response in successful_responses:
            assert response.status_code == 201


@pytest.mark.integration
class TestUsersAPIErrorHandling:
    """Test users API error handling."""
    
    def test_malformed_json(self, test_client, auth_headers):
        """Test API handling of malformed JSON."""
        response = test_client.post(
            "/api/v1/users",
            data="invalid json",
            headers={**auth_headers, "Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "error" in data
    
    def test_oversized_request(self, test_client, auth_headers):
        """Test API handling of oversized requests."""
        large_data = {
            "email": "test@example.com",
            "auth0_user_id": "auth0|test",
            "name": "A" * 10000,  # Very long name
        }
        
        response = test_client.post(
            "/api/v1/users",
            json=large_data,
            headers=auth_headers
        )
        
        # Should handle large data appropriately
        assert response.status_code in [422, 413]  # Validation error or payload too large
    
    def test_sql_injection_prevention(self, test_client, auth_headers):
        """Test API prevents SQL injection attacks."""
        malicious_data = {
            "email": "test'; DROP TABLE users; --@example.com",
            "auth0_user_id": "auth0|malicious",
            "name": "'; DELETE FROM users WHERE 1=1; --"
        }
        
        response = test_client.post(
            "/api/v1/users",
            json=malicious_data,
            headers=auth_headers
        )
        
        # Should handle malicious input safely
        # Either validation error or safe creation
        assert response.status_code in [201, 422]
        
        # Verify tables still exist by making another request
        list_response = test_client.get("/api/v1/users", headers=auth_headers)
        assert list_response.status_code == 200
    
    def test_xss_prevention(self, test_client, auth_headers):
        """Test API prevents XSS attacks."""
        xss_data = {
            "email": "test@example.com",
            "auth0_user_id": "auth0|xss",
            "name": "<script>alert('XSS')</script>",
            "given_name": "<img src=x onerror=alert('XSS')>"
        }
        
        response = test_client.post(
            "/api/v1/users",
            json=xss_data,
            headers=auth_headers
        )
        
        if response.status_code == 201:
            data = response.json()
            # Should sanitize or escape dangerous content
            assert "<script>" not in data["name"]
            assert "onerror=" not in data.get("given_name", "")
        else:
            # Or reject the malicious input
            assert response.status_code == 422
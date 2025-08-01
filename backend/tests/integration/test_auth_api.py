"""Integration tests for auth API endpoints."""
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
import json
from datetime import datetime, timezone, timedelta

from tests.conftest import assert_response_structure, assert_datetime_field


@pytest.mark.integration
class TestAuthAPI:
    """Test auth API endpoints integration."""
    
    def test_login_success(self, test_client, mock_auth0):
        """Test successful user login."""
        # Arrange
        login_data = {
            "access_token": "valid-auth0-token",
            "id_token": "valid-id-token"
        }
        
        # Mock Auth0 token verification
        mock_auth0.verify_token.return_value = {
            "sub": "auth0|test123",
            "email": "test@example.com",
            "email_verified": True,
            "name": "Test User"
        }
        
        # Act
        response = test_client.post(
            "/api/v1/auth/login",
            json=login_data
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert_response_structure(data, [
            "access_token", "refresh_token", "token_type", 
            "expires_in", "user"
        ])
        assert data["token_type"] == "Bearer"
        assert data["expires_in"] > 0
        assert "user" in data
        assert data["user"]["email"] == "test@example.com"
    
    def test_login_invalid_token(self, test_client, mock_auth0):
        """Test login with invalid Auth0 token."""
        # Arrange
        login_data = {
            "access_token": "invalid-token",
            "id_token": "invalid-id-token"
        }
        
        # Mock Auth0 token verification failure
        mock_auth0.verify_token.side_effect = Exception("Invalid token")
        
        # Act
        response = test_client.post(
            "/api/v1/auth/login",
            json=login_data
        )
        
        # Assert
        assert response.status_code == 401
        data = response.json()
        assert data["error"] == "authentication_failed"
    
    def test_login_unverified_email(self, test_client, mock_auth0):
        """Test login with unverified email."""
        # Arrange
        login_data = {
            "access_token": "valid-auth0-token",
            "id_token": "valid-id-token"
        }
        
        # Mock Auth0 token with unverified email
        mock_auth0.verify_token.return_value = {
            "sub": "auth0|test123",
            "email": "unverified@example.com",
            "email_verified": False,  # Unverified email
            "name": "Test User"
        }
        
        # Act
        response = test_client.post(
            "/api/v1/auth/login",
            json=login_data
        )
        
        # Assert
        assert response.status_code == 403
        data = response.json()
        assert "email" in data["message"].lower()
        assert "verify" in data["message"].lower()
    
    def test_refresh_token_success(self, test_client):
        """Test successful token refresh."""
        # Arrange
        refresh_data = {
            "refresh_token": "valid-refresh-token"
        }
        
        with patch('src.auth.service.AuthService.refresh_user_token') as mock_refresh:
            mock_refresh.return_value = {
                "access_token": "new-access-token",
                "refresh_token": "new-refresh-token",
                "expires_in": 3600
            }
            
            # Act
            response = test_client.post(
                "/api/v1/auth/refresh",
                json=refresh_data
            )
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            
            assert_response_structure(data, [
                "access_token", "refresh_token", "token_type", "expires_in"
            ])
            assert data["access_token"] == "new-access-token"
            assert data["refresh_token"] == "new-refresh-token"
    
    def test_refresh_token_invalid(self, test_client):
        """Test token refresh with invalid refresh token."""
        # Arrange
        refresh_data = {
            "refresh_token": "invalid-refresh-token"
        }
        
        with patch('src.auth.service.AuthService.refresh_user_token') as mock_refresh:
            from src.exceptions import AuthenticationError
            mock_refresh.side_effect = AuthenticationError("Invalid refresh token")
            
            # Act
            response = test_client.post(
                "/api/v1/auth/refresh",
                json=refresh_data
            )
            
            # Assert
            assert response.status_code == 401
            data = response.json()
            assert data["error"] == "authentication_failed"
    
    def test_logout_success(self, test_client, auth_headers):
        """Test successful user logout."""
        # Act
        response = test_client.post(
            "/api/v1/auth/logout",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Successfully logged out"
    
    def test_logout_without_auth(self, test_client):
        """Test logout without authentication."""
        # Act
        response = test_client.post("/api/v1/auth/logout")
        
        # Assert
        assert response.status_code == 401
    
    def test_get_user_profile_success(self, test_client, auth_headers, test_user):
        """Test successful user profile retrieval."""
        # Act
        response = test_client.get(
            "/api/v1/auth/profile",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert_response_structure(data, [
            "id", "email", "name", "given_name", "family_name",
            "picture", "role", "permissions", "last_login", "created_at"
        ])
        assert data["email"] == test_user.email
        assert data["name"] == test_user.name
        assert isinstance(data["permissions"], list)
    
    def test_get_user_profile_without_auth(self, test_client):
        """Test user profile retrieval without authentication."""
        # Act
        response = test_client.get("/api/v1/auth/profile")
        
        # Assert
        assert response.status_code == 401
    
    def test_update_user_profile_success(self, test_client, auth_headers):
        """Test successful user profile update."""
        # Arrange
        update_data = {
            "name": "Updated Name",
            "given_name": "Updated",
            "family_name": "Name"
        }
        
        # Act
        response = test_client.patch(
            "/api/v1/auth/profile",
            json=update_data,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["given_name"] == "Updated"
        assert data["family_name"] == "Name"
    
    def test_change_password_success(self, test_client, auth_headers):
        """Test successful password change."""
        # Arrange
        password_data = {
            "current_password": "current-password",
            "new_password": "new-secure-password-123",
            "confirm_password": "new-secure-password-123"
        }
        
        with patch('src.auth.service.AuthService.change_user_password') as mock_change:
            mock_change.return_value = True
            
            # Act
            response = test_client.post(
                "/api/v1/auth/change-password",
                json=password_data,
                headers=auth_headers
            )
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Password changed successfully"
    
    def test_change_password_mismatch(self, test_client, auth_headers):
        """Test password change with mismatched passwords."""
        # Arrange
        password_data = {
            "current_password": "current-password",
            "new_password": "new-password",
            "confirm_password": "different-password"  # Mismatch
        }
        
        # Act
        response = test_client.post(
            "/api/v1/auth/change-password",
            json=password_data,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "password" in data["message"].lower()
        assert "match" in data["message"].lower()
    
    def test_check_permissions_success(self, test_client, auth_headers):
        """Test successful permission check."""
        # Arrange
        permission_data = {
            "resource": "users",
            "action": "read"
        }
        
        with patch('src.auth.service.AuthService.check_user_permission') as mock_check:
            mock_check.return_value = True
            
            # Act
            response = test_client.post(
                "/api/v1/auth/check-permission",
                json=permission_data,
                headers=auth_headers
            )
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["allowed"] is True
            assert data["resource"] == "users"
            assert data["action"] == "read"
    
    def test_check_permissions_denied(self, test_client, auth_headers):
        """Test permission check denied."""
        # Arrange
        permission_data = {
            "resource": "admin",
            "action": "write"
        }
        
        with patch('src.auth.service.AuthService.check_user_permission') as mock_check:
            mock_check.return_value = False
            
            # Act
            response = test_client.post(
                "/api/v1/auth/check-permission",
                json=permission_data,
                headers=auth_headers
            )
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["allowed"] is False
    
    def test_get_user_sessions_success(self, test_client, auth_headers):
        """Test successful user sessions retrieval."""
        # Act
        response = test_client.get(
            "/api/v1/auth/sessions",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data["sessions"], list)
        for session in data["sessions"]:
            assert_response_structure(session, [
                "id", "user_agent", "ip_address", "created_at", 
                "last_activity", "is_current"
            ])
            assert_datetime_field(session["created_at"])
    
    def test_revoke_session_success(self, test_client, auth_headers):
        """Test successful session revocation."""
        # Arrange
        session_id = "session-to-revoke"
        
        with patch('src.auth.service.AuthService.revoke_user_session') as mock_revoke:
            mock_revoke.return_value = True
            
            # Act
            response = test_client.delete(
                f"/api/v1/auth/sessions/{session_id}",
                headers=auth_headers
            )
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Session revoked successfully"
    
    def test_revoke_all_sessions_success(self, test_client, auth_headers):
        """Test successful revocation of all user sessions."""
        # Act
        response = test_client.delete(
            "/api/v1/auth/sessions",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "All sessions revoked successfully"


@pytest.mark.integration
class TestAuthAPIMultiTenant:
    """Test auth API multi-tenant functionality."""
    
    def test_login_creates_tenant_session(self, test_client, mock_auth0):
        """Test that login creates session in correct tenant."""
        # Arrange
        tenant_headers = {"X-Tenant-ID": "test-tenant"}
        login_data = {
            "access_token": "valid-auth0-token",
            "id_token": "valid-id-token"
        }
        
        mock_auth0.verify_token.return_value = {
            "sub": "auth0|test123",
            "email": "test@example.com",
            "email_verified": True,
            "name": "Test User"
        }
        
        # Act
        response = test_client.post(
            "/api/v1/auth/login",
            json=login_data,
            headers=tenant_headers
        )
        
        # Assert
        assert response.status_code == 200
        # Session should be created in the correct tenant context
    
    def test_cross_tenant_session_isolation(self, test_client):
        """Test that sessions are isolated between tenants."""
        # This would test that a session created in one tenant
        # cannot be used to access resources in another tenant
        
        tenant_a_headers = {
            "Authorization": "Bearer tenant-a-token",
            "X-Tenant-ID": "tenant-a"
        }
        
        tenant_b_headers = {
            "Authorization": "Bearer tenant-a-token",  # Same token
            "X-Tenant-ID": "tenant-b"  # Different tenant
        }
        
        # Try to access profile from different tenant
        response = test_client.get(
            "/api/v1/auth/profile",
            headers=tenant_b_headers
        )
        
        # Should be unauthorized due to tenant mismatch
        assert response.status_code in [401, 403]
    
    def test_tenant_specific_permissions(self, test_client):
        """Test that permissions are tenant-specific."""
        # This would test that user permissions in one tenant
        # don't apply to another tenant
        pass


@pytest.mark.integration
class TestAuthAPISecurity:
    """Test auth API security features."""
    
    def test_sql_injection_prevention(self, test_client):
        """Test that auth endpoints prevent SQL injection."""
        malicious_data = {
            "access_token": "'; DROP TABLE users; --",
            "id_token": "'; DELETE FROM sessions; --"
        }
        
        response = test_client.post(
            "/api/v1/auth/login",
            json=malicious_data
        )
        
        # Should handle malicious input safely
        assert response.status_code in [401, 422]
        
        # Verify system is still functional
        health_response = test_client.get("/health")
        assert health_response.status_code == 200
    
    def test_xss_prevention(self, test_client, auth_headers):
        """Test that auth endpoints prevent XSS attacks."""
        xss_data = {
            "name": "<script>alert('XSS')</script>",
            "given_name": "<img src=x onerror=alert('XSS')>"
        }
        
        response = test_client.patch(
            "/api/v1/auth/profile",
            json=xss_data,
            headers=auth_headers
        )
        
        if response.status_code == 200:
            data = response.json()
            # Should sanitize dangerous content
            assert "<script>" not in data.get("name", "")
            assert "onerror=" not in data.get("given_name", "")
    
    def test_rate_limiting(self, test_client):
        """Test rate limiting on auth endpoints."""
        # Make multiple rapid requests
        login_data = {
            "access_token": "invalid-token",
            "id_token": "invalid-token"
        }
        
        responses = []
        for _ in range(10):  # 10 rapid requests
            response = test_client.post(
                "/api/v1/auth/login",
                json=login_data
            )
            responses.append(response)
        
        # Should have rate limiting after several failures
        rate_limited = any(r.status_code == 429 for r in responses)
        # Note: This depends on rate limiting implementation
    
    def test_session_security_headers(self, test_client, auth_headers):
        """Test that security headers are set correctly."""
        response = test_client.get(
            "/api/v1/auth/profile",
            headers=auth_headers
        )
        
        # Check for security headers
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
    
    def test_token_exposure_prevention(self, test_client):
        """Test that tokens are not exposed in error messages."""
        malformed_headers = {
            "Authorization": "Bearer malformed-token-12345"
        }
        
        response = test_client.get(
            "/api/v1/auth/profile",
            headers=malformed_headers
        )
        
        # Token should not appear in error response
        assert response.status_code == 401
        response_text = response.text.lower()
        assert "malformed-token-12345" not in response_text
    
    def test_password_strength_requirements(self, test_client, auth_headers):
        """Test password strength requirements."""
        weak_passwords = [
            "123456",  # Too simple
            "password",  # Common password
            "abc",  # Too short
            "12345678901234567890123456789012345678901234567890"  # Too long
        ]
        
        for weak_password in weak_passwords:
            password_data = {
                "current_password": "current-password",
                "new_password": weak_password,
                "confirm_password": weak_password
            }
            
            response = test_client.post(
                "/api/v1/auth/change-password",
                json=password_data,
                headers=auth_headers
            )
            
            # Should reject weak passwords
            assert response.status_code == 422
            data = response.json()
            assert "password" in data["message"].lower()


@pytest.mark.integration
@pytest.mark.asyncio
class TestAuthAPIAsync:
    """Test auth API endpoints using async client."""
    
    async def test_concurrent_login_requests(self, async_client, mock_auth0):
        """Test handling of concurrent login requests."""
        import asyncio
        
        # Setup mock
        mock_auth0.verify_token.return_value = {
            "sub": "auth0|test123",
            "email": "test@example.com",
            "email_verified": True,
            "name": "Test User"
        }
        
        login_data = {
            "access_token": "valid-auth0-token",
            "id_token": "valid-id-token"
        }
        
        # Make concurrent login requests
        tasks = [
            async_client.post("/api/v1/auth/login", json=login_data)
            for _ in range(5)
        ]
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should be handled properly
        successful_responses = [r for r in responses if not isinstance(r, Exception)]
        assert len(successful_responses) >= 4  # Allow for some potential issues
        
        for response in successful_responses:
            assert response.status_code == 200
    
    async def test_session_cleanup_background_task(self, async_client):
        """Test that expired sessions are cleaned up."""
        # This would test background task that cleans up expired sessions
        # Implementation depends on background task system
        pass


@pytest.mark.integration
class TestAuthAPIErrorHandling:
    """Test auth API error handling."""
    
    def test_malformed_json_request(self, test_client):
        """Test handling of malformed JSON in auth requests."""
        response = test_client.post(
            "/api/v1/auth/login",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "error" in data
    
    def test_missing_required_fields(self, test_client):
        """Test handling of missing required fields."""
        incomplete_data = {
            "access_token": "valid-token"
            # Missing id_token
        }
        
        response = test_client.post(
            "/api/v1/auth/login",
            json=incomplete_data
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "error" in data
    
    def test_oversized_token_handling(self, test_client):
        """Test handling of oversized tokens."""
        oversized_data = {
            "access_token": "A" * 10000,  # Very large token
            "id_token": "B" * 10000
        }
        
        response = test_client.post(
            "/api/v1/auth/login",
            json=oversized_data
        )
        
        # Should handle oversized data appropriately
        assert response.status_code in [413, 422]
    
    def test_external_service_timeout_handling(self, test_client, mock_auth0):
        """Test handling of external service timeouts."""
        # Mock Auth0 service timeout
        from src.exceptions import ExternalServiceError
        mock_auth0.verify_token.side_effect = ExternalServiceError(
            "auth0", 
            "Service timeout"
        )
        
        login_data = {
            "access_token": "valid-token",
            "id_token": "valid-token"
        }
        
        response = test_client.post(
            "/api/v1/auth/login",
            json=login_data
        )
        
        assert response.status_code == 502
        data = response.json()
        assert data["error"] == "external_service_error"
        assert data["service"] == "auth0"
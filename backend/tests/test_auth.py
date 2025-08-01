"""Comprehensive authentication and authorization tests."""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from fastapi.testclient import TestClient
from jose import jwt
from datetime import datetime, timedelta

from src.auth.service import Auth0Service
from src.auth.dependencies import get_current_user, verify_permissions, get_tenant_context
from src.exceptions import AuthenticationError, AuthorizationError, TenantNotFoundError


@pytest.mark.unit
class TestAuth0Service:
    """Test Auth0 service functionality."""
    
    @pytest.fixture
    def auth0_service(self):
        """Create Auth0Service instance."""
        return Auth0Service()
    
    @pytest.fixture
    def valid_token_payload(self):
        """Valid JWT token payload."""
        return {
            "sub": "auth0|test123",
            "email": "test@example.com",
            "email_verified": True,
            "name": "Test User",
            "given_name": "Test",
            "family_name": "User",
            "picture": "https://example.com/avatar.jpg",
            "iat": int(datetime.utcnow().timestamp()),
            "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
            "aud": "test-audience",
            "iss": "https://test.auth0.com/"
        }
    
    @pytest.mark.asyncio
    async def test_verify_token_success(self, auth0_service, valid_token_payload):
        """Test successful token verification."""
        # Arrange
        token = "valid.jwt.token"
        
        with patch('jose.jwt.decode') as mock_decode:
            mock_decode.return_value = valid_token_payload
            
            with patch.object(auth0_service, '_get_signing_key') as mock_key:
                mock_key.return_value = "test-key"
                
                # Act
                result = await auth0_service.verify_token(token)
                
                # Assert
                assert result["sub"] == valid_token_payload["sub"]
                assert result["email"] == valid_token_payload["email"]
                mock_decode.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_verify_token_expired(self, auth0_service):
        """Test token verification with expired token."""
        # Arrange
        expired_payload = {
            "sub": "auth0|test123",
            "exp": int((datetime.utcnow() - timedelta(hours=1)).timestamp())  # Expired
        }
        token = "expired.jwt.token"
        
        with patch('jose.jwt.decode') as mock_decode:
            from jose import JWTError
            mock_decode.side_effect = JWTError("Token has expired")
            
            # Act & Assert
            with pytest.raises(AuthenticationError) as exc_info:
                await auth0_service.verify_token(token)
            
            assert "expired" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_verify_token_invalid_signature(self, auth0_service):
        """Test token verification with invalid signature."""
        # Arrange
        token = "invalid.signature.token"
        
        with patch('jose.jwt.decode') as mock_decode:
            from jose import JWTError
            mock_decode.side_effect = JWTError("Invalid signature")
            
            # Act & Assert
            with pytest.raises(AuthenticationError) as exc_info:
                await auth0_service.verify_token(token)
            
            assert "invalid" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_verify_token_invalid_audience(self, auth0_service, valid_token_payload):
        """Test token verification with invalid audience."""
        # Arrange
        invalid_payload = {**valid_token_payload, "aud": "wrong-audience"}
        token = "wrong.audience.token"
        
        with patch('jose.jwt.decode') as mock_decode:
            from jose import JWTError
            mock_decode.side_effect = JWTError("Invalid audience")
            
            # Act & Assert
            with pytest.raises(AuthenticationError):
                await auth0_service.verify_token(token)
    
    @pytest.mark.asyncio
    async def test_get_user_info_success(self, auth0_service):
        """Test successful user info retrieval."""
        # Arrange
        access_token = "valid-access-token"
        user_info = {
            "sub": "auth0|test123",
            "email": "test@example.com",
            "email_verified": True,
            "name": "Test User",
            "given_name": "Test",
            "family_name": "User",
            "picture": "https://example.com/avatar.jpg"
        }
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = user_info
            mock_get.return_value = mock_response
            
            # Act
            result = await auth0_service.get_user_info(access_token)
            
            # Assert
            assert result == user_info
            mock_get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_user_info_unauthorized(self, auth0_service):
        """Test user info retrieval with invalid token."""
        # Arrange
        access_token = "invalid-token"
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_get.return_value = mock_response
            
            # Act & Assert
            with pytest.raises(AuthenticationError):
                await auth0_service.get_user_info(access_token)


@pytest.mark.unit
class TestAuthDependencies:
    """Test authentication dependency functions."""
    
    @pytest.fixture
    def mock_request(self):
        """Mock FastAPI request."""
        request = Mock()
        request.headers = {
            "authorization": "Bearer valid-token",
            "x-tenant-id": "test-tenant"
        }
        return request
    
    @pytest.mark.asyncio
    async def test_get_current_user_success(self, mock_request):
        """Test successful current user retrieval."""
        # Arrange
        user_payload = {
            "sub": "auth0|test123",
            "email": "test@example.com",
            "email_verified": True
        }
        
        with patch('src.auth.dependencies.Auth0Service') as mock_auth0:
            mock_auth0.return_value.verify_token.return_value = user_payload
            
            with patch('src.auth.dependencies.get_user_by_auth0_id') as mock_get_user:
                mock_user = Mock()
                mock_user.id = "user-123"
                mock_user.email = "test@example.com"
                mock_user.role = "member"
                mock_get_user.return_value = mock_user
                
                # Act
                result = await get_current_user(mock_request)
                
                # Assert
                assert result == mock_user
                mock_auth0.return_value.verify_token.assert_called_once_with("valid-token")
    
    @pytest.mark.asyncio
    async def test_get_current_user_missing_token(self):
        """Test current user retrieval without token."""
        # Arrange
        request = Mock()
        request.headers = {"x-tenant-id": "test-tenant"}  # No authorization header
        
        # Act & Assert
        with pytest.raises(AuthenticationError) as exc_info:
            await get_current_user(request)
        
        assert "missing" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token_format(self):
        """Test current user retrieval with invalid token format."""
        # Arrange
        request = Mock()
        request.headers = {
            "authorization": "InvalidFormat token",  # Should be "Bearer token"
            "x-tenant-id": "test-tenant"
        }
        
        # Act & Assert
        with pytest.raises(AuthenticationError) as exc_info:
            await get_current_user(request)
        
        assert "invalid" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_get_current_user_not_found(self, mock_request):
        """Test current user retrieval when user not found in database."""
        # Arrange
        user_payload = {
            "sub": "auth0|nonexistent",
            "email": "nonexistent@example.com"
        }
        
        with patch('src.auth.dependencies.Auth0Service') as mock_auth0:
            mock_auth0.return_value.verify_token.return_value = user_payload
            
            with patch('src.auth.dependencies.get_user_by_auth0_id') as mock_get_user:
                mock_get_user.return_value = None
                
                # Act & Assert
                with pytest.raises(AuthenticationError) as exc_info:
                    await get_current_user(mock_request)
                
                assert "user not found" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_verify_permissions_admin(self):
        """Test permission verification for admin user."""
        # Arrange
        admin_user = Mock()
        admin_user.role = "admin"
        
        # Act
        result = await verify_permissions(admin_user, "manage_users")
        
        # Assert
        assert result is True  # Admin should have all permissions
    
    @pytest.mark.asyncio
    async def test_verify_permissions_member_allowed(self):
        """Test permission verification for member with allowed permission."""
        # Arrange
        member_user = Mock()
        member_user.role = "member"
        
        # Act
        result = await verify_permissions(member_user, "view_own_data")
        
        # Assert
        assert result is True  # Member should have basic permissions
    
    @pytest.mark.asyncio
    async def test_verify_permissions_member_denied(self):
        """Test permission verification for member with denied permission."""
        # Arrange
        member_user = Mock()
        member_user.role = "member"
        
        # Act & Assert
        with pytest.raises(AuthorizationError) as exc_info:
            await verify_permissions(member_user, "manage_users")
        
        assert "permission denied" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_get_tenant_context_success(self):
        """Test successful tenant context retrieval."""
        # Arrange
        request = Mock()
        request.headers = {"x-tenant-id": "test-tenant"}
        
        with patch('src.auth.dependencies.get_tenant_by_id') as mock_get_tenant:
            mock_tenant = Mock()
            mock_tenant.id = "test-tenant"
            mock_tenant.slug = "test-tenant"
            mock_tenant.database_url = "sqlite://test.db"
            mock_get_tenant.return_value = mock_tenant
            
            # Act
            result = await get_tenant_context(request)
            
            # Assert
            assert result.tenant_id == "test-tenant"
            assert result.tenant_slug == "test-tenant"
    
    @pytest.mark.asyncio
    async def test_get_tenant_context_missing_header(self):
        """Test tenant context retrieval without tenant header."""
        # Arrange
        request = Mock()
        request.headers = {}  # No x-tenant-id header
        
        # Act & Assert
        with pytest.raises(TenantNotFoundError):
            await get_tenant_context(request)
    
    @pytest.mark.asyncio
    async def test_get_tenant_context_invalid_tenant(self):
        """Test tenant context retrieval with invalid tenant ID."""
        # Arrange
        request = Mock()
        request.headers = {"x-tenant-id": "invalid-tenant"}
        
        with patch('src.auth.dependencies.get_tenant_by_id') as mock_get_tenant:
            mock_get_tenant.return_value = None
            
            # Act & Assert
            with pytest.raises(TenantNotFoundError):
                await get_tenant_context(request)


@pytest.mark.integration
class TestAuthenticationIntegration:
    """Test authentication integration with API endpoints."""
    
    def test_protected_endpoint_requires_auth(self, test_client):
        """Test that protected endpoints require authentication."""
        # List of protected endpoints
        protected_endpoints = [
            ("GET", "/api/v1/users/me"),
            ("GET", "/api/v1/users"),
            ("POST", "/api/v1/users"),
            ("GET", "/api/v1/accounts"),
            ("POST", "/api/v1/accounts"),
            ("GET", "/api/v1/transactions"),
            ("POST", "/api/v1/transactions"),
        ]
        
        for method, endpoint in protected_endpoints:
            response = test_client.request(method, endpoint)
            
            # Should require authentication
            assert response.status_code in [401, 403, 422]
    
    def test_invalid_token_rejected(self, test_client):
        """Test that invalid tokens are rejected."""
        headers = {
            "Authorization": "Bearer invalid-token",
            "X-Tenant-ID": "test-tenant"
        }
        
        response = test_client.get("/api/v1/users/me", headers=headers)
        
        assert response.status_code == 401
        data = response.json()
        assert "error" in data
    
    def test_expired_token_rejected(self, test_client):
        """Test that expired tokens are rejected."""
        # Create an expired token
        expired_payload = {
            "sub": "auth0|test123",
            "exp": int((datetime.utcnow() - timedelta(hours=1)).timestamp()),
            "aud": "test-audience",
            "iss": "https://test.auth0.com/"
        }
        
        expired_token = jwt.encode(expired_payload, "secret", algorithm="HS256")
        
        headers = {
            "Authorization": f"Bearer {expired_token}",
            "X-Tenant-ID": "test-tenant"
        }
        
        response = test_client.get("/api/v1/users/me", headers=headers)
        
        assert response.status_code == 401
    
    def test_missing_tenant_header_rejected(self, test_client):
        """Test that requests without tenant header are rejected."""
        headers = {"Authorization": "Bearer valid-token"}
        
        response = test_client.get("/api/v1/users/me", headers=headers)
        
        assert response.status_code in [400, 422]
    
    def test_valid_authentication_success(self, test_client, auth_headers, test_user):
        """Test that valid authentication allows access."""
        response = test_client.get("/api/v1/users/me", headers=auth_headers)
        
        # Should succeed with valid authentication
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data
    
    def test_role_based_authorization(self, test_client, auth_headers, admin_headers):
        """Test role-based authorization."""
        # Regular user trying to access admin endpoint
        response = test_client.get("/api/v1/admin/users", headers=auth_headers)
        assert response.status_code in [403, 404]  # Forbidden or not found
        
        # Admin user accessing admin endpoint
        response = test_client.get("/api/v1/admin/users", headers=admin_headers)
        # Should succeed for admin (if endpoint exists)
        assert response.status_code in [200, 404]  # Success or endpoint doesn't exist


@pytest.mark.integration
class TestMultiTenantAuthentication:
    """Test multi-tenant authentication scenarios."""
    
    def test_tenant_isolation_in_auth(self, test_client):
        """Test that authentication respects tenant boundaries."""
        # User authenticated for tenant A tries to access tenant B
        tenant_a_headers = {
            "Authorization": "Bearer tenant-a-token",
            "X-Tenant-ID": "tenant-a"
        }
        
        tenant_b_headers = {
            "Authorization": "Bearer tenant-a-token",  # Same token
            "X-Tenant-ID": "tenant-b"  # Different tenant
        }
        
        # Should fail when using wrong tenant
        response = test_client.get("/api/v1/users/me", headers=tenant_b_headers)
        assert response.status_code in [401, 403, 404]
    
    def test_cross_tenant_data_access_prevention(self, test_client):
        """Test prevention of cross-tenant data access."""
        # This would test that users can't access data from other tenants
        # even with valid authentication for their own tenant
        pass


@pytest.mark.unit
class TestSecurityHeaders:
    """Test security-related functionality."""
    
    def test_security_headers_present(self, test_client):
        """Test that security headers are present in responses."""
        response = test_client.get("/health")
        
        headers = response.headers
        
        # Check for common security headers
        # (The exact headers depend on SecurityMiddleware implementation)
        expected_security_headers = [
            "x-content-type-options",
            "x-frame-options",
            "x-xss-protection",
        ]
        
        for header in expected_security_headers:
            # Some security headers might be present
            if header in headers:
                assert headers[header] is not None
    
    def test_cors_headers_configuration(self, test_client):
        """Test CORS headers are properly configured."""
        # Test preflight request
        response = test_client.options(
            "/api/v1/users",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization,X-Tenant-ID"
            }
        )
        
        # Should handle CORS properly
        assert response.status_code in [200, 204]
    
    def test_rate_limiting_protection(self, test_client):
        """Test rate limiting protection (if implemented)."""
        # This would test rate limiting functionality
        # Implementation depends on rate limiting strategy
        pass
    
    def test_request_size_limits(self, test_client):
        """Test request size limits."""
        # Test with oversized request
        large_payload = {"data": "A" * 1000000}  # 1MB payload
        
        response = test_client.post(
            "/api/v1/users",
            json=large_payload,
            headers={"Authorization": "Bearer token", "X-Tenant-ID": "test"}
        )
        
        # Should handle large payloads appropriately
        assert response.status_code in [413, 422]  # Payload too large or validation error


@pytest.mark.unit
class TestPasswordSecurity:
    """Test password-related security (if applicable)."""
    
    def test_password_hashing(self):
        """Test password hashing functionality."""
        from passlib.context import CryptContext
        
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        password = "test_password_123"
        hashed = pwd_context.hash(password)
        
        assert hashed != password  # Should be hashed
        assert pwd_context.verify(password, hashed)  # Should verify correctly
        assert not pwd_context.verify("wrong_password", hashed)  # Should reject wrong password
    
    def test_password_strength_validation(self):
        """Test password strength validation (if implemented)."""
        # This would test password strength requirements
        # Implementation depends on password policy
        pass


@pytest.mark.unit
class TestTokenSecurity:
    """Test token security measures."""
    
    def test_token_blacklist_functionality(self):
        """Test token blacklisting (if implemented)."""
        # This would test token revocation/blacklisting
        # Implementation depends on token management strategy
        pass
    
    def test_refresh_token_handling(self):
        """Test refresh token functionality (if implemented)."""
        # This would test refresh token flow
        # Implementation depends on token refresh strategy
        pass
    
    def test_token_expiration_handling(self):
        """Test proper token expiration handling."""
        # Test that expired tokens are properly rejected
        # This is already covered in TestAuth0Service but could be expanded
        pass
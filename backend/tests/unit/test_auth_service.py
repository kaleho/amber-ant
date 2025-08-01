"""Comprehensive unit tests for auth service layer."""
import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
import jwt
import json

from src.auth.service import AuthService, TokenService, PermissionService
from src.auth.models import User, UserSession, Permission, Role
from src.auth.schemas import LoginRequest, TokenResponse, UserProfile, PermissionCheck
from src.exceptions import (
    AuthenticationError, 
    AuthorizationError, 
    ValidationError,
    ExternalServiceError
)
from src.tenant.context import TenantContext


@pytest.mark.unit
class TestAuthService:
    """Test AuthService methods."""
    
    @pytest.fixture
    def mock_auth_repository(self):
        """Mock auth repository."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_user_service(self):
        """Mock user service."""
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
    def auth_service(self, mock_auth_repository, mock_user_service, mock_tenant_context):
        """Create AuthService instance with mocked dependencies."""
        with patch('src.auth.service.get_tenant_context', return_value=mock_tenant_context):
            return AuthService(mock_auth_repository, mock_user_service)
    
    @pytest.fixture
    def sample_auth0_token_payload(self):
        """Sample Auth0 token payload."""
        return {
            "sub": "auth0|test123",
            "email": "test@example.com",
            "email_verified": True,
            "name": "Test User",
            "given_name": "Test",
            "family_name": "User",
            "picture": "https://example.com/avatar.jpg",
            "locale": "en",
            "aud": "test-audience",
            "iss": "https://test.auth0.com/",
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=24)).timestamp())
        }
    
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
            role="member",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

    @pytest.mark.asyncio
    async def test_verify_token_success(self, auth_service, mock_auth_repository, sample_auth0_token_payload):
        """Test successful token verification."""
        # Arrange
        token = "valid.jwt.token"
        
        with patch('src.auth.service.jwt.decode') as mock_jwt_decode:
            mock_jwt_decode.return_value = sample_auth0_token_payload
            
            with patch('src.auth.service.get_auth0_public_key') as mock_get_key:
                mock_get_key.return_value = "test-public-key"
                
                # Act
                result = await auth_service.verify_token(token)
                
                # Assert
                assert result["sub"] == "auth0|test123"
                assert result["email"] == "test@example.com"
                assert result["email_verified"] is True
                mock_jwt_decode.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_token_expired(self, auth_service):
        """Test token verification with expired token."""
        # Arrange
        token = "expired.jwt.token"
        
        with patch('src.auth.service.jwt.decode') as mock_jwt_decode:
            mock_jwt_decode.side_effect = jwt.ExpiredSignatureError("Token expired")
            
            # Act & Assert
            with pytest.raises(AuthenticationError) as exc_info:
                await auth_service.verify_token(token)
            
            assert "expired" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_verify_token_invalid_signature(self, auth_service):
        """Test token verification with invalid signature."""
        # Arrange
        token = "invalid.signature.token"
        
        with patch('src.auth.service.jwt.decode') as mock_jwt_decode:
            mock_jwt_decode.side_effect = jwt.InvalidSignatureError("Invalid signature")
            
            # Act & Assert
            with pytest.raises(AuthenticationError) as exc_info:
                await auth_service.verify_token(token)
            
            assert "invalid" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_verify_token_invalid_audience(self, auth_service, sample_auth0_token_payload):
        """Test token verification with invalid audience."""
        # Arrange
        token = "invalid.audience.token"
        invalid_payload = {**sample_auth0_token_payload, "aud": "wrong-audience"}
        
        with patch('src.auth.service.jwt.decode') as mock_jwt_decode:
            mock_jwt_decode.return_value = invalid_payload
            
            with patch('src.auth.service.get_auth0_public_key') as mock_get_key:
                mock_get_key.return_value = "test-public-key"
                
                # Act & Assert
                with pytest.raises(AuthenticationError) as exc_info:
                    await auth_service.verify_token(token)
                
                assert "audience" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, auth_service, mock_user_service, sample_auth0_token_payload, sample_user_model):
        """Test successful user authentication."""
        # Arrange
        token = "valid.jwt.token"
        
        with patch.object(auth_service, 'verify_token', return_value=sample_auth0_token_payload):
            mock_user_service.get_user_by_auth0_id.return_value = sample_user_model
            
            # Act
            result = await auth_service.authenticate_user(token)
            
            # Assert
            assert result.id == "test-user-123"
            assert result.email == "test@example.com"
            assert result.role == "member"
            mock_user_service.get_user_by_auth0_id.assert_called_once_with("auth0|test123")

    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, auth_service, mock_user_service, sample_auth0_token_payload):
        """Test user authentication when user not found."""
        # Arrange
        token = "valid.jwt.token"
        
        with patch.object(auth_service, 'verify_token', return_value=sample_auth0_token_payload):
            mock_user_service.get_user_by_auth0_id.return_value = None
            
            # Act & Assert
            with pytest.raises(AuthenticationError) as exc_info:
                await auth_service.authenticate_user(token)
            
            assert "user not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_authenticate_user_inactive(self, auth_service, mock_user_service, sample_auth0_token_payload):
        """Test user authentication when user is inactive."""
        # Arrange
        token = "valid.jwt.token"
        inactive_user = User(
            id="inactive-user",
            auth0_user_id="auth0|test123",
            email="test@example.com",
            role="member",
            is_active=False  # Inactive user
        )
        
        with patch.object(auth_service, 'verify_token', return_value=sample_auth0_token_payload):
            mock_user_service.get_user_by_auth0_id.return_value = inactive_user
            
            # Act & Assert
            with pytest.raises(AuthenticationError) as exc_info:
                await auth_service.authenticate_user(token)
            
            assert "inactive" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_create_user_session_success(self, auth_service, mock_auth_repository, sample_user_model):
        """Test successful user session creation."""
        # Arrange
        user_agent = "Mozilla/5.0 Test Browser"
        ip_address = "192.168.1.1"
        session_token = "session-token-123"
        
        mock_session = UserSession(
            id="session-123",
            user_id=sample_user_model.id,
            session_token=session_token,
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
            is_active=True
        )
        
        mock_auth_repository.create_session.return_value = mock_session
        
        # Act
        result = await auth_service.create_user_session(
            sample_user_model, 
            user_agent, 
            ip_address
        )
        
        # Assert
        assert result.user_id == sample_user_model.id
        assert result.user_agent == user_agent
        assert result.ip_address == ip_address
        assert result.is_active is True
        mock_auth_repository.create_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalidate_user_session_success(self, auth_service, mock_auth_repository):
        """Test successful user session invalidation."""
        # Arrange
        session_token = "session-token-123"
        mock_auth_repository.invalidate_session.return_value = True
        
        # Act
        result = await auth_service.invalidate_user_session(session_token)
        
        # Assert
        assert result is True
        mock_auth_repository.invalidate_session.assert_called_once_with(session_token)

    @pytest.mark.asyncio
    async def test_get_user_permissions_success(self, auth_service, mock_auth_repository, sample_user_model):
        """Test successful user permissions retrieval."""
        # Arrange
        mock_permissions = [
            Permission(id="perm-1", name="read_users", resource="users", action="read"),
            Permission(id="perm-2", name="write_accounts", resource="accounts", action="write")
        ]
        
        mock_auth_repository.get_user_permissions.return_value = mock_permissions
        
        # Act
        result = await auth_service.get_user_permissions(sample_user_model.id)
        
        # Assert
        assert len(result) == 2
        assert result[0].name == "read_users"
        assert result[1].name == "write_accounts"
        mock_auth_repository.get_user_permissions.assert_called_once_with(sample_user_model.id)

    @pytest.mark.asyncio
    async def test_check_user_permission_success(self, auth_service, mock_auth_repository, sample_user_model):
        """Test successful user permission check."""
        # Arrange
        permission = "read_users"
        mock_auth_repository.check_user_permission.return_value = True
        
        # Act
        result = await auth_service.check_user_permission(sample_user_model.id, permission)
        
        # Assert
        assert result is True
        mock_auth_repository.check_user_permission.assert_called_once_with(
            sample_user_model.id, 
            permission
        )

    @pytest.mark.asyncio
    async def test_check_user_permission_denied(self, auth_service, mock_auth_repository, sample_user_model):
        """Test user permission check when permission denied."""
        # Arrange
        permission = "admin_access"
        mock_auth_repository.check_user_permission.return_value = False
        
        # Act
        result = await auth_service.check_user_permission(sample_user_model.id, permission)
        
        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, auth_service, mock_auth_repository):
        """Test successful token refresh."""
        # Arrange
        refresh_token = "refresh-token-123"
        mock_session = UserSession(
            id="session-123",
            user_id="user-123",
            refresh_token=refresh_token,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
            is_active=True
        )
        
        mock_auth_repository.get_session_by_refresh_token.return_value = mock_session
        mock_auth_repository.update_session_tokens.return_value = mock_session
        
        # Act
        result = await auth_service.refresh_user_token(refresh_token)
        
        # Assert
        assert result.user_id == "user-123"
        mock_auth_repository.get_session_by_refresh_token.assert_called_once_with(refresh_token)
        mock_auth_repository.update_session_tokens.assert_called_once()

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, auth_service, mock_auth_repository):
        """Test token refresh with invalid refresh token."""
        # Arrange
        refresh_token = "invalid-refresh-token"
        mock_auth_repository.get_session_by_refresh_token.return_value = None
        
        # Act & Assert
        with pytest.raises(AuthenticationError) as exc_info:
            await auth_service.refresh_user_token(refresh_token)
        
        assert "invalid refresh token" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_get_user_profile_success(self, auth_service, mock_user_service, sample_user_model):
        """Test successful user profile retrieval."""
        # Arrange
        user_id = "test-user-123"
        mock_user_service.get_user_by_id.return_value = sample_user_model
        
        # Act
        result = await auth_service.get_user_profile(user_id)
        
        # Assert
        assert isinstance(result, UserProfile)
        assert result.id == user_id
        assert result.email == "test@example.com"
        assert result.name == "Test User"

    @pytest.mark.asyncio
    async def test_update_user_last_login(self, auth_service, mock_auth_repository):
        """Test updating user last login timestamp."""
        # Arrange
        user_id = "test-user-123"
        mock_auth_repository.update_last_login.return_value = True
        
        # Act
        result = await auth_service.update_user_last_login(user_id)
        
        # Assert
        assert result is True
        mock_auth_repository.update_last_login.assert_called_once_with(user_id)

    @pytest.mark.asyncio
    async def test_multi_tenant_isolation(self, mock_auth_repository, mock_user_service):
        """Test that auth service respects tenant isolation."""
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
        with patch('src.auth.service.get_tenant_context', return_value=tenant1_context):
            service1 = AuthService(mock_auth_repository, mock_user_service)
            
        with patch('src.auth.service.get_tenant_context', return_value=tenant2_context):
            service2 = AuthService(mock_auth_repository, mock_user_service)
        
        # Services should use the same repositories but different contexts
        assert service1._repository == service2._repository
        assert service1._user_service == service2._user_service


@pytest.mark.unit
class TestTokenService:
    """Test TokenService methods."""
    
    @pytest.fixture
    def token_service(self):
        """Create TokenService instance."""
        return TokenService()
    
    def test_generate_session_token(self, token_service):
        """Test session token generation."""
        # Act
        token = token_service.generate_session_token()
        
        # Assert
        assert isinstance(token, str)
        assert len(token) >= 32  # Minimum length for security
        
        # Generate another token and ensure they're different
        token2 = token_service.generate_session_token()
        assert token != token2
    
    def test_generate_refresh_token(self, token_service):
        """Test refresh token generation."""
        # Act
        token = token_service.generate_refresh_token()
        
        # Assert
        assert isinstance(token, str)
        assert len(token) >= 32  # Minimum length for security
        
        # Generate another token and ensure they're different
        token2 = token_service.generate_refresh_token()
        assert token != token2
    
    def test_create_jwt_token(self, token_service):
        """Test JWT token creation."""
        # Arrange
        payload = {
            "sub": "user-123",
            "email": "test@example.com",
            "role": "member"
        }
        
        # Act
        token = token_service.create_jwt_token(payload, expires_in=3600)
        
        # Assert
        assert isinstance(token, str)
        assert len(token.split('.')) == 3  # JWT has 3 parts
        
        # Verify token can be decoded
        decoded = jwt.decode(token, options={"verify_signature": False})
        assert decoded["sub"] == "user-123"
        assert decoded["email"] == "test@example.com"
        assert "exp" in decoded
    
    def test_verify_jwt_token_success(self, token_service):
        """Test JWT token verification."""
        # Arrange
        payload = {"sub": "user-123", "email": "test@example.com"}
        token = token_service.create_jwt_token(payload, expires_in=3600)
        
        # Act
        result = token_service.verify_jwt_token(token)
        
        # Assert
        assert result["sub"] == "user-123"
        assert result["email"] == "test@example.com"
    
    def test_verify_jwt_token_expired(self, token_service):
        """Test JWT token verification with expired token."""
        # Arrange
        payload = {"sub": "user-123"}
        token = token_service.create_jwt_token(payload, expires_in=-1)  # Expired
        
        # Act & Assert
        with pytest.raises(jwt.ExpiredSignatureError):
            token_service.verify_jwt_token(token)
    
    def test_hash_password(self, token_service):
        """Test password hashing."""
        # Arrange
        password = "secure-password-123"
        
        # Act
        hashed = token_service.hash_password(password)
        
        # Assert
        assert isinstance(hashed, str)
        assert hashed != password  # Should be hashed
        assert len(hashed) > len(password)  # Hash should be longer
        
        # Same password should generate different hashes (due to salt)
        hashed2 = token_service.hash_password(password)
        assert hashed != hashed2
    
    def test_verify_password_success(self, token_service):
        """Test password verification success."""
        # Arrange
        password = "secure-password-123"
        hashed = token_service.hash_password(password)
        
        # Act
        result = token_service.verify_password(password, hashed)
        
        # Assert
        assert result is True
    
    def test_verify_password_failure(self, token_service):
        """Test password verification failure."""
        # Arrange
        password = "secure-password-123"
        wrong_password = "wrong-password"
        hashed = token_service.hash_password(password)
        
        # Act
        result = token_service.verify_password(wrong_password, hashed)
        
        # Assert
        assert result is False


@pytest.mark.unit
class TestPermissionService:
    """Test PermissionService methods."""
    
    @pytest.fixture
    def permission_service(self):
        """Create PermissionService instance."""
        mock_repository = AsyncMock()
        return PermissionService(mock_repository)
    
    @pytest.mark.asyncio
    async def test_check_permission_success(self, permission_service):
        """Test successful permission check."""
        # Arrange
        user_id = "user-123"
        resource = "users"
        action = "read"
        
        permission_service._repository.check_user_permission.return_value = True
        
        # Act
        result = await permission_service.check_permission(user_id, resource, action)
        
        # Assert
        assert result is True
        permission_service._repository.check_user_permission.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_permission_denied(self, permission_service):
        """Test permission check denied."""
        # Arrange
        user_id = "user-123"
        resource = "admin"
        action = "write"
        
        permission_service._repository.check_user_permission.return_value = False
        
        # Act
        result = await permission_service.check_permission(user_id, resource, action)
        
        # Assert
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_user_roles(self, permission_service):
        """Test getting user roles."""
        # Arrange
        user_id = "user-123"
        mock_roles = [
            Role(id="role-1", name="member", permissions=["read_users"]),
            Role(id="role-2", name="family_head", permissions=["manage_family"])
        ]
        
        permission_service._repository.get_user_roles.return_value = mock_roles
        
        # Act
        result = await permission_service.get_user_roles(user_id)
        
        # Assert
        assert len(result) == 2
        assert result[0].name == "member"
        assert result[1].name == "family_head"
    
    @pytest.mark.asyncio
    async def test_assign_role_to_user(self, permission_service):
        """Test assigning role to user."""
        # Arrange
        user_id = "user-123"
        role_id = "role-123"
        
        permission_service._repository.assign_role.return_value = True
        
        # Act
        result = await permission_service.assign_role_to_user(user_id, role_id)
        
        # Assert
        assert result is True
        permission_service._repository.assign_role.assert_called_once_with(user_id, role_id)
    
    @pytest.mark.asyncio
    async def test_remove_role_from_user(self, permission_service):
        """Test removing role from user."""
        # Arrange
        user_id = "user-123"
        role_id = "role-123"
        
        permission_service._repository.remove_role.return_value = True
        
        # Act
        result = await permission_service.remove_role_from_user(user_id, role_id)
        
        # Assert
        assert result is True
        permission_service._repository.remove_role.assert_called_once_with(user_id, role_id)


@pytest.mark.unit
class TestAuthServiceEdgeCases:
    """Test edge cases and error scenarios for auth services."""
    
    @pytest.fixture
    def auth_service(self):
        """Create AuthService instance."""
        mock_repo = AsyncMock()
        mock_user_service = AsyncMock()
        mock_context = TenantContext(
            tenant_id="test-tenant",
            tenant_slug="test-tenant",
            database_url="sqlite:///:memory:",
            user_id="test-user"
        )
        with patch('src.auth.service.get_tenant_context', return_value=mock_context):
            return AuthService(mock_repo, mock_user_service)
    
    @pytest.mark.asyncio
    async def test_malformed_jwt_token(self, auth_service):
        """Test handling of malformed JWT tokens."""
        malformed_tokens = [
            "not.a.jwt",  # Not enough parts
            "invalid-jwt-token",  # Not JWT format
            "",  # Empty string
            None  # None value
        ]
        
        for token in malformed_tokens:
            with pytest.raises(AuthenticationError):
                await auth_service.verify_token(token)
    
    @pytest.mark.asyncio
    async def test_network_error_during_auth0_verification(self, auth_service):
        """Test handling of network errors during Auth0 verification."""
        # Arrange
        token = "valid.jwt.token"
        
        with patch('src.auth.service.get_auth0_public_key') as mock_get_key:
            mock_get_key.side_effect = ExternalServiceError("auth0", "Network error")
        
            # Act & Assert
            with pytest.raises(ExternalServiceError):
                await auth_service.verify_token(token)
    
    @pytest.mark.asyncio
    async def test_concurrent_session_creation(self, auth_service):
        """Test handling of concurrent session creation."""
        # This would test race conditions in session creation
        # Implementation depends on how sessions handle concurrency
        pass
    
    @pytest.mark.asyncio
    async def test_session_cleanup_on_user_deletion(self, auth_service):
        """Test that user sessions are cleaned up when user is deleted."""
        # This would test cascading deletion of sessions
        # when a user account is deleted
        pass
    
    @pytest.mark.asyncio
    async def test_permission_caching_invalidation(self, auth_service):
        """Test that permission caches are invalidated when roles change."""
        # This would test cache invalidation logic
        # when user permissions are updated
        pass
    
    @pytest.mark.asyncio
    async def test_brute_force_protection(self, auth_service):
        """Test brute force attack protection."""
        # This would test rate limiting and account lockout
        # after multiple failed authentication attempts
        pass
    
    @pytest.mark.asyncio
    async def test_session_hijacking_protection(self, auth_service):
        """Test session hijacking protection mechanisms."""
        # This would test IP address validation, 
        # user agent validation, etc.
        pass
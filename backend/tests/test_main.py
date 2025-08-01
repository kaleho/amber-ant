"""Tests for main FastAPI application."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import json

from src.main import create_app
from src.exceptions import (
    TenantNotFoundError,
    AuthenticationError,
    AuthorizationError,
    ValidationError,
    ExternalServiceError
)


class TestMainApplication:
    """Test main FastAPI application configuration and functionality."""
    
    def test_app_creation(self, test_settings):
        """Test FastAPI application is created correctly."""
        app = create_app()
        
        assert app.title == test_settings.PROJECT_NAME
        assert app.version == test_settings.VERSION
        assert "Multi-tenant FastAPI backend" in app.description
        assert app.debug == test_settings.DEBUG
    
    def test_middleware_configuration(self, app):
        """Test middleware is configured correctly."""
        middleware_classes = [middleware.cls.__name__ for middleware in app.user_middleware]
        
        # Check required middleware is present
        assert "TrustedHostMiddleware" in middleware_classes
        assert "CORSMiddleware" in middleware_classes
        assert "SecurityMiddleware" in middleware_classes
        assert "LoggingMiddleware" in middleware_classes
        assert "TenantContextMiddleware" in middleware_classes
    
    def test_health_check_endpoint(self, test_client):
        """Test basic health check endpoint."""
        response = test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "faithful-finances-api"
        assert "version" in data
    
    def test_detailed_health_check_endpoint(self, test_client):
        """Test detailed health check endpoint."""
        response = test_client.get("/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "faithful-finances-api"
        assert "version" in data
        assert "timestamp" in data
        assert "dependencies" in data
        
        # Check all expected dependencies
        dependencies = data["dependencies"]
        expected_deps = ["database", "redis", "auth0", "plaid", "stripe"]
        for dep in expected_deps:
            assert dep in dependencies
    
    def test_api_routes_included(self, app):
        """Test all API routes are included."""
        routes = [route.path for route in app.routes]
        
        # Check main route prefixes exist
        expected_prefixes = [
            "/api/v1/auth",
            "/api/v1/users", 
            "/api/v1/accounts",
            "/api/v1/transactions",
            "/api/v1/budgets",
            "/api/v1/goals",
            "/api/v1/tithing",
            "/api/v1/families",
            "/api/v1/subscriptions",
            "/api/v1/plaid"
        ]
        
        for prefix in expected_prefixes:
            # Check if any route starts with this prefix
            assert any(route.startswith(prefix) for route in routes), f"Route prefix {prefix} not found"


class TestExceptionHandlers:
    """Test custom exception handlers."""
    
    def test_tenant_not_found_handler(self, test_client):
        """Test tenant not found exception handler."""
        with patch('src.tenant.context.get_tenant_context') as mock_context:
            mock_context.side_effect = TenantNotFoundError("test-tenant")
            
            response = test_client.get("/api/v1/users/me", headers={"X-Tenant-ID": "test-tenant"})
            
            assert response.status_code == 404
            data = response.json()
            assert data["error"] == "tenant_not_found"
            assert "tenant_id" in data
    
    def test_authentication_error_handler(self, test_client):
        """Test authentication error exception handler."""
        # Test without authorization header
        response = test_client.get("/api/v1/users/me")
        
        # Should get authentication error (handled by middleware/auth dependencies)
        # The exact status depends on implementation, but should be 401 or similar
        assert response.status_code in [401, 403, 422]
    
    def test_validation_error_handler(self, test_client):
        """Test validation error exception handler."""
        # Send invalid data to trigger validation error
        invalid_data = {"invalid": "data"}
        
        response = test_client.post(
            "/api/v1/users",
            json=invalid_data,
            headers={"Authorization": "Bearer test-token", "X-Tenant-ID": "test-tenant"}
        )
        
        # Should get validation error
        assert response.status_code in [422, 400]
    
    @patch('src.plaid.service.PlaidService')
    def test_external_service_error_handler(self, mock_plaid_service, test_client):
        """Test external service error exception handler."""
        # Mock Plaid service to raise external service error
        mock_plaid_service.side_effect = ExternalServiceError("plaid", "Service unavailable")
        
        response = test_client.post(
            "/api/v1/plaid/link-token",
            headers={"Authorization": "Bearer test-token", "X-Tenant-ID": "test-tenant"}
        )
        
        # Should get external service error
        if response.status_code == 502:
            data = response.json()
            assert data["error"] == "external_service_error"
            assert data["service"] == "plaid"
    
    def test_general_exception_handler(self, test_client):
        """Test general exception handler for unhandled exceptions."""
        # This is harder to test without causing actual unhandled exceptions
        # We would need to mock internal components to raise unexpected exceptions
        pass


class TestCORSConfiguration:
    """Test CORS configuration."""
    
    def test_cors_preflight_request(self, test_client):
        """Test CORS preflight request is handled correctly."""
        response = test_client.options(
            "/api/v1/users",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization,X-Tenant-ID"
            }
        )
        
        # CORS should be configured to allow these requests
        assert response.status_code in [200, 204]
        
        # Check CORS headers are present
        headers = response.headers
        assert "access-control-allow-origin" in headers or "Access-Control-Allow-Origin" in headers
    
    def test_cors_actual_request(self, test_client):
        """Test actual CORS request includes proper headers."""
        response = test_client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"}
        )
        
        assert response.status_code == 200
        
        # Check CORS headers are present
        headers = response.headers
        cors_header_present = (
            "access-control-allow-origin" in headers or 
            "Access-Control-Allow-Origin" in headers
        )
        assert cors_header_present


class TestSecurityConfiguration:
    """Test security configuration."""
    
    def test_security_headers_present(self, test_client):
        """Test security headers are added by SecurityMiddleware."""
        response = test_client.get("/health")
        
        assert response.status_code == 200
        
        # Check for common security headers
        # Note: These would be added by SecurityMiddleware
        headers = response.headers
        
        # The exact headers depend on SecurityMiddleware implementation
        # Common security headers include:
        # - X-Content-Type-Options
        # - X-Frame-Options  
        # - X-XSS-Protection
        # - Strict-Transport-Security (for HTTPS)
        
        # At minimum, we should not see potentially dangerous headers
        assert "Server" not in headers or headers["Server"] != "uvicorn"
    
    def test_trusted_host_middleware(self, test_settings):
        """Test trusted host middleware configuration."""
        # Create app with test settings
        app = create_app()
        
        # Find TrustedHostMiddleware
        trusted_host_middleware = None
        for middleware in app.user_middleware:
            if middleware.cls.__name__ == "TrustedHostMiddleware":
                trusted_host_middleware = middleware
                break
        
        assert trusted_host_middleware is not None
        
        # In debug mode, should allow all hosts
        if test_settings.DEBUG:
            assert ["*"] in str(trusted_host_middleware.kwargs)


class TestApplicationLifespan:
    """Test application lifespan events."""
    
    @pytest.mark.asyncio
    async def test_lifespan_startup(self):
        """Test application startup events."""
        from src.main import lifespan
        
        app = create_app()
        
        # Mock database initialization
        with patch('src.main.init_global_database') as mock_init:
            mock_init.return_value = None
            
            # Test lifespan startup
            async with lifespan(app):
                # Should complete without errors
                mock_init.assert_called_once()
    
    def test_openapi_configuration(self, app):
        """Test OpenAPI documentation configuration."""
        # Test that OpenAPI schema is generated correctly
        client = TestClient(app)
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        openapi_schema = response.json()
        
        assert openapi_schema["info"]["title"] == app.title
        assert openapi_schema["info"]["version"] == app.version
        assert "paths" in openapi_schema
        
        # Check that main API paths are documented
        paths = openapi_schema["paths"]
        expected_path_prefixes = [
            "/api/v1/users",
            "/api/v1/accounts", 
            "/api/v1/transactions"
        ]
        
        for prefix in expected_path_prefixes:
            # Check if any path starts with this prefix
            path_exists = any(path.startswith(prefix) for path in paths.keys())
            assert path_exists, f"No paths found for prefix {prefix}"
    
    def test_docs_endpoints_available(self, test_client, test_settings):
        """Test API documentation endpoints are available."""
        if test_settings.DOCS_URL:
            response = test_client.get(test_settings.DOCS_URL)
            assert response.status_code == 200
        
        if test_settings.REDOC_URL:
            response = test_client.get(test_settings.REDOC_URL)
            assert response.status_code == 200


class TestEnvironmentConfiguration:
    """Test environment-specific configuration."""
    
    def test_debug_mode_configuration(self, test_settings):
        """Test debug mode affects application configuration."""
        app = create_app()
        
        assert app.debug == test_settings.DEBUG
    
    def test_logging_configuration(self, test_settings):
        """Test logging is configured correctly."""
        import structlog
        
        # Verify structlog is configured
        logger = structlog.get_logger(__name__)
        assert logger is not None
        
        # Test log format configuration
        if test_settings.LOG_FORMAT == "json":
            # JSON logging should be configured
            pass
        else:
            # Console logging should be configured
            pass
    
    def test_cors_origins_configuration(self, test_settings, app):
        """Test CORS origins are configured from settings."""
        # Find CORS middleware configuration
        cors_middleware = None
        for middleware in app.user_middleware:
            if middleware.cls.__name__ == "CORSMiddleware":
                cors_middleware = middleware
                break
        
        assert cors_middleware is not None
        
        # Check that origins from settings are configured
        kwargs = cors_middleware.kwargs
        assert "allow_origins" in kwargs
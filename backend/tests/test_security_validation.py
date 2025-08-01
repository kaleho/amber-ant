"""Test security validation utilities."""
import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock

from src.security.validation import InputValidator, input_validator


class TestInputValidator:
    """Test cases for InputValidator class."""

    def test_sanitize_string_basic(self):
        """Test basic string sanitization."""
        validator = InputValidator()
        
        # Test normal string
        result = validator.sanitize_string("Hello World")
        assert result == "Hello World"
        
        # Test string with HTML
        result = validator.sanitize_string("<script>alert('xss')</script>", allow_html=False)
        assert "<script>" not in result
        assert "&lt;script&gt;" in result
        
        # Test length limit
        result = validator.sanitize_string("A" * 100, max_length=50)
        assert len(result) == 50
        
        # Test whitespace stripping
        result = validator.sanitize_string("  hello  ")
        assert result == "hello"

    def test_sanitize_string_xss_detection(self):
        """Test XSS pattern detection and removal."""
        validator = InputValidator()
        
        xss_inputs = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "onload=alert('xss')",
            "<iframe src='evil.com'></iframe>"
        ]
        
        for xss_input in xss_inputs:
            result = validator.sanitize_string(xss_input)
            # Should not contain dangerous patterns
            assert "script" not in result.lower() or "&lt;" in result
            assert "javascript:" not in result.lower()
            assert "onload=" not in result.lower()
            assert "iframe" not in result.lower() or "&lt;" in result

    def test_validate_email(self):
        """Test email validation."""
        validator = InputValidator()
        
        # Valid emails
        valid_emails = [
            "user@example.com",
            "test.email+tag@domain.co.uk",
            "valid123@test-domain.org"
        ]
        
        for email in valid_emails:
            assert validator.validate_email(email) is True
        
        # Invalid emails
        invalid_emails = [
            "invalid-email",
            "@domain.com",
            "user@",
            "user@domain",
            "javascript:alert('xss')@domain.com",
            "<script>@domain.com",
            "a" * 250 + "@domain.com"  # Too long
        ]
        
        for email in invalid_emails:
            assert validator.validate_email(email) is False

    def test_validate_phone_number(self):
        """Test phone number validation and normalization."""
        validator = InputValidator()
        
        # Valid US phone numbers
        test_cases = [
            ("1234567890", "+11234567890"),
            ("(123) 456-7890", "+11234567890"),
            "+1-123-456-7890", "+11234567890"),
            ("123.456.7890", "+11234567890"),
            ("11234567890", "+11234567890")
        ]
        
        for input_phone, expected in test_cases:
            result = validator.validate_phone_number(input_phone)
            assert result == expected
        
        # Invalid phone numbers
        invalid_phones = [
            "123",  # Too short
            "12345",  # Too short
            "",  # Empty
            "abc1234567890",  # Contains letters (but digits will be extracted)
        ]
        
        result = validator.validate_phone_number("123")
        assert result is None

    def test_validate_currency_amount(self):
        """Test currency amount validation."""
        validator = InputValidator()
        
        # Valid amounts
        valid_amounts = [
            ("100.00", Decimal("100.00")),
            ("1,234.56", Decimal("1234.56")),
            ("$50.25", Decimal("50.25")),
            (100, Decimal("100")),
            (Decimal("75.99"), Decimal("75.99"))
        ]
        
        for input_amount, expected in valid_amounts:
            result = validator.validate_currency_amount(input_amount)
            assert result == expected
        
        # Invalid amounts
        invalid_amounts = [
            "abc",  # Non-numeric
            "100.123",  # Too many decimal places
            "",  # Empty
            None  # None
        ]
        
        for invalid_amount in invalid_amounts:
            result = validator.validate_currency_amount(invalid_amount)
            assert result is None
        
        # Test range validation
        result = validator.validate_currency_amount("50", min_amount=Decimal("100"))
        assert result is None  # Below minimum
        
        result = validator.validate_currency_amount("200", max_amount=Decimal("100"))
        assert result is None  # Above maximum

    def test_validate_url(self):
        """Test URL validation."""
        validator = InputValidator()
        
        # Valid URLs
        valid_urls = [
            "https://example.com",
            "http://test.org/path",
            "https://sub.domain.com/path?query=value"
        ]
        
        for url in valid_urls:
            assert validator.validate_url(url) is True
        
        # Invalid URLs
        invalid_urls = [
            "javascript:alert('xss')",
            "data:text/html,<script>",
            "file:///etc/passwd",
            "ftp://example.com",  # Not in allowed schemes
            "not-a-url",
            ""
        ]
        
        for url in invalid_urls:
            assert validator.validate_url(url) is False
        
        # Test custom allowed schemes
        assert validator.validate_url("ftp://example.com", allowed_schemes=["ftp"]) is True

    def test_sanitize_filename(self):
        """Test filename sanitization."""
        validator = InputValidator()
        
        # Test cases
        test_cases = [
            ("normal_file.txt", "normal_file.txt"),
            ("file with spaces.txt", "file_with_spaces.txt"),
            ("../../../etc/passwd", ".._.._.._.._etc_passwd"),
            ("file<>:\"|?*.txt", "file________.txt"),
            ("", "unnamed_file"),
            ("." * 300 + ".txt", None)  # Will be truncated
        ]
        
        for input_filename, expected in test_cases:
            result = validator.sanitize_filename(input_filename)
            if expected is None:
                assert len(result) <= 255
            else:
                assert result == expected

    def test_validate_json_structure(self):
        """Test JSON structure validation."""
        validator = InputValidator()
        
        # Valid JSON structures
        valid_data = [
            {"name": "test", "value": 123},
            {"nested": {"data": "value"}},
            {"array": [1, 2, 3]}
        ]
        
        for data in valid_data:
            assert validator.validate_json_structure(data) is True
        
        # Test required fields
        data = {"name": "test"}
        assert validator.validate_json_structure(data, required_fields=["name"]) is True
        assert validator.validate_json_structure(data, required_fields=["missing"]) is False
        
        # Test depth limits
        deep_data = {"a": {"b": {"c": {"d": {"e": "value"}}}}}
        assert validator.validate_json_structure(deep_data, max_depth=5) is True
        assert validator.validate_json_structure(deep_data, max_depth=3) is False
        
        # Test key limits
        large_data = {f"key_{i}": i for i in range(150)}
        assert validator.validate_json_structure(large_data, max_keys=200) is True
        assert validator.validate_json_structure(large_data, max_keys=100) is False

    def test_validate_and_sanitize_input(self):
        """Test comprehensive input validation and sanitization."""
        validator = InputValidator()
        
        # Define field configuration
        field_config = {
            "name": {"type": "string", "max_length": 50, "required": True},
            "email": {"type": "email", "required": True},
            "amount": {"type": "currency", "min_amount": Decimal("0"), "max_amount": Decimal("1000")},
            "website": {"type": "url", "required": False},
            "description": {"type": "string", "allow_html": False}
        }
        
        # Valid input data
        input_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "amount": "150.50",
            "website": "https://johndoe.com",
            "description": "<p>This is a description</p>"
        }
        
        result = validator.validate_and_sanitize_input(input_data, field_config)
        
        assert result["name"] == "John Doe"
        assert result["email"] == "john@example.com"
        assert result["amount"] == Decimal("150.50")
        assert result["website"] == "https://johndoe.com"
        assert "&lt;p&gt;" in result["description"]  # HTML escaped
        
        # Test missing required field
        invalid_data = {"name": "John"}  # Missing required email
        
        with pytest.raises(ValueError, match="Required field missing: email"):
            validator.validate_and_sanitize_input(invalid_data, field_config)
        
        # Test invalid field value
        invalid_data = {
            "name": "John Doe",
            "email": "invalid-email",
            "amount": "150.50"
        }
        
        with pytest.raises(ValueError, match="Invalid email format"):
            validator.validate_and_sanitize_input(invalid_data, field_config)

    def test_sql_injection_detection(self):
        """Test SQL injection pattern detection."""
        validator = InputValidator()
        
        sql_injections = [
            "1' OR '1'='1",
            "admin'--",
            "1; DROP TABLE users;",
            "UNION SELECT * FROM passwords",
            "/* malicious comment */ SELECT"
        ]
        
        for injection in sql_injections:
            # These should be detected in the private method
            assert validator._contains_sql_injection_patterns(injection) is True
        
        # Safe inputs
        safe_inputs = [
            "normal text",
            "user@domain.com",
            "regular search query"
        ]
        
        for safe_input in safe_inputs:
            assert validator._contains_sql_injection_patterns(safe_input) is False

    def test_path_traversal_detection(self):
        """Test path traversal pattern detection."""
        validator = InputValidator()
        
        traversal_attempts = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32",
            "%2e%2e%2fetc%2fpasswd",
            "....//....//etc/passwd"
        ]
        
        for attempt in traversal_attempts:
            assert validator._contains_path_traversal_patterns(attempt) is True
        
        # Safe paths
        safe_paths = [
            "normal/file/path",
            "document.pdf",
            "folder/subfolder/file.txt"
        ]
        
        for safe_path in safe_paths:
            assert validator._contains_path_traversal_patterns(safe_path) is False

    @patch('src.security.validation.logger')
    def test_logging_integration(self, mock_logger):
        """Test that security events are properly logged."""
        validator = InputValidator()
        
        # Test XSS detection logging
        validator.sanitize_string("<script>alert('xss')</script>")
        mock_logger.warning.assert_called()
        
        # Test currency validation logging
        validator.validate_currency_amount("invalid")
        mock_logger.warning.assert_called()


class TestGlobalValidator:
    """Test the global input validator instance."""

    def test_global_validator_instance(self):
        """Test that global validator instance works correctly."""
        # Test that we can import and use the global instance
        assert input_validator is not None
        
        # Test basic functionality
        result = input_validator.sanitize_string("test")
        assert result == "test"
        
        result = input_validator.validate_email("test@example.com")
        assert result is True


@pytest.fixture
def mock_logger():
    """Mock logger fixture."""
    with patch('src.security.validation.logger') as mock:
        yield mock


class TestInputValidatorIntegration:
    """Integration tests for InputValidator with other components."""

    def test_integration_with_fastapi_request(self):
        """Test integration with FastAPI request validation."""
        validator = InputValidator()
        
        # Simulate FastAPI request data
        request_data = {
            "user_input": "<script>alert('xss')</script>",
            "email": "user@example.com",
            "amount": "$99.99"
        }
        
        # Configuration for API endpoint
        field_config = {
            "user_input": {"type": "string", "allow_html": False},
            "email": {"type": "email"},
            "amount": {"type": "currency"}
        }
        
        sanitized = validator.validate_and_sanitize_input(request_data, field_config)
        
        # Verify sanitization
        assert "<script>" not in sanitized["user_input"]
        assert sanitized["email"] == "user@example.com"
        assert sanitized["amount"] == Decimal("99.99")

    def test_performance_with_large_inputs(self):
        """Test validator performance with large inputs."""
        validator = InputValidator()
        
        # Test with large string
        large_string = "A" * 10000
        result = validator.sanitize_string(large_string, max_length=1000)
        assert len(result) == 1000
        
        # Test with large JSON structure
        large_json = {"data": [{"item": i} for i in range(1000)]}
        result = validator.validate_json_structure(large_json, max_keys=2000)
        assert result is True

    def test_edge_cases_and_unicode(self):
        """Test edge cases and Unicode handling."""
        validator = InputValidator()
        
        # Unicode strings
        unicode_string = "测试 中文 🚀 emoji"
        result = validator.sanitize_string(unicode_string)
        assert result == unicode_string
        
        # Empty and None inputs
        assert validator.sanitize_string("") == ""
        assert validator.sanitize_string(None) == "None"
        
        # Very long email
        long_email = "a" * 300 + "@example.com"
        assert validator.validate_email(long_email) is False
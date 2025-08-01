"""Enhanced input validation and sanitization utilities."""
import re
import html
import urllib.parse
from typing import Any, Dict, List, Optional, Union
import structlog
from decimal import Decimal, InvalidOperation

logger = structlog.get_logger(__name__)


class InputValidator:
    """Enhanced input validation and sanitization."""
    
    def __init__(self):
        # Common dangerous patterns
        self.sql_injection_patterns = [
            r"(\s*(union|select|insert|update|delete|drop|create|alter|exec|execute)\s+)",
            r"(/\*.*?\*/)",  # SQL comments
            r"(--[^\r\n]*)",  # Single line comments
            r"(\s*;\s*)",  # Statement separators
        ]
        
        self.xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"vbscript:",
            r"onload\s*=",
            r"onerror\s*=",
            r"onclick\s*=",
            r"<iframe[^>]*>",
            r"<embed[^>]*>",
            r"<object[^>]*>",
        ]
        
        self.path_traversal_patterns = [
            r"\.\./",
            r"\.\.\\",
            r"%2e%2e%2f",
            r"%2e%2e\\",
        ]
    
    def sanitize_string(
        self, 
        value: str, 
        max_length: Optional[int] = None,
        allow_html: bool = False,
        strip_whitespace: bool = True
    ) -> str:
        """
        Sanitize string input.
        
        Args:
            value: Input string to sanitize
            max_length: Maximum allowed length
            allow_html: Whether to allow HTML (will be escaped if False)
            strip_whitespace: Whether to strip leading/trailing whitespace
            
        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            value = str(value)
        
        if strip_whitespace:
            value = value.strip()
        
        # Length validation
        if max_length and len(value) > max_length:
            logger.warning(f"String input truncated from {len(value)} to {max_length} characters")
            value = value[:max_length]
        
        # HTML escaping
        if not allow_html:
            value = html.escape(value, quote=True)
        
        # Check for XSS patterns
        if self._contains_xss_patterns(value):
            logger.warning("Potential XSS pattern detected in input", input_preview=value[:100])
            # Additional sanitization for XSS
            for pattern in self.xss_patterns:
                value = re.sub(pattern, "", value, flags=re.IGNORECASE)
        
        return value
    
    def validate_email(self, email: str) -> bool:
        """Validate email format with comprehensive regex."""
        if not email or len(email) > 254:  # RFC 5321 limit
            return False
        
        # More comprehensive email regex
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(pattern, email):
            return False
        
        # Check for common malicious patterns
        dangerous_patterns = ["javascript:", "vbscript:", "<script", "data:"]
        email_lower = email.lower()
        
        return not any(pattern in email_lower for pattern in dangerous_patterns)
    
    def validate_phone_number(self, phone: str) -> Optional[str]:
        """Validate and normalize phone number."""
        if not phone:
            return None
        
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)
        
        # Validate length (US format)
        if len(digits) == 10:
            return f"+1{digits}"
        elif len(digits) == 11 and digits.startswith('1'):
            return f"+{digits}"
        elif len(digits) > 11:
            # International format - basic validation
            if digits.startswith('1'):
                return f"+{digits}"
        
        return None
    
    def validate_currency_amount(
        self, 
        amount: Union[str, int, float, Decimal],
        min_amount: Optional[Decimal] = None,
        max_amount: Optional[Decimal] = None
    ) -> Optional[Decimal]:
        """Validate and normalize currency amount."""
        try:
            if isinstance(amount, str):
                # Remove currency symbols and whitespace
                amount = re.sub(r'[$,\s]', '', amount)
            
            decimal_amount = Decimal(str(amount))
            
            # Validate precision (max 2 decimal places for currency)
            if decimal_amount.as_tuple().exponent < -2:
                logger.warning(f"Currency amount has too many decimal places: {amount}")
                return None
            
            # Range validation
            if min_amount is not None and decimal_amount < min_amount:
                logger.warning(f"Currency amount below minimum: {decimal_amount} < {min_amount}")
                return None
            
            if max_amount is not None and decimal_amount > max_amount:
                logger.warning(f"Currency amount above maximum: {decimal_amount} > {max_amount}")
                return None
            
            return decimal_amount
            
        except (InvalidOperation, ValueError, TypeError):
            logger.warning(f"Invalid currency amount format: {amount}")
            return None
    
    def validate_url(self, url: str, allowed_schemes: List[str] = None) -> bool:
        """Validate URL format and scheme."""
        if not url:
            return False
        
        if allowed_schemes is None:
            allowed_schemes = ['http', 'https']
        
        try:
            parsed = urllib.parse.urlparse(url)
            
            # Check scheme
            if parsed.scheme not in allowed_schemes:
                return False
            
            # Check for basic malicious patterns
            dangerous_patterns = ["javascript:", "vbscript:", "data:", "file:"]
            url_lower = url.lower()
            
            if any(pattern in url_lower for pattern in dangerous_patterns):
                return False
            
            # Basic domain validation
            if not parsed.netloc:
                return False
            
            return True
            
        except Exception:
            return False
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage."""
        if not filename:
            return "unnamed_file"
        
        # Remove path traversal attempts
        filename = re.sub(r'[/\\:*?"<>|]', '_', filename)
        
        # Remove leading dots and spaces
        filename = filename.lstrip('. ')
        
        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            max_name_length = 250 - len(ext)
            filename = name[:max_name_length] + ('.' + ext if ext else '')
        
        # Ensure it's not empty
        if not filename:
            filename = "unnamed_file"
        
        return filename
    
    def validate_json_structure(
        self, 
        data: Dict[str, Any], 
        required_fields: List[str] = None,
        max_depth: int = 10,
        max_keys: int = 100
    ) -> bool:
        """Validate JSON structure for safety."""
        if not isinstance(data, dict):
            return False
        
        # Check required fields
        if required_fields:
            for field in required_fields:
                if field not in data:
                    logger.warning(f"Missing required field: {field}")
                    return False
        
        # Check structure limits
        if not self._validate_json_limits(data, max_depth, max_keys, 0):
            return False
        
        return True
    
    def _validate_json_limits(
        self, 
        obj: Any, 
        max_depth: int, 
        max_keys: int, 
        current_depth: int
    ) -> bool:
        """Recursively validate JSON structure limits."""
        if current_depth > max_depth:
            logger.warning(f"JSON depth exceeds limit: {current_depth} > {max_depth}")
            return False
        
        if isinstance(obj, dict):
            if len(obj) > max_keys:
                logger.warning(f"JSON object has too many keys: {len(obj)} > {max_keys}")
                return False
            
            for value in obj.values():
                if not self._validate_json_limits(value, max_depth, max_keys, current_depth + 1):
                    return False
        
        elif isinstance(obj, list):
            if len(obj) > max_keys:
                logger.warning(f"JSON array has too many items: {len(obj)} > {max_keys}")
                return False
            
            for item in obj:
                if not self._validate_json_limits(item, max_depth, max_keys, current_depth + 1):
                    return False
        
        return True
    
    def _contains_sql_injection_patterns(self, value: str) -> bool:
        """Check if string contains SQL injection patterns."""
        value_lower = value.lower()
        return any(
            re.search(pattern, value_lower, re.IGNORECASE)
            for pattern in self.sql_injection_patterns
        )
    
    def _contains_xss_patterns(self, value: str) -> bool:
        """Check if string contains XSS patterns."""
        value_lower = value.lower()
        return any(
            re.search(pattern, value_lower, re.IGNORECASE)
            for pattern in self.xss_patterns
        )
    
    def _contains_path_traversal_patterns(self, value: str) -> bool:
        """Check if string contains path traversal patterns."""
        value_lower = value.lower()
        return any(
            re.search(pattern, value_lower, re.IGNORECASE)
            for pattern in self.path_traversal_patterns
        )
    
    def validate_and_sanitize_input(
        self,
        data: Dict[str, Any],
        field_config: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate and sanitize input data based on field configuration.
        
        Args:
            data: Input data dictionary
            field_config: Configuration for each field
            
        Returns:
            Sanitized data dictionary
        """
        sanitized = {}
        
        for field, config in field_config.items():
            if field not in data:
                if config.get('required', False):
                    raise ValueError(f"Required field missing: {field}")
                continue
            
            value = data[field]
            field_type = config.get('type', 'string')
            
            try:
                if field_type == 'string':
                    sanitized[field] = self.sanitize_string(
                        value,
                        max_length=config.get('max_length'),
                        allow_html=config.get('allow_html', False)
                    )
                elif field_type == 'email':
                    if self.validate_email(value):
                        sanitized[field] = value.lower().strip()
                    else:
                        raise ValueError(f"Invalid email format: {field}")
                elif field_type == 'currency':
                    amount = self.validate_currency_amount(
                        value,
                        min_amount=config.get('min_amount'),
                        max_amount=config.get('max_amount')
                    )
                    if amount is not None:
                        sanitized[field] = amount
                    else:
                        raise ValueError(f"Invalid currency amount: {field}")
                elif field_type == 'url':
                    if self.validate_url(value, config.get('allowed_schemes')):
                        sanitized[field] = value
                    else:
                        raise ValueError(f"Invalid URL format: {field}")
                else:
                    # Default: basic sanitization
                    sanitized[field] = self.sanitize_string(str(value))
                    
            except Exception as e:
                logger.warning(f"Field validation failed: {field}", error=str(e))
                if config.get('required', False):
                    raise
                # Skip optional fields that fail validation
        
        return sanitized


# Global input validator instance
input_validator = InputValidator()
"""Shared utility functions."""
import hashlib
import secrets
from typing import Any, Dict, Optional
from cryptography.fernet import Fernet
import base64
import logging

from src.config import settings

logger = logging.getLogger(__name__)


def create_fernet_key() -> Fernet:
    """Create Fernet encryption key from settings with secure key derivation."""
    try:
        from src.security.key_manager import key_manager
        
        # Use secure key derivation
        derived_key = key_manager.derive_encryption_key(
            password=settings.ENCRYPTION_KEY,
            salt=b"faithful_finances_salt_v1"  # Static salt for consistency
        )
        
        return key_manager.create_fernet_cipher(derived_key)
        
    except ImportError:
        # Fallback to original implementation if security module unavailable
        logger.warning("Using fallback encryption key derivation")
        if len(settings.ENCRYPTION_KEY) == 32:
            key = base64.urlsafe_b64encode(settings.ENCRYPTION_KEY.encode()[:32])
        else:
            key = settings.ENCRYPTION_KEY.encode()
        
        return Fernet(key)
    except Exception as e:
        logger.error(f"Encryption key derivation failed: {e}")
        raise ValueError("Failed to create encryption key")


def encrypt_token(token: str) -> str:
    """Encrypt a token for secure storage."""
    try:
        fernet = create_fernet_key()
        encrypted = fernet.encrypt(token.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    except Exception as e:
        logger.error(f"Failed to encrypt token: {e}")
        raise


def decrypt_token(encrypted_token: str) -> str:
    """Decrypt a stored token."""
    try:
        fernet = create_fernet_key()
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_token.encode())
        decrypted = fernet.decrypt(encrypted_bytes)
        return decrypted.decode()
    except Exception as e:
        logger.error(f"Failed to decrypt token: {e}")
        raise


def generate_api_key(prefix: str = "ff") -> str:
    """Generate a secure API key."""
    return f"{prefix}_{secrets.token_urlsafe(32)}"


def hash_api_key(api_key: str) -> str:
    """Hash an API key for secure storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(api_key: str, stored_hash: str) -> bool:
    """Verify an API key against stored hash."""
    return hash_api_key(api_key) == stored_hash


def generate_secure_id() -> str:
    """Generate a secure UUID-like ID."""
    import uuid
    return str(uuid.uuid4())


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage."""
    import re
    # Remove any non-alphanumeric characters except dots and hyphens
    sanitized = re.sub(r'[^a-zA-Z0-9.-]', '_', filename)
    # Remove multiple consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    return sanitized


def format_currency(amount: float, currency: str = "USD") -> str:
    """Format currency amount for display."""
    if currency == "USD":
        return f"${amount:,.2f}"
    return f"{amount:,.2f} {currency}"


def calculate_percentage(part: float, total: float) -> float:
    """Calculate percentage safely."""
    if total == 0:
        return 0.0
    return round((part / total) * 100, 2)


def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
    """Mask sensitive data showing only last few characters."""
    if len(data) <= visible_chars:
        return "*" * len(data)
    return "*" * (len(data) - visible_chars) + data[-visible_chars:]


def deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries."""
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


def validate_email(email: str) -> bool:
    """Basic email validation."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def normalize_phone_number(phone: str) -> str:
    """Normalize phone number format."""
    import re
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Add country code if missing (assuming US)
    if len(digits) == 10:
        digits = "1" + digits
    
    return digits


def get_client_ip(request) -> str:
    """Get client IP address from request."""
    # Check for X-Forwarded-For header (load balancers, proxies)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    # Check for X-Real-IP header (nginx)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fall back to direct client connection
    return request.client.host if request.client else "unknown"


def parse_user_agent(user_agent: str) -> Dict[str, str]:
    """Parse user agent string for basic info."""
    # Simple user agent parsing - could be enhanced with a library
    info = {
        "browser": "unknown",
        "os": "unknown",
        "device": "desktop"
    }
    
    user_agent_lower = user_agent.lower()
    
    # Browser detection
    if "chrome" in user_agent_lower:
        info["browser"] = "chrome"
    elif "firefox" in user_agent_lower:
        info["browser"] = "firefox"
    elif "safari" in user_agent_lower:
        info["browser"] = "safari"
    elif "edge" in user_agent_lower:
        info["browser"] = "edge"
    
    # OS detection
    if "windows" in user_agent_lower:
        info["os"] = "windows"
    elif "mac" in user_agent_lower or "darwin" in user_agent_lower:
        info["os"] = "macos"
    elif "linux" in user_agent_lower:
        info["os"] = "linux"
    elif "android" in user_agent_lower:
        info["os"] = "android"
        info["device"] = "mobile"
    elif "ios" in user_agent_lower or "iphone" in user_agent_lower:
        info["os"] = "ios"
        info["device"] = "mobile"
    
    return info


class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self):
        self._requests = {}
    
    def is_allowed(
        self, 
        key: str, 
        limit: int, 
        window_seconds: int
    ) -> tuple[bool, Dict[str, Any]]:
        """Check if request is allowed under rate limit."""
        import time
        
        now = time.time()
        window_start = now - window_seconds
        
        # Clean old requests
        if key in self._requests:
            self._requests[key] = [
                req_time for req_time in self._requests[key] 
                if req_time > window_start
            ]
        else:
            self._requests[key] = []
        
        current_requests = len(self._requests[key])
        
        if current_requests >= limit:
            # Rate limit exceeded
            oldest_request = min(self._requests[key])
            reset_time = oldest_request + window_seconds
            
            return False, {
                "limit": limit,
                "remaining": 0,
                "reset": int(reset_time),
                "retry_after": int(reset_time - now)
            }
        
        # Allow request
        self._requests[key].append(now)
        
        return True, {
            "limit": limit,
            "remaining": limit - current_requests - 1,
            "reset": int(now + window_seconds),
            "retry_after": 0
        }
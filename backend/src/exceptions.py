"""Custom exception classes."""
from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class BaseCustomException(Exception):
    """Base class for custom exceptions."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class TenantNotFoundError(BaseCustomException):
    """Raised when tenant is not found."""
    
    def __init__(self, tenant_id: str, message: str = None):
        self.tenant_id = tenant_id
        message = message or f"Tenant {tenant_id} not found"
        super().__init__(message)


class TenantInactiveError(BaseCustomException):
    """Raised when tenant is inactive."""
    pass


class InvalidTenantConfigurationError(BaseCustomException):
    """Raised when tenant configuration is invalid."""
    pass


class DatabaseConnectionError(BaseCustomException):
    """Raised when database connection fails."""
    pass


class DatabaseError(BaseCustomException):
    """Raised when database operation fails."""
    pass


class NotFoundError(BaseCustomException):
    """Raised when resource is not found."""
    pass


class AuthenticationError(BaseCustomException):
    """Raised when authentication fails."""
    pass


class AuthorizationError(BaseCustomException):
    """Raised when authorization fails."""
    pass


class ValidationError(BaseCustomException):
    """Raised when data validation fails."""
    pass


class ExternalServiceError(BaseCustomException):
    """Raised when external service error occurs."""
    
    def __init__(self, service: str, message: str, details: Optional[Dict[str, Any]] = None):
        self.service = service
        super().__init__(message, details)


class PlaidError(ExternalServiceError):
    """Raised when Plaid API error occurs."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__("plaid", message, details)


class StripeError(ExternalServiceError):
    """Raised when Stripe API error occurs."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__("stripe", message, details)


class Auth0Error(ExternalServiceError):
    """Raised when Auth0 API error occurs."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__("auth0", message, details)


class RedisError(ExternalServiceError):
    """Raised when Redis operation fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__("redis", message, details)


class BusinessLogicError(BaseCustomException):
    """Raised when business logic validation fails."""
    pass


class RateLimitExceededError(BaseCustomException):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None):
        self.retry_after = retry_after
        super().__init__(message)


class InsufficientFundsError(BusinessLogicError):
    """Raised when transaction would cause insufficient funds."""
    pass


class InvalidBudgetError(BusinessLogicError):
    """Raised when budget operation is invalid."""
    pass


class FamilyPermissionError(BusinessLogicError):
    """Raised when family permission is denied."""
    pass


# HTTP Exception helpers
def tenant_not_found_exception() -> HTTPException:
    """Create HTTP exception for tenant not found."""
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Tenant not found"
    )


def tenant_inactive_exception() -> HTTPException:
    """Create HTTP exception for inactive tenant."""
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Tenant account suspended"
    )


def unauthorized_exception() -> HTTPException:
    """Create HTTP exception for unauthorized access."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def forbidden_exception(detail: str = "Insufficient permissions") -> HTTPException:
    """Create HTTP exception for forbidden access."""
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=detail
    )


def not_found_exception(detail: str = "Resource not found") -> HTTPException:
    """Create HTTP exception for resource not found."""
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=detail
    )


def conflict_exception(detail: str = "Resource already exists") -> HTTPException:
    """Create HTTP exception for conflict."""
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=detail
    )


def validation_exception(detail: str = "Invalid input data") -> HTTPException:
    """Create HTTP exception for validation error."""
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=detail
    )


def rate_limit_exception(retry_after: int = None) -> HTTPException:
    """Create HTTP exception for rate limit exceeded."""
    headers = {"Retry-After": str(retry_after)} if retry_after else None
    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Rate limit exceeded",
        headers=headers
    )


def internal_server_exception(detail: str = "Internal server error") -> HTTPException:
    """Create HTTP exception for internal server error."""
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=detail
    )


def service_unavailable_exception(service: str = "External service") -> HTTPException:
    """Create HTTP exception for service unavailable."""
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f"{service} is currently unavailable"
    )
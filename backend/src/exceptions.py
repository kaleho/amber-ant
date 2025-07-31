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
    pass


class TenantInactiveError(BaseCustomException):
    """Raised when tenant is inactive."""
    pass


class InvalidTenantConfigurationError(BaseCustomException):
    """Raised when tenant configuration is invalid."""
    pass


class DatabaseConnectionError(BaseCustomException):
    """Raised when database connection fails."""
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


class PlaidError(BaseCustomException):
    """Raised when Plaid API error occurs."""
    pass


class StripeError(BaseCustomException):
    """Raised when Stripe API error occurs."""
    pass


class BusinessLogicError(BaseCustomException):
    """Raised when business logic validation fails."""
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


def internal_server_exception(detail: str = "Internal server error") -> HTTPException:
    """Create HTTP exception for internal server error."""
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=detail
    )
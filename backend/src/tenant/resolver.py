"""Tenant resolution strategies."""
from abc import ABC, abstractmethod
from typing import Optional
from fastapi import Request
import jwt
import logging

logger = logging.getLogger(__name__)


class TenantResolver(ABC):
    """Abstract base class for tenant resolution strategies."""
    
    @abstractmethod
    async def resolve_tenant(self, request: Request) -> Optional[str]:
        """Resolve tenant ID from request."""
        pass


class JWTTenantResolver(TenantResolver):
    """Resolve tenant from JWT token claims."""
    
    async def resolve_tenant(self, request: Request) -> Optional[str]:
        """Extract tenant ID from JWT token."""
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header[7:]  # Remove "Bearer " prefix
        
        try:
            # Decode without verification for tenant extraction
            # Actual verification happens in auth dependencies
            unverified_payload = jwt.decode(token, options={"verify_signature": False})
            
            # Extract tenant from custom claims
            tenant_id = unverified_payload.get("https://faithfulfinances.com/tenant_id")
            if tenant_id:
                logger.debug(f"Resolved tenant from JWT: {tenant_id}")
                return tenant_id
                
        except jwt.InvalidTokenError:
            logger.debug("Invalid JWT token for tenant resolution")
            
        return None


class SubdomainTenantResolver(TenantResolver):
    """Resolve tenant from subdomain."""
    
    async def resolve_tenant(self, request: Request) -> Optional[str]:
        """Extract tenant slug from subdomain."""
        host = request.headers.get("host", "")
        parts = host.split(".")
        
        if len(parts) >= 3:  # subdomain.domain.com
            subdomain = parts[0]
            if subdomain and subdomain not in ["www", "api", "staging", "dev"]:
                logger.debug(f"Resolved tenant from subdomain: {subdomain}")
                return subdomain
        
        return None


class HeaderTenantResolver(TenantResolver):
    """Resolve tenant from X-Tenant-ID header."""
    
    def __init__(self, header_name: str = "X-Tenant-ID"):
        self.header_name = header_name
    
    async def resolve_tenant(self, request: Request) -> Optional[str]:
        """Extract tenant ID from header."""
        tenant_id = request.headers.get(self.header_name)
        if tenant_id:
            logger.debug(f"Resolved tenant from header {self.header_name}: {tenant_id}")
        return tenant_id


class PathTenantResolver(TenantResolver):
    """Resolve tenant from URL path."""
    
    async def resolve_tenant(self, request: Request) -> Optional[str]:
        """Extract tenant ID from URL path like /tenants/{tenant_id}/..."""
        path_parts = request.url.path.strip("/").split("/")
        
        # Look for pattern: /v1/tenants/{tenant_id}/...
        if len(path_parts) >= 3 and path_parts[0] == "v1" and path_parts[1] == "tenants":
            tenant_id = path_parts[2]
            if tenant_id:
                logger.debug(f"Resolved tenant from path: {tenant_id}")
                return tenant_id
        
        return None


class CompositeTenantResolver(TenantResolver):
    """Composite resolver that tries multiple strategies."""
    
    def __init__(self, resolvers: list[TenantResolver]):
        self.resolvers = resolvers
    
    async def resolve_tenant(self, request: Request) -> Optional[str]:
        """Try each resolver until one succeeds."""
        for resolver in self.resolvers:
            tenant_id = await resolver.resolve_tenant(request)
            if tenant_id:
                logger.debug(f"Resolved tenant using {resolver.__class__.__name__}: {tenant_id}")
                return tenant_id
        
        logger.debug("No tenant resolved from any strategy")
        return None


def create_default_tenant_resolver() -> CompositeTenantResolver:
    """Create default composite tenant resolver."""
    from src.config import settings
    
    resolvers = [
        JWTTenantResolver(),
        SubdomainTenantResolver(),
        HeaderTenantResolver(settings.TENANT_HEADER_NAME),
        PathTenantResolver(),
    ]
    
    return CompositeTenantResolver(resolvers)
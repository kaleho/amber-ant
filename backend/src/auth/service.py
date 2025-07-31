"""Auth0 service for JWT token validation and user management."""
import httpx
import jwt
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging
from functools import lru_cache

from src.config import settings
from src.exceptions import AuthenticationError, AuthorizationError

logger = logging.getLogger(__name__)


class Auth0Service:
    """Service for Auth0 JWT token validation and management."""
    
    def __init__(self):
        self.domain = settings.AUTH0_DOMAIN
        self.audience = settings.AUTH0_AUDIENCE
        self.client_id = settings.AUTH0_CLIENT_ID
        self.client_secret = settings.AUTH0_CLIENT_SECRET
        self._jwks_cache = {}
        self._jwks_cache_expiry = None
    
    @property
    def issuer(self) -> str:
        """Get Auth0 issuer URL."""
        return f"https://{self.domain}/"
    
    @property
    def jwks_url(self) -> str:
        """Get Auth0 JWKS URL."""
        return f"https://{self.domain}/.well-known/jwks.json"
    
    async def validate_jwt_token(self, token: str) -> Dict[str, Any]:
        """Validate JWT token and return claims."""
        try:
            # Get JWT header to find the key ID
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")
            
            if not kid:
                raise AuthenticationError("Token missing key ID")
            
            # Get public key for verification
            public_key = await self._get_public_key(kid)
            
            # Decode and verify token
            claims = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                audience=self.audience,
                issuer=self.issuer,
                options={
                    "verify_signature": True,
                    "verify_aud": True,
                    "verify_iss": True,
                    "verify_exp": True,
                    "verify_nbf": True,
                    "verify_iat": True,
                }
            )
            
            logger.debug(f"Successfully validated JWT for user: {claims.get('sub')}")
            return claims
            
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
            raise AuthenticationError("Token has expired")
        except jwt.InvalidAudienceError:
            logger.warning("JWT token has invalid audience")
            raise AuthenticationError("Invalid token audience")
        except jwt.InvalidIssuerError:
            logger.warning("JWT token has invalid issuer")
            raise AuthenticationError("Invalid token issuer")
        except jwt.InvalidSignatureError:
            logger.warning("JWT token has invalid signature")
            raise AuthenticationError("Invalid token signature")
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            raise AuthenticationError(f"Invalid token: {e}")
        except Exception as e:
            logger.error(f"JWT validation error: {e}")
            raise AuthenticationError("Token validation failed")
    
    async def _get_public_key(self, kid: str) -> str:
        """Get public key from Auth0 JWKS endpoint."""
        # Check cache first
        if self._is_jwks_cache_valid():
            if kid in self._jwks_cache:
                return self._jwks_cache[kid]
        
        # Fetch JWKS from Auth0
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.jwks_url, timeout=10.0)
                response.raise_for_status()
                jwks = response.json()
            
            # Process keys and cache them
            self._jwks_cache = {}
            for key in jwks.get("keys", []):
                key_kid = key.get("kid")
                if key_kid and key.get("kty") == "RSA":
                    # Convert JWK to PEM format
                    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
                    pem_key = public_key.public_key().public_bytes(
                        encoding=jwt.algorithms.Encoding.PEM,
                        format=jwt.algorithms.PublicFormat.SubjectPublicKeyInfo
                    ).decode()
                    self._jwks_cache[key_kid] = pem_key
            
            # Set cache expiry (1 hour)
            self._jwks_cache_expiry = datetime.utcnow() + timedelta(hours=1)
            
            if kid not in self._jwks_cache:
                raise AuthenticationError(f"Public key not found for kid: {kid}")
            
            return self._jwks_cache[kid]
            
        except httpx.RequestError as e:
            logger.error(f"Failed to fetch JWKS: {e}")
            raise AuthenticationError("Failed to validate token signature")
        except Exception as e:
            logger.error(f"JWKS processing error: {e}")
            raise AuthenticationError("Failed to process token signature")
    
    def _is_jwks_cache_valid(self) -> bool:
        """Check if JWKS cache is still valid."""
        return (
            self._jwks_cache_expiry is not None and
            datetime.utcnow() < self._jwks_cache_expiry
        )
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from Auth0 userinfo endpoint."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://{self.domain}/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.RequestError as e:
            logger.error(f"Failed to get user info: {e}")
            raise AuthenticationError("Failed to retrieve user information")
    
    async def get_management_token(self) -> str:
        """Get Auth0 Management API token."""
        if not self.client_id or not self.client_secret:
            raise AuthorizationError("Auth0 client credentials not configured")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://{self.domain}/oauth/token",
                    json={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "audience": f"https://{self.domain}/api/v2/",
                        "grant_type": "client_credentials"
                    },
                    timeout=10.0
                )
                response.raise_for_status()
                token_data = response.json()
                return token_data["access_token"]
                
        except httpx.RequestError as e:
            logger.error(f"Failed to get management token: {e}")
            raise AuthorizationError("Failed to get management API access")
    
    async def update_user_metadata(
        self, 
        user_id: str, 
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update user metadata in Auth0."""
        management_token = await self.get_management_token()
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"https://{self.domain}/api/v2/users/{user_id}",
                    headers={"Authorization": f"Bearer {management_token}"},
                    json={"app_metadata": metadata},
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.RequestError as e:
            logger.error(f"Failed to update user metadata: {e}")
            raise AuthorizationError("Failed to update user information")
    
    async def assign_user_roles(self, user_id: str, role_ids: List[str]):
        """Assign roles to user in Auth0."""
        management_token = await self.get_management_token()
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://{self.domain}/api/v2/users/{user_id}/roles",
                    headers={"Authorization": f"Bearer {management_token}"},
                    json={"roles": role_ids},
                    timeout=10.0
                )
                response.raise_for_status()
                
        except httpx.RequestError as e:
            logger.error(f"Failed to assign user roles: {e}")
            raise AuthorizationError("Failed to assign user roles")
    
    async def remove_user_roles(self, user_id: str, role_ids: List[str]):
        """Remove roles from user in Auth0."""
        management_token = await self.get_management_token()
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"https://{self.domain}/api/v2/users/{user_id}/roles",
                    headers={"Authorization": f"Bearer {management_token}"},
                    json={"roles": role_ids},
                    timeout=10.0
                )
                response.raise_for_status()
                
        except httpx.RequestError as e:
            logger.error(f"Failed to remove user roles: {e}")
            raise AuthorizationError("Failed to remove user roles")
    
    def extract_tenant_from_token(self, claims: Dict[str, Any]) -> Optional[str]:
        """Extract tenant ID from JWT claims."""
        # Try different possible claim locations
        tenant_claims = [
            "https://faithfulfinances.com/tenant_id",
            "tenant_id",
            "tid",
            "org_id"
        ]
        
        for claim in tenant_claims:
            tenant_id = claims.get(claim)
            if tenant_id:
                return str(tenant_id)
        
        return None
    
    def extract_permissions(self, claims: Dict[str, Any]) -> List[str]:
        """Extract permissions from JWT claims."""
        # Auth0 typically stores permissions in the "permissions" claim
        permissions = claims.get("permissions", [])
        if isinstance(permissions, list):
            return permissions
        elif isinstance(permissions, str):
            return [permissions]
        return []
    
    def has_permission(self, claims: Dict[str, Any], required_permission: str) -> bool:
        """Check if user has required permission."""
        permissions = self.extract_permissions(claims)
        return required_permission in permissions
    
    def has_any_permission(self, claims: Dict[str, Any], required_permissions: List[str]) -> bool:
        """Check if user has any of the required permissions."""
        permissions = self.extract_permissions(claims)
        return any(perm in permissions for perm in required_permissions)
    
    def has_all_permissions(self, claims: Dict[str, Any], required_permissions: List[str]) -> bool:
        """Check if user has all required permissions."""
        permissions = self.extract_permissions(claims)
        return all(perm in permissions for perm in required_permissions)
    
    def is_global_admin(self, claims: Dict[str, Any]) -> bool:
        """Check if user is a global system administrator."""
        global_admin_claims = [
            "https://faithfulfinances.com/global_admin",
            "global_admin",
            "is_admin"
        ]
        
        for claim in global_admin_claims:
            if claims.get(claim) is True:
                return True
        
        # Check permissions
        return self.has_permission(claims, "global:admin")


# Global Auth0 service instance
auth0_service = Auth0Service()
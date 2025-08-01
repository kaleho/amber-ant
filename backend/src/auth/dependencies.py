"""Authentication and authorization dependencies."""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from src.database import get_global_database_session, get_tenant_database_session
from src.tenant.context import get_tenant_context, require_tenant_context
from src.tenant.service import TenantService
from src.tenant.models import TenantUser
from src.users.models import User
from src.users.service import UserService
from src.auth.service import auth0_service
from src.exceptions import (
    unauthorized_exception,
    forbidden_exception,
    AuthenticationError,
    AuthorizationError
)

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)


async def get_current_user_claims(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """Extract and validate user claims from JWT token."""
    if not credentials:
        raise unauthorized_exception()
    
    try:
        claims = await auth0_service.validate_jwt_token(credentials.credentials)
        
        # Check if token is blacklisted
        token_jti = claims.get('jti')
        if token_jti:
            try:
                from src.security.token_blacklist import token_blacklist
                is_revoked = await token_blacklist.is_token_revoked(token_jti)
                if is_revoked:
                    logger.warning("Revoked token attempted for use", jti=token_jti)
                    raise AuthenticationError("Token has been revoked")
                
                # Check user-level token revocation
                user_id = claims.get('sub')
                token_iat = claims.get('iat', 0)
                if user_id and token_iat:
                    is_user_revoked = await token_blacklist.is_user_token_revoked(user_id, token_iat)
                    if is_user_revoked:
                        logger.warning("User tokens revoked, rejecting token", user_id=user_id, iat=token_iat)
                        raise AuthenticationError("User tokens have been revoked")
                        
            except ImportError:
                pass  # Token blacklist not available
        
        # Log successful authentication
        try:
            from src.security.monitoring import log_auth_success
            from src.shared.utils import get_client_ip
            # Note: request context not directly available here, will be logged at higher level
        except ImportError:
            pass  # Security monitoring not available
            
        return claims
    except AuthenticationError as e:
        logger.warning(f"Authentication failed: {e}")
        
        # Log authentication failure
        try:
            from src.security.monitoring import log_auth_failure
            # Note: request context not directly available here, will be logged at higher level
        except ImportError:
            pass  # Security monitoring not available
            
        raise unauthorized_exception()
    except Exception as e:
        logger.error(f"Unexpected authentication error: {e}")
        raise unauthorized_exception()


async def get_current_user(
    claims: Dict[str, Any] = Depends(get_current_user_claims),
    tenant_db: AsyncSession = Depends(get_tenant_database_session),
    global_db: AsyncSession = Depends(get_global_database_session)
) -> User:
    """Extract and validate user from JWT token with tenant context."""
    
    try:
        # Get tenant context
        tenant_context = require_tenant_context()
        
        # Verify user belongs to this tenant
        tenant_service = TenantService(global_db)
        user_tenants = await tenant_service.get_user_tenants(claims["sub"])
        
        if not any(t.id == tenant_context.tenant_id for t in user_tenants):
            logger.warning(f"User {claims['sub']} not authorized for tenant {tenant_context.tenant_id}")
            raise forbidden_exception("User not authorized for this tenant")
        
        # Get or create user in tenant database
        user_service = UserService(tenant_db)
        user = await user_service.get_or_create_user_from_auth0(claims)
        
        if not user or not user.is_active:
            logger.warning(f"User account inactive: {claims['sub']}")
            raise forbidden_exception("User account inactive")
        
        # Update last accessed time
        await tenant_service.update_tenant_user(
            tenant_context.tenant_id,
            claims["sub"],
            {"last_accessed_at": datetime.utcnow()}
        )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User authentication error: {e}")
        raise unauthorized_exception()


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    tenant_db: AsyncSession = Depends(get_tenant_database_session),
    global_db: AsyncSession = Depends(get_global_database_session)
) -> Optional[User]:
    """Get current user if authenticated, otherwise return None."""
    if not credentials:
        return None
    
    try:
        claims = await auth0_service.validate_jwt_token(credentials.credentials)
        tenant_context = get_tenant_context()
        
        if not tenant_context:
            return None
        
        # Verify user belongs to this tenant
        tenant_service = TenantService(global_db)
        user_tenants = await tenant_service.get_user_tenants(claims["sub"])
        
        if not any(t.id == tenant_context.tenant_id for t in user_tenants):
            return None
        
        # Get user from tenant database
        user_service = UserService(tenant_db)
        user = await user_service.get_user_by_auth0_id(claims["sub"])
        
        return user if user and user.is_active else None
        
    except Exception as e:
        logger.debug(f"Optional authentication failed: {e}")
        return None


def require_permissions(required_permissions: List[str]):
    """Dependency factory for permission-based authorization."""
    
    async def permission_checker(
        claims: Dict[str, Any] = Depends(get_current_user_claims)
    ) -> Dict[str, Any]:
        """Check if user has required permissions."""
        if not auth0_service.has_all_permissions(claims, required_permissions):
            missing_perms = [
                perm for perm in required_permissions 
                if not auth0_service.has_permission(claims, perm)
            ]
            logger.warning(f"User {claims['sub']} missing permissions: {missing_perms}")
            
            # Log permission denied event
            try:
                from src.security.monitoring import log_permission_denied
                from src.tenant.context import get_tenant_context
                
                tenant_context = get_tenant_context()
                tenant_id = tenant_context.tenant_id if tenant_context else None
                
                # Note: Will be enhanced with request context at middleware level
                import asyncio
                asyncio.create_task(log_permission_denied(
                    user_id=claims['sub'],
                    tenant_id=tenant_id,
                    permission=', '.join(missing_perms)
                ))
            except ImportError:
                pass  # Security monitoring not available
            
            raise forbidden_exception(f"Missing required permissions: {', '.join(missing_perms)}")
        
        return claims
    
    return permission_checker


def require_any_permission(required_permissions: List[str]):
    """Dependency factory for any-permission authorization."""
    
    async def permission_checker(
        claims: Dict[str, Any] = Depends(get_current_user_claims)
    ) -> Dict[str, Any]:
        """Check if user has any of the required permissions."""
        if not auth0_service.has_any_permission(claims, required_permissions):
            logger.warning(f"User {claims['sub']} has none of required permissions: {required_permissions}")
            raise forbidden_exception(f"Requires one of: {', '.join(required_permissions)}")
        
        return claims
    
    return permission_checker


async def require_tenant_admin(
    current_user: User = Depends(get_current_user),
    global_db: AsyncSession = Depends(get_global_database_session)
) -> User:
    """Require user to be admin of current tenant."""
    from sqlalchemy import select, and_
    from datetime import datetime
    
    tenant_context = require_tenant_context()
    
    # Check tenant-level admin permission
    stmt = select(TenantUser).where(
        and_(
            TenantUser.auth0_id == current_user.auth0_id,
            TenantUser.tenant_id == tenant_context.tenant_id
        )
    )
    result = await global_db.execute(stmt)
    tenant_user = result.scalar_one_or_none()
    
    if not tenant_user or tenant_user.role not in ["admin", "owner", "administrator"]:
        logger.warning(f"User {current_user.auth0_id} not tenant admin for {tenant_context.tenant_id}")
        raise forbidden_exception("Tenant admin access required")
    
    return current_user


async def require_family_admin(
    current_user: User = Depends(get_current_user),
    tenant_db: AsyncSession = Depends(get_tenant_database_session)
) -> User:
    """Require user to be family administrator."""
    from src.families.service import FamilyService
    
    if not current_user.family_id:
        raise forbidden_exception("User is not part of a family")
    
    family_service = FamilyService(tenant_db)
    family = await family_service.get_family_by_id(current_user.family_id)
    
    if not family or family.administrator_id != current_user.id:
        raise forbidden_exception("Family administrator access required")
    
    return current_user


async def require_global_admin(
    claims: Dict[str, Any] = Depends(get_current_user_claims)
) -> Dict[str, Any]:
    """Require global system admin access."""
    if not auth0_service.is_global_admin(claims):
        logger.warning(f"User {claims['sub']} attempted global admin access")
        raise forbidden_exception("Global admin access required")
    
    return claims


def require_subscription_plan(required_plans: List[str]):
    """Dependency factory for subscription plan requirements."""
    
    async def plan_checker(
        current_user: User = Depends(get_current_user)
    ) -> User:
        """Check if user has required subscription plan."""
        tenant_context = require_tenant_context()
        
        if tenant_context.plan not in required_plans:
            logger.warning(f"User {current_user.auth0_id} plan {tenant_context.plan} not in {required_plans}")
            raise forbidden_exception(f"Requires subscription plan: {' or '.join(required_plans)}")
        
        return current_user
    
    return plan_checker


def require_feature(feature_name: str):
    """Dependency factory for feature access requirements."""
    
    async def feature_checker(
        current_user: User = Depends(get_current_user)
    ) -> User:
        """Check if tenant has required feature."""
        tenant_context = require_tenant_context()
        
        if not tenant_context.has_feature(feature_name):
            logger.warning(f"Tenant {tenant_context.tenant_id} missing feature: {feature_name}")
            raise forbidden_exception(f"Feature not available: {feature_name}")
        
        return current_user
    
    return feature_checker


class RoleChecker:
    """Helper class for role-based authorization."""
    
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles
    
    async def __call__(
        self,
        current_user: User = Depends(get_current_user),
        global_db: AsyncSession = Depends(get_global_database_session)
    ) -> User:
        """Check if user has allowed role in current tenant."""
        tenant_context = require_tenant_context()
        
        # Get tenant user role
        stmt = select(TenantUser).where(
            and_(
                TenantUser.auth0_id == current_user.auth0_id,
                TenantUser.tenant_id == tenant_context.tenant_id
            )
        )
        result = await global_db.execute(stmt)
        tenant_user = result.scalar_one_or_none()
        
        if not tenant_user or tenant_user.role not in self.allowed_roles:
            logger.warning(f"User {current_user.auth0_id} role not in {self.allowed_roles}")
            raise forbidden_exception(f"Requires role: {' or '.join(self.allowed_roles)}")
        
        return current_user


# Common role checkers
require_admin_role = RoleChecker(["admin", "owner", "administrator"])
require_manager_role = RoleChecker(["admin", "owner", "administrator", "manager"])
require_user_role = RoleChecker(["admin", "owner", "administrator", "manager", "user"])


async def get_api_key_tenant(
    request: Request,
    global_db: AsyncSession = Depends(get_global_database_session)
) -> Optional[str]:
    """Extract tenant from API key header."""
    from src.tenant.models import TenantApiKey
    from src.shared.utils import hash_api_key
    
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return None
    
    try:
        # Hash the API key to find in database
        key_hash = hash_api_key(api_key)
        
        # Find API key record
        stmt = select(TenantApiKey).where(
            and_(
                TenantApiKey.key_hash == key_hash,
                TenantApiKey.is_active == True
            )
        )
        result = await global_db.execute(stmt)
        api_key_record = result.scalar_one_or_none()
        
        if not api_key_record:
            return None
        
        # Check expiry
        if api_key_record.expires_at and api_key_record.expires_at < datetime.utcnow():
            return None
        
        # Update last used time
        api_key_record.last_used_at = datetime.utcnow()
        await global_db.commit()
        
        return api_key_record.tenant_id
        
    except Exception as e:
        logger.error(f"API key validation error: {e}")
        return None
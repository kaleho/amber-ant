"""Authentication API routes."""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
import logging

from src.database import get_global_database_session, get_tenant_database_session
from src.auth.dependencies import (
    get_current_user_claims, 
    get_current_user,
    require_global_admin
)
from src.auth.schemas import (
    UserClaims,
    AuthContextResponse,
    UserPermissions,
    ApiKeyCreateRequest,
    ApiKeyWithSecret,
    SessionInfo,
    SecurityEvent
)
from src.auth.service import auth0_service
from src.tenant.context import get_tenant_context
from src.tenant.service import TenantService
from src.tenant.models import TenantUser
from src.users.models import User
from src.shared.utils import get_client_ip, parse_user_agent
from src.exceptions import not_found_exception, forbidden_exception
from sqlalchemy import select, and_

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/me", response_model=AuthContextResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    claims: Dict[str, Any] = Depends(get_current_user_claims),
    global_db: AsyncSession = Depends(get_global_database_session)
):
    """Get current authenticated user's profile and context."""
    tenant_context = get_tenant_context()
    
    # Get tenant user permissions
    tenant_user = None
    if tenant_context:
        stmt = select(TenantUser).where(
            and_(
                TenantUser.auth0_id == current_user.auth0_id,
                TenantUser.tenant_id == tenant_context.tenant_id
            )
        )
        result = await global_db.execute(stmt)
        tenant_user = result.scalar_one_or_none()
    
    # Build permissions
    permissions = UserPermissions(
        permissions=auth0_service.extract_permissions(claims),
        roles=claims.get("roles", []),
        tenant_role=tenant_user.role if tenant_user else None,
        is_global_admin=auth0_service.is_global_admin(claims),
        is_tenant_admin=tenant_user and tenant_user.role in ["admin", "owner", "administrator"] if tenant_user else False,
        is_family_admin=current_user.family_role == "administrator" if current_user.family_id else False
    )
    
    return AuthContextResponse(
        user_id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        tenant_id=tenant_context.tenant_id if tenant_context else None,
        tenant_slug=tenant_context.tenant_slug if tenant_context else None,
        permissions=permissions,
        subscription_plan=tenant_context.plan if tenant_context else None,
        features=tenant_context.features if tenant_context else []
    )


@router.post("/api-keys", response_model=ApiKeyWithSecret)
async def create_api_key(
    request_data: ApiKeyCreateRequest,
    current_user: User = Depends(get_current_user),
    global_db: AsyncSession = Depends(get_global_database_session)
):
    """Create a new API key for the current tenant."""
    tenant_context = get_tenant_context()
    if not tenant_context:
        raise forbidden_exception("API keys require tenant context")
    
    tenant_service = TenantService(global_db)
    
    # Calculate expiry
    expires_at = None
    if request_data.expires_days:
        from datetime import datetime, timedelta
        expires_at = datetime.utcnow() + timedelta(days=request_data.expires_days)
    
    # Create API key
    api_key_record, api_key = await tenant_service.create_api_key(
        tenant_context.tenant_id,
        request_data,
        current_user.auth0_id
    )
    
    return ApiKeyWithSecret(
        id=api_key_record.id,
        name=api_key_record.name,
        permissions=list(api_key_record.permissions.keys()) if api_key_record.permissions else [],
        is_active=api_key_record.is_active,
        expires_at=api_key_record.expires_at,
        last_used_at=api_key_record.last_used_at,
        created_at=api_key_record.created_at,
        created_by=api_key_record.created_by,
        api_key=api_key
    )


@router.get("/sessions")
async def get_user_sessions(
    current_user: User = Depends(get_current_user)
):
    """Get current user's active sessions."""
    # This would typically integrate with a session store
    # For now, return current session info
    return [
        SessionInfo(
            session_id="current",
            user_id=current_user.id,
            tenant_id=current_user.tenant_id if hasattr(current_user, 'tenant_id') else None,
            ip_address="unknown",
            user_agent="unknown",
            created_at=current_user.created_at,
            last_active=current_user.updated_at,
            expires_at=current_user.updated_at,
            is_active=True
        )
    ]


@router.post("/sessions/{session_id}/revoke")
async def revoke_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Revoke a specific session."""
    # This would integrate with session management
    if session_id == "current":
        raise forbidden_exception("Cannot revoke current session")
    
    # Implementation would revoke the session
    return {"message": "Session revoked successfully"}


@router.get("/security-events")
async def get_security_events(
    current_user: User = Depends(get_current_user),
    limit: int = 50
):
    """Get user's recent security events."""
    # This would typically come from a security audit log
    return []


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Logout current user."""
    # Log security event
    security_event = SecurityEvent(
        event_type="logout",
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent", ""),
        success=True
    )
    
    # In a real implementation, you would:
    # 1. Invalidate the current session
    # 2. Add the token to a blacklist
    # 3. Log the security event
    # 4. Optionally redirect to Auth0 logout
    
    return {"message": "Logged out successfully"}


@router.get("/permissions")
async def get_user_permissions(
    claims: Dict[str, Any] = Depends(get_current_user_claims),
    current_user: User = Depends(get_current_user),
    global_db: AsyncSession = Depends(get_global_database_session)
):
    """Get detailed user permissions and roles."""
    tenant_context = get_tenant_context()
    
    # Get tenant-specific permissions
    tenant_permissions = {}
    if tenant_context:
        stmt = select(TenantUser).where(
            and_(
                TenantUser.auth0_id == current_user.auth0_id,
                TenantUser.tenant_id == tenant_context.tenant_id
            )
        )
        result = await global_db.execute(stmt)
        tenant_user = result.scalar_one_or_none()
        
        if tenant_user:
            tenant_permissions = tenant_user.permissions
    
    return {
        "auth0_permissions": auth0_service.extract_permissions(claims),
        "auth0_roles": claims.get("roles", []),
        "tenant_role": tenant_user.role if 'tenant_user' in locals() and tenant_user else None,
        "tenant_permissions": tenant_permissions,
        "family_role": current_user.family_role,
        "is_global_admin": auth0_service.is_global_admin(claims),
        "subscription_plan": tenant_context.plan if tenant_context else None,
        "available_features": tenant_context.features if tenant_context else []
    }


@router.get("/health")
async def auth_health_check():
    """Check authentication service health."""
    try:
        # Test Auth0 connection by fetching JWKS
        async with httpx.AsyncClient() as client:
            response = await client.get(auth0_service.jwks_url, timeout=5.0)
            response.raise_for_status()
        
        return {
            "status": "healthy",
            "auth0_connection": "ok",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Auth health check failed: {e}")
        return {
            "status": "unhealthy",
            "auth0_connection": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


# Global admin endpoints
@router.get("/admin/users")
async def list_all_users(
    claims: Dict[str, Any] = Depends(require_global_admin),
    global_db: AsyncSession = Depends(get_global_database_session),
    skip: int = 0,
    limit: int = 100
):
    """List all users across all tenants (global admin only)."""
    # This would typically integrate with Auth0 Management API
    # and provide comprehensive user listing
    return {
        "users": [],
        "total": 0,
        "skip": skip,
        "limit": limit
    }


@router.get("/admin/security-events")  
async def get_global_security_events(
    claims: Dict[str, Any] = Depends(require_global_admin),
    limit: int = 100
):
    """Get global security events (global admin only)."""
    # This would return system-wide security events
    return []
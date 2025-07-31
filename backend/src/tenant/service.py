"""Tenant service layer for business logic."""
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
import uuid
import logging
import hashlib
import secrets
from datetime import datetime, timedelta

from src.tenant.models import TenantRegistry, TenantUser, TenantApiKey, TenantSettings
from src.tenant.schemas import (
    CreateTenantRequest, 
    UpdateTenantRequest,
    CreateTenantUserRequest,
    UpdateTenantUserRequest,
    CreateTenantApiKeyRequest,
    TenantStatsResponse,
    TenantHealthResponse
)
from src.tenant.context import TenantContext
from src.tenant.manager import tenant_db_manager
from src.shared.utils import encrypt_token, decrypt_token
from src.exceptions import (
    TenantNotFoundError, 
    TenantInactiveError,
    ValidationError,
    BusinessLogicError
)
from src.config import settings

logger = logging.getLogger(__name__)


class TenantService:
    """Service for tenant management operations."""
    
    def __init__(self, global_db: AsyncSession):
        self.global_db = global_db
    
    async def get_tenant_context(self, tenant_identifier: str) -> Optional[TenantContext]:
        """Get tenant context by ID or slug."""
        stmt = select(TenantRegistry).where(
            (TenantRegistry.id == tenant_identifier) | 
            (TenantRegistry.slug == tenant_identifier)
        )
        result = await self.global_db.execute(stmt)
        tenant = result.scalar_one_or_none()
        
        if not tenant:
            return None
        
        # Decrypt auth token
        try:
            decrypted_token = decrypt_token(tenant.auth_token)
        except Exception as e:
            logger.error(f"Failed to decrypt tenant auth token: {e}")
            return None
        
        return TenantContext(
            tenant_id=tenant.id,
            tenant_slug=tenant.slug,
            database_url=tenant.database_url,
            auth_token=decrypted_token,
            plan=tenant.plan,
            is_active=tenant.is_active,
            features=list(tenant.features.keys()) if tenant.features else [],
            metadata=tenant.metadata
        )
    
    async def create_tenant(self, tenant_data: CreateTenantRequest) -> TenantContext:
        """Create new tenant with database provisioning."""
        # Validate slug availability
        await self._validate_slug_availability(tenant_data.slug)
        
        tenant_id = str(uuid.uuid4())
        
        # Prepare tenant data for database creation
        full_tenant_data = {
            "tenant_id": tenant_id,
            "slug": tenant_data.slug,
            "name": tenant_data.name,
            "plan": tenant_data.plan,
            "features": {feature: True for feature in tenant_data.features or []},
            "metadata": tenant_data.metadata or {}
        }
        
        # Create tenant database
        tenant_context = await tenant_db_manager.create_tenant_database(full_tenant_data)
        
        # Register in global database
        tenant_registry = TenantRegistry(
            id=tenant_id,
            slug=tenant_data.slug,
            name=tenant_data.name,
            database_url=tenant_context.database_url,
            auth_token=encrypt_token(tenant_context.auth_token),
            plan=tenant_data.plan,
            features=full_tenant_data["features"],
            metadata=full_tenant_data["metadata"]
        )
        
        self.global_db.add(tenant_registry)
        await self.global_db.commit()
        
        logger.info(f"Created tenant: {tenant_id} ({tenant_data.slug})")
        return tenant_context
    
    async def update_tenant(
        self, 
        tenant_id: str, 
        update_data: UpdateTenantRequest
    ) -> Optional[TenantRegistry]:
        """Update tenant information."""
        stmt = select(TenantRegistry).where(TenantRegistry.id == tenant_id)
        result = await self.global_db.execute(stmt)
        tenant = result.scalar_one_or_none()
        
        if not tenant:
            return None
        
        # Update fields
        if update_data.name is not None:
            tenant.name = update_data.name
        if update_data.plan is not None:
            tenant.plan = update_data.plan
        if update_data.is_active is not None:
            tenant.is_active = update_data.is_active
        if update_data.features is not None:
            tenant.features = {feature: True for feature in update_data.features}
        if update_data.metadata is not None:
            tenant.metadata = update_data.metadata
        
        tenant.updated_at = datetime.utcnow()
        await self.global_db.commit()
        
        logger.info(f"Updated tenant: {tenant_id}")
        return tenant
    
    async def add_user_to_tenant(
        self, 
        tenant_id: str,
        user_data: CreateTenantUserRequest
    ) -> TenantUser:
        """Add user to tenant in global registry."""
        # Check if mapping already exists
        stmt = select(TenantUser).where(
            and_(
                TenantUser.auth0_id == user_data.auth0_id,
                TenantUser.tenant_id == tenant_id
            )
        )
        result = await self.global_db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update role if different
            if existing.role != user_data.role:
                existing.role = user_data.role
                existing.permissions = user_data.permissions
                await self.global_db.commit()
            return existing
        
        # Check tenant user limit
        await self._validate_tenant_user_limit(tenant_id)
        
        # Create new mapping
        tenant_user = TenantUser(
            id=str(uuid.uuid4()),
            auth0_id=user_data.auth0_id,
            tenant_id=tenant_id,
            role=user_data.role,
            permissions=user_data.permissions
        )
        
        self.global_db.add(tenant_user)
        await self.global_db.commit()
        
        logger.info(f"Added user {user_data.auth0_id} to tenant {tenant_id}")
        return tenant_user
    
    async def update_tenant_user(
        self,
        tenant_id: str,
        auth0_id: str,
        update_data: UpdateTenantUserRequest
    ) -> Optional[TenantUser]:
        """Update tenant user information."""
        stmt = select(TenantUser).where(
            and_(
                TenantUser.auth0_id == auth0_id,
                TenantUser.tenant_id == tenant_id
            )
        )
        result = await self.global_db.execute(stmt)
        tenant_user = result.scalar_one_or_none()
        
        if not tenant_user:
            return None
        
        # Update fields
        if update_data.role is not None:
            tenant_user.role = update_data.role
        if update_data.is_active is not None:
            tenant_user.is_active = update_data.is_active
        if update_data.permissions is not None:
            tenant_user.permissions = update_data.permissions
        
        await self.global_db.commit()
        return tenant_user
    
    async def get_user_tenants(self, auth0_id: str) -> List[TenantRegistry]:
        """Get all tenants a user belongs to."""
        stmt = (
            select(TenantRegistry)
            .join(TenantUser, TenantRegistry.id == TenantUser.tenant_id)
            .where(TenantUser.auth0_id == auth0_id)
            .where(TenantUser.is_active == True)
            .where(TenantRegistry.is_active == True)
        )
        
        result = await self.global_db.execute(stmt)
        return list(result.scalars().all())
    
    async def create_api_key(
        self,
        tenant_id: str,
        key_data: CreateTenantApiKeyRequest,
        created_by: str
    ) -> tuple[TenantApiKey, str]:
        """Create new API key for tenant."""
        # Generate API key
        api_key = f"ff_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        tenant_api_key = TenantApiKey(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            key_hash=key_hash,
            name=key_data.name,
            permissions=key_data.permissions,
            expires_at=key_data.expires_at,
            created_by=created_by
        )
        
        self.global_db.add(tenant_api_key)
        await self.global_db.commit()
        
        logger.info(f"Created API key for tenant {tenant_id}")
        return tenant_api_key, api_key
    
    async def get_tenant_stats(self, tenant_id: str) -> TenantStatsResponse:
        """Get tenant statistics."""
        # Get basic tenant info
        stmt = select(TenantRegistry).where(TenantRegistry.id == tenant_id)
        result = await self.global_db.execute(stmt)
        tenant = result.scalar_one_or_none()
        
        if not tenant:
            raise TenantNotFoundError(f"Tenant {tenant_id} not found")
        
        # Get user counts
        user_count_stmt = select(func.count(TenantUser.id)).where(
            TenantUser.tenant_id == tenant_id
        )
        active_user_count_stmt = select(func.count(TenantUser.id)).where(
            and_(
                TenantUser.tenant_id == tenant_id,
                TenantUser.is_active == True
            )
        )
        
        total_users = await self.global_db.scalar(user_count_stmt) or 0
        active_users = await self.global_db.scalar(active_user_count_stmt) or 0
        
        # Get last activity
        last_activity_stmt = select(func.max(TenantUser.last_accessed_at)).where(
            TenantUser.tenant_id == tenant_id
        )
        last_activity = await self.global_db.scalar(last_activity_stmt)
        
        return TenantStatsResponse(
            tenant_id=tenant_id,
            total_users=total_users,
            active_users=active_users,
            total_accounts=0,  # These would be fetched from tenant database
            total_transactions=0,
            total_budgets=0,
            total_goals=0,
            plan=tenant.plan,
            created_at=tenant.created_at,
            last_activity=last_activity
        )
    
    async def get_tenant_health(self, tenant_id: str) -> TenantHealthResponse:
        """Check tenant health."""
        tenant_context = await self.get_tenant_context(tenant_id)
        if not tenant_context:
            return TenantHealthResponse(
                tenant_id=tenant_id,
                database_healthy=False,
                connection_count=0,
                last_migration=None,
                status="unhealthy"
            )
        
        # Check database health
        db_healthy = await tenant_db_manager.health_check(tenant_context)
        
        # Determine status
        if db_healthy and tenant_context.is_active:
            status = "healthy"
        elif db_healthy and not tenant_context.is_active:
            status = "degraded"
        else:
            status = "unhealthy"
        
        return TenantHealthResponse(
            tenant_id=tenant_id,
            database_healthy=db_healthy,
            connection_count=1 if db_healthy else 0,
            last_migration=None,  # Could be implemented with migration tracking
            status=status
        )
    
    async def deactivate_tenant(self, tenant_id: str) -> bool:
        """Deactivate tenant (soft delete)."""
        stmt = select(TenantRegistry).where(TenantRegistry.id == tenant_id)
        result = await self.global_db.execute(stmt)
        tenant = result.scalar_one_or_none()
        
        if tenant:
            tenant.is_active = False
            tenant.updated_at = datetime.utcnow()
            await self.global_db.commit()
            
            # Close database connections
            await tenant_db_manager.close_tenant_connections(tenant_id)
            
            logger.info(f"Deactivated tenant: {tenant_id}")
            return True
        
        return False
    
    async def _validate_slug_availability(self, slug: str):
        """Validate that tenant slug is available."""
        stmt = select(TenantRegistry).where(TenantRegistry.slug == slug)
        result = await self.global_db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            raise ValidationError(f"Tenant slug '{slug}' is already taken")
    
    async def _validate_tenant_user_limit(self, tenant_id: str):
        """Validate tenant user limit."""
        stmt = select(func.count(TenantUser.id)).where(
            and_(
                TenantUser.tenant_id == tenant_id,
                TenantUser.is_active == True
            )
        )
        user_count = await self.global_db.scalar(stmt) or 0
        
        if user_count >= settings.MAX_TENANTS_PER_USER:
            raise BusinessLogicError(f"Tenant user limit reached ({settings.MAX_TENANTS_PER_USER})")
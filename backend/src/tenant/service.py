"""Tenant management service."""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import uuid4
import secrets

from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.database import get_global_database_session
from src.tenant.models import TenantRegistry, TenantUser, TenantInvitation
from src.tenant.schemas import (
    TenantCreate, TenantUpdate, Tenant, TenantInDB,
    TenantUserCreate, TenantUser as TenantUserSchema,
    TenantInvitationCreate, TenantInvitation as TenantInvitationSchema,
    TenantStats, TenantLimits
)
from src.exceptions import (
    TenantNotFoundError, ValidationError, DatabaseError,
    BusinessLogicError, NotFoundError
)

logger = logging.getLogger(__name__)


class TenantService:
    """Service for managing tenants."""
    
    async def create_tenant(
        self, 
        tenant_data: TenantCreate, 
        owner_id: str,
        database_url: str,
        database_auth_token: str
    ) -> Tenant:
        """Create a new tenant."""
        async with get_global_database_session() as session:
            try:
                # Check if slug is already taken
                existing = await self._get_tenant_by_slug_db(session, tenant_data.slug)
                if existing:
                    raise ValidationError(f"Tenant slug '{tenant_data.slug}' is already taken")
                
                # Check tenant limits for owner
                owner_tenant_count = await self._count_tenants_for_owner(session, owner_id)
                from src.config import settings
                if owner_tenant_count >= settings.MAX_TENANTS_PER_USER:
                    raise BusinessLogicError(f"Maximum {settings.MAX_TENANTS_PER_USER} tenants per user")
                
                # Create tenant registry entry
                tenant_id = str(uuid4())
                tenant = TenantRegistry(
                    id=tenant_id,
                    slug=tenant_data.slug,
                    name=tenant_data.name,
                    description=tenant_data.description,
                    database_url=database_url,
                    database_auth_token=database_auth_token,
                    owner_id=owner_id
                )
                
                session.add(tenant)
                await session.flush()  # Flush to get the ID
                
                # Create owner tenant user association
                tenant_user = TenantUser(
                    tenant_id=tenant_id,
                    user_id=owner_id,
                    role="owner",
                    invitation_status="accepted"
                )
                
                session.add(tenant_user)
                await session.commit()
                
                # Initialize tenant database schema
                from src.tenant.context import TenantContext
                from src.tenant.manager import tenant_db_manager
                
                tenant_context = TenantContext(
                    tenant_id=tenant.id,
                    tenant_slug=tenant.slug,
                    database_url=tenant.database_url,
                    database_auth_token=tenant.database_auth_token,
                    name=tenant.name,
                    is_active=tenant.is_active,
                    subscription_status=tenant.subscription_status,
                    subscription_tier=tenant.subscription_tier,
                    owner_id=tenant.owner_id
                )
                
                await tenant_db_manager.initialize_tenant_database(tenant_context)
                
                logger.info("Created new tenant", 
                          tenant_id=tenant_id, 
                          slug=tenant_data.slug,
                          owner_id=owner_id)
                
                return Tenant.model_validate(tenant)
                
            except IntegrityError as e:
                await session.rollback()
                raise ValidationError(f"Tenant creation failed: {str(e)}")
            except Exception as e:
                await session.rollback()
                logger.error("Failed to create tenant", error=str(e))
                raise DatabaseError(f"Failed to create tenant: {str(e)}")
    
    async def get_tenant_by_id(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID."""
        async with get_global_database_session() as session:
            tenant = await self._get_tenant_by_id_db(session, tenant_id)
            return Tenant.model_validate(tenant) if tenant else None
    
    async def get_tenant_by_slug(self, slug: str) -> Optional[Tenant]:
        """Get tenant by slug."""
        async with get_global_database_session() as session:
            tenant = await self._get_tenant_by_slug_db(session, slug)
            return Tenant.model_validate(tenant) if tenant else None
    
    async def get_tenants_for_user(self, user_id: str) -> List[Tenant]:
        """Get all tenants for a user."""
        async with get_global_database_session() as session:
            try:
                query = (
                    select(TenantRegistry)
                    .join(TenantUser)
                    .where(
                        and_(
                            TenantUser.user_id == user_id,
                            TenantUser.is_active == True,
                            TenantUser.invitation_status == "accepted"
                        )
                    )
                    .order_by(TenantRegistry.name)
                )
                
                result = await session.execute(query)
                tenants = result.scalars().all()
                
                return [Tenant.model_validate(tenant) for tenant in tenants]
                
            except Exception as e:
                logger.error("Failed to get tenants for user", user_id=user_id, error=str(e))
                raise DatabaseError(f"Failed to get tenants for user: {str(e)}")
    
    async def update_tenant(self, tenant_id: str, tenant_data: TenantUpdate) -> Optional[Tenant]:
        """Update tenant."""
        async with get_global_database_session() as session:
            try:
                tenant = await self._get_tenant_by_id_db(session, tenant_id)
                if not tenant:
                    return None
                
                # Update fields
                update_data = tenant_data.model_dump(exclude_unset=True, exclude_none=True)
                
                if update_data:
                    query = (
                        update(TenantRegistry)
                        .where(TenantRegistry.id == tenant_id)
                        .values(**update_data)
                        .returning(TenantRegistry)
                    )
                    
                    result = await session.execute(query)
                    updated_tenant = result.scalar_one_or_none()
                    
                    if updated_tenant:
                        await session.commit()
                        logger.info("Updated tenant", tenant_id=tenant_id, changes=update_data)
                        return Tenant.model_validate(updated_tenant)
                    
                return Tenant.model_validate(tenant)
                
            except Exception as e:
                await session.rollback()
                logger.error("Failed to update tenant", tenant_id=tenant_id, error=str(e))
                raise DatabaseError(f"Failed to update tenant: {str(e)}")
    
    async def delete_tenant(self, tenant_id: str) -> bool:
        """Delete tenant (soft delete - deactivate)."""
        async with get_global_database_session() as session:
            try:
                query = (
                    update(TenantRegistry)
                    .where(TenantRegistry.id == tenant_id)
                    .values(is_active=False, updated_at=func.now())
                )
                
                result = await session.execute(query)
                await session.commit()
                
                if result.rowcount > 0:
                    logger.info("Deactivated tenant", tenant_id=tenant_id)
                    return True
                
                return False
                
            except Exception as e:
                await session.rollback()
                logger.error("Failed to delete tenant", tenant_id=tenant_id, error=str(e))
                raise DatabaseError(f"Failed to delete tenant: {str(e)}")
    
    async def add_user_to_tenant(
        self, 
        tenant_id: str, 
        user_data: TenantUserCreate,
        invited_by: str
    ) -> TenantUserSchema:
        """Add user to tenant."""
        async with get_global_database_session() as session:
            try:
                # Check if tenant exists and is active
                tenant = await self._get_tenant_by_id_db(session, tenant_id)
                if not tenant or not tenant.is_active:
                    raise TenantNotFoundError(tenant_id)
                
                # Check if user is already associated with tenant
                existing = await self._get_tenant_user_db(session, tenant_id, user_data.user_id)
                if existing:
                    raise ValidationError("User is already associated with this tenant")
                
                # Check tenant user limits
                current_user_count = await self._count_tenant_users(session, tenant_id)
                if not tenant.can_add_user(current_user_count):
                    raise BusinessLogicError(f"Tenant has reached maximum user limit ({tenant.max_users})")
                
                # Create tenant user association
                tenant_user = TenantUser(
                    tenant_id=tenant_id,
                    user_id=user_data.user_id,
                    role=user_data.role,
                    invited_by=invited_by,
                    invitation_status="accepted"
                )
                
                session.add(tenant_user)
                await session.commit()
                
                logger.info("Added user to tenant", 
                          tenant_id=tenant_id, 
                          user_id=user_data.user_id,
                          role=user_data.role)
                
                return TenantUserSchema.model_validate(tenant_user)
                
            except IntegrityError as e:
                await session.rollback()
                raise ValidationError(f"Failed to add user to tenant: {str(e)}")
            except Exception as e:
                await session.rollback()
                logger.error("Failed to add user to tenant", 
                           tenant_id=tenant_id, 
                           user_id=user_data.user_id, 
                           error=str(e))
                raise DatabaseError(f"Failed to add user to tenant: {str(e)}")
    
    async def get_tenant_stats(self, tenant_id: str) -> TenantStats:
        """Get tenant statistics."""
        async with get_global_database_session() as session:
            try:
                # Get user counts
                user_count_query = (
                    select(func.count(TenantUser.user_id))
                    .where(TenantUser.tenant_id == tenant_id)
                )
                user_count = await session.scalar(user_count_query) or 0
                
                active_user_count_query = (
                    select(func.count(TenantUser.user_id))
                    .where(
                        and_(
                            TenantUser.tenant_id == tenant_id,
                            TenantUser.is_active == True
                        )
                    )
                )
                active_user_count = await session.scalar(active_user_count_query) or 0
                
                # TODO: Get actual counts from tenant database
                # For now, return basic stats
                return TenantStats(
                    user_count=user_count,
                    active_user_count=active_user_count,
                    account_count=0,
                    transaction_count=0,
                    monthly_transaction_count=0,
                    budget_count=0,
                    goal_count=0,
                    family_member_count=0
                )
                
            except Exception as e:
                logger.error("Failed to get tenant stats", tenant_id=tenant_id, error=str(e))
                raise DatabaseError(f"Failed to get tenant stats: {str(e)}")
    
    # Private helper methods
    async def _get_tenant_by_id_db(self, session: AsyncSession, tenant_id: str) -> Optional[TenantRegistry]:
        """Get tenant by ID from database."""
        query = select(TenantRegistry).where(TenantRegistry.id == tenant_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()
    
    async def _get_tenant_by_slug_db(self, session: AsyncSession, slug: str) -> Optional[TenantRegistry]:
        """Get tenant by slug from database."""
        query = select(TenantRegistry).where(TenantRegistry.slug == slug)
        result = await session.execute(query)
        return result.scalar_one_or_none()
    
    async def _get_tenant_user_db(
        self, 
        session: AsyncSession, 
        tenant_id: str, 
        user_id: str
    ) -> Optional[TenantUser]:
        """Get tenant user association from database."""
        query = select(TenantUser).where(
            and_(
                TenantUser.tenant_id == tenant_id,
                TenantUser.user_id == user_id
            )
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()
    
    async def _count_tenants_for_owner(self, session: AsyncSession, owner_id: str) -> int:
        """Count tenants owned by user."""
        query = select(func.count(TenantRegistry.id)).where(TenantRegistry.owner_id == owner_id)
        return await session.scalar(query) or 0
    
    async def _count_tenant_users(self, session: AsyncSession, tenant_id: str) -> int:
        """Count active users in tenant."""
        query = (
            select(func.count(TenantUser.user_id))
            .where(
                and_(
                    TenantUser.tenant_id == tenant_id,
                    TenantUser.is_active == True
                )
            )
        )
        return await session.scalar(query) or 0
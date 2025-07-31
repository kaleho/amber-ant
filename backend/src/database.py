"""Multi-database connection management for global and tenant databases."""
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
import logging

from src.config import settings
from src.tenant.context import get_tenant_context, require_tenant_context
from src.tenant.manager import tenant_db_manager

logger = logging.getLogger(__name__)

# Global database engine (for tenant registry, system settings, etc.)
global_engine = create_async_engine(
    settings.GLOBAL_DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    future=True,
    pool_pre_ping=True,
    connect_args={
        "auth_token": settings.GLOBAL_AUTH_TOKEN,
    }
)

# Global session factory
global_session_maker = async_sessionmaker(
    global_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_global_database_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async session for global database."""
    async with global_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_tenant_database_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async session for current tenant's database."""
    tenant_context = require_tenant_context()
    session = await tenant_db_manager.get_tenant_session(tenant_context)
    
    try:
        yield session
    finally:
        await session.close()


# Base classes for different database contexts
GlobalBase = declarative_base()
TenantBase = declarative_base()

# Add table naming conventions
GlobalBase.metadata.naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

TenantBase.metadata.naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}


async def init_databases():
    """Initialize database connections."""
    try:
        # Test global database connection
        async with global_engine.begin() as conn:
            # Import global models to ensure they're registered
            from src.tenant.models import TenantRegistry, TenantUser  # noqa: F401
            
            # Create tables if needed (for development)
            if settings.DEBUG:
                await conn.run_sync(GlobalBase.metadata.create_all)
        
        logger.info("✅ Connected to global database successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to connect to global database: {e}")
        raise


async def close_databases():
    """Close all database connections."""
    await global_engine.dispose()
    await tenant_db_manager.close_all_connections()
    logger.info("🔒 Closed all database connections")
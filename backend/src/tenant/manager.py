"""Tenant database manager for multi-tenant architecture."""
from typing import Dict, Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.engine import Engine
import asyncio
import logging
import subprocess
import json
import uuid

from src.config import settings
from src.tenant.context import TenantContext
from src.exceptions import DatabaseConnectionError, InvalidTenantConfigurationError

logger = logging.getLogger(__name__)


class TenantDatabaseManager:
    """Manages connections to multiple tenant databases."""
    
    def __init__(self):
        self._engines: Dict[str, Engine] = {}
        self._session_makers: Dict[str, async_sessionmaker] = {}
        self._lock = asyncio.Lock()
    
    async def get_tenant_engine(self, tenant_context: TenantContext):
        """Get or create engine for tenant database."""
        tenant_id = tenant_context.tenant_id
        
        if tenant_id not in self._engines:
            async with self._lock:
                # Double-check pattern
                if tenant_id not in self._engines:
                    await self._create_tenant_engine(tenant_context)
        
        return self._engines[tenant_id]
    
    async def get_tenant_session(self, tenant_context: TenantContext) -> AsyncSession:
        """Get async session for tenant database."""
        tenant_id = tenant_context.tenant_id
        
        if tenant_id not in self._session_makers:
            await self.get_tenant_engine(tenant_context)
        
        session_maker = self._session_makers[tenant_id]
        return session_maker()
    
    async def _create_tenant_engine(self, tenant_context: TenantContext):
        """Create engine and session maker for tenant."""
        tenant_id = tenant_context.tenant_id
        
        try:
            engine = create_async_engine(
                tenant_context.database_url,
                echo=settings.DATABASE_ECHO,
                future=True,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10,
                connect_args={
                    "auth_token": tenant_context.auth_token,
                }
            )
            
            session_maker = async_sessionmaker(
                engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Test connection
            async with engine.begin() as conn:
                await conn.execute("SELECT 1")
            
            self._engines[tenant_id] = engine
            self._session_makers[tenant_id] = session_maker
            
            logger.info(f"Created database connection for tenant: {tenant_id}")
            
        except Exception as e:
            logger.error(f"Failed to create tenant engine for {tenant_id}: {e}")
            raise DatabaseConnectionError(f"Failed to connect to tenant database: {e}")
    
    async def create_tenant_database(self, tenant_data: dict) -> TenantContext:
        """Provision new tenant database in Turso."""
        tenant_slug = tenant_data["slug"]
        tenant_id = tenant_data.get("tenant_id") or str(uuid.uuid4())
        
        # Create database using Turso CLI
        db_name = f"tenant-{tenant_slug}-{tenant_id[:8]}"
        
        try:
            # Check if Turso CLI is available
            subprocess.run(
                ["turso", "--version"],
                check=True,
                capture_output=True,
                text=True
            )
            
            # Create database
            create_result = subprocess.run(
                ["turso", "db", "create", db_name],
                check=True,
                capture_output=True,
                text=True
            )
            logger.info(f"Created Turso database: {db_name}")
            
            # Get database URL
            url_result = subprocess.run(
                ["turso", "db", "show", "--url", db_name],
                check=True,
                capture_output=True,
                text=True
            )
            database_url = url_result.stdout.strip()
            
            # Create auth token
            token_result = subprocess.run(
                ["turso", "db", "tokens", "create", db_name],
                check=True,
                capture_output=True,
                text=True
            )
            auth_token = token_result.stdout.strip()
            
            # Create tenant context
            tenant_context = TenantContext(
                tenant_id=tenant_id,
                tenant_slug=tenant_slug,
                database_url=database_url,
                auth_token=auth_token,
                plan=tenant_data.get("plan", "basic"),
                is_active=True,
                features=tenant_data.get("features", []),
                metadata=tenant_data.get("metadata", {})
            )
            
            # Run tenant database migrations
            await self._run_tenant_migrations(tenant_context)
            
            logger.info(f"Successfully created tenant database: {db_name}")
            return tenant_context
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create tenant database: {e.stderr}")
            raise InvalidTenantConfigurationError(f"Tenant database creation failed: {e.stderr}")
        except FileNotFoundError:
            # Fallback for development without Turso CLI
            logger.warning("Turso CLI not found, using SQLite for development")
            return await self._create_development_database(tenant_data)
    
    async def _create_development_database(self, tenant_data: dict) -> TenantContext:
        """Create SQLite database for development."""
        tenant_slug = tenant_data["slug"]
        tenant_id = tenant_data.get("tenant_id") or str(uuid.uuid4())
        
        # Use SQLite for development
        db_path = f"./tenant_dbs/tenant_{tenant_slug}_{tenant_id[:8]}.db"
        database_url = f"sqlite+aiosqlite:///{db_path}"
        
        tenant_context = TenantContext(
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            database_url=database_url,
            auth_token="dev-token",  # Not used for SQLite
            plan=tenant_data.get("plan", "basic"),
            is_active=True,
            features=tenant_data.get("features", []),
            metadata=tenant_data.get("metadata", {})
        )
        
        # Create directory for tenant databases
        import os
        os.makedirs("./tenant_dbs", exist_ok=True)
        
        # Initialize database with schema
        await self._run_tenant_migrations(tenant_context)
        
        logger.info(f"Created development database for tenant: {tenant_id}")
        return tenant_context
    
    async def _run_tenant_migrations(self, tenant_context: TenantContext):
        """Run migrations for tenant database."""
        try:
            # Create engine temporarily for migrations
            engine = create_async_engine(
                tenant_context.database_url,
                echo=False,
                connect_args={
                    "auth_token": tenant_context.auth_token,
                } if not tenant_context.database_url.startswith("sqlite") else {}
            )
            
            # Import tenant models to ensure they're registered
            from src.users.models import User  # noqa: F401
            from src.accounts.models import Account  # noqa: F401
            from src.transactions.models import Transaction  # noqa: F401
            from src.budgets.models import Budget  # noqa: F401
            from src.goals.models import SavingsGoal  # noqa: F401
            from src.tithing.models import TithingPayment  # noqa: F401
            from src.families.models import Family, FamilyMember, FamilyInvitation  # noqa: F401
            from src.subscriptions.models import Subscription  # noqa: F401
            from src.database import TenantBase
            
            # Create all tables
            async with engine.begin() as conn:
                await conn.run_sync(TenantBase.metadata.create_all)
            
            await engine.dispose()
            logger.info(f"Ran migrations for tenant: {tenant_context.tenant_id}")
            
        except Exception as e:
            logger.error(f"Failed to run tenant migrations: {e}")
            raise DatabaseConnectionError(f"Failed to initialize tenant database: {e}")
    
    async def close_tenant_connections(self, tenant_id: str):
        """Close connections for specific tenant."""
        if tenant_id in self._engines:
            await self._engines[tenant_id].dispose()
            del self._engines[tenant_id]
            del self._session_makers[tenant_id]
            logger.info(f"Closed connections for tenant: {tenant_id}")
    
    async def close_all_connections(self):
        """Close all tenant database connections."""
        for tenant_id, engine in self._engines.items():
            await engine.dispose()
            logger.info(f"Closed connection for tenant: {tenant_id}")
        
        self._engines.clear()
        self._session_makers.clear()
        logger.info("Closed all tenant database connections")
    
    async def health_check(self, tenant_context: TenantContext) -> bool:
        """Check if tenant database is healthy."""
        try:
            session = await self.get_tenant_session(tenant_context)
            async with session:
                await session.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Tenant database health check failed for {tenant_context.tenant_id}: {e}")
            return False


# Global tenant database manager instance
tenant_db_manager = TenantDatabaseManager()
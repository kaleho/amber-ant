# MASTER DEVELOPMENT PROMPT: Multi-Tenant FastAPI Backend with Auth0 & Turso

## Project Overview

Create a **production-ready multi-tenant FastAPI backend server** with modern Python 2025 best practices, featuring Auth0 JWT authentication, Turso LibSQL multi-database architecture, UV package management, and clean tenant isolation patterns.

## 🏢 Multi-Tenant Architecture Overview

### Database Architecture
- **Global Database**: Single database for application-wide data (auth, system settings, tenant registry)
- **Tenant Databases**: Individual databases per tenant/account for complete data isolation
- **Dynamic Database Routing**: Runtime database selection based on tenant context
- **Schema Management**: Automated tenant database provisioning and migrations

### Tenant Isolation Strategy
- **Database-level isolation**: Each tenant gets their own Turso database
- **Shared application layer**: Single codebase serves all tenants
- **Tenant context resolution**: Extract tenant from JWT claims, subdomain, or header
- **Resource isolation**: Complete separation of tenant data and operations

## 🎯 Core Requirements

### Technology Stack
- **Python 3.11+** with modern async/await patterns
- **FastAPI** for high-performance REST API
- **UV package manager** for lightning-fast dependency management
- **Auth0** for enterprise-grade JWT authentication with tenant claims
- **Turso LibSQL** with multiple database support
- **SQLAlchemy 2.0** with dynamic database routing
- **Alembic** for both global and tenant migrations
- **Pydantic V2** for data validation and serialization
- **Docker** with multi-stage builds
- **pytest** with multi-tenant test support

### Architecture Principles
- **Multi-Tenant Clean Architecture** with tenant context propagation
- **Repository Pattern** with tenant-aware data access
- **Dependency Injection** with tenant context resolution
- **Service Layer** with tenant isolation
- **PEP 420 Namespace Packages** (no `__init__.py` files)
- **Async/Await** throughout the entire stack
- **Tenant Context Middleware** for automatic tenant resolution

## 🏗️ Project Structure

```
src/
├── main.py                     # FastAPI app initialization & startup
├── config.py                   # Settings & environment configuration
├── database.py                 # Multi-database connection management
├── exceptions.py               # Custom exception classes
├── middleware.py               # Tenant context middleware
├── tenant/                     # Tenant management system
│   ├── context.py              # Tenant context management
│   ├── resolver.py             # Tenant resolution strategies
│   ├── manager.py              # Tenant database management
│   ├── models.py               # Global tenant registry models
│   ├── schemas.py              # Tenant Pydantic schemas
│   ├── service.py              # Tenant provisioning service
│   └── router.py               # Tenant management endpoints
├── auth/                       # Authentication & authorization system
│   ├── dependencies.py         # Auth dependency injection
│   ├── schemas.py              # Auth Pydantic models
│   ├── service.py              # Auth business logic
│   └── router.py               # Auth API endpoints
├── users/                      # User management domain (tenant-scoped)
│   ├── models.py               # SQLAlchemy user models
│   ├── schemas.py              # User Pydantic schemas
│   ├── repository.py           # User data access layer
│   ├── service.py              # User business logic
│   └── router.py               # User API endpoints
├── accounts/                   # Account/Organization management (tenant-scoped)
│   ├── models.py               # Account models
│   ├── schemas.py              # Account schemas
│   ├── repository.py           # Account data access
│   ├── service.py              # Account business logic
│   └── router.py               # Account API endpoints
└── shared/                     # Shared utilities & common code
    ├── dependencies.py         # Common dependency injection
    ├── database.py             # Database utilities
    └── utils.py                # Utility functions

tests/
├── conftest.py                 # pytest configuration & fixtures
├── tenant/                     # Tenant management tests
├── auth/                       # Authentication tests
├── users/                      # User management tests
├── accounts/                   # Account tests
└── shared/                     # Shared test utilities

migrations/
├── global/                     # Global database migrations
│   ├── versions/
│   ├── env.py
│   └── alembic.ini
└── tenant/                     # Tenant database migration templates
    ├── versions/
    ├── env.py
    └── alembic.ini

docker/
├── Dockerfile                  # Production Docker image
├── Dockerfile.dev              # Development Docker image
└── docker-compose.yml          # Development services

.env.example                    # Environment variables template
pyproject.toml                  # UV dependencies & project config
uv.lock                         # UV lockfile
```

## 🏢 Tenant Context & Resolution

### Tenant Context Management

```python
# tenant/context.py
from contextvars import ContextVar
from typing import Optional
from dataclasses import dataclass

@dataclass
class TenantContext:
    """Tenant context information."""
    tenant_id: str
    tenant_slug: str
    database_url: str
    auth_token: str
    plan: str = "basic"
    is_active: bool = True
    features: list[str] = None

    def __post_init__(self):
        if self.features is None:
            self.features = []

# Global tenant context variable
_tenant_context: ContextVar[Optional[TenantContext]] = ContextVar('tenant_context', default=None)

def get_tenant_context() -> Optional[TenantContext]:
    """Get current tenant context."""
    return _tenant_context.get()

def set_tenant_context(context: TenantContext) -> None:
    """Set tenant context for current request."""
    _tenant_context.set(context)

def require_tenant_context() -> TenantContext:
    """Get tenant context or raise error if not set."""
    context = get_tenant_context()
    if not context:
        raise ValueError("No tenant context available")
    return context

def clear_tenant_context() -> None:
    """Clear tenant context."""
    _tenant_context.set(None)
```

### Tenant Resolution Strategies

```python
# tenant/resolver.py
from abc import ABC, abstractmethod
from typing import Optional
from fastapi import Request, HTTPException, status
import jwt
from sqlalchemy.ext.asyncio import AsyncSession

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
            return unverified_payload.get("https://yourapp.com/tenant_id")
        except jwt.InvalidTokenError:
            return None

class SubdomainTenantResolver(TenantResolver):
    """Resolve tenant from subdomain."""
    
    async def resolve_tenant(self, request: Request) -> Optional[str]:
        """Extract tenant slug from subdomain."""
        host = request.headers.get("host", "")
        parts = host.split(".")
        
        if len(parts) >= 3:  # subdomain.domain.com
            subdomain = parts[0]
            if subdomain and subdomain != "www":
                return subdomain
        
        return None

class HeaderTenantResolver(TenantResolver):
    """Resolve tenant from X-Tenant-ID header."""
    
    async def resolve_tenant(self, request: Request) -> Optional[str]:
        """Extract tenant ID from header."""
        return request.headers.get("X-Tenant-ID")

class CompositeTenantResolver(TenantResolver):
    """Composite resolver that tries multiple strategies."""
    
    def __init__(self, resolvers: list[TenantResolver]):
        self.resolvers = resolvers
    
    async def resolve_tenant(self, request: Request) -> Optional[str]:
        """Try each resolver until one succeeds."""
        for resolver in self.resolvers:
            tenant_id = await resolver.resolve_tenant(request)
            if tenant_id:
                return tenant_id
        return None
```

### Tenant Database Manager

```python
# tenant/manager.py
from typing import Dict, Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.engine import Engine
import asyncio
import logging
from src.config import settings
from src.tenant.models import TenantRegistry
from src.tenant.context import TenantContext

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
        
        engine = create_async_engine(
            tenant_context.database_url,
            echo=settings.DATABASE_ECHO,
            future=True,
            pool_pre_ping=True,
            connect_args={
                "auth_token": tenant_context.auth_token,
            }
        )
        
        session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        self._engines[tenant_id] = engine
        self._session_makers[tenant_id] = session_maker
        
        logger.info(f"Created database connection for tenant: {tenant_id}")
    
    async def create_tenant_database(self, tenant_data: dict) -> TenantContext:
        """Provision new tenant database in Turso."""
        import subprocess
        import json
        
        tenant_slug = tenant_data["slug"]
        tenant_id = tenant_data["tenant_id"]
        
        # Create database using Turso CLI
        db_name = f"tenant-{tenant_slug}-{tenant_id}"
        
        try:
            # Create database
            subprocess.run(
                ["turso", "db", "create", db_name],
                check=True,
                capture_output=True,
                text=True
            )
            
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
                is_active=True
            )
            
            # Run tenant database migrations
            await self._run_tenant_migrations(tenant_context)
            
            logger.info(f"Successfully created tenant database: {db_name}")
            return tenant_context
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create tenant database: {e}")
            raise RuntimeError(f"Tenant database creation failed: {e}")
    
    async def _run_tenant_migrations(self, tenant_context: TenantContext):
        """Run migrations for tenant database."""
        # This would integrate with Alembic to run tenant-specific migrations
        # Implementation depends on your migration strategy
        pass
    
    async def close_tenant_connections(self, tenant_id: str):
        """Close connections for specific tenant."""
        if tenant_id in self._engines:
            await self._engines[tenant_id].dispose()
            del self._engines[tenant_id]
            del self._session_makers[tenant_id]
    
    async def close_all_connections(self):
        """Close all tenant database connections."""
        for engine in self._engines.values():
            await engine.dispose()
        self._engines.clear()
        self._session_makers.clear()

# Global tenant database manager instance
tenant_db_manager = TenantDatabaseManager()
```

## 🗄️ Multi-Database Configuration

### Database Layer with Global and Tenant Databases

```python
# database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import Optional
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

async def get_global_database_session() -> AsyncSession:
    """Get async session for global database."""
    async with global_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()

async def get_tenant_database_session() -> AsyncSession:
    """Get async session for current tenant's database."""
    tenant_context = require_tenant_context()
    session = await tenant_db_manager.get_tenant_session(tenant_context)
    
    try:
        yield session
    finally:
        await session.close()

# Base classes for different database contexts
class GlobalBase(declarative_base()):
    """Base class for global database models."""
    pass

class TenantBase(declarative_base()):
    """Base class for tenant database models."""
    pass

# Database initialization
async def init_databases():
    """Initialize database connections."""
    try:
        # Test global database connection
        async with global_engine.begin() as conn:
            # Import global models
            from src.tenant.models import GlobalBase
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
```

### Multi-Tenant Model Design

```python
# tenant/models.py (Global Database Models)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Boolean, Text, JSON
from datetime import datetime
from src.database import GlobalBase

class TenantRegistry(GlobalBase):
    """Global registry of all tenants."""
    __tablename__ = "tenant_registry"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    database_url: Mapped[str] = mapped_column(String(500))
    auth_token: Mapped[str] = mapped_column(Text)  # Encrypted
    plan: Mapped[str] = mapped_column(String(50), default="basic")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    features: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class TenantUser(GlobalBase):
    """Global mapping of users to tenants (for multi-tenant users)."""
    __tablename__ = "tenant_users"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    auth0_id: Mapped[str] = mapped_column(String(255), index=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    role: Mapped[str] = mapped_column(String(50), default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

# users/models.py (Tenant Database Models)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Boolean, Text, ForeignKey, Index
from datetime import datetime
from src.database import TenantBase

class User(TenantBase):
    """User model for tenant database."""
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    auth0_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    picture: Mapped[str | None] = mapped_column(String(500), nullable=True)
    role: Mapped[str] = mapped_column(String(50), default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships within tenant
    profile: Mapped["UserProfile"] = relationship("UserProfile", back_populates="user", uselist=False)
    sessions: Mapped[list["UserSession"]] = relationship("UserSession", back_populates="user")

class Account(TenantBase):
    """Account/Organization model for tenant database."""
    __tablename__ = "accounts"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    settings: Mapped[dict] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    members: Mapped[list["AccountMember"]] = relationship("AccountMember", back_populates="account")

class AccountMember(TenantBase):
    """Account membership model."""
    __tablename__ = "account_members"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    role: Mapped[str] = mapped_column(String(50), default="member")
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    account: Mapped["Account"] = relationship("Account", back_populates="members")
    user: Mapped["User"] = relationship("User")
```

## 🔗 Tenant Context Middleware

```python
# middleware.py
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging
from src.tenant.resolver import CompositeTenantResolver, JWTTenantResolver, SubdomainTenantResolver, HeaderTenantResolver
from src.tenant.context import set_tenant_context, clear_tenant_context, TenantContext
from src.tenant.service import TenantService
from src.database import get_global_database_session

logger = logging.getLogger(__name__)

class TenantContextMiddleware(BaseHTTPMiddleware):
    """Middleware to resolve and set tenant context for each request."""
    
    def __init__(self, app, tenant_resolver: CompositeTenantResolver = None):
        super().__init__(app)
        
        # Default composite resolver with multiple strategies
        if tenant_resolver is None:
            self.tenant_resolver = CompositeTenantResolver([
                JWTTenantResolver(),
                SubdomainTenantResolver(),
                HeaderTenantResolver()
            ])
        else:
            self.tenant_resolver = tenant_resolver
    
    async def dispatch(self, request: Request, call_next):
        """Process request and set tenant context."""
        
        # Skip tenant resolution for certain paths
        if self._should_skip_tenant_resolution(request.url.path):
            return await call_next(request)
        
        try:
            # Resolve tenant identifier
            tenant_identifier = await self.tenant_resolver.resolve_tenant(request)
            
            if tenant_identifier:
                # Get tenant context from global database
                async with get_global_database_session() as global_db:
                    tenant_service = TenantService(global_db)
                    tenant_context = await tenant_service.get_tenant_context(tenant_identifier)
                    
                    if tenant_context and tenant_context.is_active:
                        # Set tenant context for this request
                        set_tenant_context(tenant_context)
                        logger.debug(f"Set tenant context: {tenant_context.tenant_id}")
                    else:
                        # Tenant not found or inactive
                        if not tenant_context:
                            logger.warning(f"Tenant not found: {tenant_identifier}")
                            raise HTTPException(
                                status_code=status.HTTP_404_NOT_FOUND,
                                detail="Tenant not found"
                            )
                        else:
                            logger.warning(f"Tenant inactive: {tenant_identifier}")
                            raise HTTPException(
                                status_code=status.HTTP_403_FORBIDDEN,
                                detail="Tenant account suspended"
                            )
            
            # Process request
            response = await call_next(request)
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Tenant context middleware error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Tenant resolution failed"
            )
        finally:
            # Always clear tenant context after request
            clear_tenant_context()
    
    def _should_skip_tenant_resolution(self, path: str) -> bool:
        """Check if tenant resolution should be skipped for this path."""
        skip_paths = [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico",
            "/api/v1/auth/login",  # Login might not have tenant context yet
            "/api/v1/tenants/register"  # Tenant registration
        ]
        
        return any(path.startswith(skip_path) for skip_path in skip_paths)
```

## 🏢 Tenant Service Layer

```python
# tenant/service.py
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
import logging
from src.tenant.models import TenantRegistry, TenantUser
from src.tenant.context import TenantContext
from src.tenant.manager import tenant_db_manager
from src.shared.utils import encrypt_token, decrypt_token

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
        
        return TenantContext(
            tenant_id=tenant.id,
            tenant_slug=tenant.slug,
            database_url=tenant.database_url,
            auth_token=decrypt_token(tenant.auth_token),
            plan=tenant.plan,
            is_active=tenant.is_active,
            features=list(tenant.features.keys()) if tenant.features else []
        )
    
    async def create_tenant(self, tenant_data: dict) -> TenantContext:
        """Create new tenant with database provisioning."""
        tenant_id = str(uuid.uuid4())
        
        # Prepare tenant data
        full_tenant_data = {
            **tenant_data,
            "tenant_id": tenant_id
        }
        
        # Create tenant database
        tenant_context = await tenant_db_manager.create_tenant_database(full_tenant_data)
        
        # Register in global database
        tenant_registry = TenantRegistry(
            id=tenant_id,
            slug=tenant_data["slug"],
            name=tenant_data["name"],
            database_url=tenant_context.database_url,
            auth_token=encrypt_token(tenant_context.auth_token),
            plan=tenant_data.get("plan", "basic"),
            features=tenant_data.get("features", {}),
            metadata=tenant_data.get("metadata", {})
        )
        
        self.global_db.add(tenant_registry)
        await self.global_db.commit()
        
        logger.info(f"Created tenant: {tenant_id} ({tenant_data['slug']})")
        return tenant_context
    
    async def add_user_to_tenant(self, auth0_id: str, tenant_id: str, role: str = "user") -> bool:
        """Add user to tenant in global registry."""
        # Check if mapping already exists
        stmt = select(TenantUser).where(
            (TenantUser.auth0_id == auth0_id) &
            (TenantUser.tenant_id == tenant_id)
        )
        result = await self.global_db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update role if different
            if existing.role != role:
                existing.role = role
                await self.global_db.commit()
            return True
        
        # Create new mapping
        tenant_user = TenantUser(
            id=str(uuid.uuid4()),
            auth0_id=auth0_id,
            tenant_id=tenant_id,
            role=role
        )
        
        self.global_db.add(tenant_user)
        await self.global_db.commit()
        
        return True
    
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
    
    async def deactivate_tenant(self, tenant_id: str) -> bool:
        """Deactivate tenant (soft delete)."""
        stmt = select(TenantRegistry).where(TenantRegistry.id == tenant_id)
        result = await self.global_db.execute(stmt)
        tenant = result.scalar_one_or_none()
        
        if tenant:
            tenant.is_active = False
            await self.global_db.commit()
            
            # Close database connections
            await tenant_db_manager.close_tenant_connections(tenant_id)
            
            return True
        
        return False
```

## 🔐 Multi-Tenant Authentication

### Enhanced Auth Dependencies

```python
# auth/dependencies.py
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging
from src.database import get_global_database_session, get_tenant_database_session
from src.tenant.context import get_tenant_context, require_tenant_context
from src.tenant.service import TenantService
from src.users.models import User
from src.users.service import UserService
from src.auth.service import Auth0Service

logger = logging.getLogger(__name__)
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    tenant_db: AsyncSession = Depends(get_tenant_database_session),
    global_db: AsyncSession = Depends(get_global_database_session)
) -> User:
    """Extract and validate user from JWT token with tenant context."""
    
    try:
        # Validate JWT token
        auth_service = Auth0Service()
        user_claims = await auth_service.validate_jwt_token(credentials.credentials)
        
        # Get tenant context
        tenant_context = require_tenant_context()
        
        # Verify user belongs to this tenant
        tenant_service = TenantService(global_db)
        user_tenants = await tenant_service.get_user_tenants(user_claims["sub"])
        
        if not any(t.id == tenant_context.tenant_id for t in user_tenants):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User not authorized for this tenant"
            )
        
        # Get or create user in tenant database
        user_service = UserService(tenant_db)
        user = await user_service.get_or_create_user_from_auth0(user_claims)
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account inactive"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

async def require_tenant_admin(
    current_user: User = Depends(get_current_user),
    global_db: AsyncSession = Depends(get_global_database_session)
) -> User:
    """Require user to be admin of current tenant."""
    tenant_context = require_tenant_context()
    
    # Check tenant-level admin permission
    tenant_service = TenantService(global_db)
    stmt = select(TenantUser).where(
        (TenantUser.auth0_id == current_user.auth0_id) &
        (TenantUser.tenant_id == tenant_context.tenant_id)
    )
    result = await global_db.execute(stmt)
    tenant_user = result.scalar_one_or_none()
    
    if not tenant_user or tenant_user.role not in ["admin", "owner"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant admin access required"
        )
    
    return current_user

async def require_global_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Require global system admin access."""
    try:
        auth_service = Auth0Service()
        user_claims = await auth_service.validate_jwt_token(credentials.credentials)
        
        # Check for global admin claim
        if not user_claims.get("https://yourapp.com/global_admin", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Global admin access required"
            )
        
        return user_claims
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Global admin authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
```

## ⚙️ Multi-Tenant Configuration

```python
# config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional

class Settings(BaseSettings):
    """Application settings for multi-tenant architecture."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )
    
    # Application
    PROJECT_NAME: str = "Multi-Tenant FastAPI Backend"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str
    ENCRYPTION_KEY: str  # For encrypting tenant auth tokens
    
    # Auth0
    AUTH0_DOMAIN: str
    AUTH0_AUDIENCE: str
    AUTH0_CLIENT_ID: Optional[str] = None
    AUTH0_CLIENT_SECRET: Optional[str] = None
    
    # Global Database (Tenant Registry)
    GLOBAL_DATABASE_URL: str  # libsql://global-db.turso.io
    GLOBAL_AUTH_TOKEN: str    # Auth token for global database
    DATABASE_ECHO: bool = False
    
    # Tenant Resolution
    DEFAULT_TENANT_RESOLVER: str = "composite"  # jwt, subdomain, header, composite
    TENANT_HEADER_NAME: str = "X-Tenant-ID"
    
    # Multi-tenancy Settings
    MAX_TENANTS_PER_USER: int = 5
    TENANT_SLUG_MIN_LENGTH: int = 3
    TENANT_SLUG_MAX_LENGTH: int = 50
    
    # CORS
    CORS_ALLOW_ORIGINS: List[str] = ["http://localhost:3000"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # Rate Limiting (Per Tenant)
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600
    
    # API Documentation
    DOCS_URL: Optional[str] = "/docs"
    REDOC_URL: Optional[str] = "/redoc"
    OPENAPI_URL: Optional[str] = "/openapi.json"
    
    @property
    def auth0_issuer(self) -> str:
        return f"https://{self.AUTH0_DOMAIN}/"
    
    @property
    def auth0_jwks_url(self) -> str:
        return f"https://{self.AUTH0_DOMAIN}/.well-known/jwks.json"

settings = Settings()
```

### Environment Variables Example

```bash
# .env.example

# Application
PROJECT_NAME="Multi-Tenant FastAPI Backend"
VERSION="1.0.0"
DEBUG=false
SECRET_KEY="your-super-secret-key-here"
ENCRYPTION_KEY="your-encryption-key-for-tenant-tokens"

# Auth0 Configuration
AUTH0_DOMAIN="your-domain.auth0.com"
AUTH0_AUDIENCE="your-api-identifier"
AUTH0_CLIENT_ID="your-auth0-client-id"
AUTH0_CLIENT_SECRET="your-auth0-client-secret"

# Global Database (Tenant Registry)
GLOBAL_DATABASE_URL="libsql://global-registry.turso.io"
GLOBAL_AUTH_TOKEN="your-global-db-auth-token"
DATABASE_ECHO=false

# Tenant Resolution
DEFAULT_TENANT_RESOLVER="composite"
TENANT_HEADER_NAME="X-Tenant-ID"

# Multi-tenancy Settings
MAX_TENANTS_PER_USER=5
TENANT_SLUG_MIN_LENGTH=3
TENANT_SLUG_MAX_LENGTH=50

# CORS Configuration
CORS_ALLOW_ORIGINS="http://localhost:3000,https://*.yourapp.com"
CORS_ALLOW_CREDENTIALS=true

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600
```

## 🧪 Multi-Tenant Testing Strategy

```python
# tests/conftest.py
import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from unittest.mock import patch
import uuid

from src.main import app
from src.database import get_global_database_session, get_tenant_database_session
from src.tenant.models import GlobalBase
from src.users.models import TenantBase
from src.tenant.context import TenantContext, set_tenant_context

# Test database URLs
TEST_GLOBAL_DB_URL = "sqlite+aiosqlite:///./test_global.db"
TEST_TENANT_DB_URL = "sqlite+aiosqlite:///./test_tenant.db"

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def test_global_db():
    """Create test global database session."""
    engine = create_async_engine(TEST_GLOBAL_DB_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(GlobalBase.metadata.create_all)
    
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(GlobalBase.metadata.drop_all)
    
    await engine.dispose()

@pytest.fixture
async def test_tenant_db():
    """Create test tenant database session."""
    engine = create_async_engine(TEST_TENANT_DB_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(TenantBase.metadata.create_all)
    
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(TenantBase.metadata.drop_all)
    
    await engine.dispose()

@pytest.fixture
def test_tenant_context():
    """Create test tenant context."""
    return TenantContext(
        tenant_id="test-tenant-123",
        tenant_slug="test-tenant",
        database_url=TEST_TENANT_DB_URL,
        auth_token="test-token",
        plan="basic",
        is_active=True
    )

@pytest.fixture
async def client_with_tenant(test_global_db, test_tenant_db, test_tenant_context):
    """Create test client with tenant context."""
    
    # Override database dependencies
    app.dependency_overrides[get_global_database_session] = lambda: test_global_db
    app.dependency_overrides[get_tenant_database_session] = lambda: test_tenant_db
    
    # Set tenant context
    set_tenant_context(test_tenant_context)
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()

@pytest.fixture
def mock_auth0_user():
    return {
        "sub": "auth0|test123",
        "email": "test@example.com",
        "name": "Test User",
        "https://yourapp.com/tenant_id": "test-tenant-123"
    }
```

## 📋 Implementation Checklist

### Phase 1: Multi-Tenant Foundation
- [ ] Set up global database for tenant registry
- [ ] Implement tenant context management system
- [ ] Create tenant resolution strategies (JWT, subdomain, header)
- [ ] Build tenant database manager with Turso integration
- [ ] Implement tenant context middleware

### Phase 2: Tenant Database Architecture
- [ ] Design global vs tenant model separation
- [ ] Implement dynamic database routing
- [ ] Create tenant database provisioning system
- [ ] Set up tenant-specific migrations
- [ ] Build tenant lifecycle management

### Phase 3: Multi-Tenant Authentication
- [ ] Enhance Auth0 integration with tenant claims
- [ ] Implement tenant-aware user authentication
- [ ] Build tenant admin authorization system
- [ ] Create global admin access controls
- [ ] Add user-tenant relationship management

### Phase 4: Tenant Management API
- [ ] Build tenant registration endpoints
- [ ] Create tenant management dashboard APIs
- [ ] Implement user invitation system
- [ ] Add tenant settings and configuration
- [ ] Build tenant analytics and monitoring

### Phase 5: Data Isolation & Security
- [ ] Ensure complete tenant data isolation
- [ ] Implement tenant-aware repositories
- [ ] Add tenant context validation
- [ ] Build tenant resource quotas
- [ ] Create tenant backup/restore system

### Phase 6: Performance & Scaling
- [ ] Optimize multi-database connection pooling
- [ ] Implement tenant database caching
- [ ] Add tenant-specific rate limiting
- [ ] Build tenant usage monitoring
- [ ] Create tenant scaling strategies

### Phase 7: Migration & Deployment
- [ ] Create tenant migration scripts
- [ ] Build tenant database deployment automation
- [ ] Implement tenant health monitoring
- [ ] Add tenant disaster recovery
- [ ] Create tenant onboarding automation

## 🎯 Multi-Tenant Success Criteria

Your implementation is complete when:

1. **Tenant Isolation**: Complete data separation between tenants
2. **Dynamic Database Routing**: Automatic tenant database selection
3. **Tenant Authentication**: JWT-based tenant context resolution
4. **Tenant Provisioning**: Automated tenant database creation
5. **Global Management**: Centralized tenant registry and management
6. **Performance**: Efficient multi-database connection handling
7. **Security**: Proper tenant authorization and access controls
8. **Testing**: Comprehensive multi-tenant test coverage

This multi-tenant architecture provides complete data isolation while maintaining operational efficiency through shared application infrastructure and centralized management.
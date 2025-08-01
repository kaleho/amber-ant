"""Main FastAPI application for Faithful Finances backend."""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import structlog

from src.config import settings
from src.exceptions import (
    TenantNotFoundError,
    AuthenticationError,
    AuthorizationError,
    ValidationError,
    ExternalServiceError
)
from src.middleware import TenantContextMiddleware, LoggingMiddleware, SecurityMiddleware
from src.security.headers import EnhancedSecurityMiddleware, HTTPSRedirectMiddleware, SecurityValidationMiddleware
from src.performance.middleware import PerformanceMiddleware, SlowRequestLogger, MetricsCollectionMiddleware
from src.database import init_databases

# Import all routers
from src.auth.router import router as auth_router
from src.users.router import router as users_router
from src.accounts.router import router as accounts_router
from src.transactions.router import router as transactions_router
from src.budgets.router import router as budgets_router
from src.goals.router import router as goals_router
from src.tithing.router import router as tithing_router
from src.families.router import router as families_router
from src.subscriptions.router import router as subscriptions_router
from src.plaid.router import router as plaid_router
from src.services.webhooks import router as webhooks_router
from src.performance.endpoints import router as performance_router


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer() if settings.LOG_FORMAT == "json" else structlog.dev.ConsoleRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Faithful Finances API", version=settings.VERSION)
    
    # Initialize global database
    await init_databases()
    logger.info("Global database initialized")
    
    # Initialize Redis connection pool
    from src.services.redis import get_redis_client, close_redis_client
    redis_client = await get_redis_client()
    logger.info("Redis connection pool initialized")
    
    # Initialize background task queues
    from src.services.background import get_celery_app
    celery_app = get_celery_app()
    logger.info("Celery application initialized")
    
    # Start performance monitoring
    from src.performance.monitoring import PerformanceMonitor
    from src.performance.metrics import global_metrics
    performance_monitor = PerformanceMonitor(global_metrics)
    
    # Start monitoring as background task (don't await to avoid blocking)
    import asyncio
    asyncio.create_task(performance_monitor.start_monitoring())
    logger.info("Performance monitoring started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Faithful Finances API")
    
    # Close Redis connections
    await close_redis_client()
    logger.info("Redis connections closed")
    
    # Background tasks will be handled by Celery worker shutdown
    logger.info("External services shutdown completed")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="Multi-tenant FastAPI backend for biblical stewardship and family financial management",
        docs_url=settings.DOCS_URL,
        redoc_url=settings.REDOC_URL,
        openapi_url=settings.OPENAPI_URL,
        lifespan=lifespan,
        debug=settings.DEBUG,
    )
    
    # Security Middleware
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=["*"] if settings.DEBUG else ["faithfulfinances.com", "*.faithfulfinances.com"]
    )
    
    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )
    
    # Custom Middleware (order matters - last added runs first)
    app.add_middleware(SecurityMiddleware)  # Keep existing for compatibility
    app.add_middleware(EnhancedSecurityMiddleware)  # Enhanced security headers
    app.add_middleware(SecurityValidationMiddleware)  # Security validations
    app.add_middleware(HTTPSRedirectMiddleware)  # HTTPS enforcement
    app.add_middleware(PerformanceMiddleware, enabled=True)  # Performance monitoring
    app.add_middleware(SlowRequestLogger, slow_threshold_ms=1000.0)  # Log slow requests
    app.add_middleware(MetricsCollectionMiddleware, collect_detailed_metrics=settings.DEBUG)  # Detailed metrics in debug mode
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(TenantContextMiddleware)
    
    # Exception Handlers
    @app.exception_handler(TenantNotFoundError)
    async def tenant_not_found_handler(request: Request, exc: TenantNotFoundError) -> JSONResponse:
        logger.warning("Tenant not found", tenant_id=exc.tenant_id, path=request.url.path)
        return JSONResponse(
            status_code=404,
            content={
                "error": "tenant_not_found",
                "message": "The specified tenant was not found or is not accessible",
                "tenant_id": exc.tenant_id
            }
        )
    
    @app.exception_handler(AuthenticationError)
    async def authentication_error_handler(request: Request, exc: AuthenticationError) -> JSONResponse:
        logger.warning("Authentication failed", path=request.url.path, reason=str(exc))
        return JSONResponse(
            status_code=401,
            content={
                "error": "authentication_failed",
                "message": "Authentication credentials are invalid or missing"
            }
        )
    
    @app.exception_handler(AuthorizationError)
    async def authorization_error_handler(request: Request, exc: AuthorizationError) -> JSONResponse:
        logger.warning("Authorization failed", path=request.url.path, reason=str(exc))
        return JSONResponse(
            status_code=403,
            content={
                "error": "authorization_failed",
                "message": "You do not have permission to access this resource"
            }
        )
    
    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
        logger.warning("Validation failed", path=request.url.path, details=exc.details)
        return JSONResponse(
            status_code=422,
            content={
                "error": "validation_failed",
                "message": "Request validation failed",
                "details": exc.details
            }
        )
    
    @app.exception_handler(ExternalServiceError)
    async def external_service_error_handler(request: Request, exc: ExternalServiceError) -> JSONResponse:
        logger.error("External service error", service=exc.service, path=request.url.path, error=str(exc))
        return JSONResponse(
            status_code=502,
            content={
                "error": "external_service_error",
                "message": f"External service '{exc.service}' is currently unavailable",
                "service": exc.service
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error("Unhandled exception", path=request.url.path, error=str(exc), exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": "An unexpected error occurred. Please try again later."
            }
        )
    
    # Health Check Endpoints
    @app.get("/health")
    async def health_check():
        """Basic health check endpoint."""
        return {
            "status": "healthy",
            "service": "faithful-finances-api",
            "version": settings.VERSION
        }
    
    @app.get("/health/detailed")
    async def detailed_health_check():
        """Detailed health check with service dependencies."""
        # Check database connectivity
        database_status = "healthy"
        try:
            from src.database import global_engine
            async with global_engine.begin() as conn:
                await conn.execute("SELECT 1")
        except Exception as e:
            database_status = "unhealthy"
            logger.error("Database health check failed", error=str(e))
        
        # Check Redis connectivity
        redis_status = "unknown"
        try:
            from src.services.redis import get_redis_client
            redis_client = await get_redis_client()
            redis_health = await redis_client.health_check()
            redis_status = redis_health["status"]
        except Exception as e:
            redis_status = "unhealthy"
            logger.error("Redis health check failed", error=str(e))
        
        # Check Stripe connectivity
        stripe_status = "unknown"
        try:
            from src.services.stripe import get_stripe_client
            stripe_client = get_stripe_client()
            stripe_health = await stripe_client.health_check()
            stripe_status = stripe_health["status"]
        except Exception as e:
            stripe_status = "unhealthy"
            logger.error("Stripe health check failed", error=str(e))
        
        # Check Plaid connectivity
        plaid_status = "unknown"
        try:
            from src.services.plaid import get_plaid_client
            plaid_client = get_plaid_client()
            plaid_health = await plaid_client.health_check()
            plaid_status = plaid_health["status"]
        except Exception as e:
            plaid_status = "unhealthy"
            logger.error("Plaid health check failed", error=str(e))
        
        # Check Auth0 connectivity
        auth0_status = "unknown"
        try:
            import httpx
            from jose import jwk
            async with httpx.AsyncClient() as client:
                response = await client.get(settings.auth0_jwks_url, timeout=5.0)
                if response.status_code == 200:
                    jwks_data = response.json()
                    if "keys" in jwks_data and len(jwks_data["keys"]) > 0:
                        auth0_status = "healthy"
                    else:
                        auth0_status = "unhealthy"
                else:
                    auth0_status = "unhealthy"
        except Exception as e:
            auth0_status = "unhealthy"
            logger.error("Auth0 health check failed", error=str(e))
        
        return {
            "status": "healthy",
            "service": "faithful-finances-api",
            "version": settings.VERSION,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "dependencies": {
                "database": database_status,
                "redis": redis_status,
                "auth0": auth0_status,
                "plaid": plaid_status,
                "stripe": stripe_status
            }
        }
    
    # API Routes
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
    app.include_router(users_router, prefix="/api/v1/users", tags=["Users"])
    app.include_router(accounts_router, prefix="/api/v1/accounts", tags=["Accounts"])
    app.include_router(transactions_router, prefix="/api/v1/transactions", tags=["Transactions"])
    app.include_router(budgets_router, prefix="/api/v1/budgets", tags=["Budgets"])
    app.include_router(goals_router, prefix="/api/v1/goals", tags=["Goals"])
    app.include_router(tithing_router, prefix="/api/v1/tithing", tags=["Tithing"])
    app.include_router(families_router, prefix="/api/v1/families", tags=["Families"])
    app.include_router(subscriptions_router, prefix="/api/v1/subscriptions", tags=["Subscriptions"])
    app.include_router(plaid_router, prefix="/api/v1/plaid", tags=["Plaid"])
    app.include_router(webhooks_router, prefix="/webhooks", tags=["Webhooks"])
    app.include_router(performance_router, prefix="/api/v1", tags=["Performance Monitoring"])
    
    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
    )
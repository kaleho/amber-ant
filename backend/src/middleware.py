"""Custom middleware for the FastAPI application."""
import time
import uuid
from typing import Callable, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
import structlog

from src.tenant.context import set_tenant_context, get_tenant_context, TenantContext
from src.tenant.resolver import get_tenant_resolver
from src.exceptions import TenantNotFoundError, AuthenticationError

logger = structlog.get_logger(__name__)


class TenantContextMiddleware(BaseHTTPMiddleware):
    """Middleware to resolve and set tenant context for each request."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and set tenant context."""
        
        # Skip tenant resolution for health checks and docs
        if request.url.path in ["/health", "/health/detailed", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Skip tenant resolution for auth endpoints that don't require it
        if request.url.path.startswith("/api/v1/auth/") and request.url.path not in [
            "/api/v1/auth/me", "/api/v1/auth/refresh"
        ]:
            return await call_next(request)
        
        tenant_resolver = get_tenant_resolver()
        
        try:
            # Resolve tenant context from request
            tenant_context = await tenant_resolver.resolve_tenant(request)
            
            if not tenant_context:
                logger.warning("No tenant context resolved", path=request.url.path)
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "tenant_required",
                        "message": "Tenant context is required for this request"
                    }
                )
            
            # Set tenant context for the request
            set_tenant_context(tenant_context)
            
            logger.debug(
                "Tenant context set",
                tenant_id=tenant_context.tenant_id,
                tenant_slug=tenant_context.tenant_slug,
                path=request.url.path
            )
            
            response = await call_next(request)
            return response
            
        except TenantNotFoundError as e:
            logger.warning("Tenant not found during resolution", tenant_id=e.tenant_id)
            return JSONResponse(
                status_code=404,
                content={
                    "error": "tenant_not_found",
                    "message": "The specified tenant was not found",
                    "tenant_id": e.tenant_id
                }
            )
        except AuthenticationError as e:
            logger.warning("Authentication failed during tenant resolution", error=str(e))
            return JSONResponse(
                status_code=401,
                content={
                    "error": "authentication_failed",
                    "message": "Authentication required for tenant access"
                }
            )
        except Exception as e:
            logger.error("Error resolving tenant context", error=str(e), exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "error": "tenant_resolution_failed",
                    "message": "Failed to resolve tenant context"
                }
            )


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging with structured logging."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response details."""
        
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Get tenant context if available
        tenant_context = None
        try:
            tenant_context = get_tenant_context()
        except:
            pass  # Tenant context might not be set yet
        
        # Log request
        start_time = time.time()
        
        logger.info(
            "Request started",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            query_params=str(request.query_params) if request.query_params else None,
            tenant_id=tenant_context.tenant_id if tenant_context else None,
            user_agent=request.headers.get("user-agent"),
            client_ip=request.client.host if request.client else None,
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            logger.info(
                "Request completed",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=round(duration * 1000, 2),
                tenant_id=tenant_context.tenant_id if tenant_context else None,
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            
            logger.error(
                "Request failed",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                duration_ms=round(duration * 1000, 2),
                error=str(e),
                tenant_id=tenant_context.tenant_id if tenant_context else None,
                exc_info=True,
            )
            
            raise


class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for adding security headers and basic protection."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers and basic protections."""
        
        # Check for suspicious activity before processing
        await self._detect_suspicious_activity(request)
        
        # Process request
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Add HSTS header for HTTPS (only in production)
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Add Content Security Policy for API responses
        if request.url.path.startswith("/api/"):
            response.headers["Content-Security-Policy"] = "default-src 'none'"
        
        return response
    
    async def _detect_suspicious_activity(self, request: Request):
        """Detect and log suspicious activity patterns."""
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")
        path = str(request.url.path).lower()
        
        suspicious_patterns = []
        
        # Check for suspicious paths
        suspicious_paths = [
            '/admin', '/wp-admin', '/phpunit', '/.env', '/config',
            '/backup', '/test', '/debug', '/console'
        ]
        
        if any(suspicious_path in path for suspicious_path in suspicious_paths):
            suspicious_patterns.append("suspicious_path")
        
        # Check for suspicious user agents
        suspicious_agents = ['sqlmap', 'nmap', 'nikto', 'gobuster', 'dirb', 'burp', 'zap']
        if any(agent in user_agent.lower() for agent in suspicious_agents):
            suspicious_patterns.append("suspicious_user_agent")
        
        # Check for potential injection attempts in query params
        query_string = str(request.url.query).lower()
        injection_patterns = ['union select', 'drop table', '<script', 'javascript:', '../']
        if any(pattern in query_string for pattern in injection_patterns):
            suspicious_patterns.append("potential_injection")
        
        # Log suspicious activity
        if suspicious_patterns:
            try:
                from src.security.monitoring import log_suspicious_activity
                import asyncio
                asyncio.create_task(log_suspicious_activity(
                    client_ip=client_ip,
                    user_agent=user_agent,
                    path=path,
                    method=request.method,
                    patterns=suspicious_patterns,
                    details={
                        'query_string': str(request.url.query)[:500],
                        'headers': dict(request.headers)
                    }
                ))
            except ImportError:
                pass
            
            logger.warning(
                "Suspicious activity detected",
                client_ip=client_ip,
                path=path,
                patterns=suspicious_patterns,
                user_agent=user_agent[:100]
            )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware with Redis backend."""
    
    def __init__(self, app, calls: int = 100, period: int = 3600):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.redis_client = None
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting based on tenant and user."""
        
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/health/detailed"]:
            return await call_next(request)
        
        try:
            # Get Redis client if not initialized
            if not self.redis_client:
                from src.services.redis import get_redis_client
                self.redis_client = await get_redis_client()
            
            # Create rate limit key based on client IP and path
            client_ip = request.client.host if request.client else "unknown"
            rate_key = f"rate_limit:{client_ip}:{request.url.path}"
            
            # Check current count
            current_count = await self.redis_client.get(rate_key)
            
            if current_count and int(current_count) >= self.calls:
                logger.warning(f"Rate limit exceeded for {client_ip} on {request.url.path}")
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "rate_limit_exceeded",
                        "message": f"Rate limit exceeded. Max {self.calls} requests per {self.period} seconds."
                    },
                    headers={"Retry-After": str(self.period)}
                )
            
            # Increment counter
            if current_count:
                await self.redis_client.incr(rate_key)
            else:
                await self.redis_client.setex(rate_key, self.period, 1)
            
        except Exception as e:
            # If Redis fails, allow request but log error
            logger.warning(f"Rate limiting failed: {e}")
        
        return await call_next(request)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting application metrics."""
    
    def __init__(self, app):
        super().__init__(app)
        self.redis_client = None
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Collect request metrics."""
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Store metrics in Redis (fire and forget)
            await self._record_metrics(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration=duration,
                success=True
            )
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Record error metrics
            await self._record_metrics(
                method=request.method,
                path=request.url.path,
                status_code=500,
                duration=duration,
                success=False,
                error=str(e)
            )
            
            raise
    
    async def _record_metrics(self, method: str, path: str, status_code: int, 
                            duration: float, success: bool, error: str = None):
        """Record metrics to Redis."""
        try:
            if not self.redis_client:
                from src.services.redis import get_redis_client
                self.redis_client = await get_redis_client()
            
            # Record request count
            count_key = f"metrics:requests:{method}:{path}:{status_code}"
            await self.redis_client.incr(count_key)
            await self.redis_client.expire(count_key, 3600)  # 1 hour expiry
            
            # Record duration histogram (simplified)
            duration_key = f"metrics:duration:{method}:{path}"
            await self.redis_client.lpush(duration_key, duration)
            await self.redis_client.ltrim(duration_key, 0, 999)  # Keep last 1000
            await self.redis_client.expire(duration_key, 3600)
            
            # Record error if present
            if not success and error:
                error_key = f"metrics:errors:{method}:{path}"
                await self.redis_client.incr(error_key)
                await self.redis_client.expire(error_key, 3600)
            
        except Exception as e:
            # Metrics collection should not fail the request
            logger.debug(f"Metrics collection failed: {e}")
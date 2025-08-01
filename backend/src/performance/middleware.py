"""
Performance monitoring middleware for FastAPI.

This middleware automatically tracks request performance metrics
and integrates with the performance monitoring system.
"""

import time
import logging
from typing import Callable, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .metrics import global_metrics, RequestTimer
from ..tenant.context import get_current_tenant
from ..auth.context import get_current_user

logger = logging.getLogger(__name__)


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically track request performance."""
    
    def __init__(self, app: ASGIApp, 
                 enabled: bool = True,
                 track_user_metrics: bool = True,
                 track_tenant_metrics: bool = True,
                 exclude_paths: Optional[list] = None):
        super().__init__(app)
        self.enabled = enabled
        self.track_user_metrics = track_user_metrics
        self.track_tenant_metrics = track_tenant_metrics
        self.exclude_paths = exclude_paths or [
            "/health",
            "/metrics", 
            "/favicon.ico",
            "/robots.txt"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and track performance metrics."""
        if not self.enabled:
            return await call_next(request)
        
        # Skip excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        # Get context information
        tenant_id = None
        user_id = None
        
        try:
            if self.track_tenant_metrics:
                tenant = get_current_tenant()
                tenant_id = tenant.id if tenant else None
        except:
            pass
        
        try:
            if self.track_user_metrics:
                user = get_current_user()
                user_id = user.get("sub") if user else None
        except:
            pass
        
        # Track request performance
        with RequestTimer(
            metrics=global_metrics,
            path=request.url.path,
            method=request.method,
            tenant_id=tenant_id,
            user_id=user_id
        ) as timer:
            try:
                response = await call_next(request)
                
                # Add performance headers to response
                response.headers["X-Response-Time"] = f"{timer.duration_ms:.2f}ms"
                if timer.query_count > 0:
                    response.headers["X-Database-Queries"] = str(timer.query_count)
                    response.headers["X-Database-Time"] = f"{timer.query_time:.2f}ms"
                
                return response
                
            except Exception as e:
                # Log performance data even for failed requests
                logger.error(
                    f"Request failed: {request.method} {request.url.path}",
                    extra={
                        "method": request.method,
                        "path": request.url.path,
                        "tenant_id": tenant_id,
                        "user_id": user_id,
                        "error": str(e)
                    }
                )
                raise


class DatabaseQueryMiddleware:
    """Middleware to track database query performance per request."""
    
    def __init__(self):
        self.active_timers = {}
    
    def start_request_tracking(self, request_id: str, timer: RequestTimer):
        """Start tracking database queries for a request."""
        self.active_timers[request_id] = timer
    
    def add_query_time(self, request_id: str, duration_ms: float):
        """Add query time to the active request timer."""
        if request_id in self.active_timers:
            self.active_timers[request_id].add_query_metrics(1, duration_ms)
    
    def end_request_tracking(self, request_id: str):
        """Stop tracking database queries for a request."""
        self.active_timers.pop(request_id, None)


# Global database query middleware instance
db_query_middleware = DatabaseQueryMiddleware()


class MetricsCollectionMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting custom performance metrics."""
    
    def __init__(self, app: ASGIApp, collect_detailed_metrics: bool = False):
        super().__init__(app)
        self.collect_detailed_metrics = collect_detailed_metrics
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Collect detailed performance metrics."""
        start_time = time.perf_counter()
        
        # Collect request details
        request_size = int(request.headers.get("content-length", 0))
        user_agent = request.headers.get("user-agent", "")
        
        # Process request
        response = await call_next(request)
        
        # Calculate metrics
        duration_ms = (time.perf_counter() - start_time) * 1000
        response_size = int(response.headers.get("content-length", 0))
        
        # Log detailed metrics if enabled
        if self.collect_detailed_metrics:
            logger.info(
                "Detailed request metrics",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                    "status_code": response.status_code,
                    "request_size_bytes": request_size,
                    "response_size_bytes": response_size,
                    "user_agent": user_agent[:100],  # Truncate long user agents
                    "client_ip": self._get_client_ip(request)
                }
            )
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"


class SlowRequestLogger(BaseHTTPMiddleware):
    """Middleware to log slow requests for analysis."""
    
    def __init__(self, app: ASGIApp, 
                 slow_threshold_ms: float = 1000.0,
                 very_slow_threshold_ms: float = 5000.0):
        super().__init__(app)
        self.slow_threshold_ms = slow_threshold_ms
        self.very_slow_threshold_ms = very_slow_threshold_ms
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log slow requests with detailed information."""
        start_time = time.perf_counter()
        
        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            # Log slow requests
            if duration_ms > self.slow_threshold_ms:
                severity = "warning" if duration_ms < self.very_slow_threshold_ms else "error"
                
                log_data = {
                    "slow_request": True,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                    "status_code": response.status_code,
                    "query_params": dict(request.query_params),
                    "user_agent": request.headers.get("user-agent", "")[:100],
                    "client_ip": self._get_client_ip(request)
                }
                
                if severity == "error":
                    logger.error("Very slow request detected", extra=log_data)
                else:
                    logger.warning("Slow request detected", extra=log_data)
            
            return response
            
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "Request failed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                    "error": str(e),
                    "client_ip": self._get_client_ip(request)
                }
            )
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"


class HealthCheckMiddleware(BaseHTTPMiddleware):
    """Middleware to handle health checks efficiently."""
    
    def __init__(self, app: ASGIApp, health_check_paths: Optional[list] = None):
        super().__init__(app)
        self.health_check_paths = health_check_paths or ["/health", "/healthz", "/ping"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle health checks with minimal overhead."""
        # Quick health check response to avoid performance tracking overhead
        if request.url.path in self.health_check_paths and request.method == "GET":
            return Response(
                content='{"status": "healthy"}',
                media_type="application/json",
                status_code=200,
                headers={"Cache-Control": "no-cache"}
            )
        
        return await call_next(request)
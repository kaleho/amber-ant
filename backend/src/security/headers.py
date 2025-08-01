"""Enhanced security headers for production deployment."""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, RedirectResponse
from typing import Callable
import structlog

from src.config import settings

logger = structlog.get_logger(__name__)


class EnhancedSecurityMiddleware(BaseHTTPMiddleware):
    """Enhanced security middleware with comprehensive security headers."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add comprehensive security headers to all responses."""
        
        # Process request
        response = await call_next(request)
        
        # Core security headers
        security_headers = {
            # Prevent MIME type sniffing
            "X-Content-Type-Options": "nosniff",
            
            # Prevent clickjacking
            "X-Frame-Options": "DENY",
            
            # Enable XSS protection (legacy browsers)
            "X-XSS-Protection": "1; mode=block",
            
            # Control referrer information
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Limit dangerous APIs
            "Permissions-Policy": "geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=(), gyroscope=(), accelerometer=()",
            
            # Cross-Origin policies
            "Cross-Origin-Embedder-Policy": "require-corp",
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Resource-Policy": "cross-origin",
            
            # Server identification
            "Server": f"{settings.PROJECT_NAME}/{settings.VERSION}",
            
            # Cache control for sensitive content
            "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0"
        }
        
        # HTTPS Strict Transport Security
        if request.url.scheme == "https" or settings.ENVIRONMENT == "production":
            security_headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        
        # Content Security Policy - tailored by content type
        csp_policy = self._get_csp_policy(request, response)
        if csp_policy:
            security_headers["Content-Security-Policy"] = csp_policy
        
        # Apply all security headers
        for header, value in security_headers.items():
            response.headers[header] = value
        
        # Remove potentially sensitive headers
        sensitive_headers = ["Server", "X-Powered-By", "X-AspNet-Version"]
        for header in sensitive_headers:
            if header in response.headers and header != "Server":  # Keep our custom server header
                del response.headers[header]
        
        return response
    
    def _get_csp_policy(self, request: Request, response: Response) -> str:
        """Generate appropriate Content Security Policy based on content type."""
        
        # API endpoints - very restrictive
        if request.url.path.startswith("/api/"):
            return "default-src 'none'; frame-ancestors 'none';"
        
        # Documentation endpoints - allow minimal resources
        elif request.url.path in ["/docs", "/redoc"]:
            return (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self'; "
                "frame-ancestors 'none';"
            )
        
        # Health endpoints - minimal policy
        elif request.url.path.startswith("/health"):
            return "default-src 'none'; frame-ancestors 'none';"
        
        # Default restrictive policy
        else:
            return (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self';"
            )


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce HTTPS in production."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Redirect HTTP requests to HTTPS in production."""
        
        # Skip redirect for health checks and local development
        if (request.url.path in ["/health", "/health/detailed"] or 
            settings.ENVIRONMENT == "development"):
            return await call_next(request)
        
        # Enforce HTTPS in production
        if (settings.ENVIRONMENT == "production" and 
            request.url.scheme != "https"):
            
            # Check for X-Forwarded-Proto header (load balancer)
            forwarded_proto = request.headers.get("X-Forwarded-Proto")
            if forwarded_proto != "https":
                https_url = request.url.replace(scheme="https")
                logger.info(
                    "Redirecting HTTP to HTTPS",
                    original_url=str(request.url),
                    redirect_url=str(https_url)
                )
                return RedirectResponse(url=str(https_url), status_code=301)
        
        return await call_next(request)


class SecurityValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for additional security validations."""
    
    def __init__(self, app):
        super().__init__(app)
        self.suspicious_user_agents = [
            "sqlmap", "nikto", "nmap", "masscan", "zap", "burp",
            "dirb", "gobuster", "wfuzz", "curl/7.0", "python-requests"
        ]
        self.max_request_size = 50 * 1024 * 1024  # 50MB
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Perform security validations on incoming requests."""
        
        # Check request size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_request_size:
            logger.warning(
                "Request size exceeded limit",
                content_length=content_length,
                max_size=self.max_request_size,
                path=request.url.path
            )
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=413,
                content={"error": "request_too_large", "message": "Request size exceeds limit"}
            )
        
        # Check for suspicious user agents
        user_agent = request.headers.get("user-agent", "").lower()
        if any(suspicious in user_agent for suspicious in self.suspicious_user_agents):
            logger.warning(
                "Suspicious user agent detected",
                user_agent=user_agent,
                path=request.url.path,
                client_ip=request.client.host if request.client else None
            )
            
            # Log security event
            from src.security.monitoring import security_monitor, SecurityEventType, RiskLevel
            await security_monitor.log_security_event(
                event_type=SecurityEventType.SUSPICIOUS_USER_AGENT,
                risk_level=RiskLevel.MEDIUM,
                ip_address=request.client.host if request.client else None,
                user_agent=user_agent,
                endpoint=request.url.path,
                method=request.method
            )
        
        # Validate Host header to prevent Host header injection
        host = request.headers.get("host")
        if host and not self._is_valid_host(host):
            logger.warning(
                "Invalid Host header",
                host=host,
                path=request.url.path
            )
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=400,
                content={"error": "invalid_host", "message": "Invalid Host header"}
            )
        
        return await call_next(request)
    
    def _is_valid_host(self, host: str) -> bool:
        """Validate Host header against allowed hosts."""
        # Remove port if present
        host_without_port = host.split(':')[0]
        
        # Define allowed hosts
        allowed_hosts = [
            "localhost",
            "127.0.0.1",
            "faithfulfinances.com",
            "api.faithfulfinances.com",
            settings.HOST if settings.HOST != "0.0.0.0" else None
        ]
        
        # Filter out None values
        allowed_hosts = [h for h in allowed_hosts if h]
        
        return host_without_port in allowed_hosts or host_without_port.endswith(".faithfulfinances.com")
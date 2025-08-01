"""Application configuration management."""
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings for multi-tenant architecture."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    # Application
    PROJECT_NAME: str = "Faithful Finances API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str
    ENCRYPTION_KEY: str
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = False
    
    # Auth0
    AUTH0_DOMAIN: str
    AUTH0_AUDIENCE: str
    AUTH0_CLIENT_ID: Optional[str] = None
    AUTH0_CLIENT_SECRET: Optional[str] = None
    
    # Global Database (Tenant Registry)
    GLOBAL_DATABASE_URL: str
    GLOBAL_AUTH_TOKEN: str
    DATABASE_ECHO: bool = False
    
    # Tenant Resolution
    DEFAULT_TENANT_RESOLVER: str = "composite"
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
    
    # Plaid Configuration
    PLAID_CLIENT_ID: str
    PLAID_SECRET: str
    PLAID_ENV: str = "sandbox"
    PLAID_PRODUCTS: str = "transactions,accounts,identity"
    PLAID_COUNTRY_CODES: str = "US"
    
    # Stripe Configuration
    STRIPE_SECRET_KEY: str
    STRIPE_PUBLISHABLE_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # Monitoring
    SENTRY_DSN: Optional[str] = None
    PROMETHEUS_METRICS_ENABLED: bool = True
    
    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    SMTP_USE_TLS: bool = True
    SMTP_USE_SSL: bool = False
    EMAIL_FROM_ADDRESS: str = "noreply@faithfulfinances.com"
    EMAIL_FROM_NAME: str = "Faithful Finances"
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # Security Configuration
    ENFORCE_HTTPS: bool = False
    SECURITY_HEADERS_ENABLED: bool = True
    CSP_ENABLED: bool = True
    HSTS_MAX_AGE: int = 31536000
    
    # Input Validation
    MAX_JSON_DEPTH: int = 10
    MAX_JSON_KEYS: int = 100
    MAX_STRING_LENGTH: int = 10000
    
    # Security Monitoring
    SECURITY_MONITORING_ENABLED: bool = True
    SECURITY_EVENT_RETENTION_DAYS: int = 90
    SUSPICIOUS_ACTIVITY_THRESHOLD: int = 5
    
    # Password Security
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_NUMBERS: bool = True
    PASSWORD_REQUIRE_SYMBOLS: bool = False
    
    # Session Security
    SESSION_TIMEOUT_MINUTES: int = 480  # 8 hours
    FAILED_LOGIN_ATTEMPTS_LIMIT: int = 5
    ACCOUNT_LOCKOUT_DURATION_MINUTES: int = 30
    
    # File Storage
    STORAGE_PROVIDER: str = "local"
    STORAGE_PATH: str = "./uploads"
    
    # Background Tasks
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # API Documentation
    DOCS_URL: Optional[str] = "/docs"
    REDOC_URL: Optional[str] = "/redoc"
    OPENAPI_URL: Optional[str] = "/openapi.json"
    
    @property
    def auth0_issuer(self) -> str:
        """Get Auth0 issuer URL."""
        return f"https://{self.AUTH0_DOMAIN}/"
    
    @property
    def auth0_jwks_url(self) -> str:
        """Get Auth0 JWKS URL."""
        return f"https://{self.AUTH0_DOMAIN}/.well-known/jwks.json"
    
    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from string."""
        if isinstance(self.CORS_ALLOW_ORIGINS, str):
            return [origin.strip() for origin in self.CORS_ALLOW_ORIGINS.split(",")]
        return self.CORS_ALLOW_ORIGINS
    
    @property
    def plaid_products_list(self) -> List[str]:
        """Parse Plaid products from string."""
        return [product.strip() for product in self.PLAID_PRODUCTS.split(",")]
    
    @property
    def plaid_country_codes_list(self) -> List[str]:
        """Parse Plaid country codes from string."""
        return [code.strip() for code in self.PLAID_COUNTRY_CODES.split(",")]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.ENVIRONMENT == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.ENVIRONMENT == "development"
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing mode."""
        return self.ENVIRONMENT == "testing"
    
    def get_security_config(self) -> dict:
        """Get security configuration dictionary."""
        return {
            "enforce_https": self.ENFORCE_HTTPS,
            "security_headers_enabled": self.SECURITY_HEADERS_ENABLED,
            "csp_enabled": self.CSP_ENABLED,
            "hsts_max_age": self.HSTS_MAX_AGE,
            "max_json_depth": self.MAX_JSON_DEPTH,
            "max_json_keys": self.MAX_JSON_KEYS,
            "max_string_length": self.MAX_STRING_LENGTH,
            "security_monitoring_enabled": self.SECURITY_MONITORING_ENABLED,
            "security_event_retention_days": self.SECURITY_EVENT_RETENTION_DAYS,
            "suspicious_activity_threshold": self.SUSPICIOUS_ACTIVITY_THRESHOLD
        }
    
    def validate_security_configuration(self) -> List[str]:
        """Validate security configuration and return warnings."""
        warnings = []
        
        # Check for weak configurations in production
        if self.is_production:
            if not self.ENFORCE_HTTPS:
                warnings.append("HTTPS enforcement should be enabled in production")
            
            if self.DEBUG:
                warnings.append("Debug mode should be disabled in production")
            
            if "*" in str(self.CORS_ALLOW_ORIGINS):
                warnings.append("CORS origins should be restricted in production")
            
            if len(self.SECRET_KEY) < 32:
                warnings.append("SECRET_KEY should be at least 32 characters long")
            
            if len(self.ENCRYPTION_KEY) < 32:
                warnings.append("ENCRYPTION_KEY should be at least 32 characters long")
        
        # Check for missing required configurations
        if not self.SECRET_KEY:
            warnings.append("SECRET_KEY is required")
        
        if not self.ENCRYPTION_KEY:
            warnings.append("ENCRYPTION_KEY is required")
        
        if not self.GLOBAL_DATABASE_URL:
            warnings.append("GLOBAL_DATABASE_URL is required")
        
        # Security monitoring checks
        if not self.SECURITY_MONITORING_ENABLED:
            warnings.append("Security monitoring should be enabled for better threat detection")
        
        if self.FAILED_LOGIN_ATTEMPTS_LIMIT > 10:
            warnings.append("FAILED_LOGIN_ATTEMPTS_LIMIT is quite high, consider lowering it")
        
        if self.SESSION_TIMEOUT_MINUTES > 1440:  # 24 hours
            warnings.append("SESSION_TIMEOUT_MINUTES is very long, consider shortening it")
        
        return warnings


# Global settings instance
settings = Settings()

# Validate security configuration on startup
import logging
security_warnings = settings.validate_security_configuration()
if security_warnings:
    logger = logging.getLogger(__name__)
    logger.warning("Security configuration warnings detected:")
    for warning in security_warnings:
        logger.warning(f"  - {warning}")
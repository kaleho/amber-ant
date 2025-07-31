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
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    SMTP_USE_TLS: bool = True
    
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


# Global settings instance
settings = Settings()
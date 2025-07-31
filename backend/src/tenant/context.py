"""Tenant context management system."""
from contextvars import ContextVar
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class TenantContext:
    """Tenant context information."""
    tenant_id: str
    tenant_slug: str
    database_url: str
    auth_token: str
    plan: str = "basic"
    is_active: bool = True
    features: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.features is None:
            self.features = []
        if self.metadata is None:
            self.metadata = {}

    @property
    def is_premium(self) -> bool:
        """Check if tenant has premium plan."""
        return self.plan in ["premium_individual", "premium_family"]

    @property
    def is_family_plan(self) -> bool:
        """Check if tenant has family plan."""
        return self.plan == "premium_family"

    def has_feature(self, feature: str) -> bool:
        """Check if tenant has specific feature."""
        return feature in self.features


# Global tenant context variable
_tenant_context: ContextVar[Optional[TenantContext]] = ContextVar(
    'tenant_context', 
    default=None
)


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
        from src.exceptions import TenantNotFoundError
        raise TenantNotFoundError("No tenant context available")
    return context


def clear_tenant_context() -> None:
    """Clear tenant context."""
    _tenant_context.set(None)


def with_tenant_context(context: TenantContext):
    """Context manager for setting tenant context."""
    class TenantContextManager:
        def __enter__(self):
            set_tenant_context(context)
            return context
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            clear_tenant_context()
    
    return TenantContextManager()
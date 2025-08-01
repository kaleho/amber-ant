"""Redis-based caching service with tenant isolation."""

import json
import pickle
from typing import Any, Optional, Dict, List, Union, Callable
from datetime import datetime, timedelta
import hashlib
import asyncio

import structlog

from .client import RedisClient, get_redis_client
from src.exceptions import RedisError

logger = structlog.get_logger(__name__)


class CacheService:
    """Redis-based caching service with tenant isolation and advanced features."""
    
    def __init__(self, redis_client: Optional[RedisClient] = None, default_ttl: int = 3600):
        self.redis_client = redis_client
        self.default_ttl = default_ttl
        self.namespace_separator = ":"
    
    async def _get_client(self) -> RedisClient:
        """Get Redis client instance."""
        if self.redis_client is None:
            self.redis_client = await get_redis_client()
        return self.redis_client
    
    def _make_key(self, tenant_id: str, key: str, namespace: str = "cache") -> str:
        """Create namespaced cache key with tenant isolation."""
        return f"{namespace}{self.namespace_separator}{tenant_id}{self.namespace_separator}{key}"
    
    def _hash_key(self, key: str) -> str:
        """Create SHA-256 hash of key for very long keys."""
        if len(key) > 200:  # Redis key length limit is ~512MB, but best practice is <200 chars
            return hashlib.sha256(key.encode()).hexdigest()
        return key
    
    def _serialize_value(self, value: Any, use_pickle: bool = True) -> str:
        """Serialize value for storage."""
        if isinstance(value, (str, int, float, bool)) and not use_pickle:
            return json.dumps(value)
        else:
            # Use pickle for complex objects (more efficient but Python-specific)
            import base64
            pickled = pickle.dumps(value)
            return base64.b64encode(pickled).decode('utf-8')
    
    def _deserialize_value(self, value: str, use_pickle: bool = True) -> Any:
        """Deserialize value from storage."""
        if not use_pickle:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                # Fallback to pickle if JSON fails
                pass
        
        # Use pickle
        import base64
        try:
            pickled = base64.b64decode(value.encode('utf-8'))
            return pickle.loads(pickled)
        except Exception as e:
            logger.error("Failed to deserialize cached value", error=str(e))
            raise RedisError(f"Cache deserialization failed: {str(e)}")
    
    async def set(
        self,
        tenant_id: str,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        namespace: str = "cache",
        use_pickle: bool = True
    ) -> bool:
        """Set cached value with tenant isolation."""
        try:
            client = await self._get_client()
            cache_key = self._make_key(tenant_id, self._hash_key(key), namespace)
            serialized_value = self._serialize_value(value, use_pickle)
            
            ttl = ttl or self.default_ttl
            success = await client.set(cache_key, serialized_value, ttl=ttl)
            
            if success:
                logger.debug("Cache set successful", tenant_id=tenant_id, key=key, ttl=ttl)
            
            return success
            
        except Exception as e:
            logger.error("Cache set failed", tenant_id=tenant_id, key=key, error=str(e))
            # Don't raise exception - cache failures should be graceful
            return False
    
    async def get(
        self,
        tenant_id: str,
        key: str,
        namespace: str = "cache",
        use_pickle: bool = True
    ) -> Optional[Any]:
        """Get cached value with tenant isolation."""
        try:
            client = await self._get_client()
            cache_key = self._make_key(tenant_id, self._hash_key(key), namespace)
            
            serialized_value = await client.get(cache_key)
            if serialized_value is None:
                return None
            
            value = self._deserialize_value(serialized_value, use_pickle)
            logger.debug("Cache hit", tenant_id=tenant_id, key=key)
            return value
            
        except Exception as e:
            logger.error("Cache get failed", tenant_id=tenant_id, key=key, error=str(e))
            # Return None on cache failures - let the application fetch fresh data
            return None
    
    async def delete(self, tenant_id: str, key: str, namespace: str = "cache") -> bool:
        """Delete cached value."""
        try:
            client = await self._get_client()
            cache_key = self._make_key(tenant_id, self._hash_key(key), namespace)
            
            deleted_count = await client.delete(cache_key)
            success = deleted_count > 0
            
            if success:
                logger.debug("Cache delete successful", tenant_id=tenant_id, key=key)
            
            return success
            
        except Exception as e:
            logger.error("Cache delete failed", tenant_id=tenant_id, key=key, error=str(e))
            return False
    
    async def exists(self, tenant_id: str, key: str, namespace: str = "cache") -> bool:
        """Check if cached value exists."""
        try:
            client = await self._get_client()
            cache_key = self._make_key(tenant_id, self._hash_key(key), namespace)
            
            exists_count = await client.exists(cache_key)
            return exists_count > 0
            
        except Exception as e:
            logger.error("Cache exists check failed", tenant_id=tenant_id, key=key, error=str(e))
            return False
    
    async def get_or_set(
        self,
        tenant_id: str,
        key: str,
        factory: Callable[[], Any],
        ttl: Optional[int] = None,
        namespace: str = "cache",
        use_pickle: bool = True
    ) -> Any:
        """Get cached value or set it using factory function."""
        # Try to get from cache first
        value = await self.get(tenant_id, key, namespace, use_pickle)
        if value is not None:
            return value
        
        # Generate new value
        try:
            if asyncio.iscoroutinefunction(factory):
                new_value = await factory()
            else:
                new_value = factory()
            
            # Cache the new value
            await self.set(tenant_id, key, new_value, ttl, namespace, use_pickle)
            return new_value
            
        except Exception as e:
            logger.error("Cache factory function failed", tenant_id=tenant_id, key=key, error=str(e))
            raise
    
    async def mget(
        self,
        tenant_id: str,
        keys: List[str],
        namespace: str = "cache",
        use_pickle: bool = True
    ) -> Dict[str, Any]:
        """Get multiple cached values."""
        try:
            client = await self._get_client()
            
            # Create cache keys
            cache_keys = [self._make_key(tenant_id, self._hash_key(key), namespace) for key in keys]
            
            # Get all values at once
            values = []
            for cache_key in cache_keys:
                value = await client.get(cache_key)
                values.append(value)
            
            # Deserialize and map back to original keys
            result = {}
            for i, (original_key, serialized_value) in enumerate(zip(keys, values)):
                if serialized_value is not None:
                    result[original_key] = self._deserialize_value(serialized_value, use_pickle)
            
            logger.debug("Cache mget successful", tenant_id=tenant_id, keys_requested=len(keys), keys_found=len(result))
            return result
            
        except Exception as e:
            logger.error("Cache mget failed", tenant_id=tenant_id, keys=keys, error=str(e))
            return {}
    
    async def mset(
        self,
        tenant_id: str,
        key_value_pairs: Dict[str, Any],
        ttl: Optional[int] = None,
        namespace: str = "cache",
        use_pickle: bool = True
    ) -> int:
        """Set multiple cached values."""
        try:
            client = await self._get_client()
            ttl = ttl or self.default_ttl
            
            success_count = 0
            for key, value in key_value_pairs.items():
                cache_key = self._make_key(tenant_id, self._hash_key(key), namespace)
                serialized_value = self._serialize_value(value, use_pickle)
                
                if await client.set(cache_key, serialized_value, ttl=ttl):
                    success_count += 1
            
            logger.debug("Cache mset completed", tenant_id=tenant_id, total=len(key_value_pairs), successful=success_count)
            return success_count
            
        except Exception as e:
            logger.error("Cache mset failed", tenant_id=tenant_id, error=str(e))
            return 0
    
    async def increment(
        self,
        tenant_id: str,
        key: str,
        amount: int = 1,
        namespace: str = "counters",
        ttl: Optional[int] = None
    ) -> int:
        """Increment a counter with tenant isolation."""
        try:
            client = await self._get_client()
            cache_key = self._make_key(tenant_id, self._hash_key(key), namespace)
            
            result = await client.incr(cache_key, amount)
            
            # Set TTL on first increment
            if result == amount and ttl:
                await client.expire(cache_key, ttl)
            
            logger.debug("Cache increment successful", tenant_id=tenant_id, key=key, result=result)
            return result
            
        except Exception as e:
            logger.error("Cache increment failed", tenant_id=tenant_id, key=key, error=str(e))
            raise RedisError(f"Cache increment failed: {str(e)}")
    
    async def clear_namespace(self, tenant_id: str, namespace: str = "cache") -> int:
        """Clear all keys in a namespace for a tenant."""
        try:
            client = await self._get_client()
            pattern = self._make_key(tenant_id, "*", namespace)
            
            keys = await client.keys(pattern)
            if not keys:
                return 0
            
            deleted_count = await client.delete(*keys)
            logger.info("Cache namespace cleared", tenant_id=tenant_id, namespace=namespace, deleted=deleted_count)
            return deleted_count
            
        except Exception as e:
            logger.error("Cache namespace clear failed", tenant_id=tenant_id, namespace=namespace, error=str(e))
            return 0
    
    async def clear_tenant(self, tenant_id: str) -> int:
        """Clear all cached data for a tenant."""
        try:
            client = await self._get_client()
            pattern = f"*{self.namespace_separator}{tenant_id}{self.namespace_separator}*"
            
            keys = await client.keys(pattern)
            if not keys:
                return 0
            
            deleted_count = await client.delete(*keys)
            logger.info("Tenant cache cleared", tenant_id=tenant_id, deleted=deleted_count)
            return deleted_count
            
        except Exception as e:
            logger.error("Tenant cache clear failed", tenant_id=tenant_id, error=str(e))
            return 0
    
    async def get_stats(self, tenant_id: str) -> Dict[str, Any]:
        """Get cache statistics for a tenant."""
        try:
            client = await self._get_client()
            pattern = f"*{self.namespace_separator}{tenant_id}{self.namespace_separator}*"
            
            keys = await client.keys(pattern)
            
            stats = {
                "tenant_id": tenant_id,
                "total_keys": len(keys),
                "namespaces": {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Group by namespace
            for key in keys:
                parts = key.split(self.namespace_separator)
                if len(parts) >= 3:
                    namespace = parts[0]
                    if namespace not in stats["namespaces"]:
                        stats["namespaces"][namespace] = 0
                    stats["namespaces"][namespace] += 1
            
            return stats
            
        except Exception as e:
            logger.error("Cache stats failed", tenant_id=tenant_id, error=str(e))
            return {"tenant_id": tenant_id, "error": str(e)}


# Helper functions for common caching patterns
def cache_key_for_user(user_id: str, operation: str) -> str:
    """Generate cache key for user-specific operations."""
    return f"user:{user_id}:{operation}"


def cache_key_for_account(account_id: str, operation: str) -> str:
    """Generate cache key for account-specific operations."""
    return f"account:{account_id}:{operation}"


def cache_key_for_transaction(transaction_id: str, operation: str) -> str:
    """Generate cache key for transaction-specific operations."""
    return f"transaction:{transaction_id}:{operation}"


def cache_key_for_budget(budget_id: str, operation: str) -> str:
    """Generate cache key for budget-specific operations."""
    return f"budget:{budget_id}:{operation}"


# Decorators for caching
def cached(
    ttl: int = 3600,
    namespace: str = "cache",
    key_generator: Optional[Callable] = None,
    use_pickle: bool = True
):
    """Decorator for caching function results."""
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            # Extract tenant_id from function context (should be first arg)
            if not args:
                raise ValueError("Cached function must have tenant_id as first argument")
            
            tenant_id = str(args[0])
            
            # Generate cache key
            if key_generator:
                cache_key = key_generator(*args, **kwargs)
            else:
                # Default key generation
                func_name = func.__name__
                args_hash = hashlib.md5(str(args[1:] + tuple(sorted(kwargs.items()))).encode()).hexdigest()[:8]
                cache_key = f"{func_name}:{args_hash}"
            
            # Try to get from cache
            cache_service = CacheService()
            cached_result = await cache_service.get(tenant_id, cache_key, namespace, use_pickle)
            
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            await cache_service.set(tenant_id, cache_key, result, ttl, namespace, use_pickle)
            return result
        
        return wrapper
    return decorator
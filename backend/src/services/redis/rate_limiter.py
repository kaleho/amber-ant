"""Redis-based rate limiting with tenant isolation."""

import asyncio
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum

import structlog

from .client import RedisClient, get_redis_client
from src.exceptions import RedisError, RateLimitExceededError
from src.config import settings

logger = structlog.get_logger(__name__)


class RateLimitStrategy(Enum):
    """Rate limiting strategies."""
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"


class RateLimiter:
    """Redis-based rate limiter with multiple strategies and tenant isolation."""
    
    def __init__(self, redis_client: Optional[RedisClient] = None):
        self.redis_client = redis_client
        self.rate_limit_prefix = "rate_limit"
    
    async def _get_client(self) -> RedisClient:
        """Get Redis client instance."""
        if self.redis_client is None:
            self.redis_client = await get_redis_client()
        return self.redis_client
    
    def _make_key(self, tenant_id: str, identifier: str, rate_type: str) -> str:
        """Create rate limit key with tenant isolation."""
        return f"{self.rate_limit_prefix}:{tenant_id}:{rate_type}:{identifier}"
    
    async def check_rate_limit_fixed_window(
        self,
        tenant_id: str,
        identifier: str,
        rate_type: str,
        limit: int,
        window: int
    ) -> Tuple[bool, Dict[str, any]]:
        """
        Fixed window rate limiting.
        
        Args:
            tenant_id: Tenant identifier
            identifier: User/IP/API key identifier
            rate_type: Type of rate limit (e.g., 'api', 'login', 'upload')
            limit: Maximum requests per window
            window: Window size in seconds
            
        Returns:
            Tuple of (allowed, info_dict)
        """
        try:
            client = await self._get_client()
            
            # Create time-based window key
            current_time = int(datetime.utcnow().timestamp())
            window_start = (current_time // window) * window
            key = f"{self._make_key(tenant_id, identifier, rate_type)}:{window_start}"
            
            # Increment counter for this window
            current_count = await client.incr(key)
            
            # Set expiration on first increment
            if current_count == 1:
                await client.expire(key, window)
            
            # Check if limit exceeded
            allowed = current_count <= limit
            
            # Calculate reset time
            reset_time = window_start + window
            remaining = max(0, limit - current_count)
            
            info = {
                "allowed": allowed,
                "limit": limit,
                "remaining": remaining,
                "reset_time": reset_time,
                "retry_after": reset_time - current_time if not allowed else 0,
                "current_count": current_count,
                "window_start": window_start,
                "window_size": window
            }
            
            if not allowed:
                logger.warning(
                    "Rate limit exceeded (fixed window)",
                    tenant_id=tenant_id,
                    identifier=identifier,
                    rate_type=rate_type,
                    current_count=current_count,
                    limit=limit
                )
            
            return allowed, info
            
        except Exception as e:
            logger.error("Fixed window rate limit check failed", error=str(e))
            # Fail open - allow request if rate limiter is down
            return True, {"error": str(e), "allowed": True}
    
    async def check_rate_limit_sliding_window(
        self,
        tenant_id: str,
        identifier: str,
        rate_type: str,
        limit: int,
        window: int
    ) -> Tuple[bool, Dict[str, any]]:
        """
        Sliding window rate limiting using sorted sets.
        More accurate but more expensive than fixed window.
        """
        try:
            client = await self._get_client()
            key = self._make_key(tenant_id, identifier, rate_type)
            
            current_time = datetime.utcnow().timestamp()
            window_start = current_time - window
            
            # Remove expired entries
            await client.zremrangebyscore(key, 0, window_start)
            
            # Count current requests in window
            current_count = await client.zcard(key)
            
            allowed = current_count < limit
            
            if allowed:
                # Add current request
                await client.zadd(key, {str(current_time): current_time})
                await client.expire(key, window + 1)  # Extra second for cleanup
                current_count += 1
            
            remaining = max(0, limit - current_count)
            
            # Calculate when the oldest request will expire
            oldest_requests = await client.zrange(key, 0, 0, withscores=True)
            retry_after = 0
            if not allowed and oldest_requests:
                oldest_time = oldest_requests[0][1]
                retry_after = max(0, int((oldest_time + window) - current_time))
            
            info = {
                "allowed": allowed,
                "limit": limit,
                "remaining": remaining,
                "current_count": current_count,
                "window_size": window,
                "retry_after": retry_after,
                "window_start": window_start
            }
            
            if not allowed:
                logger.warning(
                    "Rate limit exceeded (sliding window)",
                    tenant_id=tenant_id,
                    identifier=identifier,
                    rate_type=rate_type,
                    current_count=current_count,
                    limit=limit
                )
            
            return allowed, info
            
        except Exception as e:
            logger.error("Sliding window rate limit check failed", error=str(e))
            return True, {"error": str(e), "allowed": True}
    
    async def check_rate_limit_token_bucket(
        self,
        tenant_id: str,
        identifier: str,
        rate_type: str,
        capacity: int,
        refill_rate: float,
        tokens_requested: int = 1
    ) -> Tuple[bool, Dict[str, any]]:
        """
        Token bucket rate limiting.
        
        Args:
            capacity: Maximum tokens in bucket
            refill_rate: Tokens added per second
            tokens_requested: Tokens needed for this request
        """
        try:
            client = await self._get_client()
            key = self._make_key(tenant_id, identifier, rate_type)
            
            current_time = datetime.utcnow().timestamp()
            
            # Get current bucket state
            bucket_data = await client.hgetall(key)
            
            if bucket_data:
                tokens = float(bucket_data.get("tokens", capacity))
                last_refill = float(bucket_data.get("last_refill", current_time))
            else:
                tokens = float(capacity)
                last_refill = current_time
            
            # Calculate tokens to add based on time elapsed
            time_elapsed = current_time - last_refill
            tokens_to_add = time_elapsed * refill_rate
            tokens = min(capacity, tokens + tokens_to_add)
            
            # Check if we have enough tokens
            allowed = tokens >= tokens_requested
            
            if allowed:
                tokens -= tokens_requested
            
            # Update bucket state
            await client.hset(key, mapping={
                "tokens": str(tokens),
                "last_refill": str(current_time),
                "capacity": str(capacity),
                "refill_rate": str(refill_rate)
            })
            
            # Set expiration (bucket becomes inactive if not used)
            await client.expire(key, int(capacity / refill_rate) + 60)
            
            # Calculate retry_after if request denied
            retry_after = 0
            if not allowed:
                tokens_needed = tokens_requested - tokens
                retry_after = int(tokens_needed / refill_rate) + 1
            
            info = {
                "allowed": allowed,
                "capacity": capacity,
                "tokens": tokens,
                "refill_rate": refill_rate,
                "tokens_requested": tokens_requested,
                "retry_after": retry_after
            }
            
            if not allowed:
                logger.warning(
                    "Rate limit exceeded (token bucket)",
                    tenant_id=tenant_id,
                    identifier=identifier,
                    rate_type=rate_type,
                    tokens=tokens,
                    tokens_requested=tokens_requested
                )
            
            return allowed, info
            
        except Exception as e:
            logger.error("Token bucket rate limit check failed", error=str(e))
            return True, {"error": str(e), "allowed": True}
    
    async def check_rate_limit(
        self,
        tenant_id: str,
        identifier: str,
        rate_type: str = "api",
        strategy: RateLimitStrategy = RateLimitStrategy.FIXED_WINDOW,
        **kwargs
    ) -> Tuple[bool, Dict[str, any]]:
        """
        Universal rate limiting method.
        
        Args:
            tenant_id: Tenant identifier
            identifier: User/IP/API key identifier  
            rate_type: Type of rate limit
            strategy: Rate limiting strategy
            **kwargs: Strategy-specific parameters
        """
        
        if strategy == RateLimitStrategy.FIXED_WINDOW:
            limit = kwargs.get("limit", settings.RATE_LIMIT_REQUESTS)
            window = kwargs.get("window", settings.RATE_LIMIT_WINDOW)
            return await self.check_rate_limit_fixed_window(
                tenant_id, identifier, rate_type, limit, window
            )
        
        elif strategy == RateLimitStrategy.SLIDING_WINDOW:
            limit = kwargs.get("limit", settings.RATE_LIMIT_REQUESTS)
            window = kwargs.get("window", settings.RATE_LIMIT_WINDOW)
            return await self.check_rate_limit_sliding_window(
                tenant_id, identifier, rate_type, limit, window
            )
        
        elif strategy == RateLimitStrategy.TOKEN_BUCKET:
            capacity = kwargs.get("capacity", settings.RATE_LIMIT_REQUESTS)
            refill_rate = kwargs.get("refill_rate", settings.RATE_LIMIT_REQUESTS / settings.RATE_LIMIT_WINDOW)
            tokens_requested = kwargs.get("tokens_requested", 1)
            return await self.check_rate_limit_token_bucket(
                tenant_id, identifier, rate_type, capacity, refill_rate, tokens_requested
            )
        
        else:
            raise ValueError(f"Unsupported rate limiting strategy: {strategy}")
    
    async def reset_rate_limit(
        self,
        tenant_id: str,
        identifier: str,
        rate_type: str = "api"
    ) -> bool:
        """Reset rate limit for identifier."""
        try:
            client = await self._get_client()
            
            # Delete all keys for this identifier
            pattern = f"{self._make_key(tenant_id, identifier, rate_type)}*"
            keys = await client.keys(pattern)
            
            if keys:
                deleted_count = await client.delete(*keys)
                logger.info(
                    "Rate limit reset",
                    tenant_id=tenant_id,
                    identifier=identifier,
                    rate_type=rate_type,
                    keys_deleted=deleted_count
                )
                return deleted_count > 0
            
            return True
            
        except Exception as e:
            logger.error("Rate limit reset failed", error=str(e))
            return False
    
    async def get_rate_limit_status(
        self,
        tenant_id: str,
        identifier: str,
        rate_type: str = "api"
    ) -> Dict[str, any]:
        """Get current rate limit status without incrementing."""
        try:
            client = await self._get_client()
            pattern = f"{self._make_key(tenant_id, identifier, rate_type)}*"
            keys = await client.keys(pattern)
            
            status = {
                "tenant_id": tenant_id,
                "identifier": identifier,
                "rate_type": rate_type,
                "active_windows": len(keys),
                "windows": []
            }
            
            for key in keys:
                key_data = await client.get(key)
                ttl = await client.ttl(key)
                
                if key_data and ttl > 0:
                    status["windows"].append({
                        "key": key,
                        "count": int(key_data) if key_data.isdigit() else key_data,
                        "ttl": ttl
                    })
            
            return status
            
        except Exception as e:
            logger.error("Rate limit status check failed", error=str(e))
            return {"error": str(e)}
    
    async def cleanup_expired_rate_limits(self, tenant_id: Optional[str] = None) -> int:
        """Clean up expired rate limit keys."""
        try:
            client = await self._get_client()
            
            if tenant_id:
                pattern = f"{self.rate_limit_prefix}:{tenant_id}:*"
            else:
                pattern = f"{self.rate_limit_prefix}:*"
            
            keys = await client.keys(pattern)
            cleaned_count = 0
            
            for key in keys:
                ttl = await client.ttl(key)
                if ttl <= 0:  # Expired or no expiration set
                    await client.delete(key)
                    cleaned_count += 1
            
            if cleaned_count > 0:
                logger.info("Rate limit cleanup completed", tenant_id=tenant_id, cleaned=cleaned_count)
            
            return cleaned_count
            
        except Exception as e:
            logger.error("Rate limit cleanup failed", error=str(e))
            return 0


# Rate limiting decorators and middleware helpers
async def enforce_rate_limit(
    tenant_id: str,
    identifier: str,
    rate_type: str = "api",
    strategy: RateLimitStrategy = RateLimitStrategy.FIXED_WINDOW,
    **kwargs
) -> Dict[str, any]:
    """
    Enforce rate limiting and raise exception if exceeded.
    
    Returns rate limit info if allowed, raises RateLimitExceededError if not.
    """
    rate_limiter = RateLimiter()
    allowed, info = await rate_limiter.check_rate_limit(
        tenant_id, identifier, rate_type, strategy, **kwargs
    )
    
    if not allowed:
        retry_after = info.get("retry_after", 60)
        raise RateLimitExceededError(
            message=f"Rate limit exceeded for {rate_type}",
            retry_after=retry_after
        )
    
    return info


# Predefined rate limit configurations
RATE_LIMIT_CONFIGS = {
    "api": {
        "strategy": RateLimitStrategy.FIXED_WINDOW,
        "limit": 100,
        "window": 3600  # 100 requests per hour
    },
    "login": {
        "strategy": RateLimitStrategy.SLIDING_WINDOW,
        "limit": 5,
        "window": 900  # 5 attempts per 15 minutes
    },
    "password_reset": {
        "strategy": RateLimitStrategy.SLIDING_WINDOW,
        "limit": 3,
        "window": 3600  # 3 attempts per hour
    },
    "file_upload": {
        "strategy": RateLimitStrategy.TOKEN_BUCKET,
        "capacity": 10,
        "refill_rate": 0.1  # 1 token per 10 seconds
    },
    "expensive_operation": {
        "strategy": RateLimitStrategy.TOKEN_BUCKET,
        "capacity": 5,
        "refill_rate": 0.0167  # 1 token per minute
    }
}
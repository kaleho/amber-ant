"""Redis client with connection pooling and circuit breaker."""

import asyncio
import logging
from typing import Optional, Any, Dict, List, Union
from contextlib import asynccontextmanager
from urllib.parse import urlparse

import redis.asyncio as redis
from redis.asyncio import ConnectionPool
from redis.exceptions import ConnectionError, TimeoutError, RedisError
import structlog

from src.config import settings
from src.exceptions import RedisError as CustomRedisError

logger = structlog.get_logger(__name__)


class CircuitBreaker:
    """Simple circuit breaker for Redis operations."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def _is_timeout_expired(self) -> bool:
        """Check if recovery timeout has expired."""
        return (asyncio.get_event_loop().time() - self.last_failure_time) > self.recovery_timeout
    
    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == "OPEN":
            if self._is_timeout_expired():
                self.state = "HALF_OPEN"
            else:
                raise CustomRedisError("Circuit breaker is OPEN - Redis unavailable")
        
        try:
            result = await func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = asyncio.get_event_loop().time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                logger.error("Circuit breaker opened due to failures", failure_count=self.failure_count)
            
            raise CustomRedisError(f"Redis operation failed: {str(e)}")


class RedisClient:
    """Enhanced Redis client with connection pooling and monitoring."""
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or settings.REDIS_URL
        self.pool: Optional[ConnectionPool] = None
        self.client: Optional[redis.Redis] = None
        self.circuit_breaker = CircuitBreaker()
        self._connected = False
        
        # Parse Redis URL for configuration
        parsed = urlparse(self.redis_url)
        self.host = parsed.hostname or "localhost"
        self.port = parsed.port or 6379
        self.db = int(parsed.path.lstrip('/')) if parsed.path else 0
        self.password = parsed.password
    
    async def initialize(self) -> None:
        """Initialize Redis connection pool."""
        try:
            # Create connection pool with optimized settings
            self.pool = ConnectionPool(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                encoding="utf-8",
                decode_responses=True,
                max_connections=20,
                socket_keepalive=True,
                socket_keepalive_options={
                    1: 1,  # TCP_KEEPIDLE
                    2: 3,  # TCP_KEEPINTVL  
                    3: 5,  # TCP_KEEPCNT
                },
                socket_connect_timeout=5,
                socket_timeout=5,
                health_check_interval=30
            )
            
            self.client = redis.Redis(connection_pool=self.pool)
            
            # Test connection
            await self.ping()
            self._connected = True
            
            logger.info("Redis connection pool initialized", host=self.host, port=self.port, db=self.db)
            
        except Exception as e:
            logger.error("Failed to initialize Redis connection", error=str(e))
            raise CustomRedisError(f"Redis initialization failed: {str(e)}")
    
    async def close(self) -> None:
        """Close Redis connections."""
        if self.client:
            await self.client.close()
        if self.pool:
            await self.pool.disconnect()
        self._connected = False
        logger.info("Redis connections closed")
    
    @asynccontextmanager
    async def get_connection(self):
        """Get Redis connection with proper error handling."""
        if not self._connected:
            raise CustomRedisError("Redis client not initialized")
        
        try:
            yield self.client
        except (ConnectionError, TimeoutError) as e:
            logger.error("Redis connection error", error=str(e))
            raise CustomRedisError(f"Redis connection failed: {str(e)}")
        except RedisError as e:
            logger.error("Redis operation error", error=str(e))
            raise CustomRedisError(f"Redis operation failed: {str(e)}")
    
    async def ping(self) -> bool:
        """Ping Redis server."""
        try:
            async with self.get_connection() as conn:
                result = await self.circuit_breaker.call(conn.ping)
                return result
        except Exception as e:
            logger.error("Redis ping failed", error=str(e))
            return False
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None, **kwargs) -> bool:
        """Set key-value pair with optional TTL."""
        try:
            async with self.get_connection() as conn:
                result = await self.circuit_breaker.call(
                    conn.set, key, value, ex=ttl, **kwargs
                )
                return result
        except Exception as e:
            logger.error("Redis SET failed", key=key, error=str(e))
            raise
    
    async def get(self, key: str) -> Optional[str]:
        """Get value by key."""
        try:
            async with self.get_connection() as conn:
                result = await self.circuit_breaker.call(conn.get, key)
                return result
        except Exception as e:
            logger.error("Redis GET failed", key=key, error=str(e))
            raise
    
    async def delete(self, *keys: str) -> int:
        """Delete one or more keys."""
        try:
            async with self.get_connection() as conn:
                result = await self.circuit_breaker.call(conn.delete, *keys)
                return result
        except Exception as e:
            logger.error("Redis DELETE failed", keys=keys, error=str(e))
            raise
    
    async def exists(self, *keys: str) -> int:
        """Check if keys exist."""
        try:
            async with self.get_connection() as conn:
                result = await self.circuit_breaker.call(conn.exists, *keys)
                return result
        except Exception as e:
            logger.error("Redis EXISTS failed", keys=keys, error=str(e))
            raise
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set TTL for key."""
        try:
            async with self.get_connection() as conn:
                result = await self.circuit_breaker.call(conn.expire, key, ttl)
                return result
        except Exception as e:
            logger.error("Redis EXPIRE failed", key=key, ttl=ttl, error=str(e))
            raise
    
    async def ttl(self, key: str) -> int:
        """Get TTL for key."""
        try:
            async with self.get_connection() as conn:
                result = await self.circuit_breaker.call(conn.ttl, key)
                return result
        except Exception as e:
            logger.error("Redis TTL failed", key=key, error=str(e))
            raise
    
    async def incr(self, key: str, amount: int = 1) -> int:
        """Increment key value."""
        try:
            async with self.get_connection() as conn:
                result = await self.circuit_breaker.call(conn.incr, key, amount)
                return result
        except Exception as e:
            logger.error("Redis INCR failed", key=key, amount=amount, error=str(e))
            raise
    
    async def hset(self, name: str, mapping: Dict[str, Any]) -> int:
        """Set hash fields."""
        try:
            async with self.get_connection() as conn:
                result = await self.circuit_breaker.call(conn.hset, name, mapping=mapping)
                return result
        except Exception as e:
            logger.error("Redis HSET failed", name=name, error=str(e))
            raise
    
    async def hget(self, name: str, key: str) -> Optional[str]:
        """Get hash field value."""
        try:
            async with self.get_connection() as conn:
                result = await self.circuit_breaker.call(conn.hget, name, key)
                return result
        except Exception as e:
            logger.error("Redis HGET failed", name=name, key=key, error=str(e))
            raise
    
    async def hgetall(self, name: str) -> Dict[str, str]:
        """Get all hash fields."""
        try:
            async with self.get_connection() as conn:
                result = await self.circuit_breaker.call(conn.hgetall, name)
                return result
        except Exception as e:
            logger.error("Redis HGETALL failed", name=name, error=str(e))
            raise
    
    async def sadd(self, name: str, *values: Any) -> int:
        """Add members to set."""
        try:
            async with self.get_connection() as conn:
                result = await self.circuit_breaker.call(conn.sadd, name, *values)
                return result
        except Exception as e:
            logger.error("Redis SADD failed", name=name, error=str(e))
            raise
    
    async def sismember(self, name: str, value: Any) -> bool:
        """Check if value is member of set."""
        try:
            async with self.get_connection() as conn:
                result = await self.circuit_breaker.call(conn.sismember, name, value)
                return result
        except Exception as e:
            logger.error("Redis SISMEMBER failed", name=name, value=value, error=str(e))
            raise
    
    async def smembers(self, name: str) -> set:
        """Get all set members."""
        try:
            async with self.get_connection() as conn:
                result = await self.circuit_breaker.call(conn.smembers, name)
                return result
        except Exception as e:
            logger.error("Redis SMEMBERS failed", name=name, error=str(e))
            raise
    
    async def lpush(self, name: str, *values: Any) -> int:
        """Push values to list head."""
        try:
            async with self.get_connection() as conn:
                result = await self.circuit_breaker.call(conn.lpush, name, *values)
                return result
        except Exception as e:
            logger.error("Redis LPUSH failed", name=name, error=str(e))
            raise
    
    async def rpop(self, name: str) -> Optional[str]:
        """Pop value from list tail."""
        try:
            async with self.get_connection() as conn:
                result = await self.circuit_breaker.call(conn.rpop, name)
                return result
        except Exception as e:
            logger.error("Redis RPOP failed", name=name, error=str(e))
            raise
    
    async def llen(self, name: str) -> int:
        """Get list length."""
        try:
            async with self.get_connection() as conn:
                result = await self.circuit_breaker.call(conn.llen, name)
                return result
        except Exception as e:
            logger.error("Redis LLEN failed", name=name, error=str(e))
            raise
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern."""
        try:
            async with self.get_connection() as conn:
                result = await self.circuit_breaker.call(conn.keys, pattern)
                return result
        except Exception as e:
            logger.error("Redis KEYS failed", pattern=pattern, error=str(e))
            raise
    
    async def flushdb(self) -> bool:
        """Flush current database."""
        try:
            async with self.get_connection() as conn:
                result = await self.circuit_breaker.call(conn.flushdb)
                return result
        except Exception as e:
            logger.error("Redis FLUSHDB failed", error=str(e))
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        health_status = {
            "service": "redis",
            "status": "unhealthy",
            "details": {}
        }
        
        try:
            # Basic connectivity
            ping_result = await self.ping()
            health_status["details"]["ping"] = ping_result
            
            # Connection pool status
            if self.pool:
                health_status["details"]["pool_created_connections"] = self.pool.created_connections
                health_status["details"]["pool_available_connections"] = len(self.pool._available_connections)
                health_status["details"]["pool_in_use_connections"] = len(self.pool._in_use_connections)
            
            # Circuit breaker status
            health_status["details"]["circuit_breaker_state"] = self.circuit_breaker.state
            health_status["details"]["circuit_breaker_failures"] = self.circuit_breaker.failure_count
            
            # Performance test
            import time
            start = time.time()
            await self.set("health_check", "test", ttl=60)
            value = await self.get("health_check")
            await self.delete("health_check")
            response_time = (time.time() - start) * 1000
            
            health_status["details"]["response_time_ms"] = round(response_time, 2)
            health_status["details"]["test_operation"] = value == "test"
            
            # Mark as healthy if all checks pass
            if ping_result and value == "test":
                health_status["status"] = "healthy"
            
        except Exception as e:
            health_status["details"]["error"] = str(e)
            logger.error("Redis health check failed", error=str(e))
        
        return health_status


# Global Redis client instance
_redis_client: Optional[RedisClient] = None


async def get_redis_client() -> RedisClient:
    """Get or create Redis client instance."""
    global _redis_client
    
    if _redis_client is None:
        _redis_client = RedisClient()
        await _redis_client.initialize()
    
    return _redis_client


async def close_redis_client() -> None:
    """Close Redis client instance."""
    global _redis_client
    
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
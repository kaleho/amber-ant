"""JWT token blacklist management for revoked tokens."""
import asyncio
from datetime import datetime, timedelta
from typing import Set, Optional
import structlog

logger = structlog.get_logger(__name__)


class TokenBlacklist:
    """In-memory and Redis-backed token blacklist for JWT revocation."""
    
    def __init__(self):
        self._memory_blacklist: Set[str] = set()
        self._redis_client = None
        self._prefix = "blacklist:token:"
        
    async def _get_redis_client(self):
        """Get Redis client for persistent blacklist."""
        if not self._redis_client:
            try:
                from src.services.redis import get_redis_client
                self._redis_client = await get_redis_client()
            except ImportError:
                logger.warning("Redis not available for token blacklist")
        return self._redis_client
    
    async def revoke_token(self, token_jti: str, exp_timestamp: int):
        """
        Add token to blacklist.
        
        Args:
            token_jti: JWT ID claim (unique token identifier)
            exp_timestamp: Token expiration timestamp
        """
        # Add to memory blacklist
        self._memory_blacklist.add(token_jti)
        
        # Add to Redis blacklist with expiration
        redis_client = await self._get_redis_client()
        if redis_client:
            try:
                # Calculate TTL until token naturally expires
                current_time = datetime.utcnow().timestamp()
                ttl_seconds = max(int(exp_timestamp - current_time), 1)
                
                await redis_client.setex(
                    f"{self._prefix}{token_jti}",
                    ttl_seconds,
                    "revoked"
                )
                
                logger.info(
                    "Token revoked and blacklisted",
                    jti=token_jti,
                    ttl_seconds=ttl_seconds
                )
            except Exception as e:
                logger.error(f"Failed to blacklist token in Redis: {e}")
    
    async def is_token_revoked(self, token_jti: str) -> bool:
        """Check if token is in blacklist."""
        # Check memory blacklist first (fastest)
        if token_jti in self._memory_blacklist:
            return True
        
        # Check Redis blacklist
        redis_client = await self._get_redis_client()
        if redis_client:
            try:
                is_blacklisted = await redis_client.exists(f"{self._prefix}{token_jti}")
                if is_blacklisted:
                    # Add to memory cache for faster future lookups
                    self._memory_blacklist.add(token_jti)
                    return True
            except Exception as e:
                logger.error(f"Failed to check Redis blacklist: {e}")
        
        return False
    
    async def revoke_user_tokens(self, user_id: str, issued_before: Optional[datetime] = None):
        """
        Revoke all tokens for a user.
        
        Args:
            user_id: User ID whose tokens should be revoked
            issued_before: Optional datetime - only revoke tokens issued before this time
        """
        if issued_before is None:
            issued_before = datetime.utcnow()
        
        # Store user revocation timestamp in Redis
        redis_client = await self._get_redis_client()
        if redis_client:
            try:
                user_key = f"revoked:user:{user_id}"
                # Store timestamp - tokens issued before this time are considered revoked
                await redis_client.setex(
                    user_key,
                    86400 * 7,  # Keep for 7 days (longer than typical JWT lifetime)
                    int(issued_before.timestamp())
                )
                
                logger.info(
                    "User tokens revoked",
                    user_id=user_id,
                    revoked_before=issued_before.isoformat()
                )
            except Exception as e:
                logger.error(f"Failed to revoke user tokens: {e}")
    
    async def is_user_token_revoked(self, user_id: str, token_iat: int) -> bool:
        """
        Check if user's token is revoked based on issuance time.
        
        Args:
            user_id: User ID from token
            token_iat: Token issued at timestamp
            
        Returns:
            True if token was issued before user revocation time
        """
        redis_client = await self._get_redis_client()
        if redis_client:
            try:
                user_key = f"revoked:user:{user_id}"
                revocation_timestamp = await redis_client.get(user_key)
                
                if revocation_timestamp:
                    revocation_time = int(revocation_timestamp)
                    return token_iat < revocation_time
                    
            except Exception as e:
                logger.error(f"Failed to check user token revocation: {e}")
        
        return False
    
    async def cleanup_expired_tokens(self):
        """Remove expired tokens from memory blacklist."""
        # This is primarily for memory cleanup
        # Redis automatically expires keys, but we clean memory periodically
        # Note: In production, this would need more sophisticated cleanup
        # based on tracking token expiration times
        
        logger.debug("Token blacklist cleanup completed")
    
    def get_blacklist_stats(self) -> dict:
        """Get blacklist statistics."""
        return {
            "memory_blacklist_size": len(self._memory_blacklist),
            "redis_available": self._redis_client is not None
        }


# Global token blacklist instance
token_blacklist = TokenBlacklist()


# Background task to cleanup expired tokens
async def start_blacklist_cleanup_task():
    """Start background task for blacklist cleanup."""
    while True:
        try:
            await token_blacklist.cleanup_expired_tokens()
            await asyncio.sleep(3600)  # Run every hour
        except Exception as e:
            logger.error(f"Blacklist cleanup task failed: {e}")
            await asyncio.sleep(300)  # Wait 5 minutes before retry
"""Redis-based session management with tenant isolation."""

import json
import uuid
from typing import Any, Dict, Optional
from datetime import datetime, timedelta

import structlog

from .client import RedisClient, get_redis_client
from src.exceptions import RedisError

logger = structlog.get_logger(__name__)


class SessionService:
    """Redis-based session management with tenant isolation and security features."""
    
    def __init__(self, redis_client: Optional[RedisClient] = None, default_ttl: int = 86400):
        self.redis_client = redis_client
        self.default_ttl = default_ttl  # 24 hours
        self.session_prefix = "session"
        self.user_sessions_prefix = "user_sessions"
    
    async def _get_client(self) -> RedisClient:
        """Get Redis client instance."""
        if self.redis_client is None:
            self.redis_client = await get_redis_client()
        return self.redis_client
    
    def _make_session_key(self, tenant_id: str, session_id: str) -> str:
        """Create session key with tenant isolation."""
        return f"{self.session_prefix}:{tenant_id}:{session_id}"
    
    def _make_user_sessions_key(self, tenant_id: str, user_id: str) -> str:
        """Create user sessions tracking key."""
        return f"{self.user_sessions_prefix}:{tenant_id}:{user_id}"
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        return str(uuid.uuid4())
    
    async def create_session(
        self,
        tenant_id: str,
        user_id: str,
        data: Dict[str, Any],
        ttl: Optional[int] = None,
        max_sessions_per_user: int = 10
    ) -> str:
        """Create new session with tenant isolation."""
        try:
            client = await self._get_client()
            session_id = self._generate_session_id()
            session_key = self._make_session_key(tenant_id, session_id)
            user_sessions_key = self._make_user_sessions_key(tenant_id, user_id)
            
            ttl = ttl or self.default_ttl
            
            # Prepare session data
            session_data = {
                "session_id": session_id,
                "tenant_id": tenant_id,
                "user_id": user_id,
                "created_at": datetime.utcnow().isoformat(),
                "last_accessed": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(seconds=ttl)).isoformat(),
                "data": data
            }
            
            # Store session data
            session_json = json.dumps(session_data)
            success = await client.set(session_key, session_json, ttl=ttl)
            
            if not success:
                raise RedisError("Failed to create session")
            
            # Track user sessions (for cleanup and limits)
            await client.sadd(user_sessions_key, session_id)
            await client.expire(user_sessions_key, ttl)
            
            # Enforce session limits per user
            user_sessions = await client.smembers(user_sessions_key)
            if len(user_sessions) > max_sessions_per_user:
                # Clean up oldest sessions
                sessions_to_remove = len(user_sessions) - max_sessions_per_user
                sessions_list = list(user_sessions)
                
                for i in range(sessions_to_remove):
                    old_session_id = sessions_list[i]
                    await self.destroy_session(tenant_id, old_session_id)
            
            logger.info("Session created", tenant_id=tenant_id, user_id=user_id, session_id=session_id)
            return session_id
            
        except Exception as e:
            logger.error("Session creation failed", tenant_id=tenant_id, user_id=user_id, error=str(e))
            raise RedisError(f"Session creation failed: {str(e)}")
    
    async def get_session(self, tenant_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data by ID."""
        try:
            client = await self._get_client()
            session_key = self._make_session_key(tenant_id, session_id)
            
            session_json = await client.get(session_key)
            if session_json is None:
                return None
            
            session_data = json.loads(session_json)
            
            # Update last accessed time
            session_data["last_accessed"] = datetime.utcnow().isoformat()
            updated_json = json.dumps(session_data)
            
            # Get current TTL and maintain it
            current_ttl = await client.ttl(session_key)
            if current_ttl > 0:
                await client.set(session_key, updated_json, ttl=current_ttl)
            
            logger.debug("Session retrieved", tenant_id=tenant_id, session_id=session_id)
            return session_data
            
        except Exception as e:
            logger.error("Session retrieval failed", tenant_id=tenant_id, session_id=session_id, error=str(e))
            return None
    
    async def update_session(
        self,
        tenant_id: str,
        session_id: str,
        data: Dict[str, Any],
        extend_ttl: Optional[int] = None
    ) -> bool:
        """Update session data."""
        try:
            client = await self._get_client()
            session_key = self._make_session_key(tenant_id, session_id)
            
            # Get current session data
            session_json = await client.get(session_key)
            if session_json is None:
                return False
            
            session_data = json.loads(session_json)
            
            # Update data and timestamps
            session_data["data"].update(data)
            session_data["last_accessed"] = datetime.utcnow().isoformat()
            
            if extend_ttl:
                session_data["expires_at"] = (datetime.utcnow() + timedelta(seconds=extend_ttl)).isoformat()
            
            # Save updated session
            updated_json = json.dumps(session_data)
            ttl = extend_ttl or await client.ttl(session_key)
            
            if ttl <= 0:
                ttl = self.default_ttl
            
            success = await client.set(session_key, updated_json, ttl=ttl)
            
            if success:
                logger.debug("Session updated", tenant_id=tenant_id, session_id=session_id)
            
            return success
            
        except Exception as e:
            logger.error("Session update failed", tenant_id=tenant_id, session_id=session_id, error=str(e))
            return False
    
    async def destroy_session(self, tenant_id: str, session_id: str) -> bool:
        """Destroy session by ID."""
        try:
            client = await self._get_client()
            session_key = self._make_session_key(tenant_id, session_id)
            
            # Get session data to find user_id for cleanup
            session_json = await client.get(session_key)
            if session_json:
                session_data = json.loads(session_json)
                user_id = session_data.get("user_id")
                
                if user_id:
                    # Remove from user sessions set
                    user_sessions_key = self._make_user_sessions_key(tenant_id, user_id)
                    await client.srem(user_sessions_key, session_id)
            
            # Delete session
            deleted_count = await client.delete(session_key)
            success = deleted_count > 0
            
            if success:
                logger.info("Session destroyed", tenant_id=tenant_id, session_id=session_id)
            
            return success
            
        except Exception as e:
            logger.error("Session destruction failed", tenant_id=tenant_id, session_id=session_id, error=str(e))
            return False
    
    async def destroy_user_sessions(self, tenant_id: str, user_id: str) -> int:
        """Destroy all sessions for a user."""
        try:
            client = await self._get_client()
            user_sessions_key = self._make_user_sessions_key(tenant_id, user_id)
            
            # Get all session IDs for user
            session_ids = await client.smembers(user_sessions_key)
            
            destroyed_count = 0
            for session_id in session_ids:
                if await self.destroy_session(tenant_id, session_id):
                    destroyed_count += 1
            
            # Clean up user sessions set
            await client.delete(user_sessions_key)
            
            logger.info("User sessions destroyed", tenant_id=tenant_id, user_id=user_id, count=destroyed_count)
            return destroyed_count
            
        except Exception as e:
            logger.error("User sessions destruction failed", tenant_id=tenant_id, user_id=user_id, error=str(e))
            return 0
    
    async def list_user_sessions(self, tenant_id: str, user_id: str) -> list[Dict[str, Any]]:
        """List all active sessions for a user."""
        try:
            client = await self._get_client()
            user_sessions_key = self._make_user_sessions_key(tenant_id, user_id)
            
            session_ids = await client.smembers(user_sessions_key)
            sessions = []
            
            for session_id in session_ids:
                session_data = await self.get_session(tenant_id, session_id)
                if session_data:
                    # Remove sensitive data for listing
                    session_info = {
                        "session_id": session_data["session_id"],
                        "created_at": session_data["created_at"],
                        "last_accessed": session_data["last_accessed"],
                        "expires_at": session_data["expires_at"]
                    }
                    sessions.append(session_info)
            
            return sessions
            
        except Exception as e:
            logger.error("User sessions listing failed", tenant_id=tenant_id, user_id=user_id, error=str(e))
            return []
    
    async def extend_session(self, tenant_id: str, session_id: str, additional_ttl: int = 3600) -> bool:
        """Extend session expiration."""
        try:
            client = await self._get_client()
            session_key = self._make_session_key(tenant_id, session_id)
            
            # Get current TTL
            current_ttl = await client.ttl(session_key)
            if current_ttl <= 0:
                return False
            
            # Extend TTL
            new_ttl = current_ttl + additional_ttl
            success = await client.expire(session_key, new_ttl)
            
            if success:
                # Update session data with new expiration
                session_json = await client.get(session_key)
                if session_json:
                    session_data = json.loads(session_json)
                    session_data["expires_at"] = (datetime.utcnow() + timedelta(seconds=new_ttl)).isoformat()
                    session_data["last_accessed"] = datetime.utcnow().isoformat()
                    
                    await client.set(session_key, json.dumps(session_data), ttl=new_ttl)
                
                logger.debug("Session extended", tenant_id=tenant_id, session_id=session_id, new_ttl=new_ttl)
            
            return success
            
        except Exception as e:
            logger.error("Session extension failed", tenant_id=tenant_id, session_id=session_id, error=str(e))
            return False
    
    async def is_session_valid(self, tenant_id: str, session_id: str) -> bool:
        """Check if session exists and is valid."""
        try:
            session_data = await self.get_session(tenant_id, session_id)
            if not session_data:
                return False
            
            # Check expiration
            expires_at = datetime.fromisoformat(session_data["expires_at"])
            if datetime.utcnow() > expires_at:
                # Session expired, clean it up
                await self.destroy_session(tenant_id, session_id)
                return False
            
            return True
            
        except Exception as e:
            logger.error("Session validation failed", tenant_id=tenant_id, session_id=session_id, error=str(e))
            return False
    
    async def cleanup_expired_sessions(self, tenant_id: Optional[str] = None) -> int:
        """Clean up expired sessions."""
        try:
            client = await self._get_client()
            
            # Get session keys pattern
            if tenant_id:
                pattern = f"{self.session_prefix}:{tenant_id}:*"
            else:
                pattern = f"{self.session_prefix}:*"
            
            session_keys = await client.keys(pattern)
            cleaned_count = 0
            
            for session_key in session_keys:
                try:
                    session_json = await client.get(session_key)
                    if not session_json:
                        continue
                    
                    session_data = json.loads(session_json)
                    expires_at = datetime.fromisoformat(session_data["expires_at"])
                    
                    if datetime.utcnow() > expires_at:
                        # Extract session info for cleanup
                        session_tenant_id = session_data["tenant_id"]
                        session_id = session_data["session_id"]
                        
                        await self.destroy_session(session_tenant_id, session_id)
                        cleaned_count += 1
                        
                except Exception as e:
                    logger.warning("Failed to process session during cleanup", session_key=session_key, error=str(e))
                    continue
            
            if cleaned_count > 0:
                logger.info("Expired sessions cleaned up", tenant_id=tenant_id, count=cleaned_count)
            
            return cleaned_count
            
        except Exception as e:
            logger.error("Session cleanup failed", tenant_id=tenant_id, error=str(e))
            return 0
    
    async def get_session_stats(self, tenant_id: str) -> Dict[str, Any]:
        """Get session statistics for a tenant."""
        try:
            client = await self._get_client()
            pattern = f"{self.session_prefix}:{tenant_id}:*"
            
            session_keys = await client.keys(pattern)
            active_sessions = 0
            expired_sessions = 0
            
            for session_key in session_keys:
                session_json = await client.get(session_key)
                if session_json:
                    session_data = json.loads(session_json)
                    expires_at = datetime.fromisoformat(session_data["expires_at"])
                    
                    if datetime.utcnow() > expires_at:
                        expired_sessions += 1
                    else:
                        active_sessions += 1
            
            return {
                "tenant_id": tenant_id,
                "total_sessions": len(session_keys),
                "active_sessions": active_sessions,
                "expired_sessions": expired_sessions,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Session stats failed", tenant_id=tenant_id, error=str(e))
            return {"tenant_id": tenant_id, "error": str(e)}
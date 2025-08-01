"""Test JWT token blacklist functionality."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import asyncio

from src.security.token_blacklist import (
    TokenBlacklist,
    token_blacklist,
    start_blacklist_cleanup_task
)


@pytest.fixture
def mock_redis():
    """Mock Redis client fixture."""
    redis_mock = AsyncMock()
    redis_mock.setex = AsyncMock()
    redis_mock.exists = AsyncMock()
    redis_mock.get = AsyncMock()
    redis_mock.delete = AsyncMock()
    return redis_mock


@pytest.fixture
def mock_logger():
    """Mock logger fixture."""
    with patch('src.security.token_blacklist.logger') as mock:
        yield mock


class TestTokenBlacklist:
    """Test cases for TokenBlacklist class."""

    def test_init(self):
        """Test TokenBlacklist initialization."""
        blacklist = TokenBlacklist()
        assert blacklist._memory_blacklist == set()
        assert blacklist._redis_client is None
        assert blacklist._prefix == "blacklist:token:"

    @pytest.mark.asyncio
    async def test_get_redis_client_success(self, mock_redis):
        """Test successful Redis client initialization."""
        with patch('src.security.token_blacklist.get_redis_client', return_value=mock_redis):
            blacklist = TokenBlacklist()
            client = await blacklist._get_redis_client()
            assert client == mock_redis
            assert blacklist._redis_client == mock_redis

    @pytest.mark.asyncio
    async def test_get_redis_client_import_error(self, mock_logger):
        """Test Redis client initialization with ImportError."""
        with patch('src.security.token_blacklist.get_redis_client', side_effect=ImportError):
            blacklist = TokenBlacklist()
            client = await blacklist._get_redis_client()
            assert client is None
            mock_logger.warning.assert_called_with("Redis not available for token blacklist")

    @pytest.mark.asyncio
    async def test_revoke_token_with_redis(self, mock_redis, mock_logger):
        """Test token revocation with Redis backend."""
        with patch('src.security.token_blacklist.get_redis_client', return_value=mock_redis):
            blacklist = TokenBlacklist()
            
            # Mock current time for consistent testing
            current_time = datetime.utcnow()
            exp_time = int((current_time + timedelta(hours=1)).timestamp())
            
            with patch('src.security.token_blacklist.datetime') as mock_datetime:
                mock_datetime.utcnow.return_value = current_time
                
                await blacklist.revoke_token("test_jti", exp_time)
                
                # Verify token added to memory blacklist
                assert "test_jti" in blacklist._memory_blacklist
                
                # Verify Redis operations
                mock_redis.setex.assert_called_once()
                call_args = mock_redis.setex.call_args
                assert call_args[0][0] == "blacklist:token:test_jti"
                assert call_args[0][2] == "revoked"
                
                # Verify logging
                mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_revoke_token_without_redis(self, mock_logger):
        """Test token revocation without Redis backend."""
        with patch('src.security.token_blacklist.get_redis_client', return_value=None):
            blacklist = TokenBlacklist()
            
            current_time = datetime.utcnow()
            exp_time = int((current_time + timedelta(hours=1)).timestamp())
            
            await blacklist.revoke_token("test_jti", exp_time)
            
            # Should still add to memory blacklist
            assert "test_jti" in blacklist._memory_blacklist

    @pytest.mark.asyncio
    async def test_revoke_token_redis_error(self, mock_redis, mock_logger):
        """Test token revocation with Redis error."""
        mock_redis.setex.side_effect = Exception("Redis connection error")
        
        with patch('src.security.token_blacklist.get_redis_client', return_value=mock_redis):
            blacklist = TokenBlacklist()
            
            current_time = datetime.utcnow()
            exp_time = int((current_time + timedelta(hours=1)).timestamp())
            
            await blacklist.revoke_token("test_jti", exp_time)
            
            # Should still add to memory blacklist
            assert "test_jti" in blacklist._memory_blacklist
            
            # Should log error
            mock_logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_is_token_revoked_memory_hit(self):
        """Test token revocation check with memory cache hit."""
        blacklist = TokenBlacklist()
        blacklist._memory_blacklist.add("revoked_token")
        
        is_revoked = await blacklist.is_token_revoked("revoked_token")
        assert is_revoked is True

    @pytest.mark.asyncio
    async def test_is_token_revoked_redis_hit(self, mock_redis):
        """Test token revocation check with Redis hit."""
        mock_redis.exists.return_value = True
        
        with patch('src.security.token_blacklist.get_redis_client', return_value=mock_redis):
            blacklist = TokenBlacklist()
            
            is_revoked = await blacklist.is_token_revoked("test_jti")
            assert is_revoked is True
            
            # Should add to memory cache
            assert "test_jti" in blacklist._memory_blacklist
            
            # Verify Redis call
            mock_redis.exists.assert_called_with("blacklist:token:test_jti")

    @pytest.mark.asyncio
    async def test_is_token_revoked_not_found(self, mock_redis):
        """Test token revocation check when token not found."""
        mock_redis.exists.return_value = False
        
        with patch('src.security.token_blacklist.get_redis_client', return_value=mock_redis):
            blacklist = TokenBlacklist()
            
            is_revoked = await blacklist.is_token_revoked("valid_token")
            assert is_revoked is False

    @pytest.mark.asyncio
    async def test_is_token_revoked_redis_error(self, mock_redis, mock_logger):
        """Test token revocation check with Redis error."""
        mock_redis.exists.side_effect = Exception("Redis connection error")
        
        with patch('src.security.token_blacklist.get_redis_client', return_value=mock_redis):
            blacklist = TokenBlacklist()
            
            is_revoked = await blacklist.is_token_revoked("test_jti")
            assert is_revoked is False
            
            # Should log error
            mock_logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_revoke_user_tokens(self, mock_redis, mock_logger):
        """Test revoking all tokens for a user."""
        with patch('src.security.token_blacklist.get_redis_client', return_value=mock_redis):
            blacklist = TokenBlacklist()
            
            revocation_time = datetime.utcnow()
            
            await blacklist.revoke_user_tokens("user123", revocation_time)
            
            # Verify Redis operations
            mock_redis.setex.assert_called_once()
            call_args = mock_redis.setex.call_args
            assert call_args[0][0] == "revoked:user:user123"
            assert call_args[0][1] == 86400 * 7  # 7 days TTL
            assert call_args[0][2] == int(revocation_time.timestamp())
            
            # Verify logging
            mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_revoke_user_tokens_default_time(self, mock_redis):
        """Test revoking user tokens with default time."""
        with patch('src.security.token_blacklist.get_redis_client', return_value=mock_redis):
            blacklist = TokenBlacklist()
            
            with patch('src.security.token_blacklist.datetime') as mock_datetime:
                current_time = datetime.utcnow()
                mock_datetime.utcnow.return_value = current_time
                
                await blacklist.revoke_user_tokens("user123")
                
                # Should use current time as default
                call_args = mock_redis.setex.call_args
                assert call_args[0][2] == int(current_time.timestamp())

    @pytest.mark.asyncio
    async def test_revoke_user_tokens_redis_error(self, mock_redis, mock_logger):
        """Test user token revocation with Redis error."""
        mock_redis.setex.side_effect = Exception("Redis connection error")
        
        with patch('src.security.token_blacklist.get_redis_client', return_value=mock_redis):
            blacklist = TokenBlacklist()
            
            await blacklist.revoke_user_tokens("user123")
            
            # Should log error
            mock_logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_is_user_token_revoked_true(self, mock_redis):
        """Test user token revocation check returning True."""
        mock_redis.get.return_value = b'1640995200'  # Mock timestamp
        
        with patch('src.security.token_blacklist.get_redis_client', return_value=mock_redis):
            blacklist = TokenBlacklist()
            
            # Token issued before revocation time
            token_iat = 1640995100  # Earlier timestamp
            is_revoked = await blacklist.is_user_token_revoked("user123", token_iat)
            assert is_revoked is True
            
            # Verify Redis call
            mock_redis.get.assert_called_with("revoked:user:user123")

    @pytest.mark.asyncio
    async def test_is_user_token_revoked_false(self, mock_redis):
        """Test user token revocation check returning False."""
        mock_redis.get.return_value = b'1640995200'  # Mock timestamp
        
        with patch('src.security.token_blacklist.get_redis_client', return_value=mock_redis):
            blacklist = TokenBlacklist()
            
            # Token issued after revocation time
            token_iat = 1640995300  # Later timestamp
            is_revoked = await blacklist.is_user_token_revoked("user123", token_iat)
            assert is_revoked is False

    @pytest.mark.asyncio
    async def test_is_user_token_revoked_no_revocation(self, mock_redis):
        """Test user token revocation check when no revocation exists."""
        mock_redis.get.return_value = None
        
        with patch('src.security.token_blacklist.get_redis_client', return_value=mock_redis):
            blacklist = TokenBlacklist()
            
            is_revoked = await blacklist.is_user_token_revoked("user123", 1640995200)
            assert is_revoked is False

    @pytest.mark.asyncio
    async def test_is_user_token_revoked_redis_error(self, mock_redis, mock_logger):
        """Test user token revocation check with Redis error."""
        mock_redis.get.side_effect = Exception("Redis connection error")
        
        with patch('src.security.token_blacklist.get_redis_client', return_value=mock_redis):
            blacklist = TokenBlacklist()
            
            is_revoked = await blacklist.is_user_token_revoked("user123", 1640995200)
            assert is_revoked is False
            
            # Should log error
            mock_logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_cleanup_expired_tokens(self, mock_logger):
        """Test cleanup of expired tokens."""
        blacklist = TokenBlacklist()
        
        await blacklist.cleanup_expired_tokens()
        
        # Should log debug message
        mock_logger.debug.assert_called_with("Token blacklist cleanup completed")

    def test_get_blacklist_stats(self):
        """Test getting blacklist statistics."""
        blacklist = TokenBlacklist()
        blacklist._memory_blacklist.add("token1")
        blacklist._memory_blacklist.add("token2")
        
        stats = blacklist.get_blacklist_stats()
        
        assert stats["memory_blacklist_size"] == 2
        assert stats["redis_available"] is False

    def test_get_blacklist_stats_with_redis(self, mock_redis):
        """Test getting blacklist statistics with Redis."""
        blacklist = TokenBlacklist()
        blacklist._redis_client = mock_redis
        
        stats = blacklist.get_blacklist_stats()
        
        assert stats["redis_available"] is True


class TestGlobalTokenBlacklist:
    """Test the global token blacklist instance."""

    def test_global_instance(self):
        """Test that global blacklist instance exists."""
        assert token_blacklist is not None
        assert isinstance(token_blacklist, TokenBlacklist)

    @pytest.mark.asyncio
    async def test_global_instance_functionality(self):
        """Test basic functionality of global instance."""
        # Should not raise exceptions
        await token_blacklist.cleanup_expired_tokens()
        stats = token_blacklist.get_blacklist_stats()
        assert "memory_blacklist_size" in stats


class TestBlacklistCleanupTask:
    """Test the background cleanup task."""

    @pytest.mark.asyncio
    async def test_cleanup_task_single_iteration(self, mock_logger):
        """Test single iteration of cleanup task."""
        with patch.object(token_blacklist, 'cleanup_expired_tokens', new_callable=AsyncMock) as mock_cleanup:
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                mock_sleep.side_effect = Exception("Stop task")  # Stop after first iteration
                
                with pytest.raises(Exception, match="Stop task"):
                    await start_blacklist_cleanup_task()
                
                # Should call cleanup once
                mock_cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_task_error_handling(self, mock_logger):
        """Test cleanup task error handling."""
        with patch.object(token_blacklist, 'cleanup_expired_tokens', new_callable=AsyncMock) as mock_cleanup:
            mock_cleanup.side_effect = Exception("Cleanup failed")
            
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                # First sleep after error (5 minutes), second sleep stops the task
                mock_sleep.side_effect = [None, Exception("Stop task")]
                
                with pytest.raises(Exception, match="Stop task"):
                    await start_blacklist_cleanup_task()
                
                # Should log error
                mock_logger.error.assert_called()
                
                # Should sleep for 5 minutes (300 seconds) after error
                assert mock_sleep.call_args_list[0][0][0] == 300


class TestTokenBlacklistIntegration:
    """Integration tests for token blacklist."""

    @pytest.mark.asyncio
    async def test_complete_token_lifecycle(self, mock_redis):
        """Test complete token lifecycle from creation to revocation."""
        with patch('src.security.token_blacklist.get_redis_client', return_value=mock_redis):
            blacklist = TokenBlacklist()
            
            token_jti = "test_token_123"
            exp_time = int((datetime.utcnow() + timedelta(hours=1)).timestamp())
            
            # Initially not revoked
            mock_redis.exists.return_value = False
            is_revoked = await blacklist.is_token_revoked(token_jti)
            assert is_revoked is False
            
            # Revoke the token
            await blacklist.revoke_token(token_jti, exp_time)
            
            # Should now be revoked (memory cache hit)
            is_revoked = await blacklist.is_token_revoked(token_jti)
            assert is_revoked is True

    @pytest.mark.asyncio
    async def test_user_token_revocation_scenario(self, mock_redis):
        """Test user token revocation scenario."""
        with patch('src.security.token_blacklist.get_redis_client', return_value=mock_redis):
            blacklist = TokenBlacklist()
            
            user_id = "user123"
            revocation_time = datetime.utcnow()
            
            # Revoke all user tokens
            await blacklist.revoke_user_tokens(user_id, revocation_time)
            
            # Mock Redis response for revocation timestamp
            mock_redis.get.return_value = str(int(revocation_time.timestamp())).encode()
            
            # Token issued before revocation should be revoked
            old_token_iat = int((revocation_time - timedelta(minutes=30)).timestamp())
            is_revoked = await blacklist.is_user_token_revoked(user_id, old_token_iat)
            assert is_revoked is True
            
            # Token issued after revocation should be valid
            new_token_iat = int((revocation_time + timedelta(minutes=30)).timestamp())
            is_revoked = await blacklist.is_user_token_revoked(user_id, new_token_iat)
            assert is_revoked is False

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, mock_redis):
        """Test concurrent blacklist operations."""
        with patch('src.security.token_blacklist.get_redis_client', return_value=mock_redis):
            blacklist = TokenBlacklist()
            
            # Create multiple concurrent operations
            tasks = []
            
            # Revoke multiple tokens concurrently
            for i in range(10):
                exp_time = int((datetime.utcnow() + timedelta(hours=1)).timestamp())
                task = asyncio.create_task(blacklist.revoke_token(f"token_{i}", exp_time))
                tasks.append(task)
            
            # Check multiple tokens concurrently
            for i in range(10, 20):
                task = asyncio.create_task(blacklist.is_token_revoked(f"token_{i}"))
                tasks.append(task)
            
            # Wait for all operations to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Should not have any exceptions
            for result in results:
                assert not isinstance(result, Exception)

    @pytest.mark.asyncio
    async def test_memory_efficiency(self):
        """Test memory efficiency with large number of tokens."""
        blacklist = TokenBlacklist()
        
        # Add many tokens to memory blacklist
        for i in range(1000):
            blacklist._memory_blacklist.add(f"token_{i}")
        
        # Memory blacklist should contain all tokens
        assert len(blacklist._memory_blacklist) == 1000
        
        # Stats should reflect memory usage
        stats = blacklist.get_blacklist_stats()
        assert stats["memory_blacklist_size"] == 1000
"""Test security monitoring system."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import asyncio

from src.security.monitoring import (
    SecurityEventMonitor,
    SecurityEventType,
    RiskLevel,
    log_auth_success,
    log_auth_failure,
    log_permission_denied,
    log_suspicious_activity,
    log_rate_limit_exceeded,
    log_request_event,
    security_monitor
)


@pytest.fixture
def mock_redis():
    """Mock Redis client fixture."""
    redis_mock = AsyncMock()
    redis_mock.hset = AsyncMock()
    redis_mock.expire = AsyncMock()
    redis_mock.incr = AsyncMock()
    redis_mock.get = AsyncMock(return_value=b'1')
    redis_mock.hgetall = AsyncMock(return_value={})
    redis_mock.keys = AsyncMock(return_value=[])
    return redis_mock


@pytest.fixture
def mock_logger():
    """Mock logger fixture."""
    with patch('src.security.monitoring.logger') as mock:
        yield mock


class TestSecurityEventMonitor:
    """Test cases for SecurityEventMonitor class."""

    @pytest.mark.asyncio
    async def test_init_with_redis(self, mock_redis):
        """Test monitor initialization with Redis."""
        with patch('src.security.monitoring.get_redis_client', return_value=mock_redis):
            monitor = SecurityEventMonitor()
            redis_client = await monitor._get_redis_client()
            assert redis_client == mock_redis

    @pytest.mark.asyncio
    async def test_init_without_redis(self):
        """Test monitor initialization without Redis."""
        with patch('src.security.monitoring.get_redis_client', side_effect=ImportError):
            monitor = SecurityEventMonitor()
            redis_client = await monitor._get_redis_client()
            assert redis_client is None

    @pytest.mark.asyncio
    async def test_log_event_basic(self, mock_redis, mock_logger):
        """Test basic event logging."""
        with patch('src.security.monitoring.get_redis_client', return_value=mock_redis):
            monitor = SecurityEventMonitor()
            
            await monitor.log_event(
                event_type=SecurityEventType.LOGIN_SUCCESS,
                user_id="user123",
                tenant_id="tenant456",
                client_ip="192.168.1.1",
                user_agent="TestAgent/1.0",
                details={"method": "password"}
            )
            
            # Verify Redis calls
            mock_redis.hset.assert_called()
            mock_redis.expire.assert_called()
            
            # Verify logging
            mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_log_event_without_redis(self, mock_logger):
        """Test event logging when Redis is unavailable."""
        with patch('src.security.monitoring.get_redis_client', return_value=None):
            monitor = SecurityEventMonitor()
            
            await monitor.log_event(
                event_type=SecurityEventType.LOGIN_FAILURE,
                client_ip="192.168.1.1"
            )
            
            # Should still log to application logger
            mock_logger.warning.assert_called()

    @pytest.mark.asyncio
    async def test_log_event_with_risk_assessment(self, mock_redis, mock_logger):
        """Test event logging with risk assessment."""
        with patch('src.security.monitoring.get_redis_client', return_value=mock_redis):
            monitor = SecurityEventMonitor()
            
            # Mock risk assessment
            with patch.object(monitor, '_assess_risk_level', return_value=RiskLevel.HIGH):
                await monitor.log_event(
                    event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
                    client_ip="192.168.1.1",
                    details={"patterns": ["sql_injection", "xss_attempt"]}
                )
                
                # High risk events should trigger alerts
                mock_logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_analyze_patterns(self, mock_redis):
        """Test security pattern analysis."""
        with patch('src.security.monitoring.get_redis_client', return_value=mock_redis):
            monitor = SecurityEventMonitor()
            
            # Mock Redis data
            mock_redis.keys.return_value = [
                b"security:event:user123:20240101:LOGIN_FAILURE",
                b"security:event:user123:20240101:LOGIN_FAILURE"
            ]
            mock_redis.hgetall.return_value = {
                b"event_type": b"LOGIN_FAILURE",
                b"timestamp": b"2024-01-01T12:00:00Z",
                b"client_ip": b"192.168.1.1"
            }
            
            patterns = await monitor.analyze_patterns(
                time_window=timedelta(hours=1),
                min_events=2
            )
            
            assert len(patterns) > 0

    @pytest.mark.asyncio
    async def test_get_security_metrics(self, mock_redis):
        """Test security metrics collection."""
        with patch('src.security.monitoring.get_redis_client', return_value=mock_redis):
            monitor = SecurityEventMonitor()
            
            # Mock Redis counters
            mock_redis.get.side_effect = [b'10', b'5', b'2', b'1', b'0']
            
            metrics = await monitor.get_security_metrics(
                time_window=timedelta(hours=24)
            )
            
            assert "total_events" in metrics
            assert "events_by_type" in metrics
            assert "risk_distribution" in metrics

    def test_assess_risk_level(self):
        """Test risk level assessment."""
        monitor = SecurityEventMonitor()
        
        # Low risk event
        risk = monitor._assess_risk_level(
            SecurityEventType.LOGIN_SUCCESS,
            client_ip="192.168.1.1",
            details={}
        )
        assert risk == RiskLevel.LOW
        
        # Medium risk event
        risk = monitor._assess_risk_level(
            SecurityEventType.LOGIN_FAILURE,
            client_ip="192.168.1.1",
            details={}
        )
        assert risk == RiskLevel.MEDIUM
        
        # High risk event
        risk = monitor._assess_risk_level(
            SecurityEventType.SUSPICIOUS_ACTIVITY,
            client_ip="192.168.1.1",
            details={"patterns": ["sql_injection"]}
        )
        assert risk == RiskLevel.HIGH
        
        # Critical risk event
        risk = monitor._assess_risk_level(
            SecurityEventType.UNAUTHORIZED_ACCESS,
            client_ip="192.168.1.1",
            details={"admin_attempt": True}
        )
        assert risk == RiskLevel.CRITICAL

    def test_should_alert(self):
        """Test alert threshold logic."""
        monitor = SecurityEventMonitor()
        
        # Should alert for high and critical risks
        assert monitor._should_alert(RiskLevel.CRITICAL) is True
        assert monitor._should_alert(RiskLevel.HIGH) is True
        assert monitor._should_alert(RiskLevel.MEDIUM) is False
        assert monitor._should_alert(RiskLevel.LOW) is False

    @pytest.mark.asyncio
    async def test_send_alert(self, mock_logger):
        """Test alert sending."""
        monitor = SecurityEventMonitor()
        
        event_data = {
            "event_type": SecurityEventType.SUSPICIOUS_ACTIVITY.value,
            "client_ip": "192.168.1.1",
            "risk_level": RiskLevel.HIGH.value
        }
        
        await monitor._send_alert(event_data)
        
        # Should log critical alert
        mock_logger.critical.assert_called()

    @pytest.mark.asyncio
    async def test_cleanup_old_events(self, mock_redis):
        """Test cleanup of old security events."""
        with patch('src.security.monitoring.get_redis_client', return_value=mock_redis):
            monitor = SecurityEventMonitor()
            
            # Mock old event keys
            old_date = (datetime.utcnow() - timedelta(days=31)).strftime("%Y%m%d")
            mock_redis.keys.return_value = [
                f"security:event:user123:{old_date}:LOGIN_SUCCESS".encode(),
                f"security:counter:{old_date}:LOGIN_FAILURE".encode()
            ]
            
            mock_redis.delete = AsyncMock()
            
            await monitor.cleanup_old_events(days=30)
            
            # Should delete old keys
            mock_redis.delete.assert_called()


class TestSecurityHelperFunctions:
    """Test security monitoring helper functions."""

    @pytest.mark.asyncio
    async def test_log_auth_success(self, mock_logger):
        """Test authentication success logging."""
        with patch.object(security_monitor, 'log_event', new_callable=AsyncMock) as mock_log:
            await log_auth_success(
                user_id="user123",
                tenant_id="tenant456",
                client_ip="192.168.1.1",
                user_agent="TestAgent/1.0"
            )
            
            mock_log.assert_called_once()
            call_args = mock_log.call_args[1]
            assert call_args["event_type"] == SecurityEventType.LOGIN_SUCCESS

    @pytest.mark.asyncio
    async def test_log_auth_failure(self, mock_logger):
        """Test authentication failure logging."""
        with patch.object(security_monitor, 'log_event', new_callable=AsyncMock) as mock_log:
            await log_auth_failure(
                client_ip="192.168.1.1",
                user_agent="TestAgent/1.0",
                reason="invalid_credentials"
            )
            
            mock_log.assert_called_once()
            call_args = mock_log.call_args[1]
            assert call_args["event_type"] == SecurityEventType.LOGIN_FAILURE

    @pytest.mark.asyncio
    async def test_log_permission_denied(self, mock_logger):
        """Test permission denied logging."""
        with patch.object(security_monitor, 'log_event', new_callable=AsyncMock) as mock_log:
            await log_permission_denied(
                user_id="user123",
                tenant_id="tenant456",
                permission="admin_access",
                client_ip="192.168.1.1"
            )
            
            mock_log.assert_called_once()
            call_args = mock_log.call_args[1]
            assert call_args["event_type"] == SecurityEventType.PERMISSION_DENIED

    @pytest.mark.asyncio
    async def test_log_suspicious_activity(self, mock_logger):
        """Test suspicious activity logging."""
        with patch.object(security_monitor, 'log_event', new_callable=AsyncMock) as mock_log:
            await log_suspicious_activity(
                client_ip="192.168.1.1",
                user_agent="Attacker/1.0",
                path="/admin",
                method="GET",
                patterns=["suspicious_path", "suspicious_user_agent"]
            )
            
            mock_log.assert_called_once()
            call_args = mock_log.call_args[1]
            assert call_args["event_type"] == SecurityEventType.SUSPICIOUS_ACTIVITY

    @pytest.mark.asyncio
    async def test_log_rate_limit_exceeded(self, mock_logger):
        """Test rate limit exceeded logging."""
        with patch.object(security_monitor, 'log_event', new_callable=AsyncMock) as mock_log:
            await log_rate_limit_exceeded(
                client_ip="192.168.1.1",
                user_agent="TestAgent/1.0",
                path="/api/test",
                method="POST"
            )
            
            mock_log.assert_called_once()
            call_args = mock_log.call_args[1]
            assert call_args["event_type"] == SecurityEventType.RATE_LIMIT_EXCEEDED

    @pytest.mark.asyncio
    async def test_log_request_event(self, mock_logger):
        """Test general request event logging."""
        with patch.object(security_monitor, 'log_event', new_callable=AsyncMock) as mock_log:
            await log_request_event(
                request_id="req123",
                client_ip="192.168.1.1",
                user_agent="TestAgent/1.0",
                method="GET",
                path="/api/users"
            )
            
            mock_log.assert_called_once()
            call_args = mock_log.call_args[1]
            assert call_args["event_type"] == SecurityEventType.REQUEST


class TestSecurityMonitoringIntegration:
    """Integration tests for security monitoring."""

    @pytest.mark.asyncio
    async def test_multiple_failed_logins_pattern(self, mock_redis):
        """Test detection of multiple failed login attempts."""
        with patch('src.security.monitoring.get_redis_client', return_value=mock_redis):
            monitor = SecurityEventMonitor()
            
            # Simulate multiple failed login attempts
            for i in range(5):
                await monitor.log_event(
                    event_type=SecurityEventType.LOGIN_FAILURE,
                    client_ip="192.168.1.100",
                    user_agent="AttackerAgent/1.0",
                    details={"attempt": i + 1}
                )
            
            # Verify events were logged
            assert mock_redis.hset.call_count == 5

    @pytest.mark.asyncio
    async def test_concurrent_event_logging(self, mock_redis):
        """Test concurrent event logging."""
        with patch('src.security.monitoring.get_redis_client', return_value=mock_redis):
            monitor = SecurityEventMonitor()
            
            # Create multiple concurrent logging tasks
            tasks = []
            for i in range(10):
                task = asyncio.create_task(monitor.log_event(
                    event_type=SecurityEventType.REQUEST,
                    client_ip=f"192.168.1.{i}",
                    user_agent="TestAgent/1.0"
                ))
                tasks.append(task)
            
            # Wait for all tasks to complete
            await asyncio.gather(*tasks)
            
            # Verify all events were logged
            assert mock_redis.hset.call_count == 10

    @pytest.mark.asyncio
    async def test_error_handling_in_logging(self, mock_logger):
        """Test error handling during event logging."""
        failing_redis = AsyncMock()
        failing_redis.hset.side_effect = Exception("Redis connection failed")
        
        with patch('src.security.monitoring.get_redis_client', return_value=failing_redis):
            monitor = SecurityEventMonitor()
            
            # Should not raise exception even if Redis fails
            await monitor.log_event(
                event_type=SecurityEventType.LOGIN_SUCCESS,
                user_id="user123"
            )
            
            # Should log the error
            mock_logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_memory_usage_optimization(self, mock_redis):
        """Test that memory usage is optimized during monitoring."""
        with patch('src.security.monitoring.get_redis_client', return_value=mock_redis):
            monitor = SecurityEventMonitor()
            
            # Log many events
            for i in range(100):
                await monitor.log_event(
                    event_type=SecurityEventType.REQUEST,
                    client_ip="192.168.1.1",
                    details={"request_id": f"req_{i}"}
                )
            
            # Verify that TTL is set for event cleanup
            assert mock_redis.expire.call_count == 100


@pytest.mark.asyncio
async def test_global_monitor_instance():
    """Test that global monitor instance works correctly."""
    # Test that we can import and use the global instance
    assert security_monitor is not None
    
    # Test basic functionality (should not raise)
    with patch.object(security_monitor, 'log_event', new_callable=AsyncMock):
        await log_auth_success(user_id="test", client_ip="127.0.0.1")
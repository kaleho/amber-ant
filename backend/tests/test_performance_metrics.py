"""
Tests for performance metrics collection.

This module tests the performance metrics collection functionality
including request timing, database profiling, and system monitoring.
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from src.performance.metrics import (
    PerformanceMetrics,
    RequestMetrics,
    DatabaseMetrics,
    SystemMetrics,
    RequestTimer,
    DatabaseProfiler,
    performance_monitor,
    global_metrics
)


class TestPerformanceMetrics:
    """Test performance metrics collection."""
    
    def test_init(self):
        """Test PerformanceMetrics initialization."""
        metrics = PerformanceMetrics(max_history=100)
        
        assert metrics.max_history == 100
        assert len(metrics.request_metrics) == 0
        assert len(metrics.database_metrics) == 0
        assert len(metrics.system_metrics) == 0
        assert metrics.active_requests == 0
        assert metrics.total_requests == 0
    
    def test_add_request_metric(self):
        """Test adding request metrics."""
        metrics = PerformanceMetrics()
        
        request_metric = RequestMetrics(
            path="/api/test",
            method="GET",
            status_code=200,
            duration_ms=150.0,
            timestamp=datetime.utcnow()
        )
        
        metrics.add_request_metric(request_metric)
        
        assert len(metrics.request_metrics) == 1
        assert metrics.total_requests == 1
        assert metrics.error_counts[200] == 1
        assert "GET /api/test" in metrics.endpoint_stats
        assert len(metrics.endpoint_stats["GET /api/test"]) == 1
    
    def test_add_database_metric(self):
        """Test adding database metrics."""
        metrics = PerformanceMetrics()
        
        db_metric = DatabaseMetrics(
            query="SELECT * FROM users WHERE id = ?",
            duration_ms=25.0,
            timestamp=datetime.utcnow(),
            table="users",
            operation="SELECT"
        )
        
        metrics.add_database_metric(db_metric)
        
        assert len(metrics.database_metrics) == 1
        assert len(metrics.slow_queries) == 0  # Not slow enough
    
    def test_add_slow_database_metric(self):
        """Test adding slow database metrics."""
        metrics = PerformanceMetrics()
        
        slow_db_metric = DatabaseMetrics(
            query="SELECT * FROM transactions WHERE date > ?",
            duration_ms=600.0,  # Slow query
            timestamp=datetime.utcnow(),
            table="transactions",
            operation="SELECT"
        )
        
        metrics.add_database_metric(slow_db_metric)
        
        assert len(metrics.database_metrics) == 1
        assert len(metrics.slow_queries) == 1
    
    def test_get_recent_requests(self):
        """Test retrieving recent requests."""
        metrics = PerformanceMetrics()
        
        # Add old request
        old_request = RequestMetrics(
            path="/api/old",
            method="GET",
            status_code=200,
            duration_ms=100.0,
            timestamp=datetime.utcnow() - timedelta(minutes=10)
        )
        metrics.add_request_metric(old_request)
        
        # Add recent request
        recent_request = RequestMetrics(
            path="/api/recent",
            method="GET",
            status_code=200,
            duration_ms=100.0,
            timestamp=datetime.utcnow()
        )
        metrics.add_request_metric(recent_request)
        
        recent_requests = metrics.get_recent_requests(5)  # Last 5 minutes
        
        assert len(recent_requests) == 1
        assert recent_requests[0].path == "/api/recent"
    
    def test_get_endpoint_statistics(self):
        """Test endpoint statistics calculation."""
        metrics = PerformanceMetrics()
        
        # Add multiple requests for the same endpoint
        for i in range(5):
            request_metric = RequestMetrics(
                path="/api/test",
                method="GET",
                status_code=200,
                duration_ms=100.0 + i * 10,  # Varying durations
                timestamp=datetime.utcnow()
            )
            metrics.add_request_metric(request_metric)
        
        stats = metrics.get_endpoint_statistics("GET /api/test")
        
        assert stats["count"] == 5
        assert stats["avg_ms"] == 120.0  # (100+110+120+130+140)/5
        assert stats["min_ms"] == 100.0
        assert stats["max_ms"] == 140.0
        assert "p50_ms" in stats
        assert "p95_ms" in stats
        assert "p99_ms" in stats
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_get_system_health(self, mock_disk, mock_memory, mock_cpu):
        """Test system health metrics."""
        # Mock system calls
        mock_cpu.return_value = 45.0
        
        mock_memory_obj = Mock()
        mock_memory_obj.percent = 60.0
        mock_memory_obj.used = 8 * 1024 * 1024 * 1024  # 8GB
        mock_memory.return_value = mock_memory_obj
        
        mock_disk_obj = Mock()
        mock_disk_obj.percent = 70.0
        mock_disk.return_value = mock_disk_obj
        
        metrics = PerformanceMetrics()
        health = metrics.get_system_health()
        
        assert health["cpu_percent"] == 45.0
        assert health["memory_percent"] == 60.0
        assert health["memory_used_mb"] == 8192.0
        assert health["disk_usage_percent"] == 70.0
        assert "active_requests" in health
        assert "request_rate_per_minute" in health


class TestRequestTimer:
    """Test request timing functionality."""
    
    def test_request_timer_context_manager(self):
        """Test RequestTimer as context manager."""
        metrics = PerformanceMetrics()
        
        with RequestTimer(metrics, "/api/test", "GET") as timer:
            # Simulate some work
            import time
            time.sleep(0.01)  # 10ms
            
            # Add query metrics
            timer.add_query_metrics(2, 15.0)
        
        assert len(metrics.request_metrics) == 1
        request_metric = metrics.request_metrics[0]
        
        assert request_metric.path == "/api/test"
        assert request_metric.method == "GET"
        assert request_metric.status_code == 200  # No exception
        assert request_metric.duration_ms >= 10.0  # At least 10ms
        assert request_metric.query_count == 2
        assert request_metric.query_time_ms == 15.0
    
    def test_request_timer_with_exception(self):
        """Test RequestTimer with exception."""
        metrics = PerformanceMetrics()
        
        try:
            with RequestTimer(metrics, "/api/error", "POST"):
                raise ValueError("Test error")
        except ValueError:
            pass
        
        assert len(metrics.request_metrics) == 1
        request_metric = metrics.request_metrics[0]
        
        assert request_metric.path == "/api/error"
        assert request_metric.method == "POST"
        assert request_metric.status_code == 500  # Exception occurred


class TestDatabaseProfiler:
    """Test database profiling functionality."""
    
    def test_database_profiler_init(self):
        """Test DatabaseProfiler initialization."""
        metrics = PerformanceMetrics()
        profiler = DatabaseProfiler(metrics)
        
        assert profiler.metrics == metrics
        assert profiler.active_queries == {}
    
    def test_extract_table_name(self):
        """Test table name extraction from SQL statements."""
        metrics = PerformanceMetrics()
        profiler = DatabaseProfiler(metrics)
        
        # Test different SQL patterns
        test_cases = [
            ("SELECT * FROM users WHERE id = 1", "users"),
            ("INSERT INTO transactions (amount) VALUES (100)", "transactions"),
            ("UPDATE budgets SET amount = 200", "budgets"),
            ("DELETE FROM goals WHERE id = 5", "goals"),
            ("select id from accounts", "accounts"),  # lowercase
            ("SELECT COUNT(*) FROM user_families", "user_families"),
            ("INVALID SQL", None),
            ("", None)
        ]
        
        for sql, expected_table in test_cases:
            result = profiler._extract_table_name(sql)
            assert result == expected_table, f"Failed for SQL: {sql}"
    
    @pytest.mark.asyncio
    async def test_profile_query_context_manager(self):
        """Test query profiling context manager."""
        metrics = PerformanceMetrics()
        profiler = DatabaseProfiler(metrics)
        
        async with profiler.profile_query("SELECT * FROM test", tenant_id="tenant1"):
            # Simulate database work
            await asyncio.sleep(0.01)  # 10ms
        
        assert len(metrics.database_metrics) == 1
        db_metric = metrics.database_metrics[0]
        
        assert db_metric.query == "SELECT * FROM test"
        assert db_metric.tenant_id == "tenant1"
        assert db_metric.duration_ms >= 10.0


class TestPerformanceMonitorDecorator:
    """Test performance monitoring decorator."""
    
    @pytest.mark.asyncio
    async def test_async_function_monitoring(self):
        """Test monitoring async functions."""
        @performance_monitor
        async def test_async_function():
            await asyncio.sleep(0.01)
            return "result"
        
        with patch('src.performance.metrics.logger') as mock_logger:
            result = await test_async_function()
            
            assert result == "result"
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args
            assert "test_async_function" in call_args[0][0]
            assert "duration_ms" in call_args[1]["extra"]
    
    def test_sync_function_monitoring(self):
        """Test monitoring sync functions."""
        @performance_monitor
        def test_sync_function():
            import time
            time.sleep(0.01)
            return "result"
        
        with patch('src.performance.metrics.logger') as mock_logger:
            result = test_sync_function()
            
            assert result == "result"
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args
            assert "test_sync_function" in call_args[0][0]
            assert "duration_ms" in call_args[1]["extra"]


class TestMetricsIntegration:
    """Test metrics integration scenarios."""
    
    def test_high_frequency_requests(self):
        """Test handling high frequency requests."""
        metrics = PerformanceMetrics(max_history=100)
        
        # Add 150 requests (more than max_history)
        for i in range(150):
            request_metric = RequestMetrics(
                path=f"/api/test/{i % 10}",  # 10 different endpoints
                method="GET",
                status_code=200 if i % 10 != 0 else 500,  # Some errors
                duration_ms=100.0 + i,
                timestamp=datetime.utcnow() - timedelta(seconds=i)
            )
            metrics.add_request_metric(request_metric)
        
        # Should only keep the most recent 100
        assert len(metrics.request_metrics) == 100
        assert metrics.total_requests == 150
        
        # Error counts should accumulate
        assert metrics.error_counts[200] == 135  # 150 - 15 errors
        assert metrics.error_counts[500] == 15   # Every 10th request
    
    def test_concurrent_metric_updates(self):
        """Test thread-safe metric updates."""
        metrics = PerformanceMetrics()
        
        import threading
        import time
        
        def add_metrics(thread_id):
            for i in range(10):
                request_metric = RequestMetrics(
                    path=f"/api/thread/{thread_id}",
                    method="GET",
                    status_code=200,
                    duration_ms=100.0,
                    timestamp=datetime.utcnow()
                )
                metrics.add_request_metric(request_metric)
                time.sleep(0.001)  # Small delay
        
        # Create multiple threads
        threads = []
        for thread_id in range(5):
            thread = threading.Thread(target=add_metrics, args=(thread_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Should have 50 requests total (5 threads * 10 requests)
        assert len(metrics.request_metrics) == 50
        assert metrics.total_requests == 50
    
    def test_memory_management(self):
        """Test memory management with endpoint stats."""
        metrics = PerformanceMetrics()
        
        # Add many requests to trigger cleanup
        for i in range(2000):
            request_metric = RequestMetrics(
                path=f"/api/endpoint/{i % 100}",  # 100 different endpoints
                method="GET",
                status_code=200,
                duration_ms=100.0,
                timestamp=datetime.utcnow()
            )
            metrics.add_request_metric(request_metric)
        
        # Trigger cleanup manually
        metrics._cleanup_endpoint_stats()
        
        # Each endpoint should have at most 1000 entries
        for endpoint, durations in metrics.endpoint_stats.items():
            assert len(durations) <= 1000
    
    def test_percentile_calculation(self):
        """Test percentile calculations."""
        metrics = PerformanceMetrics()
        
        # Test with known data
        data = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        
        assert metrics._percentile(data, 50) == 50  # Median
        assert metrics._percentile(data, 90) == 90  # 90th percentile
        assert metrics._percentile(data, 95) == 95  # 95th percentile
        assert metrics._percentile([], 50) == 0.0   # Empty data
        assert metrics._percentile([100], 50) == 100  # Single value


class TestGlobalMetrics:
    """Test global metrics instance."""
    
    def test_global_metrics_instance(self):
        """Test that global_metrics is properly initialized."""
        assert global_metrics is not None
        assert isinstance(global_metrics, PerformanceMetrics)
        assert global_metrics.max_history == 10000  # Default value
    
    def test_global_metrics_thread_safety(self):
        """Test global metrics thread safety."""
        import threading
        import time
        
        # Clear any existing metrics
        global_metrics.request_metrics.clear()
        global_metrics.total_requests = 0
        
        def add_to_global_metrics(thread_id):
            for i in range(5):
                request_metric = RequestMetrics(
                    path=f"/global/test/{thread_id}",
                    method="GET",
                    status_code=200,
                    duration_ms=50.0,
                    timestamp=datetime.utcnow()
                )
                global_metrics.add_request_metric(request_metric)
                time.sleep(0.001)
        
        # Create multiple threads using global metrics
        threads = []
        for thread_id in range(3):
            thread = threading.Thread(target=add_to_global_metrics, args=(thread_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Should have 15 requests (3 threads * 5 requests)
        assert global_metrics.total_requests >= 15  # >= because other tests may add metrics
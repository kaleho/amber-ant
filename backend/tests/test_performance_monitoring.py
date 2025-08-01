"""
Tests for performance monitoring and bottleneck detection.

This module tests the performance monitoring system including
bottleneck detection, alert generation, and performance analysis.
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from src.performance.metrics import PerformanceMetrics, RequestMetrics, DatabaseMetrics
from src.performance.monitoring import (
    PerformanceMonitor,
    PerformanceThresholds,
    BottleneckDetector,
    BottleneckAlert,
    BottleneckType
)


class TestPerformanceThresholds:
    """Test performance threshold configuration."""
    
    def test_default_thresholds(self):
        """Test default threshold values."""
        thresholds = PerformanceThresholds()
        
        assert thresholds.max_avg_latency_ms == 1000.0
        assert thresholds.max_p95_latency_ms == 2000.0
        assert thresholds.max_error_rate_percent == 5.0
        assert thresholds.max_query_time_ms == 500.0
        assert thresholds.max_queries_per_request == 10
        assert thresholds.max_cpu_percent == 80.0
        assert thresholds.max_memory_percent == 85.0
        assert thresholds.max_concurrent_requests == 100
        assert thresholds.analysis_window_minutes == 5
        assert thresholds.trending_window_minutes == 15
    
    def test_custom_thresholds(self):
        """Test custom threshold configuration."""
        thresholds = PerformanceThresholds(
            max_avg_latency_ms=500.0,
            max_error_rate_percent=2.0,
            max_cpu_percent=70.0
        )
        
        assert thresholds.max_avg_latency_ms == 500.0
        assert thresholds.max_error_rate_percent == 2.0
        assert thresholds.max_cpu_percent == 70.0
        # Other values should remain default
        assert thresholds.max_p95_latency_ms == 2000.0


class TestPerformanceMonitor:
    """Test performance monitoring functionality."""
    
    def test_monitor_initialization(self):
        """Test monitor initialization."""
        metrics = PerformanceMetrics()
        thresholds = PerformanceThresholds()
        monitor = PerformanceMonitor(metrics, thresholds)
        
        assert monitor.metrics == metrics
        assert monitor.thresholds == thresholds
        assert len(monitor.alerts) == 0
        assert monitor.max_alerts == 100
    
    @pytest.mark.asyncio
    async def test_analyze_request_performance_high_latency(self):
        """Test request performance analysis with high latency."""
        metrics = PerformanceMetrics()
        thresholds = PerformanceThresholds(max_avg_latency_ms=500.0)
        monitor = PerformanceMonitor(metrics, thresholds)
        
        # Add high latency requests
        for i in range(5):
            request = RequestMetrics(
                path="/api/slow",
                method="GET",
                status_code=200,
                duration_ms=800.0,  # Above threshold
                timestamp=datetime.utcnow()
            )
            metrics.add_request_metric(request)
        
        alerts = await monitor._analyze_request_performance()
        
        assert len(alerts) == 1
        alert = alerts[0]
        assert alert.type == BottleneckType.HIGH_LATENCY
        assert alert.severity in ["medium", "high"]
        assert "GET /api/slow" in alert.affected_endpoints
        assert alert.details["avg_latency_ms"] == 800.0
    
    @pytest.mark.asyncio
    async def test_analyze_request_performance_high_error_rate(self):
        """Test request performance analysis with high error rate."""
        metrics = PerformanceMetrics()
        thresholds = PerformanceThresholds(max_error_rate_percent=10.0)
        monitor = PerformanceMonitor(metrics, thresholds)
        
        # Add requests with high error rate
        for i in range(10):
            status_code = 500 if i < 3 else 200  # 30% error rate
            request = RequestMetrics(
                path="/api/errors",
                method="POST",
                status_code=status_code,
                duration_ms=200.0,
                timestamp=datetime.utcnow()
            )
            metrics.add_request_metric(request)
        
        alerts = await monitor._analyze_request_performance()
        
        assert len(alerts) == 1
        alert = alerts[0]
        assert alert.type == BottleneckType.HIGH_ERROR_RATE
        assert alert.severity == "high"
        assert alert.details["error_rate_percent"] == 30.0
        assert alert.details["error_count"] == 3
    
    @pytest.mark.asyncio
    async def test_analyze_database_performance_slow_queries(self):
        """Test database performance analysis with slow queries."""
        metrics = PerformanceMetrics()
        thresholds = PerformanceThresholds(max_query_time_ms=200.0)
        monitor = PerformanceMonitor(metrics, thresholds)
        
        # Add slow database queries
        for i in range(3):
            db_metric = DatabaseMetrics(
                query=f"SELECT * FROM large_table WHERE complex_condition_{i}",
                duration_ms=600.0,  # Above threshold
                timestamp=datetime.utcnow(),
                table="large_table",
                operation="SELECT"
            )
            metrics.add_database_metric(db_metric)
        
        alerts = await monitor._analyze_database_performance()
        
        assert len(alerts) == 1
        alert = alerts[0]
        assert alert.type == BottleneckType.SLOW_DATABASE
        assert alert.severity in ["medium", "high"]
        assert len(alert.details["slowest_queries"]) == 3
        assert alert.details["avg_slow_time_ms"] == 600.0
    
    @pytest.mark.asyncio
    @patch('src.performance.monitoring.PerformanceMonitor._detect_n_plus_one_queries')
    async def test_analyze_database_performance_n_plus_one(self, mock_detect_n_plus_one):
        """Test N+1 query detection."""
        metrics = PerformanceMetrics()
        monitor = PerformanceMonitor(metrics)
        
        # Mock N+1 detection
        mock_detect_n_plus_one.return_value = None
        
        await monitor._analyze_database_performance()
        
        # Verify N+1 detection was called
        mock_detect_n_plus_one.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.performance.metrics.PerformanceMetrics.get_system_health')
    async def test_analyze_system_performance_high_cpu(self, mock_get_system_health):
        """Test system performance analysis with high CPU usage."""
        metrics = PerformanceMetrics()
        thresholds = PerformanceThresholds(max_cpu_percent=70.0)
        monitor = PerformanceMonitor(metrics, thresholds)
        
        # Mock high CPU usage
        mock_get_system_health.return_value = {
            "cpu_percent": 85.0,
            "memory_percent": 60.0,
            "disk_usage_percent": 50.0,
            "active_requests": 20
        }
        
        alerts = await monitor._analyze_system_performance()
        
        assert len(alerts) == 1
        alert = alerts[0]
        assert alert.type == BottleneckType.HIGH_CPU
        assert alert.severity == "high"
        assert alert.details["cpu_percent"] == 85.0
    
    @pytest.mark.asyncio
    @patch('src.performance.metrics.PerformanceMetrics.get_system_health')
    async def test_analyze_system_performance_high_memory(self, mock_get_system_health):
        """Test system performance analysis with high memory usage."""
        metrics = PerformanceMetrics()
        thresholds = PerformanceThresholds(max_memory_percent=80.0)
        monitor = PerformanceMonitor(metrics, thresholds)
        
        # Mock high memory usage
        mock_get_system_health.return_value = {
            "cpu_percent": 50.0,
            "memory_percent": 92.0,
            "memory_used_mb": 15360.0,  # 15GB
            "disk_usage_percent": 60.0,
            "active_requests": 15
        }
        
        alerts = await monitor._analyze_system_performance()
        
        assert len(alerts) == 1
        alert = alerts[0]
        assert alert.type == BottleneckType.HIGH_MEMORY
        assert alert.severity == "high"
        assert alert.details["memory_percent"] == 92.0
        assert alert.details["memory_used_mb"] == 15360.0
    
    @pytest.mark.asyncio
    @patch('src.performance.metrics.PerformanceMetrics.get_system_health')
    async def test_analyze_system_performance_high_concurrent_requests(self, mock_get_system_health):
        """Test system performance analysis with high concurrent requests."""
        metrics = PerformanceMetrics()
        thresholds = PerformanceThresholds(max_concurrent_requests=50)
        monitor = PerformanceMonitor(metrics, thresholds)
        
        # Mock high concurrent requests
        mock_get_system_health.return_value = {
            "cpu_percent": 60.0,
            "memory_percent": 70.0,
            "disk_usage_percent": 50.0,
            "active_requests": 75,
            "request_rate_per_minute": 1200
        }
        
        alerts = await monitor._analyze_system_performance()
        
        assert len(alerts) == 1
        alert = alerts[0]
        assert alert.type == BottleneckType.CONCURRENT_REQUESTS
        assert alert.severity == "high"
        assert alert.details["active_requests"] == 75
        assert alert.details["request_rate"] == 1200
    
    @pytest.mark.asyncio
    async def test_detect_n_plus_one_queries(self):
        """Test N+1 query pattern detection."""
        metrics = PerformanceMetrics()
        monitor = PerformanceMonitor(metrics)
        
        # Create many similar queries in a short time window
        base_time = datetime.utcnow()
        db_metrics = []
        
        for i in range(12):  # More than threshold
            db_metric = DatabaseMetrics(
                query=f"SELECT * FROM users WHERE id = {i}",
                duration_ms=50.0,
                timestamp=base_time,  # Same time window
                table="users",
                operation="SELECT"
            )
            db_metrics.append(db_metric)
        
        alerts = []
        await monitor._detect_n_plus_one_queries(db_metrics, alerts)
        
        assert len(alerts) == 1
        alert = alerts[0]
        assert alert.type == BottleneckType.QUERY_N_PLUS_ONE
        assert alert.severity == "medium"
        assert "SELECT:users" in alert.details["pattern"]
    
    @pytest.mark.asyncio
    async def test_analyze_performance_trends_degrading(self):
        """Test performance trend analysis - degrading performance."""
        metrics = PerformanceMetrics()
        monitor = PerformanceMonitor(metrics)
        
        # Add historical requests (better performance)
        historical_time = datetime.utcnow() - timedelta(minutes=10)
        for i in range(15):
            request = RequestMetrics(
                path="/api/test",
                method="GET",
                status_code=200,
                duration_ms=200.0,  # Good performance
                timestamp=historical_time + timedelta(seconds=i)
            )
            metrics.add_request_metric(request)
        
        # Add current requests (worse performance)
        current_time = datetime.utcnow()
        for i in range(15):
            request = RequestMetrics(
                path="/api/test",
                method="GET",
                status_code=200,
                duration_ms=400.0,  # Degraded performance (2x worse)
                timestamp=current_time - timedelta(seconds=i)
            )
            metrics.add_request_metric(request)
        
        alerts = await monitor._analyze_performance_patterns()
        
        assert len(alerts) == 1
        alert = alerts[0]
        assert alert.type == BottleneckType.HIGH_LATENCY
        assert "degradation" in alert.message.lower()
        assert alert.details["degradation_percent"] == 100.0  # 2x worse = 100% increase
    
    def test_add_alert(self):
        """Test alert addition and management."""
        metrics = PerformanceMetrics()
        monitor = PerformanceMonitor(metrics)
        
        alert = BottleneckAlert(
            type=BottleneckType.HIGH_LATENCY,
            severity="medium",
            message="Test alert",
            details={"test": "data"},
            timestamp=datetime.utcnow()
        )
        
        monitor._add_alert(alert)
        
        assert len(monitor.alerts) == 1
        assert monitor.alerts[0] == alert
    
    def test_get_recent_alerts(self):
        """Test retrieving recent alerts."""
        metrics = PerformanceMetrics()
        monitor = PerformanceMonitor(metrics)
        
        # Add old alert
        old_alert = BottleneckAlert(
            type=BottleneckType.HIGH_CPU,
            severity="low",
            message="Old alert",
            details={},
            timestamp=datetime.utcnow() - timedelta(hours=3)
        )
        monitor._add_alert(old_alert)
        
        # Add recent alert
        recent_alert = BottleneckAlert(
            type=BottleneckType.HIGH_MEMORY,
            severity="high",
            message="Recent alert",
            details={},
            timestamp=datetime.utcnow()
        )
        monitor._add_alert(recent_alert)
        
        recent_alerts = monitor.get_recent_alerts(1)  # Last 1 hour
        
        assert len(recent_alerts) == 1
        assert recent_alerts[0] == recent_alert
    
    def test_get_alert_summary_healthy(self):
        """Test alert summary when system is healthy."""
        metrics = PerformanceMetrics()
        monitor = PerformanceMonitor(metrics)
        
        summary = monitor.get_alert_summary()
        
        assert summary["status"] == "healthy"
        assert summary["alert_count"] == 0
    
    def test_get_alert_summary_with_issues(self):
        """Test alert summary with detected issues."""
        metrics = PerformanceMetrics()
        monitor = PerformanceMonitor(metrics)
        
        # Add various alerts
        high_alert = BottleneckAlert(
            type=BottleneckType.HIGH_LATENCY,
            severity="high",
            message="High latency",
            details={},
            timestamp=datetime.utcnow()
        )
        monitor._add_alert(high_alert)
        
        critical_alert = BottleneckAlert(
            type=BottleneckType.HIGH_CPU,
            severity="critical",
            message="Critical CPU",
            details={},
            timestamp=datetime.utcnow()
        )
        monitor._add_alert(critical_alert)
        
        summary = monitor.get_alert_summary()
        
        assert summary["status"] == "issues_detected"
        assert summary["overall_severity"] == "critical"
        assert summary["alert_count"] == 2
        assert summary["severity_breakdown"]["high"] == 1
        assert summary["severity_breakdown"]["critical"] == 1


class TestBottleneckDetector:
    """Test bottleneck detection algorithms."""
    
    def test_detector_initialization(self):
        """Test detector initialization."""
        metrics = PerformanceMetrics()
        detector = BottleneckDetector(metrics)
        
        assert detector.metrics == metrics
    
    @pytest.mark.asyncio
    async def test_detect_resource_contention(self):
        """Test resource contention detection."""
        metrics = PerformanceMetrics()
        detector = BottleneckDetector(metrics)
        
        # Create high concurrency with high latency scenario
        base_time = datetime.utcnow()
        
        # Add 15 concurrent requests with high latency
        for i in range(15):
            request = RequestMetrics(
                path=f"/api/endpoint/{i % 3}",
                method="GET",
                status_code=200,
                duration_ms=2500.0,  # High latency
                timestamp=base_time  # Same timestamp = high concurrency
            )
            metrics.add_request_metric(request)
        
        contentions = await detector.detect_resource_contention()
        
        assert len(contentions) == 1
        contention = contentions[0]
        assert contention["type"] == "high_concurrency_latency"
        assert contention["concurrent_requests"] == 15
        assert contention["avg_latency_ms"] == 2500.0
        assert len(contention["affected_endpoints"]) == 3
    
    @pytest.mark.asyncio
    async def test_detect_memory_leaks(self):
        """Test memory leak detection."""
        metrics = PerformanceMetrics()
        detector = BottleneckDetector(metrics)
        
        # Create increasing memory usage pattern
        base_time = datetime.utcnow() - timedelta(minutes=25)
        
        for window in range(6):  # 6 five-minute windows
            window_time = base_time + timedelta(minutes=window * 5)
            
            # Each window has increasing memory delta
            for i in range(20):
                request = RequestMetrics(
                    path="/api/memory-intensive",
                    method="POST",
                    status_code=200,
                    duration_ms=200.0,
                    timestamp=window_time + timedelta(seconds=i),
                    memory_delta_mb=5.0 + window * 2.0  # Increasing memory usage
                )
                metrics.add_request_metric(request)
        
        leaks = await detector.detect_memory_leaks()
        
        assert len(leaks) == 1
        leak = leaks[0]
        assert leak["type"] == "memory_leak_trend"
        assert leak["avg_increase_mb"] > 0
    
    @pytest.mark.asyncio
    async def test_detect_database_hotspots(self):
        """Test database hotspot detection."""
        metrics = PerformanceMetrics()
        detector = BottleneckDetector(metrics)
        
        # Create high-frequency queries on one table
        for i in range(60):
            db_metric = DatabaseMetrics(
                query=f"SELECT * FROM hot_table WHERE id = {i}",
                duration_ms=100.0,
                timestamp=datetime.utcnow(),
                table="hot_table",
                operation="SELECT"
            )
            metrics.add_database_metric(db_metric)
        
        # Create slow queries on another table
        for i in range(5):
            db_metric = DatabaseMetrics(
                query=f"SELECT * FROM slow_table JOIN other_table WHERE complex_condition_{i}",
                duration_ms=400.0,  # Slow
                timestamp=datetime.utcnow(),
                table="slow_table",
                operation="SELECT"
            )
            metrics.add_database_metric(db_metric)
        
        hotspots = await detector.detect_database_hotspots()
        
        assert len(hotspots) == 2
        
        # Find hotspots by table
        hot_table_hotspot = next(h for h in hotspots if h["table"] == "hot_table")
        slow_table_hotspot = next(h for h in hotspots if h["table"] == "slow_table")
        
        # High frequency table
        assert hot_table_hotspot["query_count"] == 60
        assert hot_table_hotspot["avg_duration_ms"] == 100.0
        
        # Slow query table
        assert slow_table_hotspot["query_count"] == 5
        assert slow_table_hotspot["avg_duration_ms"] == 400.0


class TestPerformanceIntegration:
    """Test performance monitoring integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_complete_performance_analysis_cycle(self):
        """Test complete performance analysis cycle."""
        metrics = PerformanceMetrics()
        monitor = PerformanceMonitor(metrics)
        
        # Simulate mixed workload with various issues
        
        # 1. Add normal requests
        for i in range(20):
            request = RequestMetrics(
                path="/api/normal",
                method="GET",
                status_code=200,
                duration_ms=150.0,
                timestamp=datetime.utcnow()
            )
            metrics.add_request_metric(request)
        
        # 2. Add slow requests
        for i in range(5):
            request = RequestMetrics(
                path="/api/slow",
                method="GET",
                status_code=200,
                duration_ms=1500.0,  # Slow
                timestamp=datetime.utcnow()
            )
            metrics.add_request_metric(request)
        
        # 3. Add error requests
        for i in range(3):
            request = RequestMetrics(
                path="/api/errors",
                method="POST",
                status_code=500,
                duration_ms=200.0,
                timestamp=datetime.utcnow()
            )
            metrics.add_request_metric(request)
        
        # 4. Add slow database queries
        for i in range(2):
            db_metric = DatabaseMetrics(
                query="SELECT * FROM complex_view WHERE slow_condition",
                duration_ms=800.0,
                timestamp=datetime.utcnow(),
                table="complex_view",
                operation="SELECT"
            )
            metrics.add_database_metric(db_metric)
        
        # Run complete analysis
        with patch('src.performance.metrics.PerformanceMetrics.get_system_health') as mock_health:
            mock_health.return_value = {
                "cpu_percent": 85.0,  # High CPU
                "memory_percent": 60.0,
                "disk_usage_percent": 50.0,
                "active_requests": 25
            }
            
            alerts = await monitor.analyze_performance()
        
        # Should detect multiple issues
        assert len(alerts) >= 2  # At least slow requests and high CPU
        
        # Check alert types
        alert_types = [alert.type for alert in alerts]
        assert BottleneckType.HIGH_LATENCY in alert_types
        assert BottleneckType.HIGH_CPU in alert_types
    
    @pytest.mark.asyncio 
    async def test_monitoring_with_no_data(self):
        """Test monitoring behavior with no data."""
        metrics = PerformanceMetrics()
        monitor = PerformanceMonitor(metrics)
        
        # Run analysis with no metrics
        alerts = await monitor.analyze_performance()
        
        # Should not generate alerts for empty data
        assert len(alerts) == 0
        
        # Summary should indicate healthy status
        summary = monitor.get_alert_summary()
        assert summary["status"] == "healthy"
        assert summary["alert_count"] == 0
    
    def test_alert_retention_limits(self):
        """Test alert retention limits."""
        metrics = PerformanceMetrics()
        monitor = PerformanceMonitor(metrics)
        monitor.max_alerts = 5  # Small limit for testing
        
        # Add more alerts than the limit
        for i in range(10):
            alert = BottleneckAlert(
                type=BottleneckType.HIGH_LATENCY,
                severity="medium",
                message=f"Alert {i}",
                details={"index": i},
                timestamp=datetime.utcnow()
            )
            monitor._add_alert(alert)
        
        # Should only keep the most recent alerts
        assert len(monitor.alerts) == 5
        
        # Should be the last 5 alerts (5-9)
        alert_indices = [alert.details["index"] for alert in monitor.alerts]
        assert alert_indices == [5, 6, 7, 8, 9]
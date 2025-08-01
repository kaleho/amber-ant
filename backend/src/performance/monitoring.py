"""
Performance monitoring and bottleneck detection.

This module provides advanced monitoring capabilities to identify
performance bottlenecks and system issues in real-time.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import statistics
from collections import defaultdict

from .metrics import PerformanceMetrics, RequestMetrics, DatabaseMetrics, SystemMetrics

logger = logging.getLogger(__name__)


class BottleneckType(Enum):
    """Types of performance bottlenecks."""
    HIGH_LATENCY = "high_latency"
    HIGH_ERROR_RATE = "high_error_rate" 
    SLOW_DATABASE = "slow_database"
    HIGH_CPU = "high_cpu"
    HIGH_MEMORY = "high_memory"
    HIGH_DISK = "high_disk"
    CONCURRENT_REQUESTS = "concurrent_requests"
    QUERY_N_PLUS_ONE = "query_n_plus_one"


@dataclass
class BottleneckAlert:
    """Represents a detected performance bottleneck."""
    type: BottleneckType
    severity: str  # low, medium, high, critical
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    affected_endpoints: List[str] = field(default_factory=list)
    suggested_actions: List[str] = field(default_factory=list)


@dataclass
class PerformanceThresholds:
    """Performance monitoring thresholds."""
    # Request thresholds
    max_avg_latency_ms: float = 1000.0
    max_p95_latency_ms: float = 2000.0
    max_error_rate_percent: float = 5.0
    
    # Database thresholds
    max_query_time_ms: float = 500.0
    max_queries_per_request: int = 10
    
    # System thresholds
    max_cpu_percent: float = 80.0
    max_memory_percent: float = 85.0
    max_disk_percent: float = 90.0
    max_concurrent_requests: int = 100
    
    # Time windows for analysis
    analysis_window_minutes: int = 5
    trending_window_minutes: int = 15


class PerformanceMonitor:
    """Monitors application performance and detects issues."""
    
    def __init__(self, metrics: PerformanceMetrics, thresholds: Optional[PerformanceThresholds] = None):
        self.metrics = metrics
        self.thresholds = thresholds or PerformanceThresholds()
        self.alerts: List[BottleneckAlert] = []
        self.max_alerts = 100
        self.last_analysis = datetime.utcnow()
        self.analysis_interval = timedelta(minutes=1)
    
    async def start_monitoring(self):
        """Start continuous performance monitoring."""
        logger.info("Starting performance monitoring")
        
        while True:
            try:
                await self.analyze_performance()
                await asyncio.sleep(60)  # Analyze every minute
            except Exception as e:
                logger.error(f"Error in performance monitoring: {e}")
                await asyncio.sleep(60)
    
    async def analyze_performance(self) -> List[BottleneckAlert]:
        """Analyze current performance and detect bottlenecks."""
        new_alerts = []
        
        # Analyze requests
        new_alerts.extend(await self._analyze_request_performance())
        
        # Analyze database
        new_alerts.extend(await self._analyze_database_performance())
        
        # Analyze system resources
        new_alerts.extend(await self._analyze_system_performance())
        
        # Analyze patterns
        new_alerts.extend(await self._analyze_performance_patterns())
        
        # Store new alerts
        for alert in new_alerts:
            self._add_alert(alert)
        
        self.last_analysis = datetime.utcnow()
        
        if new_alerts:
            logger.warning(f"Detected {len(new_alerts)} performance issues")
        
        return new_alerts
    
    async def _analyze_request_performance(self) -> List[BottleneckAlert]:
        """Analyze request performance for bottlenecks."""
        alerts = []
        recent_requests = self.metrics.get_recent_requests(self.thresholds.analysis_window_minutes)
        
        if not recent_requests:
            return alerts
        
        # Group by endpoint
        endpoint_metrics = defaultdict(list)
        for req in recent_requests:
            endpoint = f"{req.method} {req.path}"
            endpoint_metrics[endpoint].append(req)
        
        for endpoint, requests in endpoint_metrics.items():
            # Calculate statistics
            durations = [r.duration_ms for r in requests]
            error_requests = [r for r in requests if r.status_code >= 400]
            
            avg_latency = statistics.mean(durations)
            p95_latency = self._percentile(durations, 95)
            error_rate = (len(error_requests) / len(requests)) * 100
            
            # Check latency thresholds
            if avg_latency > self.thresholds.max_avg_latency_ms:
                alerts.append(BottleneckAlert(
                    type=BottleneckType.HIGH_LATENCY,
                    severity="high" if avg_latency > self.thresholds.max_avg_latency_ms * 2 else "medium",
                    message=f"High average latency detected on {endpoint}",
                    details={
                        "avg_latency_ms": avg_latency,
                        "threshold_ms": self.thresholds.max_avg_latency_ms,
                        "request_count": len(requests)
                    },
                    timestamp=datetime.utcnow(),
                    affected_endpoints=[endpoint],
                    suggested_actions=[
                        "Optimize endpoint logic",
                        "Check database queries",
                        "Review caching strategy",
                        "Consider async processing"
                    ]
                ))
            
            if p95_latency > self.thresholds.max_p95_latency_ms:
                alerts.append(BottleneckAlert(
                    type=BottleneckType.HIGH_LATENCY,
                    severity="high",
                    message=f"High P95 latency detected on {endpoint}",
                    details={
                        "p95_latency_ms": p95_latency,
                        "threshold_ms": self.thresholds.max_p95_latency_ms,
                        "request_count": len(requests)
                    },
                    timestamp=datetime.utcnow(),
                    affected_endpoints=[endpoint],
                    suggested_actions=[
                        "Investigate slowest requests",
                        "Optimize worst-case scenarios",
                        "Check for resource contention"
                    ]
                ))
            
            # Check error rate
            if error_rate > self.thresholds.max_error_rate_percent:
                alerts.append(BottleneckAlert(
                    type=BottleneckType.HIGH_ERROR_RATE,
                    severity="critical" if error_rate > 20 else "high",
                    message=f"High error rate detected on {endpoint}",
                    details={
                        "error_rate_percent": error_rate,
                        "threshold_percent": self.thresholds.max_error_rate_percent,
                        "error_count": len(error_requests),
                        "total_requests": len(requests),
                        "error_codes": {code: len([r for r in error_requests if r.status_code == code]) 
                                      for code in set(r.status_code for r in error_requests)}
                    },
                    timestamp=datetime.utcnow(),
                    affected_endpoints=[endpoint],
                    suggested_actions=[
                        "Review error logs",
                        "Check input validation",
                        "Verify external dependencies",
                        "Test error handling paths"
                    ]
                ))
        
        return alerts
    
    async def _analyze_database_performance(self) -> List[BottleneckAlert]:
        """Analyze database performance for bottlenecks."""
        alerts = []
        recent_db_metrics = self.metrics.get_recent_database_metrics(self.thresholds.analysis_window_minutes)
        
        if not recent_db_metrics:
            return alerts
        
        # Check for slow queries
        slow_queries = [m for m in recent_db_metrics if m.duration_ms > self.thresholds.max_query_time_ms]
        if slow_queries:
            avg_slow_time = statistics.mean([q.duration_ms for q in slow_queries])
            alerts.append(BottleneckAlert(
                type=BottleneckType.SLOW_DATABASE,
                severity="high" if len(slow_queries) > 10 else "medium",
                message=f"Slow database queries detected",
                details={
                    "slow_query_count": len(slow_queries),
                    "avg_slow_time_ms": avg_slow_time,
                    "threshold_ms": self.thresholds.max_query_time_ms,
                    "slowest_queries": [
                        {
                            "query": q.query[:100] + "..." if len(q.query) > 100 else q.query,
                            "duration_ms": q.duration_ms,
                            "table": q.table
                        }
                        for q in sorted(slow_queries, key=lambda x: x.duration_ms, reverse=True)[:5]
                    ]
                },
                timestamp=datetime.utcnow(),
                suggested_actions=[
                    "Add database indexes",
                    "Optimize query structure",
                    "Consider query caching",
                    "Review data access patterns",
                    "Check database connection pooling"
                ]
            ))
        
        # Check for N+1 query pattern
        await self._detect_n_plus_one_queries(recent_db_metrics, alerts)
        
        return alerts
    
    async def _analyze_system_performance(self) -> List[BottleneckAlert]:
        """Analyze system resource usage for bottlenecks."""
        alerts = []
        
        try:
            health = self.metrics.get_system_health()
            
            # Check CPU usage
            if health.get("cpu_percent", 0) > self.thresholds.max_cpu_percent:
                alerts.append(BottleneckAlert(
                    type=BottleneckType.HIGH_CPU,
                    severity="critical" if health["cpu_percent"] > 90 else "high",
                    message="High CPU usage detected",
                    details={
                        "cpu_percent": health["cpu_percent"],
                        "threshold_percent": self.thresholds.max_cpu_percent
                    },
                    timestamp=datetime.utcnow(),
                    suggested_actions=[
                        "Scale horizontally",
                        "Optimize CPU-intensive operations",
                        "Review background tasks",
                        "Check for infinite loops"
                    ]
                ))
            
            # Check memory usage
            if health.get("memory_percent", 0) > self.thresholds.max_memory_percent:
                alerts.append(BottleneckAlert(
                    type=BottleneckType.HIGH_MEMORY,
                    severity="critical" if health["memory_percent"] > 95 else "high",
                    message="High memory usage detected",
                    details={
                        "memory_percent": health["memory_percent"],
                        "memory_used_mb": health.get("memory_used_mb", 0),
                        "threshold_percent": self.thresholds.max_memory_percent
                    },
                    timestamp=datetime.utcnow(),
                    suggested_actions=[
                        "Check for memory leaks",
                        "Optimize data structures",
                        "Implement memory caching limits",
                        "Scale memory resources"
                    ]
                ))
            
            # Check disk usage
            if health.get("disk_usage_percent", 0) > self.thresholds.max_disk_percent:
                alerts.append(BottleneckAlert(
                    type=BottleneckType.HIGH_DISK,
                    severity="critical" if health["disk_usage_percent"] > 95 else "high",
                    message="High disk usage detected",
                    details={
                        "disk_usage_percent": health["disk_usage_percent"],
                        "threshold_percent": self.thresholds.max_disk_percent
                    },
                    timestamp=datetime.utcnow(),
                    suggested_actions=[
                        "Clean up log files",
                        "Archive old data",
                        "Increase disk space",
                        "Implement log rotation"
                    ]
                ))
            
            # Check concurrent requests
            if health.get("active_requests", 0) > self.thresholds.max_concurrent_requests:
                alerts.append(BottleneckAlert(
                    type=BottleneckType.CONCURRENT_REQUESTS,
                    severity="high",
                    message="High concurrent request load",
                    details={
                        "active_requests": health["active_requests"],
                        "threshold": self.thresholds.max_concurrent_requests,
                        "request_rate": health.get("request_rate_per_minute", 0)
                    },
                    timestamp=datetime.utcnow(),
                    suggested_actions=[
                        "Implement request rate limiting",
                        "Scale application instances",
                        "Optimize request processing",
                        "Add load balancing"
                    ]
                ))
        
        except Exception as e:
            logger.error(f"Error analyzing system performance: {e}")
        
        return alerts
    
    async def _analyze_performance_patterns(self) -> List[BottleneckAlert]:
        """Analyze performance patterns and trends."""
        alerts = []
        
        # Check for degrading performance trends
        current_requests = self.metrics.get_recent_requests(self.thresholds.analysis_window_minutes)
        historical_requests = self.metrics.get_recent_requests(self.thresholds.trending_window_minutes)
        
        if len(current_requests) > 10 and len(historical_requests) > 20:
            current_avg = statistics.mean([r.duration_ms for r in current_requests])
            historical_avg = statistics.mean([r.duration_ms for r in historical_requests])
            
            # If current performance is 50% worse than historical
            if current_avg > historical_avg * 1.5:
                alerts.append(BottleneckAlert(
                    type=BottleneckType.HIGH_LATENCY,
                    severity="medium",
                    message="Performance degradation trend detected",
                    details={
                        "current_avg_ms": current_avg,
                        "historical_avg_ms": historical_avg,
                        "degradation_percent": ((current_avg - historical_avg) / historical_avg) * 100
                    },
                    timestamp=datetime.utcnow(),
                    suggested_actions=[
                        "Check recent deployments",
                        "Review system changes",
                        "Monitor resource usage trends",
                        "Investigate external dependencies"
                    ]
                ))
        
        return alerts
    
    async def _detect_n_plus_one_queries(self, db_metrics: List[DatabaseMetrics], alerts: List[BottleneckAlert]):
        """Detect N+1 query patterns."""
        # Group queries by time windows (1 second windows)
        time_windows = defaultdict(list)
        
        for metric in db_metrics:
            window = int(metric.timestamp.timestamp())
            time_windows[window].append(metric)
        
        for window, queries in time_windows.items():
            if len(queries) > self.thresholds.max_queries_per_request:
                # Check for similar queries (potential N+1)
                query_patterns = defaultdict(list)
                for query in queries:
                    # Simple pattern matching - group by table and operation
                    pattern = f"{query.operation}:{query.table}"
                    query_patterns[pattern].append(query)
                
                for pattern, pattern_queries in query_patterns.items():
                    if len(pattern_queries) > 5:  # More than 5 similar queries
                        alerts.append(BottleneckAlert(
                            type=BottleneckType.QUERY_N_PLUS_ONE,
                            severity="medium",
                            message=f"Potential N+1 query pattern detected",
                            details={
                                "pattern": pattern,
                                "query_count": len(pattern_queries),
                                "time_window": window,
                                "avg_duration_ms": statistics.mean([q.duration_ms for q in pattern_queries])
                            },
                            timestamp=datetime.utcnow(),
                            suggested_actions=[
                                "Use eager loading/joins",
                                "Implement query batching",
                                "Add query result caching",
                                "Review ORM relationships"
                            ]
                        ))
    
    def _add_alert(self, alert: BottleneckAlert):
        """Add an alert to the alert list."""
        self.alerts.append(alert)
        
        # Keep only the most recent alerts
        if len(self.alerts) > self.max_alerts:
            self.alerts = self.alerts[-self.max_alerts:]
        
        # Log the alert
        logger.warning(
            f"Performance alert: {alert.message}",
            extra={
                "alert_type": alert.type.value,
                "severity": alert.severity,
                "details": alert.details
            }
        )
    
    def get_recent_alerts(self, hours: int = 1) -> List[BottleneckAlert]:
        """Get alerts from the last N hours."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return [alert for alert in self.alerts if alert.timestamp >= cutoff]
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get a summary of recent alerts."""
        recent_alerts = self.get_recent_alerts(24)  # Last 24 hours
        
        if not recent_alerts:
            return {"status": "healthy", "alert_count": 0}
        
        alert_counts = defaultdict(int)
        severity_counts = defaultdict(int)
        
        for alert in recent_alerts:
            alert_counts[alert.type.value] += 1
            severity_counts[alert.severity] += 1
        
        overall_severity = "low"
        if severity_counts["critical"] > 0:
            overall_severity = "critical"
        elif severity_counts["high"] > 0:
            overall_severity = "high"
        elif severity_counts["medium"] > 0:
            overall_severity = "medium"
        
        return {
            "status": "issues_detected" if recent_alerts else "healthy",
            "overall_severity": overall_severity,
            "alert_count": len(recent_alerts),
            "alert_types": dict(alert_counts),
            "severity_breakdown": dict(severity_counts),
            "most_recent_alert": recent_alerts[-1].message if recent_alerts else None
        }
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of data."""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]


class BottleneckDetector:
    """Specialized bottleneck detection algorithms."""
    
    def __init__(self, metrics: PerformanceMetrics):
        self.metrics = metrics
    
    async def detect_resource_contention(self) -> List[Dict[str, Any]]:
        """Detect resource contention issues."""
        contentions = []
        
        # Analyze concurrent request patterns
        recent_requests = self.metrics.get_recent_requests(5)
        if not recent_requests:
            return contentions
        
        # Group by time buckets (1-second intervals)
        time_buckets = defaultdict(list)
        for req in recent_requests:
            bucket = int(req.timestamp.timestamp())
            time_buckets[bucket].append(req)
        
        # Look for time periods with high concurrency and high latency
        for bucket, requests in time_buckets.items():
            if len(requests) >= 10:  # High concurrency
                avg_latency = statistics.mean([r.duration_ms for r in requests])
                if avg_latency > 2000:  # High latency
                    contentions.append({
                        "type": "high_concurrency_latency",
                        "timestamp": bucket,
                        "concurrent_requests": len(requests),
                        "avg_latency_ms": avg_latency,
                        "affected_endpoints": list(set(f"{r.method} {r.path}" for r in requests))
                    })
        
        return contentions
    
    async def detect_memory_leaks(self) -> List[Dict[str, Any]]:
        """Detect potential memory leaks."""
        leaks = []
        
        # Analyze memory usage trends
        recent_requests = self.metrics.get_recent_requests(30)  # 30 minutes
        if len(recent_requests) < 100:
            return leaks
        
        # Group by 5-minute windows
        windows = defaultdict(list)
        for req in recent_requests:
            window = int(req.timestamp.timestamp() / 300) * 300  # 5-minute buckets
            if req.memory_delta_mb > 0:
                windows[window].append(req.memory_delta_mb)
        
        # Check for consistently increasing memory usage
        if len(windows) >= 3:
            window_avgs = []
            for window in sorted(windows.keys()):
                if windows[window]:
                    window_avgs.append(statistics.mean(windows[window]))
            
            # Simple trend detection - if each window is higher than the previous
            if len(window_avgs) >= 3:
                increasing_trend = all(
                    window_avgs[i] > window_avgs[i-1] 
                    for i in range(1, len(window_avgs))
                )
                
                if increasing_trend:
                    leaks.append({
                        "type": "memory_leak_trend",
                        "trend_data": window_avgs,
                        "avg_increase_mb": statistics.mean([
                            window_avgs[i] - window_avgs[i-1] 
                            for i in range(1, len(window_avgs))
                        ])
                    })
        
        return leaks
    
    async def detect_database_hotspots(self) -> List[Dict[str, Any]]:
        """Detect database performance hotspots."""
        hotspots = []
        
        db_metrics = self.metrics.get_recent_database_metrics(10)
        if not db_metrics:
            return hotspots
        
        # Group by table
        table_metrics = defaultdict(list)
        for metric in db_metrics:
            if metric.table:
                table_metrics[metric.table].append(metric)
        
        # Find tables with high query frequency or slow queries
        for table, metrics in table_metrics.items():
            total_time = sum(m.duration_ms for m in metrics)
            avg_time = total_time / len(metrics)
            query_count = len(metrics)
            
            if query_count > 50 or avg_time > 200:  # High frequency or slow
                hotspots.append({
                    "type": "database_hotspot",
                    "table": table,
                    "query_count": query_count,
                    "avg_duration_ms": avg_time,
                    "total_time_ms": total_time,
                    "operations": {
                        op: len([m for m in metrics if m.operation == op])
                        for op in set(m.operation for m in metrics)
                    }
                })
        
        return hotspots
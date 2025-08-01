"""
Performance metrics collection and tracking.

This module provides classes for collecting various performance metrics
including request timing, database performance, and system resource usage.
"""

import time
import psutil
import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
from contextlib import asynccontextmanager
import functools
import threading
from sqlalchemy import event
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


@dataclass
class RequestMetrics:
    """Metrics for a single request."""
    path: str
    method: str
    status_code: int
    duration_ms: float
    timestamp: datetime
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    endpoint: Optional[str] = None
    query_count: int = 0
    query_time_ms: float = 0.0
    memory_delta_mb: float = 0.0
    cpu_usage_percent: float = 0.0


@dataclass
class DatabaseMetrics:
    """Metrics for database operations."""
    query: str
    duration_ms: float
    timestamp: datetime
    tenant_id: Optional[str] = None
    table: Optional[str] = None
    operation: str = "SELECT"  # SELECT, INSERT, UPDATE, DELETE
    rows_affected: int = 0
    connection_time_ms: float = 0.0


@dataclass
class SystemMetrics:
    """System-level performance metrics."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_usage_percent: float
    active_connections: int = 0
    request_rate: float = 0.0


class PerformanceMetrics:
    """Central performance metrics collector."""
    
    def __init__(self, max_history: int = 10000):
        self.max_history = max_history
        self.request_metrics: deque = deque(maxlen=max_history)
        self.database_metrics: deque = deque(maxlen=max_history)
        self.system_metrics: deque = deque(maxlen=max_history)
        self._lock = threading.Lock()
        
        # Aggregated statistics
        self.endpoint_stats: Dict[str, List[float]] = defaultdict(list)
        self.slow_queries: List[DatabaseMetrics] = []
        self.error_counts: Dict[int, int] = defaultdict(int)
        
        # Real-time counters
        self.active_requests = 0
        self.total_requests = 0
        self.last_cleanup = datetime.utcnow()
    
    def add_request_metric(self, metric: RequestMetrics) -> None:
        """Add a request metric."""
        with self._lock:
            self.request_metrics.append(metric)
            self.endpoint_stats[f"{metric.method} {metric.path}"].append(metric.duration_ms)
            self.error_counts[metric.status_code] += 1
            self.total_requests += 1
            
            # Clean up old endpoint stats periodically
            if datetime.utcnow() - self.last_cleanup > timedelta(hours=1):
                self._cleanup_endpoint_stats()
    
    def add_database_metric(self, metric: DatabaseMetrics) -> None:
        """Add a database metric."""
        with self._lock:
            self.database_metrics.append(metric)
            
            # Track slow queries (> 100ms)
            if metric.duration_ms > 100:
                self.slow_queries.append(metric)
                # Keep only the 100 slowest queries
                if len(self.slow_queries) > 100:
                    self.slow_queries = sorted(
                        self.slow_queries, 
                        key=lambda x: x.duration_ms, 
                        reverse=True
                    )[:100]
    
    def add_system_metric(self, metric: SystemMetrics) -> None:
        """Add a system metric."""
        with self._lock:
            self.system_metrics.append(metric)
    
    def get_recent_requests(self, minutes: int = 5) -> List[RequestMetrics]:
        """Get requests from the last N minutes."""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        with self._lock:
            return [m for m in self.request_metrics if m.timestamp >= cutoff]
    
    def get_recent_database_metrics(self, minutes: int = 5) -> List[DatabaseMetrics]:
        """Get database metrics from the last N minutes."""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        with self._lock:
            return [m for m in self.database_metrics if m.timestamp >= cutoff]
    
    def get_endpoint_statistics(self, endpoint: str) -> Dict[str, Any]:
        """Get statistics for a specific endpoint."""
        with self._lock:
            durations = self.endpoint_stats.get(endpoint, [])
            if not durations:
                return {}
            
            durations = durations[-1000:]  # Last 1000 requests
            return {
                "count": len(durations),
                "avg_ms": sum(durations) / len(durations),
                "min_ms": min(durations),
                "max_ms": max(durations),
                "p50_ms": self._percentile(durations, 50),
                "p95_ms": self._percentile(durations, 95),
                "p99_ms": self._percentile(durations, 99)
            }
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get current system health metrics."""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Get recent request rate
            recent_requests = self.get_recent_requests(1)  # Last minute
            request_rate = len(recent_requests)
            
            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_mb": memory.used / 1024 / 1024,
                "disk_usage_percent": disk.percent,
                "active_requests": self.active_requests,
                "request_rate_per_minute": request_rate,
                "total_requests": self.total_requests
            }
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {}
    
    def _cleanup_endpoint_stats(self) -> None:
        """Clean up old endpoint statistics."""
        for endpoint in list(self.endpoint_stats.keys()):
            # Keep only last 1000 requests per endpoint
            self.endpoint_stats[endpoint] = self.endpoint_stats[endpoint][-1000:]
        self.last_cleanup = datetime.utcnow()
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of data."""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]


class RequestTimer:
    """Context manager for timing requests."""
    
    def __init__(self, metrics: PerformanceMetrics, path: str, method: str, 
                 tenant_id: Optional[str] = None, user_id: Optional[str] = None):
        self.metrics = metrics
        self.path = path
        self.method = method
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.start_time = 0.0
        self.start_memory = 0.0
        self.start_cpu = 0.0
        self.query_count = 0
        self.query_time = 0.0
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        try:
            process = psutil.Process()
            self.start_memory = process.memory_info().rss / 1024 / 1024  # MB
            self.start_cpu = process.cpu_percent()
        except:
            self.start_memory = 0.0
            self.start_cpu = 0.0
        
        self.metrics.active_requests += 1
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.perf_counter() - self.start_time) * 1000
        
        # Calculate resource usage
        memory_delta = 0.0
        cpu_usage = 0.0
        try:
            process = psutil.Process()
            end_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_delta = end_memory - self.start_memory
            cpu_usage = process.cpu_percent()
        except:
            pass
        
        # Determine status code
        status_code = 500 if exc_type else 200
        
        metric = RequestMetrics(
            path=self.path,
            method=self.method,
            status_code=status_code,
            duration_ms=duration_ms,
            timestamp=datetime.utcnow(),
            tenant_id=self.tenant_id,
            user_id=self.user_id,
            query_count=self.query_count,
            query_time_ms=self.query_time,
            memory_delta_mb=memory_delta,
            cpu_usage_percent=cpu_usage
        )
        
        self.metrics.add_request_metric(metric)
        self.metrics.active_requests -= 1
    
    def add_query_metrics(self, count: int, duration_ms: float):
        """Add database query metrics to this request."""
        self.query_count += count
        self.query_time += duration_ms


class DatabaseProfiler:
    """Profiles database operations."""
    
    def __init__(self, metrics: PerformanceMetrics):
        self.metrics = metrics
        self.active_queries: Dict[int, float] = {}
        self._setup_sqlalchemy_profiling()
    
    def _setup_sqlalchemy_profiling(self):
        """Set up SQLAlchemy event listeners for profiling."""
        
        @event.listens_for(Engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.perf_counter()
        
        @event.listens_for(Engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            if hasattr(context, '_query_start_time'):
                duration_ms = (time.perf_counter() - context._query_start_time) * 1000
                
                # Extract operation type
                operation = statement.strip().split()[0].upper() if statement else "UNKNOWN"
                
                # Extract table name (basic extraction)
                table = self._extract_table_name(statement)
                
                metric = DatabaseMetrics(
                    query=statement[:500],  # Truncate long queries
                    duration_ms=duration_ms,
                    timestamp=datetime.utcnow(),
                    table=table,
                    operation=operation,
                    rows_affected=cursor.rowcount if hasattr(cursor, 'rowcount') else 0
                )
                
                self.metrics.add_database_metric(metric)
    
    def _extract_table_name(self, statement: str) -> Optional[str]:
        """Extract table name from SQL statement."""
        if not statement:
            return None
        
        statement = statement.upper().strip()
        
        # Simple table extraction patterns
        patterns = [
            r'FROM\s+(\w+)',
            r'INSERT\s+INTO\s+(\w+)',
            r'UPDATE\s+(\w+)',
            r'DELETE\s+FROM\s+(\w+)'
        ]
        
        import re
        for pattern in patterns:
            match = re.search(pattern, statement)
            if match:
                return match.group(1).lower()
        
        return None
    
    @asynccontextmanager
    async def profile_query(self, query: str, tenant_id: Optional[str] = None):
        """Context manager for profiling individual queries."""
        start_time = time.perf_counter()
        try:
            yield
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            metric = DatabaseMetrics(
                query=query,
                duration_ms=duration_ms,
                timestamp=datetime.utcnow(),
                tenant_id=tenant_id
            )
            
            self.metrics.add_database_metric(metric)


def performance_monitor(func: Callable) -> Callable:
    """Decorator for monitoring function performance."""
    
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.info(
                f"Function {func.__name__} took {duration_ms:.2f}ms",
                extra={
                    "function": func.__name__,
                    "duration_ms": duration_ms,
                    "performance_monitor": True
                }
            )
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.info(
                f"Function {func.__name__} took {duration_ms:.2f}ms",
                extra={
                    "function": func.__name__,
                    "duration_ms": duration_ms,
                    "performance_monitor": True
                }
            )
    
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


# Global metrics instance
global_metrics = PerformanceMetrics()
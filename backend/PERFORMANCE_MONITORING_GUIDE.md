# 🚀 Performance Monitoring Guide

This guide provides comprehensive information about the performance monitoring system implemented in the Faithful Finances API.

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Metrics Collection](#metrics-collection)
4. [Bottleneck Detection](#bottleneck-detection)
5. [Performance Reports](#performance-reports)
6. [API Endpoints](#api-endpoints)
7. [Configuration](#configuration)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

## 🎯 Overview

The performance monitoring system provides comprehensive insights into application performance including:

- **Request Performance**: Response times, error rates, throughput
- **Database Performance**: Query execution times, slow queries, N+1 detection
- **System Resources**: CPU, memory, disk usage monitoring
- **Bottleneck Detection**: Automated identification of performance issues
- **Trend Analysis**: Performance degradation and improvement tracking
- **Real-time Alerts**: Proactive notification of performance problems

### Key Features

- 🔍 **Automatic Metrics Collection**: Zero-configuration performance tracking
- 🚨 **Intelligent Alerting**: Smart bottleneck detection with severity levels
- 📊 **Comprehensive Reports**: Detailed performance analysis and recommendations
- 🎯 **Endpoint Analysis**: Per-endpoint performance breakdown
- 💾 **Database Profiling**: SQL query performance monitoring
- 📈 **Trend Detection**: Performance degradation identification
- 🔧 **Optimization Recommendations**: Actionable improvement suggestions

## 🏗️ Architecture

### Core Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Middleware    │───▶│   Metrics       │───▶│   Monitoring    │
│   (Collection)  │    │   (Storage)     │    │   (Analysis)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Request Timer  │    │ Database        │    │ Bottleneck      │
│  DB Profiler    │    │ Profiler        │    │ Detector        │
│  System Monitor │    │ System Metrics  │    │ Alert Manager   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Data Flow

1. **Collection**: Middleware automatically captures metrics
2. **Storage**: Metrics stored in memory with configurable retention
3. **Analysis**: Background monitoring analyzes performance patterns
4. **Alerting**: Bottlenecks detected and alerts generated
5. **Reporting**: Comprehensive reports available via API

## 📊 Metrics Collection

### Request Metrics

Automatically collected for every HTTP request:

```python
@dataclass
class RequestMetrics:
    path: str                    # Request path
    method: str                  # HTTP method
    status_code: int            # Response status
    duration_ms: float          # Total request time
    timestamp: datetime         # When request occurred
    tenant_id: str             # Multi-tenant context
    user_id: str               # User context
    query_count: int           # Database queries made
    query_time_ms: float       # Total database time
    memory_delta_mb: float     # Memory usage change
    cpu_usage_percent: float   # CPU usage during request
```

### Database Metrics

Collected for all database operations:

```python
@dataclass
class DatabaseMetrics:
    query: str                  # SQL query (truncated)
    duration_ms: float         # Query execution time
    timestamp: datetime        # When query executed
    tenant_id: str            # Multi-tenant context
    table: str                # Primary table accessed
    operation: str            # SELECT, INSERT, UPDATE, DELETE
    rows_affected: int        # Number of rows affected
    connection_time_ms: float # Connection establishment time
```

### System Metrics

Real-time resource monitoring:

```python
@dataclass
class SystemMetrics:
    timestamp: datetime        # Measurement time
    cpu_percent: float        # CPU usage percentage
    memory_percent: float     # Memory usage percentage
    memory_used_mb: float     # Memory used in MB
    disk_usage_percent: float # Disk usage percentage
    active_connections: int   # Active database connections
    request_rate: float       # Requests per minute
```

## 🔍 Bottleneck Detection

### Automatic Detection

The monitoring system automatically detects various performance bottlenecks:

#### 1. High Latency Detection
- **Threshold**: Configurable average and P95 response times
- **Analysis**: Per-endpoint latency analysis
- **Severity**: Based on how much threshold is exceeded
- **Actions**: Suggests optimization strategies

#### 2. High Error Rate Detection
- **Threshold**: Configurable error percentage
- **Analysis**: Error distribution by status code
- **Severity**: Critical for >20% error rate
- **Actions**: Recommends error investigation steps

#### 3. Slow Database Queries
- **Threshold**: Configurable query execution time
- **Analysis**: Identifies slowest queries and patterns
- **Severity**: Based on frequency and duration
- **Actions**: Suggests indexing and optimization

#### 4. N+1 Query Detection
- **Pattern**: Multiple similar queries in short time window
- **Analysis**: Groups queries by table and operation
- **Severity**: Medium (performance optimization)
- **Actions**: Recommends eager loading and batching

#### 5. Resource Exhaustion
- **CPU**: High CPU usage detection
- **Memory**: High memory usage and leak detection
- **Disk**: Disk space monitoring
- **Concurrency**: High concurrent request detection

#### 6. Performance Degradation
- **Trend Analysis**: Compares current vs historical performance
- **Threshold**: >50% performance degradation
- **Severity**: Medium (investigation needed)
- **Actions**: Suggests change review and resource scaling

### Alert Severity Levels

| Severity | Description | Typical Response |
|----------|-------------|------------------|
| **Low** | Minor performance issues | Monitor and review |
| **Medium** | Noticeable performance impact | Investigate within hours |
| **High** | Significant performance degradation | Investigate within 30 minutes |
| **Critical** | Severe performance issues | Immediate attention required |

## 📈 Performance Reports

### Report Types

#### 1. Summary Report
Quick overview of system health:

```json
{
  "health_score": 85,
  "status": "good",
  "total_requests": 1247,
  "error_rate_percent": 2.1,
  "avg_response_time_ms": 234.5,
  "p95_response_time_ms": 892.1,
  "critical_alerts": 0,
  "high_alerts": 1
}
```

#### 2. Detailed Performance Report
Comprehensive analysis including:

- **Request Analysis**: Per-endpoint performance breakdown
- **Database Analysis**: Query performance and hotspots
- **System Analysis**: Resource usage trends
- **Bottleneck Analysis**: Detected issues and recommendations
- **Trend Analysis**: Performance changes over time

#### 3. Endpoint-Specific Analysis
Deep dive into specific endpoint performance:

```json
{
  "endpoint": "GET /api/transactions",
  "total_requests": 523,
  "avg_duration_ms": 189.4,
  "p95_duration_ms": 456.7,
  "error_rate_percent": 1.2,
  "avg_queries_per_request": 3.2,
  "time_series": {
    "2024-01-15T10:00:00Z": {
      "count": 45,
      "avg_ms": 178.2,
      "p95_ms": 423.1
    }
  }
}
```

### Optimization Recommendations

Reports include actionable recommendations:

- **Database Optimization**: Index suggestions, query improvements
- **Caching Strategies**: Redis caching recommendations
- **Resource Scaling**: CPU/memory scaling suggestions
- **Code Optimization**: Async processing recommendations
- **Architecture Changes**: Microservices, load balancing suggestions

## 🔌 API Endpoints

### Public Endpoints

#### GET /api/v1/performance/health
Basic performance health check:

```bash
curl https://api.faithfulfinances.com/api/v1/performance/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "system_metrics": {
    "cpu_percent": 45.2,
    "memory_percent": 62.1,
    "active_requests": 8
  },
  "performance_score": 87
}
```

#### GET /api/v1/performance/metrics
Current performance metrics:

```bash
curl "https://api.faithfulfinances.com/api/v1/performance/metrics?minutes=5"
```

### Admin Endpoints

Require admin authentication (`Authorization: Bearer <admin-token>`):

#### GET /api/v1/performance/endpoints
Endpoint performance statistics:

```bash
curl -H "Authorization: Bearer <token>" \
  "https://api.faithfulfinances.com/api/v1/performance/endpoints?top_n=10"
```

#### GET /api/v1/performance/database
Database performance metrics:

```bash
curl -H "Authorization: Bearer <token>" \
  "https://api.faithfulfinances.com/api/v1/performance/database?minutes=10"
```

#### GET /api/v1/performance/alerts
Performance alerts:

```bash
curl -H "Authorization: Bearer <token>" \
  "https://api.faithfulfinances.com/api/v1/performance/alerts?hours=24&severity=high"
```

#### GET /api/v1/performance/report
Comprehensive performance report:

```bash
curl -H "Authorization: Bearer <token>" \
  "https://api.faithfulfinances.com/api/v1/performance/report?hours=24&format=summary"
```

#### POST /api/v1/performance/analyze
Trigger immediate analysis:

```bash
curl -X POST -H "Authorization: Bearer <token>" \
  "https://api.faithfulfinances.com/api/v1/performance/analyze"
```

#### GET /api/v1/performance/analyze/endpoint/{path}
Analyze specific endpoint:

```bash
curl -H "Authorization: Bearer <token>" \
  "https://api.faithfulfinances.com/api/v1/performance/analyze/endpoint/api/transactions?method=GET&hours=24"
```

## ⚙️ Configuration

### Environment Variables

Performance monitoring can be configured through environment variables:

```bash
# Performance monitoring
PERFORMANCE_MONITORING_ENABLED=true
PERFORMANCE_METRICS_RETENTION=10000
PERFORMANCE_SLOW_REQUEST_THRESHOLD_MS=1000
PERFORMANCE_COLLECT_DETAILED_METRICS=false

# Alerting thresholds
PERFORMANCE_MAX_AVG_LATENCY_MS=1000
PERFORMANCE_MAX_P95_LATENCY_MS=2000
PERFORMANCE_MAX_ERROR_RATE_PERCENT=5
PERFORMANCE_MAX_QUERY_TIME_MS=500
PERFORMANCE_MAX_CPU_PERCENT=80
PERFORMANCE_MAX_MEMORY_PERCENT=85
```

### Custom Thresholds

Configure performance thresholds in your application:

```python
from src.performance.monitoring import PerformanceThresholds

# Custom thresholds for high-performance requirements
thresholds = PerformanceThresholds(
    max_avg_latency_ms=500.0,       # Stricter latency requirement
    max_p95_latency_ms=1000.0,      # Tighter P95 requirement
    max_error_rate_percent=2.0,     # Lower error tolerance
    max_query_time_ms=200.0,        # Faster database requirements
    max_cpu_percent=70.0,           # Conservative CPU threshold
    max_memory_percent=75.0,        # Conservative memory threshold
    analysis_window_minutes=3,      # Faster detection
    trending_window_minutes=10      # Shorter trend analysis
)
```

### Middleware Configuration

Configure performance middleware in `main.py`:

```python
# Performance monitoring middleware
app.add_middleware(
    PerformanceMiddleware,
    enabled=True,                    # Enable/disable monitoring
    track_user_metrics=True,        # Track per-user metrics
    track_tenant_metrics=True,      # Track per-tenant metrics
    exclude_paths=[                 # Paths to exclude from monitoring
        "/health",
        "/metrics",
        "/favicon.ico"
    ]
)

# Slow request logging
app.add_middleware(
    SlowRequestLogger,
    slow_threshold_ms=1000.0,       # Log requests slower than 1s
    very_slow_threshold_ms=5000.0   # Error log for requests slower than 5s
)
```

## 🎯 Best Practices

### 1. Monitoring Strategy

#### Production Monitoring
- **Enable All Metrics**: Comprehensive monitoring in production
- **Conservative Thresholds**: Set alerts to trigger before user impact
- **Regular Reviews**: Weekly performance report reviews
- **Trend Monitoring**: Watch for gradual performance degradation

#### Development Monitoring
- **Detailed Metrics**: Enable detailed collection during development
- **Performance Testing**: Regular load testing with monitoring
- **Bottleneck Identification**: Use monitoring to guide optimization
- **Baseline Establishment**: Document baseline performance metrics

### 2. Alert Management

#### Alert Response Procedures
1. **Critical Alerts**: Immediate investigation (< 15 minutes)
2. **High Alerts**: Investigation within 1 hour
3. **Medium Alerts**: Investigation within 4 hours
4. **Low Alerts**: Review during next maintenance window

#### Alert Fatigue Prevention
- **Tune Thresholds**: Adjust to reduce false positives
- **Use Trending**: Focus on performance trends vs absolute values
- **Correlate Metrics**: Look at related metrics together
- **Regular Review**: Monthly threshold review and adjustment

### 3. Performance Optimization

#### Database Optimization
```sql
-- Add indexes for slow queries identified by monitoring
CREATE INDEX CONCURRENTLY idx_transactions_user_date 
ON transactions(user_id, created_at);

-- Analyze query patterns from monitoring data
EXPLAIN ANALYZE SELECT * FROM transactions 
WHERE user_id = ? AND created_at > ?;
```

#### Caching Strategy
```python
# Cache frequently accessed data identified by monitoring
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_user_summary(user_id: str) -> dict:
    # Expensive operation identified by monitoring
    return calculate_user_financial_summary(user_id)
```

#### Async Processing
```python
# Move slow operations to background tasks
from celery import Celery

@celery.task
def process_large_transaction_import(file_path: str):
    # Time-consuming operation moved to background
    return import_transactions_from_file(file_path)
```

### 4. Resource Management

#### Memory Management
- **Monitor Memory Trends**: Watch for memory leaks
- **Implement Limits**: Set maximum memory per request
- **Use Pagination**: Avoid loading large datasets
- **Clear Caches**: Regular cache cleanup

#### CPU Optimization
- **Profile CPU Usage**: Identify CPU-intensive operations
- **Use Async/Await**: Non-blocking I/O operations
- **Optimize Algorithms**: Improve algorithmic complexity
- **Scale Horizontally**: Add more instances for CPU-bound tasks

### 5. Capacity Planning

#### Growth Planning
- **Monitor Trends**: Track growth in request volume
- **Capacity Modeling**: Predict resource needs
- **Load Testing**: Regular capacity testing
- **Auto-scaling**: Implement automatic scaling

#### Resource Allocation
- **Database Connections**: Monitor and tune connection pools
- **Memory Allocation**: Adjust memory limits based on usage
- **CPU Cores**: Scale CPU resources based on utilization
- **Storage**: Monitor and plan storage growth

## 🔧 Troubleshooting

### Common Issues

#### 1. High Latency Alerts

**Symptoms:**
- Average response time above threshold
- P95 response time significantly elevated
- User complaints about slow performance

**Investigation Steps:**
1. Check specific slow endpoints in performance dashboard
2. Review database query performance for those endpoints
3. Check system resource usage (CPU, memory)
4. Look for recent deployments or configuration changes
5. Analyze query patterns for N+1 queries

**Common Solutions:**
- Add database indexes for slow queries
- Implement caching for frequently accessed data
- Optimize expensive operations
- Scale resources if needed

#### 2. High Error Rate Alerts

**Symptoms:**
- Error rate above configured threshold
- Specific endpoints showing high error rates
- Pattern of specific HTTP status codes

**Investigation Steps:**
1. Review error logs for specific error messages
2. Check external service dependencies
3. Validate input data and validation rules
4. Check database connectivity and health
5. Review recent code changes

**Common Solutions:**
- Fix input validation issues
- Improve error handling
- Check external service configuration
- Review database schema changes

#### 3. Database Performance Issues

**Symptoms:**
- Slow query alerts
- High database response times
- N+1 query pattern detection

**Investigation Steps:**
1. Review slow query details in performance report
2. Analyze query execution plans
3. Check database resource usage
4. Review query patterns and frequency
5. Validate database indexes

**Common Solutions:**
- Add missing database indexes
- Optimize complex queries
- Implement query caching
- Use eager loading for relationships
- Consider read replicas for heavy read workloads

#### 4. Memory Issues

**Symptoms:**
- High memory usage alerts
- Memory leak trend detection
- Out of memory errors

**Investigation Steps:**
1. Review memory usage trends over time
2. Check for memory leaks in specific endpoints
3. Analyze object allocation patterns
4. Review caching strategies
5. Check for memory-intensive operations

**Common Solutions:**
- Implement memory limits
- Fix memory leaks in code
- Optimize caching strategies
- Use pagination for large datasets
- Scale memory resources

### Debugging Tools

#### 1. Performance Dashboard
Access the performance monitoring dashboard:
```bash
curl -H "Authorization: Bearer <admin-token>" \
  "https://api.faithfulfinances.com/api/v1/performance/health"
```

#### 2. Detailed Endpoint Analysis
Analyze specific problematic endpoints:
```bash
curl -H "Authorization: Bearer <admin-token>" \
  "https://api.faithfulfinances.com/api/v1/performance/analyze/endpoint/api/slow-endpoint?hours=24"
```

#### 3. Database Query Analysis
Review slow database queries:
```bash
curl -H "Authorization: Bearer <admin-token>" \
  "https://api.faithfulfinances.com/api/v1/performance/database?minutes=30&include_slow_queries=true"
```

#### 4. System Resource Monitoring
Check current system health:
```bash
curl -H "Authorization: Bearer <admin-token>" \
  "https://api.faithfulfinances.com/api/v1/performance/metrics?include_system=true"
```

### Performance Testing

#### Load Testing Script
```python
import asyncio
import aiohttp
import time

async def load_test():
    async with aiohttp.ClientSession() as session:
        start_time = time.time()
        
        # Create 100 concurrent requests
        tasks = []
        for i in range(100):
            task = session.get('https://api.faithfulfinances.com/api/v1/transactions')
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        end_time = time.time()
        
        success_count = sum(1 for r in responses if r.status == 200)
        print(f"Completed 100 requests in {end_time - start_time:.2f}s")
        print(f"Success rate: {success_count}/100")

# Run load test
asyncio.run(load_test())
```

## 📚 Additional Resources

### Documentation
- [FastAPI Performance](https://fastapi.tiangolo.com/advanced/behind-a-proxy/)
- [SQLAlchemy Performance](https://docs.sqlalchemy.org/en/14/orm/examples.html#performance)
- [Redis Caching](https://redis.io/docs/manual/performance/)

### Monitoring Tools
- [Grafana Dashboards](https://grafana.com/grafana/dashboards/)
- [Prometheus Metrics](https://prometheus.io/docs/practices/naming/)
- [APM Tools](https://docs.sentry.io/product/performance/)

### Performance Optimization
- [Database Indexing](https://use-the-index-luke.com/)
- [Async Python](https://docs.python.org/3/library/asyncio.html)
- [Caching Strategies](https://aws.amazon.com/caching/)

This comprehensive performance monitoring system ensures your Faithful Finances API maintains optimal performance while providing detailed insights for continuous improvement.
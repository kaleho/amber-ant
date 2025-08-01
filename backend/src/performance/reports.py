"""
Performance reporting and analysis tools.

This module provides comprehensive performance reporting capabilities
including trend analysis, bottleneck reports, and optimization recommendations.
"""

import asyncio
import statistics
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import json

from .metrics import PerformanceMetrics, RequestMetrics, DatabaseMetrics
from .monitoring import PerformanceMonitor, BottleneckAlert, BottleneckType


@dataclass
class PerformanceReport:
    """Comprehensive performance report."""
    report_id: str
    generated_at: datetime
    time_period: Dict[str, datetime]
    summary: Dict[str, Any]
    request_analysis: Dict[str, Any]
    database_analysis: Dict[str, Any]
    system_analysis: Dict[str, Any]
    bottlenecks: List[Dict[str, Any]]
    recommendations: List[str]
    trends: Dict[str, Any]


class PerformanceReporter:
    """Generates comprehensive performance reports."""
    
    def __init__(self, metrics: PerformanceMetrics, monitor: PerformanceMonitor):
        self.metrics = metrics
        self.monitor = monitor
    
    async def generate_report(self, 
                            hours: int = 24,
                            include_recommendations: bool = True,
                            include_trends: bool = True) -> PerformanceReport:
        """Generate a comprehensive performance report."""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        report_id = f"perf_report_{int(end_time.timestamp())}"
        
        # Get data for the time period
        requests = self._get_requests_in_period(start_time, end_time)
        db_metrics = self._get_db_metrics_in_period(start_time, end_time)
        alerts = self.monitor.get_recent_alerts(hours)
        
        # Generate report sections
        summary = await self._generate_summary(requests, db_metrics, alerts)
        request_analysis = await self._analyze_requests(requests)
        database_analysis = await self._analyze_database(db_metrics)
        system_analysis = await self._analyze_system()
        bottlenecks = await self._analyze_bottlenecks(alerts)
        
        recommendations = []
        trends = {}
        
        if include_recommendations:
            recommendations = await self._generate_recommendations(
                request_analysis, database_analysis, bottlenecks
            )
        
        if include_trends:
            trends = await self._analyze_trends(requests, db_metrics, hours)
        
        return PerformanceReport(
            report_id=report_id,
            generated_at=end_time,
            time_period={"start": start_time, "end": end_time},
            summary=summary,
            request_analysis=request_analysis,
            database_analysis=database_analysis,
            system_analysis=system_analysis,
            bottlenecks=bottlenecks,
            recommendations=recommendations,
            trends=trends
        )
    
    async def _generate_summary(self, 
                               requests: List[RequestMetrics],
                               db_metrics: List[DatabaseMetrics],
                               alerts: List[BottleneckAlert]) -> Dict[str, Any]:
        """Generate report summary."""
        if not requests:
            return {"status": "no_data", "message": "No requests in time period"}
        
        # Request summary
        total_requests = len(requests)
        error_requests = [r for r in requests if r.status_code >= 400]
        error_rate = (len(error_requests) / total_requests) * 100
        
        durations = [r.duration_ms for r in requests]
        avg_duration = statistics.mean(durations)
        p95_duration = self._percentile(durations, 95)
        p99_duration = self._percentile(durations, 99)
        
        # Database summary
        total_queries = len(db_metrics)
        slow_queries = [q for q in db_metrics if q.duration_ms > 500]
        
        # Alert summary
        critical_alerts = [a for a in alerts if a.severity == "critical"]
        high_alerts = [a for a in alerts if a.severity == "high"]
        
        # Overall health score (0-100)
        health_score = self._calculate_health_score(
            error_rate, avg_duration, len(slow_queries), len(critical_alerts)
        )
        
        return {
            "health_score": health_score,
            "status": self._get_status_from_score(health_score),
            "total_requests": total_requests,
            "error_rate_percent": error_rate,
            "avg_response_time_ms": avg_duration,
            "p95_response_time_ms": p95_duration,
            "p99_response_time_ms": p99_duration,
            "total_database_queries": total_queries,
            "slow_queries_count": len(slow_queries),
            "critical_alerts": len(critical_alerts),
            "high_alerts": len(high_alerts),
            "total_alerts": len(alerts)
        }
    
    async def _analyze_requests(self, requests: List[RequestMetrics]) -> Dict[str, Any]:
        """Analyze request performance."""
        if not requests:
            return {}
        
        # Group by endpoint
        endpoint_stats = defaultdict(list)
        for req in requests:
            endpoint = f"{req.method} {req.path}"
            endpoint_stats[endpoint].append(req)
        
        # Analyze each endpoint
        endpoints = {}
        for endpoint, endpoint_requests in endpoint_stats.items():
            durations = [r.duration_ms for r in endpoint_requests]
            errors = [r for r in endpoint_requests if r.status_code >= 400]
            
            endpoints[endpoint] = {
                "request_count": len(endpoint_requests),
                "avg_duration_ms": statistics.mean(durations),
                "p95_duration_ms": self._percentile(durations, 95),
                "error_count": len(errors),
                "error_rate_percent": (len(errors) / len(endpoint_requests)) * 100,
                "total_query_count": sum(r.query_count for r in endpoint_requests),
                "avg_queries_per_request": statistics.mean([r.query_count for r in endpoint_requests])
            }
        
        # Find top slow and error-prone endpoints
        slowest_endpoints = sorted(
            endpoints.items(),
            key=lambda x: x[1]["p95_duration_ms"],
            reverse=True
        )[:5]
        
        highest_error_endpoints = sorted(
            endpoints.items(),
            key=lambda x: x[1]["error_rate_percent"],
            reverse=True
        )[:5]
        
        most_queried_endpoints = sorted(
            endpoints.items(),
            key=lambda x: x[1]["avg_queries_per_request"],
            reverse=True
        )[:5]
        
        # Status code analysis
        status_codes = Counter(r.status_code for r in requests)
        
        # Time-based analysis
        hourly_stats = self._analyze_hourly_patterns(requests)
        
        return {
            "endpoint_count": len(endpoints),
            "endpoints": endpoints,
            "slowest_endpoints": dict(slowest_endpoints),
            "highest_error_endpoints": dict(highest_error_endpoints),
            "most_queried_endpoints": dict(most_queried_endpoints),
            "status_code_distribution": dict(status_codes),
            "hourly_patterns": hourly_stats
        }
    
    async def _analyze_database(self, db_metrics: List[DatabaseMetrics]) -> Dict[str, Any]:
        """Analyze database performance."""
        if not db_metrics:
            return {}
        
        # Overall stats
        total_queries = len(db_metrics)
        durations = [q.duration_ms for q in db_metrics]
        avg_duration = statistics.mean(durations)
        
        # Group by table
        table_stats = defaultdict(list)
        for metric in db_metrics:
            if metric.table:
                table_stats[metric.table].append(metric)
        
        # Analyze tables
        tables = {}
        for table, table_queries in table_stats.items():
            table_durations = [q.duration_ms for q in table_queries]
            operations = Counter(q.operation for q in table_queries)
            
            tables[table] = {
                "query_count": len(table_queries),
                "avg_duration_ms": statistics.mean(table_durations),
                "max_duration_ms": max(table_durations),
                "operations": dict(operations),
                "total_time_ms": sum(table_durations)
            }
        
        # Find slowest queries
        slowest_queries = sorted(
            db_metrics,
            key=lambda x: x.duration_ms,
            reverse=True
        )[:10]
        
        # Operation analysis
        operations = Counter(q.operation for q in db_metrics)
        
        return {
            "total_queries": total_queries,
            "avg_query_duration_ms": avg_duration,
            "p95_query_duration_ms": self._percentile(durations, 95),
            "slow_queries_count": len([q for q in db_metrics if q.duration_ms > 500]),
            "tables": tables,
            "slowest_queries": [
                {
                    "query": q.query[:100] + "..." if len(q.query) > 100 else q.query,
                    "duration_ms": q.duration_ms,
                    "table": q.table,
                    "operation": q.operation,
                    "timestamp": q.timestamp.isoformat()
                }
                for q in slowest_queries
            ],
            "operation_distribution": dict(operations)
        }
    
    async def _analyze_system(self) -> Dict[str, Any]:
        """Analyze system performance."""
        try:
            current_health = self.metrics.get_system_health()
            return {
                "current_metrics": current_health,
                "status": "healthy" if all(
                    current_health.get(key, 0) < threshold
                    for key, threshold in [
                        ("cpu_percent", 80),
                        ("memory_percent", 85),
                        ("disk_usage_percent", 90)
                    ]
                ) else "degraded"
            }
        except Exception:
            return {"status": "error", "message": "Could not retrieve system metrics"}
    
    async def _analyze_bottlenecks(self, alerts: List[BottleneckAlert]) -> List[Dict[str, Any]]:
        """Analyze detected bottlenecks."""
        bottlenecks = []
        
        # Group alerts by type
        alert_groups = defaultdict(list)
        for alert in alerts:
            alert_groups[alert.type].append(alert)
        
        for bottleneck_type, type_alerts in alert_groups.items():
            severity_counts = Counter(alert.severity for alert in type_alerts)
            affected_endpoints = set()
            for alert in type_alerts:
                affected_endpoints.update(alert.affected_endpoints)
            
            bottlenecks.append({
                "type": bottleneck_type.value,
                "alert_count": len(type_alerts),
                "severity_distribution": dict(severity_counts),
                "affected_endpoints": list(affected_endpoints),
                "most_recent": type_alerts[-1].timestamp.isoformat(),
                "sample_message": type_alerts[-1].message,
                "suggested_actions": type_alerts[-1].suggested_actions
            })
        
        return bottlenecks
    
    async def _generate_recommendations(self, 
                                      request_analysis: Dict[str, Any],
                                      database_analysis: Dict[str, Any],
                                      bottlenecks: List[Dict[str, Any]]) -> List[str]:
        """Generate optimization recommendations."""
        recommendations = []
        
        # Request-based recommendations
        if request_analysis:
            if request_analysis.get("slowest_endpoints"):
                recommendations.append(
                    "Optimize slow endpoints - consider caching, query optimization, or async processing"
                )
            
            if any(ep["error_rate_percent"] > 5 for ep in request_analysis.get("endpoints", {}).values()):
                recommendations.append(
                    "Investigate high error rates - check input validation and error handling"
                )
            
            if any(ep["avg_queries_per_request"] > 10 for ep in request_analysis.get("endpoints", {}).values()):
                recommendations.append(
                    "Reduce database queries per request - implement eager loading or query optimization"
                )
        
        # Database-based recommendations
        if database_analysis:
            if database_analysis.get("slow_queries_count", 0) > 0:
                recommendations.append(
                    "Add database indexes for slow queries or optimize query structure"
                )
            
            if database_analysis.get("p95_query_duration_ms", 0) > 1000:
                recommendations.append(
                    "Review database connection pooling and query optimization strategies"
                )
        
        # Bottleneck-based recommendations
        for bottleneck in bottlenecks:
            if bottleneck["type"] == "high_cpu":
                recommendations.append(
                    "Scale CPU resources or optimize CPU-intensive operations"
                )
            elif bottleneck["type"] == "high_memory":
                recommendations.append(
                    "Investigate memory leaks or implement memory optimization strategies"
                )
            elif bottleneck["type"] == "slow_database":
                recommendations.append(
                    "Optimize database queries and consider read replicas for heavy read workloads"
                )
        
        return recommendations
    
    async def _analyze_trends(self, 
                            requests: List[RequestMetrics],
                            db_metrics: List[DatabaseMetrics],
                            hours: int) -> Dict[str, Any]:
        """Analyze performance trends."""
        if not requests or hours < 2:
            return {}
        
        # Split time period in half for comparison
        mid_time = datetime.utcnow() - timedelta(hours=hours/2)
        
        early_requests = [r for r in requests if r.timestamp < mid_time]
        recent_requests = [r for r in requests if r.timestamp >= mid_time]
        
        if not early_requests or not recent_requests:
            return {}
        
        # Compare performance metrics
        early_avg = statistics.mean([r.duration_ms for r in early_requests])
        recent_avg = statistics.mean([r.duration_ms for r in recent_requests])
        
        early_error_rate = len([r for r in early_requests if r.status_code >= 400]) / len(early_requests) * 100
        recent_error_rate = len([r for r in recent_requests if r.status_code >= 400]) / len(recent_requests) * 100
        
        # Calculate trends
        latency_trend = ((recent_avg - early_avg) / early_avg) * 100 if early_avg > 0 else 0
        error_trend = recent_error_rate - early_error_rate
        
        return {
            "latency_trend_percent": latency_trend,
            "error_rate_trend_percent": error_trend,
            "early_period": {
                "avg_latency_ms": early_avg,
                "error_rate_percent": early_error_rate,
                "request_count": len(early_requests)
            },
            "recent_period": {
                "avg_latency_ms": recent_avg,
                "error_rate_percent": recent_error_rate,
                "request_count": len(recent_requests)
            },
            "trend_status": self._get_trend_status(latency_trend, error_trend)
        }
    
    def _get_requests_in_period(self, start: datetime, end: datetime) -> List[RequestMetrics]:
        """Get requests in the specified time period."""
        return [
            req for req in self.metrics.request_metrics
            if start <= req.timestamp <= end
        ]
    
    def _get_db_metrics_in_period(self, start: datetime, end: datetime) -> List[DatabaseMetrics]:
        """Get database metrics in the specified time period."""
        return [
            metric for metric in self.metrics.database_metrics
            if start <= metric.timestamp <= end
        ]
    
    def _analyze_hourly_patterns(self, requests: List[RequestMetrics]) -> Dict[str, Any]:
        """Analyze hourly request patterns."""
        hourly_counts = defaultdict(int)
        hourly_durations = defaultdict(list)
        
        for req in requests:
            hour = req.timestamp.hour
            hourly_counts[hour] += 1
            hourly_durations[hour].append(req.duration_ms)
        
        hourly_stats = {}
        for hour in range(24):
            if hour in hourly_counts:
                durations = hourly_durations[hour]
                hourly_stats[hour] = {
                    "request_count": hourly_counts[hour],
                    "avg_duration_ms": statistics.mean(durations),
                    "p95_duration_ms": self._percentile(durations, 95)
                }
            else:
                hourly_stats[hour] = {
                    "request_count": 0,
                    "avg_duration_ms": 0,
                    "p95_duration_ms": 0
                }
        
        return hourly_stats
    
    def _calculate_health_score(self, error_rate: float, avg_duration: float, 
                               slow_queries: int, critical_alerts: int) -> int:
        """Calculate overall health score (0-100)."""
        score = 100
        
        # Deduct for error rate
        if error_rate > 5:
            score -= min(30, error_rate * 2)
        
        # Deduct for high latency
        if avg_duration > 1000:
            score -= min(25, (avg_duration - 1000) / 100)
        
        # Deduct for slow queries
        if slow_queries > 0:
            score -= min(20, slow_queries)
        
        # Deduct for critical alerts
        score -= critical_alerts * 10
        
        return max(0, int(score))
    
    def _get_status_from_score(self, score: int) -> str:
        """Get status description from health score."""
        if score >= 90:
            return "excellent"
        elif score >= 80:
            return "good"
        elif score >= 70:
            return "fair"
        elif score >= 60:
            return "poor"
        else:
            return "critical"
    
    def _get_trend_status(self, latency_trend: float, error_trend: float) -> str:
        """Get trend status description."""
        if latency_trend > 20 or error_trend > 2:
            return "degrading"
        elif latency_trend < -10 and error_trend < -1:
            return "improving"
        else:
            return "stable"
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of data."""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]


class PerformanceAnalyzer:
    """Advanced performance analysis tools."""
    
    def __init__(self, metrics: PerformanceMetrics):
        self.metrics = metrics
    
    async def analyze_endpoint_performance(self, endpoint: str, hours: int = 24) -> Dict[str, Any]:
        """Analyze performance for a specific endpoint."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        endpoint_requests = [
            req for req in self.metrics.request_metrics
            if f"{req.method} {req.path}" == endpoint and req.timestamp >= cutoff
        ]
        
        if not endpoint_requests:
            return {"error": "No data found for endpoint"}
        
        durations = [r.duration_ms for r in endpoint_requests]
        error_requests = [r for r in endpoint_requests if r.status_code >= 400]
        
        # Performance percentiles
        percentiles = {}
        for p in [50, 75, 90, 95, 99]:
            percentiles[f"p{p}"] = self._percentile(durations, p)
        
        # Time series analysis (hourly buckets)
        hourly_data = defaultdict(list)
        for req in endpoint_requests:
            hour_bucket = req.timestamp.replace(minute=0, second=0, microsecond=0)
            hourly_data[hour_bucket].append(req.duration_ms)
        
        time_series = {}
        for hour, hour_durations in hourly_data.items():
            time_series[hour.isoformat()] = {
                "count": len(hour_durations),
                "avg_ms": statistics.mean(hour_durations),
                "p95_ms": self._percentile(hour_durations, 95)
            }
        
        return {
            "endpoint": endpoint,
            "analysis_period_hours": hours,
            "total_requests": len(endpoint_requests),
            "error_count": len(error_requests),
            "error_rate_percent": (len(error_requests) / len(endpoint_requests)) * 100,
            "avg_duration_ms": statistics.mean(durations),
            "min_duration_ms": min(durations),
            "max_duration_ms": max(durations),
            "std_dev_ms": statistics.stdev(durations) if len(durations) > 1 else 0,
            "percentiles": percentiles,
            "time_series": time_series,
            "avg_queries_per_request": statistics.mean([r.query_count for r in endpoint_requests]),
            "avg_query_time_ms": statistics.mean([r.query_time_ms for r in endpoint_requests])
        }
    
    async def compare_time_periods(self, hours1: int, hours2: int) -> Dict[str, Any]:
        """Compare performance between two time periods."""
        now = datetime.utcnow()
        
        # Recent period
        recent_start = now - timedelta(hours=hours1)
        recent_requests = [
            req for req in self.metrics.request_metrics
            if recent_start <= req.timestamp <= now
        ]
        
        # Historical period
        historical_end = recent_start
        historical_start = historical_end - timedelta(hours=hours2)
        historical_requests = [
            req for req in self.metrics.request_metrics
            if historical_start <= req.timestamp <= historical_end
        ]
        
        if not recent_requests or not historical_requests:
            return {"error": "Insufficient data for comparison"}
        
        def analyze_period(requests):
            durations = [r.duration_ms for r in requests]
            errors = [r for r in requests if r.status_code >= 400]
            return {
                "request_count": len(requests),
                "avg_duration_ms": statistics.mean(durations),
                "p95_duration_ms": self._percentile(durations, 95),
                "error_count": len(errors),
                "error_rate_percent": (len(errors) / len(requests)) * 100
            }
        
        recent_stats = analyze_period(recent_requests)
        historical_stats = analyze_period(historical_requests)
        
        # Calculate changes
        changes = {}
        for metric in ["avg_duration_ms", "p95_duration_ms", "error_rate_percent"]:
            if historical_stats[metric] > 0:
                change_percent = ((recent_stats[metric] - historical_stats[metric]) / 
                                historical_stats[metric]) * 100
                changes[f"{metric}_change_percent"] = change_percent
        
        return {
            "recent_period": {
                "hours": hours1,
                "stats": recent_stats
            },
            "historical_period": {
                "hours": hours2,
                "stats": historical_stats
            },
            "changes": changes,
            "overall_trend": self._determine_overall_trend(changes)
        }
    
    def _determine_overall_trend(self, changes: Dict[str, float]) -> str:
        """Determine overall performance trend."""
        latency_change = changes.get("avg_duration_ms_change_percent", 0)
        error_change = changes.get("error_rate_percent_change_percent", 0)
        
        if latency_change > 20 or error_change > 50:
            return "significantly_worse"
        elif latency_change > 10 or error_change > 20:
            return "worse"
        elif latency_change < -10 and error_change < -20:
            return "better"
        elif latency_change < -20 and error_change < -50:
            return "significantly_better"
        else:
            return "stable"
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of data."""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]


def export_report_to_json(report: PerformanceReport) -> str:
    """Export performance report to JSON format."""
    report_dict = asdict(report)
    
    # Convert datetime objects to ISO strings
    report_dict["generated_at"] = report.generated_at.isoformat()
    report_dict["time_period"]["start"] = report.time_period["start"].isoformat()
    report_dict["time_period"]["end"] = report.time_period["end"].isoformat()
    
    return json.dumps(report_dict, indent=2, default=str)
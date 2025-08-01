"""
Performance monitoring API endpoints.

This module provides REST API endpoints for accessing performance
metrics, reports, and monitoring data.
"""

import asyncio
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse

from .metrics import global_metrics
from .monitoring import PerformanceMonitor, PerformanceThresholds
from .reports import PerformanceReporter, PerformanceAnalyzer, export_report_to_json
from ..auth.dependencies import get_current_user
from ..config import settings

# Initialize performance monitoring components
performance_monitor = PerformanceMonitor(global_metrics)
performance_reporter = PerformanceReporter(global_metrics, performance_monitor)
performance_analyzer = PerformanceAnalyzer(global_metrics)

router = APIRouter(prefix="/performance", tags=["Performance Monitoring"])


async def require_admin_user(current_user: dict = Depends(get_current_user)):
    """Require admin user for performance endpoints."""
    if not current_user or current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.get("/health")
async def get_performance_health():
    """Get current performance health status."""
    try:
        health = global_metrics.get_system_health()
        alert_summary = performance_monitor.get_alert_summary()
        
        return {
            "status": "healthy" if alert_summary["status"] == "healthy" else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "system_metrics": health,
            "alerts": alert_summary,
            "performance_score": _calculate_performance_score(health, alert_summary)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving performance health: {str(e)}")


@router.get("/metrics")
async def get_current_metrics(
    include_system: bool = Query(True, description="Include system metrics"),
    include_requests: bool = Query(True, description="Include request metrics"),
    minutes: int = Query(5, ge=1, le=60, description="Time window in minutes")
):
    """Get current performance metrics."""
    try:
        metrics = {}
        
        if include_system:
            metrics["system"] = global_metrics.get_system_health()
        
        if include_requests:
            recent_requests = global_metrics.get_recent_requests(minutes)
            if recent_requests:
                durations = [r.duration_ms for r in recent_requests]
                errors = [r for r in recent_requests if r.status_code >= 400]
                
                metrics["requests"] = {
                    "total_count": len(recent_requests),
                    "error_count": len(errors),
                    "error_rate_percent": (len(errors) / len(recent_requests)) * 100,
                    "avg_duration_ms": sum(durations) / len(durations),
                    "min_duration_ms": min(durations),
                    "max_duration_ms": max(durations),
                    "p95_duration_ms": _percentile(durations, 95),
                    "active_requests": global_metrics.active_requests
                }
            else:
                metrics["requests"] = {"total_count": 0, "message": "No recent requests"}
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "time_window_minutes": minutes,
            "metrics": metrics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving metrics: {str(e)}")


@router.get("/endpoints")
async def get_endpoint_statistics(
    endpoint: Optional[str] = Query(None, description="Specific endpoint to analyze"),
    top_n: int = Query(10, ge=1, le=50, description="Number of top endpoints to return")
):
    """Get endpoint performance statistics."""
    try:
        if endpoint:
            # Get statistics for specific endpoint
            stats = global_metrics.get_endpoint_statistics(endpoint)
            if not stats:
                raise HTTPException(status_code=404, detail="Endpoint not found or no data available")
            
            return {
                "endpoint": endpoint,
                "statistics": stats,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            # Get top endpoints by various metrics
            recent_requests = global_metrics.get_recent_requests(30)  # Last 30 minutes
            if not recent_requests:
                return {"message": "No recent requests", "endpoints": []}
            
            # Group by endpoint
            endpoint_data = {}
            for req in recent_requests:
                endpoint_key = f"{req.method} {req.path}"
                if endpoint_key not in endpoint_data:
                    endpoint_data[endpoint_key] = []
                endpoint_data[endpoint_key].append(req)
            
            # Calculate statistics for each endpoint
            endpoint_stats = []
            for endpoint_key, requests in endpoint_data.items():
                durations = [r.duration_ms for r in requests]
                errors = [r for r in requests if r.status_code >= 400]
                
                endpoint_stats.append({
                    "endpoint": endpoint_key,
                    "request_count": len(requests),
                    "avg_duration_ms": sum(durations) / len(durations),
                    "p95_duration_ms": _percentile(durations, 95),
                    "error_count": len(errors),
                    "error_rate_percent": (len(errors) / len(requests)) * 100,
                    "total_query_count": sum(r.query_count for r in requests)
                })
            
            # Sort by different criteria
            slowest = sorted(endpoint_stats, key=lambda x: x["p95_duration_ms"], reverse=True)[:top_n]
            most_errors = sorted(endpoint_stats, key=lambda x: x["error_rate_percent"], reverse=True)[:top_n]
            most_requests = sorted(endpoint_stats, key=lambda x: x["request_count"], reverse=True)[:top_n]
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "time_window_minutes": 30,
                "total_endpoints": len(endpoint_stats),
                "slowest_endpoints": slowest,
                "highest_error_endpoints": most_errors,
                "most_requested_endpoints": most_requests
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving endpoint statistics: {str(e)}")


@router.get("/database")
async def get_database_metrics(
    minutes: int = Query(10, ge=1, le=60, description="Time window in minutes"),
    include_slow_queries: bool = Query(True, description="Include slow query details")
):
    """Get database performance metrics."""
    try:
        db_metrics = global_metrics.get_recent_database_metrics(minutes)
        
        if not db_metrics:
            return {
                "message": "No recent database activity",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Overall statistics
        durations = [q.duration_ms for q in db_metrics]
        slow_queries = [q for q in db_metrics if q.duration_ms > 500]
        
        # Group by table
        table_stats = {}
        for metric in db_metrics:
            if metric.table:
                if metric.table not in table_stats:
                    table_stats[metric.table] = []
                table_stats[metric.table].append(metric)
        
        # Analyze each table
        table_analysis = {}
        for table, table_queries in table_stats.items():
            table_durations = [q.duration_ms for q in table_queries]
            table_analysis[table] = {
                "query_count": len(table_queries),
                "avg_duration_ms": sum(table_durations) / len(table_durations),
                "max_duration_ms": max(table_durations),
                "total_time_ms": sum(table_durations)
            }
        
        response = {
            "timestamp": datetime.utcnow().isoformat(),
            "time_window_minutes": minutes,
            "summary": {
                "total_queries": len(db_metrics),
                "avg_duration_ms": sum(durations) / len(durations),
                "p95_duration_ms": _percentile(durations, 95),
                "slow_queries_count": len(slow_queries),
                "tables_accessed": len(table_stats)
            },
            "table_statistics": table_analysis
        }
        
        if include_slow_queries and slow_queries:
            response["slow_queries"] = [
                {
                    "query": q.query[:200] + "..." if len(q.query) > 200 else q.query,
                    "duration_ms": q.duration_ms,
                    "table": q.table,
                    "operation": q.operation,
                    "timestamp": q.timestamp.isoformat()
                }
                for q in sorted(slow_queries, key=lambda x: x.duration_ms, reverse=True)[:10]
            ]
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving database metrics: {str(e)}")


@router.get("/alerts")
async def get_performance_alerts(
    hours: int = Query(1, ge=1, le=48, description="Time window in hours"),
    severity: Optional[str] = Query(None, regex="^(low|medium|high|critical)$", description="Filter by severity")
):
    """Get performance alerts."""
    try:
        alerts = performance_monitor.get_recent_alerts(hours)
        
        if severity:
            alerts = [alert for alert in alerts if alert.severity == severity]
        
        alert_data = []
        for alert in alerts:
            alert_data.append({
                "type": alert.type.value,
                "severity": alert.severity,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "details": alert.details,
                "affected_endpoints": alert.affected_endpoints,
                "suggested_actions": alert.suggested_actions
            })
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "time_window_hours": hours,
            "total_alerts": len(alert_data),
            "alerts": alert_data,
            "summary": performance_monitor.get_alert_summary()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving alerts: {str(e)}")


@router.post("/analyze")
async def trigger_performance_analysis(current_user: dict = Depends(require_admin_user)):
    """Trigger immediate performance analysis."""
    try:
        alerts = await performance_monitor.analyze_performance()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "analysis_completed": True,
            "new_alerts_count": len(alerts),
            "new_alerts": [
                {
                    "type": alert.type.value,
                    "severity": alert.severity,
                    "message": alert.message,
                    "details": alert.details
                }
                for alert in alerts
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running performance analysis: {str(e)}")


@router.get("/report")
async def generate_performance_report(
    hours: int = Query(24, ge=1, le=168, description="Report time window in hours"),
    format: str = Query("json", regex="^(json|summary)$", description="Report format"),
    current_user: dict = Depends(require_admin_user)
):
    """Generate comprehensive performance report."""
    try:
        report = await performance_reporter.generate_report(
            hours=hours,
            include_recommendations=True,
            include_trends=True
        )
        
        if format == "summary":
            return {
                "report_id": report.report_id,
                "generated_at": report.generated_at.isoformat(),
                "time_period": {
                    "start": report.time_period["start"].isoformat(),
                    "end": report.time_period["end"].isoformat()
                },
                "summary": report.summary,
                "recommendations": report.recommendations,
                "bottleneck_count": len(report.bottlenecks),
                "trend_status": report.trends.get("trend_status", "unknown")
            }
        else:
            # Return full JSON report
            return JSONResponse(
                content=export_report_to_json(report),
                media_type="application/json"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating performance report: {str(e)}")


@router.get("/analyze/endpoint/{endpoint_path:path}")
async def analyze_specific_endpoint(
    endpoint_path: str,
    method: str = Query("GET", description="HTTP method"),
    hours: int = Query(24, ge=1, le=168, description="Analysis time window in hours"),
    current_user: dict = Depends(require_admin_user)
):
    """Analyze performance for a specific endpoint."""
    try:
        endpoint = f"{method.upper()} {endpoint_path}"
        analysis = await performance_analyzer.analyze_endpoint_performance(endpoint, hours)
        
        if "error" in analysis:
            raise HTTPException(status_code=404, detail=analysis["error"])
        
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing endpoint: {str(e)}")


@router.get("/compare")
async def compare_performance_periods(
    recent_hours: int = Query(1, ge=1, le=48, description="Recent period in hours"),
    historical_hours: int = Query(24, ge=1, le=168, description="Historical period in hours"),
    current_user: dict = Depends(require_admin_user)
):
    """Compare performance between two time periods."""
    try:
        comparison = await performance_analyzer.compare_time_periods(recent_hours, historical_hours)
        
        if "error" in comparison:
            raise HTTPException(status_code=400, detail=comparison["error"])
        
        return comparison
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error comparing performance periods: {str(e)}")


@router.get("/config")
async def get_performance_config(current_user: dict = Depends(require_admin_user)):
    """Get current performance monitoring configuration."""
    try:
        return {
            "monitoring_enabled": True,
            "metrics_retention_count": global_metrics.max_history,
            "alert_retention_count": performance_monitor.max_alerts,
            "thresholds": {
                "max_avg_latency_ms": performance_monitor.thresholds.max_avg_latency_ms,
                "max_p95_latency_ms": performance_monitor.thresholds.max_p95_latency_ms,
                "max_error_rate_percent": performance_monitor.thresholds.max_error_rate_percent,
                "max_query_time_ms": performance_monitor.thresholds.max_query_time_ms,
                "max_queries_per_request": performance_monitor.thresholds.max_queries_per_request,
                "max_cpu_percent": performance_monitor.thresholds.max_cpu_percent,
                "max_memory_percent": performance_monitor.thresholds.max_memory_percent,
                "max_concurrent_requests": performance_monitor.thresholds.max_concurrent_requests
            },
            "analysis_intervals": {
                "analysis_window_minutes": performance_monitor.thresholds.analysis_window_minutes,
                "trending_window_minutes": performance_monitor.thresholds.trending_window_minutes
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving configuration: {str(e)}")


def _calculate_performance_score(health: Dict[str, Any], alerts: Dict[str, Any]) -> int:
    """Calculate overall performance score (0-100)."""
    score = 100
    
    # Deduct for high resource usage
    cpu_usage = health.get("cpu_percent", 0)
    memory_usage = health.get("memory_percent", 0)
    
    if cpu_usage > 80:
        score -= min(20, (cpu_usage - 80) / 2)
    
    if memory_usage > 85:
        score -= min(15, (memory_usage - 85) / 3)
    
    # Deduct for alerts
    alert_severity = alerts.get("overall_severity", "low")
    if alert_severity == "critical":
        score -= 30
    elif alert_severity == "high":
        score -= 20
    elif alert_severity == "medium":
        score -= 10
    
    # Deduct for high active requests
    active_requests = health.get("active_requests", 0)
    if active_requests > 50:
        score -= min(15, active_requests - 50)
    
    return max(0, int(score))


def _percentile(data: list, percentile: int) -> float:
    """Calculate percentile of data."""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    index = int(len(sorted_data) * percentile / 100)
    return sorted_data[min(index, len(sorted_data) - 1)]
"""
Performance monitoring router for HealthMate backend.

This router provides endpoints for:
- API performance metrics
- Database performance metrics
- System resource monitoring
- Performance alerts and notifications
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import logging

from app.database import get_db
from app.utils.performance_monitoring import performance_monitor
from app.utils.rbac import require_role
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/api/summary", response_model=Dict[str, Any])
async def get_api_performance_summary(
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.HEALTHCARE_PROVIDER])),
    hours: int = 1,
    db: Session = Depends(get_db)
):
    """
    Get API performance summary for the last N hours.
    
    Args:
        hours: Number of hours to look back (default: 1)
    """
    try:
        summary = performance_monitor.get_api_performance_summary(hours=hours)
        
        return {
            "message": "API performance summary retrieved successfully",
            "data": summary,
            "hours": hours
        }
        
    except Exception as e:
        logger.error(f"Failed to get API performance summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get API performance summary: {str(e)}"
        )

@router.get("/database/summary", response_model=Dict[str, Any])
async def get_database_performance_summary(
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.HEALTHCARE_PROVIDER])),
    hours: int = 1,
    db: Session = Depends(get_db)
):
    """
    Get database performance summary for the last N hours.
    
    Args:
        hours: Number of hours to look back (default: 1)
    """
    try:
        summary = performance_monitor.get_db_performance_summary(hours=hours)
        
        return {
            "message": "Database performance summary retrieved successfully",
            "data": summary,
            "hours": hours
        }
        
    except Exception as e:
        logger.error(f"Failed to get database performance summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get database performance summary: {str(e)}"
        )

@router.get("/system/summary", response_model=Dict[str, Any])
async def get_system_performance_summary(
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.HEALTHCARE_PROVIDER])),
    hours: int = 1,
    db: Session = Depends(get_db)
):
    """
    Get system performance summary for the last N hours.
    
    Args:
        hours: Number of hours to look back (default: 1)
    """
    try:
        summary = performance_monitor.get_system_performance_summary(hours=hours)
        
        return {
            "message": "System performance summary retrieved successfully",
            "data": summary,
            "hours": hours
        }
        
    except Exception as e:
        logger.error(f"Failed to get system performance summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system performance summary: {str(e)}"
        )

@router.get("/alerts", response_model=Dict[str, Any])
async def get_performance_alerts(
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.HEALTHCARE_PROVIDER])),
    db: Session = Depends(get_db)
):
    """
    Get current performance alerts based on thresholds.
    
    Returns alerts for:
    - High API response times
    - Slow database queries
    - High system resource usage
    """
    try:
        alerts = performance_monitor.get_performance_alerts()
        
        return {
            "message": "Performance alerts retrieved successfully",
            "data": {
                "alerts": alerts,
                "total_alerts": len(alerts),
                "timestamp": performance_monitor.api_metrics[-1].timestamp.isoformat() if performance_monitor.api_metrics else None
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance alerts: {str(e)}"
        )

@router.get("/health", response_model=Dict[str, Any])
async def get_performance_health(db: Session = Depends(get_db)):
    """
    Get overall performance health status.
    
    Returns a comprehensive health check including:
    - API performance status
    - Database performance status
    - System resource status
    - Overall health score
    """
    try:
        # Get all performance summaries
        api_summary = performance_monitor.get_api_performance_summary(hours=1)
        db_summary = performance_monitor.get_db_performance_summary(hours=1)
        system_summary = performance_monitor.get_system_performance_summary(hours=1)
        alerts = performance_monitor.get_performance_alerts()
        
        # Calculate health score (0-100)
        health_score = 100
        
        # Deduct points for performance issues
        if api_summary.get("average_response_time", 0) > 1000:
            health_score -= 20
        elif api_summary.get("average_response_time", 0) > 500:
            health_score -= 10
        
        if db_summary.get("average_execution_time", 0) > 500:
            health_score -= 20
        elif db_summary.get("average_execution_time", 0) > 200:
            health_score -= 10
        
        # Check system resources
        cpu_usage = system_summary.get("metrics", {}).get("cpu_usage", {}).get("current", 0)
        memory_usage = system_summary.get("metrics", {}).get("memory_usage", {}).get("current", 0)
        
        if cpu_usage > 80:
            health_score -= 15
        elif cpu_usage > 60:
            health_score -= 5
        
        if memory_usage > 85:
            health_score -= 15
        elif memory_usage > 70:
            health_score -= 5
        
        # Deduct points for alerts
        health_score -= len(alerts) * 5
        
        # Ensure health score is between 0 and 100
        health_score = max(0, min(100, health_score))
        
        # Determine overall status
        if health_score >= 80:
            status = "healthy"
        elif health_score >= 60:
            status = "warning"
        else:
            status = "critical"
        
        return {
            "status": status,
            "health_score": health_score,
            "message": "Performance health check completed",
            "data": {
                "api_performance": {
                    "status": "healthy" if api_summary.get("average_response_time", 0) < 500 else "warning",
                    "average_response_time": api_summary.get("average_response_time", 0),
                    "error_rate": api_summary.get("error_rate", 0)
                },
                "database_performance": {
                    "status": "healthy" if db_summary.get("average_execution_time", 0) < 200 else "warning",
                    "average_execution_time": db_summary.get("average_execution_time", 0),
                    "slow_queries": db_summary.get("slow_queries", 0)
                },
                "system_resources": {
                    "cpu_usage": cpu_usage,
                    "memory_usage": memory_usage,
                    "status": "healthy" if cpu_usage < 60 and memory_usage < 70 else "warning"
                },
                "alerts": {
                    "count": len(alerts),
                    "active_alerts": alerts
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Performance health check failed: {e}")
        return {
            "status": "unknown",
            "health_score": 0,
            "message": "Performance health check failed",
            "error": str(e)
        }

@router.delete("/metrics/clear", response_model=Dict[str, Any])
async def clear_old_metrics(
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """
    Clear performance metrics older than specified hours.
    
    Args:
        hours: Clear metrics older than this many hours (default: 24)
    """
    try:
        performance_monitor.clear_old_metrics(hours=hours)
        
        return {
            "message": f"Cleared performance metrics older than {hours} hours"
        }
        
    except Exception as e:
        logger.error(f"Failed to clear old metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear old metrics: {str(e)}"
        )

@router.get("/metrics/raw", response_model=Dict[str, Any])
async def get_raw_metrics(
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    metric_type: str = "api",
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get raw performance metrics data.
    
    Args:
        metric_type: Type of metrics to retrieve (api, database, system, custom)
        limit: Maximum number of metrics to return (default: 100)
    """
    try:
        if metric_type == "api":
            metrics = list(performance_monitor.api_metrics)[-limit:]
            data = [
                {
                    "endpoint": m.endpoint,
                    "method": m.method,
                    "response_time": m.response_time,
                    "status_code": m.status_code,
                    "timestamp": m.timestamp.isoformat(),
                    "user_id": m.user_id
                }
                for m in metrics
            ]
        elif metric_type == "database":
            metrics = list(performance_monitor.db_metrics)[-limit:]
            data = [
                {
                    "query": m.query[:200] + "..." if len(m.query) > 200 else m.query,
                    "execution_time": m.execution_time,
                    "timestamp": m.timestamp.isoformat(),
                    "table_name": m.table_name,
                    "rows_affected": m.rows_affected
                }
                for m in metrics
            ]
        elif metric_type == "system":
            metrics = list(performance_monitor.system_metrics)[-limit:]
            data = [
                {
                    "name": m.name,
                    "value": m.value,
                    "unit": m.unit,
                    "timestamp": m.timestamp.isoformat()
                }
                for m in metrics
            ]
        elif metric_type == "custom":
            metrics = list(performance_monitor.custom_metrics)[-limit:]
            data = [
                {
                    "name": m.name,
                    "value": m.value,
                    "unit": m.unit,
                    "timestamp": m.timestamp.isoformat(),
                    "metadata": m.metadata
                }
                for m in metrics
            ]
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid metric type: {metric_type}. Must be one of: api, database, system, custom"
            )
        
        return {
            "message": f"Raw {metric_type} metrics retrieved successfully",
            "data": {
                "metric_type": metric_type,
                "count": len(data),
                "metrics": data
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get raw metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get raw metrics: {str(e)}"
        )

@router.post("/thresholds/update", response_model=Dict[str, Any])
async def update_performance_thresholds(
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    slow_api_threshold: Optional[int] = None,
    slow_db_threshold: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Update performance monitoring thresholds.
    
    Args:
        slow_api_threshold: New threshold for slow API calls in milliseconds
        slow_db_threshold: New threshold for slow database queries in milliseconds
    """
    try:
        if slow_api_threshold is not None:
            performance_monitor.slow_api_threshold = slow_api_threshold
        
        if slow_db_threshold is not None:
            performance_monitor.slow_db_threshold = slow_db_threshold
        
        return {
            "message": "Performance thresholds updated successfully",
            "data": {
                "slow_api_threshold": performance_monitor.slow_api_threshold,
                "slow_db_threshold": performance_monitor.slow_db_threshold
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to update performance thresholds: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update performance thresholds: {str(e)}"
        ) 
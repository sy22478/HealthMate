"""
Load Balancing Router for HealthMate Backend.

This router provides endpoints for:
- Load balancer health monitoring
- Database node management
- Auto-scaling status
- Performance metrics
- Failover management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from app.database import get_db
from app.utils.load_balancer import get_load_balancer, QueryType
from app.utils.rbac import require_role
from app.models.user import UserRole
from app.utils.performance_monitoring import performance_monitor

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/health", response_model=Dict[str, Any])
async def load_balancer_health_check():
    """
    Comprehensive health check for load balancing system.
    
    Returns:
        Health status of all load balancing components
    """
    try:
        load_balancer = get_load_balancer()
        health_status = load_balancer.get_health_status()
        
        # Add additional system health information
        system_health = {
            "load_balancer": health_status,
            "performance_metrics": performance_monitor.get_system_performance_summary(hours=1),
            "cache_status": await get_cache_health_status(),
            "celery_status": await get_celery_health_status(),
            "overall_status": "healthy"
        }
        
        # Determine overall status
        if health_status["overall_status"] == "critical":
            system_health["overall_status"] = "critical"
        elif health_status["overall_status"] == "degraded":
            system_health["overall_status"] = "degraded"
        
        logger.info("Load balancer health check completed", extra={
            "overall_status": system_health["overall_status"]
        })
        
        return system_health
        
    except Exception as e:
        logger.error(f"Load balancer health check failed: {e}")
        return {
            "overall_status": "critical",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@router.get("/nodes", response_model=Dict[str, Any])
@require_role([UserRole.ADMIN])
async def get_database_nodes():
    """
    Get information about all database nodes.
    
    Returns:
        Database node information and status
    """
    try:
        load_balancer = get_load_balancer()
        health_status = load_balancer.get_health_status()
        
        return {
            "nodes": health_status["nodes"],
            "statistics": health_status["statistics"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get database nodes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get database nodes: {str(e)}"
        )

@router.post("/nodes/{node_name}/disable", response_model=Dict[str, Any])
@require_role([UserRole.ADMIN])
async def disable_database_node(node_name: str):
    """
    Disable a database node for maintenance.
    
    Args:
        node_name: Name of the node to disable
        
    Returns:
        Operation result
    """
    try:
        load_balancer = get_load_balancer()
        
        if node_name not in load_balancer.nodes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Database node {node_name} not found"
            )
        
        # Disable the node
        load_balancer.nodes[node_name].is_active = False
        load_balancer.nodes[node_name].health_status = "maintenance"
        
        logger.info(f"Database node {node_name} disabled for maintenance")
        
        return {
            "message": f"Database node {node_name} disabled successfully",
            "node_name": node_name,
            "status": "disabled",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to disable database node {node_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disable database node: {str(e)}"
        )

@router.post("/nodes/{node_name}/enable", response_model=Dict[str, Any])
@require_role([UserRole.ADMIN])
async def enable_database_node(node_name: str):
    """
    Enable a database node after maintenance.
    
    Args:
        node_name: Name of the node to enable
        
    Returns:
        Operation result
    """
    try:
        load_balancer = get_load_balancer()
        
        if node_name not in load_balancer.nodes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Database node {node_name} not found"
            )
        
        # Enable the node
        load_balancer.nodes[node_name].is_active = True
        load_balancer.nodes[node_name].health_status = "healthy"
        
        logger.info(f"Database node {node_name} enabled")
        
        return {
            "message": f"Database node {node_name} enabled successfully",
            "node_name": node_name,
            "status": "enabled",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to enable database node {node_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enable database node: {str(e)}"
        )

@router.get("/performance", response_model=Dict[str, Any])
@require_role([UserRole.ADMIN])
async def get_load_balancer_performance():
    """
    Get performance metrics for load balancing system.
    
    Returns:
        Performance metrics and statistics
    """
    try:
        load_balancer = get_load_balancer()
        health_status = load_balancer.get_health_status()
        
        # Calculate performance metrics
        total_queries = health_status["statistics"]["total_queries"]
        failed_queries = health_status["statistics"]["failed_queries"]
        success_rate = ((total_queries - failed_queries) / total_queries * 100) if total_queries > 0 else 100
        
        # Get response times
        response_times = []
        for node_name, node_status in health_status["nodes"].items():
            if node_status["response_time_ms"]:
                response_times.append(node_status["response_time_ms"])
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        performance_metrics = {
            "query_statistics": health_status["statistics"],
            "success_rate_percentage": round(success_rate, 2),
            "average_response_time_ms": round(avg_response_time, 2),
            "active_nodes": sum(1 for node in health_status["nodes"].values() if node["is_active"]),
            "total_nodes": len(health_status["nodes"]),
            "failover_count": health_status["statistics"]["replica_failovers"] + health_status["statistics"]["primary_failovers"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return performance_metrics
        
    except Exception as e:
        logger.error(f"Failed to get load balancer performance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance metrics: {str(e)}"
        )

@router.post("/test-query", response_model=Dict[str, Any])
@require_role([UserRole.ADMIN])
async def test_database_query(
    query_type: QueryType = QueryType.READ,
    query: str = "SELECT 1 as test",
    params: Optional[Dict] = None
):
    """
    Test database query execution through load balancer.
    
    Args:
        query_type: Type of query to test
        query: SQL query to execute
        params: Query parameters
        
    Returns:
        Test result
    """
    try:
        load_balancer = get_load_balancer()
        start_time = datetime.utcnow()
        
        if query_type == QueryType.READ:
            result = load_balancer.execute_read_query(query, params)
        elif query_type == QueryType.WRITE:
            result = load_balancer.execute_write_query(query, params)
        elif query_type == QueryType.ANALYTICS:
            result = load_balancer.execute_analytics_query(query, params)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported query type: {query_type}"
            )
        
        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return {
            "query_type": query_type.value,
            "query": query,
            "params": params,
            "result": result,
            "execution_time_ms": round(execution_time, 2),
            "success": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Query test failed: {e}")
        return {
            "query_type": query_type.value,
            "query": query,
            "params": params,
            "error": str(e),
            "success": False,
            "timestamp": datetime.utcnow().isoformat()
        }

@router.get("/auto-scaling/status", response_model=Dict[str, Any])
@require_role([UserRole.ADMIN])
async def get_auto_scaling_status():
    """
    Get auto-scaling system status.
    
    Returns:
        Auto-scaling status and configuration
    """
    try:
        # This would integrate with Kubernetes HPA and other scaling systems
        # For now, we'll return a mock status
        auto_scaling_status = {
            "horizontal_pod_autoscaler": {
                "status": "active",
                "min_replicas": 3,
                "max_replicas": 20,
                "current_replicas": 3,
                "target_cpu_utilization": 70,
                "target_memory_utilization": 80
            },
            "vertical_pod_autoscaler": {
                "status": "active",
                "mode": "Auto",
                "update_policy": "Auto"
            },
            "cluster_autoscaler": {
                "status": "active",
                "min_nodes": 3,
                "max_nodes": 10,
                "current_nodes": 3,
                "utilization_threshold": 0.5
            },
            "database_replicas": {
                "status": "active",
                "min_replicas": 2,
                "max_replicas": 8,
                "current_replicas": 3,
                "auto_scaling_enabled": True
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return auto_scaling_status
        
    except Exception as e:
        logger.error(f"Failed to get auto-scaling status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get auto-scaling status: {str(e)}"
        )

@router.post("/auto-scaling/scale-up", response_model=Dict[str, Any])
@require_role([UserRole.ADMIN])
async def trigger_scale_up(component: str = "application"):
    """
    Trigger manual scale up for a component.
    
    Args:
        component: Component to scale (application, database, cache)
        
    Returns:
        Scale up operation result
    """
    try:
        # This would integrate with Kubernetes scaling APIs
        # For now, we'll return a mock response
        scale_result = {
            "component": component,
            "action": "scale_up",
            "status": "triggered",
            "message": f"Scale up triggered for {component}",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Manual scale up triggered for {component}")
        
        return scale_result
        
    except Exception as e:
        logger.error(f"Failed to trigger scale up for {component}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger scale up: {str(e)}"
        )

@router.post("/auto-scaling/scale-down", response_model=Dict[str, Any])
@require_role([UserRole.ADMIN])
async def trigger_scale_down(component: str = "application"):
    """
    Trigger manual scale down for a component.
    
    Args:
        component: Component to scale (application, database, cache)
        
    Returns:
        Scale down operation result
    """
    try:
        # This would integrate with Kubernetes scaling APIs
        # For now, we'll return a mock response
        scale_result = {
            "component": component,
            "action": "scale_down",
            "status": "triggered",
            "message": f"Scale down triggered for {component}",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Manual scale down triggered for {component}")
        
        return scale_result
        
    except Exception as e:
        logger.error(f"Failed to trigger scale down for {component}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger scale down: {str(e)}"
        )

async def get_cache_health_status() -> Dict[str, Any]:
    """Get cache health status."""
    try:
        from app.utils.cache import get_cache_manager
        cache = get_cache_manager()
        stats = cache.get_stats()
        
        return {
            "status": "healthy" if stats.get("connected", False) else "unhealthy",
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Failed to get cache health status: {e}")
        return {
            "status": "unknown",
            "error": str(e)
        }

async def get_celery_health_status() -> Dict[str, Any]:
    """Get Celery health status."""
    try:
        from app.celery_app import celery_app
        
        # Get Celery worker status
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        active = inspect.active()
        
        worker_count = len(stats) if stats else 0
        active_tasks = sum(len(tasks) for tasks in active.values()) if active else 0
        
        return {
            "status": "healthy" if worker_count > 0 else "unhealthy",
            "worker_count": worker_count,
            "active_tasks": active_tasks,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Failed to get Celery health status: {e}")
        return {
            "status": "unknown",
            "error": str(e)
        } 
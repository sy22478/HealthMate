"""
Database optimization router for HealthMate backend.

This router provides endpoints for:
- Database index management
- Query performance monitoring
- Connection pool optimization
- Database statistics and health checks
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import logging

from app.database import get_db
from app.models.database_optimization import get_db_optimizer, query_performance_monitor
from app.utils.rbac import require_role
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/indexes/create", response_model=Dict[str, Any])
async def create_database_indexes(
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """
    Create common database indexes for improved query performance.
    
    This endpoint creates indexes on frequently queried columns to improve
    database performance for common operations.
    """
    try:
        optimizer = get_db_optimizer()
        result = optimizer.create_common_indexes()
        
        logger.info("Database indexes creation requested", extra={
            "indexes_status": result
        })
        
        return {
            "message": "Database indexes creation completed",
            "status": result,
            "success": all(result.values()) if isinstance(result, dict) else False
        }
        
    except Exception as e:
        logger.error(f"Failed to create database indexes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create database indexes: {str(e)}"
        )

@router.get("/performance/summary", response_model=Dict[str, Any])
async def get_performance_summary(
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.HEALTHCARE_PROVIDER])),
    db: Session = Depends(get_db)
):
    """
    Get a summary of database query performance metrics.
    
    Returns statistics about query execution times, slow queries,
    and recent query performance.
    """
    try:
        optimizer = get_db_optimizer()
        summary = optimizer.get_performance_summary()
        
        return {
            "message": "Performance summary retrieved successfully",
            "data": summary
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance summary: {str(e)}"
        )

@router.post("/connection-pool/optimize", response_model=Dict[str, Any])
async def optimize_connection_pool(
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    pool_size: int = 10,
    max_overflow: int = 20,
    db: Session = Depends(get_db)
):
    """
    Optimize database connection pool settings.
    
    Args:
        pool_size: Number of connections to maintain in the pool
        max_overflow: Maximum number of connections that can be created beyond pool_size
    """
    try:
        optimizer = get_db_optimizer()
        success = optimizer.optimize_connection_pool(pool_size, max_overflow)
        
        if success:
            return {
                "message": "Connection pool optimized successfully",
                "pool_size": pool_size,
                "max_overflow": max_overflow
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to optimize connection pool"
            )
            
    except Exception as e:
        logger.error(f"Failed to optimize connection pool: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to optimize connection pool: {str(e)}"
        )

@router.get("/stats", response_model=Dict[str, Any])
async def get_database_stats(
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.HEALTHCARE_PROVIDER])),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive database statistics and health information.
    
    Returns information about table statistics, index usage,
    and connection information.
    """
    try:
        optimizer = get_db_optimizer()
        stats = optimizer.get_database_stats()
        
        return {
            "message": "Database statistics retrieved successfully",
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get database stats: {str(e)}"
        )

@router.post("/query/analyze", response_model=Dict[str, Any])
async def analyze_query_performance(
    query: str,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    params: Dict[str, Any] = None,
    db: Session = Depends(get_db)
):
    """
    Analyze the performance of a specific SQL query.
    
    Args:
        query: SQL query to analyze
        params: Query parameters (optional)
    """
    try:
        optimizer = get_db_optimizer()
        metrics = optimizer.analyze_query_performance(query, params)
        
        return {
            "message": "Query performance analysis completed",
            "data": {
                "query": metrics.query,
                "execution_time": metrics.execution_time,
                "timestamp": metrics.timestamp.isoformat(),
                "rows_affected": metrics.rows_affected,
                "is_slow": metrics.execution_time > 1.0
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to analyze query performance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze query performance: {str(e)}"
        )

@router.get("/health", response_model=Dict[str, Any])
async def database_health_check(db: Session = Depends(get_db)):
    """
    Perform a comprehensive database health check.
    
    This endpoint checks database connectivity, performance,
    and overall health status.
    """
    try:
        optimizer = get_db_optimizer()
        
        # Test basic connectivity
        with optimizer.engine.connect() as connection:
            connection.execute("SELECT 1")
        
        # Get performance summary
        performance = optimizer.get_performance_summary()
        
        # Get database stats
        stats = optimizer.get_database_stats()
        
        # Determine overall health
        health_status = "healthy"
        issues = []
        
        # Check for slow queries
        if performance.get("slow_queries_count", 0) > 5:
            health_status = "warning"
            issues.append("High number of slow queries detected")
        
        # Check connection count
        if stats.get("connections", {}).get("active_connections", 0) > 50:
            health_status = "warning"
            issues.append("High number of active connections")
        
        return {
            "status": health_status,
            "message": "Database health check completed",
            "issues": issues,
            "performance_summary": performance,
            "database_stats": stats
        }
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": "Database health check failed",
            "error": str(e),
            "issues": ["Database connectivity issues"]
        }

@router.delete("/performance/log", response_model=Dict[str, Any])
async def clear_performance_log(
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """
    Clear the performance log.
    
    This endpoint clears the in-memory performance log to free up memory.
    """
    try:
        optimizer = get_db_optimizer()
        optimizer.performance_log.clear()
        
        return {
            "message": "Performance log cleared successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to clear performance log: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear performance log: {str(e)}"
        ) 
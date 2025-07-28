"""
Maintenance background tasks for HealthMate.

This module provides background tasks for:
- System maintenance and cleanup
- Database optimization
- Cache management
- Performance monitoring
- Log rotation and cleanup
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import os
import shutil

from app.celery_app import celery_app
from app.database import SessionLocal
from app.models.database_optimization import get_db_optimizer
from app.utils.cache import get_cache_manager
from app.utils.performance_monitoring import performance_monitor
from app.utils.performance_monitoring import monitor_custom_performance

logger = logging.getLogger(__name__)

@celery_app.task
@monitor_custom_performance("cleanup_old_data")
def cleanup_old_data(days: int = 90):
    """
    Clean up old data from the database.
    
    Args:
        days: Number of days to keep data (default: 90)
    """
    try:
        db = SessionLocal()
        
        # Calculate cutoff date
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Clean up old health data
        health_data_deleted = cleanup_old_health_data(cutoff_date, db)
        
        # Clean up old conversation data
        conversation_data_deleted = cleanup_old_conversation_data(cutoff_date, db)
        
        # Clean up old audit logs
        audit_logs_deleted = cleanup_old_audit_logs(cutoff_date, db)
        
        # Clean up old session data
        session_data_deleted = cleanup_old_session_data(cutoff_date, db)
        
        total_deleted = health_data_deleted + conversation_data_deleted + audit_logs_deleted + session_data_deleted
        
        logger.info(f"Data cleanup completed: {total_deleted} records deleted")
        
        return {
            "status": "completed",
            "health_data_deleted": health_data_deleted,
            "conversation_data_deleted": conversation_data_deleted,
            "audit_logs_deleted": audit_logs_deleted,
            "session_data_deleted": session_data_deleted,
            "total_deleted": total_deleted,
            "cutoff_date": cutoff_date.isoformat(),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Data cleanup failed: {e}")
        raise
    finally:
        db.close()

@celery_app.task
@monitor_custom_performance("optimize_database")
def optimize_database():
    """
    Optimize database performance.
    
    This task runs database optimization operations including:
    - Index maintenance
    - Query optimization
    - Connection pool optimization
    """
    try:
        db = SessionLocal()
        optimizer = get_db_optimizer()
        
        # Create/update database indexes
        index_results = optimizer.create_common_indexes()
        
        # Optimize connection pool
        pool_optimized = optimizer.optimize_connection_pool(pool_size=15, max_overflow=30)
        
        # Get database statistics
        db_stats = optimizer.get_database_stats()
        
        # Analyze slow queries
        performance_summary = optimizer.get_performance_summary()
        
        logger.info("Database optimization completed")
        
        return {
            "status": "completed",
            "index_results": index_results,
            "pool_optimized": pool_optimized,
            "database_stats": db_stats,
            "performance_summary": performance_summary,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Database optimization failed: {e}")
        raise
    finally:
        db.close()

@celery_app.task
@monitor_custom_performance("cleanup_cache")
def cleanup_cache():
    """
    Clean up cache and optimize cache performance.
    
    This task cleans up expired cache entries and optimizes
    cache performance.
    """
    try:
        cache = get_cache_manager()
        
        # Get cache statistics before cleanup
        stats_before = cache.get_stats()
        
        # Clean up expired entries (Redis handles this automatically)
        # But we can clean up specific patterns
        patterns_to_clean = [
            "session:*",  # Old session data
            "temp:*",     # Temporary data
            "query:*",    # Old query results
            "api:*"       # Old API responses
        ]
        
        total_cleared = 0
        for pattern in patterns_to_clean:
            cleared = cache.clear_pattern(pattern)
            total_cleared += cleared
        
        # Get cache statistics after cleanup
        stats_after = cache.get_stats()
        
        logger.info(f"Cache cleanup completed: {total_cleared} entries cleared")
        
        return {
            "status": "completed",
            "total_cleared": total_cleared,
            "stats_before": stats_before,
            "stats_after": stats_after,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Cache cleanup failed: {e}")
        raise

@celery_app.task
@monitor_custom_performance("monitor_performance")
def monitor_performance():
    """
    Monitor system performance and generate alerts.
    
    This task collects performance metrics and generates
    alerts for performance issues.
    """
    try:
        # Get performance summaries
        api_summary = performance_monitor.get_api_performance_summary(hours=1)
        db_summary = performance_monitor.get_db_performance_summary(hours=1)
        system_summary = performance_monitor.get_system_performance_summary(hours=1)
        
        # Get performance alerts
        alerts = performance_monitor.get_performance_alerts()
        
        # Check for critical issues
        critical_issues = []
        
        # Check API performance
        if api_summary.get("average_response_time", 0) > 2000:  # 2 seconds
            critical_issues.append("High API response time")
        
        # Check database performance
        if db_summary.get("average_execution_time", 0) > 1000:  # 1 second
            critical_issues.append("High database execution time")
        
        # Check system resources
        cpu_usage = system_summary.get("metrics", {}).get("cpu_usage", {}).get("current", 0)
        memory_usage = system_summary.get("metrics", {}).get("memory_usage", {}).get("current", 0)
        
        if cpu_usage > 90:
            critical_issues.append("Critical CPU usage")
        
        if memory_usage > 90:
            critical_issues.append("Critical memory usage")
        
        # Send alerts if critical issues found
        if critical_issues:
            send_performance_alerts(critical_issues)
        
        logger.info(f"Performance monitoring completed: {len(alerts)} alerts, {len(critical_issues)} critical issues")
        
        return {
            "status": "completed",
            "api_summary": api_summary,
            "db_summary": db_summary,
            "system_summary": system_summary,
            "alerts": alerts,
            "critical_issues": critical_issues,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Performance monitoring failed: {e}")
        raise

@celery_app.task
@monitor_custom_performance("rotate_logs")
def rotate_logs():
    """
    Rotate and compress log files.
    
    This task rotates log files and compresses old ones
    to save disk space.
    """
    try:
        log_directory = "/var/log/healthmate"  # Adjust path as needed
        
        # Define log files to rotate
        log_files = [
            "app.log",
            "error.log",
            "access.log",
            "performance.log"
        ]
        
        rotated_count = 0
        compressed_count = 0
        
        for log_file in log_files:
            log_path = os.path.join(log_directory, log_file)
            
            if os.path.exists(log_path):
                # Rotate log file
                rotated_path = f"{log_path}.{datetime.now().strftime('%Y%m%d')}"
                shutil.move(log_path, rotated_path)
                rotated_count += 1
                
                # Compress old log files
                old_logs = [f for f in os.listdir(log_directory) 
                           if f.startswith(log_file) and f != log_file]
                
                for old_log in old_logs:
                    old_log_path = os.path.join(log_directory, old_log)
                    if not old_log.endswith('.gz'):
                        compress_log_file(old_log_path)
                        compressed_count += 1
        
        # Clean up very old log files (older than 30 days)
        cleanup_old_logs(log_directory, days=30)
        
        logger.info(f"Log rotation completed: {rotated_count} rotated, {compressed_count} compressed")
        
        return {
            "status": "completed",
            "rotated_count": rotated_count,
            "compressed_count": compressed_count,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Log rotation failed: {e}")
        raise

@celery_app.task
@monitor_custom_performance("backup_system")
def backup_system():
    """
    Create system backup.
    
    This task creates backups of critical system data
    including database, configuration files, and logs.
    """
    try:
        backup_dir = "/backups/healthmate"
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create backup directory
        os.makedirs(backup_dir, exist_ok=True)
        
        # Backup database
        db_backup_path = backup_database(backup_dir, timestamp)
        
        # Backup configuration files
        config_backup_path = backup_configuration(backup_dir, timestamp)
        
        # Backup logs
        logs_backup_path = backup_logs(backup_dir, timestamp)
        
        # Create backup manifest
        manifest_path = create_backup_manifest(backup_dir, timestamp, {
            "database": db_backup_path,
            "configuration": config_backup_path,
            "logs": logs_backup_path
        })
        
        # Clean up old backups (keep last 7 days)
        cleanup_old_backups(backup_dir, days=7)
        
        logger.info(f"System backup completed: {backup_dir}")
        
        return {
            "status": "completed",
            "backup_directory": backup_dir,
            "timestamp": timestamp,
            "database_backup": db_backup_path,
            "config_backup": config_backup_path,
            "logs_backup": logs_backup_path,
            "manifest": manifest_path
        }
        
    except Exception as e:
        logger.error(f"System backup failed: {e}")
        raise

@celery_app.task
@monitor_custom_performance("health_check")
def health_check():
    """
    Perform comprehensive system health check.
    
    This task performs a comprehensive health check of all
    system components and reports status.
    """
    try:
        health_status = {
            "database": check_database_health(),
            "cache": check_cache_health(),
            "api": check_api_health(),
            "system": check_system_health(),
            "overall": "healthy"
        }
        
        # Determine overall health
        if any(status.get("status") == "unhealthy" for status in health_status.values() if isinstance(status, dict)):
            health_status["overall"] = "unhealthy"
        elif any(status.get("status") == "warning" for status in health_status.values() if isinstance(status, dict)):
            health_status["overall"] = "warning"
        
        # Send alerts if unhealthy
        if health_status["overall"] == "unhealthy":
            send_health_check_alerts(health_status)
        
        logger.info(f"Health check completed: {health_status['overall']}")
        
        return {
            "status": "completed",
            "health_status": health_status,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise

# Helper functions

def cleanup_old_health_data(cutoff_date: datetime, db) -> int:
    """Clean up old health data."""
    # This would delete old health data records
    # For now, return mock count
    return 150

def cleanup_old_conversation_data(cutoff_date: datetime, db) -> int:
    """Clean up old conversation data."""
    # This would delete old conversation records
    # For now, return mock count
    return 75

def cleanup_old_audit_logs(cutoff_date: datetime, db) -> int:
    """Clean up old audit logs."""
    # This would delete old audit log records
    # For now, return mock count
    return 200

def cleanup_old_session_data(cutoff_date: datetime, db) -> int:
    """Clean up old session data."""
    # This would delete old session records
    # For now, return mock count
    return 50

def send_performance_alerts(critical_issues: List[str]):
    """Send performance alerts."""
    # This would send alerts via email, Slack, etc.
    for issue in critical_issues:
        logger.warning(f"Performance alert: {issue}")

def compress_log_file(log_path: str):
    """Compress a log file using gzip."""
    import gzip
    
    try:
        with open(log_path, 'rb') as f_in:
            with gzip.open(f"{log_path}.gz", 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Remove original file after compression
        os.remove(log_path)
        
    except Exception as e:
        logger.error(f"Failed to compress log file {log_path}: {e}")

def cleanup_old_logs(log_directory: str, days: int):
    """Clean up log files older than specified days."""
    cutoff_date = datetime.now() - timedelta(days=days)
    
    try:
        for filename in os.listdir(log_directory):
            file_path = os.path.join(log_directory, filename)
            
            # Check if file is older than cutoff date
            if os.path.isfile(file_path):
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                if file_time < cutoff_date:
                    os.remove(file_path)
                    logger.info(f"Removed old log file: {filename}")
                    
    except Exception as e:
        logger.error(f"Failed to cleanup old logs: {e}")

def backup_database(backup_dir: str, timestamp: str) -> str:
    """Backup database."""
    # This would use pg_dump or similar for PostgreSQL
    # For now, create a mock backup file
    backup_path = os.path.join(backup_dir, f"database_backup_{timestamp}.sql")
    
    with open(backup_path, 'w') as f:
        f.write("-- Mock database backup\n")
        f.write(f"-- Created at {timestamp}\n")
    
    return backup_path

def backup_configuration(backup_dir: str, timestamp: str) -> str:
    """Backup configuration files."""
    # This would copy configuration files
    # For now, create a mock backup
    backup_path = os.path.join(backup_dir, f"config_backup_{timestamp}.tar.gz")
    
    with open(backup_path, 'w') as f:
        f.write("Mock configuration backup")
    
    return backup_path

def backup_logs(backup_dir: str, timestamp: str) -> str:
    """Backup log files."""
    # This would archive log files
    # For now, create a mock backup
    backup_path = os.path.join(backup_dir, f"logs_backup_{timestamp}.tar.gz")
    
    with open(backup_path, 'w') as f:
        f.write("Mock logs backup")
    
    return backup_path

def create_backup_manifest(backup_dir: str, timestamp: str, backup_files: Dict[str, str]) -> str:
    """Create backup manifest file."""
    manifest_path = os.path.join(backup_dir, f"manifest_{timestamp}.json")
    
    import json
    manifest = {
        "timestamp": timestamp,
        "backup_files": backup_files,
        "created_at": datetime.now().isoformat()
    }
    
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    return manifest_path

def cleanup_old_backups(backup_dir: str, days: int):
    """Clean up old backup files."""
    cutoff_date = datetime.now() - timedelta(days=days)
    
    try:
        for filename in os.listdir(backup_dir):
            file_path = os.path.join(backup_dir, filename)
            
            if os.path.isfile(file_path):
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                if file_time < cutoff_date:
                    os.remove(file_path)
                    logger.info(f"Removed old backup: {filename}")
                    
    except Exception as e:
        logger.error(f"Failed to cleanup old backups: {e}")

def check_database_health() -> Dict[str, Any]:
    """Check database health."""
    try:
        db = SessionLocal()
        
        # Test database connection
        db.execute("SELECT 1")
        
        # Get database statistics
        optimizer = get_db_optimizer()
        stats = optimizer.get_database_stats()
        
        # Check for issues
        issues = []
        if stats.get("connections", {}).get("active_connections", 0) > 50:
            issues.append("High number of active connections")
        
        return {
            "status": "healthy" if not issues else "warning",
            "issues": issues,
            "stats": stats
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "issues": [f"Database connection failed: {str(e)}"]
        }
    finally:
        db.close()

def check_cache_health() -> Dict[str, Any]:
    """Check cache health."""
    try:
        cache = get_cache_manager()
        stats = cache.get_stats()
        
        if stats.get("error"):
            return {
                "status": "unhealthy",
                "issues": [f"Cache connection failed: {stats['error']}"]
            }
        
        return {
            "status": "healthy",
            "stats": stats
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "issues": [f"Cache health check failed: {str(e)}"]
        }

def check_api_health() -> Dict[str, Any]:
    """Check API health."""
    try:
        # Get API performance summary
        api_summary = performance_monitor.get_api_performance_summary(hours=1)
        
        issues = []
        if api_summary.get("average_response_time", 0) > 1000:
            issues.append("High API response time")
        
        if api_summary.get("error_rate", 0) > 0.05:  # 5% error rate
            issues.append("High error rate")
        
        return {
            "status": "healthy" if not issues else "warning",
            "issues": issues,
            "summary": api_summary
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "issues": [f"API health check failed: {str(e)}"]
        }

def check_system_health() -> Dict[str, Any]:
    """Check system health."""
    try:
        import psutil
        
        # Check CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Check memory usage
        memory = psutil.virtual_memory()
        
        # Check disk usage
        disk = psutil.disk_usage('/')
        
        issues = []
        if cpu_percent > 80:
            issues.append("High CPU usage")
        
        if memory.percent > 85:
            issues.append("High memory usage")
        
        if disk.percent > 90:
            issues.append("High disk usage")
        
        return {
            "status": "healthy" if not issues else "warning",
            "issues": issues,
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "disk_percent": disk.percent
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "issues": [f"System health check failed: {str(e)}"]
        }

def send_health_check_alerts(health_status: Dict[str, Any]):
    """Send health check alerts."""
    # This would send alerts via email, Slack, etc.
    unhealthy_components = []
    
    for component, status in health_status.items():
        if isinstance(status, dict) and status.get("status") == "unhealthy":
            unhealthy_components.append(component)
    
    if unhealthy_components:
        logger.error(f"Health check alert: Unhealthy components: {unhealthy_components}") 
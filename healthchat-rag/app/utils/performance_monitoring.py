"""
Performance monitoring utilities for HealthMate backend.

This module provides:
- API response time monitoring
- Database query performance tracking
- System resource monitoring
- Performance metrics collection
"""

import time
import logging
import psutil
import threading
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
from contextlib import contextmanager
from functools import wraps
import json

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Data class for storing performance metrics."""
    name: str
    value: float
    timestamp: datetime
    unit: str = "ms"
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class APIMetric:
    """Data class for storing API performance metrics."""
    endpoint: str
    method: str
    response_time: float
    status_code: int
    timestamp: datetime
    user_id: Optional[str] = None
    request_size: Optional[int] = None
    response_size: Optional[int] = None

@dataclass
class DatabaseMetric:
    """Data class for storing database performance metrics."""
    query: str
    execution_time: float
    timestamp: datetime
    table_name: Optional[str] = None
    rows_affected: Optional[int] = None
    connection_pool_size: Optional[int] = None

class PerformanceMonitor:
    """Performance monitoring and metrics collection utility."""
    
    def __init__(self, max_metrics: int = 10000):
        """
        Initialize performance monitor.
        
        Args:
            max_metrics: Maximum number of metrics to store in memory
        """
        self.max_metrics = max_metrics
        self.api_metrics: deque = deque(maxlen=max_metrics)
        self.db_metrics: deque = deque(maxlen=max_metrics)
        self.system_metrics: deque = deque(maxlen=max_metrics)
        self.custom_metrics: deque = deque(maxlen=max_metrics)
        self.lock = threading.Lock()
        
        # Performance thresholds
        self.slow_api_threshold = 1000  # ms
        self.slow_db_threshold = 500    # ms
        
        # Start system monitoring
        self._start_system_monitoring()
    
    def _start_system_monitoring(self):
        """Start background system monitoring."""
        def monitor_system():
            while True:
                try:
                    self.record_system_metrics()
                    time.sleep(60)  # Monitor every minute
                except Exception as e:
                    logger.error(f"System monitoring error: {e}")
                    time.sleep(60)
        
        monitor_thread = threading.Thread(target=monitor_system, daemon=True)
        monitor_thread.start()
    
    def record_api_metric(
        self,
        endpoint: str,
        method: str,
        response_time: float,
        status_code: int,
        user_id: Optional[str] = None,
        request_size: Optional[int] = None,
        response_size: Optional[int] = None
    ):
        """Record API performance metric."""
        metric = APIMetric(
            endpoint=endpoint,
            method=method,
            response_time=response_time,
            status_code=status_code,
            timestamp=datetime.now(),
            user_id=user_id,
            request_size=request_size,
            response_size=response_size
        )
        
        with self.lock:
            self.api_metrics.append(metric)
        
        # Log slow API calls
        if response_time > self.slow_api_threshold:
            logger.warning("Slow API call detected", extra={
                "endpoint": endpoint,
                "method": method,
                "response_time": response_time,
                "status_code": status_code,
                "user_id": user_id
            })
    
    def record_db_metric(
        self,
        query: str,
        execution_time: float,
        table_name: Optional[str] = None,
        rows_affected: Optional[int] = None,
        connection_pool_size: Optional[int] = None
    ):
        """Record database performance metric."""
        metric = DatabaseMetric(
            query=query,
            execution_time=execution_time,
            timestamp=datetime.now(),
            table_name=table_name,
            rows_affected=rows_affected,
            connection_pool_size=connection_pool_size
        )
        
        with self.lock:
            self.db_metrics.append(metric)
        
        # Log slow database queries
        if execution_time > self.slow_db_threshold:
            logger.warning("Slow database query detected", extra={
                "query": query[:200] + "..." if len(query) > 200 else query,
                "execution_time": execution_time,
                "table_name": table_name,
                "rows_affected": rows_affected
            })
    
    def record_system_metrics(self):
        """Record system resource metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Network I/O
            network = psutil.net_io_counters()
            
            metrics = [
                PerformanceMetric("cpu_usage", cpu_percent, datetime.now(), "%"),
                PerformanceMetric("memory_usage", memory.percent, datetime.now(), "%"),
                PerformanceMetric("memory_available", memory.available / (1024**3), datetime.now(), "GB"),
                PerformanceMetric("disk_usage", disk.percent, datetime.now(), "%"),
                PerformanceMetric("disk_free", disk.free / (1024**3), datetime.now(), "GB"),
                PerformanceMetric("network_bytes_sent", network.bytes_sent / (1024**2), datetime.now(), "MB"),
                PerformanceMetric("network_bytes_recv", network.bytes_recv / (1024**2), datetime.now(), "MB")
            ]
            
            with self.lock:
                for metric in metrics:
                    self.system_metrics.append(metric)
                    
        except Exception as e:
            logger.error(f"Failed to record system metrics: {e}")
    
    def record_custom_metric(self, name: str, value: float, unit: str = "ms", metadata: Optional[Dict[str, Any]] = None):
        """Record custom performance metric."""
        metric = PerformanceMetric(
            name=name,
            value=value,
            timestamp=datetime.now(),
            unit=unit,
            metadata=metadata or {}
        )
        
        with self.lock:
            self.custom_metrics.append(metric)
    
    def get_api_performance_summary(self, hours: int = 1) -> Dict[str, Any]:
        """Get API performance summary for the last N hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self.lock:
            recent_metrics = [
                m for m in self.api_metrics
                if m.timestamp >= cutoff_time
            ]
        
        if not recent_metrics:
            return {"message": "No API metrics available"}
        
        response_times = [m.response_time for m in recent_metrics]
        status_codes = [m.status_code for m in recent_metrics]
        
        # Group by endpoint
        endpoint_stats = defaultdict(list)
        for metric in recent_metrics:
            endpoint_stats[metric.endpoint].append(metric.response_time)
        
        return {
            "total_requests": len(recent_metrics),
            "average_response_time": sum(response_times) / len(response_times),
            "min_response_time": min(response_times),
            "max_response_time": max(response_times),
            "slow_requests": len([rt for rt in response_times if rt > self.slow_api_threshold]),
            "error_rate": len([sc for sc in status_codes if sc >= 400]) / len(status_codes),
            "endpoint_performance": {
                endpoint: {
                    "count": len(times),
                    "average": sum(times) / len(times),
                    "max": max(times)
                }
                for endpoint, times in endpoint_stats.items()
            }
        }
    
    def get_db_performance_summary(self, hours: int = 1) -> Dict[str, Any]:
        """Get database performance summary for the last N hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self.lock:
            recent_metrics = [
                m for m in self.db_metrics
                if m.timestamp >= cutoff_time
            ]
        
        if not recent_metrics:
            return {"message": "No database metrics available"}
        
        execution_times = [m.execution_time for m in recent_metrics]
        
        # Group by table
        table_stats = defaultdict(list)
        for metric in recent_metrics:
            if metric.table_name:
                table_stats[metric.table_name].append(metric.execution_time)
        
        return {
            "total_queries": len(recent_metrics),
            "average_execution_time": sum(execution_times) / len(execution_times),
            "min_execution_time": min(execution_times),
            "max_execution_time": max(execution_times),
            "slow_queries": len([et for et in execution_times if et > self.slow_db_threshold]),
            "table_performance": {
                table: {
                    "count": len(times),
                    "average": sum(times) / len(times),
                    "max": max(times)
                }
                for table, times in table_stats.items()
            }
        }
    
    def get_system_performance_summary(self, hours: int = 1) -> Dict[str, Any]:
        """Get system performance summary for the last N hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self.lock:
            recent_metrics = [
                m for m in self.system_metrics
                if m.timestamp >= cutoff_time
            ]
        
        if not recent_metrics:
            return {"message": "No system metrics available"}
        
        # Group by metric name
        metric_groups = defaultdict(list)
        for metric in recent_metrics:
            metric_groups[metric.name].append(metric.value)
        
        return {
            "metrics": {
                name: {
                    "current": values[-1] if values else 0,
                    "average": sum(values) / len(values) if values else 0,
                    "min": min(values) if values else 0,
                    "max": max(values) if values else 0,
                    "unit": next((m.unit for m in recent_metrics if m.name == name), "unknown")
                }
                for name, values in metric_groups.items()
            }
        }
    
    def get_performance_alerts(self) -> List[Dict[str, Any]]:
        """Get performance alerts based on thresholds."""
        alerts = []
        
        # Check API performance
        api_summary = self.get_api_performance_summary(hours=1)
        if api_summary.get("average_response_time", 0) > self.slow_api_threshold:
            alerts.append({
                "type": "api_performance",
                "severity": "warning",
                "message": f"High average API response time: {api_summary['average_response_time']:.2f}ms",
                "timestamp": datetime.now().isoformat()
            })
        
        # Check database performance
        db_summary = self.get_db_performance_summary(hours=1)
        if db_summary.get("average_execution_time", 0) > self.slow_db_threshold:
            alerts.append({
                "type": "database_performance",
                "severity": "warning",
                "message": f"High average database execution time: {db_summary['average_execution_time']:.2f}ms",
                "timestamp": datetime.now().isoformat()
            })
        
        # Check system resources
        system_summary = self.get_system_performance_summary(hours=1)
        cpu_usage = system_summary.get("metrics", {}).get("cpu_usage", {}).get("current", 0)
        memory_usage = system_summary.get("metrics", {}).get("memory_usage", {}).get("current", 0)
        
        if cpu_usage > 80:
            alerts.append({
                "type": "system_resource",
                "severity": "warning",
                "message": f"High CPU usage: {cpu_usage:.1f}%",
                "timestamp": datetime.now().isoformat()
            })
        
        if memory_usage > 85:
            alerts.append({
                "type": "system_resource",
                "severity": "warning",
                "message": f"High memory usage: {memory_usage:.1f}%",
                "timestamp": datetime.now().isoformat()
            })
        
        return alerts
    
    def clear_old_metrics(self, hours: int = 24):
        """Clear metrics older than specified hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self.lock:
            # Clear old API metrics
            self.api_metrics = deque(
                [m for m in self.api_metrics if m.timestamp >= cutoff_time],
                maxlen=self.max_metrics
            )
            
            # Clear old DB metrics
            self.db_metrics = deque(
                [m for m in self.db_metrics if m.timestamp >= cutoff_time],
                maxlen=self.max_metrics
            )
            
            # Clear old system metrics
            self.system_metrics = deque(
                [m for m in self.system_metrics if m.timestamp >= cutoff_time],
                maxlen=self.max_metrics
            )
            
            # Clear old custom metrics
            self.custom_metrics = deque(
                [m for m in self.custom_metrics if m.timestamp >= cutoff_time],
                maxlen=self.max_metrics
            )
        
        logger.info(f"Cleared metrics older than {hours} hours")

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

def monitor_api_performance():
    """Decorator to monitor API endpoint performance."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                response_time = (time.time() - start_time) * 1000  # Convert to ms
                
                # Extract endpoint info from function
                endpoint = func.__name__
                method = "GET"  # Default, could be enhanced to detect HTTP method
                
                performance_monitor.record_api_metric(
                    endpoint=endpoint,
                    method=method,
                    response_time=response_time,
                    status_code=200  # Default success
                )
                
                return result
                
            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                
                performance_monitor.record_api_metric(
                    endpoint=func.__name__,
                    method="GET",
                    response_time=response_time,
                    status_code=500  # Error
                )
                
                raise
        
        return wrapper
    return decorator

@contextmanager
def monitor_db_performance(query: str, table_name: Optional[str] = None):
    """
    Context manager to monitor database query performance.
    
    Usage:
        with monitor_db_performance("SELECT * FROM users", "users") as metrics:
            # Execute database query
            result = db.execute(query)
            metrics.rows_affected = result.rowcount
    """
    start_time = time.time()
    metrics = {"rows_affected": None}
    
    try:
        yield metrics
    finally:
        execution_time = (time.time() - start_time) * 1000  # Convert to ms
        
        performance_monitor.record_db_metric(
            query=query,
            execution_time=execution_time,
            table_name=table_name,
            rows_affected=metrics.get("rows_affected")
        )

def monitor_custom_performance(name: str, unit: str = "ms"):
    """Decorator to monitor custom function performance."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = (time.time() - start_time) * 1000
                
                performance_monitor.record_custom_metric(
                    name=name,
                    value=execution_time,
                    unit=unit
                )
                
                return result
                
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                
                performance_monitor.record_custom_metric(
                    name=f"{name}_error",
                    value=execution_time,
                    unit=unit,
                    metadata={"error": str(e)}
                )
                
                raise
        
        return wrapper
    return decorator 
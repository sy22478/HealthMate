"""
Celery configuration for HealthMate backend.

This module provides:
- Background task processing
- Job queuing for long-running operations
- Scheduled task management
- Task monitoring and error handling
"""

import os
from celery import Celery
from celery.schedules import crontab
import logging

logger = logging.getLogger(__name__)

# Get Redis URL from environment
redis_url = os.getenv("HEALTHMATE_REDIS_URL", "redis://localhost:6379/0")

# Create Celery instance
celery_app = Celery(
    "healthmate",
    broker=redis_url,
    backend=redis_url,
    include=[
        "app.tasks.health_data_tasks",
        "app.tasks.analytics_tasks",
        "app.tasks.notification_tasks",
        "app.tasks.maintenance_tasks"
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task routing
    task_routes={
        "app.tasks.health_data_tasks.*": {"queue": "health_data"},
        "app.tasks.analytics_tasks.*": {"queue": "analytics"},
        "app.tasks.notification_tasks.*": {"queue": "notifications"},
        "app.tasks.maintenance_tasks.*": {"queue": "maintenance"},
    },
    
    # Task execution
    task_always_eager=False,
    task_eager_propagates=True,
    task_ignore_result=False,
    task_store_errors_even_if_ignored=True,
    
    # Worker configuration
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    
    # Result backend
    result_expires=3600,  # 1 hour
    result_backend_transport_options={
        "master_name": "mymaster",
        "visibility_timeout": 3600,
    },
    
    # Beat schedule for periodic tasks
    beat_schedule={
        "health-data-sync": {
            "task": "app.tasks.health_data_tasks.sync_health_data",
            "schedule": crontab(minute="*/15"),  # Every 15 minutes
        },
        "analytics-computation": {
            "task": "app.tasks.analytics_tasks.compute_analytics",
            "schedule": crontab(minute="0", hour="*/2"),  # Every 2 hours
        },
        "database-cleanup": {
            "task": "app.tasks.maintenance_tasks.cleanup_old_data",
            "schedule": crontab(minute="0", hour="2"),  # Daily at 2 AM
        },
        "performance-monitoring": {
            "task": "app.tasks.maintenance_tasks.monitor_performance",
            "schedule": crontab(minute="*/5"),  # Every 5 minutes
        },
        "cache-cleanup": {
            "task": "app.tasks.maintenance_tasks.cleanup_cache",
            "schedule": crontab(minute="0", hour="*/6"),  # Every 6 hours
        },
        "notification-queue": {
            "task": "app.tasks.notification_tasks.process_notification_queue",
            "schedule": crontab(minute="*/1"),  # Every minute
        },
    },
    
    # Task retry configuration
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_remote_tracebacks=True,
    
    # Logging
    worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s] [%(task_name)s(%(task_id)s)] %(message)s",
)

# Task error handling
@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery setup."""
    logger.info(f"Request: {self.request!r}")

# Task monitoring
@celery_app.task(bind=True)
def monitor_task_execution(self, task_name, *args, **kwargs):
    """Monitor task execution and log performance metrics."""
    import time
    from app.utils.performance_monitoring import performance_monitor
    
    start_time = time.time()
    
    try:
        # Execute the actual task
        result = self.apply_async(args=args, kwargs=kwargs)
        
        execution_time = (time.time() - start_time) * 1000
        
        # Record performance metric
        performance_monitor.record_custom_metric(
            name=f"celery_task_{task_name}",
            value=execution_time,
            unit="ms",
            metadata={
                "task_id": self.request.id,
                "task_name": task_name,
                "status": "success"
            }
        )
        
        return result
        
    except Exception as e:
        execution_time = (time.time() - start_time) * 1000
        
        # Record error metric
        performance_monitor.record_custom_metric(
            name=f"celery_task_{task_name}_error",
            value=execution_time,
            unit="ms",
            metadata={
                "task_id": self.request.id,
                "task_name": task_name,
                "error": str(e),
                "status": "error"
            }
        )
        
        logger.error(f"Task {task_name} failed: {e}")
        raise

# Health check task
@celery_app.task
def health_check():
    """Health check task for monitoring Celery workers."""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "worker_count": len(celery_app.control.inspect().active())
    }

# Task queue monitoring
@celery_app.task
def monitor_queue_status():
    """Monitor queue status and report metrics."""
    try:
        inspect = celery_app.control.inspect()
        
        active_tasks = inspect.active()
        reserved_tasks = inspect.reserved()
        revoked_tasks = inspect.revoked()
        
        queue_stats = {
            "active_tasks": len(active_tasks) if active_tasks else 0,
            "reserved_tasks": len(reserved_tasks) if reserved_tasks else 0,
            "revoked_tasks": len(revoked_tasks) if revoked_tasks else 0,
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        logger.info(f"Queue status: {queue_stats}")
        return queue_stats
        
    except Exception as e:
        logger.error(f"Failed to monitor queue status: {e}")
        return {"error": str(e)}

# Task cleanup
@celery_app.task
def cleanup_completed_tasks():
    """Clean up completed tasks from result backend."""
    try:
        # Clean up tasks older than 24 hours
        celery_app.backend.cleanup()
        logger.info("Completed tasks cleanup finished")
        return {"status": "success", "message": "Tasks cleaned up"}
        
    except Exception as e:
        logger.error(f"Failed to cleanup tasks: {e}")
        return {"status": "error", "error": str(e)}

# Task retry configuration
@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def retryable_task(self, task_func, *args, **kwargs):
    """Wrapper for tasks that should be retried on failure."""
    try:
        return task_func(*args, **kwargs)
    except Exception as exc:
        logger.error(f"Task {task_func.__name__} failed, retrying: {exc}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

# Task priority configuration
@celery_app.task(bind=True, priority=10)
def high_priority_task(self, task_func, *args, **kwargs):
    """Wrapper for high priority tasks."""
    return task_func(*args, **kwargs)

@celery_app.task(bind=True, priority=5)
def medium_priority_task(self, task_func, *args, **kwargs):
    """Wrapper for medium priority tasks."""
    return task_func(*args, **kwargs)

@celery_app.task(bind=True, priority=1)
def low_priority_task(self, task_func, *args, **kwargs):
    """Wrapper for low priority tasks."""
    return task_func(*args, **kwargs)

# Task rate limiting
@celery_app.task(bind=True, rate_limit="10/m")
def rate_limited_task(self, task_func, *args, **kwargs):
    """Wrapper for rate-limited tasks (max 10 per minute)."""
    return task_func(*args, **kwargs)

# Task timeout configuration
@celery_app.task(bind=True, time_limit=300, soft_time_limit=240)
def timeout_task(self, task_func, *args, **kwargs):
    """Wrapper for tasks with timeout limits."""
    return task_func(*args, **kwargs)

# Task result caching
@celery_app.task(bind=True, cache_backend="redis")
def cached_task(self, task_func, cache_key, *args, **kwargs):
    """Wrapper for tasks with result caching."""
    from app.utils.cache import get_cache_manager
    
    cache = get_cache_manager()
    
    # Try to get from cache first
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return cached_result
    
    # Execute task and cache result
    result = task_func(*args, **kwargs)
    cache.set(cache_key, result, ttl=3600)  # Cache for 1 hour
    
    return result

# Task progress tracking
@celery_app.task(bind=True)
def progress_tracked_task(self, task_func, total_steps, *args, **kwargs):
    """Wrapper for tasks with progress tracking."""
    try:
        # Update progress to 0%
        self.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": total_steps, "status": "Starting..."}
        )
        
        # Execute task with progress updates
        result = task_func(self, total_steps, *args, **kwargs)
        
        # Update progress to 100%
        self.update_state(
            state="SUCCESS",
            meta={"current": total_steps, "total": total_steps, "status": "Completed"}
        )
        
        return result
        
    except Exception as e:
        self.update_state(
            state="FAILURE",
            meta={"current": 0, "total": total_steps, "status": f"Failed: {str(e)}"}
        )
        raise

# Task chaining
@celery_app.task
def chain_tasks(*task_signatures):
    """Chain multiple tasks together."""
    from celery import chain
    
    task_chain = chain(*task_signatures)
    return task_chain.apply_async()

# Task grouping
@celery_app.task
def group_tasks(*task_signatures):
    """Group multiple tasks for parallel execution."""
    from celery import group
    
    task_group = group(*task_signatures)
    return task_group.apply_async()

# Task chord (group with callback)
@celery_app.task
def chord_tasks(header_tasks, callback_task):
    """Execute header tasks in parallel, then callback when all complete."""
    from celery import chord
    
    task_chord = chord(header_tasks, callback_task)
    return task_chord.apply_async()

# Task monitoring and alerting
@celery_app.task
def monitor_task_health():
    """Monitor overall task health and send alerts if needed."""
    try:
        inspect = celery_app.control.inspect()
        
        # Check worker status
        stats = inspect.stats()
        active = inspect.active()
        reserved = inspect.reserved()
        
        # Calculate health metrics
        total_workers = len(stats) if stats else 0
        total_active_tasks = sum(len(tasks) for tasks in active.values()) if active else 0
        total_reserved_tasks = sum(len(tasks) for tasks in reserved.values()) if reserved else 0
        
        health_status = {
            "workers": total_workers,
            "active_tasks": total_active_tasks,
            "reserved_tasks": total_reserved_tasks,
            "status": "healthy" if total_workers > 0 else "unhealthy",
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        # Send alert if unhealthy
        if health_status["status"] == "unhealthy":
            logger.warning("Celery worker health check failed")
            # Here you would send an alert (email, Slack, etc.)
        
        return health_status
        
    except Exception as e:
        logger.error(f"Task health monitoring failed: {e}")
        return {"status": "error", "error": str(e)} 
"""
Backup and Disaster Recovery API Router

This module provides API endpoints for backup and disaster recovery operations.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from app.config import Settings
from app.services.backup_service import BackupService
from app.services.disaster_recovery_service import DisasterRecoveryService
from app.tasks.backup_disaster_recovery_tasks import (
    create_database_backup,
    create_file_backup,
    cleanup_old_backups,
    perform_health_checks,
    initiate_automated_failover,
    execute_disaster_recovery,
    restore_from_backup,
    setup_system_redundancy,
    track_recovery_objectives,
    get_disaster_recovery_status,
    verify_backup_integrity,
    test_disaster_recovery_procedure,
    backup_health_monitor
)
from app.exceptions.database_exceptions import DatabaseBackupError
from app.exceptions.external_api_exceptions import InfrastructureError
from app.utils.auth_middleware import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/backup-dr", tags=["Backup & Disaster Recovery"])


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()


def get_backup_service(settings: Settings = Depends(get_settings)) -> BackupService:
    """Get backup service instance."""
    return BackupService(settings)


def get_dr_service(settings: Settings = Depends(get_settings)) -> DisasterRecoveryService:
    """Get disaster recovery service instance."""
    return DisasterRecoveryService(settings)


# Backup Management Endpoints

@router.post("/backups/database", response_model=Dict[str, Any])
async def create_database_backup_endpoint(
    backup_type: str = Query("full", description="Type of backup to create"),
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user)
):
    """
    Create a database backup.
    
    Args:
        backup_type: Type of backup (full, incremental, differential)
        background_tasks: Background tasks for async processing
        current_user: Current authenticated user
        
    Returns:
        Dict containing backup task information
    """
    try:
        # Start backup task in background
        task = create_database_backup.delay(backup_type)
        
        return {
            "task_id": task.id,
            "status": "started",
            "backup_type": backup_type,
            "started_at": datetime.utcnow().isoformat(),
            "message": "Database backup task started"
        }
        
    except Exception as e:
        logger.error(f"Failed to start database backup: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start database backup: {str(e)}")


@router.post("/backups/files", response_model=Dict[str, Any])
async def create_file_backup_endpoint(
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user)
):
    """
    Create a file backup.
    
    Args:
        background_tasks: Background tasks for async processing
        current_user: Current authenticated user
        
    Returns:
        Dict containing backup task information
    """
    try:
        # Start file backup task in background
        task = create_file_backup.delay()
        
        return {
            "task_id": task.id,
            "status": "started",
            "backup_type": "file",
            "started_at": datetime.utcnow().isoformat(),
            "message": "File backup task started"
        }
        
    except Exception as e:
        logger.error(f"Failed to start file backup: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start file backup: {str(e)}")


@router.get("/backups", response_model=List[Dict[str, Any]])
async def list_backups(
    backup_type: Optional[str] = Query(None, description="Filter by backup type"),
    backup_service: BackupService = Depends(get_backup_service),
    current_user: User = Depends(get_current_user)
):
    """
    List available backups.
    
    Args:
        backup_type: Filter by backup type
        backup_service: Backup service instance
        current_user: Current authenticated user
        
    Returns:
        List of backup metadata
    """
    try:
        backups = await backup_service.list_backups(backup_type)
        return backups
        
    except Exception as e:
        logger.error(f"Failed to list backups: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list backups: {str(e)}")


@router.get("/backups/status", response_model=Dict[str, Any])
async def get_backup_status(
    backup_service: BackupService = Depends(get_backup_service),
    current_user: User = Depends(get_current_user)
):
    """
    Get backup status and statistics.
    
    Args:
        backup_service: Backup service instance
        current_user: Current authenticated user
        
    Returns:
        Dict containing backup status information
    """
    try:
        status = await backup_service.get_backup_status()
        return status
        
    except Exception as e:
        logger.error(f"Failed to get backup status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get backup status: {str(e)}")


@router.post("/backups/{backup_id}/restore", response_model=Dict[str, Any])
async def restore_backup_endpoint(
    backup_id: str,
    restore_type: str = Query("full", description="Type of restore"),
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user)
):
    """
    Restore from backup.
    
    Args:
        backup_id: ID of backup to restore from
        restore_type: Type of restore
        background_tasks: Background tasks for async processing
        current_user: Current authenticated user
        
    Returns:
        Dict containing restore task information
    """
    try:
        # Start restore task in background
        task = restore_from_backup.delay(backup_id, restore_type)
        
        return {
            "task_id": task.id,
            "status": "started",
            "backup_id": backup_id,
            "restore_type": restore_type,
            "started_at": datetime.utcnow().isoformat(),
            "message": "Backup restore task started"
        }
        
    except Exception as e:
        logger.error(f"Failed to start backup restore: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start backup restore: {str(e)}")


@router.post("/backups/{backup_id}/verify", response_model=Dict[str, Any])
async def verify_backup_integrity_endpoint(
    backup_id: str,
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user)
):
    """
    Verify backup integrity.
    
    Args:
        backup_id: ID of backup to verify
        background_tasks: Background tasks for async processing
        current_user: Current authenticated user
        
    Returns:
        Dict containing verification task information
    """
    try:
        # Start verification task in background
        task = verify_backup_integrity.delay(backup_id)
        
        return {
            "task_id": task.id,
            "status": "started",
            "backup_id": backup_id,
            "started_at": datetime.utcnow().isoformat(),
            "message": "Backup integrity verification task started"
        }
        
    except Exception as e:
        logger.error(f"Failed to start backup verification: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start backup verification: {str(e)}")


@router.post("/backups/cleanup", response_model=Dict[str, Any])
async def cleanup_old_backups_endpoint(
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user)
):
    """
    Clean up old backups based on retention policy.
    
    Args:
        background_tasks: Background tasks for async processing
        current_user: Current authenticated user
        
    Returns:
        Dict containing cleanup task information
    """
    try:
        # Start cleanup task in background
        task = cleanup_old_backups.delay()
        
        return {
            "task_id": task.id,
            "status": "started",
            "started_at": datetime.utcnow().isoformat(),
            "message": "Backup cleanup task started"
        }
        
    except Exception as e:
        logger.error(f"Failed to start backup cleanup: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start backup cleanup: {str(e)}")


# Disaster Recovery Endpoints

@router.get("/health", response_model=Dict[str, Any])
async def perform_health_checks_endpoint(
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user)
):
    """
    Perform system health checks.
    
    Args:
        background_tasks: Background tasks for async processing
        current_user: Current authenticated user
        
    Returns:
        Dict containing health check results
    """
    try:
        # Start health checks task in background
        task = perform_health_checks.delay()
        
        return {
            "task_id": task.id,
            "status": "started",
            "started_at": datetime.utcnow().isoformat(),
            "message": "Health checks task started"
        }
        
    except Exception as e:
        logger.error(f"Failed to start health checks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start health checks: {str(e)}")


@router.post("/failover", response_model=Dict[str, Any])
async def initiate_failover_endpoint(
    component: str = Query(..., description="Component to failover"),
    reason: str = Query(..., description="Reason for failover"),
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user)
):
    """
    Initiate automated failover.
    
    Args:
        component: Component to failover
        reason: Reason for failover
        background_tasks: Background tasks for async processing
        current_user: Current authenticated user
        
    Returns:
        Dict containing failover task information
    """
    try:
        # Start failover task in background
        task = initiate_automated_failover.delay(component, reason)
        
        return {
            "task_id": task.id,
            "status": "started",
            "component": component,
            "reason": reason,
            "started_at": datetime.utcnow().isoformat(),
            "message": "Failover task started"
        }
        
    except Exception as e:
        logger.error(f"Failed to start failover: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start failover: {str(e)}")


@router.post("/recovery", response_model=Dict[str, Any])
async def execute_disaster_recovery_endpoint(
    scenario: str = Query(..., description="Disaster scenario to recover from"),
    automated: bool = Query(True, description="Whether to execute automatically"),
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user)
):
    """
    Execute disaster recovery procedure.
    
    Args:
        scenario: Disaster scenario to recover from
        automated: Whether to execute automatically
        background_tasks: Background tasks for async processing
        current_user: Current authenticated user
        
    Returns:
        Dict containing recovery task information
    """
    try:
        # Start recovery task in background
        task = execute_disaster_recovery.delay(scenario, automated)
        
        return {
            "task_id": task.id,
            "status": "started",
            "scenario": scenario,
            "automated": automated,
            "started_at": datetime.utcnow().isoformat(),
            "message": "Disaster recovery task started"
        }
        
    except Exception as e:
        logger.error(f"Failed to start disaster recovery: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start disaster recovery: {str(e)}")


@router.post("/redundancy/setup", response_model=Dict[str, Any])
async def setup_system_redundancy_endpoint(
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user)
):
    """
    Setup system redundancy.
    
    Args:
        background_tasks: Background tasks for async processing
        current_user: Current authenticated user
        
    Returns:
        Dict containing redundancy setup task information
    """
    try:
        # Start redundancy setup task in background
        task = setup_system_redundancy.delay()
        
        return {
            "task_id": task.id,
            "status": "started",
            "started_at": datetime.utcnow().isoformat(),
            "message": "System redundancy setup task started"
        }
        
    except Exception as e:
        logger.error(f"Failed to start redundancy setup: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start redundancy setup: {str(e)}")


@router.get("/recovery-objectives", response_model=Dict[str, Any])
async def track_recovery_objectives_endpoint(
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user)
):
    """
    Track recovery time and point objectives.
    
    Args:
        background_tasks: Background tasks for async processing
        current_user: Current authenticated user
        
    Returns:
        Dict containing RTO/RPO tracking information
    """
    try:
        # Start tracking task in background
        task = track_recovery_objectives.delay()
        
        return {
            "task_id": task.id,
            "status": "started",
            "started_at": datetime.utcnow().isoformat(),
            "message": "Recovery objectives tracking task started"
        }
        
    except Exception as e:
        logger.error(f"Failed to start recovery objectives tracking: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start recovery objectives tracking: {str(e)}")


@router.get("/status", response_model=Dict[str, Any])
async def get_disaster_recovery_status_endpoint(
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user)
):
    """
    Get disaster recovery status.
    
    Args:
        background_tasks: Background tasks for async processing
        current_user: Current authenticated user
        
    Returns:
        Dict containing disaster recovery status
    """
    try:
        # Start status task in background
        task = get_disaster_recovery_status.delay()
        
        return {
            "task_id": task.id,
            "status": "started",
            "started_at": datetime.utcnow().isoformat(),
            "message": "Disaster recovery status task started"
        }
        
    except Exception as e:
        logger.error(f"Failed to start disaster recovery status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start disaster recovery status: {str(e)}")


@router.post("/test", response_model=Dict[str, Any])
async def test_disaster_recovery_procedure_endpoint(
    scenario: str = Query(..., description="Disaster scenario to test"),
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user)
):
    """
    Test disaster recovery procedure.
    
    Args:
        scenario: Disaster scenario to test
        background_tasks: Background tasks for async processing
        current_user: Current authenticated user
        
    Returns:
        Dict containing test task information
    """
    try:
        # Start test task in background
        task = test_disaster_recovery_procedure.delay(scenario)
        
        return {
            "task_id": task.id,
            "status": "started",
            "scenario": scenario,
            "started_at": datetime.utcnow().isoformat(),
            "message": "Disaster recovery test task started"
        }
        
    except Exception as e:
        logger.error(f"Failed to start disaster recovery test: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start disaster recovery test: {str(e)}")


@router.get("/monitor", response_model=Dict[str, Any])
async def backup_health_monitor_endpoint(
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user)
):
    """
    Monitor backup health and trigger alerts if needed.
    
    Args:
        background_tasks: Background tasks for async processing
        current_user: Current authenticated user
        
    Returns:
        Dict containing monitoring task information
    """
    try:
        # Start monitoring task in background
        task = backup_health_monitor.delay()
        
        return {
            "task_id": task.id,
            "status": "started",
            "started_at": datetime.utcnow().isoformat(),
            "message": "Backup health monitoring task started"
        }
        
    except Exception as e:
        logger.error(f"Failed to start backup health monitoring: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start backup health monitoring: {str(e)}")


# Task Status Endpoints

@router.get("/tasks/{task_id}", response_model=Dict[str, Any])
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get task status by ID.
    
    Args:
        task_id: Task ID to check
        current_user: Current authenticated user
        
    Returns:
        Dict containing task status
    """
    try:
        # Import Celery app to get task result
        from app.celery_app import celery_app
        
        # Get task result
        task_result = celery_app.AsyncResult(task_id)
        
        result = {
            "task_id": task_id,
            "status": task_result.status,
            "info": task_result.info if task_result.info else None
        }
        
        if task_result.failed():
            result["error"] = str(task_result.info)
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to get task status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")


# Configuration Endpoints

@router.get("/config", response_model=Dict[str, Any])
async def get_backup_dr_config(
    backup_service: BackupService = Depends(get_backup_service),
    dr_service: DisasterRecoveryService = Depends(get_dr_service),
    current_user: User = Depends(get_current_user)
):
    """
    Get backup and disaster recovery configuration.
    
    Args:
        backup_service: Backup service instance
        dr_service: Disaster recovery service instance
        current_user: Current authenticated user
        
    Returns:
        Dict containing configuration information
    """
    try:
        return {
            "backup_config": backup_service.backup_config,
            "recovery_config": dr_service.recovery_config,
            "retrieved_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get backup/DR config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get configuration: {str(e)}")


@router.get("/playbooks", response_model=List[Dict[str, Any]])
async def get_disaster_recovery_playbooks(
    dr_service: DisasterRecoveryService = Depends(get_dr_service),
    current_user: User = Depends(get_current_user)
):
    """
    Get available disaster recovery playbooks.
    
    Args:
        dr_service: Disaster recovery service instance
        current_user: Current authenticated user
        
    Returns:
        List of available playbooks
    """
    try:
        scenarios = ["database_failure", "region_outage", "application_failure"]
        playbooks = []
        
        for scenario in scenarios:
            playbook = await dr_service.create_disaster_recovery_playbook(scenario)
            playbooks.append(playbook)
        
        return playbooks
        
    except Exception as e:
        logger.error(f"Failed to get disaster recovery playbooks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get playbooks: {str(e)}")


@router.get("/playbooks/{scenario}", response_model=Dict[str, Any])
async def get_disaster_recovery_playbook(
    scenario: str,
    dr_service: DisasterRecoveryService = Depends(get_dr_service),
    current_user: User = Depends(get_current_user)
):
    """
    Get specific disaster recovery playbook.
    
    Args:
        scenario: Disaster scenario
        dr_service: Disaster recovery service instance
        current_user: Current authenticated user
        
    Returns:
        Dict containing playbook details
    """
    try:
        playbook = await dr_service.create_disaster_recovery_playbook(scenario)
        return playbook
        
    except Exception as e:
        logger.error(f"Failed to get disaster recovery playbook: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get playbook: {str(e)}") 
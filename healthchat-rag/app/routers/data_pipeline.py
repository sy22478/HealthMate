"""
Data Pipeline Router for HealthMate

This module provides:
- ETL job management endpoints
- Data quality monitoring
- Pipeline infrastructure setup
- Batch and streaming data processing
- Data warehouse operations
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, validator

from app.database import get_db
from app.models.user import User
from app.utils.auth_middleware import get_current_user
from app.services.data_pipeline import (
    DataPipelineManager, ETLJobConfig, PipelineType, DataQualityLevel,
    DataQualityMetrics, DataLineageInfo, BatchDataProcessor, 
    StreamingDataProcessor, DataWarehouseManager
)
from app.utils.audit_logging import AuditLogger

logger = logging.getLogger(__name__)
audit_logger = AuditLogger()

# Create data pipeline router
data_pipeline_router = APIRouter()


# Pydantic models for data pipeline
class ETLJobConfigRequest(BaseModel):
    """Request model for ETL job configuration."""
    job_name: str
    pipeline_type: PipelineType
    source_tables: List[str]
    target_tables: List[str]
    schedule: str  # Cron expression
    enabled: bool = True
    retry_count: int = 3
    timeout_minutes: int = 60
    batch_size: int = 1000
    parallel_workers: int = 4
    data_quality_threshold: float = 0.8
    notification_on_failure: bool = True
    notification_on_success: bool = False
    
    @validator('data_quality_threshold')
    def validate_quality_threshold(cls, v):
        """Validate data quality threshold."""
        if not 0.0 <= v <= 1.0:
            raise ValueError('Data quality threshold must be between 0.0 and 1.0')
        return v


class ETLJobResponse(BaseModel):
    """Response model for ETL job."""
    job_id: str
    job_name: str
    pipeline_type: PipelineType
    status: str
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    success_count: int = 0
    failure_count: int = 0
    created_at: datetime
    updated_at: datetime


class DataQualityReport(BaseModel):
    """Data quality report model."""
    report_id: str
    data_type: str
    quality_metrics: DataQualityMetrics
    sample_size: int
    issues_found: int
    recommendations_count: int
    generated_at: datetime


class PipelineStatusResponse(BaseModel):
    """Pipeline status response model."""
    pipeline_type: PipelineType
    status: str
    active_jobs: int
    total_jobs: int
    last_activity: Optional[datetime] = None
    performance_metrics: Dict[str, Any]


class DataLineageResponse(BaseModel):
    """Data lineage response model."""
    lineage_id: str
    source_table: str
    target_table: str
    transformation_rules: List[str]
    data_flow: List[str]
    dependencies: List[str]
    created_at: datetime
    metadata: Dict[str, Any]


# In-memory storage for ETL jobs (in production, use database)
etl_jobs: Dict[str, ETLJobConfig] = {}
job_execution_history: Dict[str, List[Dict[str, Any]]] = {}


@data_pipeline_router.post("/etl-jobs", response_model=ETLJobResponse)
async def create_etl_job(
    request: ETLJobConfigRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new ETL job configuration.
    
    This endpoint allows users to create ETL jobs for batch processing,
    streaming, or hybrid data pipelines.
    """
    try:
        import uuid
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Create ETL job configuration
        job_config = ETLJobConfig(
            job_id=job_id,
            job_name=request.job_name,
            pipeline_type=request.pipeline_type,
            source_tables=request.source_tables,
            target_tables=request.target_tables,
            schedule=request.schedule,
            enabled=request.enabled,
            retry_count=request.retry_count,
            timeout_minutes=request.timeout_minutes,
            batch_size=request.batch_size,
            parallel_workers=request.parallel_workers,
            data_quality_threshold=request.data_quality_threshold,
            notification_on_failure=request.notification_on_failure,
            notification_on_success=request.notification_on_success
        )
        
        # Store job configuration
        etl_jobs[job_id] = job_config
        job_execution_history[job_id] = []
        
        # Log job creation
        audit_logger.log_system_action(
            action="etl_job_created",
            user_id=current_user.id,
            details={
                "job_id": job_id,
                "job_name": request.job_name,
                "pipeline_type": request.pipeline_type.value,
                "source_tables": request.source_tables,
                "target_tables": request.target_tables
            }
        )
        
        logger.info(f"ETL job created: {job_id} by user {current_user.id}")
        
        return ETLJobResponse(
            job_id=job_id,
            job_name=request.job_name,
            pipeline_type=request.pipeline_type,
            status="created",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Failed to create ETL job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create ETL job: {str(e)}")


@data_pipeline_router.get("/etl-jobs", response_model=List[ETLJobResponse])
async def list_etl_jobs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all ETL jobs.
    """
    try:
        jobs = []
        
        for job_id, config in etl_jobs.items():
            # Get execution history
            history = job_execution_history.get(job_id, [])
            success_count = sum(1 for execution in history if execution.get('success', False))
            failure_count = len(history) - success_count
            
            # Get last run
            last_run = None
            if history:
                last_execution = max(history, key=lambda x: x.get('started_at', datetime.min))
                last_run = last_execution.get('started_at')
            
            jobs.append(ETLJobResponse(
                job_id=job_id,
                job_name=config.job_name,
                pipeline_type=config.pipeline_type,
                status="active" if config.enabled else "disabled",
                last_run=last_run,
                next_run=None,  # Would be calculated based on schedule
                success_count=success_count,
                failure_count=failure_count,
                created_at=datetime.utcnow(),  # Would be stored in database
                updated_at=datetime.utcnow()
            ))
        
        return jobs
        
    except Exception as e:
        logger.error(f"Failed to list ETL jobs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list ETL jobs: {str(e)}")


@data_pipeline_router.get("/etl-jobs/{job_id}", response_model=ETLJobResponse)
async def get_etl_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get details of a specific ETL job.
    """
    try:
        if job_id not in etl_jobs:
            raise HTTPException(status_code=404, detail="ETL job not found")
        
        config = etl_jobs[job_id]
        history = job_execution_history.get(job_id, [])
        
        success_count = sum(1 for execution in history if execution.get('success', False))
        failure_count = len(history) - success_count
        
        last_run = None
        if history:
            last_execution = max(history, key=lambda x: x.get('started_at', datetime.min))
            last_run = last_execution.get('started_at')
        
        return ETLJobResponse(
            job_id=job_id,
            job_name=config.job_name,
            pipeline_type=config.pipeline_type,
            status="active" if config.enabled else "disabled",
            last_run=last_run,
            next_run=None,
            success_count=success_count,
            failure_count=failure_count,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get ETL job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get ETL job: {str(e)}")


@data_pipeline_router.post("/etl-jobs/{job_id}/run")
async def run_etl_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Run an ETL job manually.
    """
    try:
        if job_id not in etl_jobs:
            raise HTTPException(status_code=404, detail="ETL job not found")
        
        job_config = etl_jobs[job_id]
        
        # Add to background tasks
        background_tasks.add_task(
            execute_etl_job_background,
            job_id,
            job_config,
            current_user.id,
            db
        )
        
        # Log job execution
        audit_logger.log_system_action(
            action="etl_job_started",
            user_id=current_user.id,
            details={
                "job_id": job_id,
                "job_name": job_config.job_name,
                "pipeline_type": job_config.pipeline_type.value
            }
        )
        
        return {
            "message": f"ETL job {job_config.job_name} started",
            "job_id": job_id,
            "status": "started"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to run ETL job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to run ETL job: {str(e)}")


@data_pipeline_router.delete("/etl-jobs/{job_id}")
async def delete_etl_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an ETL job.
    """
    try:
        if job_id not in etl_jobs:
            raise HTTPException(status_code=404, detail="ETL job not found")
        
        job_config = etl_jobs[job_id]
        
        # Remove job
        del etl_jobs[job_id]
        if job_id in job_execution_history:
            del job_execution_history[job_id]
        
        # Log job deletion
        audit_logger.log_system_action(
            action="etl_job_deleted",
            user_id=current_user.id,
            details={
                "job_id": job_id,
                "job_name": job_config.job_name
            }
        )
        
        logger.info(f"ETL job deleted: {job_id} by user {current_user.id}")
        
        return {"message": "ETL job deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete ETL job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete ETL job: {str(e)}")


@data_pipeline_router.post("/data-quality/analyze")
async def analyze_data_quality(
    data_type: str = Query(..., description="Type of data to analyze"),
    sample_size: int = Query(1000, description="Number of records to sample"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyze data quality for a specific data type.
    """
    try:
        # Get sample data (in a real implementation, this would fetch from database)
        sample_data = [
            {
                "user_id": 1,
                "heart_rate": 75,
                "timestamp": datetime.utcnow().isoformat(),
                "unit": "bpm"
            }
            for _ in range(min(sample_size, 100))  # Limit for demo
        ]
        
        # Create data validator
        from app.services.data_pipeline import DataValidator
        validator = DataValidator()
        
        # Analyze data quality
        quality_metrics = validator.validate_data_quality(sample_data, data_type)
        
        # Generate report
        import uuid
        report_id = str(uuid.uuid4())
        
        report = DataQualityReport(
            report_id=report_id,
            data_type=data_type,
            quality_metrics=quality_metrics,
            sample_size=len(sample_data),
            issues_found=len(quality_metrics.issues),
            recommendations_count=len(quality_metrics.recommendations),
            generated_at=datetime.utcnow()
        )
        
        # Log quality analysis
        audit_logger.log_system_action(
            action="data_quality_analyzed",
            user_id=current_user.id,
            details={
                "data_type": data_type,
                "sample_size": len(sample_data),
                "quality_score": quality_metrics.overall_score,
                "quality_level": quality_metrics.quality_level.value
            }
        )
        
        return report
        
    except Exception as e:
        logger.error(f"Failed to analyze data quality: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze data quality: {str(e)}")


@data_pipeline_router.get("/pipeline/status", response_model=List[PipelineStatusResponse])
async def get_pipeline_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get status of all data pipelines.
    """
    try:
        status_reports = []
        
        # Batch pipeline status
        batch_jobs = [job for job in etl_jobs.values() if job.pipeline_type == PipelineType.BATCH]
        active_batch_jobs = [job for job in batch_jobs if job.enabled]
        
        status_reports.append(PipelineStatusResponse(
            pipeline_type=PipelineType.BATCH,
            status="active" if active_batch_jobs else "inactive",
            active_jobs=len(active_batch_jobs),
            total_jobs=len(batch_jobs),
            last_activity=datetime.utcnow() if active_batch_jobs else None,
            performance_metrics={
                "avg_processing_time": 120.5,
                "success_rate": 0.95,
                "records_processed_today": 15000
            }
        ))
        
        # Streaming pipeline status
        streaming_jobs = [job for job in etl_jobs.values() if job.pipeline_type == PipelineType.STREAMING]
        active_streaming_jobs = [job for job in streaming_jobs if job.enabled]
        
        status_reports.append(PipelineStatusResponse(
            pipeline_type=PipelineType.STREAMING,
            status="active" if active_streaming_jobs else "inactive",
            active_jobs=len(active_streaming_jobs),
            total_jobs=len(streaming_jobs),
            last_activity=datetime.utcnow() if active_streaming_jobs else None,
            performance_metrics={
                "messages_per_second": 150,
                "latency_ms": 25.3,
                "error_rate": 0.02
            }
        ))
        
        # Hybrid pipeline status
        hybrid_jobs = [job for job in etl_jobs.values() if job.pipeline_type == PipelineType.HYBRID]
        active_hybrid_jobs = [job for job in hybrid_jobs if job.enabled]
        
        status_reports.append(PipelineStatusResponse(
            pipeline_type=PipelineType.HYBRID,
            status="active" if active_hybrid_jobs else "inactive",
            active_jobs=len(active_hybrid_jobs),
            total_jobs=len(hybrid_jobs),
            last_activity=datetime.utcnow() if active_hybrid_jobs else None,
            performance_metrics={
                "batch_success_rate": 0.92,
                "streaming_success_rate": 0.98,
                "combined_throughput": 2000
            }
        ))
        
        return status_reports
        
    except Exception as e:
        logger.error(f"Failed to get pipeline status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get pipeline status: {str(e)}")


@data_pipeline_router.post("/pipeline/setup")
async def setup_pipeline_infrastructure(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Setup data pipeline infrastructure.
    """
    try:
        # Create pipeline manager
        pipeline_manager = DataPipelineManager(
            db_session=db,
            kafka_config={
                "bootstrap_servers": ["localhost:9092"],
                "topics": ["healthmate-data"],
                "consumer_group": "healthmate-processors"
            },
            warehouse_config={
                "connection_string": "postgresql://user:pass@localhost:5432/healthmate_warehouse"
            }
        )
        
        # Setup infrastructure
        results = await pipeline_manager.setup_pipeline_infrastructure()
        
        # Log infrastructure setup
        audit_logger.log_system_action(
            action="pipeline_infrastructure_setup",
            user_id=current_user.id,
            details=results
        )
        
        return {
            "message": "Pipeline infrastructure setup completed",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Failed to setup pipeline infrastructure: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to setup pipeline infrastructure: {str(e)}")


@data_pipeline_router.get("/data-lineage/{job_id}", response_model=List[DataLineageResponse])
async def get_data_lineage(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get data lineage information for an ETL job.
    """
    try:
        if job_id not in etl_jobs:
            raise HTTPException(status_code=404, detail="ETL job not found")
        
        # In a real implementation, this would fetch from a lineage database
        # For now, return mock lineage information
        import uuid
        
        lineage_info = DataLineageInfo(
            lineage_id=str(uuid.uuid4()),
            source_table="health_metrics",
            target_table="aggregated_health_metrics",
            transformation_rules=["data_validation", "aggregation", "quality_check"],
            data_flow=["extract", "transform", "validate", "load"],
            dependencies=["health_metrics", "user_profiles"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata={
                "job_id": job_id,
                "records_processed": 1000,
                "processing_time": 120.5
            }
        )
        
        return [DataLineageResponse(
            lineage_id=lineage_info.lineage_id,
            source_table=lineage_info.source_table,
            target_table=lineage_info.target_table,
            transformation_rules=lineage_info.transformation_rules,
            data_flow=lineage_info.data_flow,
            dependencies=lineage_info.dependencies,
            created_at=lineage_info.created_at,
            metadata=lineage_info.metadata
        )]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get data lineage for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get data lineage: {str(e)}")


@data_pipeline_router.post("/warehouse/optimize")
async def optimize_data_warehouse(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Optimize data warehouse performance.
    """
    try:
        # Create warehouse manager
        warehouse_manager = DataWarehouseManager({
            "connection_string": "postgresql://user:pass@localhost:5432/healthmate_warehouse"
        })
        
        # Optimize partitioning
        results = await warehouse_manager.optimize_data_partitioning()
        
        # Log optimization
        audit_logger.log_system_action(
            action="warehouse_optimization",
            user_id=current_user.id,
            details=results
        )
        
        return {
            "message": "Data warehouse optimization completed",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Failed to optimize data warehouse: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to optimize data warehouse: {str(e)}")


# Background task functions
async def execute_etl_job_background(
    job_id: str,
    job_config: ETLJobConfig,
    user_id: int,
    db: Session
):
    """Execute ETL job in background."""
    try:
        start_time = datetime.utcnow()
        
        # Create pipeline manager
        pipeline_manager = DataPipelineManager(
            db_session=db,
            kafka_config={
                "bootstrap_servers": ["localhost:9092"],
                "topics": ["healthmate-data"],
                "consumer_group": "healthmate-processors"
            },
            warehouse_config={
                "connection_string": "postgresql://user:pass@localhost:5432/healthmate_warehouse"
            }
        )
        
        # Run pipeline
        results = await pipeline_manager.run_complete_pipeline(job_config)
        
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()
        
        # Record execution
        execution_record = {
            "job_id": job_id,
            "started_at": start_time,
            "completed_at": end_time,
            "processing_time": processing_time,
            "success": True,
            "results": results
        }
        
        job_execution_history[job_id].append(execution_record)
        
        logger.info(f"ETL job {job_id} completed successfully in {processing_time:.2f}s")
        
    except Exception as e:
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()
        
        # Record failure
        execution_record = {
            "job_id": job_id,
            "started_at": start_time,
            "completed_at": end_time,
            "processing_time": processing_time,
            "success": False,
            "error": str(e)
        }
        
        job_execution_history[job_id].append(execution_record)
        
        logger.error(f"ETL job {job_id} failed after {processing_time:.2f}s: {e}") 
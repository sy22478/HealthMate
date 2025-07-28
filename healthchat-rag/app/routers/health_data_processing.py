"""
Health Data Processing Router
API endpoints for health data integration, processing, and analytics
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from app.database import get_db
from app.utils.auth_middleware import get_current_user
from app.models.user import User
from app.services.enhanced import (
    DataIntegrationService, DataSourceConfig, DataType, DataSourceType,
    HealthDataProcessor, ProcessingStage, get_health_data_processor,
    HealthAnalyticsEngine, AnalyticsType, get_health_analytics_engine
)
from app.schemas.enhanced_health_schemas import (
    DataSourceConfigCreate, DataSourceConfigResponse,
    HealthDataProcessingRequest, HealthDataProcessingResponse,
    HealthAnalyticsRequest, HealthAnalyticsResponse
)
from app.exceptions.health_exceptions import HealthDataError, BusinessIntelligenceError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health-data", tags=["Health Data Processing"])

@router.post("/data-sources", response_model=DataSourceConfigResponse)
async def create_data_source_config(
    config: DataSourceConfigCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new data source configuration"""
    try:
        # Convert to DataSourceConfig
        data_source_config = DataSourceConfig(
            source_type=config.source_type,
            api_key=config.api_key,
            api_secret=config.api_secret,
            base_url=config.base_url,
            rate_limit_per_minute=config.rate_limit_per_minute,
            timeout_seconds=config.timeout_seconds,
            retry_attempts=config.retry_attempts,
            retry_delay_seconds=config.retry_delay_seconds,
            enabled=config.enabled,
            custom_headers=config.custom_headers,
            custom_params=config.custom_params
        )
        
        # Register with data integration service
        data_integration_service = DataIntegrationService()
        # Note: In a real implementation, you'd store this in the database
        # and manage provider lifecycle properly
        
        return DataSourceConfigResponse(
            id=1,  # Would be generated from database
            source_type=config.source_type,
            base_url=config.base_url,
            enabled=config.enabled,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error creating data source config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create data source config: {str(e)}")

@router.get("/data-sources", response_model=List[DataSourceConfigResponse])
async def list_data_source_configs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all data source configurations for the user"""
    try:
        # In a real implementation, you'd fetch from database
        # For now, return mock data
        return [
            DataSourceConfigResponse(
                id=1,
                source_type=DataSourceType.FITBIT,
                base_url="https://api.fitbit.com",
                enabled=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        ]
        
    except Exception as e:
        logger.error(f"Error listing data source configs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list data source configs: {str(e)}")

@router.post("/fetch-data")
async def fetch_health_data(
    request: HealthDataProcessingRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fetch health data from external sources"""
    try:
        # Get data integration service
        data_integration_service = DataIntegrationService()
        
        # Set date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=request.days_back or 30)
        
        # Fetch data
        data_points = await data_integration_service.fetch_user_health_data(
            user_id=current_user.id,
            data_types=request.data_types,
            sources=request.sources,
            start_date=start_date,
            end_date=end_date
        )
        
        # Process data in background if requested
        if request.process_data:
            background_tasks.add_task(
                process_health_data_background,
                current_user.id,
                data_points,
                request.processing_stages
            )
        
        return {
            "message": f"Successfully fetched {len(data_points)} data points",
            "data_points_count": len(data_points),
            "processing_started": request.process_data
        }
        
    except Exception as e:
        logger.error(f"Error fetching health data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch health data: {str(e)}")

@router.post("/process-data", response_model=HealthDataProcessingResponse)
async def process_health_data(
    request: HealthDataProcessingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process health data through the processing pipeline"""
    try:
        # Get health data processor
        processor = get_health_data_processor(db)
        
        # Get data points (in a real implementation, you'd fetch from storage)
        # For now, we'll use mock data
        from app.services.enhanced import HealthDataPoint
        data_points = [
            HealthDataPoint(
                user_id=current_user.id,
                data_type=DataType.HEART_RATE,
                value=75,
                unit='bpm',
                timestamp=datetime.utcnow(),
                source=DataSourceType.MANUAL_ENTRY,
                confidence=0.9
            )
        ]
        
        # Process data
        result = await processor.process_health_data(
            user_id=current_user.id,
            data_points=data_points,
            stages=request.processing_stages or list(ProcessingStage)
        )
        
        return HealthDataProcessingResponse(
            success=result.success,
            stage=result.stage,
            data_points_processed=result.data_points_processed,
            data_points_valid=result.data_points_valid,
            data_points_invalid=result.data_points_invalid,
            quality_score=result.quality_score,
            processing_time=result.processing_time,
            errors=result.errors,
            warnings=result.warnings,
            metadata=result.metadata
        )
        
    except DataProcessingError as e:
        logger.error(f"Data processing error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing health data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process health data: {str(e)}")

@router.post("/analytics", response_model=HealthAnalyticsResponse)
async def run_health_analytics(
    request: HealthAnalyticsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Run comprehensive health analytics"""
    try:
        # Get analytics engine
        analytics_engine = get_health_analytics_engine(db)
        
        # Run analytics
        results = await analytics_engine.run_comprehensive_analytics(
            user_id=current_user.id,
            analytics_types=request.analytics_types or list(AnalyticsType)
        )
        
        return HealthAnalyticsResponse(
            user_id=current_user.id,
            analytics_results=results,
            generated_at=datetime.utcnow()
        )
        
    except AnalyticsError as e:
        logger.error(f"Analytics error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error running health analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to run health analytics: {str(e)}")

@router.get("/trends")
async def get_health_trends(
    data_types: Optional[List[DataType]] = Query(None),
    days_back: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get health trends for the user"""
    try:
        # Get analytics engine
        analytics_engine = get_health_analytics_engine(db)
        
        # Get user health data
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)
        
        # In a real implementation, you'd fetch actual data
        # For now, return mock trends
        mock_trends = [
            {
                "data_type": "heart_rate",
                "direction": "stable",
                "slope": 0.1,
                "strength": 0.05,
                "confidence": 0.8,
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat(),
                "data_points": 30
            }
        ]
        
        return {
            "user_id": current_user.id,
            "trends": mock_trends,
            "analysis_period": f"{days_back} days"
        }
        
    except Exception as e:
        logger.error(f"Error getting health trends: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get health trends: {str(e)}")

@router.get("/health-score")
async def get_health_score(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current health score for the user"""
    try:
        # Get analytics engine
        analytics_engine = get_health_analytics_engine(db)
        
        # In a real implementation, you'd calculate actual health score
        # For now, return mock score
        mock_score = {
            "overall_score": 0.85,
            "category": "good",
            "component_scores": {
                "heart_rate": 0.9,
                "steps": 0.8,
                "sleep": 0.7,
                "weight": 0.9
            },
            "factors": ["Good heart rate", "Adequate sleep"],
            "recommendations": ["Increase daily steps", "Maintain current habits"],
            "last_updated": datetime.utcnow().isoformat()
        }
        
        return {
            "user_id": current_user.id,
            "health_score": mock_score
        }
        
    except Exception as e:
        logger.error(f"Error getting health score: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get health score: {str(e)}")

@router.get("/risk-assessment")
async def get_health_risk_assessment(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get health risk assessment for the user"""
    try:
        # Get analytics engine
        analytics_engine = get_health_analytics_engine(db)
        
        # In a real implementation, you'd calculate actual risk assessment
        # For now, return mock assessment
        mock_risks = [
            {
                "risk_type": "cardiovascular",
                "risk_level": "low",
                "probability": 0.2,
                "severity": "moderate",
                "factors": ["Age", "Family history"],
                "mitigation_strategies": ["Regular exercise", "Heart-healthy diet"],
                "monitoring_recommendations": ["Annual checkup", "Blood pressure monitoring"]
            }
        ]
        
        return {
            "user_id": current_user.id,
            "risk_assessment": mock_risks,
            "assessment_date": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting risk assessment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get risk assessment: {str(e)}")

@router.get("/comparative-analysis")
async def get_comparative_analysis(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comparative analysis against peer groups"""
    try:
        # Get analytics engine
        analytics_engine = get_health_analytics_engine(db)
        
        # In a real implementation, you'd perform actual comparative analysis
        # For now, return mock analysis
        mock_comparison = [
            {
                "comparison_type": "heart_rate_peer_comparison",
                "user_percentile": 75.0,
                "peer_group": "age_gender_matched",
                "differences": {
                    "vs_peer_average": -5.0,
                    "percentile": 75.0
                },
                "insights": ["Your heart rate is above average for your peer group"],
                "recommendations": ["Consider improving cardiovascular fitness"]
            }
        ]
        
        return {
            "user_id": current_user.id,
            "comparative_analysis": mock_comparison,
            "analysis_date": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting comparative analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get comparative analysis: {str(e)}")

async def process_health_data_background(
    user_id: int,
    data_points: List,
    processing_stages: List[ProcessingStage]
):
    """Background task for processing health data"""
    try:
        # Get database session
        db = next(get_db())
        
        # Get processor
        processor = get_health_data_processor(db)
        
        # Process data
        result = await processor.process_health_data(
            user_id=user_id,
            data_points=data_points,
            stages=processing_stages
        )
        
        logger.info(f"Background processing completed for user {user_id}: {result.success}")
        
    except Exception as e:
        logger.error(f"Background processing failed for user {user_id}: {str(e)}")
    finally:
        db.close() 
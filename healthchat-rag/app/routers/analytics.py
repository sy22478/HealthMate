"""
Health Analytics Router
Endpoints for health data analytics and insights
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from app.database import get_db
from app.models.user import User
from app.utils.auth_middleware import get_current_user
from app.services.health_analytics import HealthAnalyticsService
from app.utils.audit_logging import AuditLogger

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics", tags=["Health Analytics"])

# Pydantic schemas for analytics
class TrendAnalysisRequest(BaseModel):
    data_type: str = Field(..., description="Type of health data to analyze")
    days: int = Field(30, ge=1, le=365, description="Number of days to analyze")

class AnalyticsResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    message: Optional[str] = None

# Analytics Endpoints

@router.get("/trends/{data_type}", response_model=AnalyticsResponse)
async def get_health_trends(
    data_type: str,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get health data trends analysis"""
    try:
        analytics_service = HealthAnalyticsService(db)
        trend_data = analytics_service.get_health_trends(current_user.id, data_type, days)
        
        AuditLogger.log_health_event(
            event_type="trend_analysis_requested",
            user_id=current_user.id,
            data_type=data_type,
            days=days,
            success=True
        )
        
        return AnalyticsResponse(
            success=True,
            data=trend_data,
            message="Trend analysis completed successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting health trends for user {current_user.id}: {e}")
        AuditLogger.log_health_event(
            event_type="trend_analysis_requested",
            user_id=current_user.id,
            data_type=data_type,
            days=days,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to analyze health trends")

@router.get("/symptoms", response_model=AnalyticsResponse)
async def get_symptom_analysis(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get symptom analysis and patterns"""
    try:
        analytics_service = HealthAnalyticsService(db)
        symptom_data = analytics_service.get_symptom_analysis(current_user.id, days)
        
        AuditLogger.log_health_event(
            event_type="symptom_analysis_requested",
            user_id=current_user.id,
            days=days,
            success=True
        )
        
        return AnalyticsResponse(
            success=True,
            data=symptom_data,
            message="Symptom analysis completed successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting symptom analysis for user {current_user.id}: {e}")
        AuditLogger.log_health_event(
            event_type="symptom_analysis_requested",
            user_id=current_user.id,
            days=days,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to analyze symptoms")

@router.get("/medications", response_model=AnalyticsResponse)
async def get_medication_adherence(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get medication adherence analysis"""
    try:
        analytics_service = HealthAnalyticsService(db)
        medication_data = analytics_service.get_medication_adherence(current_user.id, days)
        
        AuditLogger.log_health_event(
            event_type="medication_analysis_requested",
            user_id=current_user.id,
            days=days,
            success=True
        )
        
        return AnalyticsResponse(
            success=True,
            data=medication_data,
            message="Medication adherence analysis completed successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting medication adherence for user {current_user.id}: {e}")
        AuditLogger.log_health_event(
            event_type="medication_analysis_requested",
            user_id=current_user.id,
            days=days,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to analyze medication adherence")

@router.get("/health-score", response_model=AnalyticsResponse)
async def get_health_score(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get overall health score and analysis"""
    try:
        analytics_service = HealthAnalyticsService(db)
        health_score_data = analytics_service.get_health_score(current_user.id)
        
        AuditLogger.log_health_event(
            event_type="health_score_requested",
            user_id=current_user.id,
            success=True
        )
        
        return AnalyticsResponse(
            success=True,
            data=health_score_data,
            message="Health score calculated successfully"
        )
        
    except Exception as e:
        logger.error(f"Error calculating health score for user {current_user.id}: {e}")
        AuditLogger.log_health_event(
            event_type="health_score_requested",
            user_id=current_user.id,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to calculate health score")

@router.get("/recommendations", response_model=AnalyticsResponse)
async def get_health_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get personalized health recommendations"""
    try:
        analytics_service = HealthAnalyticsService(db)
        recommendations = analytics_service.get_health_recommendations(current_user.id)
        
        AuditLogger.log_health_event(
            event_type="health_recommendations_requested",
            user_id=current_user.id,
            success=True
        )
        
        return AnalyticsResponse(
            success=True,
            data={"recommendations": recommendations},
            message="Health recommendations generated successfully"
        )
        
    except Exception as e:
        logger.error(f"Error generating health recommendations for user {current_user.id}: {e}")
        AuditLogger.log_health_event(
            event_type="health_recommendations_requested",
            user_id=current_user.id,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to generate health recommendations")

@router.get("/dashboard", response_model=AnalyticsResponse)
async def get_health_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive health dashboard data"""
    try:
        analytics_service = HealthAnalyticsService(db)
        
        # Get all analytics data for dashboard
        health_score = analytics_service.get_health_score(current_user.id)
        symptom_analysis = analytics_service.get_symptom_analysis(current_user.id, 30)
        medication_adherence = analytics_service.get_medication_adherence(current_user.id, 30)
        recommendations = analytics_service.get_health_recommendations(current_user.id)
        
        # Compile dashboard data
        dashboard_data = {
            "health_score": health_score,
            "symptom_analysis": symptom_analysis,
            "medication_adherence": medication_adherence,
            "recommendations": recommendations,
            "last_updated": datetime.utcnow().isoformat()
        }
        
        AuditLogger.log_health_event(
            event_type="health_dashboard_requested",
            user_id=current_user.id,
            success=True
        )
        
        return AnalyticsResponse(
            success=True,
            data=dashboard_data,
            message="Health dashboard data retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting health dashboard for user {current_user.id}: {e}")
        AuditLogger.log_health_event(
            event_type="health_dashboard_requested",
            user_id=current_user.id,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to get health dashboard")

@router.get("/data-types", response_model=AnalyticsResponse)
async def get_available_data_types(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of available health data types for analysis"""
    try:
        from app.models.health_data import HealthData
        
        # Get unique data types for the user
        data_types = db.query(HealthData.data_type).filter(
            HealthData.user_id == current_user.id
        ).distinct().all()
        
        available_types = [dt[0] for dt in data_types]
        
        AuditLogger.log_health_event(
            event_type="data_types_requested",
            user_id=current_user.id,
            success=True
        )
        
        return AnalyticsResponse(
            success=True,
            data={"data_types": available_types},
            message="Available data types retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting data types for user {current_user.id}: {e}")
        AuditLogger.log_health_event(
            event_type="data_types_requested",
            user_id=current_user.id,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to get data types") 
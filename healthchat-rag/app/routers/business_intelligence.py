"""
Business Intelligence Router
API endpoints for business intelligence data and reports
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.services.auth import get_current_user
from app.services.enhanced.business_intelligence import (
    get_business_intelligence_service, ReportType, AggregationPeriod,
    MetricType
)
from app.schemas.common_schemas import StandardResponse
from app.utils.rate_limiting import rate_limit
from app.utils.audit_logging import audit_logger
from app.exceptions.health_exceptions import BusinessIntelligenceError

logger = logging.getLogger(__name__)

# Initialize router
bi_router = APIRouter(prefix="/api/v1/business-intelligence", tags=["Business Intelligence"])

# Security
security = HTTPBearer()

@bi_router.get("/health-metrics/aggregated", response_model=StandardResponse)
@rate_limit(max_requests=10, window_seconds=3600)  # 10 requests per hour
async def get_aggregated_health_metrics(
    period: AggregationPeriod = Query(AggregationPeriod.DAILY, description="Aggregation period"),
    start_date: datetime = Query(..., description="Start date for aggregation"),
    end_date: datetime = Query(..., description="End date for aggregation"),
    user_id: Optional[int] = Query(None, description="Specific user ID (admin only)"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> StandardResponse:
    """
    Get aggregated health metrics for business intelligence.
    
    This endpoint provides aggregated health metrics for analysis and reporting.
    Admin users can query metrics for specific users.
    """
    try:
        # Get current user
        current_user = await get_current_user(credentials.credentials, db)
        
        # Check if user has admin privileges for specific user queries
        if user_id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required to query specific user metrics"
            )
        
        # Initialize BI service
        bi_service = get_business_intelligence_service(db)
        
        # Get aggregated metrics
        if user_id:
            # Query specific user
            aggregated_metrics = await bi_service.aggregate_health_metrics(
                user_id=user_id,
                period=period,
                start_date=start_date,
                end_date=end_date
            )
            metrics_data = aggregated_metrics.__dict__ if aggregated_metrics else None
        else:
            # Query all users (admin only)
            if current_user.role != "admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin privileges required to query all user metrics"
                )
            
            # Get all active users
            users = db.query(User).filter(User.is_active == True).all()
            metrics_data = []
            
            for user in users:
                try:
                    user_metrics = await bi_service.aggregate_health_metrics(
                        user_id=user.id,
                        period=period,
                        start_date=start_date,
                        end_date=end_date
                    )
                    if user_metrics:
                        metrics_data.append(user_metrics.__dict__)
                except Exception as e:
                    logger.warning(f"Failed to aggregate metrics for user {user.id}: {e}")
        
        # Log access
        audit_logger.log_data_access(
            user_id=current_user.id,
            data_type="aggregated_health_metrics",
            access_type="read",
            details={
                "period": period.value,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "target_user_id": user_id
            }
        )
        
        return StandardResponse(
            success=True,
            message="Aggregated health metrics retrieved successfully",
            data={
                "metrics": metrics_data,
                "period": period.value,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_records": len(metrics_data) if isinstance(metrics_data, list) else 1
            }
        )
        
    except HTTPException:
        raise
    except BusinessIntelligenceError as e:
        logger.error(f"Business intelligence error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving aggregated health metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve aggregated health metrics: {str(e)}")

@bi_router.get("/user-engagement", response_model=StandardResponse)
@rate_limit(max_requests=10, window_seconds=3600)  # 10 requests per hour
async def get_user_engagement_metrics(
    date: datetime = Query(..., description="Date for engagement metrics"),
    user_id: Optional[int] = Query(None, description="Specific user ID (admin only)"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> StandardResponse:
    """
    Get user engagement metrics for business intelligence.
    
    This endpoint provides user engagement analytics for analysis and reporting.
    Admin users can query metrics for specific users.
    """
    try:
        # Get current user
        current_user = await get_current_user(credentials.credentials, db)
        
        # Check if user has admin privileges for specific user queries
        if user_id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required to query specific user engagement"
            )
        
        # Initialize BI service
        bi_service = get_business_intelligence_service(db)
        
        # Get engagement metrics
        if user_id:
            # Query specific user
            engagement_metrics = await bi_service.track_user_engagement(
                user_id=user_id,
                date=date
            )
            engagement_data = engagement_metrics.__dict__ if engagement_metrics else None
        else:
            # Query all users (admin only)
            if current_user.role != "admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin privileges required to query all user engagement"
                )
            
            # Get all active users
            users = db.query(User).filter(User.is_active == True).all()
            engagement_data = []
            
            for user in users:
                try:
                    user_engagement = await bi_service.track_user_engagement(
                        user_id=user.id,
                        date=date
                    )
                    if user_engagement:
                        engagement_data.append(user_engagement.__dict__)
                except Exception as e:
                    logger.warning(f"Failed to track engagement for user {user.id}: {e}")
        
        # Log access
        audit_logger.log_data_access(
            user_id=current_user.id,
            data_type="user_engagement_metrics",
            access_type="read",
            details={
                "date": date.isoformat(),
                "target_user_id": user_id
            }
        )
        
        return StandardResponse(
            success=True,
            message="User engagement metrics retrieved successfully",
            data={
                "engagement": engagement_data,
                "date": date.isoformat(),
                "total_records": len(engagement_data) if isinstance(engagement_data, list) else 1
            }
        )
        
    except HTTPException:
        raise
    except BusinessIntelligenceError as e:
        logger.error(f"Business intelligence error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving user engagement metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve user engagement metrics: {str(e)}")

@bi_router.get("/system-performance", response_model=StandardResponse)
@rate_limit(max_requests=20, window_seconds=3600)  # 20 requests per hour
async def get_system_performance_metrics(
    service_name: Optional[str] = Query(None, description="Specific service name"),
    environment: str = Query("production", description="Environment"),
    start_time: datetime = Query(..., description="Start time for metrics"),
    end_time: datetime = Query(..., description="End time for metrics"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> StandardResponse:
    """
    Get system performance metrics for business intelligence.
    
    This endpoint provides system performance analytics for monitoring and reporting.
    """
    try:
        # Get current user
        current_user = await get_current_user(credentials.credentials, db)
        
        # Check if user has admin privileges
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required to access system performance metrics"
            )
        
        # Initialize BI service
        bi_service = get_business_intelligence_service(db)
        
        # Get performance metrics
        if service_name:
            # Query specific service
            performance_metrics = await bi_service.collect_system_performance_metrics(
                service_name=service_name,
                environment=environment
            )
            performance_data = performance_metrics.__dict__ if performance_metrics else None
        else:
            # Query all services
            services = ["api", "database", "cache", "queue", "storage"]
            performance_data = []
            
            for service in services:
                try:
                    service_metrics = await bi_service.collect_system_performance_metrics(
                        service_name=service,
                        environment=environment
                    )
                    if service_metrics:
                        performance_data.append(service_metrics.__dict__)
                except Exception as e:
                    logger.warning(f"Failed to collect performance metrics for service {service}: {e}")
        
        # Log access
        audit_logger.log_data_access(
            user_id=current_user.id,
            data_type="system_performance_metrics",
            access_type="read",
            details={
                "service_name": service_name,
                "environment": environment,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            }
        )
        
        return StandardResponse(
            success=True,
            message="System performance metrics retrieved successfully",
            data={
                "performance": performance_data,
                "environment": environment,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "total_services": len(performance_data) if isinstance(performance_data, list) else 1
            }
        )
        
    except HTTPException:
        raise
    except BusinessIntelligenceError as e:
        logger.error(f"Business intelligence error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving system performance metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve system performance metrics: {str(e)}")

@bi_router.post("/reports/generate", response_model=StandardResponse)
@rate_limit(max_requests=5, window_seconds=3600)  # 5 requests per hour
async def generate_business_intelligence_report(
    report_type: ReportType,
    start_date: datetime,
    end_date: datetime,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> StandardResponse:
    """
    Generate business intelligence report.
    
    This endpoint generates comprehensive BI reports for analysis and decision making.
    """
    try:
        # Get current user
        current_user = await get_current_user(credentials.credentials, db)
        
        # Check if user has admin privileges
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required to generate business intelligence reports"
            )
        
        # Initialize BI service
        bi_service = get_business_intelligence_service(db)
        
        # Generate report
        report = await bi_service.generate_automated_report(
            report_type=report_type,
            start_date=start_date,
            end_date=end_date,
            generated_by=current_user.email
        )
        
        # Log report generation
        audit_logger.log_system_action(
            action="bi_report_generated",
            user_id=current_user.id,
            details={
                "report_type": report_type.value,
                "report_id": report.report_id,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        )
        
        return StandardResponse(
            success=True,
            message="Business intelligence report generated successfully",
            data={
                "report": {
                    "report_id": report.report_id,
                    "report_type": report.report_type.value,
                    "generated_at": report.generated_at.isoformat(),
                    "period_start": report.period_start.isoformat(),
                    "period_end": report.period_end.isoformat(),
                    "summary": report.summary,
                    "insights": report.insights,
                    "recommendations": report.recommendations,
                    "confidence_score": report.confidence_score
                }
            }
        )
        
    except HTTPException:
        raise
    except BusinessIntelligenceError as e:
        logger.error(f"Business intelligence error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating business intelligence report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate business intelligence report: {str(e)}")

@bi_router.get("/reports/list", response_model=StandardResponse)
@rate_limit(max_requests=10, window_seconds=3600)  # 10 requests per hour
async def list_business_intelligence_reports(
    report_type: Optional[ReportType] = Query(None, description="Filter by report type"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    limit: int = Query(50, description="Number of reports to return"),
    offset: int = Query(0, description="Number of reports to skip"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> StandardResponse:
    """
    List business intelligence reports.
    
    This endpoint lists available BI reports with optional filtering.
    """
    try:
        # Get current user
        current_user = await get_current_user(credentials.credentials, db)
        
        # Check if user has admin privileges
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required to list business intelligence reports"
            )
        
        # In a real implementation, this would query a reports table
        # For now, return a placeholder response
        reports = [
            {
                "report_id": "bi_report_health_summary_20240101_20240107",
                "report_type": "health_summary",
                "generated_at": "2024-01-07T00:00:00Z",
                "period_start": "2024-01-01T00:00:00Z",
                "period_end": "2024-01-07T23:59:59Z",
                "generated_by": "system",
                "status": "completed"
            },
            {
                "report_id": "bi_report_user_engagement_20240101_20240107",
                "report_type": "user_engagement",
                "generated_at": "2024-01-07T00:00:00Z",
                "period_start": "2024-01-01T00:00:00Z",
                "period_end": "2024-01-07T23:59:59Z",
                "generated_by": "system",
                "status": "completed"
            }
        ]
        
        # Apply filters
        if report_type:
            reports = [r for r in reports if r["report_type"] == report_type.value]
        
        if start_date:
            reports = [r for r in reports if datetime.fromisoformat(r["period_start"].replace("Z", "+00:00")) >= start_date]
        
        if end_date:
            reports = [r for r in reports if datetime.fromisoformat(r["period_end"].replace("Z", "+00:00")) <= end_date]
        
        # Apply pagination
        total_count = len(reports)
        reports = reports[offset:offset + limit]
        
        # Log access
        audit_logger.log_data_access(
            user_id=current_user.id,
            data_type="business_intelligence_reports",
            access_type="read",
            details={
                "report_type": report_type.value if report_type else None,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "limit": limit,
                "offset": offset
            }
        )
        
        return StandardResponse(
            success=True,
            message="Business intelligence reports listed successfully",
            data={
                "reports": reports,
                "total_count": total_count,
                "limit": limit,
                "offset": offset
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing business intelligence reports: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list business intelligence reports: {str(e)}")

@bi_router.get("/dashboard/summary", response_model=StandardResponse)
@rate_limit(max_requests=20, window_seconds=3600)  # 20 requests per hour
async def get_business_intelligence_dashboard_summary(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> StandardResponse:
    """
    Get business intelligence dashboard summary.
    
    This endpoint provides a summary of key BI metrics for dashboard display.
    """
    try:
        # Get current user
        current_user = await get_current_user(credentials.credentials, db)
        
        # Check if user has admin privileges
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required to access business intelligence dashboard"
            )
        
        # In a real implementation, this would aggregate data from various BI tables
        # For now, return a placeholder summary
        dashboard_summary = {
            "health_metrics": {
                "total_users": 1250,
                "avg_health_score": 78.5,
                "active_users_today": 342,
                "data_completeness": 0.85
            },
            "user_engagement": {
                "avg_engagement_score": 0.75,
                "avg_session_duration_minutes": 45,
                "feature_adoption_rate": 0.68,
                "retention_rate": 0.82
            },
            "system_performance": {
                "avg_response_time_ms": 150.5,
                "error_rate": 0.005,
                "uptime_percentage": 99.95,
                "active_services": 5
            },
            "reports": {
                "reports_generated_today": 3,
                "reports_generated_this_week": 21,
                "avg_report_generation_time_seconds": 45.2
            }
        }
        
        # Log access
        audit_logger.log_data_access(
            user_id=current_user.id,
            data_type="business_intelligence_dashboard",
            access_type="read",
            details={}
        )
        
        return StandardResponse(
            success=True,
            message="Business intelligence dashboard summary retrieved successfully",
            data=dashboard_summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving business intelligence dashboard summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve business intelligence dashboard summary: {str(e)}") 
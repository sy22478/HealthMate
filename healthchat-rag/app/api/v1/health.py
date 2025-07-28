"""
Version 1 Health API endpoints.

This module provides versioned health data endpoints with improved
response optimization, pagination, caching, and compression.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response, Query, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import time
from datetime import datetime

from app.database import get_db
from app.models.health_data import HealthData
from app.models.user import User
from app.schemas.health_schemas import HealthDataCreate, HealthDataUpdate, HealthDataResponse
from app.services.health_functions import HealthFunctions
from app.utils.auth_middleware import get_current_user
from app.utils.rate_limiting import rate_limit
from app.utils.cache import cache_response, get_cached_response
from app.utils.pagination import (
    get_pagination_params, paginate_response, apply_pagination,
    create_pagination_metadata, PaginationParams
)
from app.utils.compression import compress_response, get_acceptable_encoding
from app.utils.audit_logging import audit_log

router = APIRouter(prefix="/health", tags=["Health v1"])
security = HTTPBearer()

@router.post("/data", response_model=Dict[str, Any])
@rate_limit(max_requests=20, window_seconds=300)  # 20 requests per 5 minutes
async def create_health_data(
    health_data: HealthDataCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    response: Response = None
) -> Dict[str, Any]:
    """
    Create health data with optimized response.
    
    Args:
        health_data: Health data to create
        credentials: HTTP bearer token
        db: Database session
        response: FastAPI response object
        
    Returns:
        Created health data with metadata
    """
    start_time = time.time()
    
    try:
        # Get current user
        current_user = await get_current_user(credentials.credentials, db)
        
        # Create health data
        db_health_data = HealthData(
            user_id=current_user.id,
            data_type=health_data.data_type,
            value=health_data.value,
            unit=health_data.unit,
            timestamp=health_data.timestamp,
            notes=health_data.notes
        )
        
        db.add(db_health_data)
        db.commit()
        db.refresh(db_health_data)
        
        # Prepare optimized response
        response_data = {
            "id": db_health_data.id,
            "data_type": db_health_data.data_type,
            "value": db_health_data.value,
            "unit": db_health_data.unit,
            "timestamp": db_health_data.timestamp.isoformat(),
            "notes": db_health_data.notes,
            "created_at": db_health_data.created_at.isoformat(),
            "metadata": {
                "version": "v1",
                "timestamp": datetime.utcnow().isoformat(),
                "processing_time_ms": round((time.time() - start_time) * 1000, 2)
            }
        }
        
        # Add cache invalidation headers
        if response:
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        
        # Audit log
        audit_log(
            event_type="health_data_created",
            user_id=current_user.id,
            user_email=current_user.email,
            details={
                "data_type": health_data.data_type,
                "data_id": db_health_data.id,
                "method": "api_v1"
            }
        )
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        audit_log(
            event_type="health_data_creation_failed",
            user_id=current_user.id if 'current_user' in locals() else None,
            details={"error": str(e), "data_type": health_data.data_type}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create health data"
        )

@router.get("/data", response_model=Dict[str, Any])
@cache_response(expire_seconds=300)  # Cache for 5 minutes
async def get_health_data(
    pagination: PaginationParams = Depends(get_pagination_params),
    data_type: Optional[str] = Query(None, description="Filter by data type"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get paginated health data with filtering and optimization.
    
    Args:
        pagination: Pagination parameters
        data_type: Filter by data type
        start_date: Start date filter
        end_date: End date filter
        credentials: HTTP bearer token
        db: Database session
        
    Returns:
        Paginated health data with metadata
    """
    start_time = time.time()
    
    try:
        # Get current user
        current_user = await get_current_user(credentials.credentials, db)
        
        # Build query
        query = db.query(HealthData).filter(HealthData.user_id == current_user.id)
        
        # Apply filters
        if data_type:
            query = query.filter(HealthData.data_type == data_type)
        
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                query = query.filter(HealthData.timestamp >= start_dt)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid start_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
                )
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                query = query.filter(HealthData.timestamp <= end_dt)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid end_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
                )
        
        # Apply pagination
        paginated_query, total = apply_pagination(
            query, pagination, order_by="timestamp", order_direction="desc"
        )
        
        # Get results
        health_data_list = paginated_query.all()
        
        # Convert to response format
        items = []
        for health_data in health_data_list:
            items.append({
                "id": health_data.id,
                "data_type": health_data.data_type,
                "value": health_data.value,
                "unit": health_data.unit,
                "timestamp": health_data.timestamp.isoformat(),
                "notes": health_data.notes,
                "created_at": health_data.created_at.isoformat()
            })
        
        # Create paginated response
        paginated_response = paginate_response(
            items=items,
            total=total,
            page=pagination.page,
            size=pagination.size,
            metadata=create_pagination_metadata(
                page=pagination.page,
                size=pagination.size,
                total=total,
                processing_time_ms=round((time.time() - start_time) * 1000, 2)
            )
        )
        
        # Add version metadata
        response_data = paginated_response.dict()
        response_data["metadata"]["version"] = "v1"
        response_data["metadata"]["timestamp"] = datetime.utcnow().isoformat()
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve health data"
        )

@router.get("/data/{data_id}", response_model=Dict[str, Any])
@cache_response(expire_seconds=600)  # Cache for 10 minutes
async def get_health_data_by_id(
    data_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get specific health data by ID with caching.
    
    Args:
        data_id: Health data ID
        credentials: HTTP bearer token
        db: Database session
        
    Returns:
        Health data with metadata
    """
    try:
        # Get current user
        current_user = await get_current_user(credentials.credentials, db)
        
        # Get health data
        health_data = db.query(HealthData).filter(
            HealthData.id == data_id,
            HealthData.user_id == current_user.id
        ).first()
        
        if not health_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Health data not found"
            )
        
        return {
            "id": health_data.id,
            "data_type": health_data.data_type,
            "value": health_data.value,
            "unit": health_data.unit,
            "timestamp": health_data.timestamp.isoformat(),
            "notes": health_data.notes,
            "created_at": health_data.created_at.isoformat(),
            "metadata": {
                "version": "v1",
                "timestamp": datetime.utcnow().isoformat(),
                "cached": False
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve health data"
        )

@router.put("/data/{data_id}", response_model=Dict[str, Any])
@rate_limit(max_requests=10, window_seconds=300)  # 10 requests per 5 minutes
async def update_health_data(
    data_id: int,
    health_data_update: HealthDataUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    response: Response = None
) -> Dict[str, Any]:
    """
    Update health data with optimized response.
    
    Args:
        data_id: Health data ID
        health_data_update: Health data update
        credentials: HTTP bearer token
        db: Database session
        response: FastAPI response object
        
    Returns:
        Updated health data with metadata
    """
    start_time = time.time()
    
    try:
        # Get current user
        current_user = await get_current_user(credentials.credentials, db)
        
        # Get health data
        health_data = db.query(HealthData).filter(
            HealthData.id == data_id,
            HealthData.user_id == current_user.id
        ).first()
        
        if not health_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Health data not found"
            )
        
        # Update fields
        update_data = health_data_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(health_data, field, value)
        
        db.commit()
        db.refresh(health_data)
        
        # Prepare optimized response
        response_data = {
            "id": health_data.id,
            "data_type": health_data.data_type,
            "value": health_data.value,
            "unit": health_data.unit,
            "timestamp": health_data.timestamp.isoformat(),
            "notes": health_data.notes,
            "updated_at": datetime.utcnow().isoformat(),
            "metadata": {
                "version": "v1",
                "timestamp": datetime.utcnow().isoformat(),
                "processing_time_ms": round((time.time() - start_time) * 1000, 2)
            }
        }
        
        # Add cache invalidation headers
        if response:
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        
        # Audit log
        audit_log(
            event_type="health_data_updated",
            user_id=current_user.id,
            user_email=current_user.email,
            details={
                "data_id": data_id,
                "updated_fields": list(update_data.keys()),
                "method": "api_v1"
            }
        )
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        audit_log(
            event_type="health_data_update_failed",
            user_id=current_user.id if 'current_user' in locals() else None,
            details={"error": str(e), "data_id": data_id}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update health data"
        )

@router.delete("/data/{data_id}")
@rate_limit(max_requests=5, window_seconds=300)  # 5 requests per 5 minutes
async def delete_health_data(
    data_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Delete health data.
    
    Args:
        data_id: Health data ID
        credentials: HTTP bearer token
        db: Database session
        
    Returns:
        Deletion confirmation
    """
    try:
        # Get current user
        current_user = await get_current_user(credentials.credentials, db)
        
        # Get health data
        health_data = db.query(HealthData).filter(
            HealthData.id == data_id,
            HealthData.user_id == current_user.id
        ).first()
        
        if not health_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Health data not found"
            )
        
        # Delete health data
        db.delete(health_data)
        db.commit()
        
        # Audit log
        audit_log(
            event_type="health_data_deleted",
            user_id=current_user.id,
            user_email=current_user.email,
            details={
                "data_id": data_id,
                "data_type": health_data.data_type,
                "method": "api_v1"
            }
        )
        
        return {"message": "Health data deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        audit_log(
            event_type="health_data_deletion_failed",
            user_id=current_user.id if 'current_user' in locals() else None,
            details={"error": str(e), "data_id": data_id}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete health data"
        )

@router.post("/bmi", response_model=Dict[str, Any])
@cache_response(expire_seconds=3600)  # Cache for 1 hour
async def calculate_bmi(
    weight_kg: float = Query(..., gt=0, description="Weight in kilograms"),
    height_m: float = Query(..., gt=0, description="Height in meters"),
    request: Request = None
) -> Dict[str, Any]:
    """
    Calculate BMI with caching and compression.
    
    Args:
        weight_kg: Weight in kilograms
        height_m: Height in meters
        request: FastAPI request object
        
    Returns:
        BMI calculation with metadata
    """
    start_time = time.time()
    
    try:
        health_functions = HealthFunctions()
        bmi_result = health_functions.calculate_bmi(weight_kg, height_m)
        
        response_data = {
            "bmi": bmi_result["bmi"],
            "category": bmi_result["category"],
            "weight_kg": weight_kg,
            "height_m": height_m,
            "metadata": {
                "version": "v1",
                "timestamp": datetime.utcnow().isoformat(),
                "processing_time_ms": round((time.time() - start_time) * 1000, 2)
            }
        }
        
        return response_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate BMI"
        )

@router.post("/symptoms", response_model=Dict[str, Any])
@rate_limit(max_requests=10, window_seconds=300)  # 10 requests per 5 minutes
async def check_symptoms(
    symptoms: List[str] = Query(..., description="List of symptoms"),
    severity: str = Query(..., description="Symptom severity (mild/moderate/severe)"),
    request: Request = None
) -> Dict[str, Any]:
    """
    Check symptoms with rate limiting.
    
    Args:
        symptoms: List of symptoms
        severity: Symptom severity
        request: FastAPI request object
        
    Returns:
        Symptom analysis with recommendations
    """
    start_time = time.time()
    
    try:
        health_functions = HealthFunctions()
        symptom_result = health_functions.analyze_symptoms(symptoms, severity)
        
        response_data = {
            "message": symptom_result["message"],
            "recommendations": symptom_result["recommendations"],
            "urgency": symptom_result["urgency"],
            "symptoms": symptoms,
            "severity": severity,
            "metadata": {
                "version": "v1",
                "timestamp": datetime.utcnow().isoformat(),
                "processing_time_ms": round((time.time() - start_time) * 1000, 2)
            }
        }
        
        return response_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze symptoms"
        )

@router.post("/drug-interactions", response_model=Dict[str, Any])
@rate_limit(max_requests=15, window_seconds=300)  # 15 requests per 5 minutes
async def check_drug_interactions(
    medications: List[str] = Query(..., description="List of medications"),
    request: Request = None
) -> Dict[str, Any]:
    """
    Check drug interactions with rate limiting.
    
    Args:
        medications: List of medications
        request: FastAPI request object
        
    Returns:
        Drug interaction analysis
    """
    start_time = time.time()
    
    try:
        health_functions = HealthFunctions()
        interaction_result = health_functions.check_drug_interactions(medications)
        
        response_data = {
            "interactions": interaction_result["interactions"],
            "interactions_found": interaction_result["interactions_found"],
            "recommendation": interaction_result["recommendation"],
            "medications": medications,
            "metadata": {
                "version": "v1",
                "timestamp": datetime.utcnow().isoformat(),
                "processing_time_ms": round((time.time() - start_time) * 1000, 2)
            }
        }
        
        return response_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check drug interactions"
        )

@router.get("/analytics", response_model=Dict[str, Any])
@cache_response(expire_seconds=1800)  # Cache for 30 minutes
async def get_health_analytics(
    data_type: Optional[str] = Query(None, description="Filter by data type"),
    period: str = Query("30d", description="Analysis period (7d, 30d, 90d, 1y)"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get health analytics with caching.
    
    Args:
        data_type: Filter by data type
        period: Analysis period
        credentials: HTTP bearer token
        db: Database session
        
    Returns:
        Health analytics with metadata
    """
    start_time = time.time()
    
    try:
        # Get current user
        current_user = await get_current_user(credentials.credentials, db)
        
        # Build query
        query = db.query(HealthData).filter(HealthData.user_id == current_user.id)
        
        if data_type:
            query = query.filter(HealthData.data_type == data_type)
        
        # Get health data
        health_data_list = query.all()
        
        # Calculate analytics (simplified for demo)
        analytics = {
            "total_records": len(health_data_list),
            "data_types": list(set([data.data_type for data in health_data_list])),
            "date_range": {
                "earliest": min([data.timestamp for data in health_data_list]).isoformat() if health_data_list else None,
                "latest": max([data.timestamp for data in health_data_list]).isoformat() if health_data_list else None
            },
            "period": period
        }
        
        response_data = {
            "analytics": analytics,
            "metadata": {
                "version": "v1",
                "timestamp": datetime.utcnow().isoformat(),
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                "cached": False
            }
        }
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve health analytics"
        ) 
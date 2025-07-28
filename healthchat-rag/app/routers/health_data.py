"""
Health Data Management Router
Comprehensive endpoints for health data CRUD operations
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from app.database import get_db
from app.models.health_data import HealthData, SymptomLog, MedicationLog, HealthGoal, HealthAlert
from app.models.user import User
from app.utils.auth_middleware import get_current_user
from app.utils.encryption_utils import encryption_manager
from app.utils.audit_logging import AuditLogger

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health-data", tags=["Health Data"])

# Pydantic schemas for health data
class HealthDataCreate(BaseModel):
    data_type: str = Field(..., description="Type of health data (blood_pressure, heart_rate, etc.)")
    value: str = Field(..., description="Health data value (JSON or string)")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    notes: Optional[str] = Field(None, description="Additional notes")
    source: Optional[str] = Field("manual", description="Data source (manual, device, api)")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence level (0.0 to 1.0)")
    timestamp: Optional[datetime] = Field(None, description="Timestamp of the data")

class HealthDataUpdate(BaseModel):
    value: Optional[str] = Field(None, description="Updated health data value")
    unit: Optional[str] = Field(None, description="Updated unit of measurement")
    notes: Optional[str] = Field(None, description="Updated notes")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Updated confidence level")

class HealthDataResponse(BaseModel):
    id: int
    data_type: str
    value: str
    unit: Optional[str]
    timestamp: datetime
    source: Optional[str]
    confidence: Optional[float]
    created_at: datetime
    updated_at: datetime

class SymptomLogCreate(BaseModel):
    symptom: str = Field(..., description="Symptom name")
    severity: str = Field(..., description="Severity level (mild, moderate, severe)")
    description: Optional[str] = Field(None, description="Symptom description")
    location: Optional[str] = Field(None, description="Body location")
    duration: Optional[str] = Field(None, description="Duration of symptom")
    triggers: Optional[str] = Field(None, description="Known triggers")
    treatments: Optional[str] = Field(None, description="Treatments tried")
    pain_level: Optional[int] = Field(None, ge=0, le=10, description="Pain level (0-10)")
    timestamp: Optional[datetime] = Field(None, description="When symptom occurred")

class MedicationLogCreate(BaseModel):
    medication_name: str = Field(..., description="Name of medication")
    dosage: str = Field(..., description="Dosage information")
    frequency: str = Field(..., description="Frequency of medication")
    prescribed_by: Optional[str] = Field(None, description="Prescribing doctor")
    prescription_date: Optional[datetime] = Field(None, description="Date prescribed")
    expiry_date: Optional[datetime] = Field(None, description="Expiry date")
    notes: Optional[str] = Field(None, description="Additional notes")
    side_effects: Optional[str] = Field(None, description="Side effects experienced")
    effectiveness: Optional[int] = Field(None, ge=1, le=10, description="Effectiveness rating (1-10)")

class HealthGoalCreate(BaseModel):
    goal_type: str = Field(..., description="Type of health goal")
    target_value: str = Field(..., description="Target value (JSON or string)")
    current_value: Optional[str] = Field(None, description="Current value")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    deadline: Optional[datetime] = Field(None, description="Goal deadline")
    description: str = Field(..., description="Goal description")

# Health Data Endpoints

@router.post("/", response_model=HealthDataResponse)
async def create_health_data(
    data: HealthDataCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new health data entry"""
    try:
        health_data = HealthData(
            user_id=current_user.id,
            data_type=data.data_type,
            value=data.value,
            unit=data.unit,
            notes=data.notes,
            source=data.source,
            confidence=data.confidence,
            timestamp=data.timestamp or datetime.utcnow()
        )
        
        db.add(health_data)
        db.commit()
        db.refresh(health_data)
        
        # Decrypt for response
        health_data.decrypt_sensitive_fields()
        
        AuditLogger.log_health_event(
            event_type="health_data_created",
            user_id=current_user.id,
            data_type=data.data_type,
            success=True
        )
        
        return health_data.to_dict(include_sensitive=True)
        
    except Exception as e:
        logger.error(f"Error creating health data: {e}")
        AuditLogger.log_health_event(
            event_type="health_data_created",
            user_id=current_user.id,
            data_type=data.data_type,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to create health data")

@router.get("/", response_model=List[HealthDataResponse])
async def get_health_data(
    data_type: Optional[str] = Query(None, description="Filter by data type"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    limit: int = Query(100, le=1000, description="Number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get health data with optional filtering"""
    try:
        query = db.query(HealthData).filter(HealthData.user_id == current_user.id)
        
        if data_type:
            query = query.filter(HealthData.data_type == data_type)
        
        if start_date:
            query = query.filter(HealthData.timestamp >= start_date)
        
        if end_date:
            query = query.filter(HealthData.timestamp <= end_date)
        
        health_data = query.order_by(HealthData.timestamp.desc()).offset(offset).limit(limit).all()
        
        # Decrypt sensitive fields
        for data in health_data:
            data.decrypt_sensitive_fields()
        
        return [data.to_dict(include_sensitive=True) for data in health_data]
        
    except Exception as e:
        logger.error(f"Error retrieving health data: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve health data")

@router.get("/{data_id}", response_model=HealthDataResponse)
async def get_health_data_by_id(
    data_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific health data entry by ID"""
    try:
        health_data = db.query(HealthData).filter(
            HealthData.id == data_id,
            HealthData.user_id == current_user.id
        ).first()
        
        if not health_data:
            raise HTTPException(status_code=404, detail="Health data not found")
        
        health_data.decrypt_sensitive_fields()
        return health_data.to_dict(include_sensitive=True)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving health data by ID: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve health data")

@router.put("/{data_id}", response_model=HealthDataResponse)
async def update_health_data(
    data_id: int,
    data: HealthDataUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update health data entry"""
    try:
        health_data = db.query(HealthData).filter(
            HealthData.id == data_id,
            HealthData.user_id == current_user.id
        ).first()
        
        if not health_data:
            raise HTTPException(status_code=404, detail="Health data not found")
        
        # Update fields
        if data.value is not None:
            health_data.value = data.value
        if data.unit is not None:
            health_data.unit = data.unit
        if data.notes is not None:
            health_data.notes = data.notes
        if data.confidence is not None:
            health_data.confidence = data.confidence
        
        health_data.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(health_data)
        
        health_data.decrypt_sensitive_fields()
        
        AuditLogger.log_health_event(
            event_type="health_data_updated",
            user_id=current_user.id,
            data_id=data_id,
            success=True
        )
        
        return health_data.to_dict(include_sensitive=True)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating health data: {e}")
        AuditLogger.log_health_event(
            event_type="health_data_updated",
            user_id=current_user.id,
            data_id=data_id,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to update health data")

@router.delete("/{data_id}")
async def delete_health_data(
    data_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete health data entry"""
    try:
        health_data = db.query(HealthData).filter(
            HealthData.id == data_id,
            HealthData.user_id == current_user.id
        ).first()
        
        if not health_data:
            raise HTTPException(status_code=404, detail="Health data not found")
        
        db.delete(health_data)
        db.commit()
        
        AuditLogger.log_health_event(
            event_type="health_data_deleted",
            user_id=current_user.id,
            data_id=data_id,
            success=True
        )
        
        return {"message": "Health data deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting health data: {e}")
        AuditLogger.log_health_event(
            event_type="health_data_deleted",
            user_id=current_user.id,
            data_id=data_id,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to delete health data")

@router.get("/types/summary")
async def get_health_data_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get summary of health data by type"""
    try:
        # Get count and latest entry for each data type
        summary = db.query(
            HealthData.data_type,
            db.func.count(HealthData.id).label('count'),
            db.func.max(HealthData.timestamp).label('latest_entry')
        ).filter(
            HealthData.user_id == current_user.id
        ).group_by(HealthData.data_type).all()
        
        return [
            {
                "data_type": item.data_type,
                "count": item.count,
                "latest_entry": item.latest_entry.isoformat() if item.latest_entry else None
            }
            for item in summary
        ]
        
    except Exception as e:
        logger.error(f"Error getting health data summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get health data summary")

@router.post("/export")
async def export_health_data(
    data_types: Optional[List[str]] = Query(None, description="Specific data types to export"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    format: str = Query("json", description="Export format (json, csv)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export health data"""
    try:
        query = db.query(HealthData).filter(HealthData.user_id == current_user.id)
        
        if data_types:
            query = query.filter(HealthData.data_type.in_(data_types))
        
        if start_date:
            query = query.filter(HealthData.timestamp >= start_date)
        
        if end_date:
            query = query.filter(HealthData.timestamp <= end_date)
        
        health_data = query.order_by(HealthData.timestamp.desc()).all()
        
        # Decrypt sensitive fields for export
        for data in health_data:
            data.decrypt_sensitive_fields()
        
        export_data = [data.to_dict(include_sensitive=True) for data in health_data]
        
        AuditLogger.log_health_event(
            event_type="health_data_exported",
            user_id=current_user.id,
            data_count=len(export_data),
            success=True
        )
        
        if format.lower() == "csv":
            # TODO: Implement CSV export
            return {"message": "CSV export not yet implemented", "data": export_data}
        else:
            return {
                "export_date": datetime.utcnow().isoformat(),
                "data_count": len(export_data),
                "data": export_data
            }
        
    except Exception as e:
        logger.error(f"Error exporting health data: {e}")
        AuditLogger.log_health_event(
            event_type="health_data_exported",
            user_id=current_user.id,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to export health data") 
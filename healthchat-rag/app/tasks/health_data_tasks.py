"""
Health data background tasks for HealthMate.

This module provides background tasks for:
- Health data synchronization
- Data validation and cleaning
- Health metrics calculation
- Data export and backup
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from celery import current_task

from app.celery_app import celery_app
from app.database import SessionLocal
from app.models.enhanced_health_models import HealthData, UserHealthProfile
from app.utils.performance_monitoring import monitor_custom_performance

logger = logging.getLogger(__name__)

@celery_app.task
@monitor_custom_performance("sync_health_data")
def sync_health_data():
    """
    Synchronize health data from external sources.
    
    This task runs every 15 minutes to sync health data
    from connected devices and external APIs.
    """
    try:
        db = SessionLocal()
        
        # Get users with active health data connections
        # This is a simplified example - in production you'd query actual connections
        users_with_connections = db.query(UserHealthProfile).filter(
            UserHealthProfile.has_external_connections == True
        ).all()
        
        synced_count = 0
        error_count = 0
        
        for user_profile in users_with_connections:
            try:
                # Sync data for each user
                result = sync_user_health_data(user_profile.user_id, db)
                if result["success"]:
                    synced_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to sync health data for user {user_profile.user_id}: {e}")
                error_count += 1
        
        logger.info(f"Health data sync completed: {synced_count} successful, {error_count} errors")
        
        return {
            "status": "completed",
            "synced_count": synced_count,
            "error_count": error_count,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health data sync task failed: {e}")
        raise
    finally:
        db.close()

@celery_app.task
@monitor_custom_performance("validate_health_data")
def validate_health_data(user_id: int):
    """
    Validate and clean health data for a specific user.
    
    Args:
        user_id: ID of the user whose data to validate
    """
    try:
        db = SessionLocal()
        
        # Get user's health data
        health_data = db.query(HealthData).filter(
            HealthData.user_id == user_id
        ).all()
        
        validated_count = 0
        cleaned_count = 0
        error_count = 0
        
        for data_point in health_data:
            try:
                # Validate data point
                if validate_data_point(data_point):
                    validated_count += 1
                    
                    # Clean data if needed
                    if clean_data_point(data_point):
                        cleaned_count += 1
                        
            except Exception as e:
                logger.error(f"Failed to validate data point {data_point.id}: {e}")
                error_count += 1
        
        logger.info(f"Health data validation completed for user {user_id}: {validated_count} validated, {cleaned_count} cleaned, {error_count} errors")
        
        return {
            "user_id": user_id,
            "validated_count": validated_count,
            "cleaned_count": cleaned_count,
            "error_count": error_count,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health data validation task failed for user {user_id}: {e}")
        raise
    finally:
        db.close()

@celery_app.task
@monitor_custom_performance("calculate_health_metrics")
def calculate_health_metrics(user_id: int):
    """
    Calculate health metrics for a specific user.
    
    Args:
        user_id: ID of the user whose metrics to calculate
    """
    try:
        db = SessionLocal()
        
        # Calculate various health metrics
        metrics = {}
        
        # BMI calculation
        metrics["bmi"] = calculate_bmi(user_id, db)
        
        # Blood pressure trends
        metrics["blood_pressure_trend"] = calculate_blood_pressure_trend(user_id, db)
        
        # Heart rate variability
        metrics["hrv"] = calculate_hrv(user_id, db)
        
        # Sleep quality score
        metrics["sleep_quality"] = calculate_sleep_quality(user_id, db)
        
        # Activity level
        metrics["activity_level"] = calculate_activity_level(user_id, db)
        
        # Overall health score
        metrics["health_score"] = calculate_overall_health_score(metrics)
        
        # Update user's health profile
        user_profile = db.query(UserHealthProfile).filter(
            UserHealthProfile.user_id == user_id
        ).first()
        
        if user_profile:
            user_profile.last_metrics_calculation = datetime.now()
            user_profile.health_metrics = metrics
            db.commit()
        
        logger.info(f"Health metrics calculated for user {user_id}")
        
        return {
            "user_id": user_id,
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health metrics calculation failed for user {user_id}: {e}")
        raise
    finally:
        db.close()

@celery_app.task
@monitor_custom_performance("export_health_data")
def export_health_data(user_id: int, export_format: str = "json"):
    """
    Export user's health data in specified format.
    
    Args:
        user_id: ID of the user whose data to export
        export_format: Format for export (json, csv, pdf)
    """
    try:
        db = SessionLocal()
        
        # Get user's health data
        health_data = db.query(HealthData).filter(
            HealthData.user_id == user_id
        ).all()
        
        # Convert to export format
        if export_format == "json":
            export_data = export_to_json(health_data)
        elif export_format == "csv":
            export_data = export_to_csv(health_data)
        elif export_format == "pdf":
            export_data = export_to_pdf(health_data)
        else:
            raise ValueError(f"Unsupported export format: {export_format}")
        
        # Store export file (in production, this would be to cloud storage)
        file_path = f"/tmp/health_export_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{export_format}"
        
        with open(file_path, 'w') as f:
            f.write(export_data)
        
        logger.info(f"Health data exported for user {user_id} in {export_format} format")
        
        return {
            "user_id": user_id,
            "export_format": export_format,
            "file_path": file_path,
            "data_points": len(health_data),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health data export failed for user {user_id}: {e}")
        raise
    finally:
        db.close()

@celery_app.task
@monitor_custom_performance("backup_health_data")
def backup_health_data():
    """
    Create backup of all health data.
    
    This task runs daily to create backups of health data.
    """
    try:
        db = SessionLocal()
        
        # Get all health data
        health_data = db.query(HealthData).all()
        
        # Create backup
        backup_data = {
            "timestamp": datetime.now().isoformat(),
            "total_records": len(health_data),
            "data": [data.to_dict() for data in health_data]
        }
        
        # Store backup (in production, this would be to cloud storage)
        backup_path = f"/tmp/health_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        import json
        with open(backup_path, 'w') as f:
            json.dump(backup_data, f, indent=2)
        
        logger.info(f"Health data backup created: {len(health_data)} records")
        
        return {
            "backup_path": backup_path,
            "total_records": len(health_data),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health data backup failed: {e}")
        raise
    finally:
        db.close()

# Helper functions

def sync_user_health_data(user_id: int, db) -> Dict[str, Any]:
    """Sync health data for a specific user."""
    # This would integrate with actual health APIs
    # For now, return a mock result
    return {
        "success": True,
        "synced_data_points": 10,
        "user_id": user_id
    }

def validate_data_point(data_point: HealthData) -> bool:
    """Validate a single health data point."""
    # Check for reasonable values
    if data_point.value is None:
        return False
    
    # Add more validation logic based on data type
    return True

def clean_data_point(data_point: HealthData) -> bool:
    """Clean a single health data point."""
    # Remove outliers, fix formatting, etc.
    # For now, return True (no cleaning needed)
    return True

def calculate_bmi(user_id: int, db) -> float:
    """Calculate BMI for a user."""
    # This would use actual height and weight data
    return 22.5  # Mock value

def calculate_blood_pressure_trend(user_id: int, db) -> Dict[str, Any]:
    """Calculate blood pressure trends."""
    return {
        "systolic_trend": "stable",
        "diastolic_trend": "stable",
        "average_systolic": 120,
        "average_diastolic": 80
    }

def calculate_hrv(user_id: int, db) -> float:
    """Calculate heart rate variability."""
    return 45.2  # Mock value

def calculate_sleep_quality(user_id: int, db) -> float:
    """Calculate sleep quality score."""
    return 8.5  # Mock value

def calculate_activity_level(user_id: int, db) -> str:
    """Calculate activity level."""
    return "moderate"  # Mock value

def calculate_overall_health_score(metrics: Dict[str, Any]) -> float:
    """Calculate overall health score from individual metrics."""
    # Simple weighted average
    weights = {
        "bmi": 0.2,
        "hrv": 0.2,
        "sleep_quality": 0.3,
        "activity_level": 0.3
    }
    
    score = 0
    for metric, weight in weights.items():
        if metric in metrics:
            if isinstance(metrics[metric], (int, float)):
                score += metrics[metric] * weight
            elif isinstance(metrics[metric], str):
                # Convert string metrics to numeric scores
                if metrics[metric] == "moderate":
                    score += 7.5 * weight
                elif metrics[metric] == "high":
                    score += 9.0 * weight
                else:
                    score += 5.0 * weight
    
    return round(score, 2)

def export_to_json(health_data: List[HealthData]) -> str:
    """Export health data to JSON format."""
    import json
    
    export_data = []
    for data in health_data:
        export_data.append({
            "id": data.id,
            "user_id": data.user_id,
            "metric_type": data.metric_type,
            "value": data.value,
            "timestamp": data.timestamp.isoformat() if data.timestamp else None,
            "unit": data.unit
        })
    
    return json.dumps(export_data, indent=2)

def export_to_csv(health_data: List[HealthData]) -> str:
    """Export health data to CSV format."""
    import csv
    from io import StringIO
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(["ID", "User ID", "Metric Type", "Value", "Timestamp", "Unit"])
    
    # Write data
    for data in health_data:
        writer.writerow([
            data.id,
            data.user_id,
            data.metric_type,
            data.value,
            data.timestamp.isoformat() if data.timestamp else "",
            data.unit or ""
        ])
    
    return output.getvalue()

def export_to_pdf(health_data: List[HealthData]) -> str:
    """Export health data to PDF format."""
    # This would use a library like reportlab to generate PDF
    # For now, return a simple text representation
    pdf_content = "Health Data Export\n"
    pdf_content += "=" * 20 + "\n\n"
    
    for data in health_data:
        pdf_content += f"ID: {data.id}\n"
        pdf_content += f"User ID: {data.user_id}\n"
        pdf_content += f"Metric: {data.metric_type}\n"
        pdf_content += f"Value: {data.value}\n"
        pdf_content += f"Timestamp: {data.timestamp}\n"
        pdf_content += f"Unit: {data.unit}\n"
        pdf_content += "-" * 20 + "\n"
    
    return pdf_content 
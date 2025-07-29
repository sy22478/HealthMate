"""
Health Visualization Router
Endpoints for health chart and graph data
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
from app.services.health_visualization import HealthVisualizationService
from app.utils.audit_logging import AuditLogger

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/visualization", tags=["Health Visualization"])

# Pydantic schemas
class ChartDataResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    message: Optional[str] = None

class ChartExportRequest(BaseModel):
    chart_type: str = Field(..., description="Type of chart to export")
    days: int = Field(30, ge=1, le=365, description="Number of days of data")
    format: str = Field("json", regex="^(json|csv)$", description="Export format")

# Visualization Endpoints

@router.get("/dashboard-charts", response_model=ChartDataResponse)
async def get_dashboard_charts(
    days: int = Query(30, ge=7, le=365, description="Number of days of data"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive dashboard charts data"""
    try:
        visualization_service = HealthVisualizationService(db)
        charts_data = visualization_service.generate_health_dashboard_charts(current_user.id, days)
        
        AuditLogger.log_health_event(
            event_type="dashboard_charts_requested",
            user_id=current_user.id,
            days=days,
            success=True
        )
        
        return ChartDataResponse(
            success=True,
            data=charts_data,
            message="Dashboard charts data retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting dashboard charts: {e}")
        AuditLogger.log_health_event(
            event_type="dashboard_charts_requested",
            user_id=current_user.id,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to get dashboard charts")

@router.get("/chart/{chart_type}")
async def get_specific_chart(
    chart_type: str,
    days: int = Query(30, ge=7, le=365, description="Number of days of data"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific chart data"""
    try:
        visualization_service = HealthVisualizationService(db)
        chart_data = visualization_service.generate_export_data(current_user.id, chart_type, days)
        
        if "error" in chart_data:
            raise HTTPException(status_code=400, detail=chart_data["error"])
        
        AuditLogger.log_health_event(
            event_type="specific_chart_requested",
            user_id=current_user.id,
            chart_type=chart_type,
            days=days,
            success=True
        )
        
        return {
            "success": True,
            "chart_type": chart_type,
            "data": chart_data,
            "days": days,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting specific chart: {e}")
        AuditLogger.log_health_event(
            event_type="specific_chart_requested",
            user_id=current_user.id,
            chart_type=chart_type,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to get chart data")

@router.get("/available-charts")
async def get_available_charts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of available chart types"""
    try:
        available_charts = [
            {
                "type": "health_trends",
                "name": "Health Trends Over Time",
                "description": "Line chart showing health data trends",
                "category": "trends"
            },
            {
                "type": "symptom_distribution",
                "name": "Symptom Distribution",
                "description": "Pie chart showing symptom frequency and severity",
                "category": "symptoms"
            },
            {
                "type": "medication_adherence",
                "name": "Medication Adherence",
                "description": "Line chart showing medication adherence over time",
                "category": "medications"
            },
            {
                "type": "data_completeness",
                "name": "Data Completeness",
                "description": "Doughnut chart showing data completeness by type",
                "category": "overview"
            },
            {
                "type": "health_score_timeline",
                "name": "Health Score Timeline",
                "description": "Line chart showing health score over time",
                "category": "overview"
            },
            {
                "type": "correlation_matrix",
                "name": "Health Data Correlations",
                "description": "Heatmap showing correlations between health data types",
                "category": "analytics"
            }
        ]
        
        AuditLogger.log_health_event(
            event_type="available_charts_requested",
            user_id=current_user.id,
            success=True
        )
        
        return {
            "success": True,
            "charts": available_charts,
            "total_charts": len(available_charts)
        }
        
    except Exception as e:
        logger.error(f"Error getting available charts: {e}")
        AuditLogger.log_health_event(
            event_type="available_charts_requested",
            user_id=current_user.id,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to get available charts")

@router.post("/export-chart")
async def export_chart_data(
    request: ChartExportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export chart data in specified format"""
    try:
        visualization_service = HealthVisualizationService(db)
        chart_data = visualization_service.generate_export_data(
            current_user.id, 
            request.chart_type, 
            request.days
        )
        
        if "error" in chart_data:
            raise HTTPException(status_code=400, detail=chart_data["error"])
        
        export_data = {
            "chart_type": request.chart_type,
            "export_date": datetime.utcnow().isoformat(),
            "data_period_days": request.days,
            "format": request.format,
            "data": chart_data
        }
        
        AuditLogger.log_health_event(
            event_type="chart_export_requested",
            user_id=current_user.id,
            chart_type=request.chart_type,
            format=request.format,
            success=True
        )
        
        if request.format.lower() == "csv":
            # TODO: Implement CSV export
            return {
                "message": "CSV export not yet implemented",
                "data": export_data
            }
        else:
            return export_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting chart data: {e}")
        AuditLogger.log_health_event(
            event_type="chart_export_requested",
            user_id=current_user.id,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to export chart data")

@router.get("/chart-config/{chart_type}")
async def get_chart_configuration(
    chart_type: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get configuration options for specific chart type"""
    try:
        chart_configs = {
            "health_trends": {
                "type": "line",
                "options": {
                    "responsive": True,
                    "scales": {
                        "x": {"type": "time", "time": {"unit": "day"}},
                        "y": {"beginAtZero": False}
                    },
                    "plugins": {
                        "legend": {"display": True},
                        "tooltip": {"enabled": True}
                    }
                },
                "data_structure": {
                    "type": "object",
                    "properties": {
                        "datasets": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "label": {"type": "string"},
                                    "data": {"type": "array"},
                                    "borderColor": {"type": "string"},
                                    "backgroundColor": {"type": "string"}
                                }
                            }
                        }
                    }
                }
            },
            "symptom_distribution": {
                "type": "pie",
                "options": {
                    "responsive": True,
                    "plugins": {
                        "legend": {"display": True},
                        "tooltip": {"enabled": True}
                    }
                },
                "data_structure": {
                    "type": "object",
                    "properties": {
                        "datasets": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "data": {"type": "array"},
                                    "backgroundColor": {"type": "array"},
                                    "labels": {"type": "array"}
                                }
                            }
                        }
                    }
                }
            },
            "medication_adherence": {
                "type": "line",
                "options": {
                    "responsive": True,
                    "scales": {
                        "x": {"type": "time", "time": {"unit": "day"}},
                        "y": {"beginAtZero": True, "max": 100}
                    },
                    "plugins": {
                        "legend": {"display": True},
                        "tooltip": {"enabled": True}
                    }
                },
                "data_structure": {
                    "type": "object",
                    "properties": {
                        "datasets": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "label": {"type": "string"},
                                    "data": {"type": "array"},
                                    "borderColor": {"type": "string"},
                                    "backgroundColor": {"type": "string"},
                                    "fill": {"type": "boolean"}
                                }
                            }
                        }
                    }
                }
            },
            "data_completeness": {
                "type": "doughnut",
                "options": {
                    "responsive": True,
                    "plugins": {
                        "legend": {"display": True},
                        "tooltip": {"enabled": True}
                    }
                },
                "data_structure": {
                    "type": "object",
                    "properties": {
                        "datasets": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "data": {"type": "array"},
                                    "backgroundColor": {"type": "array"},
                                    "labels": {"type": "array"}
                                }
                            }
                        }
                    }
                }
            },
            "health_score_timeline": {
                "type": "line",
                "options": {
                    "responsive": True,
                    "scales": {
                        "x": {"type": "time", "time": {"unit": "week"}},
                        "y": {"beginAtZero": True, "max": 100}
                    },
                    "plugins": {
                        "legend": {"display": True},
                        "tooltip": {"enabled": True}
                    }
                },
                "data_structure": {
                    "type": "object",
                    "properties": {
                        "datasets": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "label": {"type": "string"},
                                    "data": {"type": "array"},
                                    "borderColor": {"type": "string"},
                                    "backgroundColor": {"type": "string"},
                                    "fill": {"type": "boolean"}
                                }
                            }
                        }
                    }
                }
            },
            "correlation_matrix": {
                "type": "heatmap",
                "options": {
                    "responsive": True,
                    "plugins": {
                        "legend": {"display": True},
                        "tooltip": {"enabled": True}
                    }
                },
                "data_structure": {
                    "type": "object",
                    "properties": {
                        "labels": {"type": "array"},
                        "data": {"type": "array"},
                        "colorScale": {"type": "string"}
                    }
                }
            }
        }
        
        if chart_type not in chart_configs:
            raise HTTPException(status_code=404, detail=f"Chart type '{chart_type}' not found")
        
        AuditLogger.log_health_event(
            event_type="chart_config_requested",
            user_id=current_user.id,
            chart_type=chart_type,
            success=True
        )
        
        return {
            "success": True,
            "chart_type": chart_type,
            "config": chart_configs[chart_type]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chart configuration: {e}")
        AuditLogger.log_health_event(
            event_type="chart_config_requested",
            user_id=current_user.id,
            chart_type=chart_type,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to get chart configuration")

@router.get("/chart-preview/{chart_type}")
async def get_chart_preview(
    chart_type: str,
    days: int = Query(7, ge=1, le=30, description="Number of days for preview"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a preview of chart data with limited data points"""
    try:
        visualization_service = HealthVisualizationService(db)
        chart_data = visualization_service.generate_export_data(current_user.id, chart_type, days)
        
        if "error" in chart_data:
            raise HTTPException(status_code=400, detail=chart_data["error"])
        
        # Limit data points for preview
        if "datasets" in chart_data and chart_data["datasets"]:
            for dataset in chart_data["datasets"]:
                if "data" in dataset and len(dataset["data"]) > 10:
                    dataset["data"] = dataset["data"][:10]  # Limit to 10 data points
        
        AuditLogger.log_health_event(
            event_type="chart_preview_requested",
            user_id=current_user.id,
            chart_type=chart_type,
            days=days,
            success=True
        )
        
        return {
            "success": True,
            "chart_type": chart_type,
            "preview_data": chart_data,
            "preview_days": days,
            "note": "Limited data points for preview"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chart preview: {e}")
        AuditLogger.log_health_event(
            event_type="chart_preview_requested",
            user_id=current_user.id,
            chart_type=chart_type,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to get chart preview") 
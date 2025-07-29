"""
Advanced Health Analytics Router
Comprehensive analytics endpoints for health dashboard
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
from app.services.health_insights_service import HealthInsightsService
from app.utils.audit_logging import AuditLogger
import json

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/advanced-analytics", tags=["Advanced Analytics"])

# Pydantic schemas
class DashboardDataResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    message: Optional[str] = None

class AnalyticsFilter(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    data_types: Optional[List[str]] = None
    include_trends: bool = True
    include_insights: bool = True

# Advanced Analytics Endpoints

@router.get("/dashboard", response_model=DashboardDataResponse)
async def get_comprehensive_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive health dashboard data"""
    try:
        analytics_service = HealthAnalyticsService(db)
        insights_service = HealthInsightsService(db)
        
        # Get all analytics data
        health_score = analytics_service.get_health_score(current_user.id)
        symptom_analysis = analytics_service.get_symptom_analysis(current_user.id, 30)
        medication_adherence = analytics_service.get_medication_adherence(current_user.id, 30)
        recommendations = analytics_service.get_health_recommendations(current_user.id)
        health_insights = insights_service.generate_health_insights(current_user.id)
        
        # Compile dashboard data
        dashboard_data = {
            "overview": {
                "health_score": health_score.get("overall_score", 0),
                "total_health_data_points": health_score.get("data_summary", {}).get("health_data_points", 0),
                "total_symptoms": symptom_analysis.get("total_symptoms", 0),
                "medication_adherence_rate": medication_adherence.get("adherence_rate", 0),
                "last_updated": datetime.utcnow().isoformat()
            },
            "health_score": health_score,
            "symptom_analysis": symptom_analysis,
            "medication_adherence": medication_adherence,
            "recommendations": recommendations,
            "health_insights": health_insights,
            "quick_stats": {
                "data_types_tracked": len(health_score.get("data_summary", {}).get("data_types", [])),
                "severe_symptoms": symptom_analysis.get("severity_distribution", {}).get("severe", 0),
                "active_medications": medication_adherence.get("unique_medications", 0),
                "risk_factors": len(health_insights.get("risk_factors", []))
            }
        }
        
        AuditLogger.log_health_event(
            event_type="comprehensive_dashboard_requested",
            user_id=current_user.id,
            success=True
        )
        
        return DashboardDataResponse(
            success=True,
            data=dashboard_data,
            message="Dashboard data retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting comprehensive dashboard: {e}")
        AuditLogger.log_health_event(
            event_type="comprehensive_dashboard_requested",
            user_id=current_user.id,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to get dashboard data")

@router.get("/trends/comprehensive")
async def get_comprehensive_trends(
    data_types: Optional[List[str]] = Query(None, description="Specific data types to analyze"),
    days: int = Query(30, ge=7, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive trend analysis for multiple data types"""
    try:
        analytics_service = HealthAnalyticsService(db)
        
        # Get available data types if not specified
        if not data_types:
            from app.models.health_data import HealthData
            available_types = db.query(HealthData.data_type).filter(
                HealthData.user_id == current_user.id
            ).distinct().all()
            data_types = [dt[0] for dt in available_types]
        
        # Analyze trends for each data type
        trends_data = {}
        for data_type in data_types:
            try:
                trend = analytics_service.get_health_trends(current_user.id, data_type, days)
                trends_data[data_type] = trend
            except Exception as e:
                logger.warning(f"Failed to analyze trends for {data_type}: {e}")
                trends_data[data_type] = {"error": str(e)}
        
        # Generate summary insights
        summary_insights = []
        improving_trends = []
        concerning_trends = []
        
        for data_type, trend_data in trends_data.items():
            if "error" in trend_data:
                continue
            
            trend = trend_data.get("trend", "unknown")
            if trend == "improving":
                improving_trends.append(data_type)
            elif trend == "concerning":
                concerning_trends.append(data_type)
            
            if trend_data.get("insights"):
                summary_insights.extend(trend_data["insights"])
        
        comprehensive_trends = {
            "trends_by_type": trends_data,
            "summary": {
                "total_data_types": len(data_types),
                "improving_trends": improving_trends,
                "concerning_trends": concerning_trends,
                "stable_trends": [dt for dt in data_types if trends_data.get(dt, {}).get("trend") == "stable"],
                "insights": summary_insights[:5]  # Top 5 insights
            },
            "analysis_period_days": days
        }
        
        AuditLogger.log_health_event(
            event_type="comprehensive_trends_requested",
            user_id=current_user.id,
            data_types_count=len(data_types),
            days=days,
            success=True
        )
        
        return comprehensive_trends
        
    except Exception as e:
        logger.error(f"Error getting comprehensive trends: {e}")
        AuditLogger.log_health_event(
            event_type="comprehensive_trends_requested",
            user_id=current_user.id,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to get comprehensive trends")

@router.get("/correlations")
async def get_health_correlations(
    primary_data_type: str = Query(..., description="Primary data type to analyze"),
    secondary_data_types: Optional[List[str]] = Query(None, description="Secondary data types to correlate"),
    days: int = Query(30, ge=7, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze correlations between different health data types"""
    try:
        from app.models.health_data import HealthData
        from sqlalchemy import and_
        import statistics
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get primary data
        primary_data = db.query(HealthData).filter(
            and_(
                HealthData.user_id == current_user.id,
                HealthData.data_type == primary_data_type,
                HealthData.timestamp >= start_date
            )
        ).order_by(HealthData.timestamp.asc()).all()
        
        if not primary_data:
            raise HTTPException(status_code=404, detail=f"No {primary_data_type} data found")
        
        # Decrypt and extract primary values
        for data in primary_data:
            data.decrypt_sensitive_fields()
        
        primary_values = []
        primary_timestamps = []
        
        for data in primary_data:
            try:
                if data.value.startswith('{'):
                    parsed = json.loads(data.value)
                    if isinstance(parsed, dict):
                        for key in ['value', 'systolic', 'diastolic', 'reading']:
                            if key in parsed and isinstance(parsed[key], (int, float)):
                                primary_values.append(float(parsed[key]))
                                primary_timestamps.append(data.timestamp)
                                break
                else:
                    primary_values.append(float(data.value))
                    primary_timestamps.append(data.timestamp)
            except (ValueError, json.JSONDecodeError, KeyError):
                continue
        
        if len(primary_values) < 2:
            raise HTTPException(status_code=400, detail="Insufficient primary data for correlation analysis")
        
        # Get secondary data types if not specified
        if not secondary_data_types:
            available_types = db.query(HealthData.data_type).filter(
                and_(
                    HealthData.user_id == current_user.id,
                    HealthData.data_type != primary_data_type
                )
            ).distinct().all()
            secondary_data_types = [dt[0] for dt in available_types]
        
        # Analyze correlations
        correlations = {}
        for secondary_type in secondary_data_types:
            try:
                secondary_data = db.query(HealthData).filter(
                    and_(
                        HealthData.user_id == current_user.id,
                        HealthData.data_type == secondary_type,
                        HealthData.timestamp >= start_date
                    )
                ).order_by(HealthData.timestamp.asc()).all()
                
                if not secondary_data:
                    continue
                
                # Decrypt and extract secondary values
                for data in secondary_data:
                    data.decrypt_sensitive_fields()
                
                secondary_values = []
                secondary_timestamps = []
                
                for data in secondary_data:
                    try:
                        if data.value.startswith('{'):
                            parsed = json.loads(data.value)
                            if isinstance(parsed, dict):
                                for key in ['value', 'systolic', 'diastolic', 'reading']:
                                    if key in parsed and isinstance(parsed[key], (int, float)):
                                        secondary_values.append(float(parsed[key]))
                                        secondary_timestamps.append(data.timestamp)
                                        break
                        else:
                            secondary_values.append(float(data.value))
                            secondary_timestamps.append(data.timestamp)
                    except (ValueError, json.JSONDecodeError, KeyError):
                        continue
                
                if len(secondary_values) < 2:
                    continue
                
                # Calculate correlation (simplified approach)
                # For production, use proper statistical correlation methods
                correlation_strength = self._calculate_correlation_strength(
                    primary_values, secondary_values
                )
                
                correlations[secondary_type] = {
                    "correlation_strength": correlation_strength,
                    "data_points": min(len(primary_values), len(secondary_values)),
                    "interpretation": self._interpret_correlation(correlation_strength)
                }
                
            except Exception as e:
                logger.warning(f"Failed to analyze correlation with {secondary_type}: {e}")
                correlations[secondary_type] = {"error": str(e)}
        
        correlation_analysis = {
            "primary_data_type": primary_data_type,
            "secondary_data_types": secondary_data_types,
            "correlations": correlations,
            "analysis_period_days": days,
            "primary_data_summary": {
                "data_points": len(primary_values),
                "average": round(statistics.mean(primary_values), 2),
                "range": f"{round(min(primary_values), 2)} - {round(max(primary_values), 2)}"
            }
        }
        
        AuditLogger.log_health_event(
            event_type="correlation_analysis_requested",
            user_id=current_user.id,
            primary_data_type=primary_data_type,
            secondary_types_count=len(secondary_data_types),
            success=True
        )
        
        return correlation_analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting health correlations: {e}")
        AuditLogger.log_health_event(
            event_type="correlation_analysis_requested",
            user_id=current_user.id,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to get health correlations")
    
    def _calculate_correlation_strength(self, values1: List[float], values2: List[float]) -> float:
        """Calculate correlation strength between two sets of values"""
        try:
            # Use the shorter list length
            min_length = min(len(values1), len(values2))
            if min_length < 2:
                return 0.0
            
            # Take the first min_length values from each list
            v1 = values1[:min_length]
            v2 = values2[:min_length]
            
            # Calculate correlation coefficient
            mean1 = statistics.mean(v1)
            mean2 = statistics.mean(v2)
            
            numerator = sum((x - mean1) * (y - mean2) for x, y in zip(v1, v2))
            denominator1 = sum((x - mean1) ** 2 for x in v1)
            denominator2 = sum((y - mean2) ** 2 for y in v2)
            
            if denominator1 == 0 or denominator2 == 0:
                return 0.0
            
            correlation = numerator / (denominator1 * denominator2) ** 0.5
            return round(correlation, 3)
            
        except Exception as e:
            logger.error(f"Error calculating correlation: {e}")
            return 0.0
    
    def _interpret_correlation(self, correlation: float) -> str:
        """Interpret correlation strength"""
        abs_corr = abs(correlation)
        if abs_corr >= 0.7:
            return "Strong correlation"
        elif abs_corr >= 0.4:
            return "Moderate correlation"
        elif abs_corr >= 0.2:
            return "Weak correlation"
        else:
            return "No significant correlation"

@router.get("/predictions")
async def get_health_predictions(
    data_type: str = Query(..., description="Data type to predict"),
    prediction_days: int = Query(7, ge=1, le=30, description="Number of days to predict"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get health predictions based on historical data"""
    try:
        from app.models.health_data import HealthData
        from sqlalchemy import and_
        import statistics
        
        # Get historical data (last 90 days for better prediction)
        start_date = datetime.utcnow() - timedelta(days=90)
        
        historical_data = db.query(HealthData).filter(
            and_(
                HealthData.user_id == current_user.id,
                HealthData.data_type == data_type,
                HealthData.timestamp >= start_date
            )
        ).order_by(HealthData.timestamp.asc()).all()
        
        if len(historical_data) < 5:
            raise HTTPException(status_code=400, detail="Insufficient historical data for prediction")
        
        # Decrypt and extract values
        for data in historical_data:
            data.decrypt_sensitive_fields()
        
        values = []
        timestamps = []
        
        for data in historical_data:
            try:
                if data.value.startswith('{'):
                    parsed = json.loads(data.value)
                    if isinstance(parsed, dict):
                        for key in ['value', 'systolic', 'diastolic', 'reading']:
                            if key in parsed and isinstance(parsed[key], (int, float)):
                                values.append(float(parsed[key]))
                                timestamps.append(data.timestamp)
                                break
                else:
                    values.append(float(data.value))
                    timestamps.append(data.timestamp)
            except (ValueError, json.JSONDecodeError, KeyError):
                continue
        
        if len(values) < 5:
            raise HTTPException(status_code=400, detail="Insufficient numeric data for prediction")
        
        # Simple prediction using trend analysis
        predictions = self._generate_simple_predictions(values, prediction_days)
        
        # Calculate confidence intervals
        confidence_intervals = self._calculate_confidence_intervals(values, predictions)
        
        prediction_data = {
            "data_type": data_type,
            "historical_data_points": len(values),
            "prediction_days": prediction_days,
            "predictions": predictions,
            "confidence_intervals": confidence_intervals,
            "trend_analysis": {
                "current_trend": self._analyze_trend(values),
                "prediction_confidence": self._calculate_prediction_confidence(values),
                "data_quality": self._assess_data_quality(values)
            },
            "disclaimer": "These predictions are based on historical data patterns and should not replace professional medical advice."
        }
        
        AuditLogger.log_health_event(
            event_type="health_predictions_requested",
            user_id=current_user.id,
            data_type=data_type,
            prediction_days=prediction_days,
            success=True
        )
        
        return prediction_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting health predictions: {e}")
        AuditLogger.log_health_event(
            event_type="health_predictions_requested",
            user_id=current_user.id,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to get health predictions")
    
    def _generate_simple_predictions(self, values: List[float], days: int) -> List[Dict[str, Any]]:
        """Generate simple predictions based on trend analysis"""
        try:
            if len(values) < 2:
                return []
            
            # Calculate trend
            recent_values = values[-10:] if len(values) >= 10 else values
            if len(recent_values) < 2:
                return []
            
            # Simple linear trend
            x_values = list(range(len(recent_values)))
            y_values = recent_values
            
            # Calculate slope (trend)
            n = len(x_values)
            sum_x = sum(x_values)
            sum_y = sum(y_values)
            sum_xy = sum(x * y for x, y in zip(x_values, y_values))
            sum_x2 = sum(x * x for x in x_values)
            
            if n * sum_x2 - sum_x * sum_x == 0:
                slope = 0
            else:
                slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            
            # Generate predictions
            predictions = []
            last_value = recent_values[-1]
            
            for day in range(1, days + 1):
                predicted_value = last_value + (slope * day)
                predictions.append({
                    "day": day,
                    "predicted_value": round(predicted_value, 2),
                    "date": (datetime.utcnow() + timedelta(days=day)).isoformat()
                })
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error generating predictions: {e}")
            return []
    
    def _calculate_confidence_intervals(self, values: List[float], predictions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate confidence intervals for predictions"""
        try:
            if not values or not predictions:
                return []
            
            # Calculate standard deviation of historical data
            std_dev = statistics.stdev(values) if len(values) > 1 else 0
            
            confidence_intervals = []
            for pred in predictions:
                # 95% confidence interval (±2 standard deviations)
                margin_of_error = 2 * std_dev
                confidence_intervals.append({
                    "day": pred["day"],
                    "lower_bound": round(pred["predicted_value"] - margin_of_error, 2),
                    "upper_bound": round(pred["predicted_value"] + margin_of_error, 2),
                    "confidence_level": 0.95
                })
            
            return confidence_intervals
            
        except Exception as e:
            logger.error(f"Error calculating confidence intervals: {e}")
            return []
    
    def _analyze_trend(self, values: List[float]) -> str:
        """Analyze the trend of values"""
        try:
            if len(values) < 2:
                return "insufficient_data"
            
            # Compare first and last third of data
            third = len(values) // 3
            if third < 1:
                return "insufficient_data"
            
            first_third = values[:third]
            last_third = values[-third:]
            
            first_avg = statistics.mean(first_third)
            last_avg = statistics.mean(last_third)
            
            change_percent = ((last_avg - first_avg) / first_avg) * 100 if first_avg != 0 else 0
            
            if change_percent > 5:
                return "increasing"
            elif change_percent < -5:
                return "decreasing"
            else:
                return "stable"
                
        except Exception as e:
            logger.error(f"Error analyzing trend: {e}")
            return "unknown"
    
    def _calculate_prediction_confidence(self, values: List[float]) -> str:
        """Calculate confidence level for predictions"""
        try:
            if len(values) < 5:
                return "low"
            elif len(values) < 15:
                return "medium"
            else:
                return "high"
        except Exception as e:
            logger.error(f"Error calculating prediction confidence: {e}")
            return "unknown"
    
    def _assess_data_quality(self, values: List[float]) -> str:
        """Assess the quality of data for predictions"""
        try:
            if len(values) < 5:
                return "poor"
            
            # Calculate coefficient of variation
            mean_val = statistics.mean(values)
            std_dev = statistics.stdev(values) if len(values) > 1 else 0
            
            if mean_val == 0:
                return "poor"
            
            cv = (std_dev / mean_val) * 100
            
            if cv < 10:
                return "excellent"
            elif cv < 20:
                return "good"
            elif cv < 30:
                return "fair"
            else:
                return "poor"
                
        except Exception as e:
            logger.error(f"Error assessing data quality: {e}")
            return "unknown"

@router.get("/export/analytics")
async def export_analytics_data(
    format: str = Query("json", regex="^(json|csv)$", description="Export format"),
    include_insights: bool = Query(True, description="Include insights in export"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export comprehensive analytics data"""
    try:
        analytics_service = HealthAnalyticsService(db)
        insights_service = HealthInsightsService(db)
        
        # Get all analytics data
        health_score = analytics_service.get_health_score(current_user.id)
        symptom_analysis = analytics_service.get_symptom_analysis(current_user.id, 30)
        medication_adherence = analytics_service.get_medication_adherence(current_user.id, 30)
        recommendations = analytics_service.get_health_recommendations(current_user.id)
        
        export_data = {
            "export_date": datetime.utcnow().isoformat(),
            "user_id": current_user.id,
            "health_score": health_score,
            "symptom_analysis": symptom_analysis,
            "medication_adherence": medication_adherence,
            "recommendations": recommendations
        }
        
        if include_insights:
            health_insights = insights_service.generate_health_insights(current_user.id)
            export_data["health_insights"] = health_insights
        
        AuditLogger.log_health_event(
            event_type="analytics_export_requested",
            user_id=current_user.id,
            format=format,
            success=True
        )
        
        if format.lower() == "csv":
            # TODO: Implement CSV export
            return {"message": "CSV export not yet implemented", "data": export_data}
        else:
            return export_data
        
    except Exception as e:
        logger.error(f"Error exporting analytics data: {e}")
        AuditLogger.log_health_event(
            event_type="analytics_export_requested",
            user_id=current_user.id,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to export analytics data") 
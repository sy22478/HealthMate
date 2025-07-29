"""
Health Visualization Service
Provides chart and graph data for health analytics
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from app.models.health_data import HealthData, SymptomLog, MedicationLog
from app.models.user import User
from app.utils.encryption_utils import encryption_manager
import json
import statistics

logger = logging.getLogger(__name__)

class HealthVisualizationService:
    """Service for generating visualization data for health analytics"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_health_dashboard_charts(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive chart data for health dashboard"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            charts_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "charts": {
                    "health_trends": self._generate_health_trends_chart(user_id, start_date),
                    "symptom_distribution": self._generate_symptom_distribution_chart(user_id, start_date),
                    "medication_adherence": self._generate_medication_adherence_chart(user_id, start_date),
                    "data_completeness": self._generate_data_completeness_chart(user_id, start_date),
                    "health_score_timeline": self._generate_health_score_timeline(user_id, start_date),
                    "correlation_matrix": self._generate_correlation_matrix(user_id, start_date)
                }
            }
            
            return charts_data
            
        except Exception as e:
            logger.error(f"Error generating dashboard charts: {e}")
            return {"error": str(e), "timestamp": datetime.utcnow().isoformat()}
    
    def _generate_health_trends_chart(self, user_id: int, start_date: datetime) -> Dict[str, Any]:
        """Generate health trends chart data"""
        try:
            # Get health data by type
            health_data = self.db.query(HealthData).filter(
                and_(
                    HealthData.user_id == user_id,
                    HealthData.timestamp >= start_date
                )
            ).order_by(HealthData.timestamp.asc()).all()
            
            # Decrypt sensitive fields
            for data in health_data:
                data.decrypt_sensitive_fields()
            
            # Group by data type and date
            data_by_type = {}
            for data in health_data:
                if data.data_type not in data_by_type:
                    data_by_type[data.data_type] = []
                
                try:
                    # Extract numeric value
                    if data.value.startswith('{'):
                        parsed = json.loads(data.value)
                        if isinstance(parsed, dict):
                            for key in ['value', 'systolic', 'diastolic', 'reading']:
                                if key in parsed and isinstance(parsed[key], (int, float)):
                                    data_by_type[data.data_type].append({
                                        'date': data.timestamp.date().isoformat(),
                                        'value': float(parsed[key]),
                                        'timestamp': data.timestamp.isoformat()
                                    })
                                    break
                    else:
                        data_by_type[data.data_type].append({
                            'date': data.timestamp.date().isoformat(),
                            'value': float(data.value),
                            'timestamp': data.timestamp.isoformat()
                        })
                except (ValueError, json.JSONDecodeError, KeyError):
                    continue
            
            # Generate chart data
            chart_data = {
                "type": "line",
                "title": "Health Trends Over Time",
                "x_axis": "Date",
                "y_axis": "Value",
                "datasets": []
            }
            
            for data_type, data_points in data_by_type.items():
                if len(data_points) < 2:
                    continue
                
                # Sort by date
                data_points.sort(key=lambda x: x['timestamp'])
                
                dataset = {
                    "label": data_type.replace('_', ' ').title(),
                    "data": [
                        {
                            "x": point['date'],
                            "y": point['value']
                        }
                        for point in data_points
                    ],
                    "borderColor": self._get_color_for_data_type(data_type),
                    "backgroundColor": self._get_color_for_data_type(data_type, alpha=0.1),
                    "fill": False
                }
                
                chart_data["datasets"].append(dataset)
            
            return chart_data
            
        except Exception as e:
            logger.error(f"Error generating health trends chart: {e}")
            return {"error": str(e)}
    
    def _generate_symptom_distribution_chart(self, user_id: int, start_date: datetime) -> Dict[str, Any]:
        """Generate symptom distribution chart data"""
        try:
            symptoms = self.db.query(SymptomLog).filter(
                and_(
                    SymptomLog.user_id == user_id,
                    SymptomLog.timestamp >= start_date
                )
            ).all()
            
            # Decrypt sensitive fields
            for symptom in symptoms:
                symptom.decrypt_sensitive_fields()
            
            # Count symptoms by type and severity
            symptom_counts = {}
            severity_counts = {"mild": 0, "moderate": 0, "severe": 0}
            
            for symptom in symptoms:
                # Count by symptom type
                if symptom.symptom not in symptom_counts:
                    symptom_counts[symptom.symptom] = 0
                symptom_counts[symptom.symptom] += 1
                
                # Count by severity
                severity_counts[symptom.severity] += 1
            
            # Generate pie chart for symptom types
            symptom_pie_data = {
                "type": "pie",
                "title": "Symptom Distribution",
                "datasets": [{
                    "data": list(symptom_counts.values()),
                    "backgroundColor": self._generate_colors(len(symptom_counts)),
                    "labels": list(symptom_counts.keys())
                }]
            }
            
            # Generate bar chart for severity
            severity_bar_data = {
                "type": "bar",
                "title": "Symptom Severity Distribution",
                "x_axis": "Severity",
                "y_axis": "Count",
                "datasets": [{
                    "label": "Symptom Count",
                    "data": list(severity_counts.values()),
                    "backgroundColor": ["#4CAF50", "#FF9800", "#F44336"],
                    "labels": list(severity_counts.keys())
                }]
            }
            
            return {
                "symptom_types": symptom_pie_data,
                "severity_distribution": severity_bar_data,
                "total_symptoms": len(symptoms)
            }
            
        except Exception as e:
            logger.error(f"Error generating symptom distribution chart: {e}")
            return {"error": str(e)}
    
    def _generate_medication_adherence_chart(self, user_id: int, start_date: datetime) -> Dict[str, Any]:
        """Generate medication adherence chart data"""
        try:
            medications = self.db.query(MedicationLog).filter(
                and_(
                    MedicationLog.user_id == user_id,
                    MedicationLog.taken_at >= start_date
                )
            ).all()
            
            # Decrypt sensitive fields
            for med in medications:
                med.decrypt_sensitive_fields()
            
            # Group by medication and date
            med_by_date = {}
            for med in medications:
                date_key = med.taken_at.date().isoformat()
                if date_key not in med_by_date:
                    med_by_date[date_key] = {}
                
                if med.medication_name not in med_by_date[date_key]:
                    med_by_date[date_key][med.medication_name] = 0
                med_by_date[date_key][med.medication_name] += 1
            
            # Calculate adherence rate by date
            adherence_data = []
            unique_meds = len(set(med.medication_name for med in medications))
            
            for date, med_counts in sorted(med_by_date.items()):
                total_doses = sum(med_counts.values())
                adherence_rate = (total_doses / unique_meds * 100) if unique_meds > 0 else 0
                adherence_data.append({
                    "x": date,
                    "y": round(adherence_rate, 1)
                })
            
            # Generate chart data
            chart_data = {
                "type": "line",
                "title": "Medication Adherence Over Time",
                "x_axis": "Date",
                "y_axis": "Adherence Rate (%)",
                "datasets": [{
                    "label": "Adherence Rate",
                    "data": adherence_data,
                    "borderColor": "#2196F3",
                    "backgroundColor": "rgba(33, 150, 243, 0.1)",
                    "fill": True
                }]
            }
            
            return chart_data
            
        except Exception as e:
            logger.error(f"Error generating medication adherence chart: {e}")
            return {"error": str(e)}
    
    def _generate_data_completeness_chart(self, user_id: int, start_date: datetime) -> Dict[str, Any]:
        """Generate data completeness chart"""
        try:
            # Get all health data
            health_data = self.db.query(HealthData).filter(
                and_(
                    HealthData.user_id == user_id,
                    HealthData.timestamp >= start_date
                )
            ).all()
            
            # Count data by type
            data_counts = {}
            for data in health_data:
                if data.data_type not in data_counts:
                    data_counts[data.data_type] = 0
                data_counts[data.data_type] += 1
            
            # Generate chart data
            chart_data = {
                "type": "doughnut",
                "title": "Data Completeness by Type",
                "datasets": [{
                    "data": list(data_counts.values()),
                    "backgroundColor": self._generate_colors(len(data_counts)),
                    "labels": list(data_counts.keys())
                }]
            }
            
            return chart_data
            
        except Exception as e:
            logger.error(f"Error generating data completeness chart: {e}")
            return {"error": str(e)}
    
    def _generate_health_score_timeline(self, user_id: int, start_date: datetime) -> Dict[str, Any]:
        """Generate health score timeline chart"""
        try:
            # This would typically calculate health scores over time
            # For now, we'll create a placeholder with sample data
            # In a real implementation, you'd calculate health scores for different time periods
            
            # Get health data to estimate health scores
            health_data = self.db.query(HealthData).filter(
                and_(
                    HealthData.user_id == user_id,
                    HealthData.timestamp >= start_date
                )
            ).order_by(HealthData.timestamp.asc()).all()
            
            # Group by week and calculate estimated health scores
            weekly_scores = {}
            for data in health_data:
                week_start = data.timestamp.date() - timedelta(days=data.timestamp.weekday())
                week_key = week_start.isoformat()
                
                if week_key not in weekly_scores:
                    weekly_scores[week_key] = {
                        'data_points': 0,
                        'total_score': 0
                    }
                
                weekly_scores[week_key]['data_points'] += 1
                weekly_scores[week_key]['total_score'] += 10  # Base score per data point
            
            # Calculate average scores
            timeline_data = []
            for week, score_data in sorted(weekly_scores.items()):
                avg_score = min(100, score_data['total_score'] / max(1, score_data['data_points']))
                timeline_data.append({
                    "x": week,
                    "y": round(avg_score, 1)
                })
            
            chart_data = {
                "type": "line",
                "title": "Health Score Timeline",
                "x_axis": "Week",
                "y_axis": "Health Score",
                "datasets": [{
                    "label": "Health Score",
                    "data": timeline_data,
                    "borderColor": "#4CAF50",
                    "backgroundColor": "rgba(76, 175, 80, 0.1)",
                    "fill": True
                }]
            }
            
            return chart_data
            
        except Exception as e:
            logger.error(f"Error generating health score timeline: {e}")
            return {"error": str(e)}
    
    def _generate_correlation_matrix(self, user_id: int, start_date: datetime) -> Dict[str, Any]:
        """Generate correlation matrix data"""
        try:
            # Get health data by type
            health_data = self.db.query(HealthData).filter(
                and_(
                    HealthData.user_id == user_id,
                    HealthData.timestamp >= start_date
                )
            ).all()
            
            # Decrypt sensitive fields
            for data in health_data:
                data.decrypt_sensitive_fields()
            
            # Group by data type
            data_by_type = {}
            for data in health_data:
                if data.data_type not in data_by_type:
                    data_by_type[data.data_type] = []
                
                try:
                    if data.value.startswith('{'):
                        parsed = json.loads(data.value)
                        if isinstance(parsed, dict):
                            for key in ['value', 'systolic', 'diastolic', 'reading']:
                                if key in parsed and isinstance(parsed[key], (int, float)):
                                    data_by_type[data.data_type].append(float(parsed[key]))
                                    break
                    else:
                        data_by_type[data.data_type].append(float(data.value))
                except (ValueError, json.JSONDecodeError, KeyError):
                    continue
            
            # Calculate correlations
            data_types = list(data_by_type.keys())
            correlation_matrix = []
            
            for i, type1 in enumerate(data_types):
                row = []
                for j, type2 in enumerate(data_types):
                    if i == j:
                        row.append(1.0)  # Perfect correlation with self
                    else:
                        correlation = self._calculate_correlation(
                            data_by_type[type1], data_by_type[type2]
                        )
                        row.append(round(correlation, 2))
                correlation_matrix.append(row)
            
            chart_data = {
                "type": "heatmap",
                "title": "Health Data Correlations",
                "x_axis": "Data Types",
                "y_axis": "Data Types",
                "labels": data_types,
                "data": correlation_matrix,
                "colorScale": "RdYlBu"
            }
            
            return chart_data
            
        except Exception as e:
            logger.error(f"Error generating correlation matrix: {e}")
            return {"error": str(e)}
    
    def _calculate_correlation(self, values1: List[float], values2: List[float]) -> float:
        """Calculate correlation coefficient between two sets of values"""
        try:
            if len(values1) < 2 or len(values2) < 2:
                return 0.0
            
            # Use the shorter list length
            min_length = min(len(values1), len(values2))
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
            return correlation
            
        except Exception as e:
            logger.error(f"Error calculating correlation: {e}")
            return 0.0
    
    def _get_color_for_data_type(self, data_type: str, alpha: float = 1.0) -> str:
        """Get color for specific data type"""
        colors = {
            "blood_pressure": f"rgba(244, 67, 54, {alpha})",  # Red
            "heart_rate": f"rgba(233, 30, 99, {alpha})",      # Pink
            "weight": f"rgba(156, 39, 176, {alpha})",         # Purple
            "blood_sugar": f"rgba(103, 58, 183, {alpha})",    # Deep Purple
            "temperature": f"rgba(63, 81, 181, {alpha})",     # Indigo
            "oxygen_saturation": f"rgba(33, 150, 243, {alpha})", # Blue
            "sleep_hours": f"rgba(0, 188, 212, {alpha})",     # Cyan
            "steps": f"rgba(0, 150, 136, {alpha})",           # Teal
            "calories": f"rgba(76, 175, 80, {alpha})",        # Green
            "water_intake": f"rgba(139, 195, 74, {alpha})",   # Light Green
            "mood": f"rgba(205, 220, 57, {alpha})",           # Lime
            "stress_level": f"rgba(255, 193, 7, {alpha})",    # Amber
            "pain_level": f"rgba(255, 152, 0, {alpha})",      # Orange
            "energy_level": f"rgba(255, 87, 34, {alpha})"     # Deep Orange
        }
        
        return colors.get(data_type, f"rgba(158, 158, 158, {alpha})")  # Default gray
    
    def _generate_colors(self, count: int) -> List[str]:
        """Generate a list of colors for charts"""
        base_colors = [
            "#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF",
            "#FF9F40", "#FF6384", "#C9CBCF", "#4BC0C0", "#FF6384"
        ]
        
        colors = []
        for i in range(count):
            colors.append(base_colors[i % len(base_colors)])
        
        return colors
    
    def generate_export_data(self, user_id: int, chart_type: str, days: int = 30) -> Dict[str, Any]:
        """Generate export data for specific chart types"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            if chart_type == "health_trends":
                return self._generate_health_trends_chart(user_id, start_date)
            elif chart_type == "symptom_distribution":
                return self._generate_symptom_distribution_chart(user_id, start_date)
            elif chart_type == "medication_adherence":
                return self._generate_medication_adherence_chart(user_id, start_date)
            elif chart_type == "data_completeness":
                return self._generate_data_completeness_chart(user_id, start_date)
            elif chart_type == "health_score_timeline":
                return self._generate_health_score_timeline(user_id, start_date)
            elif chart_type == "correlation_matrix":
                return self._generate_correlation_matrix(user_id, start_date)
            else:
                return {"error": f"Unknown chart type: {chart_type}"}
                
        except Exception as e:
            logger.error(f"Error generating export data: {e}")
            return {"error": str(e)} 
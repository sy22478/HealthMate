"""
Health Analytics Service
Provides comprehensive health data analysis and insights
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from app.models.health_data import HealthData, SymptomLog, MedicationLog, HealthGoal, HealthAlert
from app.models.user import User
from app.utils.encryption_utils import encryption_manager
import json
import statistics

logger = logging.getLogger(__name__)

class HealthAnalyticsService:
    """Service for health data analytics and insights"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_health_trends(self, user_id: int, data_type: str, days: int = 30) -> Dict[str, Any]:
        """Analyze health data trends over time"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get health data for the specified type and time period
            health_data = self.db.query(HealthData).filter(
                and_(
                    HealthData.user_id == user_id,
                    HealthData.data_type == data_type,
                    HealthData.timestamp >= start_date
                )
            ).order_by(HealthData.timestamp.asc()).all()
            
            if not health_data:
                return {
                    "data_type": data_type,
                    "trend": "no_data",
                    "message": f"No {data_type} data available for the last {days} days",
                    "data_points": 0
                }
            
            # Decrypt sensitive fields
            for data in health_data:
                data.decrypt_sensitive_fields()
            
            # Extract numeric values for analysis
            values = []
            timestamps = []
            
            for data in health_data:
                try:
                    # Try to parse as JSON first, then as float
                    if data.value.startswith('{'):
                        parsed_value = json.loads(data.value)
                        if isinstance(parsed_value, dict):
                            # Look for common numeric fields
                            for key in ['value', 'systolic', 'diastolic', 'reading', 'level']:
                                if key in parsed_value and isinstance(parsed_value[key], (int, float)):
                                    values.append(float(parsed_value[key]))
                                    timestamps.append(data.timestamp)
                                    break
                        else:
                            values.append(float(parsed_value))
                            timestamps.append(data.timestamp)
                    else:
                        values.append(float(data.value))
                        timestamps.append(data.timestamp)
                except (ValueError, json.JSONDecodeError, KeyError):
                    continue
            
            if not values:
                return {
                    "data_type": data_type,
                    "trend": "no_numeric_data",
                    "message": f"No numeric {data_type} data available for analysis",
                    "data_points": len(health_data)
                }
            
            # Calculate trend statistics
            trend_analysis = self._calculate_trend_statistics(values, timestamps)
            
            return {
                "data_type": data_type,
                "trend": trend_analysis["trend"],
                "data_points": len(values),
                "total_records": len(health_data),
                "statistics": trend_analysis["statistics"],
                "trend_data": trend_analysis["trend_data"],
                "insights": trend_analysis["insights"]
            }
            
        except Exception as e:
            logger.error(f"Error analyzing health trends for user {user_id}: {e}")
            raise
    
    def _calculate_trend_statistics(self, values: List[float], timestamps: List[datetime]) -> Dict[str, Any]:
        """Calculate comprehensive trend statistics"""
        if len(values) < 2:
            return {
                "trend": "insufficient_data",
                "statistics": {},
                "trend_data": [],
                "insights": ["Insufficient data for trend analysis"]
            }
        
        # Basic statistics
        mean_value = statistics.mean(values)
        median_value = statistics.median(values)
        min_value = min(values)
        max_value = max(values)
        
        # Calculate trend direction
        if len(values) >= 2:
            # Simple linear trend calculation
            first_half = values[:len(values)//2]
            second_half = values[len(values)//2:]
            
            first_avg = statistics.mean(first_half)
            second_avg = statistics.mean(second_half)
            
            if second_avg > first_avg * 1.05:  # 5% increase
                trend = "increasing"
            elif second_avg < first_avg * 0.95:  # 5% decrease
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"
        
        # Calculate standard deviation
        try:
            std_dev = statistics.stdev(values)
        except statistics.StatisticsError:
            std_dev = 0
        
        # Generate insights
        insights = []
        
        if trend == "increasing":
            insights.append(f"Values are trending upward over the analyzed period")
        elif trend == "decreasing":
            insights.append(f"Values are trending downward over the analyzed period")
        else:
            insights.append(f"Values are relatively stable over the analyzed period")
        
        if std_dev > mean_value * 0.2:  # High variability
            insights.append("High variability detected in measurements")
        elif std_dev < mean_value * 0.05:  # Low variability
            insights.append("Consistent measurements with low variability")
        
        if max_value > mean_value * 1.5:
            insights.append("Some unusually high values detected")
        
        if min_value < mean_value * 0.5:
            insights.append("Some unusually low values detected")
        
        # Prepare trend data for visualization
        trend_data = [
            {
                "timestamp": ts.isoformat(),
                "value": val
            }
            for ts, val in zip(timestamps, values)
        ]
        
        return {
            "trend": trend,
            "statistics": {
                "mean": round(mean_value, 2),
                "median": round(median_value, 2),
                "min": round(min_value, 2),
                "max": round(max_value, 2),
                "std_dev": round(std_dev, 2),
                "count": len(values)
            },
            "trend_data": trend_data,
            "insights": insights
        }
    
    def get_symptom_analysis(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Analyze symptom patterns and frequency"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get symptom logs for the time period
            symptoms = self.db.query(SymptomLog).filter(
                and_(
                    SymptomLog.user_id == user_id,
                    SymptomLog.timestamp >= start_date
                )
            ).all()
            
            if not symptoms:
                return {
                    "analysis": "no_symptoms",
                    "message": f"No symptoms logged in the last {days} days",
                    "total_symptoms": 0
                }
            
            # Decrypt sensitive fields
            for symptom in symptoms:
                symptom.decrypt_sensitive_fields()
            
            # Analyze symptom patterns
            symptom_frequency = {}
            severity_distribution = {"mild": 0, "moderate": 0, "severe": 0}
            pain_levels = []
            
            for symptom in symptoms:
                # Count symptom frequency
                symptom_frequency[symptom.symptom] = symptom_frequency.get(symptom.symptom, 0) + 1
                
                # Count severity distribution
                severity_distribution[symptom.severity] += 1
                
                # Collect pain levels
                if symptom.pain_level is not None:
                    pain_levels.append(symptom.pain_level)
            
            # Generate insights
            insights = []
            
            if symptom_frequency:
                most_common = max(symptom_frequency.items(), key=lambda x: x[1])
                insights.append(f"Most common symptom: {most_common[0]} ({most_common[1]} occurrences)")
            
            if severity_distribution["severe"] > 0:
                insights.append(f"{severity_distribution['severe']} severe symptoms detected - consider consulting a healthcare provider")
            
            if pain_levels:
                avg_pain = statistics.mean(pain_levels)
                insights.append(f"Average pain level: {round(avg_pain, 1)}/10")
                
                if avg_pain > 7:
                    insights.append("High average pain levels detected - consider pain management strategies")
            
            return {
                "analysis": "symptom_patterns",
                "total_symptoms": len(symptoms),
                "symptom_frequency": symptom_frequency,
                "severity_distribution": severity_distribution,
                "pain_statistics": {
                    "average": round(statistics.mean(pain_levels), 1) if pain_levels else None,
                    "max": max(pain_levels) if pain_levels else None,
                    "min": min(pain_levels) if pain_levels else None
                },
                "insights": insights,
                "time_period_days": days
            }
            
        except Exception as e:
            logger.error(f"Error analyzing symptoms for user {user_id}: {e}")
            raise
    
    def get_medication_adherence(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Analyze medication adherence patterns"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get medication logs for the time period
            medications = self.db.query(MedicationLog).filter(
                and_(
                    MedicationLog.user_id == user_id,
                    MedicationLog.taken_at >= start_date
                )
            ).all()
            
            if not medications:
                return {
                    "analysis": "no_medications",
                    "message": f"No medications logged in the last {days} days",
                    "adherence_rate": 0
                }
            
            # Decrypt sensitive fields
            for med in medications:
                med.decrypt_sensitive_fields()
            
            # Analyze medication patterns
            medication_frequency = {}
            effectiveness_ratings = []
            
            for med in medications:
                # Count medication frequency
                medication_frequency[med.medication_name] = medication_frequency.get(med.medication_name, 0) + 1
                
                # Collect effectiveness ratings
                if med.effectiveness is not None:
                    effectiveness_ratings.append(med.effectiveness)
            
            # Calculate adherence rate (simplified - assumes daily medications)
            total_expected = len(medication_frequency) * days
            total_taken = len(medications)
            adherence_rate = (total_taken / total_expected * 100) if total_expected > 0 else 0
            
            # Generate insights
            insights = []
            
            if adherence_rate < 80:
                insights.append(f"Medication adherence rate is {round(adherence_rate, 1)}% - consider setting reminders")
            else:
                insights.append(f"Good medication adherence rate: {round(adherence_rate, 1)}%")
            
            if effectiveness_ratings:
                avg_effectiveness = statistics.mean(effectiveness_ratings)
                insights.append(f"Average medication effectiveness: {round(avg_effectiveness, 1)}/10")
                
                if avg_effectiveness < 5:
                    insights.append("Low medication effectiveness detected - consider discussing with healthcare provider")
            
            return {
                "analysis": "medication_adherence",
                "adherence_rate": round(adherence_rate, 1),
                "total_medications_taken": total_taken,
                "medication_frequency": medication_frequency,
                "effectiveness_statistics": {
                    "average": round(statistics.mean(effectiveness_ratings), 1) if effectiveness_ratings else None,
                    "count": len(effectiveness_ratings)
                },
                "insights": insights,
                "time_period_days": days
            }
            
        except Exception as e:
            logger.error(f"Error analyzing medication adherence for user {user_id}: {e}")
            raise
    
    def get_health_score(self, user_id: int) -> Dict[str, Any]:
        """Calculate overall health score based on various factors"""
        try:
            # Get recent health data (last 30 days)
            start_date = datetime.utcnow() - timedelta(days=30)
            
            # Collect various health metrics
            health_data = self.db.query(HealthData).filter(
                and_(
                    HealthData.user_id == user_id,
                    HealthData.timestamp >= start_date
                )
            ).all()
            
            symptoms = self.db.query(SymptomLog).filter(
                and_(
                    SymptomLog.user_id == user_id,
                    SymptomLog.timestamp >= start_date
                )
            ).all()
            
            medications = self.db.query(MedicationLog).filter(
                and_(
                    MedicationLog.user_id == user_id,
                    MedicationLog.taken_at >= start_date
                )
            ).all()
            
            # Decrypt sensitive fields
            for data in health_data:
                data.decrypt_sensitive_fields()
            for symptom in symptoms:
                symptom.decrypt_sensitive_fields()
            for med in medications:
                med.decrypt_sensitive_fields()
            
            # Calculate health score components
            score_components = {}
            total_score = 0
            max_score = 0
            
            # Data consistency score (0-25 points)
            data_types = set(data.data_type for data in health_data)
            consistency_score = min(len(data_types) * 5, 25)
            score_components["data_consistency"] = consistency_score
            total_score += consistency_score
            max_score += 25
            
            # Symptom severity score (0-25 points)
            if symptoms:
                severe_symptoms = sum(1 for s in symptoms if s.severity == "severe")
                moderate_symptoms = sum(1 for s in symptoms if s.severity == "moderate")
                
                symptom_score = max(0, 25 - (severe_symptoms * 10) - (moderate_symptoms * 5))
                score_components["symptom_management"] = symptom_score
                total_score += symptom_score
            else:
                score_components["symptom_management"] = 25
                total_score += 25
            max_score += 25
            
            # Medication adherence score (0-25 points)
            if medications:
                # Simplified adherence calculation
                unique_meds = len(set(med.medication_name for med in medications))
                adherence_score = min(25, unique_meds * 5)
                score_components["medication_adherence"] = adherence_score
                total_score += adherence_score
            else:
                score_components["medication_adherence"] = 25
                total_score += 25
            max_score += 25
            
            # Activity level score (0-25 points)
            # This would need to be implemented based on actual activity data
            activity_score = 15  # Placeholder
            score_components["activity_level"] = activity_score
            total_score += activity_score
            max_score += 25
            
            # Calculate overall health score
            overall_score = (total_score / max_score * 100) if max_score > 0 else 0
            
            # Generate health insights
            insights = []
            
            if overall_score >= 80:
                insights.append("Excellent overall health score! Keep up the good work.")
            elif overall_score >= 60:
                insights.append("Good health score. Consider improving areas with lower scores.")
            elif overall_score >= 40:
                insights.append("Moderate health score. Focus on improving health habits.")
            else:
                insights.append("Health score needs improvement. Consider consulting a healthcare provider.")
            
            if score_components["symptom_management"] < 15:
                insights.append("High symptom severity detected - consider medical consultation")
            
            if score_components["medication_adherence"] < 15:
                insights.append("Low medication adherence - consider setting reminders or discussing with provider")
            
            return {
                "overall_score": round(overall_score, 1),
                "score_components": score_components,
                "insights": insights,
                "data_summary": {
                    "health_data_points": len(health_data),
                    "symptoms_logged": len(symptoms),
                    "medications_taken": len(medications),
                    "data_types_tracked": len(data_types)
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating health score for user {user_id}: {e}")
            raise
    
    def get_health_recommendations(self, user_id: int) -> List[Dict[str, Any]]:
        """Generate personalized health recommendations"""
        try:
            recommendations = []
            
            # Get recent health data
            start_date = datetime.utcnow() - timedelta(days=30)
            
            # Analyze different aspects and generate recommendations
            health_score = self.get_health_score(user_id)
            symptom_analysis = self.get_symptom_analysis(user_id)
            medication_adherence = self.get_medication_adherence(user_id)
            
            # Generate recommendations based on health score
            if health_score["overall_score"] < 60:
                recommendations.append({
                    "category": "general_health",
                    "priority": "high",
                    "title": "Improve Overall Health",
                    "description": "Your health score indicates areas for improvement. Focus on consistent health tracking and symptom management.",
                    "action_items": [
                        "Log health data regularly",
                        "Monitor symptoms closely",
                        "Follow medication schedules",
                        "Consider lifestyle improvements"
                    ]
                })
            
            # Symptom-based recommendations
            if symptom_analysis.get("analysis") == "symptom_patterns":
                if symptom_analysis["severity_distribution"]["severe"] > 0:
                    recommendations.append({
                        "category": "symptom_management",
                        "priority": "high",
                        "title": "Address Severe Symptoms",
                        "description": f"You have {symptom_analysis['severity_distribution']['severe']} severe symptoms. Consider consulting a healthcare provider.",
                        "action_items": [
                            "Schedule a medical appointment",
                            "Document symptom patterns",
                            "Consider emergency care if symptoms worsen"
                        ]
                    })
            
            # Medication-based recommendations
            if medication_adherence.get("analysis") == "medication_adherence":
                if medication_adherence["adherence_rate"] < 80:
                    recommendations.append({
                        "category": "medication_management",
                        "priority": "medium",
                        "title": "Improve Medication Adherence",
                        "description": f"Your medication adherence rate is {medication_adherence['adherence_rate']}%. Consider setting up reminders.",
                        "action_items": [
                            "Set medication reminders",
                            "Use a pill organizer",
                            "Discuss adherence with healthcare provider",
                            "Log medications consistently"
                        ]
                    })
            
            # General wellness recommendations
            recommendations.append({
                "category": "wellness",
                "priority": "low",
                "title": "Maintain Healthy Habits",
                "description": "Continue with healthy lifestyle practices to maintain good health.",
                "action_items": [
                    "Regular exercise",
                    "Balanced nutrition",
                    "Adequate sleep",
                    "Stress management",
                    "Regular health checkups"
                ]
            })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating health recommendations for user {user_id}: {e}")
            raise 
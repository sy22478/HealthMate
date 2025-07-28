"""
Health Insights Service
Provides real-time health insights and recommendations
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from app.models.health_data import HealthData, SymptomLog, MedicationLog, HealthAlert
from app.models.user import User
from app.utils.encryption_utils import encryption_manager
import json
import statistics

logger = logging.getLogger(__name__)

class HealthInsightsService:
    """Service for generating health insights and recommendations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_health_insights(self, user_id: int) -> Dict[str, Any]:
        """Generate comprehensive health insights for a user"""
        try:
            insights = {
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "insights": [],
                "alerts": [],
                "recommendations": [],
                "trends": {},
                "risk_factors": []
            }
            
            # Get recent health data (last 30 days)
            start_date = datetime.utcnow() - timedelta(days=30)
            
            # Analyze different health aspects
            health_data_insights = self._analyze_health_data(user_id, start_date)
            symptom_insights = self._analyze_symptoms(user_id, start_date)
            medication_insights = self._analyze_medications(user_id, start_date)
            trend_insights = self._analyze_trends(user_id, start_date)
            risk_insights = self._assess_risk_factors(user_id, start_date)
            
            # Combine all insights
            insights["insights"].extend(health_data_insights)
            insights["insights"].extend(symptom_insights)
            insights["insights"].extend(medication_insights)
            insights["trends"] = trend_insights
            insights["risk_factors"] = risk_insights
            
            # Generate recommendations based on insights
            insights["recommendations"] = self._generate_recommendations(insights)
            
            # Generate alerts for concerning patterns
            insights["alerts"] = self._generate_alerts(insights)
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating health insights for user {user_id}: {e}")
            return {"error": str(e), "timestamp": datetime.utcnow().isoformat()}
    
    def _analyze_health_data(self, user_id: int, start_date: datetime) -> List[Dict[str, Any]]:
        """Analyze health data patterns"""
        insights = []
        
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
                data_by_type[data.data_type].append(data)
            
            # Analyze each data type
            for data_type, data_list in data_by_type.items():
                if len(data_list) < 2:
                    continue
                
                # Extract numeric values
                values = []
                for data in data_list:
                    try:
                        if data.value.startswith('{'):
                            parsed = json.loads(data.value)
                            if isinstance(parsed, dict):
                                # Look for numeric values
                                for key in ['value', 'systolic', 'diastolic', 'reading']:
                                    if key in parsed and isinstance(parsed[key], (int, float)):
                                        values.append(float(parsed[key]))
                                        break
                        else:
                            values.append(float(data.value))
                    except (ValueError, json.JSONDecodeError, KeyError):
                        continue
                
                if len(values) < 2:
                    continue
                
                # Calculate statistics
                mean_val = statistics.mean(values)
                std_dev = statistics.stdev(values) if len(values) > 1 else 0
                min_val = min(values)
                max_val = max(values)
                
                # Generate insights based on data type
                insight = self._generate_data_type_insight(
                    data_type, values, mean_val, std_dev, min_val, max_val
                )
                
                if insight:
                    insights.append(insight)
        
        except Exception as e:
            logger.error(f"Error analyzing health data: {e}")
        
        return insights
    
    def _generate_data_type_insight(self, data_type: str, values: List[float], mean: float, std_dev: float, min_val: float, max_val: float) -> Optional[Dict[str, Any]]:
        """Generate specific insights for different data types"""
        
        if data_type == "blood_pressure":
            # Analyze blood pressure patterns
            systolic_values = []
            diastolic_values = []
            
            # Extract systolic and diastolic values
            for val in values:
                if val > 200:  # Likely systolic
                    systolic_values.append(val)
                elif val < 200:  # Likely diastolic
                    diastolic_values.append(val)
            
            if systolic_values and diastolic_values:
                avg_systolic = statistics.mean(systolic_values)
                avg_diastolic = statistics.mean(diastolic_values)
                
                # Blood pressure categories
                if avg_systolic >= 180 or avg_diastolic >= 110:
                    category = "Stage 2 Hypertension"
                    severity = "high"
                elif avg_systolic >= 140 or avg_diastolic >= 90:
                    category = "Stage 1 Hypertension"
                    severity = "medium"
                elif avg_systolic >= 120 or avg_diastolic >= 80:
                    category = "Elevated"
                    severity = "low"
                else:
                    category = "Normal"
                    severity = "good"
                
                return {
                    "type": "blood_pressure_analysis",
                    "category": category,
                    "severity": severity,
                    "average_systolic": round(avg_systolic, 1),
                    "average_diastolic": round(avg_diastolic, 1),
                    "data_points": len(values),
                    "recommendation": self._get_blood_pressure_recommendation(category)
                }
        
        elif data_type == "heart_rate":
            # Analyze heart rate patterns
            if mean > 100:
                category = "Tachycardia"
                severity = "medium"
            elif mean < 60:
                category = "Bradycardia"
                severity = "medium"
            else:
                category = "Normal"
                severity = "good"
            
            return {
                "type": "heart_rate_analysis",
                "category": category,
                "severity": severity,
                "average": round(mean, 1),
                "range": f"{round(min_val, 1)} - {round(max_val, 1)}",
                "data_points": len(values),
                "recommendation": self._get_heart_rate_recommendation(category)
            }
        
        elif data_type == "weight":
            # Analyze weight trends
            if len(values) >= 3:
                # Calculate trend
                first_half = values[:len(values)//2]
                second_half = values[len(values)//2:]
                
                first_avg = statistics.mean(first_half)
                second_avg = statistics.mean(second_half)
                
                if second_avg > first_avg * 1.02:  # 2% increase
                    trend = "increasing"
                    severity = "medium"
                elif second_avg < first_avg * 0.98:  # 2% decrease
                    trend = "decreasing"
                    severity = "low"
                else:
                    trend = "stable"
                    severity = "good"
                
                return {
                    "type": "weight_trend_analysis",
                    "trend": trend,
                    "severity": severity,
                    "average": round(mean, 1),
                    "change_percentage": round(((second_avg - first_avg) / first_avg) * 100, 1),
                    "data_points": len(values),
                    "recommendation": self._get_weight_recommendation(trend)
                }
        
        elif data_type == "blood_sugar":
            # Analyze blood sugar patterns
            if mean > 200:
                category = "High"
                severity = "high"
            elif mean > 140:
                category = "Elevated"
                severity = "medium"
            elif mean < 70:
                category = "Low"
                severity = "high"
            else:
                category = "Normal"
                severity = "good"
            
            return {
                "type": "blood_sugar_analysis",
                "category": category,
                "severity": severity,
                "average": round(mean, 1),
                "data_points": len(values),
                "recommendation": self._get_blood_sugar_recommendation(category)
            }
        
        return None
    
    def _analyze_symptoms(self, user_id: int, start_date: datetime) -> List[Dict[str, Any]]:
        """Analyze symptom patterns"""
        insights = []
        
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
            
            if not symptoms:
                return insights
            
            # Analyze symptom frequency
            symptom_frequency = {}
            severity_distribution = {"mild": 0, "moderate": 0, "severe": 0}
            
            for symptom in symptoms:
                symptom_frequency[symptom.symptom] = symptom_frequency.get(symptom.symptom, 0) + 1
                severity_distribution[symptom.severity] += 1
            
            # Generate insights
            if symptom_frequency:
                most_common = max(symptom_frequency.items(), key=lambda x: x[1])
                insights.append({
                    "type": "symptom_frequency",
                    "most_common_symptom": most_common[0],
                    "frequency": most_common[1],
                    "total_symptoms": len(symptoms),
                    "severity_distribution": severity_distribution
                })
            
            # Check for concerning patterns
            if severity_distribution["severe"] > 0:
                insights.append({
                    "type": "severe_symptom_alert",
                    "count": severity_distribution["severe"],
                    "recommendation": "Consider consulting a healthcare provider for severe symptoms"
                })
            
            # Analyze pain levels
            pain_levels = [s.pain_level for s in symptoms if s.pain_level is not None]
            if pain_levels:
                avg_pain = statistics.mean(pain_levels)
                insights.append({
                    "type": "pain_analysis",
                    "average_pain_level": round(avg_pain, 1),
                    "max_pain_level": max(pain_levels),
                    "recommendation": self._get_pain_recommendation(avg_pain)
                })
        
        except Exception as e:
            logger.error(f"Error analyzing symptoms: {e}")
        
        return insights
    
    def _analyze_medications(self, user_id: int, start_date: datetime) -> List[Dict[str, Any]]:
        """Analyze medication patterns"""
        insights = []
        
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
            
            if not medications:
                return insights
            
            # Analyze medication adherence
            unique_meds = len(set(med.medication_name for med in medications))
            total_doses = len(medications)
            
            # Calculate adherence rate (simplified)
            expected_doses = unique_meds * 30  # Assume daily medications
            adherence_rate = (total_doses / expected_doses * 100) if expected_doses > 0 else 0
            
            insights.append({
                "type": "medication_adherence",
                "adherence_rate": round(adherence_rate, 1),
                "unique_medications": unique_meds,
                "total_doses": total_doses,
                "recommendation": self._get_adherence_recommendation(adherence_rate)
            })
            
            # Analyze effectiveness
            effectiveness_ratings = [med.effectiveness for med in medications if med.effectiveness is not None]
            if effectiveness_ratings:
                avg_effectiveness = statistics.mean(effectiveness_ratings)
                insights.append({
                    "type": "medication_effectiveness",
                    "average_effectiveness": round(avg_effectiveness, 1),
                    "recommendation": self._get_effectiveness_recommendation(avg_effectiveness)
                })
        
        except Exception as e:
            logger.error(f"Error analyzing medications: {e}")
        
        return insights
    
    def _analyze_trends(self, user_id: int, start_date: datetime) -> Dict[str, Any]:
        """Analyze health trends over time"""
        trends = {}
        
        try:
            # Get health data for trend analysis
            health_data = self.db.query(HealthData).filter(
                and_(
                    HealthData.user_id == user_id,
                    HealthData.timestamp >= start_date
                )
            ).order_by(HealthData.timestamp.asc()).all()
            
            # Decrypt sensitive fields
            for data in health_data:
                data.decrypt_sensitive_fields()
            
            # Group by data type and analyze trends
            data_by_type = {}
            for data in health_data:
                if data.data_type not in data_by_type:
                    data_by_type[data.data_type] = []
                data_by_type[data.data_type].append(data)
            
            for data_type, data_list in data_by_type.items():
                if len(data_list) < 3:
                    continue
                
                # Extract numeric values
                values = []
                timestamps = []
                
                for data in data_list:
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
                
                if len(values) < 3:
                    continue
                
                # Calculate trend
                first_half = values[:len(values)//2]
                second_half = values[len(values)//2:]
                
                if first_half and second_half:
                    first_avg = statistics.mean(first_half)
                    second_avg = statistics.mean(second_half)
                    
                    if second_avg > first_avg * 1.05:
                        trend = "increasing"
                    elif second_avg < first_avg * 0.95:
                        trend = "decreasing"
                    else:
                        trend = "stable"
                    
                    trends[data_type] = {
                        "trend": trend,
                        "change_percentage": round(((second_avg - first_avg) / first_avg) * 100, 1),
                        "data_points": len(values)
                    }
        
        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
        
        return trends
    
    def _assess_risk_factors(self, user_id: int, start_date: datetime) -> List[Dict[str, Any]]:
        """Assess health risk factors"""
        risk_factors = []
        
        try:
            # Get user profile
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return risk_factors
            
            user.decrypt_sensitive_fields()
            
            # Age-related risks
            if user.age and user.age > 65:
                risk_factors.append({
                    "factor": "age",
                    "level": "medium",
                    "description": "Advanced age increases risk for certain health conditions",
                    "recommendation": "Regular health checkups and preventive screenings"
                })
            
            # Medical conditions
            if user.medical_conditions:
                risk_factors.append({
                    "factor": "existing_conditions",
                    "level": "high",
                    "description": "Existing medical conditions require ongoing management",
                    "recommendation": "Follow treatment plans and regular monitoring"
                })
            
            # Multiple medications
            if user.medications:
                risk_factors.append({
                    "factor": "polypharmacy",
                    "level": "medium",
                    "description": "Multiple medications increase risk of interactions",
                    "recommendation": "Regular medication reviews with healthcare provider"
                })
            
            # Recent severe symptoms
            severe_symptoms = self.db.query(SymptomLog).filter(
                and_(
                    SymptomLog.user_id == user_id,
                    SymptomLog.severity == "severe",
                    SymptomLog.timestamp >= start_date
                )
            ).count()
            
            if severe_symptoms > 0:
                risk_factors.append({
                    "factor": "recent_severe_symptoms",
                    "level": "high",
                    "description": f"{severe_symptoms} severe symptoms logged recently",
                    "recommendation": "Immediate medical evaluation recommended"
                })
        
        except Exception as e:
            logger.error(f"Error assessing risk factors: {e}")
        
        return risk_factors
    
    def _generate_recommendations(self, insights: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on insights"""
        recommendations = []
        
        try:
            # Process insights and generate recommendations
            for insight in insights.get("insights", []):
                if insight.get("type") == "blood_pressure_analysis":
                    if insight.get("severity") in ["medium", "high"]:
                        recommendations.append("Monitor blood pressure regularly and consider lifestyle changes")
                
                elif insight.get("type") == "heart_rate_analysis":
                    if insight.get("severity") in ["medium", "high"]:
                        recommendations.append("Consult healthcare provider about heart rate patterns")
                
                elif insight.get("type") == "severe_symptom_alert":
                    recommendations.append("Schedule medical appointment for severe symptoms")
                
                elif insight.get("type") == "medication_adherence":
                    if insight.get("adherence_rate", 100) < 80:
                        recommendations.append("Improve medication adherence with reminders and organization")
            
            # Add general recommendations
            if not recommendations:
                recommendations.append("Continue monitoring health data for better insights")
                recommendations.append("Maintain regular health checkups")
                recommendations.append("Follow healthy lifestyle practices")
        
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
        
        return recommendations
    
    def _generate_alerts(self, insights: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate alerts for concerning patterns"""
        alerts = []
        
        try:
            for insight in insights.get("insights", []):
                if insight.get("severity") == "high":
                    alerts.append({
                        "type": "high_severity_insight",
                        "message": f"High severity health pattern detected: {insight.get('type', 'unknown')}",
                        "priority": "high",
                        "recommendation": insight.get("recommendation", "Consult healthcare provider")
                    })
            
            # Check risk factors
            for risk in insights.get("risk_factors", []):
                if risk.get("level") == "high":
                    alerts.append({
                        "type": "high_risk_factor",
                        "message": f"High risk factor: {risk.get('factor', 'unknown')}",
                        "priority": "high",
                        "recommendation": risk.get("recommendation", "Medical evaluation recommended")
                    })
        
        except Exception as e:
            logger.error(f"Error generating alerts: {e}")
        
        return alerts
    
    # Recommendation helper methods
    def _get_blood_pressure_recommendation(self, category: str) -> str:
        recommendations = {
            "Stage 2 Hypertension": "Immediate medical consultation recommended",
            "Stage 1 Hypertension": "Lifestyle changes and regular monitoring advised",
            "Elevated": "Consider lifestyle modifications",
            "Normal": "Maintain current healthy practices"
        }
        return recommendations.get(category, "Consult healthcare provider")
    
    def _get_heart_rate_recommendation(self, category: str) -> str:
        recommendations = {
            "Tachycardia": "Consult healthcare provider about elevated heart rate",
            "Bradycardia": "Medical evaluation recommended for low heart rate",
            "Normal": "Heart rate within normal range"
        }
        return recommendations.get(category, "Consult healthcare provider")
    
    def _get_weight_recommendation(self, trend: str) -> str:
        recommendations = {
            "increasing": "Consider dietary and exercise modifications",
            "decreasing": "Monitor weight loss and ensure healthy practices",
            "stable": "Maintain current weight management practices"
        }
        return recommendations.get(trend, "Consult healthcare provider")
    
    def _get_blood_sugar_recommendation(self, category: str) -> str:
        recommendations = {
            "High": "Immediate medical attention recommended",
            "Elevated": "Monitor blood sugar and consult healthcare provider",
            "Low": "Immediate medical attention for low blood sugar",
            "Normal": "Continue monitoring blood sugar levels"
        }
        return recommendations.get(category, "Consult healthcare provider")
    
    def _get_pain_recommendation(self, avg_pain: float) -> str:
        if avg_pain > 7:
            return "Consider pain management consultation"
        elif avg_pain > 4:
            return "Monitor pain levels and consider treatment options"
        else:
            return "Continue monitoring pain levels"
    
    def _get_adherence_recommendation(self, adherence_rate: float) -> str:
        if adherence_rate < 80:
            return "Improve medication adherence with reminders and organization"
        else:
            return "Good medication adherence - continue current practices"
    
    def _get_effectiveness_recommendation(self, effectiveness: float) -> str:
        if effectiveness < 5:
            return "Discuss medication effectiveness with healthcare provider"
        else:
            return "Medication appears effective - continue as prescribed" 
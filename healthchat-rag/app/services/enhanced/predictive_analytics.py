"""
Predictive Analytics Backend Service
Health risk assessment models, trend prediction, and preventive care recommendation engine
"""

import asyncio
import logging
import json
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import pickle
import hashlib
from collections import defaultdict

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from app.models.user import User
from app.models.enhanced_health_models import UserHealthProfile, HealthMetricsAggregation
from app.database import get_db
from app.exceptions.external_api_exceptions import ExternalAPIError
from app.utils.encryption_utils import field_encryption

logger = logging.getLogger(__name__)

class RiskLevel(str, Enum):
    """Risk level enumeration"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"

class PredictionType(str, Enum):
    """Prediction type enumeration"""
    CARDIOVASCULAR_RISK = "cardiovascular_risk"
    DIABETES_RISK = "diabetes_risk"
    MENTAL_HEALTH_RISK = "mental_health_risk"
    HEALTH_TREND = "health_trend"
    EARLY_WARNING = "early_warning"
    PREVENTIVE_CARE = "preventive_care"

class TrendDirection(str, Enum):
    """Trend direction enumeration"""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    FLUCTUATING = "fluctuating"

@dataclass
class RiskAssessment:
    """Risk assessment result"""
    risk_type: PredictionType
    risk_level: RiskLevel
    risk_score: float
    confidence: float
    factors: List[str]
    recommendations: List[str]
    assessment_date: datetime
    next_assessment_date: datetime

@dataclass
class HealthTrend:
    """Health trend prediction"""
    metric_name: str
    current_value: float
    predicted_value: float
    trend_direction: TrendDirection
    confidence: float
    timeframe_days: int
    factors: List[str]
    recommendations: List[str]

@dataclass
class EarlyWarning:
    """Early warning system result"""
    warning_type: str
    severity: RiskLevel
    probability: float
    timeframe_days: int
    symptoms: List[str]
    risk_factors: List[str]
    recommendations: List[str]
    urgency: str

@dataclass
class PreventiveRecommendation:
    """Preventive care recommendation"""
    recommendation_type: str
    priority: str
    description: str
    rationale: str
    expected_benefit: str
    timeframe: str
    resources: List[str]
    confidence: float

class PredictiveAnalyticsBackend:
    """Advanced predictive analytics backend for health risk assessment and trend prediction"""
    
    def __init__(self, 
                 model_update_frequency_days: int = 30,
                 prediction_horizon_days: int = 90,
                 min_data_points: int = 10):
        self.model_update_frequency_days = model_update_frequency_days
        self.prediction_horizon_days = prediction_horizon_days
        self.min_data_points = min_data_points
        
        # Risk assessment thresholds
        self.risk_thresholds = {
            RiskLevel.LOW: 0.3,
            RiskLevel.MODERATE: 0.6,
            RiskLevel.HIGH: 0.8,
            RiskLevel.CRITICAL: 0.9
        }
        
        # Model cache
        self.model_cache: Dict[str, Any] = {}
        self.last_model_update: Dict[str, datetime] = {}
        
        # Medical knowledge base for risk factors
        self.risk_factors = self._initialize_risk_factors()
        
        logger.info("Predictive Analytics Backend initialized successfully")
    
    def _initialize_risk_factors(self) -> Dict[str, Dict[str, Any]]:
        """Initialize medical risk factors and their weights"""
        return {
            "cardiovascular": {
                "age": {"weight": 0.15, "high_risk_threshold": 65},
                "gender": {"weight": 0.1, "high_risk": ["male"]},
                "blood_pressure": {"weight": 0.2, "high_risk_threshold": 140},
                "cholesterol": {"weight": 0.15, "high_risk_threshold": 200},
                "smoking": {"weight": 0.15, "high_risk": True},
                "diabetes": {"weight": 0.1, "high_risk": True},
                "obesity": {"weight": 0.1, "high_risk_threshold": 30},
                "family_history": {"weight": 0.05, "high_risk": True}
            },
            "diabetes": {
                "age": {"weight": 0.1, "high_risk_threshold": 45},
                "gender": {"weight": 0.05, "high_risk": ["male"]},
                "bmi": {"weight": 0.2, "high_risk_threshold": 25},
                "family_history": {"weight": 0.15, "high_risk": True},
                "physical_activity": {"weight": 0.15, "high_risk": False},
                "diet": {"weight": 0.1, "high_risk": "poor"},
                "blood_pressure": {"weight": 0.1, "high_risk_threshold": 130},
                "gestational_diabetes": {"weight": 0.05, "high_risk": True},
                "polycystic_ovary": {"weight": 0.05, "high_risk": True}
            },
            "mental_health": {
                "age": {"weight": 0.1, "high_risk_threshold": 18},
                "gender": {"weight": 0.05, "high_risk": ["female"]},
                "family_history": {"weight": 0.2, "high_risk": True},
                "stress_level": {"weight": 0.25, "high_risk_threshold": 7},
                "sleep_quality": {"weight": 0.15, "high_risk_threshold": 5},
                "social_support": {"weight": 0.1, "high_risk": False},
                "life_events": {"weight": 0.1, "high_risk": True},
                "substance_use": {"weight": 0.05, "high_risk": True}
            }
        }
    
    async def assess_cardiovascular_risk(self, user_id: int) -> RiskAssessment:
        """Assess cardiovascular risk using multiple factors"""
        try:
            # Get user health data
            health_data = await self._get_user_health_data(user_id)
            
            if not health_data:
                raise ExternalAPIError("Insufficient health data for cardiovascular risk assessment")
            
            # Calculate risk score
            risk_score = self._calculate_cardiovascular_risk(health_data)
            
            # Determine risk level
            risk_level = self._determine_risk_level(risk_score)
            
            # Identify risk factors
            factors = self._identify_cardiovascular_risk_factors(health_data)
            
            # Generate recommendations
            recommendations = self._generate_cardiovascular_recommendations(risk_level, factors)
            
            # Calculate confidence
            confidence = self._calculate_assessment_confidence(health_data, "cardiovascular")
            
            return RiskAssessment(
                risk_type=PredictionType.CARDIOVASCULAR_RISK,
                risk_level=risk_level,
                risk_score=risk_score,
                confidence=confidence,
                factors=factors,
                recommendations=recommendations,
                assessment_date=datetime.utcnow(),
                next_assessment_date=datetime.utcnow() + timedelta(days=90)
            )
            
        except Exception as e:
            logger.error(f"Error in cardiovascular risk assessment: {e}")
            raise ExternalAPIError(f"Cardiovascular risk assessment failed: {str(e)}")
    
    def _calculate_cardiovascular_risk(self, health_data: Dict[str, Any]) -> float:
        """Calculate cardiovascular risk score"""
        risk_score = 0.0
        factors = self.risk_factors["cardiovascular"]
        
        # Age factor
        age = health_data.get('age', 0)
        if age > factors["age"]["high_risk_threshold"]:
            risk_score += factors["age"]["weight"]
        elif age > 45:
            risk_score += factors["age"]["weight"] * 0.5
        
        # Gender factor
        gender = health_data.get('gender', '').lower()
        if gender in factors["gender"]["high_risk"]:
            risk_score += factors["gender"]["weight"]
        
        # Blood pressure factor
        systolic_bp = health_data.get('systolic_bp', 0)
        diastolic_bp = health_data.get('diastolic_bp', 0)
        if systolic_bp > factors["blood_pressure"]["high_risk_threshold"] or diastolic_bp > 90:
            risk_score += factors["blood_pressure"]["weight"]
        elif systolic_bp > 120 or diastolic_bp > 80:
            risk_score += factors["blood_pressure"]["weight"] * 0.5
        
        # Cholesterol factor
        total_cholesterol = health_data.get('total_cholesterol', 0)
        if total_cholesterol > factors["cholesterol"]["high_risk_threshold"]:
            risk_score += factors["cholesterol"]["weight"]
        elif total_cholesterol > 180:
            risk_score += factors["cholesterol"]["weight"] * 0.5
        
        # Smoking factor
        if health_data.get('smoking', False):
            risk_score += factors["smoking"]["weight"]
        
        # Diabetes factor
        if health_data.get('diabetes', False):
            risk_score += factors["diabetes"]["weight"]
        
        # Obesity factor (BMI)
        bmi = health_data.get('bmi', 0)
        if bmi > factors["obesity"]["high_risk_threshold"]:
            risk_score += factors["obesity"]["weight"]
        elif bmi > 25:
            risk_score += factors["obesity"]["weight"] * 0.5
        
        # Family history factor
        if health_data.get('family_history_cardiovascular', False):
            risk_score += factors["family_history"]["weight"]
        
        return min(risk_score, 1.0)
    
    async def assess_diabetes_risk(self, user_id: int) -> RiskAssessment:
        """Assess diabetes risk using multiple factors"""
        try:
            # Get user health data
            health_data = await self._get_user_health_data(user_id)
            
            if not health_data:
                raise ExternalAPIError("Insufficient health data for diabetes risk assessment")
            
            # Calculate risk score
            risk_score = self._calculate_diabetes_risk(health_data)
            
            # Determine risk level
            risk_level = self._determine_risk_level(risk_score)
            
            # Identify risk factors
            factors = self._identify_diabetes_risk_factors(health_data)
            
            # Generate recommendations
            recommendations = self._generate_diabetes_recommendations(risk_level, factors)
            
            # Calculate confidence
            confidence = self._calculate_assessment_confidence(health_data, "diabetes")
            
            return RiskAssessment(
                risk_type=PredictionType.DIABETES_RISK,
                risk_level=risk_level,
                risk_score=risk_score,
                confidence=confidence,
                factors=factors,
                recommendations=recommendations,
                assessment_date=datetime.utcnow(),
                next_assessment_date=datetime.utcnow() + timedelta(days=90)
            )
            
        except Exception as e:
            logger.error(f"Error in diabetes risk assessment: {e}")
            raise ExternalAPIError(f"Diabetes risk assessment failed: {str(e)}")
    
    def _calculate_diabetes_risk(self, health_data: Dict[str, Any]) -> float:
        """Calculate diabetes risk score"""
        risk_score = 0.0
        factors = self.risk_factors["diabetes"]
        
        # Age factor
        age = health_data.get('age', 0)
        if age > factors["age"]["high_risk_threshold"]:
            risk_score += factors["age"]["weight"]
        elif age > 35:
            risk_score += factors["age"]["weight"] * 0.5
        
        # Gender factor
        gender = health_data.get('gender', '').lower()
        if gender in factors["gender"]["high_risk"]:
            risk_score += factors["gender"]["weight"]
        
        # BMI factor
        bmi = health_data.get('bmi', 0)
        if bmi > factors["bmi"]["high_risk_threshold"]:
            risk_score += factors["bmi"]["weight"]
        elif bmi > 23:
            risk_score += factors["bmi"]["weight"] * 0.5
        
        # Family history factor
        if health_data.get('family_history_diabetes', False):
            risk_score += factors["family_history"]["weight"]
        
        # Physical activity factor
        if not health_data.get('regular_exercise', False):
            risk_score += factors["physical_activity"]["weight"]
        
        # Diet factor
        diet_quality = health_data.get('diet_quality', 'good')
        if diet_quality == factors["diet"]["high_risk"]:
            risk_score += factors["diet"]["weight"]
        
        # Blood pressure factor
        systolic_bp = health_data.get('systolic_bp', 0)
        if systolic_bp > factors["blood_pressure"]["high_risk_threshold"]:
            risk_score += factors["blood_pressure"]["weight"]
        
        # Gestational diabetes factor
        if health_data.get('gestational_diabetes_history', False):
            risk_score += factors["gestational_diabetes"]["weight"]
        
        # Polycystic ovary syndrome factor
        if health_data.get('polycystic_ovary_syndrome', False):
            risk_score += factors["polycystic_ovary"]["weight"]
        
        return min(risk_score, 1.0)
    
    async def assess_mental_health_risk(self, user_id: int) -> RiskAssessment:
        """Assess mental health risk using multiple factors"""
        try:
            # Get user health data
            health_data = await self._get_user_health_data(user_id)
            
            if not health_data:
                raise ExternalAPIError("Insufficient health data for mental health risk assessment")
            
            # Calculate risk score
            risk_score = self._calculate_mental_health_risk(health_data)
            
            # Determine risk level
            risk_level = self._determine_risk_level(risk_score)
            
            # Identify risk factors
            factors = self._identify_mental_health_risk_factors(health_data)
            
            # Generate recommendations
            recommendations = self._generate_mental_health_recommendations(risk_level, factors)
            
            # Calculate confidence
            confidence = self._calculate_assessment_confidence(health_data, "mental_health")
            
            return RiskAssessment(
                risk_type=PredictionType.MENTAL_HEALTH_RISK,
                risk_level=risk_level,
                risk_score=risk_score,
                confidence=confidence,
                factors=factors,
                recommendations=recommendations,
                assessment_date=datetime.utcnow(),
                next_assessment_date=datetime.utcnow() + timedelta(days=60)
            )
            
        except Exception as e:
            logger.error(f"Error in mental health risk assessment: {e}")
            raise ExternalAPIError(f"Mental health risk assessment failed: {str(e)}")
    
    def _calculate_mental_health_risk(self, health_data: Dict[str, Any]) -> float:
        """Calculate mental health risk score"""
        risk_score = 0.0
        factors = self.risk_factors["mental_health"]
        
        # Age factor
        age = health_data.get('age', 0)
        if age > factors["age"]["high_risk_threshold"]:
            risk_score += factors["age"]["weight"] * 0.5
        
        # Gender factor
        gender = health_data.get('gender', '').lower()
        if gender in factors["gender"]["high_risk"]:
            risk_score += factors["gender"]["weight"]
        
        # Family history factor
        if health_data.get('family_history_mental_health', False):
            risk_score += factors["family_history"]["weight"]
        
        # Stress level factor
        stress_level = health_data.get('stress_level', 5)
        if stress_level > factors["stress_level"]["high_risk_threshold"]:
            risk_score += factors["stress_level"]["weight"]
        elif stress_level > 5:
            risk_score += factors["stress_level"]["weight"] * 0.5
        
        # Sleep quality factor
        sleep_quality = health_data.get('sleep_quality', 7)
        if sleep_quality < factors["sleep_quality"]["high_risk_threshold"]:
            risk_score += factors["sleep_quality"]["weight"]
        elif sleep_quality < 6:
            risk_score += factors["sleep_quality"]["weight"] * 0.5
        
        # Social support factor
        if not health_data.get('strong_social_support', False):
            risk_score += factors["social_support"]["weight"]
        
        # Life events factor
        if health_data.get('recent_life_events', False):
            risk_score += factors["life_events"]["weight"]
        
        # Substance use factor
        if health_data.get('substance_use', False):
            risk_score += factors["substance_use"]["weight"]
        
        return min(risk_score, 1.0)
    
    def _determine_risk_level(self, risk_score: float) -> RiskLevel:
        """Determine risk level based on risk score"""
        if risk_score >= self.risk_thresholds[RiskLevel.CRITICAL]:
            return RiskLevel.CRITICAL
        elif risk_score >= self.risk_thresholds[RiskLevel.HIGH]:
            return RiskLevel.HIGH
        elif risk_score >= self.risk_thresholds[RiskLevel.MODERATE]:
            return RiskLevel.MODERATE
        else:
            return RiskLevel.LOW
    
    def _identify_cardiovascular_risk_factors(self, health_data: Dict[str, Any]) -> List[str]:
        """Identify cardiovascular risk factors"""
        factors = []
        
        if health_data.get('age', 0) > 65:
            factors.append("Advanced age (>65 years)")
        
        if health_data.get('gender', '').lower() == 'male':
            factors.append("Male gender")
        
        if health_data.get('systolic_bp', 0) > 140:
            factors.append("High blood pressure")
        
        if health_data.get('total_cholesterol', 0) > 200:
            factors.append("High cholesterol")
        
        if health_data.get('smoking', False):
            factors.append("Smoking")
        
        if health_data.get('diabetes', False):
            factors.append("Diabetes")
        
        if health_data.get('bmi', 0) > 30:
            factors.append("Obesity")
        
        if health_data.get('family_history_cardiovascular', False):
            factors.append("Family history of cardiovascular disease")
        
        return factors
    
    def _identify_diabetes_risk_factors(self, health_data: Dict[str, Any]) -> List[str]:
        """Identify diabetes risk factors"""
        factors = []
        
        if health_data.get('age', 0) > 45:
            factors.append("Age over 45")
        
        if health_data.get('gender', '').lower() == 'male':
            factors.append("Male gender")
        
        if health_data.get('bmi', 0) > 25:
            factors.append("Overweight/obesity")
        
        if health_data.get('family_history_diabetes', False):
            factors.append("Family history of diabetes")
        
        if not health_data.get('regular_exercise', False):
            factors.append("Physical inactivity")
        
        if health_data.get('diet_quality', 'good') == 'poor':
            factors.append("Poor diet")
        
        if health_data.get('systolic_bp', 0) > 130:
            factors.append("High blood pressure")
        
        if health_data.get('gestational_diabetes_history', False):
            factors.append("History of gestational diabetes")
        
        if health_data.get('polycystic_ovary_syndrome', False):
            factors.append("Polycystic ovary syndrome")
        
        return factors
    
    def _identify_mental_health_risk_factors(self, health_data: Dict[str, Any]) -> List[str]:
        """Identify mental health risk factors"""
        factors = []
        
        if health_data.get('gender', '').lower() == 'female':
            factors.append("Female gender")
        
        if health_data.get('family_history_mental_health', False):
            factors.append("Family history of mental health conditions")
        
        if health_data.get('stress_level', 5) > 7:
            factors.append("High stress levels")
        
        if health_data.get('sleep_quality', 7) < 5:
            factors.append("Poor sleep quality")
        
        if not health_data.get('strong_social_support', False):
            factors.append("Limited social support")
        
        if health_data.get('recent_life_events', False):
            factors.append("Recent stressful life events")
        
        if health_data.get('substance_use', False):
            factors.append("Substance use")
        
        return factors
    
    def _generate_cardiovascular_recommendations(self, risk_level: RiskLevel, factors: List[str]) -> List[str]:
        """Generate cardiovascular health recommendations"""
        recommendations = []
        
        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            recommendations.append("Schedule immediate consultation with a cardiologist")
            recommendations.append("Monitor blood pressure daily")
            recommendations.append("Consider medication review with healthcare provider")
        
        if "High blood pressure" in factors:
            recommendations.append("Reduce sodium intake to less than 2,300mg per day")
            recommendations.append("Engage in regular aerobic exercise (150 minutes/week)")
        
        if "High cholesterol" in factors:
            recommendations.append("Adopt heart-healthy diet (Mediterranean or DASH diet)")
            recommendations.append("Consider statin therapy consultation")
        
        if "Smoking" in factors:
            recommendations.append("Quit smoking - seek smoking cessation support")
            recommendations.append("Avoid secondhand smoke exposure")
        
        if "Obesity" in factors:
            recommendations.append("Work with dietitian to develop weight loss plan")
            recommendations.append("Aim for 5-10% weight loss")
        
        recommendations.append("Regular cardiovascular health screenings")
        recommendations.append("Maintain healthy lifestyle habits")
        
        return recommendations
    
    def _generate_diabetes_recommendations(self, risk_level: RiskLevel, factors: List[str]) -> List[str]:
        """Generate diabetes prevention recommendations"""
        recommendations = []
        
        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            recommendations.append("Schedule consultation with endocrinologist")
            recommendations.append("Begin regular blood glucose monitoring")
            recommendations.append("Consider preventive medication consultation")
        
        if "Overweight/obesity" in factors:
            recommendations.append("Work with dietitian for weight management plan")
            recommendations.append("Aim for 7% weight loss through diet and exercise")
        
        if "Physical inactivity" in factors:
            recommendations.append("Start with 150 minutes of moderate exercise per week")
            recommendations.append("Include both aerobic and strength training")
        
        if "Poor diet" in factors:
            recommendations.append("Adopt balanced diet with controlled portions")
            recommendations.append("Focus on whole grains, vegetables, and lean proteins")
        
        recommendations.append("Regular diabetes screening (A1C, fasting glucose)")
        recommendations.append("Monitor blood pressure and cholesterol levels")
        
        return recommendations
    
    def _generate_mental_health_recommendations(self, risk_level: RiskLevel, factors: List[str]) -> List[str]:
        """Generate mental health recommendations"""
        recommendations = []
        
        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            recommendations.append("Schedule consultation with mental health professional")
            recommendations.append("Consider therapy or counseling options")
            recommendations.append("Discuss medication options with psychiatrist if needed")
        
        if "High stress levels" in factors:
            recommendations.append("Practice stress management techniques (meditation, yoga)")
            recommendations.append("Consider stress reduction programs")
        
        if "Poor sleep quality" in factors:
            recommendations.append("Establish regular sleep schedule")
            recommendations.append("Create relaxing bedtime routine")
            recommendations.append("Avoid screens 1 hour before bedtime")
        
        if "Limited social support" in factors:
            recommendations.append("Join support groups or community activities")
            recommendations.append("Strengthen existing relationships")
        
        recommendations.append("Regular mental health check-ins")
        recommendations.append("Maintain healthy lifestyle habits")
        
        return recommendations
    
    async def predict_health_trends(self, user_id: int, metric_name: str, 
                                  timeframe_days: int = 90) -> HealthTrend:
        """Predict health metric trends"""
        try:
            # Get historical health data
            historical_data = await self._get_historical_health_data(user_id, metric_name)
            
            if len(historical_data) < self.min_data_points:
                raise ExternalAPIError(f"Insufficient data for {metric_name} trend prediction")
            
            # Calculate current value
            current_value = historical_data[-1]['value']
            
            # Predict future value
            predicted_value = self._predict_future_value(historical_data, timeframe_days)
            
            # Determine trend direction
            trend_direction = self._determine_trend_direction(historical_data, predicted_value)
            
            # Calculate confidence
            confidence = self._calculate_trend_confidence(historical_data)
            
            # Identify factors
            factors = self._identify_trend_factors(historical_data, metric_name)
            
            # Generate recommendations
            recommendations = self._generate_trend_recommendations(trend_direction, metric_name)
            
            return HealthTrend(
                metric_name=metric_name,
                current_value=current_value,
                predicted_value=predicted_value,
                trend_direction=trend_direction,
                confidence=confidence,
                timeframe_days=timeframe_days,
                factors=factors,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Error in health trend prediction: {e}")
            raise ExternalAPIError(f"Health trend prediction failed: {str(e)}")
    
    def _predict_future_value(self, historical_data: List[Dict[str, Any]], 
                            timeframe_days: int) -> float:
        """Predict future value using simple linear regression"""
        try:
            # Extract values and dates
            values = [point['value'] for point in historical_data]
            dates = [point['date'] for point in historical_data]
            
            # Convert dates to days since first measurement
            first_date = min(dates)
            days = [(date - first_date).days for date in dates]
            
            # Simple linear regression
            n = len(values)
            sum_x = sum(days)
            sum_y = sum(values)
            sum_xy = sum(days[i] * values[i] for i in range(n))
            sum_x2 = sum(days[i] ** 2 for i in range(n))
            
            # Calculate slope and intercept
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
            intercept = (sum_y - slope * sum_x) / n
            
            # Predict future value
            future_days = max(days) + timeframe_days
            predicted_value = slope * future_days + intercept
            
            return max(predicted_value, 0)  # Ensure non-negative for health metrics
            
        except Exception as e:
            logger.error(f"Error in value prediction: {e}")
            return historical_data[-1]['value']  # Return current value as fallback
    
    def _determine_trend_direction(self, historical_data: List[Dict[str, Any]], 
                                 predicted_value: float) -> TrendDirection:
        """Determine trend direction"""
        current_value = historical_data[-1]['value']
        change_percentage = (predicted_value - current_value) / current_value
        
        if change_percentage > 0.05:  # 5% improvement
            return TrendDirection.IMPROVING
        elif change_percentage < -0.05:  # 5% decline
            return TrendDirection.DECLINING
        elif abs(change_percentage) <= 0.05:  # Within 5%
            return TrendDirection.STABLE
        else:
            return TrendDirection.FLUCTUATING
    
    async def generate_early_warnings(self, user_id: int) -> List[EarlyWarning]:
        """Generate early warnings for potential health issues"""
        try:
            warnings = []
            
            # Get user health data
            health_data = await self._get_user_health_data(user_id)
            if not health_data:
                return warnings
            
            # Check for various warning conditions
            warnings.extend(self._check_blood_pressure_warnings(health_data))
            warnings.extend(self._check_blood_sugar_warnings(health_data))
            warnings.extend(self._check_weight_warnings(health_data))
            warnings.extend(self._check_sleep_warnings(health_data))
            warnings.extend(self._check_stress_warnings(health_data))
            
            return warnings
            
        except Exception as e:
            logger.error(f"Error generating early warnings: {e}")
            return []
    
    def _check_blood_pressure_warnings(self, health_data: Dict[str, Any]) -> List[EarlyWarning]:
        """Check for blood pressure warnings"""
        warnings = []
        
        systolic_bp = health_data.get('systolic_bp', 0)
        diastolic_bp = health_data.get('diastolic_bp', 0)
        
        if systolic_bp > 180 or diastolic_bp > 110:
            warnings.append(EarlyWarning(
                warning_type="Hypertensive Crisis",
                severity=RiskLevel.CRITICAL,
                probability=0.9,
                timeframe_days=1,
                symptoms=["Severe headache", "Chest pain", "Vision problems"],
                risk_factors=["Uncontrolled hypertension"],
                recommendations=["Seek immediate medical attention", "Call emergency services if severe symptoms"],
                urgency="immediate"
            ))
        elif systolic_bp > 140 or diastolic_bp > 90:
            warnings.append(EarlyWarning(
                warning_type="High Blood Pressure",
                severity=RiskLevel.HIGH,
                probability=0.7,
                timeframe_days=7,
                symptoms=["Headache", "Shortness of breath", "Nosebleeds"],
                risk_factors=["Lifestyle factors", "Family history"],
                recommendations=["Schedule doctor appointment", "Monitor blood pressure daily", "Reduce salt intake"],
                urgency="high"
            ))
        
        return warnings
    
    def _check_blood_sugar_warnings(self, health_data: Dict[str, Any]) -> List[EarlyWarning]:
        """Check for blood sugar warnings"""
        warnings = []
        
        fasting_glucose = health_data.get('fasting_glucose', 0)
        a1c = health_data.get('a1c', 0)
        
        if fasting_glucose > 126 or a1c > 6.5:
            warnings.append(EarlyWarning(
                warning_type="High Blood Sugar",
                severity=RiskLevel.HIGH,
                probability=0.8,
                timeframe_days=14,
                symptoms=["Increased thirst", "Frequent urination", "Fatigue"],
                risk_factors=["Poor diet", "Physical inactivity", "Family history"],
                recommendations=["Schedule diabetes screening", "Improve diet", "Increase physical activity"],
                urgency="high"
            ))
        
        return warnings
    
    def _check_weight_warnings(self, health_data: Dict[str, Any]) -> List[EarlyWarning]:
        """Check for weight-related warnings"""
        warnings = []
        
        bmi = health_data.get('bmi', 0)
        weight_change = health_data.get('recent_weight_change', 0)
        
        if bmi > 30:
            warnings.append(EarlyWarning(
                warning_type="Obesity Risk",
                severity=RiskLevel.MODERATE,
                probability=0.6,
                timeframe_days=30,
                symptoms=["Difficulty with physical activity", "Joint pain"],
                risk_factors=["Poor diet", "Physical inactivity"],
                recommendations=["Consult with dietitian", "Start exercise program", "Monitor calorie intake"],
                urgency="moderate"
            ))
        elif abs(weight_change) > 10:  # 10% weight change
            warnings.append(EarlyWarning(
                warning_type="Significant Weight Change",
                severity=RiskLevel.MODERATE,
                probability=0.5,
                timeframe_days=30,
                symptoms=["Fatigue", "Changes in appetite"],
                risk_factors=["Stress", "Dietary changes", "Medical conditions"],
                recommendations=["Schedule doctor appointment", "Monitor weight trends", "Review lifestyle changes"],
                urgency="moderate"
            ))
        
        return warnings
    
    def _check_sleep_warnings(self, health_data: Dict[str, Any]) -> List[EarlyWarning]:
        """Check for sleep-related warnings"""
        warnings = []
        
        sleep_quality = health_data.get('sleep_quality', 7)
        sleep_duration = health_data.get('sleep_duration', 8)
        
        if sleep_quality < 4 or sleep_duration < 6:
            warnings.append(EarlyWarning(
                warning_type="Poor Sleep Quality",
                severity=RiskLevel.MODERATE,
                probability=0.6,
                timeframe_days=7,
                symptoms=["Fatigue", "Difficulty concentrating", "Mood changes"],
                risk_factors=["Stress", "Poor sleep hygiene", "Medical conditions"],
                recommendations=["Improve sleep hygiene", "Establish regular sleep schedule", "Reduce screen time before bed"],
                urgency="moderate"
            ))
        
        return warnings
    
    def _check_stress_warnings(self, health_data: Dict[str, Any]) -> List[EarlyWarning]:
        """Check for stress-related warnings"""
        warnings = []
        
        stress_level = health_data.get('stress_level', 5)
        
        if stress_level > 8:
            warnings.append(EarlyWarning(
                warning_type="High Stress Levels",
                severity=RiskLevel.MODERATE,
                probability=0.7,
                timeframe_days=14,
                symptoms=["Anxiety", "Irritability", "Sleep problems", "Physical tension"],
                risk_factors=["Work pressure", "Life events", "Poor coping mechanisms"],
                recommendations=["Practice stress management techniques", "Consider counseling", "Prioritize self-care"],
                urgency="moderate"
            ))
        
        return warnings
    
    async def generate_preventive_recommendations(self, user_id: int) -> List[PreventiveRecommendation]:
        """Generate preventive care recommendations"""
        try:
            recommendations = []
            
            # Get user health data
            health_data = await self._get_user_health_data(user_id)
            if not health_data:
                return recommendations
            
            # Age-based recommendations
            age = health_data.get('age', 0)
            if age >= 50:
                recommendations.append(PreventiveRecommendation(
                    recommendation_type="Colon Cancer Screening",
                    priority="high",
                    description="Schedule colonoscopy or stool-based screening",
                    rationale="Recommended for adults 50+ to detect early signs of colon cancer",
                    expected_benefit="Early detection of colorectal cancer",
                    timeframe="Within 6 months",
                    resources=["Gastroenterologist", "Primary care provider"],
                    confidence=0.9
                ))
            
            if age >= 40:
                recommendations.append(PreventiveRecommendation(
                    recommendation_type="Breast Cancer Screening",
                    priority="high",
                    description="Schedule mammogram",
                    rationale="Recommended for women 40+ to detect early breast cancer",
                    expected_benefit="Early detection of breast cancer",
                    timeframe="Annually",
                    resources=["Mammography center", "Primary care provider"],
                    confidence=0.9
                ))
            
            # Lifestyle recommendations
            if not health_data.get('regular_exercise', False):
                recommendations.append(PreventiveRecommendation(
                    recommendation_type="Physical Activity",
                    priority="medium",
                    description="Start regular exercise program",
                    rationale="Regular physical activity reduces risk of chronic diseases",
                    expected_benefit="Improved cardiovascular health, weight management",
                    timeframe="Start within 2 weeks",
                    resources=["Personal trainer", "Exercise programs", "Fitness apps"],
                    confidence=0.8
                ))
            
            if health_data.get('diet_quality', 'good') == 'poor':
                recommendations.append(PreventiveRecommendation(
                    recommendation_type="Diet Improvement",
                    priority="medium",
                    description="Consult with registered dietitian",
                    rationale="Healthy diet is fundamental to disease prevention",
                    expected_benefit="Better nutrition, reduced disease risk",
                    timeframe="Within 1 month",
                    resources=["Registered dietitian", "Nutrition programs"],
                    confidence=0.8
                ))
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating preventive recommendations: {e}")
            return []
    
    async def _get_user_health_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user health data for analysis"""
        try:
            db = next(get_db())
            
            # Get user health profile
            profile = db.query(UserHealthProfile).filter(
                UserHealthProfile.user_id == user_id
            ).first()
            
            if not profile:
                return None
            
            # Convert to dictionary
            health_data = {
                'age': profile.age,
                'gender': profile.gender,
                'bmi': profile.bmi,
                'systolic_bp': profile.systolic_blood_pressure,
                'diastolic_bp': profile.diastolic_blood_pressure,
                'total_cholesterol': profile.total_cholesterol,
                'smoking': profile.smoking_status == 'current_smoker',
                'diabetes': profile.diabetes_status == 'diagnosed',
                'family_history_cardiovascular': profile.family_history_cardiovascular,
                'family_history_diabetes': profile.family_history_diabetes,
                'family_history_mental_health': profile.family_history_mental_health,
                'regular_exercise': profile.activity_level in ['moderately_active', 'very_active'],
                'diet_quality': profile.diet_quality,
                'stress_level': profile.stress_level,
                'sleep_quality': profile.sleep_quality,
                'sleep_duration': profile.sleep_duration,
                'strong_social_support': profile.social_support_level in ['strong', 'very_strong'],
                'recent_life_events': profile.recent_life_events,
                'substance_use': profile.substance_use_status == 'current_user',
                'gestational_diabetes_history': profile.gestational_diabetes_history,
                'polycystic_ovary_syndrome': profile.polycystic_ovary_syndrome
            }
            
            return health_data
            
        except Exception as e:
            logger.error(f"Error getting user health data: {e}")
            return None
    
    async def _get_historical_health_data(self, user_id: int, metric_name: str) -> List[Dict[str, Any]]:
        """Get historical health data for trend analysis"""
        try:
            db = next(get_db())
            
            # Get health metrics aggregation
            metrics = db.query(HealthMetricsAggregation).filter(
                and_(
                    HealthMetricsAggregation.user_id == user_id,
                    HealthMetricsAggregation.metric_name == metric_name
                )
            ).order_by(HealthMetricsAggregation.aggregation_date).all()
            
            return [
                {
                    'date': metric.aggregation_date,
                    'value': metric.average_value
                }
                for metric in metrics
            ]
            
        except Exception as e:
            logger.error(f"Error getting historical health data: {e}")
            return []
    
    def _calculate_assessment_confidence(self, health_data: Dict[str, Any], assessment_type: str) -> float:
        """Calculate confidence in risk assessment"""
        # Count available data points
        available_fields = sum(1 for value in health_data.values() if value is not None)
        total_fields = len(health_data)
        
        # Base confidence on data completeness
        data_completeness = available_fields / total_fields
        
        # Adjust based on assessment type
        if assessment_type == "cardiovascular":
            required_fields = ['age', 'gender', 'systolic_bp', 'diastolic_bp', 'total_cholesterol']
        elif assessment_type == "diabetes":
            required_fields = ['age', 'bmi', 'family_history_diabetes', 'regular_exercise']
        elif assessment_type == "mental_health":
            required_fields = ['stress_level', 'sleep_quality', 'family_history_mental_health']
        else:
            required_fields = []
        
        # Check required fields
        required_completeness = sum(1 for field in required_fields if health_data.get(field) is not None) / len(required_fields)
        
        # Combine data completeness and required field completeness
        confidence = (data_completeness * 0.4 + required_completeness * 0.6)
        
        return min(confidence, 1.0)
    
    def _calculate_trend_confidence(self, historical_data: List[Dict[str, Any]]) -> float:
        """Calculate confidence in trend prediction"""
        if len(historical_data) < self.min_data_points:
            return 0.3
        
        # Calculate data consistency
        values = [point['value'] for point in historical_data]
        mean_value = np.mean(values)
        std_value = np.std(values)
        
        if mean_value == 0:
            return 0.5
        
        # Coefficient of variation
        cv = std_value / mean_value
        
        # Higher confidence for more consistent data
        if cv < 0.1:
            confidence = 0.9
        elif cv < 0.2:
            confidence = 0.8
        elif cv < 0.3:
            confidence = 0.7
        else:
            confidence = 0.6
        
        # Adjust for data points
        data_points_factor = min(len(historical_data) / 20.0, 1.0)
        confidence *= data_points_factor
        
        return confidence
    
    def _identify_trend_factors(self, historical_data: List[Dict[str, Any]], metric_name: str) -> List[str]:
        """Identify factors affecting health trends"""
        factors = []
        
        # Analyze trend consistency
        values = [point['value'] for point in historical_data]
        if len(values) >= 3:
            recent_trend = values[-1] - values[-3]
            if abs(recent_trend) > np.std(values) * 2:
                factors.append(f"Recent significant change in {metric_name}")
        
        # Check for seasonal patterns
        if len(historical_data) >= 12:
            factors.append("Seasonal variations may affect trends")
        
        # Data quality factors
        if len(historical_data) < 10:
            factors.append("Limited historical data available")
        
        return factors
    
    def _generate_trend_recommendations(self, trend_direction: TrendDirection, metric_name: str) -> List[str]:
        """Generate recommendations based on trend direction"""
        recommendations = []
        
        if trend_direction == TrendDirection.DECLINING:
            recommendations.append(f"Monitor {metric_name} more frequently")
            recommendations.append("Consult healthcare provider about declining trend")
            recommendations.append("Review lifestyle factors affecting this metric")
        elif trend_direction == TrendDirection.IMPROVING:
            recommendations.append(f"Continue current practices improving {metric_name}")
            recommendations.append("Maintain positive lifestyle changes")
        elif trend_direction == TrendDirection.FLUCTUATING:
            recommendations.append(f"Track {metric_name} more consistently")
            recommendations.append("Identify factors causing fluctuations")
        
        recommendations.append("Regular health check-ups recommended")
        
        return recommendations

# Global predictive analytics backend instance
predictive_analytics_backend = None

def get_predictive_analytics_backend() -> PredictiveAnalyticsBackend:
    """Get or create predictive analytics backend instance"""
    global predictive_analytics_backend
    if predictive_analytics_backend is None:
        predictive_analytics_backend = PredictiveAnalyticsBackend()
    return predictive_analytics_backend 
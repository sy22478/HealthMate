"""
Predictive Analytics Backend Router
FastAPI router for health risk assessment, trend prediction, and preventive care recommendations
"""

import time
import logging
from typing import List, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer

from app.schemas.enhanced_health_schemas import (
    RiskAssessmentRequest, RiskAssessmentResponse, PredictionType, RiskLevel,
    HealthTrendRequest, HealthTrendResponse, TrendDirection,
    EarlyWarningResponse, PreventiveRecommendationResponse, PredictiveAnalyticsSummaryResponse
)
from app.services.enhanced.predictive_analytics import (
    get_predictive_analytics_backend, RiskAssessment, HealthTrend,
    EarlyWarning, PreventiveRecommendation
)
from app.utils.auth_middleware import get_current_user
from app.models.user import User
from app.config import settings

logger = logging.getLogger(__name__)
security = HTTPBearer()

router = APIRouter(prefix="/predictive-analytics", tags=["Predictive Analytics Backend"])

# Initialize predictive analytics backend
predictive_analytics = get_predictive_analytics_backend()

@router.post("/risk-assessment", response_model=RiskAssessmentResponse)
async def assess_health_risk(
    request: RiskAssessmentRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Assess health risk for various conditions
    
    Performs comprehensive risk assessment for:
    - Cardiovascular disease risk
    - Diabetes risk
    - Mental health risk
    
    Uses multiple factors including age, gender, medical history,
    lifestyle factors, and current health metrics.
    """
    try:
        start_time = time.time()
        
        # Perform risk assessment based on type
        if request.risk_type == PredictionType.CARDIOVASCULAR_RISK:
            assessment = await predictive_analytics.assess_cardiovascular_risk(current_user.id)
        elif request.risk_type == PredictionType.DIABETES_RISK:
            assessment = await predictive_analytics.assess_diabetes_risk(current_user.id)
        elif request.risk_type == PredictionType.MENTAL_HEALTH_RISK:
            assessment = await predictive_analytics.assess_mental_health_risk(current_user.id)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported risk assessment type: {request.risk_type}"
            )
        
        processing_time = time.time() - start_time
        
        logger.info(f"Risk assessment completed for user {current_user.id} in {processing_time:.3f}s")
        
        return RiskAssessmentResponse(
            risk_type=assessment.risk_type,
            risk_level=assessment.risk_level,
            risk_score=assessment.risk_score,
            confidence=assessment.confidence,
            factors=assessment.factors,
            recommendations=assessment.recommendations if request.include_recommendations else [],
            assessment_date=assessment.assessment_date,
            next_assessment_date=assessment.next_assessment_date
        )
        
    except Exception as e:
        logger.error(f"Error in risk assessment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Risk assessment failed: {str(e)}"
        )

@router.get("/risk-assessment/cardiovascular", response_model=RiskAssessmentResponse)
async def assess_cardiovascular_risk(
    current_user: User = Depends(get_current_user)
):
    """
    Assess cardiovascular disease risk
    
    Evaluates risk factors including:
    - Age and gender
    - Blood pressure levels
    - Cholesterol levels
    - Smoking status
    - Diabetes status
    - Obesity (BMI)
    - Family history
    """
    try:
        start_time = time.time()
        
        assessment = await predictive_analytics.assess_cardiovascular_risk(current_user.id)
        
        processing_time = time.time() - start_time
        
        logger.info(f"Cardiovascular risk assessment completed for user {current_user.id} in {processing_time:.3f}s")
        
        return RiskAssessmentResponse(
            risk_type=assessment.risk_type,
            risk_level=assessment.risk_level,
            risk_score=assessment.risk_score,
            confidence=assessment.confidence,
            factors=assessment.factors,
            recommendations=assessment.recommendations,
            assessment_date=assessment.assessment_date,
            next_assessment_date=assessment.next_assessment_date
        )
        
    except Exception as e:
        logger.error(f"Error in cardiovascular risk assessment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cardiovascular risk assessment failed: {str(e)}"
        )

@router.get("/risk-assessment/diabetes", response_model=RiskAssessmentResponse)
async def assess_diabetes_risk(
    current_user: User = Depends(get_current_user)
):
    """
    Assess diabetes risk
    
    Evaluates risk factors including:
    - Age and gender
    - BMI and obesity
    - Family history
    - Physical activity levels
    - Diet quality
    - Blood pressure
    - Gestational diabetes history
    - Polycystic ovary syndrome
    """
    try:
        start_time = time.time()
        
        assessment = await predictive_analytics.assess_diabetes_risk(current_user.id)
        
        processing_time = time.time() - start_time
        
        logger.info(f"Diabetes risk assessment completed for user {current_user.id} in {processing_time:.3f}s")
        
        return RiskAssessmentResponse(
            risk_type=assessment.risk_type,
            risk_level=assessment.risk_level,
            risk_score=assessment.risk_score,
            confidence=assessment.confidence,
            factors=assessment.factors,
            recommendations=assessment.recommendations,
            assessment_date=assessment.assessment_date,
            next_assessment_date=assessment.next_assessment_date
        )
        
    except Exception as e:
        logger.error(f"Error in diabetes risk assessment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Diabetes risk assessment failed: {str(e)}"
        )

@router.get("/risk-assessment/mental-health", response_model=RiskAssessmentResponse)
async def assess_mental_health_risk(
    current_user: User = Depends(get_current_user)
):
    """
    Assess mental health risk
    
    Evaluates risk factors including:
    - Age and gender
    - Family history
    - Stress levels
    - Sleep quality
    - Social support
    - Recent life events
    - Substance use
    """
    try:
        start_time = time.time()
        
        assessment = await predictive_analytics.assess_mental_health_risk(current_user.id)
        
        processing_time = time.time() - start_time
        
        logger.info(f"Mental health risk assessment completed for user {current_user.id} in {processing_time:.3f}s")
        
        return RiskAssessmentResponse(
            risk_type=assessment.risk_type,
            risk_level=assessment.risk_level,
            risk_score=assessment.risk_score,
            confidence=assessment.confidence,
            factors=assessment.factors,
            recommendations=assessment.recommendations,
            assessment_date=assessment.assessment_date,
            next_assessment_date=assessment.next_assessment_date
        )
        
    except Exception as e:
        logger.error(f"Error in mental health risk assessment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Mental health risk assessment failed: {str(e)}"
        )

@router.post("/health-trends", response_model=HealthTrendResponse)
async def predict_health_trends(
    request: HealthTrendRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Predict health metric trends
    
    Analyzes historical health data to predict future trends for:
    - Blood pressure
    - Blood sugar levels
    - Weight/BMI
    - Heart rate
    - Sleep quality
    - Stress levels
    - Other health metrics
    """
    try:
        start_time = time.time()
        
        trend = await predictive_analytics.predict_health_trends(
            user_id=current_user.id,
            metric_name=request.metric_name,
            timeframe_days=request.timeframe_days
        )
        
        processing_time = time.time() - start_time
        
        logger.info(f"Health trend prediction completed for user {current_user.id} in {processing_time:.3f}s")
        
        return HealthTrendResponse(
            metric_name=trend.metric_name,
            current_value=trend.current_value,
            predicted_value=trend.predicted_value,
            trend_direction=trend.trend_direction,
            confidence=trend.confidence,
            timeframe_days=trend.timeframe_days,
            factors=trend.factors,
            recommendations=trend.recommendations
        )
        
    except Exception as e:
        logger.error(f"Error in health trend prediction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health trend prediction failed: {str(e)}"
        )

@router.get("/health-trends/{metric_name}", response_model=HealthTrendResponse)
async def predict_health_trend(
    metric_name: str,
    timeframe_days: int = Query(90, ge=30, le=365, description="Prediction timeframe in days"),
    current_user: User = Depends(get_current_user)
):
    """
    Predict health trend for specific metric
    
    Provides trend prediction for a specific health metric with:
    - Current value analysis
    - Future value prediction
    - Trend direction identification
    - Confidence scoring
    - Personalized recommendations
    """
    try:
        start_time = time.time()
        
        trend = await predictive_analytics.predict_health_trends(
            user_id=current_user.id,
            metric_name=metric_name,
            timeframe_days=timeframe_days
        )
        
        processing_time = time.time() - start_time
        
        logger.info(f"Health trend prediction for {metric_name} completed for user {current_user.id} in {processing_time:.3f}s")
        
        return HealthTrendResponse(
            metric_name=trend.metric_name,
            current_value=trend.current_value,
            predicted_value=trend.predicted_value,
            trend_direction=trend.trend_direction,
            confidence=trend.confidence,
            timeframe_days=trend.timeframe_days,
            factors=trend.factors,
            recommendations=trend.recommendations
        )
        
    except Exception as e:
        logger.error(f"Error in health trend prediction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health trend prediction failed: {str(e)}"
        )

@router.get("/early-warnings", response_model=List[EarlyWarningResponse])
async def get_early_warnings(
    current_user: User = Depends(get_current_user)
):
    """
    Get early warnings for potential health issues
    
    Monitors health data for early warning signs including:
    - Blood pressure warnings
    - Blood sugar warnings
    - Weight-related warnings
    - Sleep quality warnings
    - Stress level warnings
    """
    try:
        start_time = time.time()
        
        warnings = await predictive_analytics.generate_early_warnings(current_user.id)
        
        processing_time = time.time() - start_time
        
        logger.info(f"Early warnings generated for user {current_user.id} in {processing_time:.3f}s")
        
        return [
            EarlyWarningResponse(
                warning_type=warning.warning_type,
                severity=warning.severity,
                probability=warning.probability,
                timeframe_days=warning.timeframe_days,
                symptoms=warning.symptoms,
                risk_factors=warning.risk_factors,
                recommendations=warning.recommendations,
                urgency=warning.urgency
            )
            for warning in warnings
        ]
        
    except Exception as e:
        logger.error(f"Error generating early warnings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Early warning generation failed: {str(e)}"
        )

@router.get("/preventive-recommendations", response_model=List[PreventiveRecommendationResponse])
async def get_preventive_recommendations(
    current_user: User = Depends(get_current_user)
):
    """
    Get preventive care recommendations
    
    Generates personalized preventive care recommendations based on:
    - Age and gender
    - Medical history
    - Current health status
    - Lifestyle factors
    - Risk assessments
    """
    try:
        start_time = time.time()
        
        recommendations = await predictive_analytics.generate_preventive_recommendations(current_user.id)
        
        processing_time = time.time() - start_time
        
        logger.info(f"Preventive recommendations generated for user {current_user.id} in {processing_time:.3f}s")
        
        return [
            PreventiveRecommendationResponse(
                recommendation_type=rec.recommendation_type,
                priority=rec.priority,
                description=rec.description,
                rationale=rec.rationale,
                expected_benefit=rec.expected_benefit,
                timeframe=rec.timeframe,
                resources=rec.resources,
                confidence=rec.confidence
            )
            for rec in recommendations
        ]
        
    except Exception as e:
        logger.error(f"Error generating preventive recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Preventive recommendation generation failed: {str(e)}"
        )

@router.get("/comprehensive-assessment")
async def get_comprehensive_assessment(
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive health assessment
    
    Performs all available assessments and provides:
    - Cardiovascular risk assessment
    - Diabetes risk assessment
    - Mental health risk assessment
    - Early warnings
    - Preventive recommendations
    - Health trend predictions
    """
    try:
        start_time = time.time()
        
        # Perform all assessments
        cardiovascular_risk = await predictive_analytics.assess_cardiovascular_risk(current_user.id)
        diabetes_risk = await predictive_analytics.assess_diabetes_risk(current_user.id)
        mental_health_risk = await predictive_analytics.assess_mental_health_risk(current_user.id)
        early_warnings = await predictive_analytics.generate_early_warnings(current_user.id)
        preventive_recommendations = await predictive_analytics.generate_preventive_recommendations(current_user.id)
        
        processing_time = time.time() - start_time
        
        logger.info(f"Comprehensive assessment completed for user {current_user.id} in {processing_time:.3f}s")
        
        return {
            "user_id": current_user.id,
            "assessment_date": datetime.utcnow().isoformat(),
            "processing_time": processing_time,
            "cardiovascular_risk": {
                "risk_level": cardiovascular_risk.risk_level.value,
                "risk_score": cardiovascular_risk.risk_score,
                "confidence": cardiovascular_risk.confidence,
                "factors": cardiovascular_risk.factors,
                "recommendations": cardiovascular_risk.recommendations
            },
            "diabetes_risk": {
                "risk_level": diabetes_risk.risk_level.value,
                "risk_score": diabetes_risk.risk_score,
                "confidence": diabetes_risk.confidence,
                "factors": diabetes_risk.factors,
                "recommendations": diabetes_risk.recommendations
            },
            "mental_health_risk": {
                "risk_level": mental_health_risk.risk_level.value,
                "risk_score": mental_health_risk.risk_score,
                "confidence": mental_health_risk.confidence,
                "factors": mental_health_risk.factors,
                "recommendations": mental_health_risk.recommendations
            },
            "early_warnings": [
                {
                    "warning_type": warning.warning_type,
                    "severity": warning.severity.value,
                    "probability": warning.probability,
                    "urgency": warning.urgency,
                    "recommendations": warning.recommendations
                }
                for warning in early_warnings
            ],
            "preventive_recommendations": [
                {
                    "recommendation_type": rec.recommendation_type,
                    "priority": rec.priority,
                    "description": rec.description,
                    "timeframe": rec.timeframe
                }
                for rec in preventive_recommendations
            ]
        }
        
    except Exception as e:
        logger.error(f"Error in comprehensive assessment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Comprehensive assessment failed: {str(e)}"
        )

@router.get("/analytics/summary", response_model=PredictiveAnalyticsSummaryResponse)
async def get_predictive_analytics_summary(
    current_user: User = Depends(get_current_user)
):
    """
    Get predictive analytics summary
    
    Provides summary statistics including:
    - Total assessments performed
    - Average confidence scores
    - Risk level distribution
    - Active warnings count
    - Preventive recommendations count
    """
    try:
        start_time = time.time()
        
        # Get all assessments for summary
        cardiovascular_risk = await predictive_analytics.assess_cardiovascular_risk(current_user.id)
        diabetes_risk = await predictive_analytics.assess_diabetes_risk(current_user.id)
        mental_health_risk = await predictive_analytics.assess_mental_health_risk(current_user.id)
        early_warnings = await predictive_analytics.generate_early_warnings(current_user.id)
        preventive_recommendations = await predictive_analytics.generate_preventive_recommendations(current_user.id)
        
        # Calculate summary statistics
        total_assessments = 3
        average_confidence = (cardiovascular_risk.confidence + diabetes_risk.confidence + mental_health_risk.confidence) / 3
        
        risk_distribution = {
            "low": 0,
            "moderate": 0,
            "high": 0,
            "critical": 0
        }
        
        for assessment in [cardiovascular_risk, diabetes_risk, mental_health_risk]:
            risk_distribution[assessment.risk_level.value] += 1
        
        processing_time = time.time() - start_time
        
        logger.info(f"Predictive analytics summary generated for user {current_user.id} in {processing_time:.3f}s")
        
        return PredictiveAnalyticsSummaryResponse(
            total_assessments=total_assessments,
            average_confidence=average_confidence,
            risk_distribution=risk_distribution,
            active_warnings=len(early_warnings),
            preventive_recommendations=len(preventive_recommendations)
        )
        
    except Exception as e:
        logger.error(f"Error generating predictive analytics summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Predictive analytics summary generation failed: {str(e)}"
        )

@router.get("/capabilities")
async def get_predictive_analytics_capabilities():
    """
    Get available predictive analytics capabilities
    """
    return {
        "risk_assessment": {
            "cardiovascular_risk": "Assess cardiovascular disease risk using multiple factors",
            "diabetes_risk": "Assess diabetes risk based on lifestyle and medical factors",
            "mental_health_risk": "Assess mental health risk using psychological and social factors"
        },
        "trend_prediction": {
            "health_trends": "Predict future health metric trends using historical data",
            "metric_prediction": "Predict specific health metric values over time",
            "trend_analysis": "Analyze trend directions and confidence levels"
        },
        "early_warning_system": {
            "blood_pressure_warnings": "Monitor blood pressure for warning signs",
            "blood_sugar_warnings": "Monitor blood sugar levels for diabetes risk",
            "weight_warnings": "Monitor weight changes and BMI trends",
            "sleep_warnings": "Monitor sleep quality and duration",
            "stress_warnings": "Monitor stress levels and mental health indicators"
        },
        "preventive_care": {
            "age_based_recommendations": "Generate age-appropriate preventive care recommendations",
            "lifestyle_recommendations": "Provide lifestyle-based preventive care suggestions",
            "screening_recommendations": "Recommend appropriate health screenings",
            "vaccination_recommendations": "Suggest vaccination schedules"
        },
        "analytics": {
            "comprehensive_assessment": "Perform complete health assessment with all available metrics",
            "summary_statistics": "Generate summary statistics and analytics",
            "confidence_scoring": "Calculate confidence levels for all predictions",
            "trend_analysis": "Analyze health trends and patterns"
        }
    }

@router.get("/health")
async def predictive_analytics_health_check():
    """
    Health check endpoint for predictive analytics backend
    """
    try:
        # Test basic functionality
        test_health_data = {
            'age': 45,
            'gender': 'male',
            'bmi': 25,
            'systolic_bp': 120,
            'diastolic_bp': 80
        }
        
        # Test risk calculation
        risk_score = predictive_analytics._calculate_cardiovascular_risk(test_health_data)
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "risk_assessment": "available",
            "trend_prediction": "available",
            "early_warning_system": "available",
            "preventive_care": "available",
            "test_result": "successful",
            "test_risk_score": risk_score
        }
        
    except Exception as e:
        logger.error(f"Predictive analytics health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Predictive analytics backend unavailable: {str(e)}"
        ) 
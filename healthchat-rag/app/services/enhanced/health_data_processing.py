"""
Enhanced Health Data Processing Pipeline
Comprehensive service for health data ingestion, validation, transformation, and analytics
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
import statistics
from collections import defaultdict
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.database import get_db
from app.models.enhanced_health_models import (
    UserHealthProfile, HealthMetricsAggregation, EnhancedMedication, 
    EnhancedSymptomLog, HealthMetricsAggregation
)
from app.services.enhanced.data_integration import (
    DataIntegrationService, HealthDataPoint, DataType, DataSourceType
)
from app.exceptions.health_exceptions import HealthDataError, MedicalDataError
from app.utils.encryption_utils import field_encryption

logger = logging.getLogger(__name__)

class ProcessingStage(str, Enum):
    """Data processing stages"""
    INGESTION = "ingestion"
    VALIDATION = "validation"
    TRANSFORMATION = "transformation"
    ENRICHMENT = "enrichment"
    AGGREGATION = "aggregation"
    ANALYTICS = "analytics"
    STORAGE = "storage"

class DataQualityLevel(str, Enum):
    """Data quality levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    INVALID = "invalid"

@dataclass
class ProcessingResult:
    """Result of data processing operation"""
    success: bool
    stage: ProcessingStage
    data_points_processed: int
    data_points_valid: int
    data_points_invalid: int
    quality_score: float
    processing_time: float
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]

@dataclass
class AnomalyDetection:
    """Anomaly detection result"""
    data_point_id: str
    anomaly_type: str
    severity: str
    confidence: float
    description: str
    suggested_action: str
    detected_at: datetime

class HealthDataProcessor:
    """Main health data processing service"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.data_integration = DataIntegrationService()
        self.processing_rules = self._load_processing_rules()
        self.anomaly_detectors = self._initialize_anomaly_detectors()
    
    def _load_processing_rules(self) -> Dict[str, Any]:
        """Load data processing rules and thresholds"""
        return {
            'heart_rate': {
                'min_value': 30,
                'max_value': 200,
                'outlier_threshold': 2.5,  # Standard deviations
                'missing_threshold': 0.1,  # 10% missing data allowed
                'quality_weights': {
                    'completeness': 0.3,
                    'accuracy': 0.4,
                    'consistency': 0.3
                }
            },
            'blood_pressure': {
                'systolic': {'min': 70, 'max': 200},
                'diastolic': {'min': 40, 'max': 130},
                'ratio_threshold': 3.0,  # Max systolic/diastolic ratio
                'quality_weights': {
                    'completeness': 0.25,
                    'accuracy': 0.5,
                    'consistency': 0.25
                }
            },
            'steps': {
                'min_value': 0,
                'max_value': 50000,
                'daily_threshold': 100000,
                'quality_weights': {
                    'completeness': 0.4,
                    'accuracy': 0.4,
                    'consistency': 0.2
                }
            },
            'sleep': {
                'min_hours': 0,
                'max_hours': 24,
                'quality_weights': {
                    'completeness': 0.3,
                    'accuracy': 0.4,
                    'consistency': 0.3
                }
            },
            'weight': {
                'min_value': 10,
                'max_value': 500,
                'daily_change_threshold': 10,  # kg
                'quality_weights': {
                    'completeness': 0.2,
                    'accuracy': 0.6,
                    'consistency': 0.2
                }
            }
        }
    
    def _initialize_anomaly_detectors(self) -> Dict[str, Any]:
        """Initialize anomaly detection algorithms"""
        return {
            'statistical': self._statistical_anomaly_detection,
            'threshold': self._threshold_anomaly_detection,
            'trend': self._trend_anomaly_detection,
            'pattern': self._pattern_anomaly_detection
        }
    
    async def process_health_data(self, user_id: int, data_points: List[HealthDataPoint], 
                                stages: List[ProcessingStage] = None) -> ProcessingResult:
        """Process health data through the complete pipeline"""
        if stages is None:
            stages = list(ProcessingStage)
        
        start_time = datetime.utcnow()
        total_points = len(data_points)
        valid_points = 0
        invalid_points = 0
        errors = []
        warnings = []
        
        try:
            processed_data = data_points
            
            # Stage 1: Ingestion
            if ProcessingStage.INGESTION in stages:
                ingestion_result = await self._ingest_data(user_id, processed_data)
                processed_data = ingestion_result['data']
                errors.extend(ingestion_result['errors'])
                warnings.extend(ingestion_result['warnings'])
            
            # Stage 2: Validation
            if ProcessingStage.VALIDATION in stages:
                validation_result = await self._validate_data(processed_data)
                processed_data = validation_result['valid_data']
                valid_points = len(processed_data)
                invalid_points = total_points - valid_points
                errors.extend(validation_result['errors'])
                warnings.extend(validation_result['warnings'])
            
            # Stage 3: Transformation
            if ProcessingStage.TRANSFORMATION in stages:
                transformation_result = await self._transform_data(processed_data)
                processed_data = transformation_result['data']
                errors.extend(transformation_result['errors'])
                warnings.extend(transformation_result['warnings'])
            
            # Stage 4: Enrichment
            if ProcessingStage.ENRICHMENT in stages:
                enrichment_result = await self._enrich_data(user_id, processed_data)
                processed_data = enrichment_result['data']
                errors.extend(enrichment_result['errors'])
                warnings.extend(enrichment_result['warnings'])
            
            # Stage 5: Aggregation
            if ProcessingStage.AGGREGATION in stages:
                aggregation_result = await self._aggregate_data(user_id, processed_data)
                errors.extend(aggregation_result['errors'])
                warnings.extend(aggregation_result['warnings'])
            
            # Stage 6: Analytics
            if ProcessingStage.ANALYTICS in stages:
                analytics_result = await self._run_analytics(user_id, processed_data)
                errors.extend(analytics_result['errors'])
                warnings.extend(analytics_result['warnings'])
            
            # Stage 7: Storage
            if ProcessingStage.STORAGE in stages:
                storage_result = await self._store_data(user_id, processed_data)
                errors.extend(storage_result['errors'])
                warnings.extend(storage_result['warnings'])
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            quality_score = self._calculate_quality_score(processed_data, valid_points, total_points)
            
            return ProcessingResult(
                success=len(errors) == 0,
                stage=ProcessingStage.ANALYTICS if ProcessingStage.ANALYTICS in stages else stages[-1],
                data_points_processed=total_points,
                data_points_valid=valid_points,
                data_points_invalid=invalid_points,
                quality_score=quality_score,
                processing_time=processing_time,
                errors=errors,
                warnings=warnings,
                metadata={
                    'stages_completed': stages,
                    'data_sources': list(set(dp.source for dp in processed_data)),
                    'data_types': list(set(dp.data_type for dp in processed_data))
                }
            )
            
        except Exception as e:
            logger.error(f"Data processing failed: {str(e)}")
            return ProcessingResult(
                success=False,
                stage=ProcessingStage.INGESTION,
                data_points_processed=total_points,
                data_points_valid=0,
                data_points_invalid=total_points,
                quality_score=0.0,
                processing_time=(datetime.utcnow() - start_time).total_seconds(),
                errors=[str(e)],
                warnings=[],
                metadata={}
            )
    
    async def _ingest_data(self, user_id: int, data_points: List[HealthDataPoint]) -> Dict[str, Any]:
        """Ingest and prepare data for processing"""
        errors = []
        warnings = []
        ingested_data = []
        
        for point in data_points:
            try:
                # Basic ingestion checks
                if not point.user_id or point.user_id != user_id:
                    errors.append(f"Invalid user ID for data point: {point}")
                    continue
                
                if not point.timestamp:
                    errors.append(f"Missing timestamp for data point: {point}")
                    continue
                
                if not point.data_type:
                    errors.append(f"Missing data type for data point: {point}")
                    continue
                
                # Add ingestion metadata
                if not point.metadata:
                    point.metadata = {}
                point.metadata['ingested_at'] = datetime.utcnow().isoformat()
                point.metadata['ingestion_version'] = '1.0'
                
                ingested_data.append(point)
                
            except Exception as e:
                errors.append(f"Error ingesting data point: {str(e)}")
        
        return {
            'data': ingested_data,
            'errors': errors,
            'warnings': warnings
        }
    
    async def _validate_data(self, data_points: List[HealthDataPoint]) -> Dict[str, Any]:
        """Validate data points against quality rules"""
        errors = []
        warnings = []
        valid_data = []
        
        for point in data_points:
            try:
                validation_result = self._validate_data_point(point)
                
                if validation_result['is_valid']:
                    valid_data.append(point)
                else:
                    errors.extend(validation_result['errors'])
                
                warnings.extend(validation_result['warnings'])
                
            except Exception as e:
                errors.append(f"Error validating data point: {str(e)}")
        
        return {
            'valid_data': valid_data,
            'errors': errors,
            'warnings': warnings
        }
    
    def _validate_data_point(self, point: HealthDataPoint) -> Dict[str, Any]:
        """Validate a single data point"""
        errors = []
        warnings = []
        is_valid = True
        
        # Get validation rules for data type
        rules = self.processing_rules.get(point.data_type.value, {})
        
        if not rules:
            warnings.append(f"No validation rules found for data type: {point.data_type}")
            return {'is_valid': True, 'errors': errors, 'warnings': warnings}
        
        # Type-specific validation
        if point.data_type == DataType.HEART_RATE:
            is_valid, type_errors, type_warnings = self._validate_heart_rate(point, rules)
            errors.extend(type_errors)
            warnings.extend(type_warnings)
        
        elif point.data_type == DataType.BLOOD_PRESSURE:
            is_valid, type_errors, type_warnings = self._validate_blood_pressure(point, rules)
            errors.extend(type_errors)
            warnings.extend(type_warnings)
        
        elif point.data_type == DataType.STEPS:
            is_valid, type_errors, type_warnings = self._validate_steps(point, rules)
            errors.extend(type_errors)
            warnings.extend(type_warnings)
        
        elif point.data_type == DataType.SLEEP:
            is_valid, type_errors, type_warnings = self._validate_sleep(point, rules)
            errors.extend(type_errors)
            warnings.extend(type_warnings)
        
        elif point.data_type == DataType.WEIGHT:
            is_valid, type_errors, type_warnings = self._validate_weight(point, rules)
            errors.extend(type_errors)
            warnings.extend(type_warnings)
        
        # Confidence validation
        if point.confidence is not None and point.confidence < 0.5:
            warnings.append(f"Low confidence data point: {point.confidence}")
        
        return {
            'is_valid': is_valid,
            'errors': errors,
            'warnings': warnings
        }
    
    def _validate_heart_rate(self, point: HealthDataPoint, rules: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        """Validate heart rate data point"""
        errors = []
        warnings = []
        is_valid = True
        
        if not isinstance(point.value, (int, float)):
            errors.append("Heart rate value must be numeric")
            is_valid = False
        else:
            if point.value < rules['min_value'] or point.value > rules['max_value']:
                errors.append(f"Heart rate {point.value} outside valid range [{rules['min_value']}, {rules['max_value']}]")
                is_valid = False
            
            # Check for statistical outliers
            if point.value > 120 or point.value < 50:
                warnings.append(f"Unusual heart rate value: {point.value}")
        
        return is_valid, errors, warnings
    
    def _validate_blood_pressure(self, point: HealthDataPoint, rules: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        """Validate blood pressure data point"""
        errors = []
        warnings = []
        is_valid = True
        
        if isinstance(point.value, dict):
            systolic = point.value.get('systolic')
            diastolic = point.value.get('diastolic')
            
            if systolic is None or diastolic is None:
                errors.append("Blood pressure must have both systolic and diastolic values")
                is_valid = False
            else:
                # Validate systolic
                if systolic < rules['systolic']['min'] or systolic > rules['systolic']['max']:
                    errors.append(f"Systolic {systolic} outside valid range")
                    is_valid = False
                
                # Validate diastolic
                if diastolic < rules['diastolic']['min'] or diastolic > rules['diastolic']['max']:
                    errors.append(f"Diastolic {diastolic} outside valid range")
                    is_valid = False
                
                # Validate ratio
                if diastolic > 0 and systolic / diastolic > rules['ratio_threshold']:
                    warnings.append(f"Unusual blood pressure ratio: {systolic}/{diastolic}")
        else:
            errors.append("Blood pressure value must be a dictionary with systolic and diastolic")
            is_valid = False
        
        return is_valid, errors, warnings
    
    def _validate_steps(self, point: HealthDataPoint, rules: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        """Validate steps data point"""
        errors = []
        warnings = []
        is_valid = True
        
        if not isinstance(point.value, int):
            errors.append("Steps value must be an integer")
            is_valid = False
        else:
            if point.value < rules['min_value'] or point.value > rules['max_value']:
                errors.append(f"Steps {point.value} outside valid range")
                is_valid = False
            
            if point.value > rules['daily_threshold']:
                warnings.append(f"Unusually high step count: {point.value}")
        
        return is_valid, errors, warnings
    
    def _validate_sleep(self, point: HealthDataPoint, rules: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        """Validate sleep data point"""
        errors = []
        warnings = []
        is_valid = True
        
        if not isinstance(point.value, (int, float)):
            errors.append("Sleep value must be numeric")
            is_valid = False
        else:
            # Convert to hours if in minutes
            hours = point.value / 60 if point.value > 24 else point.value
            
            if hours < rules['min_hours'] or hours > rules['max_hours']:
                errors.append(f"Sleep duration {hours} hours outside valid range")
                is_valid = False
            
            if hours < 4 or hours > 12:
                warnings.append(f"Unusual sleep duration: {hours} hours")
        
        return is_valid, errors, warnings
    
    def _validate_weight(self, point: HealthDataPoint, rules: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        """Validate weight data point"""
        errors = []
        warnings = []
        is_valid = True
        
        if not isinstance(point.value, (int, float)):
            errors.append("Weight value must be numeric")
            is_valid = False
        else:
            if point.value < rules['min_value'] or point.value > rules['max_value']:
                errors.append(f"Weight {point.value} outside valid range")
                is_valid = False
        
        return is_valid, errors, warnings
    
    async def _transform_data(self, data_points: List[HealthDataPoint]) -> Dict[str, Any]:
        """Transform data points to standard format"""
        errors = []
        warnings = []
        transformed_data = []
        
        for point in data_points:
            try:
                transformed_point = self._transform_data_point(point)
                transformed_data.append(transformed_point)
                
            except Exception as e:
                errors.append(f"Error transforming data point: {str(e)}")
        
        return {
            'data': transformed_data,
            'errors': errors,
            'warnings': warnings
        }
    
    def _transform_data_point(self, point: HealthDataPoint) -> HealthDataPoint:
        """Transform a single data point"""
        # Add transformation metadata
        if not point.metadata:
            point.metadata = {}
        point.metadata['transformed_at'] = datetime.utcnow().isoformat()
        point.metadata['transformation_version'] = '1.0'
        
        # Type-specific transformations
        if point.data_type == DataType.HEART_RATE:
            # Ensure heart rate is in bpm
            if point.unit and point.unit != 'bpm':
                # Convert if needed
                pass
        
        elif point.data_type == DataType.SLEEP:
            # Ensure sleep is in minutes
            if point.unit == 'hours':
                point.value = point.value * 60
                point.unit = 'minutes'
        
        elif point.data_type == DataType.WEIGHT:
            # Ensure weight is in kg
            if point.unit == 'lbs':
                point.value = point.value * 0.453592
                point.unit = 'kg'
        
        return point
    
    async def _enrich_data(self, user_id: int, data_points: List[HealthDataPoint]) -> Dict[str, Any]:
        """Enrich data points with additional context"""
        errors = []
        warnings = []
        enriched_data = []
        
        # Get user health profile for context
        try:
            health_profile = self.db.query(UserHealthProfile).filter(
                UserHealthProfile.user_id == user_id
            ).first()
        except Exception as e:
            errors.append(f"Error fetching health profile: {str(e)}")
            health_profile = None
        
        for point in data_points:
            try:
                enriched_point = self._enrich_data_point(point, health_profile)
                enriched_data.append(enriched_point)
                
            except Exception as e:
                errors.append(f"Error enriching data point: {str(e)}")
        
        return {
            'data': enriched_data,
            'errors': errors,
            'warnings': warnings
        }
    
    def _enrich_data_point(self, point: HealthDataPoint, health_profile: UserHealthProfile) -> HealthDataPoint:
        """Enrich a single data point with context"""
        if not point.metadata:
            point.metadata = {}
        
        point.metadata['enriched_at'] = datetime.utcnow().isoformat()
        
        # Add health profile context
        if health_profile:
            point.metadata['user_context'] = {
                'age': health_profile.user.age if hasattr(health_profile.user, 'age') else None,
                'gender': health_profile.gender.value if health_profile.gender else None,
                'activity_level': health_profile.activity_level.value if health_profile.activity_level else None,
                'bmi': health_profile.bmi
            }
        
        # Add time-based context
        point.metadata['time_context'] = {
            'hour_of_day': point.timestamp.hour,
            'day_of_week': point.timestamp.weekday(),
            'is_weekend': point.timestamp.weekday() >= 5,
            'season': self._get_season(point.timestamp)
        }
        
        return point
    
    def _get_season(self, timestamp: datetime) -> str:
        """Get season for a timestamp"""
        month = timestamp.month
        if month in [12, 1, 2]:
            return 'winter'
        elif month in [3, 4, 5]:
            return 'spring'
        elif month in [6, 7, 8]:
            return 'summer'
        else:
            return 'fall'
    
    async def _aggregate_data(self, user_id: int, data_points: List[HealthDataPoint]) -> Dict[str, Any]:
        """Aggregate data points into metrics"""
        errors = []
        warnings = []
        
        try:
            # Group data by type and time period
            grouped_data = self._group_data_for_aggregation(data_points)
            
            # Create aggregation records
            for period, group_data in grouped_data.items():
                for data_type, points in group_data.items():
                    try:
                        metrics = self._calculate_aggregation_metrics(points)
                        
                        # Create or update aggregation record
                        aggregation = HealthMetricsAggregation(
                            health_profile_id=user_id,  # Assuming 1:1 relationship
                            aggregation_period='daily',
                            period_start=period,
                            period_end=period + timedelta(days=1),
                            **metrics
                        )
                        
                        # Save to database
                        self.db.add(aggregation)
                        
                    except Exception as e:
                        errors.append(f"Error aggregating {data_type} for {period}: {str(e)}")
            
            self.db.commit()
            
        except Exception as e:
            errors.append(f"Error in data aggregation: {str(e)}")
            self.db.rollback()
        
        return {
            'errors': errors,
            'warnings': warnings
        }
    
    def _group_data_for_aggregation(self, data_points: List[HealthDataPoint]) -> Dict[datetime, Dict[str, List[HealthDataPoint]]]:
        """Group data points by date and type for aggregation"""
        grouped = defaultdict(lambda: defaultdict(list))
        
        for point in data_points:
            date_key = point.timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
            grouped[date_key][point.data_type.value].append(point)
        
        return grouped
    
    def _calculate_aggregation_metrics(self, data_points: List[HealthDataPoint]) -> Dict[str, Any]:
        """Calculate aggregation metrics for a group of data points"""
        metrics = {}
        
        if not data_points:
            return metrics
        
        data_type = data_points[0].data_type
        values = [p.value for p in data_points if isinstance(p.value, (int, float))]
        
        if not values:
            return metrics
        
        if data_type == DataType.HEART_RATE:
            metrics.update({
                'avg_heart_rate': statistics.mean(values),
                'min_heart_rate': min(values),
                'max_heart_rate': max(values),
                'resting_heart_rate': min(values)  # Assume minimum is resting
            })
        
        elif data_type == DataType.STEPS:
            metrics.update({
                'total_steps': sum(values),
                'avg_steps_per_day': statistics.mean(values)
            })
        
        elif data_type == DataType.SLEEP:
            # Convert minutes to hours
            hours = [v / 60 for v in values]
            metrics.update({
                'avg_sleep_hours': statistics.mean(hours),
                'total_sleep_hours': sum(hours)
            })
        
        elif data_type == DataType.WEIGHT:
            metrics.update({
                'avg_weight': statistics.mean(values),
                'weight_change': values[-1] - values[0] if len(values) > 1 else 0
            })
        
        return metrics
    
    async def _run_analytics(self, user_id: int, data_points: List[HealthDataPoint]) -> Dict[str, Any]:
        """Run analytics on processed data"""
        errors = []
        warnings = []
        
        try:
            # Detect anomalies
            anomalies = await self._detect_anomalies(data_points)
            
            # Calculate trends
            trends = await self._calculate_trends(data_points)
            
            # Generate insights
            insights = await self._generate_insights(user_id, data_points, trends, anomalies)
            
            # Store analytics results
            # This would typically be stored in a separate analytics table
            
        except Exception as e:
            errors.append(f"Error running analytics: {str(e)}")
        
        return {
            'errors': errors,
            'warnings': warnings
        }
    
    async def _detect_anomalies(self, data_points: List[HealthDataPoint]) -> List[AnomalyDetection]:
        """Detect anomalies in health data"""
        anomalies = []
        
        # Group by data type
        by_type = defaultdict(list)
        for point in data_points:
            by_type[point.data_type].append(point)
        
        for data_type, points in by_type.items():
            if len(points) < 3:  # Need at least 3 points for anomaly detection
                continue
            
            values = [p.value for p in points if isinstance(p.value, (int, float))]
            if not values:
                continue
            
            # Statistical anomaly detection
            stat_anomalies = self._statistical_anomaly_detection(values, points)
            anomalies.extend(stat_anomalies)
            
            # Threshold anomaly detection
            threshold_anomalies = self._threshold_anomaly_detection(values, points, data_type)
            anomalies.extend(threshold_anomalies)
        
        return anomalies
    
    def _statistical_anomaly_detection(self, values: List[float], points: List[HealthDataPoint]) -> List[AnomalyDetection]:
        """Detect statistical anomalies using z-score"""
        anomalies = []
        
        if len(values) < 3:
            return anomalies
        
        mean = statistics.mean(values)
        std = statistics.stdev(values)
        
        if std == 0:
            return anomalies
        
        for i, value in enumerate(values):
            z_score = abs((value - mean) / std)
            
            if z_score > 2.5:  # Threshold for anomaly
                anomalies.append(AnomalyDetection(
                    data_point_id=str(i),
                    anomaly_type="statistical_outlier",
                    severity="high" if z_score > 3.0 else "medium",
                    confidence=min(z_score / 4.0, 1.0),
                    description=f"Value {value} is {z_score:.2f} standard deviations from mean",
                    suggested_action="Review data accuracy and consider medical consultation if persistent",
                    detected_at=datetime.utcnow()
                ))
        
        return anomalies
    
    def _threshold_anomaly_detection(self, values: List[float], points: List[HealthDataPoint], 
                                   data_type: DataType) -> List[AnomalyDetection]:
        """Detect anomalies based on medical thresholds"""
        anomalies = []
        
        rules = self.processing_rules.get(data_type.value, {})
        if not rules:
            return anomalies
        
        for i, value in enumerate(values):
            if data_type == DataType.HEART_RATE:
                if value > 100 or value < 60:
                    anomalies.append(AnomalyDetection(
                        data_point_id=str(i),
                        anomaly_type="medical_threshold",
                        severity="medium",
                        confidence=0.8,
                        description=f"Heart rate {value} outside normal range (60-100 bpm)",
                        suggested_action="Monitor and consult healthcare provider if persistent",
                        detected_at=datetime.utcnow()
                    ))
            
            elif data_type == DataType.BLOOD_PRESSURE:
                # This would need to handle dict values
                pass
        
        return anomalies
    
    def _trend_anomaly_detection(self, values: List[float], points: List[HealthDataPoint]) -> List[AnomalyDetection]:
        """Detect trend-based anomalies"""
        # Implementation for trend detection
        return []
    
    def _pattern_anomaly_detection(self, values: List[float], points: List[HealthDataPoint]) -> List[AnomalyDetection]:
        """Detect pattern-based anomalies"""
        # Implementation for pattern detection
        return []
    
    async def _calculate_trends(self, data_points: List[HealthDataPoint]) -> Dict[str, Any]:
        """Calculate trends in health data"""
        trends = {}
        
        # Group by data type
        by_type = defaultdict(list)
        for point in data_points:
            by_type[point.data_type].append(point)
        
        for data_type, points in by_type.items():
            if len(points) < 2:
                continue
            
            # Sort by timestamp
            sorted_points = sorted(points, key=lambda p: p.timestamp)
            values = [p.value for p in sorted_points if isinstance(p.value, (int, float))]
            
            if len(values) < 2:
                continue
            
            # Calculate linear trend
            x = list(range(len(values)))
            if len(x) > 1:
                slope, intercept = np.polyfit(x, values, 1)
                trends[data_type.value] = {
                    'slope': slope,
                    'intercept': intercept,
                    'trend_direction': 'increasing' if slope > 0 else 'decreasing' if slope < 0 else 'stable',
                    'trend_strength': abs(slope),
                    'data_points': len(values)
                }
        
        return trends
    
    async def _generate_insights(self, user_id: int, data_points: List[HealthDataPoint], 
                               trends: Dict[str, Any], anomalies: List[AnomalyDetection]) -> List[Dict[str, Any]]:
        """Generate insights from processed data"""
        insights = []
        
        # Trend insights
        for data_type, trend in trends.items():
            if trend['trend_strength'] > 0.1:  # Significant trend
                insights.append({
                    'type': 'trend',
                    'data_type': data_type,
                    'message': f"{data_type.replace('_', ' ').title()} is {trend['trend_direction']}",
                    'severity': 'medium',
                    'confidence': min(trend['trend_strength'], 1.0)
                })
        
        # Anomaly insights
        for anomaly in anomalies:
            insights.append({
                'type': 'anomaly',
                'data_type': 'health_data',
                'message': anomaly.description,
                'severity': anomaly.severity,
                'confidence': anomaly.confidence,
                'suggested_action': anomaly.suggested_action
            })
        
        return insights
    
    async def _store_data(self, user_id: int, data_points: List[HealthDataPoint]) -> Dict[str, Any]:
        """Store processed data in database"""
        errors = []
        warnings = []
        
        try:
            # This would typically store data points in a dedicated table
            # For now, we'll just log the storage operation
            logger.info(f"Storing {len(data_points)} processed data points for user {user_id}")
            
        except Exception as e:
            errors.append(f"Error storing data: {str(e)}")
        
        return {
            'errors': errors,
            'warnings': warnings
        }
    
    def _calculate_quality_score(self, data_points: List[HealthDataPoint], valid_count: int, total_count: int) -> float:
        """Calculate overall data quality score"""
        if total_count == 0:
            return 0.0
        
        # Base score from validation
        validation_score = valid_count / total_count
        
        # Additional quality factors
        completeness_score = self._calculate_completeness_score(data_points)
        consistency_score = self._calculate_consistency_score(data_points)
        accuracy_score = self._calculate_accuracy_score(data_points)
        
        # Weighted average
        quality_score = (
            validation_score * 0.4 +
            completeness_score * 0.2 +
            consistency_score * 0.2 +
            accuracy_score * 0.2
        )
        
        return min(quality_score, 1.0)
    
    def _calculate_completeness_score(self, data_points: List[HealthDataPoint]) -> float:
        """Calculate data completeness score"""
        if not data_points:
            return 0.0
        
        complete_points = sum(1 for p in data_points if p.value is not None and p.timestamp is not None)
        return complete_points / len(data_points)
    
    def _calculate_consistency_score(self, data_points: List[HealthDataPoint]) -> float:
        """Calculate data consistency score"""
        if len(data_points) < 2:
            return 1.0
        
        # Check for consistent data types and units
        data_types = set(p.data_type for p in data_points)
        units = set(p.unit for p in data_points if p.unit)
        
        consistency_score = 1.0
        
        # Penalize mixed data types (unless expected)
        if len(data_types) > 1:
            consistency_score *= 0.8
        
        # Penalize mixed units
        if len(units) > 1:
            consistency_score *= 0.9
        
        return consistency_score
    
    def _calculate_accuracy_score(self, data_points: List[HealthDataPoint]) -> float:
        """Calculate data accuracy score"""
        if not data_points:
            return 0.0
        
        # Use confidence scores if available
        confidence_scores = [p.confidence for p in data_points if p.confidence is not None]
        
        if confidence_scores:
            return statistics.mean(confidence_scores)
        else:
            # Default accuracy score
            return 0.8

# Global processor instance
health_data_processor = None

def get_health_data_processor(db_session: Session) -> HealthDataProcessor:
    """Get or create health data processor instance"""
    global health_data_processor
    if health_data_processor is None:
        health_data_processor = HealthDataProcessor(db_session)
    return health_data_processor 
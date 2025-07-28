"""
Machine Learning Data Preparation Service for HealthMate
Comprehensive ML data preparation including feature engineering, preprocessing, versioning, and performance tracking
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib
import pickle
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder
from sklearn.feature_selection import SelectKBest, f_classif, RFE
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from collections import defaultdict
import joblib
import os
from pathlib import Path

from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc, asc, text

from app.database import get_db
from app.models.enhanced_health_models import UserHealthProfile, HealthMetricsAggregation, ConversationHistory
from app.models.user import User
from app.services.enhanced.business_intelligence import (
    get_business_intelligence_service, AggregatedHealthMetrics
)
from app.exceptions.health_exceptions import MLDataPreparationError
from app.utils.encryption_utils import field_encryption
from app.utils.performance_monitoring import monitor_custom_performance

logger = logging.getLogger(__name__)

class FeatureType(str, Enum):
    """Types of features for ML models"""
    NUMERICAL = "numerical"
    CATEGORICAL = "categorical"
    TEMPORAL = "temporal"
    TEXT = "text"
    SEQUENCE = "sequence"
    AGGREGATED = "aggregated"

class PreprocessingType(str, Enum):
    """Types of data preprocessing"""
    SCALING = "scaling"
    ENCODING = "encoding"
    IMPUTATION = "imputation"
    FEATURE_SELECTION = "feature_selection"
    DIMENSIONALITY_REDUCTION = "dimensionality_reduction"
    NORMALIZATION = "normalization"

class ModelType(str, Enum):
    """Types of ML models"""
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    CLUSTERING = "clustering"
    TIME_SERIES = "time_series"
    RECOMMENDATION = "recommendation"
    ANOMALY_DETECTION = "anomaly_detection"

class DataVersion(str, Enum):
    """Data versioning types"""
    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"

@dataclass
class FeatureDefinition:
    """Definition of a feature for ML models"""
    name: str
    feature_type: FeatureType
    source_table: str
    source_column: str
    description: str
    preprocessing_steps: List[PreprocessingType] = field(default_factory=list)
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    is_required: bool = True
    default_value: Any = None
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class FeatureSet:
    """Collection of features for ML models"""
    feature_set_id: str
    name: str
    description: str
    features: List[FeatureDefinition]
    target_variable: str
    model_type: ModelType
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: str = "1.0.0"

@dataclass
class ProcessedDataset:
    """Processed dataset for ML training"""
    dataset_id: str
    feature_set_id: str
    data_hash: str
    features: List[str]
    target_variable: str
    X_train: np.ndarray
    X_test: np.ndarray
    y_train: np.ndarray
    y_test: np.ndarray
    preprocessing_pipeline: Any
    feature_names: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class ModelVersion:
    """ML model version information"""
    model_id: str
    version: str
    model_type: ModelType
    feature_set_id: str
    dataset_id: str
    model_path: str
    hyperparameters: Dict[str, Any]
    performance_metrics: Dict[str, float]
    training_metadata: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = False

@dataclass
class ModelPerformance:
    """Model performance tracking"""
    model_id: str
    version: str
    metric_name: str
    metric_value: float
    evaluation_date: datetime
    dataset_split: str  # train, test, validation
    environment: str  # development, staging, production
    metadata: Dict[str, Any] = field(default_factory=dict)

class FeatureEngineeringPipeline:
    """Feature engineering pipeline for ML models"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.bi_service = get_business_intelligence_service(db_session)
        self.config = self._load_feature_engineering_config()
    
    def _load_feature_engineering_config(self) -> Dict[str, Any]:
        """Load feature engineering configuration"""
        return {
            'feature_extraction': {
                'health_metrics': {
                    'aggregation_periods': ['daily', 'weekly', 'monthly'],
                    'statistical_features': ['mean', 'std', 'min', 'max', 'trend'],
                    'rolling_windows': [7, 14, 30]
                },
                'user_engagement': {
                    'time_windows': [1, 7, 30],  # days
                    'engagement_features': ['login_frequency', 'session_duration', 'feature_usage'],
                    'behavioral_features': ['page_visits', 'actions_performed', 'retention_score']
                },
                'temporal_features': {
                    'time_features': ['hour', 'day_of_week', 'month', 'season'],
                    'lag_features': [1, 3, 7, 14],  # days
                    'rolling_features': [7, 14, 30]  # days
                }
            },
            'preprocessing': {
                'scaling_methods': ['standard', 'minmax', 'robust'],
                'encoding_methods': ['onehot', 'label', 'target'],
                'imputation_methods': ['mean', 'median', 'mode', 'forward_fill'],
                'feature_selection': {
                    'methods': ['correlation', 'mutual_info', 'chi2', 'rfe'],
                    'max_features': 100
                }
            },
            'validation': {
                'data_quality_threshold': 0.8,
                'feature_correlation_threshold': 0.95,
                'missing_data_threshold': 0.3
            }
        }
    
    @monitor_custom_performance("extract_health_features")
    async def extract_health_features(self, user_id: int, start_date: datetime, 
                                    end_date: datetime) -> Dict[str, Any]:
        """Extract health-related features for ML models"""
        try:
            features = {}
            
            # Get aggregated health metrics
            for period in self.config['feature_extraction']['health_metrics']['aggregation_periods']:
                aggregated_metrics = await self.bi_service.aggregate_health_metrics(
                    user_id=user_id,
                    period=period,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if aggregated_metrics:
                    period_features = self._extract_health_metrics_features(aggregated_metrics)
                    features[f"health_{period}"] = period_features
            
            # Extract statistical features
            statistical_features = await self._extract_statistical_features(user_id, start_date, end_date)
            features['statistical'] = statistical_features
            
            # Extract trend features
            trend_features = await self._extract_trend_features(user_id, start_date, end_date)
            features['trends'] = trend_features
            
            # Extract rolling window features
            rolling_features = await self._extract_rolling_features(user_id, start_date, end_date)
            features['rolling'] = rolling_features
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting health features: {str(e)}")
            raise MLDataPreparationError(f"Failed to extract health features: {str(e)}")
    
    def _extract_health_metrics_features(self, metrics: AggregatedHealthMetrics) -> Dict[str, float]:
        """Extract features from health metrics"""
        features = {}
        
        # Blood pressure features
        if metrics.avg_blood_pressure_systolic:
            features['avg_systolic'] = metrics.avg_blood_pressure_systolic
        if metrics.avg_blood_pressure_diastolic:
            features['avg_diastolic'] = metrics.avg_blood_pressure_diastolic
        
        # Heart rate features
        if metrics.avg_heart_rate:
            features['avg_heart_rate'] = metrics.avg_heart_rate
        if metrics.resting_heart_rate:
            features['resting_heart_rate'] = metrics.resting_heart_rate
        
        # Weight features
        if metrics.avg_weight:
            features['avg_weight'] = metrics.avg_weight
        if metrics.weight_change:
            features['weight_change'] = metrics.weight_change
        
        # Activity features
        if metrics.total_steps:
            features['total_steps'] = metrics.total_steps
        if metrics.avg_steps_per_day:
            features['avg_steps_per_day'] = metrics.avg_steps_per_day
        if metrics.total_calories_burned:
            features['total_calories'] = metrics.total_calories_burned
        
        # Sleep features
        if metrics.avg_sleep_hours:
            features['avg_sleep_hours'] = metrics.avg_sleep_hours
        if metrics.sleep_quality_score:
            features['sleep_quality'] = metrics.sleep_quality_score
        
        # Medication features
        if metrics.medication_adherence_rate:
            features['medication_adherence'] = metrics.medication_adherence_rate
        if metrics.missed_doses:
            features['missed_doses'] = metrics.missed_doses
        
        # Health score features
        if metrics.overall_health_score:
            features['health_score'] = metrics.overall_health_score
        if metrics.health_score_trend:
            features['health_score_trend'] = metrics.health_score_trend
        
        return features
    
    async def _extract_statistical_features(self, user_id: int, start_date: datetime, 
                                          end_date: datetime) -> Dict[str, float]:
        """Extract statistical features from health data"""
        try:
            # Get health metrics aggregations for statistical analysis
            aggregations = self.db.query(HealthMetricsAggregation).filter(
                and_(
                    HealthMetricsAggregation.health_profile_id == user_id,
                    HealthMetricsAggregation.period_start >= start_date,
                    HealthMetricsAggregation.period_end <= end_date
                )
            ).all()
            
            if not aggregations:
                return {}
            
            features = {}
            
            # Calculate statistical features for each metric
            metrics_to_analyze = [
                'avg_blood_pressure_systolic', 'avg_blood_pressure_diastolic',
                'avg_heart_rate', 'avg_weight', 'total_steps', 'avg_sleep_hours'
            ]
            
            for metric in metrics_to_analyze:
                values = [getattr(agg, metric) for agg in aggregations if getattr(agg, metric) is not None]
                
                if len(values) >= 3:  # Need at least 3 values for statistics
                    features[f"{metric}_mean"] = np.mean(values)
                    features[f"{metric}_std"] = np.std(values)
                    features[f"{metric}_min"] = np.min(values)
                    features[f"{metric}_max"] = np.max(values)
                    features[f"{metric}_range"] = np.max(values) - np.min(values)
                    features[f"{metric}_cv"] = np.std(values) / np.mean(values) if np.mean(values) != 0 else 0
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting statistical features: {str(e)}")
            return {}
    
    async def _extract_trend_features(self, user_id: int, start_date: datetime, 
                                    end_date: datetime) -> Dict[str, float]:
        """Extract trend features from health data"""
        try:
            # Get health metrics aggregations for trend analysis
            aggregations = self.db.query(HealthMetricsAggregation).filter(
                and_(
                    HealthMetricsAggregation.health_profile_id == user_id,
                    HealthMetricsAggregation.period_start >= start_date,
                    HealthMetricsAggregation.period_end <= end_date
                )
            ).order_by(HealthMetricsAggregation.period_start).all()
            
            if len(aggregations) < 3:
                return {}
            
            features = {}
            
            # Calculate trend features for each metric
            metrics_to_analyze = [
                'avg_blood_pressure_systolic', 'avg_heart_rate', 'avg_weight',
                'total_steps', 'avg_sleep_hours', 'overall_health_score'
            ]
            
            for metric in metrics_to_analyze:
                values = [getattr(agg, metric) for agg in aggregations if getattr(agg, metric) is not None]
                timestamps = [agg.period_start for agg in aggregations if getattr(agg, metric) is not None]
                
                if len(values) >= 3:
                    # Calculate linear trend
                    time_numeric = [(ts - timestamps[0]).total_seconds() / 86400 for ts in timestamps]
                    slope, intercept, r_value, p_value, std_err = np.polyfit(time_numeric, values, 1)
                    
                    features[f"{metric}_trend_slope"] = slope
                    features[f"{metric}_trend_r_squared"] = r_value ** 2
                    features[f"{metric}_trend_p_value"] = p_value
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting trend features: {str(e)}")
            return {}
    
    async def _extract_rolling_features(self, user_id: int, start_date: datetime, 
                                      end_date: datetime) -> Dict[str, float]:
        """Extract rolling window features from health data"""
        try:
            # Get health metrics aggregations for rolling analysis
            aggregations = self.db.query(HealthMetricsAggregation).filter(
                and_(
                    HealthMetricsAggregation.health_profile_id == user_id,
                    HealthMetricsAggregation.period_start >= start_date,
                    HealthMetricsAggregation.period_end <= end_date
                )
            ).order_by(HealthMetricsAggregation.period_start).all()
            
            if len(aggregations) < 7:  # Need at least 7 days for rolling features
                return {}
            
            features = {}
            
            # Calculate rolling features for each metric
            metrics_to_analyze = [
                'avg_blood_pressure_systolic', 'avg_heart_rate', 'avg_weight',
                'total_steps', 'avg_sleep_hours'
            ]
            
            for metric in metrics_to_analyze:
                values = [getattr(agg, metric) for agg in aggregations if getattr(agg, metric) is not None]
                
                if len(values) >= 7:
                    # 7-day rolling average
                    rolling_7 = pd.Series(values).rolling(window=7, min_periods=1).mean()
                    features[f"{metric}_rolling_7_mean"] = rolling_7.iloc[-1] if not rolling_7.empty else 0
                    
                    # 14-day rolling average
                    if len(values) >= 14:
                        rolling_14 = pd.Series(values).rolling(window=14, min_periods=1).mean()
                        features[f"{metric}_rolling_14_mean"] = rolling_14.iloc[-1] if not rolling_14.empty else 0
                    
                    # 30-day rolling average
                    if len(values) >= 30:
                        rolling_30 = pd.Series(values).rolling(window=30, min_periods=1).mean()
                        features[f"{metric}_rolling_30_mean"] = rolling_30.iloc[-1] if not rolling_30.empty else 0
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting rolling features: {str(e)}")
            return {}
    
    @monitor_custom_performance("extract_engagement_features")
    async def extract_engagement_features(self, user_id: int, start_date: datetime, 
                                        end_date: datetime) -> Dict[str, Any]:
        """Extract user engagement features for ML models"""
        try:
            features = {}
            
            # Extract engagement features for different time windows
            for window in self.config['feature_extraction']['user_engagement']['time_windows']:
                window_start = end_date - timedelta(days=window)
                engagement_metrics = await self.bi_service.track_user_engagement(
                    user_id=user_id,
                    date=end_date
                )
                
                if engagement_metrics:
                    window_features = self._extract_engagement_metrics_features(engagement_metrics, window)
                    features[f"engagement_{window}d"] = window_features
            
            # Extract behavioral features
            behavioral_features = await self._extract_behavioral_features(user_id, start_date, end_date)
            features['behavioral'] = behavioral_features
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting engagement features: {str(e)}")
            raise MLDataPreparationError(f"Failed to extract engagement features: {str(e)}")
    
    def _extract_engagement_metrics_features(self, metrics: Any, window_days: int) -> Dict[str, float]:
        """Extract features from engagement metrics"""
        features = {}
        
        # Login features
        features['login_count'] = getattr(metrics, 'login_count', 0)
        features['session_duration_minutes'] = getattr(metrics, 'session_duration_minutes', 0)
        features['total_sessions'] = getattr(metrics, 'total_sessions', 0)
        features['avg_session_duration'] = getattr(metrics, 'session_duration_minutes', 0) / max(getattr(metrics, 'total_sessions', 1), 1)
        
        # Feature usage features
        features['health_data_points_added'] = getattr(metrics, 'health_data_points_added', 0)
        features['chat_messages_sent'] = getattr(metrics, 'chat_messages_sent', 0)
        features['notifications_received'] = getattr(metrics, 'notifications_received', 0)
        
        # Engagement scores
        features['engagement_score'] = getattr(metrics, 'engagement_score', 0)
        features['feature_adoption_rate'] = getattr(metrics, 'feature_adoption_rate', 0)
        features['retention_score'] = getattr(metrics, 'retention_score', 0)
        
        # Behavioral features
        features['time_spent_in_app_minutes'] = getattr(metrics, 'time_spent_in_app_minutes', 0)
        features['actions_performed'] = getattr(metrics, 'actions_performed', 0)
        
        # Normalize by time window
        for key in features:
            if isinstance(features[key], (int, float)) and features[key] > 0:
                features[key] = features[key] / window_days
        
        return features
    
    async def _extract_behavioral_features(self, user_id: int, start_date: datetime, 
                                         end_date: datetime) -> Dict[str, Any]:
        """Extract behavioral features from user activity"""
        try:
            features = {}
            
            # Get conversation history for behavioral analysis
            conversations = self.db.query(ConversationHistory).filter(
                and_(
                    ConversationHistory.user_id == user_id,
                    ConversationHistory.created_at >= start_date,
                    ConversationHistory.created_at <= end_date
                )
            ).all()
            
            if conversations:
                # Message frequency
                features['message_frequency'] = len(conversations) / (end_date - start_date).days
                
                # Message types
                message_types = [conv.message_type for conv in conversations]
                features['user_message_ratio'] = message_types.count('user_message') / len(message_types)
                features['ai_response_ratio'] = message_types.count('ai_response') / len(message_types)
                
                # Feedback analysis
                feedback_scores = [conv.user_rating for conv in conversations if conv.user_rating]
                if feedback_scores:
                    features['avg_feedback_score'] = np.mean(feedback_scores)
                    features['feedback_count'] = len(feedback_scores)
                
                # Urgency analysis
                urgency_levels = [conv.urgency_level for conv in conversations if conv.urgency_level]
                if urgency_levels:
                    features['high_urgency_ratio'] = urgency_levels.count('high') / len(urgency_levels)
                    features['emergency_ratio'] = urgency_levels.count('emergency') / len(urgency_levels)
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting behavioral features: {str(e)}")
            return {}
    
    @monitor_custom_performance("extract_temporal_features")
    async def extract_temporal_features(self, timestamp: datetime) -> Dict[str, Any]:
        """Extract temporal features from timestamp"""
        try:
            features = {}
            
            # Time-based features
            features['hour'] = timestamp.hour
            features['day_of_week'] = timestamp.weekday()
            features['day_of_month'] = timestamp.day
            features['month'] = timestamp.month
            features['quarter'] = (timestamp.month - 1) // 3 + 1
            features['year'] = timestamp.year
            
            # Seasonal features
            features['is_weekend'] = 1 if timestamp.weekday() >= 5 else 0
            features['is_morning'] = 1 if 6 <= timestamp.hour <= 12 else 0
            features['is_afternoon'] = 1 if 12 < timestamp.hour <= 18 else 0
            features['is_evening'] = 1 if 18 < timestamp.hour <= 22 else 0
            features['is_night'] = 1 if timestamp.hour > 22 or timestamp.hour < 6 else 0
            
            # Cyclical features (sin/cos encoding)
            features['hour_sin'] = np.sin(2 * np.pi * timestamp.hour / 24)
            features['hour_cos'] = np.cos(2 * np.pi * timestamp.hour / 24)
            features['day_of_week_sin'] = np.sin(2 * np.pi * timestamp.weekday() / 7)
            features['day_of_week_cos'] = np.cos(2 * np.pi * timestamp.weekday() / 7)
            features['month_sin'] = np.sin(2 * np.pi * timestamp.month / 12)
            features['month_cos'] = np.cos(2 * np.pi * timestamp.month / 12)
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting temporal features: {str(e)}")
            raise MLDataPreparationError(f"Failed to extract temporal features: {str(e)}")

class DataPreprocessor:
    """Data preprocessing for ML models"""
    
    def __init__(self):
        self.scalers = {}
        self.encoders = {}
        self.imputers = {}
        self.feature_selectors = {}
        self.pca_models = {}
    
    @monitor_custom_performance("preprocess_features")
    def preprocess_features(self, features: Dict[str, Any], preprocessing_config: Dict[str, Any]) -> Dict[str, Any]:
        """Preprocess features according to configuration"""
        try:
            processed_features = features.copy()
            
            # Handle missing values
            if 'imputation' in preprocessing_config:
                processed_features = self._handle_missing_values(processed_features, preprocessing_config['imputation'])
            
            # Scale numerical features
            if 'scaling' in preprocessing_config:
                processed_features = self._scale_features(processed_features, preprocessing_config['scaling'])
            
            # Encode categorical features
            if 'encoding' in preprocessing_config:
                processed_features = self._encode_features(processed_features, preprocessing_config['encoding'])
            
            # Feature selection
            if 'feature_selection' in preprocessing_config:
                processed_features = self._select_features(processed_features, preprocessing_config['feature_selection'])
            
            # Dimensionality reduction
            if 'dimensionality_reduction' in preprocessing_config:
                processed_features = self._reduce_dimensions(processed_features, preprocessing_config['dimensionality_reduction'])
            
            return processed_features
            
        except Exception as e:
            logger.error(f"Error preprocessing features: {str(e)}")
            raise MLDataPreparationError(f"Failed to preprocess features: {str(e)}")
    
    def _handle_missing_values(self, features: Dict[str, Any], imputation_config: Dict[str, Any]) -> Dict[str, Any]:
        """Handle missing values in features"""
        try:
            method = imputation_config.get('method', 'mean')
            
            # Separate numerical and categorical features
            numerical_features = {}
            categorical_features = {}
            
            for key, value in features.items():
                if isinstance(value, (int, float)) and not np.isnan(value) if isinstance(value, float) else True:
                    if isinstance(value, (int, float)):
                        numerical_features[key] = value
                    else:
                        categorical_features[key] = value
            
            # Impute numerical features
            if numerical_features:
                numerical_values = list(numerical_features.values())
                if method == 'mean':
                    imputed_value = np.mean([v for v in numerical_values if v is not None and not np.isnan(v)])
                elif method == 'median':
                    imputed_value = np.median([v for v in numerical_values if v is not None and not np.isnan(v)])
                else:
                    imputed_value = 0
                
                for key in numerical_features:
                    if numerical_features[key] is None or (isinstance(numerical_features[key], float) and np.isnan(numerical_features[key])):
                        features[key] = imputed_value
            
            # Impute categorical features
            if categorical_features:
                categorical_values = list(categorical_features.values())
                if method == 'mode':
                    # Find most common value
                    value_counts = defaultdict(int)
                    for value in categorical_values:
                        if value is not None:
                            value_counts[value] += 1
                    imputed_value = max(value_counts.items(), key=lambda x: x[1])[0] if value_counts else 'unknown'
                else:
                    imputed_value = 'unknown'
                
                for key in categorical_features:
                    if categorical_features[key] is None:
                        features[key] = imputed_value
            
            return features
            
        except Exception as e:
            logger.error(f"Error handling missing values: {str(e)}")
            return features
    
    def _scale_features(self, features: Dict[str, Any], scaling_config: Dict[str, Any]) -> Dict[str, Any]:
        """Scale numerical features"""
        try:
            method = scaling_config.get('method', 'standard')
            
            # Get numerical features
            numerical_features = {k: v for k, v in features.items() if isinstance(v, (int, float))}
            
            if not numerical_features:
                return features
            
            # Convert to numpy array
            feature_names = list(numerical_features.keys())
            feature_values = np.array(list(numerical_features.values())).reshape(1, -1)
            
            # Apply scaling
            if method == 'standard':
                scaler = StandardScaler()
            elif method == 'minmax':
                scaler = MinMaxScaler()
            else:
                scaler = StandardScaler()
            
            scaled_values = scaler.fit_transform(feature_values)
            
            # Store scaler for later use
            self.scalers[method] = scaler
            
            # Update features
            for i, name in enumerate(feature_names):
                features[name] = scaled_values[0, i]
            
            return features
            
        except Exception as e:
            logger.error(f"Error scaling features: {str(e)}")
            return features
    
    def _encode_features(self, features: Dict[str, Any], encoding_config: Dict[str, Any]) -> Dict[str, Any]:
        """Encode categorical features"""
        try:
            method = encoding_config.get('method', 'label')
            
            # Get categorical features
            categorical_features = {k: v for k, v in features.items() if not isinstance(v, (int, float))}
            
            if not categorical_features:
                return features
            
            for key, value in categorical_features.items():
                if method == 'label':
                    # Label encoding
                    if key not in self.encoders:
                        self.encoders[key] = LabelEncoder()
                        # Fit on current value
                        self.encoders[key].fit([value])
                    
                    features[key] = self.encoders[key].transform([value])[0]
                
                elif method == 'onehot':
                    # One-hot encoding (simplified - just create binary features)
                    encoded_key = f"{key}_{value}"
                    features[encoded_key] = 1
                    # Remove original feature
                    del features[key]
            
            return features
            
        except Exception as e:
            logger.error(f"Error encoding features: {str(e)}")
            return features
    
    def _select_features(self, features: Dict[str, Any], selection_config: Dict[str, Any]) -> Dict[str, Any]:
        """Select most important features"""
        try:
            method = selection_config.get('method', 'correlation')
            max_features = selection_config.get('max_features', 100)
            
            # Convert features to numpy array
            feature_names = list(features.keys())
            feature_values = np.array(list(features.values())).reshape(1, -1)
            
            if len(feature_names) <= max_features:
                return features
            
            # Apply feature selection
            if method == 'correlation':
                # Simple correlation-based selection (placeholder)
                selected_features = feature_names[:max_features]
            else:
                selected_features = feature_names[:max_features]
            
            # Keep only selected features
            return {k: v for k, v in features.items() if k in selected_features}
            
        except Exception as e:
            logger.error(f"Error selecting features: {str(e)}")
            return features
    
    def _reduce_dimensions(self, features: Dict[str, Any], reduction_config: Dict[str, Any]) -> Dict[str, Any]:
        """Reduce dimensionality of features"""
        try:
            method = reduction_config.get('method', 'pca')
            n_components = reduction_config.get('n_components', 10)
            
            # Convert features to numpy array
            feature_values = np.array(list(features.values())).reshape(1, -1)
            
            if method == 'pca':
                pca = PCA(n_components=min(n_components, feature_values.shape[1]))
                reduced_values = pca.fit_transform(feature_values)
                
                # Store PCA model
                self.pca_models['pca'] = pca
                
                # Update features with reduced dimensions
                reduced_features = {}
                for i in range(reduced_values.shape[1]):
                    reduced_features[f'pca_component_{i}'] = reduced_values[0, i]
                
                return reduced_features
            
            return features
            
        except Exception as e:
            logger.error(f"Error reducing dimensions: {str(e)}")
            return features

class DataVersioning:
    """Data versioning for ML models"""
    
    def __init__(self, base_path: str = "data/ml_versions"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    @monitor_custom_performance("version_dataset")
    def version_dataset(self, dataset: ProcessedDataset, version_type: DataVersion = DataVersion.PATCH) -> str:
        """Version a processed dataset"""
        try:
            # Generate version string
            version = self._generate_version(version_type)
            
            # Create version directory
            version_dir = self.base_path / f"dataset_{dataset.dataset_id}_v{version}"
            version_dir.mkdir(parents=True, exist_ok=True)
            
            # Save dataset
            dataset_path = version_dir / "dataset.pkl"
            with open(dataset_path, 'wb') as f:
                pickle.dump(dataset, f)
            
            # Save metadata
            metadata = {
                'dataset_id': dataset.dataset_id,
                'version': version,
                'feature_set_id': dataset.feature_set_id,
                'data_hash': dataset.data_hash,
                'features': dataset.features,
                'target_variable': dataset.target_variable,
                'feature_names': dataset.feature_names,
                'metadata': dataset.metadata,
                'created_at': dataset.created_at.isoformat()
            }
            
            metadata_path = version_dir / "metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Save preprocessing pipeline
            pipeline_path = version_dir / "preprocessing_pipeline.pkl"
            with open(pipeline_path, 'wb') as f:
                pickle.dump(dataset.preprocessing_pipeline, f)
            
            logger.info(f"Dataset versioned: {dataset.dataset_id} v{version}")
            return version
            
        except Exception as e:
            logger.error(f"Error versioning dataset: {str(e)}")
            raise MLDataPreparationError(f"Failed to version dataset: {str(e)}")
    
    def _generate_version(self, version_type: DataVersion) -> str:
        """Generate version string"""
        # In a real implementation, this would read from a version file
        # For now, return a simple timestamp-based version
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"1.0.{timestamp}"
    
    @monitor_custom_performance("load_dataset_version")
    def load_dataset_version(self, dataset_id: str, version: str) -> ProcessedDataset:
        """Load a specific version of a dataset"""
        try:
            version_dir = self.base_path / f"dataset_{dataset_id}_v{version}"
            
            if not version_dir.exists():
                raise MLDataPreparationError(f"Dataset version not found: {dataset_id} v{version}")
            
            dataset_path = version_dir / "dataset.pkl"
            with open(dataset_path, 'rb') as f:
                dataset = pickle.load(f)
            
            return dataset
            
        except Exception as e:
            logger.error(f"Error loading dataset version: {str(e)}")
            raise MLDataPreparationError(f"Failed to load dataset version: {str(e)}")
    
    @monitor_custom_performance("list_dataset_versions")
    def list_dataset_versions(self, dataset_id: str) -> List[str]:
        """List all versions of a dataset"""
        try:
            versions = []
            pattern = f"dataset_{dataset_id}_v*"
            
            for version_dir in self.base_path.glob(pattern):
                version = version_dir.name.split('_v')[1]
                versions.append(version)
            
            return sorted(versions)
            
        except Exception as e:
            logger.error(f"Error listing dataset versions: {str(e)}")
            return []

class ModelPerformanceTracker:
    """Model performance tracking"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    @monitor_custom_performance("track_model_performance")
    async def track_model_performance(self, model_performance: ModelPerformance) -> bool:
        """Track model performance metrics"""
        try:
            # In a real implementation, this would save to a database table
            # For now, we'll just log the performance
            logger.info(f"Model performance tracked: {model_performance.model_id} v{model_performance.version} - {model_performance.metric_name}: {model_performance.metric_value}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error tracking model performance: {str(e)}")
            return False
    
    @monitor_custom_performance("get_model_performance_history")
    async def get_model_performance_history(self, model_id: str, metric_name: Optional[str] = None) -> List[ModelPerformance]:
        """Get performance history for a model"""
        try:
            # In a real implementation, this would query a database
            # For now, return empty list
            return []
            
        except Exception as e:
            logger.error(f"Error getting model performance history: {str(e)}")
            return []

class MLDataPreparationService:
    """Main ML data preparation service"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.feature_engineering = FeatureEngineeringPipeline(db_session)
        self.preprocessor = DataPreprocessor()
        self.versioning = DataVersioning()
        self.performance_tracker = ModelPerformanceTracker(db_session)
    
    @monitor_custom_performance("prepare_ml_dataset")
    async def prepare_ml_dataset(self, user_ids: List[int], feature_set: FeatureSet, 
                               target_variable: str, test_size: float = 0.2,
                               random_state: int = 42) -> ProcessedDataset:
        """Prepare a complete ML dataset"""
        try:
            # Extract features for all users
            all_features = []
            all_targets = []
            
            for user_id in user_ids:
                try:
                    # Extract health features
                    health_features = await self.feature_engineering.extract_health_features(
                        user_id=user_id,
                        start_date=datetime.now() - timedelta(days=90),
                        end_date=datetime.now()
                    )
                    
                    # Extract engagement features
                    engagement_features = await self.feature_engineering.extract_engagement_features(
                        user_id=user_id,
                        start_date=datetime.now() - timedelta(days=30),
                        end_date=datetime.now()
                    )
                    
                    # Extract temporal features
                    temporal_features = await self.feature_engineering.extract_temporal_features(
                        timestamp=datetime.now()
                    )
                    
                    # Combine all features
                    combined_features = {}
                    combined_features.update(health_features.get('health_daily', {}))
                    combined_features.update(engagement_features.get('engagement_7d', {}))
                    combined_features.update(temporal_features)
                    
                    # Get target variable (placeholder - in real implementation, this would come from actual data)
                    target_value = combined_features.get(target_variable, 0)
                    
                    all_features.append(combined_features)
                    all_targets.append(target_value)
                    
                except Exception as e:
                    logger.warning(f"Failed to extract features for user {user_id}: {e}")
                    continue
            
            if not all_features:
                raise MLDataPreparationError("No features extracted for any users")
            
            # Convert to DataFrame for easier processing
            df = pd.DataFrame(all_features)
            
            # Handle missing values
            df = df.fillna(0)  # Simple imputation
            
            # Split into train/test
            from sklearn.model_selection import train_test_split
            
            X = df.drop(columns=[target_variable]) if target_variable in df.columns else df
            y = df[target_variable] if target_variable in df.columns else pd.Series(all_targets)
            
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=random_state
            )
            
            # Create dataset
            dataset_id = f"dataset_{len(user_ids)}_users_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            data_hash = hashlib.md5(str(all_features).encode()).hexdigest()
            
            dataset = ProcessedDataset(
                dataset_id=dataset_id,
                feature_set_id=feature_set.feature_set_id,
                data_hash=data_hash,
                features=list(X.columns),
                target_variable=target_variable,
                X_train=X_train.values,
                X_test=X_test.values,
                y_train=y_train.values,
                y_test=y_test.values,
                preprocessing_pipeline=self.preprocessor,
                feature_names=list(X.columns),
                metadata={
                    'user_count': len(user_ids),
                    'feature_count': len(X.columns),
                    'test_size': test_size,
                    'random_state': random_state
                }
            )
            
            # Version the dataset
            version = self.versioning.version_dataset(dataset)
            logger.info(f"ML dataset prepared: {dataset_id} v{version}")
            
            return dataset
            
        except Exception as e:
            logger.error(f"Error preparing ML dataset: {str(e)}")
            raise MLDataPreparationError(f"Failed to prepare ML dataset: {str(e)}")
    
    @monitor_custom_performance("create_feature_set")
    def create_feature_set(self, name: str, description: str, features: List[FeatureDefinition],
                          target_variable: str, model_type: ModelType) -> FeatureSet:
        """Create a new feature set"""
        try:
            feature_set_id = f"feature_set_{name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            feature_set = FeatureSet(
                feature_set_id=feature_set_id,
                name=name,
                description=description,
                features=features,
                target_variable=target_variable,
                model_type=model_type
            )
            
            logger.info(f"Feature set created: {feature_set_id}")
            return feature_set
            
        except Exception as e:
            logger.error(f"Error creating feature set: {str(e)}")
            raise MLDataPreparationError(f"Failed to create feature set: {str(e)}")

# Factory functions
def get_ml_data_preparation_service(db_session: Session) -> MLDataPreparationService:
    """Get ML data preparation service instance"""
    return MLDataPreparationService(db_session)

# Global instance for background tasks
ml_data_preparation_service = None

def get_global_ml_data_preparation_service() -> MLDataPreparationService:
    """Get global ML data preparation service instance"""
    global ml_data_preparation_service
    if ml_data_preparation_service is None:
        db = next(get_db())
        ml_data_preparation_service = MLDataPreparationService(db)
    return ml_data_preparation_service 
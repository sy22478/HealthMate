"""
Tests for ML Data Preparation System
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session
import numpy as np
import pandas as pd

from app.services.enhanced.ml_data_preparation import (
    MLDataPreparationService, FeatureEngineeringPipeline, DataPreprocessor, DataVersioning, ModelPerformanceTracker,
    FeatureType, PreprocessingType, ModelType, DataVersion, FeatureDefinition, FeatureSet,
    ProcessedDataset, ModelVersion, ModelPerformance
)
from app.exceptions.health_exceptions import MLDataPreparationError
from app.models.enhanced_health_models import HealthMetricsAggregation, UserHealthProfile
from app.models.user import User

class TestMLDataPreparationService:
    @pytest.fixture
    def mock_db_session(self):
        return Mock(spec=Session)
    
    @pytest.fixture
    def ml_service(self, mock_db_session):
        return MLDataPreparationService(mock_db_session)
    
    @pytest.fixture
    def sample_feature_definition(self):
        return FeatureDefinition(
            name="avg_heart_rate",
            feature_type=FeatureType.NUMERICAL,
            source_table="health_metrics_aggregation",
            source_column="avg_heart_rate",
            description="Average heart rate"
        )
    
    @pytest.fixture
    def sample_feature_set(self, sample_feature_definition):
        return FeatureSet(
            feature_set_id="test_feature_set",
            name="Test Feature Set",
            description="Test feature set for ML models",
            features=[sample_feature_definition],
            target_variable="health_score",
            model_type=ModelType.REGRESSION
        )
    
    @pytest.fixture
    def sample_health_metrics_aggregation(self):
        return HealthMetricsAggregation(
            id=1, health_profile_id=1, aggregation_period="daily",
            period_start=datetime(2024, 1, 1), period_end=datetime(2024, 1, 2),
            avg_blood_pressure_systolic=120.0, avg_heart_rate=72.0, total_steps=8000,
            medication_adherence_rate=95.0, overall_health_score=82.0
        )
    
    def test_ml_service_initialization(self, ml_service):
        """Test ML data preparation service initialization"""
        assert ml_service is not None
        assert hasattr(ml_service, 'feature_engineering')
        assert hasattr(ml_service, 'preprocessor')
        assert hasattr(ml_service, 'versioning')
        assert hasattr(ml_service, 'performance_tracker')
    
    def test_create_feature_set(self, ml_service):
        """Test feature set creation"""
        features = [
            FeatureDefinition(
                name="test_feature",
                feature_type=FeatureType.NUMERICAL,
                source_table="test_table",
                source_column="test_column",
                description="Test feature"
            )
        ]
        
        feature_set = ml_service.create_feature_set(
            name="Test Feature Set",
            description="Test description",
            features=features,
            target_variable="target",
            model_type=ModelType.REGRESSION
        )
        
        assert feature_set.name == "Test Feature Set"
        assert feature_set.target_variable == "target"
        assert feature_set.model_type == ModelType.REGRESSION
        assert len(feature_set.features) == 1
        assert feature_set.feature_set_id.startswith("feature_set_test_feature_set")

class TestFeatureEngineeringPipeline:
    @pytest.fixture
    def mock_db_session(self):
        return Mock(spec=Session)
    
    @pytest.fixture
    def feature_pipeline(self, mock_db_session):
        return FeatureEngineeringPipeline(mock_db_session)
    
    @pytest.fixture
    def sample_health_metrics_aggregation(self):
        return HealthMetricsAggregation(
            id=1, health_profile_id=1, aggregation_period="daily",
            period_start=datetime(2024, 1, 1), period_end=datetime(2024, 1, 2),
            avg_blood_pressure_systolic=120.0, avg_heart_rate=72.0, total_steps=8000,
            medication_adherence_rate=95.0, overall_health_score=82.0
        )
    
    def test_feature_pipeline_initialization(self, feature_pipeline):
        """Test feature engineering pipeline initialization"""
        assert feature_pipeline is not None
        assert hasattr(feature_pipeline, 'config')
        assert 'feature_extraction' in feature_pipeline.config
    
    @pytest.mark.asyncio
    async def test_extract_health_features(self, feature_pipeline, sample_health_metrics_aggregation):
        """Test health feature extraction"""
        with patch.object(feature_pipeline.bi_service, 'aggregate_health_metrics') as mock_aggregate:
            mock_aggregate.return_value = sample_health_metrics_aggregation
            
            features = await feature_pipeline.extract_health_features(
                user_id=1,
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 2)
            )
            
            assert 'health_daily' in features
            assert 'statistical' in features
            assert 'trends' in features
            assert 'rolling' in features
    
    def test_extract_health_metrics_features(self, feature_pipeline, sample_health_metrics_aggregation):
        """Test health metrics feature extraction"""
        features = feature_pipeline._extract_health_metrics_features(sample_health_metrics_aggregation)
        
        assert 'avg_systolic' in features
        assert 'avg_heart_rate' in features
        assert 'medication_adherence' in features
        assert 'health_score' in features
        assert features['avg_systolic'] == 120.0
        assert features['avg_heart_rate'] == 72.0
    
    @pytest.mark.asyncio
    async def test_extract_statistical_features(self, feature_pipeline):
        """Test statistical feature extraction"""
        # Mock database query
        mock_aggregations = [
            HealthMetricsAggregation(
                id=1, health_profile_id=1, avg_heart_rate=70.0, avg_blood_pressure_systolic=120.0
            ),
            HealthMetricsAggregation(
                id=2, health_profile_id=1, avg_heart_rate=75.0, avg_blood_pressure_systolic=125.0
            ),
            HealthMetricsAggregation(
                id=3, health_profile_id=1, avg_heart_rate=80.0, avg_blood_pressure_systolic=130.0
            )
        ]
        
        feature_pipeline.db.query.return_value.filter.return_value.all.return_value = mock_aggregations
        
        features = await feature_pipeline._extract_statistical_features(
            user_id=1,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 3)
        )
        
        assert 'avg_heart_rate_mean' in features
        assert 'avg_heart_rate_std' in features
        assert features['avg_heart_rate_mean'] == 75.0
    
    @pytest.mark.asyncio
    async def test_extract_trend_features(self, feature_pipeline):
        """Test trend feature extraction"""
        # Mock database query with time series data
        mock_aggregations = [
            HealthMetricsAggregation(
                id=1, health_profile_id=1, period_start=datetime(2024, 1, 1),
                avg_heart_rate=70.0, overall_health_score=80.0
            ),
            HealthMetricsAggregation(
                id=2, health_profile_id=1, period_start=datetime(2024, 1, 2),
                avg_heart_rate=75.0, overall_health_score=82.0
            ),
            HealthMetricsAggregation(
                id=3, health_profile_id=1, period_start=datetime(2024, 1, 3),
                avg_heart_rate=80.0, overall_health_score=85.0
            )
        ]
        
        feature_pipeline.db.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_aggregations
        
        features = await feature_pipeline._extract_trend_features(
            user_id=1,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 3)
        )
        
        assert 'avg_heart_rate_trend_slope' in features
        assert 'overall_health_score_trend_slope' in features
    
    @pytest.mark.asyncio
    async def test_extract_engagement_features(self, feature_pipeline):
        """Test engagement feature extraction"""
        with patch.object(feature_pipeline.bi_service, 'track_user_engagement') as mock_track:
            mock_track.return_value = Mock(
                login_count=5,
                session_duration_minutes=45,
                chat_messages_sent=10,
                engagement_score=0.8
            )
            
            features = await feature_pipeline.extract_engagement_features(
                user_id=1,
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 2)
            )
            
            assert 'engagement_7d' in features
            assert 'behavioral' in features
    
    def test_extract_engagement_metrics_features(self, feature_pipeline):
        """Test engagement metrics feature extraction"""
        mock_metrics = Mock(
            login_count=5,
            session_duration_minutes=45,
            chat_messages_sent=10,
            engagement_score=0.8
        )
        
        features = feature_pipeline._extract_engagement_metrics_features(mock_metrics, 7)
        
        assert 'login_count' in features
        assert 'session_duration_minutes' in features
        assert 'engagement_score' in features
    
    @pytest.mark.asyncio
    async def test_extract_temporal_features(self, feature_pipeline):
        """Test temporal feature extraction"""
        timestamp = datetime(2024, 1, 15, 14, 30)  # Monday, 2:30 PM
        
        features = await feature_pipeline.extract_temporal_features(timestamp)
        
        assert 'hour' in features
        assert 'day_of_week' in features
        assert 'month' in features
        assert 'is_weekend' in features
        assert 'is_afternoon' in features
        assert 'hour_sin' in features
        assert 'hour_cos' in features
        assert features['hour'] == 14
        assert features['day_of_week'] == 0  # Monday
        assert features['is_weekend'] == 0
        assert features['is_afternoon'] == 1

class TestDataPreprocessor:
    @pytest.fixture
    def preprocessor(self):
        return DataPreprocessor()
    
    def test_preprocessor_initialization(self, preprocessor):
        """Test data preprocessor initialization"""
        assert preprocessor is not None
        assert hasattr(preprocessor, 'scalers')
        assert hasattr(preprocessor, 'encoders')
        assert hasattr(preprocessor, 'imputers')
    
    def test_preprocess_features(self, preprocessor):
        """Test feature preprocessing"""
        features = {
            'avg_heart_rate': 75.0,
            'avg_blood_pressure_systolic': 120.0,
            'medication_adherence': 0.95,
            'login_count': 5
        }
        
        preprocessing_config = {
            'imputation': {'method': 'mean'},
            'scaling': {'method': 'standard'}
        }
        
        processed_features = preprocessor.preprocess_features(features, preprocessing_config)
        
        assert len(processed_features) == len(features)
        assert all(key in processed_features for key in features.keys())
    
    def test_handle_missing_values(self, preprocessor):
        """Test missing value handling"""
        features = {
            'avg_heart_rate': 75.0,
            'avg_blood_pressure_systolic': None,
            'medication_adherence': 0.95,
            'login_count': 5
        }
        
        imputation_config = {'method': 'mean'}
        
        processed_features = preprocessor._handle_missing_values(features, imputation_config)
        
        assert processed_features['avg_blood_pressure_systolic'] is not None
        assert processed_features['avg_blood_pressure_systolic'] > 0
    
    def test_scale_features(self, preprocessor):
        """Test feature scaling"""
        features = {
            'avg_heart_rate': 75.0,
            'avg_blood_pressure_systolic': 120.0,
            'medication_adherence': 0.95
        }
        
        scaling_config = {'method': 'standard'}
        
        processed_features = preprocessor._scale_features(features, scaling_config)
        
        assert len(processed_features) == len(features)
        assert 'standard' in preprocessor.scalers
    
    def test_encode_features(self, preprocessor):
        """Test feature encoding"""
        features = {
            'avg_heart_rate': 75.0,
            'user_type': 'premium',
            'medication_adherence': 0.95
        }
        
        encoding_config = {'method': 'label'}
        
        processed_features = preprocessor._encode_features(features, encoding_config)
        
        assert 'user_type' in preprocessor.encoders
        assert isinstance(processed_features['user_type'], int)
    
    def test_select_features(self, preprocessor):
        """Test feature selection"""
        features = {
            'feature_1': 1.0,
            'feature_2': 2.0,
            'feature_3': 3.0,
            'feature_4': 4.0,
            'feature_5': 5.0
        }
        
        selection_config = {'method': 'correlation', 'max_features': 3}
        
        processed_features = preprocessor._select_features(features, selection_config)
        
        assert len(processed_features) <= 3
    
    def test_reduce_dimensions(self, preprocessor):
        """Test dimensionality reduction"""
        features = {
            'feature_1': 1.0,
            'feature_2': 2.0,
            'feature_3': 3.0,
            'feature_4': 4.0,
            'feature_5': 5.0
        }
        
        reduction_config = {'method': 'pca', 'n_components': 3}
        
        processed_features = preprocessor._reduce_dimensions(features, reduction_config)
        
        assert len(processed_features) == 3
        assert all(key.startswith('pca_component_') for key in processed_features.keys())

class TestDataVersioning:
    @pytest.fixture
    def versioning(self, tmp_path):
        return DataVersioning(str(tmp_path / "ml_versions"))
    
    @pytest.fixture
    def sample_dataset(self):
        return ProcessedDataset(
            dataset_id="test_dataset",
            feature_set_id="test_feature_set",
            data_hash="test_hash",
            features=["feature_1", "feature_2"],
            target_variable="target",
            X_train=np.array([[1, 2], [3, 4]]),
            X_test=np.array([[5, 6]]),
            y_train=np.array([1, 0]),
            y_test=np.array([1]),
            preprocessing_pipeline=Mock(),
            feature_names=["feature_1", "feature_2"]
        )
    
    def test_versioning_initialization(self, versioning):
        """Test data versioning initialization"""
        assert versioning is not None
        assert hasattr(versioning, 'base_path')
    
    def test_version_dataset(self, versioning, sample_dataset):
        """Test dataset versioning"""
        version = versioning.version_dataset(sample_dataset)
        
        assert version is not None
        assert isinstance(version, str)
        assert version.startswith("1.0.")
    
    def test_generate_version(self, versioning):
        """Test version generation"""
        version = versioning._generate_version(DataVersion.PATCH)
        
        assert version is not None
        assert isinstance(version, str)
        assert version.startswith("1.0.")
    
    def test_list_dataset_versions(self, versioning, sample_dataset):
        """Test listing dataset versions"""
        # First create a version
        version = versioning.version_dataset(sample_dataset)
        
        # Then list versions
        versions = versioning.list_dataset_versions("test_dataset")
        
        assert len(versions) >= 1
        assert version in versions
    
    def test_load_dataset_version(self, versioning, sample_dataset):
        """Test loading dataset version"""
        # First create a version
        version = versioning.version_dataset(sample_dataset)
        
        # Then load it
        loaded_dataset = versioning.load_dataset_version("test_dataset", version)
        
        assert loaded_dataset.dataset_id == sample_dataset.dataset_id
        assert loaded_dataset.feature_set_id == sample_dataset.feature_set_id

class TestModelPerformanceTracker:
    @pytest.fixture
    def mock_db_session(self):
        return Mock(spec=Session)
    
    @pytest.fixture
    def performance_tracker(self, mock_db_session):
        return ModelPerformanceTracker(mock_db_session)
    
    @pytest.fixture
    def sample_model_performance(self):
        return ModelPerformance(
            model_id="test_model",
            version="1.0.0",
            metric_name="accuracy",
            metric_value=0.85,
            evaluation_date=datetime.now(),
            dataset_split="test",
            environment="development"
        )
    
    def test_performance_tracker_initialization(self, performance_tracker):
        """Test model performance tracker initialization"""
        assert performance_tracker is not None
        assert hasattr(performance_tracker, 'db')
    
    @pytest.mark.asyncio
    async def test_track_model_performance(self, performance_tracker, sample_model_performance):
        """Test model performance tracking"""
        success = await performance_tracker.track_model_performance(sample_model_performance)
        
        assert success is True
    
    @pytest.mark.asyncio
    async def test_get_model_performance_history(self, performance_tracker):
        """Test getting model performance history"""
        history = await performance_tracker.get_model_performance_history("test_model")
        
        assert isinstance(history, list)

class TestEnums:
    def test_feature_type_enum(self):
        """Test FeatureType enum"""
        assert FeatureType.NUMERICAL == "numerical"
        assert FeatureType.CATEGORICAL == "categorical"
        assert FeatureType.TEMPORAL == "temporal"
        assert FeatureType.TEXT == "text"
        assert FeatureType.SEQUENCE == "sequence"
        assert FeatureType.AGGREGATED == "aggregated"
    
    def test_preprocessing_type_enum(self):
        """Test PreprocessingType enum"""
        assert PreprocessingType.SCALING == "scaling"
        assert PreprocessingType.ENCODING == "encoding"
        assert PreprocessingType.IMPUTATION == "imputation"
        assert PreprocessingType.FEATURE_SELECTION == "feature_selection"
        assert PreprocessingType.DIMENSIONALITY_REDUCTION == "dimensionality_reduction"
        assert PreprocessingType.NORMALIZATION == "normalization"
    
    def test_model_type_enum(self):
        """Test ModelType enum"""
        assert ModelType.CLASSIFICATION == "classification"
        assert ModelType.REGRESSION == "regression"
        assert ModelType.CLUSTERING == "clustering"
        assert ModelType.TIME_SERIES == "time_series"
        assert ModelType.RECOMMENDATION == "recommendation"
        assert ModelType.ANOMALY_DETECTION == "anomaly_detection"
    
    def test_data_version_enum(self):
        """Test DataVersion enum"""
        assert DataVersion.MAJOR == "major"
        assert DataVersion.MINOR == "minor"
        assert DataVersion.PATCH == "patch"

class TestDataClasses:
    def test_feature_definition(self):
        """Test FeatureDefinition dataclass"""
        feature_def = FeatureDefinition(
            name="test_feature",
            feature_type=FeatureType.NUMERICAL,
            source_table="test_table",
            source_column="test_column",
            description="Test feature"
        )
        
        assert feature_def.name == "test_feature"
        assert feature_def.feature_type == FeatureType.NUMERICAL
        assert feature_def.source_table == "test_table"
        assert feature_def.source_column == "test_column"
        assert feature_def.description == "Test feature"
        assert feature_def.is_required is True
    
    def test_feature_set(self):
        """Test FeatureSet dataclass"""
        features = [
            FeatureDefinition(
                name="test_feature",
                feature_type=FeatureType.NUMERICAL,
                source_table="test_table",
                source_column="test_column",
                description="Test feature"
            )
        ]
        
        feature_set = FeatureSet(
            feature_set_id="test_set",
            name="Test Set",
            description="Test feature set",
            features=features,
            target_variable="target",
            model_type=ModelType.REGRESSION
        )
        
        assert feature_set.feature_set_id == "test_set"
        assert feature_set.name == "Test Set"
        assert feature_set.target_variable == "target"
        assert feature_set.model_type == ModelType.REGRESSION
        assert len(feature_set.features) == 1
    
    def test_processed_dataset(self):
        """Test ProcessedDataset dataclass"""
        dataset = ProcessedDataset(
            dataset_id="test_dataset",
            feature_set_id="test_set",
            data_hash="test_hash",
            features=["feature_1", "feature_2"],
            target_variable="target",
            X_train=np.array([[1, 2], [3, 4]]),
            X_test=np.array([[5, 6]]),
            y_train=np.array([1, 0]),
            y_test=np.array([1]),
            preprocessing_pipeline=Mock(),
            feature_names=["feature_1", "feature_2"]
        )
        
        assert dataset.dataset_id == "test_dataset"
        assert dataset.feature_set_id == "test_set"
        assert dataset.data_hash == "test_hash"
        assert len(dataset.features) == 2
        assert dataset.target_variable == "target"
        assert dataset.X_train.shape == (2, 2)
        assert dataset.X_test.shape == (1, 2)
    
    def test_model_version(self):
        """Test ModelVersion dataclass"""
        model_version = ModelVersion(
            model_id="test_model",
            version="1.0.0",
            model_type=ModelType.REGRESSION,
            feature_set_id="test_set",
            dataset_id="test_dataset",
            model_path="/path/to/model",
            hyperparameters={"learning_rate": 0.01},
            performance_metrics={"accuracy": 0.85},
            training_metadata={"epochs": 100}
        )
        
        assert model_version.model_id == "test_model"
        assert model_version.version == "1.0.0"
        assert model_version.model_type == ModelType.REGRESSION
        assert model_version.feature_set_id == "test_set"
        assert model_version.dataset_id == "test_dataset"
        assert model_version.model_path == "/path/to/model"
        assert model_version.hyperparameters["learning_rate"] == 0.01
        assert model_version.performance_metrics["accuracy"] == 0.85
    
    def test_model_performance(self):
        """Test ModelPerformance dataclass"""
        performance = ModelPerformance(
            model_id="test_model",
            version="1.0.0",
            metric_name="accuracy",
            metric_value=0.85,
            evaluation_date=datetime.now(),
            dataset_split="test",
            environment="development"
        )
        
        assert performance.model_id == "test_model"
        assert performance.version == "1.0.0"
        assert performance.metric_name == "accuracy"
        assert performance.metric_value == 0.85
        assert performance.dataset_split == "test"
        assert performance.environment == "development"

class TestFactoryFunctions:
    def test_get_ml_data_preparation_service(self, mock_db_session):
        """Test factory function for ML data preparation service"""
        service = get_ml_data_preparation_service(mock_db_session)
        
        assert isinstance(service, MLDataPreparationService)
        assert service.db == mock_db_session
    
    def test_get_global_ml_data_preparation_service(self):
        """Test global factory function for ML data preparation service"""
        # This would require a real database session in a real test environment
        # For now, we'll just test that the function exists and can be called
        assert callable(get_global_ml_data_preparation_service)

class TestErrorHandling:
    def test_ml_data_preparation_error(self):
        """Test MLDataPreparationError exception"""
        error = MLDataPreparationError("Test error message", "TEST_ERROR", {"detail": "test"})
        
        assert error.message == "Test error message"
        assert error.error_code == "TEST_ERROR"
        assert error.error_type == "MLDataPreparationError"
        assert error.details["detail"] == "test"
    
    @pytest.mark.asyncio
    async def test_feature_extraction_error_handling(self, mock_db_session):
        """Test error handling in feature extraction"""
        feature_pipeline = FeatureEngineeringPipeline(mock_db_session)
        
        with patch.object(feature_pipeline.bi_service, 'aggregate_health_metrics') as mock_aggregate:
            mock_aggregate.side_effect = Exception("Database error")
            
            with pytest.raises(MLDataPreparationError):
                await feature_pipeline.extract_health_features(
                    user_id=1,
                    start_date=datetime(2024, 1, 1),
                    end_date=datetime(2024, 1, 2)
                )
    
    def test_preprocessing_error_handling(self):
        """Test error handling in data preprocessing"""
        preprocessor = DataPreprocessor()
        
        # Test with invalid preprocessing config
        features = {'test': 1.0}
        invalid_config = {'invalid_step': {}}
        
        # Should not raise an exception, but handle gracefully
        processed_features = preprocessor.preprocess_features(features, invalid_config)
        assert processed_features == features 
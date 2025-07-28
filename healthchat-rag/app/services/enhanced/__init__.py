"""
Enhanced Services Package
Advanced health data processing and analytics services
"""

from .data_integration import (
    DataIntegrationService, DataProviderFactory, DataSourceConfig, 
    HealthDataPoint, DataType, DataSourceType, BaseDataProvider,
    FitbitDataProvider, AppleHealthDataProvider, data_integration_service
)

from .health_data_processing import (
    HealthDataProcessor, ProcessingResult, ProcessingStage, 
    DataQualityLevel, AnomalyDetection, get_health_data_processor
)

from .health_analytics import (
    HealthAnalyticsEngine, AnalyticsType, TrendDirection, HealthScoreCategory,
    TrendAnalysis, PatternRecognition, HealthScore, ComparativeAnalysis,
    RiskAssessment, get_health_analytics_engine
)

from .vector_store_optimized import (
    EnhancedVectorStore, SearchType, DocumentType, CredibilityLevel,
    SearchQuery, SearchResult, get_enhanced_vector_store
)

from .ai_processing_pipeline import (
    AIProcessingPipeline, ProcessingType, ImageType, AnalysisConfidence,
    ProcessingResult, ImageAnalysisResult, ConversationMemory, get_ai_processing_pipeline
)

from .user_modeling import (
    UserModelingBackend, InteractionType, ContentCategory, PreferenceStrength,
    UserInteraction, UserPreferenceProfile, BehaviorPattern, PersonalizationRecommendation,
    get_user_modeling_backend
)

from .predictive_analytics import (
    PredictiveAnalyticsBackend, RiskLevel, PredictionType, TrendDirection,
    RiskAssessment, HealthTrend, EarlyWarning, PreventiveRecommendation,
    get_predictive_analytics_backend
)

from .business_intelligence import (
    BusinessIntelligenceService, MetricType, AggregationPeriod, ReportType,
    AggregatedHealthMetrics, UserEngagementMetrics, SystemPerformanceMetrics,
    BusinessIntelligenceReport, get_business_intelligence_service, get_global_bi_service
)

from .ml_data_preparation import (
    MLDataPreparationService, FeatureEngineeringPipeline, DataPreprocessor, DataVersioning, ModelPerformanceTracker,
    FeatureType, PreprocessingType, ModelType, DataVersion, FeatureDefinition, FeatureSet,
    ProcessedDataset, ModelVersion, ModelPerformance,
    get_ml_data_preparation_service, get_global_ml_data_preparation_service
)

__all__ = [
    # Data Integration
    'DataIntegrationService',
    'DataProviderFactory', 
    'DataSourceConfig',
    'HealthDataPoint',
    'DataType',
    'DataSourceType',
    'BaseDataProvider',
    'FitbitDataProvider',
    'AppleHealthDataProvider',
    'data_integration_service',
    
    # Health Data Processing
    'HealthDataProcessor',
    'ProcessingResult',
    'ProcessingStage',
    'DataQualityLevel',
    'AnomalyDetection',
    'get_health_data_processor',
    
    # Health Analytics
    'HealthAnalyticsEngine',
    'AnalyticsType',
    'TrendDirection',
    'HealthScoreCategory',
    'TrendAnalysis',
    'PatternRecognition',
    'HealthScore',
    'ComparativeAnalysis',
    'RiskAssessment',
    'get_health_analytics_engine',
    
    # Vector Store Optimization
    'EnhancedVectorStore',
    'SearchType',
    'DocumentType',
    'CredibilityLevel',
    'SearchQuery',
    'SearchResult',
    'get_enhanced_vector_store',
    
    # AI Processing Pipeline
    'AIProcessingPipeline',
    'ProcessingType',
    'ImageType',
    'AnalysisConfidence',
    'ProcessingResult',
    'ImageAnalysisResult',
    'ConversationMemory',
    'get_ai_processing_pipeline',
    
    # User Modeling Backend
    'UserModelingBackend',
    'InteractionType',
    'ContentCategory',
    'PreferenceStrength',
    'UserInteraction',
    'UserPreferenceProfile',
    'BehaviorPattern',
    'PersonalizationRecommendation',
    'get_user_modeling_backend',
    
    # Predictive Analytics Backend
    'PredictiveAnalyticsBackend',
    'RiskLevel',
    'PredictionType',
    'TrendDirection',
    'RiskAssessment',
    'HealthTrend',
    'EarlyWarning',
    'PreventiveRecommendation',
    'get_predictive_analytics_backend',
    
    # Business Intelligence
    'BusinessIntelligenceService',
    'MetricType',
    'AggregationPeriod',
    'ReportType',
    'AggregatedHealthMetrics',
    'UserEngagementMetrics',
    'SystemPerformanceMetrics',
    'BusinessIntelligenceReport',
    'get_business_intelligence_service',
    'get_global_bi_service',
    
    # ML Data Preparation
    'MLDataPreparationService',
    'FeatureEngineeringPipeline',
    'DataPreprocessor',
    'DataVersioning',
    'ModelPerformanceTracker',
    'FeatureType',
    'PreprocessingType',
    'ModelType',
    'DataVersion',
    'FeatureDefinition',
    'FeatureSet',
    'ProcessedDataset',
    'ModelVersion',
    'ModelPerformance',
    'get_ml_data_preparation_service',
    'get_global_ml_data_preparation_service'
] 
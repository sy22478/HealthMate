"""
Pydantic Schemas for HealthMate API
Provides comprehensive data validation and serialization
"""

from .auth_schemas import *
from .health_schemas import *
from .chat_schemas import *
from .common_schemas import *
from .enhanced_health_schemas import *

__all__ = [
    # Auth schemas
    "UserRegister",
    "UserLogin", 
    "UserResponse",
    "TokenResponse",
    "PasswordChange",
    "PasswordReset",
    "UserProfile",
    
    # Health schemas
    "HealthDataCreate",
    "HealthDataUpdate",
    "HealthDataResponse",
    "HealthMetrics",
    "SymptomLog",
    "MedicationLog",
    "HealthAlert",
    "HealthGoal",
    
    # Enhanced health schemas
    "UserHealthProfileCreate",
    "UserHealthProfileUpdate", 
    "UserHealthProfileResponse",
    "EnhancedMedicationCreate",
    "EnhancedMedicationUpdate",
    "EnhancedMedicationResponse",
    "MedicationDoseLogCreate",
    "MedicationDoseLogResponse",
    "EnhancedSymptomLogCreate",
    "EnhancedSymptomLogUpdate",
    "EnhancedSymptomLogResponse",
    "ConversationHistoryCreate",
    "ConversationHistoryResponse",
    "UserPreferenceCreate",
    "UserPreferenceUpdate",
    "UserPreferenceResponse",
    "UserFeedbackCreate",
    "UserFeedbackResponse",
    
    # Vector Store Optimization schemas
    "SearchType",
    "DocumentType", 
    "CredibilityLevel",
    "VectorSearchQuery",
    "VectorSearchResult",
    "VectorSearchResponse",
    "DocumentUploadRequest",
    "DocumentUploadResponse",
    "IndexStatisticsResponse",
    "DocumentDeleteRequest",
    "DocumentUpdateRequest",
    "VectorStoreOperationResponse",
    
    # AI Processing Pipeline schemas
    "ProcessingType",
    "ImageType",
    "AnalysisConfidence",
    "TextProcessingRequest",
    "TextProcessingResponse",
    "ImageProcessingRequest",
    "ImageAnalysisResponse",
    "DocumentProcessingRequest",
    "ConversationMemoryRequest",
    "ConversationMemoryResponse",
    
    # User Modeling Backend schemas
    "InteractionType",
    "ContentCategory",
    "PreferenceStrength",
    "UserInteractionRequest",
    "UserInteractionResponse",
    "UserPreferenceProfileResponse",
    "BehaviorPatternResponse",
    "PersonalizationRecommendationResponse",
    "UserModelingAnalyticsResponse",
    
    # Predictive Analytics Backend schemas
    "RiskLevel",
    "PredictionType",
    "TrendDirection",
    "RiskAssessmentRequest",
    "RiskAssessmentResponse",
    "HealthTrendRequest",
    "HealthTrendResponse",
    "EarlyWarningResponse",
    "PreventiveRecommendationResponse",
    "PredictiveAnalyticsSummaryResponse",
    
    # Chat schemas
    "ChatMessageCreate",
    "ChatMessageResponse",
    "ChatSessionCreate",
    "ChatSessionResponse",
    "ChatHistoryResponse",
    
    # Common schemas
    "ErrorResponse",
    "SuccessResponse",
    "PaginatedResponse"
] 
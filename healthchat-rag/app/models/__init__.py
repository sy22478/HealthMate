"""
Database Models for HealthMate
"""
from .user import User, Conversation
from .health_data import HealthData, SymptomLog, MedicationLog, HealthGoal, HealthAlert
from .enhanced_health_models import (
    UserHealthProfile, EnhancedMedication, MedicationDoseLog, EnhancedSymptomLog,
    HealthMetricsAggregation, ConversationHistory, AIResponseCache, UserPreference, UserFeedback
)
from .notification_models import (
    Notification, NotificationTemplate, NotificationDeliveryAttempt,
    UserNotificationPreference, NotificationBounce,
    NotificationType, NotificationPriority, NotificationChannel, NotificationStatus
)

__all__ = [
    "User",
    "Conversation", 
    "HealthData",
    "SymptomLog",
    "MedicationLog",
    "HealthGoal",
    "HealthAlert",
    # Enhanced health models
    "UserHealthProfile",
    "EnhancedMedication", 
    "MedicationDoseLog",
    "EnhancedSymptomLog",
    "HealthMetricsAggregation",
    # AI and conversation models
    "ConversationHistory",
    "AIResponseCache",
    "UserPreference",
    "UserFeedback",
    # Notification models
    "Notification",
    "NotificationTemplate",
    "NotificationDeliveryAttempt",
    "UserNotificationPreference",
    "NotificationBounce",
    "NotificationType",
    "NotificationPriority",
    "NotificationChannel",
    "NotificationStatus"
] 
"""
Enhanced Health Data Pydantic Schemas
Comprehensive schemas for enhanced health data, medications, symptoms, and AI interactions
"""
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime, date
from enum import Enum

from .health_schemas import (
    Gender, BloodType, ActivityLevel, SmokingStatus, AlcoholConsumption,
    MedicationStatus, SeverityLevel, HealthGoalStatus
)

class ConversationType(str, Enum):
    """Conversation type enumeration"""
    GENERAL_HEALTH = "general_health"
    SYMPTOM_DISCUSSION = "symptom_discussion"
    MEDICATION_QUERY = "medication_query"
    TREATMENT_PLAN = "treatment_plan"
    EMERGENCY = "emergency"

class FeedbackType(str, Enum):
    """Feedback type enumeration"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"

# Enhanced Medication Schemas
class EnhancedMedicationCreate(BaseModel):
    """Enhanced medication creation schema"""
    health_profile_id: int = Field(..., description="Health profile ID")
    medication_name: str = Field(..., max_length=200, description="Medication name")
    generic_name: Optional[str] = Field(None, max_length=200, description="Generic name")
    medication_type: Optional[str] = Field(None, max_length=100, description="Medication type")
    dosage_form: Optional[str] = Field(None, max_length=100, description="Dosage form")
    strength: str = Field(..., max_length=100, description="Medication strength")
    dosage_instructions: str = Field(..., description="Dosage instructions")
    frequency: str = Field(..., max_length=100, description="Frequency")
    prescribed_by: Optional[str] = Field(None, max_length=200, description="Prescribed by")
    prescription_date: Optional[date] = Field(None, description="Prescription date")
    expiry_date: Optional[date] = Field(None, description="Expiry date")
    refill_date: Optional[date] = Field(None, description="Refill date")
    refills_remaining: Optional[int] = Field(None, ge=0, description="Refills remaining")
    pharmacy: Optional[str] = Field(None, max_length=200, description="Pharmacy")
    status: Optional[MedicationStatus] = Field(MedicationStatus.ACTIVE, description="Medication status")
    start_date: Optional[date] = Field(None, description="Start date")
    end_date: Optional[date] = Field(None, description="End date")
    reason_for_discontinuation: Optional[str] = Field(None, description="Reason for discontinuation")
    side_effects: Optional[Dict[str, Any]] = Field(None, description="Side effects")
    effectiveness_rating: Optional[int] = Field(None, ge=1, le=10, description="Effectiveness rating (1-10)")
    adherence_rate: Optional[float] = Field(None, ge=0.0, le=100.0, description="Adherence rate percentage")
    notes: Optional[str] = Field(None, description="Notes")
    drug_interactions: Optional[Dict[str, Any]] = Field(None, description="Drug interactions")
    contraindications: Optional[Dict[str, Any]] = Field(None, description="Contraindications")
    warnings: Optional[str] = Field(None, description="Warnings")
    cost_per_unit: Optional[float] = Field(None, ge=0, description="Cost per unit")
    insurance_coverage: Optional[bool] = Field(None, description="Insurance coverage")
    copay_amount: Optional[float] = Field(None, ge=0, description="Copay amount")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "health_profile_id": 1,
                "medication_name": "Lisinopril",
                "generic_name": "Lisinopril",
                "medication_type": "prescription",
                "dosage_form": "tablet",
                "strength": "10mg",
                "dosage_instructions": "Take 1 tablet daily",
                "frequency": "once daily",
                "prescribed_by": "Dr. Smith",
                "status": "active"
            }
        }
    )


class EnhancedMedicationUpdate(BaseModel):
    """Enhanced medication update schema"""
    medication_name: Optional[str] = Field(None, max_length=200, description="Medication name")
    generic_name: Optional[str] = Field(None, max_length=200, description="Generic name")
    medication_type: Optional[str] = Field(None, max_length=100, description="Medication type")
    dosage_form: Optional[str] = Field(None, max_length=100, description="Dosage form")
    strength: Optional[str] = Field(None, max_length=100, description="Medication strength")
    dosage_instructions: Optional[str] = Field(None, description="Dosage instructions")
    frequency: Optional[str] = Field(None, max_length=100, description="Frequency")
    prescribed_by: Optional[str] = Field(None, max_length=200, description="Prescribed by")
    prescription_date: Optional[date] = Field(None, description="Prescription date")
    expiry_date: Optional[date] = Field(None, description="Expiry date")
    refill_date: Optional[date] = Field(None, description="Refill date")
    refills_remaining: Optional[int] = Field(None, ge=0, description="Refills remaining")
    pharmacy: Optional[str] = Field(None, max_length=200, description="Pharmacy")
    status: Optional[MedicationStatus] = Field(None, description="Medication status")
    start_date: Optional[date] = Field(None, description="Start date")
    end_date: Optional[date] = Field(None, description="End date")
    reason_for_discontinuation: Optional[str] = Field(None, description="Reason for discontinuation")
    side_effects: Optional[Dict[str, Any]] = Field(None, description="Side effects")
    effectiveness_rating: Optional[int] = Field(None, ge=1, le=10, description="Effectiveness rating (1-10)")
    adherence_rate: Optional[float] = Field(None, ge=0.0, le=100.0, description="Adherence rate percentage")
    notes: Optional[str] = Field(None, description="Notes")
    drug_interactions: Optional[Dict[str, Any]] = Field(None, description="Drug interactions")
    contraindications: Optional[Dict[str, Any]] = Field(None, description="Contraindications")
    warnings: Optional[str] = Field(None, description="Warnings")
    cost_per_unit: Optional[float] = Field(None, ge=0, description="Cost per unit")
    insurance_coverage: Optional[bool] = Field(None, description="Insurance coverage")
    copay_amount: Optional[float] = Field(None, ge=0, description="Copay amount")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "effectiveness_rating": 8,
                "adherence_rate": 95.0,
                "notes": "Working well, no side effects"
            }
        }
    )


class EnhancedMedicationResponse(BaseModel):
    """Enhanced medication response schema"""
    id: int = Field(..., description="Medication ID")
    health_profile_id: int = Field(..., description="Health profile ID")
    medication_name: str = Field(..., description="Medication name")
    generic_name: Optional[str] = Field(None, description="Generic name")
    medication_type: Optional[str] = Field(None, description="Medication type")
    dosage_form: Optional[str] = Field(None, description="Dosage form")
    strength: str = Field(..., description="Medication strength")
    dosage_instructions: str = Field(..., description="Dosage instructions")
    frequency: str = Field(..., description="Frequency")
    prescribed_by: Optional[str] = Field(None, description="Prescribed by")
    prescription_date: Optional[date] = Field(None, description="Prescription date")
    expiry_date: Optional[date] = Field(None, description="Expiry date")
    refill_date: Optional[date] = Field(None, description="Refill date")
    refills_remaining: Optional[int] = Field(None, description="Refills remaining")
    pharmacy: Optional[str] = Field(None, description="Pharmacy")
    status: MedicationStatus = Field(..., description="Medication status")
    start_date: Optional[date] = Field(None, description="Start date")
    end_date: Optional[date] = Field(None, description="End date")
    reason_for_discontinuation: Optional[str] = Field(None, description="Reason for discontinuation")
    side_effects: Optional[Dict[str, Any]] = Field(None, description="Side effects")
    effectiveness_rating: Optional[int] = Field(None, description="Effectiveness rating (1-10)")
    adherence_rate: Optional[float] = Field(None, description="Adherence rate percentage")
    notes: Optional[str] = Field(None, description="Notes")
    drug_interactions: Optional[Dict[str, Any]] = Field(None, description="Drug interactions")
    contraindications: Optional[Dict[str, Any]] = Field(None, description="Contraindications")
    warnings: Optional[str] = Field(None, description="Warnings")
    cost_per_unit: Optional[float] = Field(None, description="Cost per unit")
    insurance_coverage: Optional[bool] = Field(None, description="Insurance coverage")
    copay_amount: Optional[float] = Field(None, description="Copay amount")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "health_profile_id": 1,
                "medication_name": "Lisinopril",
                "strength": "10mg",
                "dosage_instructions": "Take 1 tablet daily",
                "frequency": "once daily",
                "status": "active",
                "effectiveness_rating": 8,
                "adherence_rate": 95.0,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }
    )


# Medication Dose Log Schemas
class MedicationDoseLogCreate(BaseModel):
    """Medication dose log creation schema"""
    medication_id: int = Field(..., description="Medication ID")
    dose_taken: str = Field(..., max_length=100, description="Dose taken")
    scheduled_time: Optional[datetime] = Field(None, description="Scheduled time")
    actual_time_taken: datetime = Field(default_factory=datetime.utcnow, description="Actual time taken")
    taken_as_prescribed: Optional[bool] = Field(None, description="Taken as prescribed")
    reason_for_deviation: Optional[str] = Field(None, description="Reason for deviation")
    missed_dose: Optional[bool] = Field(False, description="Missed dose")
    side_effects_experienced: Optional[Dict[str, Any]] = Field(None, description="Side effects experienced")
    effectiveness_rating: Optional[int] = Field(None, ge=1, le=10, description="Effectiveness rating (1-10)")
    notes: Optional[str] = Field(None, description="Notes")
    location_taken: Optional[str] = Field(None, max_length=200, description="Location taken")
    taken_with_food: Optional[bool] = Field(None, description="Taken with food")
    other_medications_taken: Optional[Dict[str, Any]] = Field(None, description="Other medications taken")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "medication_id": 1,
                "dose_taken": "10mg",
                "taken_as_prescribed": True,
                "effectiveness_rating": 8,
                "taken_with_food": True
            }
        }
    )


class MedicationDoseLogResponse(BaseModel):
    """Medication dose log response schema"""
    id: int = Field(..., description="Dose log ID")
    medication_id: int = Field(..., description="Medication ID")
    dose_taken: str = Field(..., description="Dose taken")
    scheduled_time: Optional[datetime] = Field(None, description="Scheduled time")
    actual_time_taken: datetime = Field(..., description="Actual time taken")
    taken_as_prescribed: Optional[bool] = Field(None, description="Taken as prescribed")
    reason_for_deviation: Optional[str] = Field(None, description="Reason for deviation")
    missed_dose: bool = Field(..., description="Missed dose")
    side_effects_experienced: Optional[Dict[str, Any]] = Field(None, description="Side effects experienced")
    effectiveness_rating: Optional[int] = Field(None, description="Effectiveness rating (1-10)")
    notes: Optional[str] = Field(None, description="Notes")
    location_taken: Optional[str] = Field(None, description="Location taken")
    taken_with_food: Optional[bool] = Field(None, description="Taken with food")
    other_medications_taken: Optional[Dict[str, Any]] = Field(None, description="Other medications taken")
    created_at: datetime = Field(..., description="Creation timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "medication_id": 1,
                "dose_taken": "10mg",
                "actual_time_taken": "2024-01-01T08:00:00Z",
                "taken_as_prescribed": True,
                "missed_dose": False,
                "created_at": "2024-01-01T08:00:00Z"
            }
        }
    )


# Enhanced Symptom Log Schemas
class EnhancedSymptomLogCreate(BaseModel):
    """Enhanced symptom log creation schema"""
    health_profile_id: int = Field(..., description="Health profile ID")
    symptom_name: str = Field(..., max_length=200, description="Symptom name")
    symptom_category: Optional[str] = Field(None, max_length=100, description="Symptom category")
    severity: SeverityLevel = Field(..., description="Symptom severity")
    pain_level: Optional[int] = Field(None, ge=0, le=10, description="Pain level (0-10)")
    description: Optional[str] = Field(None, description="Symptom description")
    location: Optional[str] = Field(None, max_length=200, description="Symptom location")
    duration: Optional[str] = Field(None, max_length=100, description="Symptom duration")
    frequency: Optional[str] = Field(None, max_length=100, description="Symptom frequency")
    triggers: Optional[Dict[str, Any]] = Field(None, description="Symptom triggers")
    aggravating_factors: Optional[Dict[str, Any]] = Field(None, description="Aggravating factors")
    relieving_factors: Optional[Dict[str, Any]] = Field(None, description="Relieving factors")
    associated_symptoms: Optional[Dict[str, Any]] = Field(None, description="Associated symptoms")
    impact_on_daily_activities: Optional[str] = Field(None, max_length=100, description="Impact on daily activities")
    impact_on_sleep: Optional[str] = Field(None, max_length=100, description="Impact on sleep")
    impact_on_mood: Optional[str] = Field(None, max_length=100, description="Impact on mood")
    treatments_tried: Optional[Dict[str, Any]] = Field(None, description="Treatments tried")
    treatment_effectiveness: Optional[Dict[str, Any]] = Field(None, description="Treatment effectiveness")
    medications_taken: Optional[Dict[str, Any]] = Field(None, description="Medications taken")
    related_conditions: Optional[Dict[str, Any]] = Field(None, description="Related conditions")
    doctor_consulted: Optional[bool] = Field(False, description="Whether doctor was consulted")
    doctor_notes: Optional[str] = Field(None, description="Doctor notes")
    emergency_visit: Optional[bool] = Field(False, description="Whether emergency visit was made")
    onset_time: Optional[datetime] = Field(None, description="Symptom onset time")
    peak_time: Optional[datetime] = Field(None, description="Symptom peak time")
    resolution_time: Optional[datetime] = Field(None, description="Symptom resolution time")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "health_profile_id": 1,
                "symptom_name": "Headache",
                "symptom_category": "pain",
                "severity": "moderate",
                "pain_level": 6,
                "description": "Dull headache in the front of the head",
                "location": "Frontal region",
                "duration": "2 hours",
                "frequency": "Occasional"
            }
        }
    )


class EnhancedSymptomLogUpdate(BaseModel):
    """Enhanced symptom log update schema"""
    symptom_name: Optional[str] = Field(None, max_length=200, description="Symptom name")
    symptom_category: Optional[str] = Field(None, max_length=100, description="Symptom category")
    severity: Optional[SeverityLevel] = Field(None, description="Symptom severity")
    pain_level: Optional[int] = Field(None, ge=0, le=10, description="Pain level (0-10)")
    description: Optional[str] = Field(None, description="Symptom description")
    location: Optional[str] = Field(None, max_length=200, description="Symptom location")
    duration: Optional[str] = Field(None, max_length=100, description="Symptom duration")
    frequency: Optional[str] = Field(None, max_length=100, description="Symptom frequency")
    triggers: Optional[Dict[str, Any]] = Field(None, description="Symptom triggers")
    aggravating_factors: Optional[Dict[str, Any]] = Field(None, description="Aggravating factors")
    relieving_factors: Optional[Dict[str, Any]] = Field(None, description="Relieving factors")
    associated_symptoms: Optional[Dict[str, Any]] = Field(None, description="Associated symptoms")
    impact_on_daily_activities: Optional[str] = Field(None, max_length=100, description="Impact on daily activities")
    impact_on_sleep: Optional[str] = Field(None, max_length=100, description="Impact on sleep")
    impact_on_mood: Optional[str] = Field(None, max_length=100, description="Impact on mood")
    treatments_tried: Optional[Dict[str, Any]] = Field(None, description="Treatments tried")
    treatment_effectiveness: Optional[Dict[str, Any]] = Field(None, description="Treatment effectiveness")
    medications_taken: Optional[Dict[str, Any]] = Field(None, description="Medications taken")
    related_conditions: Optional[Dict[str, Any]] = Field(None, description="Related conditions")
    doctor_consulted: Optional[bool] = Field(None, description="Whether doctor was consulted")
    doctor_notes: Optional[str] = Field(None, description="Doctor notes")
    emergency_visit: Optional[bool] = Field(None, description="Whether emergency visit was made")
    onset_time: Optional[datetime] = Field(None, description="Symptom onset time")
    peak_time: Optional[datetime] = Field(None, description="Symptom peak time")
    resolution_time: Optional[datetime] = Field(None, description="Symptom resolution time")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "severity": "mild",
                "pain_level": 3,
                "resolution_time": "2024-01-01T12:00:00Z"
            }
        }
    )


class EnhancedSymptomLogResponse(BaseModel):
    """Enhanced symptom log response schema"""
    id: int = Field(..., description="Symptom log ID")
    health_profile_id: int = Field(..., description="Health profile ID")
    symptom_name: str = Field(..., description="Symptom name")
    symptom_category: Optional[str] = Field(None, description="Symptom category")
    severity: SeverityLevel = Field(..., description="Symptom severity")
    pain_level: Optional[int] = Field(None, description="Pain level (0-10)")
    description: Optional[str] = Field(None, description="Symptom description")
    location: Optional[str] = Field(None, description="Symptom location")
    duration: Optional[str] = Field(None, description="Symptom duration")
    frequency: Optional[str] = Field(None, description="Symptom frequency")
    triggers: Optional[Dict[str, Any]] = Field(None, description="Symptom triggers")
    aggravating_factors: Optional[Dict[str, Any]] = Field(None, description="Aggravating factors")
    relieving_factors: Optional[Dict[str, Any]] = Field(None, description="Relieving factors")
    associated_symptoms: Optional[Dict[str, Any]] = Field(None, description="Associated symptoms")
    impact_on_daily_activities: Optional[str] = Field(None, description="Impact on daily activities")
    impact_on_sleep: Optional[str] = Field(None, description="Impact on sleep")
    impact_on_mood: Optional[str] = Field(None, description="Impact on mood")
    treatments_tried: Optional[Dict[str, Any]] = Field(None, description="Treatments tried")
    treatment_effectiveness: Optional[Dict[str, Any]] = Field(None, description="Treatment effectiveness")
    medications_taken: Optional[Dict[str, Any]] = Field(None, description="Medications taken")
    related_conditions: Optional[Dict[str, Any]] = Field(None, description="Related conditions")
    doctor_consulted: bool = Field(..., description="Whether doctor was consulted")
    doctor_notes: Optional[str] = Field(None, description="Doctor notes")
    emergency_visit: bool = Field(..., description="Whether emergency visit was made")
    onset_time: Optional[datetime] = Field(None, description="Symptom onset time")
    peak_time: Optional[datetime] = Field(None, description="Symptom peak time")
    resolution_time: Optional[datetime] = Field(None, description="Symptom resolution time")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "health_profile_id": 1,
                "symptom_name": "Headache",
                "severity": "moderate",
                "pain_level": 6,
                "created_at": "2024-01-01T10:00:00Z",
                "updated_at": "2024-01-01T10:00:00Z"
            }
        }
    )


# AI Interaction Schemas
class ConversationHistoryCreate(BaseModel):
    """Conversation history creation schema"""
    user_id: int = Field(..., description="User ID")
    conversation_id: str = Field(..., max_length=100, description="Conversation ID")
    message_type: str = Field(..., max_length=50, description="Message type")
    content: str = Field(..., description="Message content")
    content_summary: Optional[str] = Field(None, description="Content summary")
    conversation_type: Optional[ConversationType] = Field(None, description="Conversation type")
    context_sources: Optional[Dict[str, Any]] = Field(None, description="Context sources")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score")
    response_time_ms: Optional[int] = Field(None, ge=0, description="Response time in milliseconds")
    user_feedback: Optional[FeedbackType] = Field(None, description="User feedback")
    feedback_comment: Optional[str] = Field(None, description="Feedback comment")
    user_rating: Optional[int] = Field(None, ge=1, le=5, description="User rating (1-5)")
    health_context: Optional[Dict[str, Any]] = Field(None, description="Health context")
    symptom_mentions: Optional[Dict[str, Any]] = Field(None, description="Symptom mentions")
    medication_mentions: Optional[Dict[str, Any]] = Field(None, description="Medication mentions")
    urgency_level: Optional[str] = Field(None, max_length=20, description="Urgency level")
    model_used: Optional[str] = Field(None, max_length=100, description="Model used")
    tokens_used: Optional[int] = Field(None, ge=0, description="Tokens used")
    processing_metadata: Optional[Dict[str, Any]] = Field(None, description="Processing metadata")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": 1,
                "conversation_id": "conv_123",
                "message_type": "user_message",
                "content": "I have a headache",
                "conversation_type": "symptom_discussion",
                "urgency_level": "low"
            }
        }
    )


class ConversationHistoryResponse(BaseModel):
    """Conversation history response schema"""
    id: int = Field(..., description="Conversation history ID")
    user_id: int = Field(..., description="User ID")
    conversation_id: str = Field(..., description="Conversation ID")
    message_type: str = Field(..., description="Message type")
    content: str = Field(..., description="Message content")
    content_summary: Optional[str] = Field(None, description="Content summary")
    conversation_type: Optional[ConversationType] = Field(None, description="Conversation type")
    context_sources: Optional[Dict[str, Any]] = Field(None, description="Context sources")
    confidence_score: Optional[float] = Field(None, description="Confidence score")
    response_time_ms: Optional[int] = Field(None, description="Response time in milliseconds")
    user_feedback: Optional[FeedbackType] = Field(None, description="User feedback")
    feedback_comment: Optional[str] = Field(None, description="Feedback comment")
    user_rating: Optional[int] = Field(None, description="User rating (1-5)")
    health_context: Optional[Dict[str, Any]] = Field(None, description="Health context")
    symptom_mentions: Optional[Dict[str, Any]] = Field(None, description="Symptom mentions")
    medication_mentions: Optional[Dict[str, Any]] = Field(None, description="Medication mentions")
    urgency_level: Optional[str] = Field(None, description="Urgency level")
    model_used: Optional[str] = Field(None, description="Model used")
    tokens_used: Optional[int] = Field(None, description="Tokens used")
    processing_metadata: Optional[Dict[str, Any]] = Field(None, description="Processing metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "user_id": 1,
                "conversation_id": "conv_123",
                "message_type": "user_message",
                "content": "I have a headache",
                "conversation_type": "symptom_discussion",
                "created_at": "2024-01-01T10:00:00Z",
                "updated_at": "2024-01-01T10:00:00Z"
            }
        }
    )


# User Preference Schemas
class UserPreferenceCreate(BaseModel):
    """User preference creation schema"""
    user_id: int = Field(..., description="User ID")
    preferred_language: Optional[str] = Field("en", max_length=10, description="Preferred language")
    communication_style: Optional[str] = Field(None, max_length=50, description="Communication style")
    response_length_preference: Optional[str] = Field(None, max_length=20, description="Response length preference")
    notification_frequency: Optional[str] = Field(None, max_length=20, description="Notification frequency")
    health_detail_level: Optional[str] = Field(None, max_length=20, description="Health detail level")
    medical_terminology_level: Optional[str] = Field(None, max_length=20, description="Medical terminology level")
    include_statistics: Optional[bool] = Field(True, description="Include statistics")
    include_recommendations: Optional[bool] = Field(True, description="Include recommendations")
    data_sharing_level: Optional[str] = Field("minimal", max_length=20, description="Data sharing level")
    allow_analytics: Optional[bool] = Field(True, description="Allow analytics")
    allow_research_use: Optional[bool] = Field(False, description="Allow research use")
    ai_personality: Optional[str] = Field(None, max_length=50, description="AI personality")
    conversation_memory_duration: Optional[int] = Field(None, ge=1, le=365, description="Conversation memory duration in days")
    auto_suggestions: Optional[bool] = Field(True, description="Auto suggestions")
    proactive_alerts: Optional[bool] = Field(True, description="Proactive alerts")
    font_size: Optional[str] = Field("medium", max_length=20, description="Font size")
    color_scheme: Optional[str] = Field("default", max_length=20, description="Color scheme")
    screen_reader_support: Optional[bool] = Field(True, description="Screen reader support")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": 1,
                "preferred_language": "en",
                "communication_style": "friendly",
                "response_length_preference": "medium",
                "health_detail_level": "detailed",
                "ai_personality": "empathetic"
            }
        }
    )


class UserPreferenceUpdate(BaseModel):
    """User preference update schema"""
    preferred_language: Optional[str] = Field(None, max_length=10, description="Preferred language")
    communication_style: Optional[str] = Field(None, max_length=50, description="Communication style")
    response_length_preference: Optional[str] = Field(None, max_length=20, description="Response length preference")
    notification_frequency: Optional[str] = Field(None, max_length=20, description="Notification frequency")
    health_detail_level: Optional[str] = Field(None, max_length=20, description="Health detail level")
    medical_terminology_level: Optional[str] = Field(None, max_length=20, description="Medical terminology level")
    include_statistics: Optional[bool] = Field(None, description="Include statistics")
    include_recommendations: Optional[bool] = Field(None, description="Include recommendations")
    data_sharing_level: Optional[str] = Field(None, max_length=20, description="Data sharing level")
    allow_analytics: Optional[bool] = Field(None, description="Allow analytics")
    allow_research_use: Optional[bool] = Field(None, description="Allow research use")
    ai_personality: Optional[str] = Field(None, max_length=50, description="AI personality")
    conversation_memory_duration: Optional[int] = Field(None, ge=1, le=365, description="Conversation memory duration in days")
    auto_suggestions: Optional[bool] = Field(None, description="Auto suggestions")
    proactive_alerts: Optional[bool] = Field(None, description="Proactive alerts")
    font_size: Optional[str] = Field(None, max_length=20, description="Font size")
    color_scheme: Optional[str] = Field(None, max_length=20, description="Color scheme")
    screen_reader_support: Optional[bool] = Field(None, description="Screen reader support")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "communication_style": "professional",
                "ai_personality": "direct",
                "font_size": "large"
            }
        }
    )


class UserPreferenceResponse(BaseModel):
    """User preference response schema"""
    id: int = Field(..., description="Preference ID")
    user_id: int = Field(..., description="User ID")
    preferred_language: str = Field(..., description="Preferred language")
    communication_style: Optional[str] = Field(None, description="Communication style")
    response_length_preference: Optional[str] = Field(None, description="Response length preference")
    notification_frequency: Optional[str] = Field(None, description="Notification frequency")
    health_detail_level: Optional[str] = Field(None, description="Health detail level")
    medical_terminology_level: Optional[str] = Field(None, description="Medical terminology level")
    include_statistics: bool = Field(..., description="Include statistics")
    include_recommendations: bool = Field(..., description="Include recommendations")
    data_sharing_level: str = Field(..., description="Data sharing level")
    allow_analytics: bool = Field(..., description="Allow analytics")
    allow_research_use: bool = Field(..., description="Allow research use")
    ai_personality: Optional[str] = Field(None, description="AI personality")
    conversation_memory_duration: Optional[int] = Field(None, description="Conversation memory duration in days")
    auto_suggestions: bool = Field(..., description="Auto suggestions")
    proactive_alerts: bool = Field(..., description="Proactive alerts")
    font_size: str = Field(..., description="Font size")
    color_scheme: str = Field(..., description="Color scheme")
    screen_reader_support: bool = Field(..., description="Screen reader support")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "user_id": 1,
                "preferred_language": "en",
                "communication_style": "friendly",
                "include_statistics": True,
                "ai_personality": "empathetic",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }
    )


# User Feedback Schemas
class UserFeedbackCreate(BaseModel):
    """User feedback creation schema"""
    user_id: int = Field(..., description="User ID")
    conversation_id: Optional[str] = Field(None, max_length=100, description="Conversation ID")
    response_id: Optional[int] = Field(None, description="Response ID")
    feedback_type: FeedbackType = Field(..., description="Feedback type")
    rating: Optional[int] = Field(None, ge=1, le=5, description="Rating (1-5)")
    detailed_feedback: Optional[str] = Field(None, description="Detailed feedback")
    category: Optional[str] = Field(None, max_length=100, description="Feedback category")
    context: Optional[Dict[str, Any]] = Field(None, description="Context")
    user_expectation: Optional[str] = Field(None, description="User expectation")
    actual_outcome: Optional[str] = Field(None, description="Actual outcome")
    impact_on_health_decision: Optional[str] = Field(None, max_length=50, description="Impact on health decision")
    action_taken: Optional[str] = Field(None, description="Action taken")
    follow_up_needed: Optional[bool] = Field(False, description="Follow up needed")
    response_accuracy: Optional[int] = Field(None, ge=1, le=5, description="Response accuracy (1-5)")
    response_helpfulness: Optional[int] = Field(None, ge=1, le=5, description="Response helpfulness (1-5)")
    response_clarity: Optional[int] = Field(None, ge=1, le=5, description="Response clarity (1-5)")
    overall_satisfaction: Optional[int] = Field(None, ge=1, le=5, description="Overall satisfaction (1-5)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": 1,
                "conversation_id": "conv_123",
                "feedback_type": "positive",
                "rating": 5,
                "category": "accuracy",
                "response_accuracy": 5,
                "response_helpfulness": 5,
                "overall_satisfaction": 5
            }
        }
    )


class UserFeedbackResponse(BaseModel):
    """User feedback response schema"""
    id: int = Field(..., description="Feedback ID")
    user_id: int = Field(..., description="User ID")
    conversation_id: Optional[str] = Field(None, description="Conversation ID")
    response_id: Optional[int] = Field(None, description="Response ID")
    feedback_type: FeedbackType = Field(..., description="Feedback type")
    rating: Optional[int] = Field(None, description="Rating (1-5)")
    detailed_feedback: Optional[str] = Field(None, description="Detailed feedback")
    category: Optional[str] = Field(None, description="Feedback category")
    context: Optional[Dict[str, Any]] = Field(None, description="Context")
    user_expectation: Optional[str] = Field(None, description="User expectation")
    actual_outcome: Optional[str] = Field(None, description="Actual outcome")
    impact_on_health_decision: Optional[str] = Field(None, description="Impact on health decision")
    action_taken: Optional[str] = Field(None, description="Action taken")
    follow_up_needed: bool = Field(..., description="Follow up needed")
    response_accuracy: Optional[int] = Field(None, description="Response accuracy (1-5)")
    response_helpfulness: Optional[int] = Field(None, description="Response helpfulness (1-5)")
    response_clarity: Optional[int] = Field(None, description="Response clarity (1-5)")
    overall_satisfaction: Optional[int] = Field(None, description="Overall satisfaction (1-5)")
    follow_up_completed: bool = Field(..., description="Follow up completed")
    follow_up_notes: Optional[str] = Field(None, description="Follow up notes")
    resolution_status: Optional[str] = Field(None, description="Resolution status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "user_id": 1,
                "feedback_type": "positive",
                "rating": 5,
                "follow_up_needed": False,
                "follow_up_completed": False,
                "created_at": "2024-01-01T10:00:00Z",
                "updated_at": "2024-01-01T10:00:00Z"
            }
        }
    )

# Health Data Processing Schemas
class DataSourceConfigCreate(BaseModel):
    """Data source configuration creation schema"""
    source_type: str = Field(..., description="Data source type")
    api_key: str = Field(..., description="API key")
    api_secret: str = Field(..., description="API secret")
    base_url: str = Field(..., description="Base URL")
    rate_limit_per_minute: Optional[int] = Field(60, ge=1, le=1000, description="Rate limit per minute")
    timeout_seconds: Optional[int] = Field(30, ge=5, le=300, description="Timeout in seconds")
    retry_attempts: Optional[int] = Field(3, ge=1, le=10, description="Retry attempts")
    retry_delay_seconds: Optional[int] = Field(5, ge=1, le=60, description="Retry delay in seconds")
    enabled: Optional[bool] = Field(True, description="Whether the source is enabled")
    custom_headers: Optional[Dict[str, str]] = Field(None, description="Custom headers")
    custom_params: Optional[Dict[str, Any]] = Field(None, description="Custom parameters")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source_type": "fitbit",
                "api_key": "your_api_key",
                "api_secret": "your_api_secret",
                "base_url": "https://api.fitbit.com",
                "rate_limit_per_minute": 60,
                "timeout_seconds": 30,
                "enabled": True
            }
        }
    )

class DataSourceConfigResponse(BaseModel):
    """Data source configuration response schema"""
    id: int = Field(..., description="Configuration ID")
    source_type: str = Field(..., description="Data source type")
    base_url: str = Field(..., description="Base URL")
    enabled: bool = Field(..., description="Whether the source is enabled")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "source_type": "fitbit",
                "base_url": "https://api.fitbit.com",
                "enabled": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }
    )

class HealthDataProcessingRequest(BaseModel):
    """Health data processing request schema"""
    data_types: List[str] = Field(..., description="Data types to process")
    sources: List[str] = Field(..., description="Data sources")
    days_back: Optional[int] = Field(30, ge=1, le=365, description="Days of data to fetch")
    process_data: Optional[bool] = Field(True, description="Whether to process the data")
    processing_stages: Optional[List[str]] = Field(None, description="Processing stages to run")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "data_types": ["heart_rate", "steps", "sleep"],
                "sources": ["fitbit", "manual_entry"],
                "days_back": 30,
                "process_data": True,
                "processing_stages": ["ingestion", "validation", "transformation"]
            }
        }
    )

class HealthDataProcessingResponse(BaseModel):
    """Health data processing response schema"""
    success: bool = Field(..., description="Whether processing was successful")
    stage: str = Field(..., description="Last processing stage completed")
    data_points_processed: int = Field(..., description="Number of data points processed")
    data_points_valid: int = Field(..., description="Number of valid data points")
    data_points_invalid: int = Field(..., description="Number of invalid data points")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Data quality score")
    processing_time: float = Field(..., description="Processing time in seconds")
    errors: List[str] = Field(..., description="Processing errors")
    warnings: List[str] = Field(..., description="Processing warnings")
    metadata: Dict[str, Any] = Field(..., description="Processing metadata")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "stage": "analytics",
                "data_points_processed": 100,
                "data_points_valid": 95,
                "data_points_invalid": 5,
                "quality_score": 0.95,
                "processing_time": 2.5,
                "errors": [],
                "warnings": ["Some data points had low confidence"],
                "metadata": {
                    "stages_completed": ["ingestion", "validation", "transformation"],
                    "data_sources": ["fitbit"],
                    "data_types": ["heart_rate", "steps"]
                }
            }
        }
    )

class HealthAnalyticsRequest(BaseModel):
    """Health analytics request schema"""
    analytics_types: Optional[List[str]] = Field(None, description="Types of analytics to run")
    include_trends: Optional[bool] = Field(True, description="Include trend analysis")
    include_patterns: Optional[bool] = Field(True, description="Include pattern recognition")
    include_health_score: Optional[bool] = Field(True, description="Include health scoring")
    include_comparative: Optional[bool] = Field(True, description="Include comparative analysis")
    include_risk_assessment: Optional[bool] = Field(True, description="Include risk assessment")
    include_predictions: Optional[bool] = Field(False, description="Include predictive modeling")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "analytics_types": ["trend_analysis", "health_scoring", "risk_assessment"],
                "include_trends": True,
                "include_patterns": True,
                "include_health_score": True,
                "include_comparative": False,
                "include_risk_assessment": True,
                "include_predictions": False
            }
        }
    )

class HealthAnalyticsResponse(BaseModel):
    """Health analytics response schema"""
    user_id: int = Field(..., description="User ID")
    analytics_results: Dict[str, Any] = Field(..., description="Analytics results")
    generated_at: datetime = Field(..., description="When analytics were generated")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": 1,
                "analytics_results": {
                    "trends": [
                        {
                            "data_type": "heart_rate",
                            "direction": "stable",
                            "confidence": 0.8
                        }
                    ],
                    "health_score": {
                        "overall_score": 0.85,
                        "category": "good"
                    }
                },
                "generated_at": "2024-01-01T00:00:00Z"
            }
        }
    )

# Vector Store Optimization Schemas
class SearchType(str, Enum):
    """Search type enumeration"""
    VECTOR_ONLY = "vector_only"
    HYBRID = "hybrid"
    KEYWORD_ONLY = "keyword_only"
    SEMANTIC = "semantic"

class DocumentType(str, Enum):
    """Document type enumeration"""
    MEDICAL_GUIDELINE = "medical_guideline"
    DRUG_INFORMATION = "drug_information"
    SYMPTOM_DESCRIPTION = "symptom_description"
    TREATMENT_PROTOCOL = "treatment_protocol"
    DIAGNOSTIC_CRITERIA = "diagnostic_criteria"
    RESEARCH_PAPER = "research_paper"
    CLINICAL_TRIAL = "clinical_trial"
    PATIENT_EDUCATION = "patient_education"
    EMERGENCY_PROTOCOL = "emergency_protocol"

class CredibilityLevel(str, Enum):
    """Credibility level enumeration"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class VectorSearchQuery(BaseModel):
    """Vector search query schema"""
    query: str = Field(..., description="Search query text", min_length=1, max_length=1000)
    search_type: SearchType = Field(default=SearchType.HYBRID, description="Type of search to perform")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Search filters")
    max_results: int = Field(default=10, ge=1, le=100, description="Maximum number of results")
    min_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Minimum similarity score")
    include_metadata: bool = Field(default=True, description="Include metadata in results")

    class Config:
        schema_extra = {
            "example": {
                "query": "What are the symptoms of diabetes?",
                "search_type": "hybrid",
                "filters": {
                    "document_type": ["medical_guideline", "patient_education"],
                    "credibility_level": ["high", "medium"]
                },
                "max_results": 10,
                "min_score": 0.7,
                "include_metadata": True
            }
        }

class VectorSearchResult(BaseModel):
    """Vector search result schema"""
    text: str = Field(..., description="Result text content")
    source: str = Field(..., description="Document source")
    title: str = Field(..., description="Document title")
    score: float = Field(..., description="Similarity score", ge=0.0, le=1.0)
    document_type: DocumentType = Field(..., description="Document type")
    credibility_level: CredibilityLevel = Field(..., description="Credibility level")
    last_updated: datetime = Field(..., description="Last update timestamp")
    relevance_score: float = Field(..., description="Relevance score", ge=0.0, le=1.0)
    confidence_score: float = Field(..., description="Confidence score", ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        schema_extra = {
            "example": {
                "text": "Diabetes symptoms include increased thirst, frequent urination, and fatigue...",
                "source": "mayo_clinic",
                "title": "Diabetes Symptoms and Causes",
                "score": 0.85,
                "document_type": "medical_guideline",
                "credibility_level": "high",
                "last_updated": "2024-01-15T10:30:00Z",
                "relevance_score": 0.92,
                "confidence_score": 0.88,
                "metadata": {
                    "medical_terms": ["diabetes", "thirst", "fatigue"],
                    "key_concepts": ["symptoms", "diagnosis"]
                }
            }
        }

class VectorSearchResponse(BaseModel):
    """Vector search response schema"""
    results: List[VectorSearchResult] = Field(..., description="Search results")
    total_results: int = Field(..., description="Total number of results")
    search_time: float = Field(..., description="Search execution time in seconds")
    query: VectorSearchQuery = Field(..., description="Original search query")

    class Config:
        schema_extra = {
            "example": {
                "results": [],
                "total_results": 5,
                "search_time": 0.245,
                "query": {
                    "query": "What are the symptoms of diabetes?",
                    "search_type": "hybrid",
                    "max_results": 10
                }
            }
        }

class DocumentUploadRequest(BaseModel):
    """Document upload request schema"""
    documents: List[Dict[str, Any]] = Field(..., description="Documents to upload")
    
    class Config:
        schema_extra = {
            "example": {
                "documents": [
                    {
                        "content": "Diabetes is a chronic disease that affects how your body turns food into energy...",
                        "source": "cdc_diabetes_guide",
                        "title": "Diabetes Overview",
                        "document_type": "medical_guideline",
                        "credibility_level": "high",
                        "last_updated": "2024-01-15T10:30:00Z"
                    }
                ]
            }
        }

class DocumentUploadResponse(BaseModel):
    """Document upload response schema"""
    total_documents: int = Field(..., description="Total documents processed")
    successful_uploads: int = Field(..., description="Successfully uploaded documents")
    failed_uploads: int = Field(..., description="Failed uploads")
    errors: List[str] = Field(default_factory=list, description="Error messages")
    processing_time: float = Field(..., description="Processing time in seconds")

    class Config:
        schema_extra = {
            "example": {
                "total_documents": 10,
                "successful_uploads": 9,
                "failed_uploads": 1,
                "errors": ["Document 5: Invalid format"],
                "processing_time": 2.45
            }
        }

class IndexStatisticsResponse(BaseModel):
    """Index statistics response schema"""
    total_vector_count: int = Field(..., description="Total number of vectors")
    dimension: int = Field(..., description="Vector dimensions")
    index_fullness: float = Field(..., description="Index fullness percentage")
    namespaces: Dict[str, Any] = Field(default_factory=dict, description="Namespace information")

    class Config:
        schema_extra = {
            "example": {
                "total_vector_count": 15000,
                "dimension": 1536,
                "index_fullness": 0.75,
                "namespaces": {
                    "default": {"vector_count": 15000}
                }
            }
        }

class DocumentDeleteRequest(BaseModel):
    """Document deletion request schema"""
    source: str = Field(..., description="Source identifier to delete")

    class Config:
        schema_extra = {
            "example": {
                "source": "old_medical_guidelines"
            }
        }

class DocumentUpdateRequest(BaseModel):
    """Document metadata update request schema"""
    source: str = Field(..., description="Source identifier to update")
    updates: Dict[str, Any] = Field(..., description="Metadata updates to apply")

    class Config:
        schema_extra = {
            "example": {
                "source": "cdc_guidelines",
                "updates": {
                    "credibility_level": "high",
                    "last_updated": "2024-01-15T10:30:00Z"
                }
            }
        }

class VectorStoreOperationResponse(BaseModel):
    """Generic vector store operation response schema"""
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Operation message")
    operation_time: float = Field(..., description="Operation execution time in seconds")

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Documents deleted successfully",
                "operation_time": 0.15
            }
        }

# AI Processing Pipeline Schemas
class ProcessingType(str, Enum):
    """AI processing type enumeration"""
    TEXT_ANALYSIS = "text_analysis"
    IMAGE_ANALYSIS = "image_analysis"
    DOCUMENT_OCR = "document_ocr"
    MEDICAL_IMAGE = "medical_image"
    CONVERSATION_MEMORY = "conversation_memory"
    CONTEXT_GENERATION = "context_generation"

class ImageType(str, Enum):
    """Image type enumeration"""
    MEDICAL_SCAN = "medical_scan"
    DOCUMENT = "document"
    PHOTO = "photo"
    DIAGRAM = "diagram"
    CHART = "chart"

class AnalysisConfidence(str, Enum):
    """Analysis confidence levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class TextProcessingRequest(BaseModel):
    """Text processing request schema"""
    text: str = Field(..., description="Text to process", min_length=1, max_length=10000)
    processing_type: ProcessingType = Field(default=ProcessingType.TEXT_ANALYSIS, description="Type of processing")

    class Config:
        schema_extra = {
            "example": {
                "text": "Patient reports severe chest pain and shortness of breath",
                "processing_type": "text_analysis"
            }
        }

class TextProcessingResponse(BaseModel):
    """Text processing response schema"""
    content: str = Field(..., description="Processed content")
    confidence: float = Field(..., description="Processing confidence", ge=0.0, le=1.0)
    processing_type: ProcessingType = Field(..., description="Processing type used")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Processing metadata")
    processing_time: float = Field(..., description="Processing time in seconds")
    model_used: str = Field(..., description="AI model used for processing")

    class Config:
        schema_extra = {
            "example": {
                "content": "Patient reports severe chest pain and shortness of breath",
                "confidence": 0.85,
                "processing_type": "text_analysis",
                "metadata": {
                    "entities": [{"entity": "chest pain", "type": "symptom"}],
                    "medical_terms": ["chest pain", "shortness of breath"],
                    "urgency": "high"
                },
                "processing_time": 0.245,
                "model_used": "medical_nlp_pipeline"
            }
        }

class ImageProcessingRequest(BaseModel):
    """Image processing request schema"""
    image_data: str = Field(..., description="Base64 encoded image data")
    image_type: ImageType = Field(default=ImageType.MEDICAL_SCAN, description="Type of image")

    class Config:
        schema_extra = {
            "example": {
                "image_data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
                "image_type": "medical_scan"
            }
        }

class ImageAnalysisResponse(BaseModel):
    """Image analysis response schema"""
    description: str = Field(..., description="Image description")
    detected_objects: List[str] = Field(default_factory=list, description="Detected objects")
    medical_findings: List[str] = Field(default_factory=list, description="Medical findings")
    confidence: AnalysisConfidence = Field(..., description="Analysis confidence")
    bounding_boxes: List[Dict[str, Any]] = Field(default_factory=list, description="Object bounding boxes")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Analysis metadata")

    class Config:
        schema_extra = {
            "example": {
                "description": "Chest X-ray showing clear lung fields with no obvious abnormalities",
                "detected_objects": ["lungs", "ribs", "heart"],
                "medical_findings": ["normal lung fields", "no pneumothorax"],
                "confidence": "high",
                "bounding_boxes": [],
                "metadata": {
                    "image_type": "medical_scan",
                    "processing_time": 1.234
                }
            }
        }

class DocumentProcessingRequest(BaseModel):
    """Document processing request schema"""
    document_data: str = Field(..., description="Base64 encoded document data")
    file_type: str = Field(..., description="Document file type (pdf, png, jpg, etc.)")

    class Config:
        schema_extra = {
            "example": {
                "document_data": "JVBERi0xLjQKJcOkw7zDtsO...",
                "file_type": "pdf"
            }
        }

class ConversationMemoryRequest(BaseModel):
    """Conversation memory request schema"""
    conversation_id: str = Field(..., description="Conversation identifier")
    user_id: int = Field(..., description="User identifier")
    message: Dict[str, Any] = Field(..., description="Message to add to memory")
    action: str = Field(default="add", description="Memory action (add, get, update, clear)")

    class Config:
        schema_extra = {
            "example": {
                "conversation_id": "conv_12345",
                "user_id": 1,
                "message": {
                    "role": "user",
                    "content": "I have chest pain",
                    "timestamp": "2024-01-15T10:30:00Z"
                },
                "action": "add"
            }
        }

class ConversationMemoryResponse(BaseModel):
    """Conversation memory response schema"""
    conversation_id: str = Field(..., description="Conversation identifier")
    user_id: int = Field(..., description="User identifier")
    messages: List[Dict[str, Any]] = Field(default_factory=list, description="Conversation messages")
    context_summary: str = Field(..., description="Conversation context summary")
    medical_context: Dict[str, Any] = Field(default_factory=dict, description="Medical context")
    last_updated: datetime = Field(..., description="Last update timestamp")
    memory_score: float = Field(..., description="Memory importance score", ge=0.0, le=1.0)

    class Config:
        schema_extra = {
            "example": {
                "conversation_id": "conv_12345",
                "user_id": 1,
                "messages": [],
                "context_summary": "Patient discussing chest pain symptoms",
                "medical_context": {
                    "symptoms_mentioned": ["chest pain"],
                    "conditions_discussed": [],
                    "medications_referenced": []
                },
                "last_updated": "2024-01-15T10:30:00Z",
                "memory_score": 0.75
            }
        }

# User Modeling Backend Schemas
class InteractionType(str, Enum):
    """User interaction types"""
    CHAT_MESSAGE = "chat_message"
    HEALTH_DATA_ENTRY = "health_data_entry"
    MEDICATION_LOG = "medication_log"
    SYMPTOM_LOG = "symptom_log"
    SEARCH_QUERY = "search_query"
    DOCUMENT_VIEW = "document_view"
    FEEDBACK_SUBMISSION = "feedback_submission"
    GOAL_SETTING = "goal_setting"
    REMINDER_INTERACTION = "reminder_interaction"
    PROFILE_UPDATE = "profile_update"

class ContentCategory(str, Enum):
    """Content categories for personalization"""
    DIABETES = "diabetes"
    CARDIOVASCULAR = "cardiovascular"
    MENTAL_HEALTH = "mental_health"
    NUTRITION = "nutrition"
    EXERCISE = "exercise"
    MEDICATION = "medication"
    SYMPTOMS = "symptoms"
    PREVENTIVE_CARE = "preventive_care"
    EMERGENCY = "emergency"
    GENERAL_HEALTH = "general_health"

class PreferenceStrength(str, Enum):
    """Preference strength levels"""
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    NEUTRAL = "neutral"

class UserInteractionRequest(BaseModel):
    """User interaction tracking request schema"""
    interaction_type: InteractionType = Field(..., description="Type of interaction")
    content: str = Field(..., description="Interaction content", min_length=1, max_length=5000)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    session_id: str = Field(..., description="Session identifier")
    duration: Optional[float] = Field(None, description="Interaction duration in seconds", ge=0)
    engagement_score: Optional[float] = Field(None, description="Engagement score", ge=0.0, le=1.0)

    class Config:
        schema_extra = {
            "example": {
                "interaction_type": "chat_message",
                "content": "I have been experiencing chest pain for the past week",
                "metadata": {
                    "message_length": 65,
                    "response_time": 2.5
                },
                "session_id": "sess_12345",
                "duration": 30.5,
                "engagement_score": 0.8
            }
        }

class UserInteractionResponse(BaseModel):
    """User interaction tracking response schema"""
    success: bool = Field(..., description="Tracking success status")
    interaction_id: str = Field(..., description="Generated interaction identifier")
    engagement_score: float = Field(..., description="Calculated engagement score", ge=0.0, le=1.0)
    profile_updated: bool = Field(..., description="Whether user profile was updated")
    message: str = Field(..., description="Response message")

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "interaction_id": "int_67890",
                "engagement_score": 0.75,
                "profile_updated": False,
                "message": "Interaction tracked successfully"
            }
        }

class UserPreferenceProfileResponse(BaseModel):
    """User preference profile response schema"""
    user_id: int = Field(..., description="User identifier")
    content_preferences: Dict[str, float] = Field(..., description="Content category preferences")
    interaction_patterns: Dict[str, Any] = Field(..., description="Interaction patterns")
    health_goals: List[str] = Field(default_factory=list, description="Health goals")
    communication_style: str = Field(..., description="Communication style")
    engagement_level: str = Field(..., description="Engagement level")
    last_updated: datetime = Field(..., description="Last update timestamp")
    confidence_score: float = Field(..., description="Profile confidence score", ge=0.0, le=1.0)

    class Config:
        schema_extra = {
            "example": {
                "user_id": 1,
                "content_preferences": {
                    "diabetes": 0.8,
                    "cardiovascular": 0.6,
                    "nutrition": 0.4
                },
                "interaction_patterns": {
                    "peak_hours": {"9": 0.3, "14": 0.4, "20": 0.3},
                    "interaction_types": {"chat_message": 0.5, "health_data_entry": 0.3}
                },
                "health_goals": [
                    "Manage blood sugar levels",
                    "Improve cardiovascular health"
                ],
                "communication_style": "formal",
                "engagement_level": "high",
                "last_updated": "2024-01-15T10:30:00Z",
                "confidence_score": 0.85
            }
        }

class BehaviorPatternResponse(BaseModel):
    """Behavior pattern response schema"""
    pattern_type: str = Field(..., description="Pattern type")
    frequency: float = Field(..., description="Pattern frequency", ge=0.0, le=1.0)
    time_distribution: Dict[str, float] = Field(default_factory=dict, description="Time distribution")
    content_affinity: Dict[str, float] = Field(default_factory=dict, description="Content affinity")
    confidence: float = Field(..., description="Pattern confidence", ge=0.0, le=1.0)
    last_observed: datetime = Field(..., description="Last observation timestamp")

    class Config:
        schema_extra = {
            "example": {
                "pattern_type": "time_distribution",
                "frequency": 0.8,
                "time_distribution": {"9": 0.4, "14": 0.3, "20": 0.3},
                "content_affinity": {},
                "confidence": 0.75,
                "last_observed": "2024-01-15T10:30:00Z"
            }
        }

class PersonalizationRecommendationResponse(BaseModel):
    """Personalization recommendation response schema"""
    content_type: str = Field(..., description="Content type")
    content_id: str = Field(..., description="Content identifier")
    relevance_score: float = Field(..., description="Relevance score", ge=0.0, le=1.0)
    reasoning: str = Field(..., description="Recommendation reasoning")
    user_preferences_used: List[str] = Field(default_factory=list, description="Preferences used")
    confidence: float = Field(..., description="Recommendation confidence", ge=0.0, le=1.0)

    class Config:
        schema_extra = {
            "example": {
                "content_type": "content",
                "content_id": "category_diabetes",
                "relevance_score": 0.85,
                "reasoning": "Based on your interest in diabetes topics",
                "user_preferences_used": ["content_preference_diabetes"],
                "confidence": 0.8
            }
        }

class UserModelingAnalyticsResponse(BaseModel):
    """User modeling analytics response schema"""
    total_interactions: int = Field(..., description="Total interactions tracked")
    profile_confidence: float = Field(..., description="Average profile confidence", ge=0.0, le=1.0)
    engagement_distribution: Dict[str, int] = Field(..., description="Engagement level distribution")
    top_content_categories: List[Dict[str, Any]] = Field(..., description="Top content categories")
    behavior_patterns_count: int = Field(..., description="Number of behavior patterns identified")

    class Config:
        schema_extra = {
            "example": {
                "total_interactions": 150,
                "profile_confidence": 0.78,
                "engagement_distribution": {
                    "high": 45,
                    "medium": 75,
                    "low": 30
                },
                "top_content_categories": [
                    {"category": "diabetes", "preference": 0.8},
                    {"category": "cardiovascular", "preference": 0.6}
                ],
                "behavior_patterns_count": 8
            }
        }

# Predictive Analytics Backend Schemas
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

class RiskAssessmentRequest(BaseModel):
    """Risk assessment request schema"""
    risk_type: PredictionType = Field(..., description="Type of risk assessment")
    include_recommendations: bool = Field(default=True, description="Include recommendations in response")

    class Config:
        schema_extra = {
            "example": {
                "risk_type": "cardiovascular_risk",
                "include_recommendations": True
            }
        }

class RiskAssessmentResponse(BaseModel):
    """Risk assessment response schema"""
    risk_type: PredictionType = Field(..., description="Type of risk assessment")
    risk_level: RiskLevel = Field(..., description="Assessed risk level")
    risk_score: float = Field(..., description="Risk score", ge=0.0, le=1.0)
    confidence: float = Field(..., description="Assessment confidence", ge=0.0, le=1.0)
    factors: List[str] = Field(default_factory=list, description="Identified risk factors")
    recommendations: List[str] = Field(default_factory=list, description="Health recommendations")
    assessment_date: datetime = Field(..., description="Assessment date")
    next_assessment_date: datetime = Field(..., description="Recommended next assessment date")

    class Config:
        schema_extra = {
            "example": {
                "risk_type": "cardiovascular_risk",
                "risk_level": "moderate",
                "risk_score": 0.45,
                "confidence": 0.85,
                "factors": ["High blood pressure", "Age over 65"],
                "recommendations": ["Monitor blood pressure daily", "Reduce sodium intake"],
                "assessment_date": "2024-01-15T10:30:00Z",
                "next_assessment_date": "2024-04-15T10:30:00Z"
            }
        }

class HealthTrendRequest(BaseModel):
    """Health trend prediction request schema"""
    metric_name: str = Field(..., description="Health metric to predict", min_length=1)
    timeframe_days: int = Field(default=90, ge=30, le=365, description="Prediction timeframe in days")

    class Config:
        schema_extra = {
            "example": {
                "metric_name": "blood_pressure",
                "timeframe_days": 90
            }
        }

class HealthTrendResponse(BaseModel):
    """Health trend prediction response schema"""
    metric_name: str = Field(..., description="Health metric name")
    current_value: float = Field(..., description="Current metric value")
    predicted_value: float = Field(..., description="Predicted metric value")
    trend_direction: TrendDirection = Field(..., description="Trend direction")
    confidence: float = Field(..., description="Prediction confidence", ge=0.0, le=1.0)
    timeframe_days: int = Field(..., description="Prediction timeframe")
    factors: List[str] = Field(default_factory=list, description="Factors affecting trend")
    recommendations: List[str] = Field(default_factory=list, description="Health recommendations")

    class Config:
        schema_extra = {
            "example": {
                "metric_name": "blood_pressure",
                "current_value": 140.0,
                "predicted_value": 135.0,
                "trend_direction": "improving",
                "confidence": 0.75,
                "timeframe_days": 90,
                "factors": ["Recent lifestyle changes", "Medication adherence"],
                "recommendations": ["Continue current blood pressure management", "Monitor regularly"]
            }
        }

class EarlyWarningResponse(BaseModel):
    """Early warning system response schema"""
    warning_type: str = Field(..., description="Type of warning")
    severity: RiskLevel = Field(..., description="Warning severity")
    probability: float = Field(..., description="Warning probability", ge=0.0, le=1.0)
    timeframe_days: int = Field(..., description="Warning timeframe")
    symptoms: List[str] = Field(default_factory=list, description="Associated symptoms")
    risk_factors: List[str] = Field(default_factory=list, description="Identified risk factors")
    recommendations: List[str] = Field(default_factory=list, description="Action recommendations")
    urgency: str = Field(..., description="Urgency level")

    class Config:
        schema_extra = {
            "example": {
                "warning_type": "High Blood Pressure",
                "severity": "high",
                "probability": 0.7,
                "timeframe_days": 7,
                "symptoms": ["Headache", "Shortness of breath"],
                "risk_factors": ["Lifestyle factors", "Family history"],
                "recommendations": ["Schedule doctor appointment", "Monitor blood pressure daily"],
                "urgency": "high"
            }
        }

class PreventiveRecommendationResponse(BaseModel):
    """Preventive care recommendation response schema"""
    recommendation_type: str = Field(..., description="Type of recommendation")
    priority: str = Field(..., description="Recommendation priority")
    description: str = Field(..., description="Recommendation description")
    rationale: str = Field(..., description="Recommendation rationale")
    expected_benefit: str = Field(..., description="Expected health benefit")
    timeframe: str = Field(..., description="Recommended timeframe")
    resources: List[str] = Field(default_factory=list, description="Available resources")
    confidence: float = Field(..., description="Recommendation confidence", ge=0.0, le=1.0)

    class Config:
        schema_extra = {
            "example": {
                "recommendation_type": "Colon Cancer Screening",
                "priority": "high",
                "description": "Schedule colonoscopy or stool-based screening",
                "rationale": "Recommended for adults 50+ to detect early signs of colon cancer",
                "expected_benefit": "Early detection of colorectal cancer",
                "timeframe": "Within 6 months",
                "resources": ["Gastroenterologist", "Primary care provider"],
                "confidence": 0.9
            }
        }

class PredictiveAnalyticsSummaryResponse(BaseModel):
    """Predictive analytics summary response schema"""
    total_assessments: int = Field(..., description="Total risk assessments performed")
    average_confidence: float = Field(..., description="Average assessment confidence", ge=0.0, le=1.0)
    risk_distribution: Dict[str, int] = Field(..., description="Risk level distribution")
    active_warnings: int = Field(..., description="Number of active early warnings")
    preventive_recommendations: int = Field(..., description="Number of preventive recommendations")

    class Config:
        schema_extra = {
            "example": {
                "total_assessments": 25,
                "average_confidence": 0.82,
                "risk_distribution": {
                    "low": 10,
                    "moderate": 8,
                    "high": 5,
                    "critical": 2
                },
                "active_warnings": 3,
                "preventive_recommendations": 12
            }
        } 
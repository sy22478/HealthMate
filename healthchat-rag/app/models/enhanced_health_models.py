"""
Enhanced Health Data Models for HealthMate

This module provides comprehensive health data models including:
- Enhanced user health profiles
- Detailed medication tracking
- Advanced symptom logging
- Health metrics aggregation
- AI interaction models
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Float, JSON, Date, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, date
from enum import Enum as PyEnum
import uuid
from app.base import Base
from app.utils.encryption_utils import field_encryption

# Enums for health data
class Gender(PyEnum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"

class BloodType(PyEnum):
    A_POSITIVE = "A+"
    A_NEGATIVE = "A-"
    B_POSITIVE = "B+"
    B_NEGATIVE = "B-"
    AB_POSITIVE = "AB+"
    AB_NEGATIVE = "AB-"
    O_POSITIVE = "O+"
    O_NEGATIVE = "O-"

class ActivityLevel(PyEnum):
    SEDENTARY = "sedentary"
    LIGHTLY_ACTIVE = "lightly_active"
    MODERATELY_ACTIVE = "moderately_active"
    VERY_ACTIVE = "very_active"
    EXTREMELY_ACTIVE = "extremely_active"

class SmokingStatus(PyEnum):
    NEVER_SMOKED = "never_smoked"
    FORMER_SMOKER = "former_smoker"
    CURRENT_SMOKER = "current_smoker"
    OCCASIONAL_SMOKER = "occasional_smoker"

class AlcoholConsumption(PyEnum):
    NEVER = "never"
    OCCASIONAL = "occasional"
    MODERATE = "moderate"
    HEAVY = "heavy"
    FORMER_DRINKER = "former_drinker"

class MedicationStatus(PyEnum):
    ACTIVE = "active"
    DISCONTINUED = "discontinued"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"

class SymptomSeverity(PyEnum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"

class HealthGoalStatus(PyEnum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    ON_HOLD = "on_hold"

class ConversationType(PyEnum):
    GENERAL_HEALTH = "general_health"
    SYMPTOM_DISCUSSION = "symptom_discussion"
    MEDICATION_QUERY = "medication_query"
    TREATMENT_PLAN = "treatment_plan"
    EMERGENCY = "emergency"

class FeedbackType(PyEnum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"

class UserHealthProfile(Base):
    """Comprehensive user health profile model"""
    __tablename__ = "user_health_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Basic health information
    height_cm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    bmi = Column(Float, nullable=True)
    body_fat_percentage = Column(Float, nullable=True)
    muscle_mass_kg = Column(Float, nullable=True)
    
    # Demographics
    gender = Column(Enum(Gender), nullable=True)
    blood_type = Column(Enum(BloodType), nullable=True)
    ethnicity = Column(String(100), nullable=True)  # Encrypted
    occupation = Column(String(200), nullable=True)  # Encrypted
    
    # Lifestyle factors
    activity_level = Column(Enum(ActivityLevel), nullable=True)
    smoking_status = Column(Enum(SmokingStatus), nullable=True)
    alcohol_consumption = Column(Enum(AlcoholConsumption), nullable=True)
    exercise_frequency = Column(String(50), nullable=True)  # Encrypted
    sleep_hours_per_night = Column(Float, nullable=True)
    
    # Medical history
    primary_care_physician = Column(String(200), nullable=True)  # Encrypted
    specialist_physicians = Column(Text, nullable=True)  # Encrypted JSON
    hospital_preferences = Column(Text, nullable=True)  # Encrypted JSON
    insurance_provider = Column(String(200), nullable=True)  # Encrypted
    insurance_policy_number = Column(String(100), nullable=True)  # Encrypted
    
    # Family history
    family_medical_history = Column(Text, nullable=True)  # Encrypted JSON
    
    # Allergies and sensitivities
    food_allergies = Column(Text, nullable=True)  # Encrypted JSON
    drug_allergies = Column(Text, nullable=True)  # Encrypted JSON
    environmental_allergies = Column(Text, nullable=True)  # Encrypted JSON
    
    # Chronic conditions
    chronic_conditions = Column(Text, nullable=True)  # Encrypted JSON
    mental_health_conditions = Column(Text, nullable=True)  # Encrypted JSON
    
    # Emergency information
    emergency_contacts = Column(Text, nullable=True)  # Encrypted JSON
    advance_directives = Column(Text, nullable=True)  # Encrypted JSON
    organ_donor_status = Column(Boolean, nullable=True)
    
    # Health goals and preferences
    health_goals = Column(Text, nullable=True)  # Encrypted JSON
    treatment_preferences = Column(Text, nullable=True)  # Encrypted JSON
    communication_preferences = Column(Text, nullable=True)  # Encrypted JSON
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_health_assessment = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="health_profile")
    medications = relationship("EnhancedMedication", back_populates="health_profile")
    symptoms = relationship("EnhancedSymptomLog", back_populates="health_profile")
    health_metrics = relationship("HealthMetricsAggregation", back_populates="health_profile")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._encrypt_sensitive_fields()
    
    def _encrypt_sensitive_fields(self):
        """Encrypt sensitive fields before saving"""
        sensitive_fields = [
            'ethnicity', 'occupation', 'specialist_physicians', 'hospital_preferences',
            'insurance_provider', 'insurance_policy_number', 'family_medical_history',
            'food_allergies', 'drug_allergies', 'environmental_allergies',
            'chronic_conditions', 'mental_health_conditions', 'emergency_contacts',
            'advance_directives', 'health_goals', 'treatment_preferences',
            'communication_preferences'
        ]
        field_encryption.encrypt_model_fields(self, sensitive_fields)
    
    def decrypt_sensitive_fields(self):
        """Decrypt sensitive fields for display"""
        sensitive_fields = [
            'ethnicity', 'occupation', 'specialist_physicians', 'hospital_preferences',
            'insurance_provider', 'insurance_policy_number', 'family_medical_history',
            'food_allergies', 'drug_allergies', 'environmental_allergies',
            'chronic_conditions', 'mental_health_conditions', 'emergency_contacts',
            'advance_directives', 'health_goals', 'treatment_preferences',
            'communication_preferences'
        ]
        field_encryption.decrypt_model_fields(self, sensitive_fields)
    
    def calculate_bmi(self):
        """Calculate BMI if height and weight are available"""
        if self.height_cm and self.weight_kg:
            height_m = self.height_cm / 100
            self.bmi = self.weight_kg / (height_m ** 2)
        return self.bmi
    
    def to_dict(self, include_sensitive=False):
        """Convert to dictionary, optionally including decrypted sensitive data"""
        profile_dict = {
            'id': self.id,
            'user_id': self.user_id,
            'height_cm': self.height_cm,
            'weight_kg': self.weight_kg,
            'bmi': self.bmi,
            'body_fat_percentage': self.body_fat_percentage,
            'muscle_mass_kg': self.muscle_mass_kg,
            'gender': self.gender.value if self.gender else None,
            'blood_type': self.blood_type.value if self.blood_type else None,
            'activity_level': self.activity_level.value if self.activity_level else None,
            'smoking_status': self.smoking_status.value if self.smoking_status else None,
            'alcohol_consumption': self.alcohol_consumption.value if self.alcohol_consumption else None,
            'sleep_hours_per_night': self.sleep_hours_per_night,
            'organ_donor_status': self.organ_donor_status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_health_assessment': self.last_health_assessment.isoformat() if self.last_health_assessment else None
        }
        
        if include_sensitive:
            self.decrypt_sensitive_fields()
            profile_dict.update({
                'ethnicity': self.ethnicity,
                'occupation': self.occupation,
                'specialist_physicians': self.specialist_physicians,
                'hospital_preferences': self.hospital_preferences,
                'insurance_provider': self.insurance_provider,
                'insurance_policy_number': self.insurance_policy_number,
                'family_medical_history': self.family_medical_history,
                'food_allergies': self.food_allergies,
                'drug_allergies': self.drug_allergies,
                'environmental_allergies': self.environmental_allergies,
                'chronic_conditions': self.chronic_conditions,
                'mental_health_conditions': self.mental_health_conditions,
                'emergency_contacts': self.emergency_contacts,
                'advance_directives': self.advance_directives,
                'health_goals': self.health_goals,
                'treatment_preferences': self.treatment_preferences,
                'communication_preferences': self.communication_preferences
            })
        
        return profile_dict

class EnhancedMedication(Base):
    """Enhanced medication tracking model"""
    __tablename__ = "enhanced_medications"
    
    id = Column(Integer, primary_key=True, index=True)
    health_profile_id = Column(Integer, ForeignKey("user_health_profiles.id"), nullable=False)
    
    # Medication details
    medication_name = Column(String(200), nullable=False)
    generic_name = Column(String(200), nullable=True)
    medication_type = Column(String(100), nullable=True)  # prescription, otc, supplement
    dosage_form = Column(String(100), nullable=True)  # tablet, capsule, liquid, etc.
    strength = Column(String(100), nullable=False)  # 10mg, 500mg, etc.
    dosage_instructions = Column(Text, nullable=False)  # Encrypted
    frequency = Column(String(100), nullable=False)  # twice daily, as needed, etc.
    
    # Prescription information
    prescribed_by = Column(String(200), nullable=True)  # Encrypted
    prescription_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)
    refill_date = Column(Date, nullable=True)
    refills_remaining = Column(Integer, nullable=True)
    pharmacy = Column(String(200), nullable=True)  # Encrypted
    
    # Status and tracking
    status = Column(Enum(MedicationStatus), default=MedicationStatus.ACTIVE)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    reason_for_discontinuation = Column(Text, nullable=True)  # Encrypted
    
    # Side effects and monitoring
    side_effects = Column(Text, nullable=True)  # Encrypted JSON
    effectiveness_rating = Column(Integer, nullable=True)  # 1-10 scale
    adherence_rate = Column(Float, nullable=True)  # 0.0-100.0
    notes = Column(Text, nullable=True)  # Encrypted
    
    # Interactions and contraindications
    drug_interactions = Column(Text, nullable=True)  # Encrypted JSON
    contraindications = Column(Text, nullable=True)  # Encrypted JSON
    warnings = Column(Text, nullable=True)  # Encrypted
    
    # Cost and insurance
    cost_per_unit = Column(Float, nullable=True)
    insurance_coverage = Column(Boolean, nullable=True)
    copay_amount = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    health_profile = relationship("UserHealthProfile", back_populates="medications")
    medication_logs = relationship("MedicationDoseLog", back_populates="medication")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._encrypt_sensitive_fields()
    
    def _encrypt_sensitive_fields(self):
        """Encrypt sensitive fields before saving"""
        sensitive_fields = [
            'dosage_instructions', 'prescribed_by', 'pharmacy',
            'reason_for_discontinuation', 'side_effects', 'notes',
            'drug_interactions', 'contraindications', 'warnings'
        ]
        field_encryption.encrypt_model_fields(self, sensitive_fields)
    
    def decrypt_sensitive_fields(self):
        """Decrypt sensitive fields for display"""
        sensitive_fields = [
            'dosage_instructions', 'prescribed_by', 'pharmacy',
            'reason_for_discontinuation', 'side_effects', 'notes',
            'drug_interactions', 'contraindications', 'warnings'
        ]
        field_encryption.decrypt_model_fields(self, sensitive_fields)
    
    def to_dict(self, include_sensitive=False):
        """Convert to dictionary, optionally including decrypted sensitive data"""
        medication_dict = {
            'id': self.id,
            'health_profile_id': self.health_profile_id,
            'medication_name': self.medication_name,
            'generic_name': self.generic_name,
            'medication_type': self.medication_type,
            'dosage_form': self.dosage_form,
            'strength': self.strength,
            'frequency': self.frequency,
            'prescription_date': self.prescription_date.isoformat() if self.prescription_date else None,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'refill_date': self.refill_date.isoformat() if self.refill_date else None,
            'refills_remaining': self.refills_remaining,
            'status': self.status.value if self.status else None,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'effectiveness_rating': self.effectiveness_rating,
            'adherence_rate': self.adherence_rate,
            'cost_per_unit': self.cost_per_unit,
            'insurance_coverage': self.insurance_coverage,
            'copay_amount': self.copay_amount,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_sensitive:
            self.decrypt_sensitive_fields()
            medication_dict.update({
                'dosage_instructions': self.dosage_instructions,
                'prescribed_by': self.prescribed_by,
                'pharmacy': self.pharmacy,
                'reason_for_discontinuation': self.reason_for_discontinuation,
                'side_effects': self.side_effects,
                'notes': self.notes,
                'drug_interactions': self.drug_interactions,
                'contraindications': self.contraindications,
                'warnings': self.warnings
            })
        
        return medication_dict

class MedicationDoseLog(Base):
    """Detailed medication dose logging"""
    __tablename__ = "medication_dose_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    medication_id = Column(Integer, ForeignKey("enhanced_medications.id"), nullable=False)
    
    # Dose information
    dose_taken = Column(String(100), nullable=False)  # "10mg", "1 tablet", etc.
    scheduled_time = Column(DateTime, nullable=True)
    actual_time_taken = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Adherence tracking
    taken_as_prescribed = Column(Boolean, nullable=True)
    reason_for_deviation = Column(Text, nullable=True)  # Encrypted
    missed_dose = Column(Boolean, default=False)
    
    # Side effects and effectiveness
    side_effects_experienced = Column(Text, nullable=True)  # Encrypted JSON
    effectiveness_rating = Column(Integer, nullable=True)  # 1-10 scale
    notes = Column(Text, nullable=True)  # Encrypted
    
    # Location and context
    location_taken = Column(String(200), nullable=True)  # Encrypted
    taken_with_food = Column(Boolean, nullable=True)
    other_medications_taken = Column(Text, nullable=True)  # Encrypted JSON
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    medication = relationship("EnhancedMedication", back_populates="medication_logs")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._encrypt_sensitive_fields()
    
    def _encrypt_sensitive_fields(self):
        """Encrypt sensitive fields before saving"""
        sensitive_fields = [
            'reason_for_deviation', 'side_effects_experienced', 'notes',
            'location_taken', 'other_medications_taken'
        ]
        field_encryption.encrypt_model_fields(self, sensitive_fields)
    
    def decrypt_sensitive_fields(self):
        """Decrypt sensitive fields for display"""
        sensitive_fields = [
            'reason_for_deviation', 'side_effects_experienced', 'notes',
            'location_taken', 'other_medications_taken'
        ]
        field_encryption.decrypt_model_fields(self, sensitive_fields)
    
    def to_dict(self, include_sensitive=False):
        """Convert to dictionary, optionally including decrypted sensitive data"""
        log_dict = {
            'id': self.id,
            'medication_id': self.medication_id,
            'dose_taken': self.dose_taken,
            'scheduled_time': self.scheduled_time.isoformat() if self.scheduled_time else None,
            'actual_time_taken': self.actual_time_taken.isoformat() if self.actual_time_taken else None,
            'taken_as_prescribed': self.taken_as_prescribed,
            'missed_dose': self.missed_dose,
            'effectiveness_rating': self.effectiveness_rating,
            'taken_with_food': self.taken_with_food,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if include_sensitive:
            self.decrypt_sensitive_fields()
            log_dict.update({
                'reason_for_deviation': self.reason_for_deviation,
                'side_effects_experienced': self.side_effects_experienced,
                'notes': self.notes,
                'location_taken': self.location_taken,
                'other_medications_taken': self.other_medications_taken
            })
        
        return log_dict

class EnhancedSymptomLog(Base):
    """Enhanced symptom logging model"""
    __tablename__ = "enhanced_symptom_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    health_profile_id = Column(Integer, ForeignKey("user_health_profiles.id"), nullable=False)
    
    # Symptom details
    symptom_name = Column(String(200), nullable=False)
    symptom_category = Column(String(100), nullable=True)  # pain, gastrointestinal, respiratory, etc.
    severity = Column(Enum(SymptomSeverity), nullable=False)
    pain_level = Column(Integer, nullable=True)  # 0-10 scale
    
    # Detailed description
    description = Column(Text, nullable=True)  # Encrypted
    location = Column(String(200), nullable=True)  # Encrypted
    duration = Column(String(100), nullable=True)  # Encrypted
    frequency = Column(String(100), nullable=True)  # Encrypted
    
    # Context and triggers
    triggers = Column(Text, nullable=True)  # Encrypted JSON
    aggravating_factors = Column(Text, nullable=True)  # Encrypted JSON
    relieving_factors = Column(Text, nullable=True)  # Encrypted JSON
    associated_symptoms = Column(Text, nullable=True)  # Encrypted JSON
    
    # Impact assessment
    impact_on_daily_activities = Column(String(100), nullable=True)  # none, mild, moderate, severe
    impact_on_sleep = Column(String(100), nullable=True)  # none, mild, moderate, severe
    impact_on_mood = Column(String(100), nullable=True)  # none, mild, moderate, severe
    
    # Treatment and management
    treatments_tried = Column(Text, nullable=True)  # Encrypted JSON
    treatment_effectiveness = Column(Text, nullable=True)  # Encrypted JSON
    medications_taken = Column(Text, nullable=True)  # Encrypted JSON
    
    # Medical context
    related_conditions = Column(Text, nullable=True)  # Encrypted JSON
    doctor_consulted = Column(Boolean, default=False)
    doctor_notes = Column(Text, nullable=True)  # Encrypted
    emergency_visit = Column(Boolean, default=False)
    
    # Timestamps
    onset_time = Column(DateTime, nullable=True)
    peak_time = Column(DateTime, nullable=True)
    resolution_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    health_profile = relationship("UserHealthProfile", back_populates="symptoms")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._encrypt_sensitive_fields()
    
    def _encrypt_sensitive_fields(self):
        """Encrypt sensitive fields before saving"""
        sensitive_fields = [
            'description', 'location', 'duration', 'frequency', 'triggers',
            'aggravating_factors', 'relieving_factors', 'associated_symptoms',
            'treatments_tried', 'treatment_effectiveness', 'medications_taken',
            'related_conditions', 'doctor_notes'
        ]
        field_encryption.encrypt_model_fields(self, sensitive_fields)
    
    def decrypt_sensitive_fields(self):
        """Decrypt sensitive fields for display"""
        sensitive_fields = [
            'description', 'location', 'duration', 'frequency', 'triggers',
            'aggravating_factors', 'relieving_factors', 'associated_symptoms',
            'treatments_tried', 'treatment_effectiveness', 'medications_taken',
            'related_conditions', 'doctor_notes'
        ]
        field_encryption.decrypt_model_fields(self, sensitive_fields)
    
    def to_dict(self, include_sensitive=False):
        """Convert to dictionary, optionally including decrypted sensitive data"""
        symptom_dict = {
            'id': self.id,
            'health_profile_id': self.health_profile_id,
            'symptom_name': self.symptom_name,
            'symptom_category': self.symptom_category,
            'severity': self.severity.value if self.severity else None,
            'pain_level': self.pain_level,
            'impact_on_daily_activities': self.impact_on_daily_activities,
            'impact_on_sleep': self.impact_on_sleep,
            'impact_on_mood': self.impact_on_mood,
            'doctor_consulted': self.doctor_consulted,
            'emergency_visit': self.emergency_visit,
            'onset_time': self.onset_time.isoformat() if self.onset_time else None,
            'peak_time': self.peak_time.isoformat() if self.peak_time else None,
            'resolution_time': self.resolution_time.isoformat() if self.resolution_time else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_sensitive:
            self.decrypt_sensitive_fields()
            symptom_dict.update({
                'description': self.description,
                'location': self.location,
                'duration': self.duration,
                'frequency': self.frequency,
                'triggers': self.triggers,
                'aggravating_factors': self.aggravating_factors,
                'relieving_factors': self.relieving_factors,
                'associated_symptoms': self.associated_symptoms,
                'treatments_tried': self.treatments_tried,
                'treatment_effectiveness': self.treatment_effectiveness,
                'medications_taken': self.medications_taken,
                'related_conditions': self.related_conditions,
                'doctor_notes': self.doctor_notes
            })
        
        return symptom_dict

class HealthMetricsAggregation(Base):
    """Health metrics aggregation table for analytics"""
    __tablename__ = "health_metrics_aggregations"
    
    id = Column(Integer, primary_key=True, index=True)
    health_profile_id = Column(Integer, ForeignKey("user_health_profiles.id"), nullable=False)
    
    # Aggregation period
    aggregation_period = Column(String(20), nullable=False)  # daily, weekly, monthly
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Health metrics
    avg_blood_pressure_systolic = Column(Float, nullable=True)
    avg_blood_pressure_diastolic = Column(Float, nullable=True)
    min_blood_pressure_systolic = Column(Float, nullable=True)
    max_blood_pressure_systolic = Column(Float, nullable=True)
    min_blood_pressure_diastolic = Column(Float, nullable=True)
    max_blood_pressure_diastolic = Column(Float, nullable=True)
    
    avg_heart_rate = Column(Float, nullable=True)
    min_heart_rate = Column(Float, nullable=True)
    max_heart_rate = Column(Float, nullable=True)
    resting_heart_rate = Column(Float, nullable=True)
    
    avg_weight = Column(Float, nullable=True)
    weight_change = Column(Float, nullable=True)
    bmi_trend = Column(Float, nullable=True)
    
    avg_blood_sugar = Column(Float, nullable=True)
    min_blood_sugar = Column(Float, nullable=True)
    max_blood_sugar = Column(Float, nullable=True)
    
    avg_temperature = Column(Float, nullable=True)
    min_temperature = Column(Float, nullable=True)
    max_temperature = Column(Float, nullable=True)
    
    # Activity metrics
    total_steps = Column(Integer, nullable=True)
    avg_steps_per_day = Column(Float, nullable=True)
    total_calories_burned = Column(Float, nullable=True)
    avg_calories_burned_per_day = Column(Float, nullable=True)
    total_exercise_minutes = Column(Integer, nullable=True)
    avg_exercise_minutes_per_day = Column(Float, nullable=True)
    
    # Sleep metrics
    avg_sleep_hours = Column(Float, nullable=True)
    total_sleep_hours = Column(Float, nullable=True)
    sleep_quality_score = Column(Float, nullable=True)  # 0-100 scale
    
    # Medication adherence
    medication_adherence_rate = Column(Float, nullable=True)  # 0-100 percentage
    total_medications_taken = Column(Integer, nullable=True)
    total_medications_scheduled = Column(Integer, nullable=True)
    missed_doses = Column(Integer, nullable=True)
    
    # Symptom tracking
    total_symptoms_logged = Column(Integer, nullable=True)
    avg_symptom_severity = Column(Float, nullable=True)
    most_common_symptom = Column(String(200), nullable=True)
    symptom_frequency = Column(Text, nullable=True)  # Encrypted JSON
    
    # Health score
    overall_health_score = Column(Float, nullable=True)  # 0-100 scale
    health_score_trend = Column(Float, nullable=True)  # positive/negative change
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    health_profile = relationship("UserHealthProfile", back_populates="health_metrics")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._encrypt_sensitive_fields()
    
    def _encrypt_sensitive_fields(self):
        """Encrypt sensitive fields before saving"""
        sensitive_fields = ['symptom_frequency']
        field_encryption.encrypt_model_fields(self, sensitive_fields)
    
    def decrypt_sensitive_fields(self):
        """Decrypt sensitive fields for display"""
        sensitive_fields = ['symptom_frequency']
        field_encryption.decrypt_model_fields(self, sensitive_fields)
    
    def calculate_health_score(self):
        """Calculate overall health score based on various metrics"""
        score = 0
        factors = 0
        
        # Blood pressure score (normal range: 90-140/60-90)
        if self.avg_blood_pressure_systolic and self.avg_blood_pressure_diastolic:
            bp_score = 100
            if self.avg_blood_pressure_systolic < 90 or self.avg_blood_pressure_systolic > 140:
                bp_score -= 20
            if self.avg_blood_pressure_diastolic < 60 or self.avg_blood_pressure_diastolic > 90:
                bp_score -= 20
            score += bp_score
            factors += 1
        
        # Heart rate score (normal range: 60-100)
        if self.avg_heart_rate:
            hr_score = 100
            if self.avg_heart_rate < 60 or self.avg_heart_rate > 100:
                hr_score -= 30
            score += hr_score
            factors += 1
        
        # BMI score (normal range: 18.5-24.9)
        if self.bmi_trend:
            bmi_score = 100
            if self.bmi_trend < 18.5 or self.bmi_trend > 24.9:
                bmi_score -= 25
            score += bmi_score
            factors += 1
        
        # Medication adherence score
        if self.medication_adherence_rate:
            adherence_score = self.medication_adherence_rate
            score += adherence_score
            factors += 1
        
        # Sleep score
        if self.avg_sleep_hours:
            sleep_score = 100
            if self.avg_sleep_hours < 6 or self.avg_sleep_hours > 9:
                sleep_score -= 30
            score += sleep_score
            factors += 1
        
        # Activity score
        if self.avg_steps_per_day:
            activity_score = min(100, (self.avg_steps_per_day / 10000) * 100)
            score += activity_score
            factors += 1
        
        if factors > 0:
            self.overall_health_score = score / factors
        else:
            self.overall_health_score = None
        
        return self.overall_health_score
    
    def to_dict(self, include_sensitive=False):
        """Convert to dictionary, optionally including decrypted sensitive data"""
        metrics_dict = {
            'id': self.id,
            'health_profile_id': self.health_profile_id,
            'aggregation_period': self.aggregation_period,
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'avg_blood_pressure_systolic': self.avg_blood_pressure_systolic,
            'avg_blood_pressure_diastolic': self.avg_blood_pressure_diastolic,
            'min_blood_pressure_systolic': self.min_blood_pressure_systolic,
            'max_blood_pressure_systolic': self.max_blood_pressure_systolic,
            'min_blood_pressure_diastolic': self.min_blood_pressure_diastolic,
            'max_blood_pressure_diastolic': self.max_blood_pressure_diastolic,
            'avg_heart_rate': self.avg_heart_rate,
            'min_heart_rate': self.min_heart_rate,
            'max_heart_rate': self.max_heart_rate,
            'resting_heart_rate': self.resting_heart_rate,
            'avg_weight': self.avg_weight,
            'weight_change': self.weight_change,
            'bmi_trend': self.bmi_trend,
            'avg_blood_sugar': self.avg_blood_sugar,
            'min_blood_sugar': self.min_blood_sugar,
            'max_blood_sugar': self.max_blood_sugar,
            'avg_temperature': self.avg_temperature,
            'min_temperature': self.min_temperature,
            'max_temperature': self.max_temperature,
            'total_steps': self.total_steps,
            'avg_steps_per_day': self.avg_steps_per_day,
            'total_calories_burned': self.total_calories_burned,
            'avg_calories_burned_per_day': self.avg_calories_burned_per_day,
            'total_exercise_minutes': self.total_exercise_minutes,
            'avg_exercise_minutes_per_day': self.avg_exercise_minutes_per_day,
            'avg_sleep_hours': self.avg_sleep_hours,
            'total_sleep_hours': self.total_sleep_hours,
            'sleep_quality_score': self.sleep_quality_score,
            'medication_adherence_rate': self.medication_adherence_rate,
            'total_medications_taken': self.total_medications_taken,
            'total_medications_scheduled': self.total_medications_scheduled,
            'missed_doses': self.missed_doses,
            'total_symptoms_logged': self.total_symptoms_logged,
            'avg_symptom_severity': self.avg_symptom_severity,
            'most_common_symptom': self.most_common_symptom,
            'overall_health_score': self.overall_health_score,
            'health_score_trend': self.health_score_trend,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_sensitive:
            self.decrypt_sensitive_fields()
            metrics_dict.update({
                'symptom_frequency': self.symptom_frequency
            })
        
        return metrics_dict 


class ConversationHistory(Base):
    """Enhanced conversation history storage model"""
    __tablename__ = "conversation_histories"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    conversation_id = Column(String(100), nullable=False, index=True)  # UUID for conversation grouping
    
    # Message details
    message_type = Column(String(50), nullable=False)  # user_message, ai_response, system_message
    content = Column(Text, nullable=False)  # Encrypted
    content_summary = Column(Text, nullable=True)  # Encrypted - for quick reference
    
    # Context and metadata
    conversation_type = Column(Enum(ConversationType), nullable=True)
    context_sources = Column(Text, nullable=True)  # Encrypted JSON - RAG sources used
    confidence_score = Column(Float, nullable=True)  # AI confidence in response
    response_time_ms = Column(Integer, nullable=True)  # Response generation time
    
    # User interaction tracking
    user_feedback = Column(Enum(FeedbackType), nullable=True)
    feedback_comment = Column(Text, nullable=True)  # Encrypted
    user_rating = Column(Integer, nullable=True)  # 1-5 scale
    
    # Medical context
    health_context = Column(Text, nullable=True)  # Encrypted JSON - relevant health data
    symptom_mentions = Column(Text, nullable=True)  # Encrypted JSON - symptoms discussed
    medication_mentions = Column(Text, nullable=True)  # Encrypted JSON - medications discussed
    urgency_level = Column(String(20), nullable=True)  # low, medium, high, emergency
    
    # AI processing metadata
    model_used = Column(String(100), nullable=True)  # gpt-4, gpt-3.5-turbo, etc.
    tokens_used = Column(Integer, nullable=True)
    processing_metadata = Column(Text, nullable=True)  # Encrypted JSON - additional AI metadata
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="conversation_history")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._encrypt_sensitive_fields()
    
    def _encrypt_sensitive_fields(self):
        """Encrypt sensitive fields before saving"""
        sensitive_fields = [
            'content', 'content_summary', 'context_sources', 'feedback_comment',
            'health_context', 'symptom_mentions', 'medication_mentions', 'processing_metadata'
        ]
        field_encryption.encrypt_model_fields(self, sensitive_fields)
    
    def decrypt_sensitive_fields(self):
        """Decrypt sensitive fields for display"""
        sensitive_fields = [
            'content', 'content_summary', 'context_sources', 'feedback_comment',
            'health_context', 'symptom_mentions', 'medication_mentions', 'processing_metadata'
        ]
        field_encryption.decrypt_model_fields(self, sensitive_fields)
    
    def to_dict(self, include_sensitive=False):
        """Convert to dictionary, optionally including decrypted sensitive data"""
        history_dict = {
            'id': self.id,
            'user_id': self.user_id,
            'conversation_id': self.conversation_id,
            'message_type': self.message_type,
            'conversation_type': self.conversation_type.value if self.conversation_type else None,
            'confidence_score': self.confidence_score,
            'response_time_ms': self.response_time_ms,
            'user_feedback': self.user_feedback.value if self.user_feedback else None,
            'user_rating': self.user_rating,
            'urgency_level': self.urgency_level,
            'model_used': self.model_used,
            'tokens_used': self.tokens_used,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_sensitive:
            self.decrypt_sensitive_fields()
            history_dict.update({
                'content': self.content,
                'content_summary': self.content_summary,
                'context_sources': self.context_sources,
                'feedback_comment': self.feedback_comment,
                'health_context': self.health_context,
                'symptom_mentions': self.symptom_mentions,
                'medication_mentions': self.medication_mentions,
                'processing_metadata': self.processing_metadata
            })
        
        return history_dict


class AIResponseCache(Base):
    """AI response caching model for performance optimization"""
    __tablename__ = "ai_response_caches"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Cache key components
    query_hash = Column(String(64), nullable=False, index=True)  # SHA256 hash of query
    user_context_hash = Column(String(64), nullable=True, index=True)  # Hash of user context
    model_version = Column(String(100), nullable=False)
    
    # Cached response
    cached_response = Column(Text, nullable=False)  # Encrypted
    response_metadata = Column(Text, nullable=True)  # Encrypted JSON
    
    # Cache management
    cache_hits = Column(Integer, default=0)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # Cache expiration
    
    # Quality metrics
    response_quality_score = Column(Float, nullable=True)  # 0-1 scale
    user_satisfaction_score = Column(Float, nullable=True)  # Average user rating
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._encrypt_sensitive_fields()
    
    def _encrypt_sensitive_fields(self):
        """Encrypt sensitive fields before saving"""
        sensitive_fields = ['cached_response', 'response_metadata']
        field_encryption.encrypt_model_fields(self, sensitive_fields)
    
    def decrypt_sensitive_fields(self):
        """Decrypt sensitive fields for display"""
        sensitive_fields = ['cached_response', 'response_metadata']
        field_encryption.decrypt_model_fields(self, sensitive_fields)
    
    def to_dict(self, include_sensitive=False):
        """Convert to dictionary, optionally including decrypted sensitive data"""
        cache_dict = {
            'id': self.id,
            'query_hash': self.query_hash,
            'user_context_hash': self.user_context_hash,
            'model_version': self.model_version,
            'cache_hits': self.cache_hits,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'response_quality_score': self.response_quality_score,
            'user_satisfaction_score': self.user_satisfaction_score
        }
        
        if include_sensitive:
            self.decrypt_sensitive_fields()
            cache_dict.update({
                'cached_response': self.cached_response,
                'response_metadata': self.response_metadata
            })
        
        return cache_dict


class UserPreference(Base):
    """User preference tracking model for personalization"""
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # Communication preferences
    preferred_language = Column(String(10), default="en")
    communication_style = Column(String(50), nullable=True)  # formal, casual, technical, simple
    response_length_preference = Column(String(20), nullable=True)  # short, medium, detailed
    notification_frequency = Column(String(20), nullable=True)  # immediate, daily, weekly
    
    # Health information preferences
    health_detail_level = Column(String(20), nullable=True)  # basic, detailed, comprehensive
    medical_terminology_level = Column(String(20), nullable=True)  # simple, moderate, advanced
    include_statistics = Column(Boolean, default=True)
    include_recommendations = Column(Boolean, default=True)
    
    # Privacy preferences
    data_sharing_level = Column(String(20), default="minimal")  # minimal, standard, comprehensive
    allow_analytics = Column(Boolean, default=True)
    allow_research_use = Column(Boolean, default=False)
    
    # AI interaction preferences
    ai_personality = Column(String(50), nullable=True)  # friendly, professional, empathetic, direct
    conversation_memory_duration = Column(Integer, nullable=True)  # days to remember context
    auto_suggestions = Column(Boolean, default=True)
    proactive_alerts = Column(Boolean, default=True)
    
    # Accessibility preferences
    font_size = Column(String(20), default="medium")  # small, medium, large
    color_scheme = Column(String(20), default="default")  # default, high_contrast, dark_mode
    screen_reader_support = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="preferences")
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'preferred_language': self.preferred_language,
            'communication_style': self.communication_style,
            'response_length_preference': self.response_length_preference,
            'notification_frequency': self.notification_frequency,
            'health_detail_level': self.health_detail_level,
            'medical_terminology_level': self.medical_terminology_level,
            'include_statistics': self.include_statistics,
            'include_recommendations': self.include_recommendations,
            'data_sharing_level': self.data_sharing_level,
            'allow_analytics': self.allow_analytics,
            'allow_research_use': self.allow_research_use,
            'ai_personality': self.ai_personality,
            'conversation_memory_duration': self.conversation_memory_duration,
            'auto_suggestions': self.auto_suggestions,
            'proactive_alerts': self.proactive_alerts,
            'font_size': self.font_size,
            'color_scheme': self.color_scheme,
            'screen_reader_support': self.screen_reader_support,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class UserFeedback(Base):
    """Enhanced user feedback and rating model"""
    __tablename__ = "user_feedbacks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    conversation_id = Column(String(100), nullable=True, index=True)
    response_id = Column(Integer, nullable=True)  # Reference to specific AI response
    
    # Feedback details
    feedback_type = Column(Enum(FeedbackType), nullable=False)
    rating = Column(Integer, nullable=True)  # 1-5 scale
    detailed_feedback = Column(Text, nullable=True)  # Encrypted
    category = Column(String(100), nullable=True)  # accuracy, helpfulness, clarity, etc.
    
    # Context information
    context = Column(Text, nullable=True)  # Encrypted JSON - what was being discussed
    user_expectation = Column(Text, nullable=True)  # Encrypted - what user expected
    actual_outcome = Column(Text, nullable=True)  # Encrypted - what actually happened
    
    # Impact assessment
    impact_on_health_decision = Column(String(50), nullable=True)  # positive, negative, neutral
    action_taken = Column(Text, nullable=True)  # Encrypted - what user did based on response
    follow_up_needed = Column(Boolean, default=False)
    
    # Quality metrics
    response_accuracy = Column(Integer, nullable=True)  # 1-5 scale
    response_helpfulness = Column(Integer, nullable=True)  # 1-5 scale
    response_clarity = Column(Integer, nullable=True)  # 1-5 scale
    overall_satisfaction = Column(Integer, nullable=True)  # 1-5 scale
    
    # Follow-up tracking
    follow_up_completed = Column(Boolean, default=False)
    follow_up_notes = Column(Text, nullable=True)  # Encrypted
    resolution_status = Column(String(50), nullable=True)  # resolved, pending, escalated
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="feedbacks")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._encrypt_sensitive_fields()
    
    def _encrypt_sensitive_fields(self):
        """Encrypt sensitive fields before saving"""
        sensitive_fields = [
            'detailed_feedback', 'context', 'user_expectation', 'actual_outcome',
            'action_taken', 'follow_up_notes'
        ]
        field_encryption.encrypt_model_fields(self, sensitive_fields)
    
    def decrypt_sensitive_fields(self):
        """Decrypt sensitive fields for display"""
        sensitive_fields = [
            'detailed_feedback', 'context', 'user_expectation', 'actual_outcome',
            'action_taken', 'follow_up_notes'
        ]
        field_encryption.decrypt_model_fields(self, sensitive_fields)
    
    def to_dict(self, include_sensitive=False):
        """Convert to dictionary, optionally including decrypted sensitive data"""
        feedback_dict = {
            'id': self.id,
            'user_id': self.user_id,
            'conversation_id': self.conversation_id,
            'response_id': self.response_id,
            'feedback_type': self.feedback_type.value if self.feedback_type else None,
            'rating': self.rating,
            'category': self.category,
            'impact_on_health_decision': self.impact_on_health_decision,
            'follow_up_needed': self.follow_up_needed,
            'response_accuracy': self.response_accuracy,
            'response_helpfulness': self.response_helpfulness,
            'response_clarity': self.response_clarity,
            'overall_satisfaction': self.overall_satisfaction,
            'follow_up_completed': self.follow_up_completed,
            'resolution_status': self.resolution_status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_sensitive:
            self.decrypt_sensitive_fields()
            feedback_dict.update({
                'detailed_feedback': self.detailed_feedback,
                'context': self.context,
                'user_expectation': self.user_expectation,
                'actual_outcome': self.actual_outcome,
                'action_taken': self.action_taken,
                'follow_up_notes': self.follow_up_notes
            })
        
        return feedback_dict 
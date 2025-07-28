"""
Health Data Pydantic Schemas
Comprehensive schemas for health data, metrics, and medical information
"""
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime, date
from enum import Enum

class BloodType(str, Enum):
    """Blood type enumeration"""
    A_POSITIVE = "A+"
    A_NEGATIVE = "A-"
    B_POSITIVE = "B+"
    B_NEGATIVE = "B-"
    AB_POSITIVE = "AB+"
    AB_NEGATIVE = "AB-"
    O_POSITIVE = "O+"
    O_NEGATIVE = "O-"

class Gender(str, Enum):
    """Gender enumeration"""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"

class ActivityLevel(str, Enum):
    """Activity level enumeration"""
    SEDENTARY = "sedentary"
    LIGHTLY_ACTIVE = "lightly_active"
    MODERATELY_ACTIVE = "moderately_active"
    VERY_ACTIVE = "very_active"
    EXTREMELY_ACTIVE = "extremely_active"

class SmokingStatus(str, Enum):
    """Smoking status enumeration"""
    NEVER_SMOKED = "never_smoked"
    FORMER_SMOKER = "former_smoker"
    CURRENT_SMOKER = "current_smoker"
    OCCASIONAL_SMOKER = "occasional_smoker"

class AlcoholConsumption(str, Enum):
    """Alcohol consumption enumeration"""
    NEVER = "never"
    OCCASIONAL = "occasional"
    MODERATE = "moderate"
    HEAVY = "heavy"
    FORMER_DRINKER = "former_drinker"

class MedicationStatus(str, Enum):
    """Medication status enumeration"""
    ACTIVE = "active"
    DISCONTINUED = "discontinued"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"

class SeverityLevel(str, Enum):
    """Severity level enumeration"""
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"

class HealthGoalStatus(str, Enum):
    """Health goal status enumeration"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    ON_HOLD = "on_hold"

class HealthDataCreate(BaseModel):
    """Health data creation schema"""
    user_id: int = Field(..., description="User ID")
    data_type: str = Field(..., description="Type of health data")
    value: Any = Field(..., description="Health data value")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Data timestamp")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")
    source: Optional[str] = Field(None, max_length=100, description="Data source")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Data confidence level")

    @field_validator('data_type')
    def validate_data_type(cls, v):
        """Validate data type"""
        valid_types = [
            'blood_pressure', 'heart_rate', 'temperature', 'weight', 'height',
            'blood_glucose', 'oxygen_saturation', 'respiratory_rate',
            'pain_level', 'mood', 'sleep_hours', 'steps', 'calories',
            'medication_taken', 'symptom_log', 'appointment'
        ]
        if v not in valid_types:
            raise ValueError(f"Invalid data type. Must be one of: {', '.join(valid_types)}")
        return v

    @field_validator('value')
    def validate_value(cls, v, values):
        """Validate value based on data type"""
        if 'data_type' not in values:
            return v
        
        data_type = values['data_type']
        
        if data_type in ['blood_pressure']:
            if not isinstance(v, dict) or 'systolic' not in v or 'diastolic' not in v:
                raise ValueError("Blood pressure must be a dict with 'systolic' and 'diastolic' values")
            if not (70 <= v['systolic'] <= 200 and 40 <= v['diastolic'] <= 130):
                raise ValueError("Blood pressure values out of valid range")
        
        elif data_type in ['heart_rate', 'respiratory_rate']:
            if not isinstance(v, (int, float)) or not (30 <= v <= 200):
                raise ValueError("Heart rate/respiratory rate must be between 30 and 200")
        
        elif data_type == 'temperature':
            if not isinstance(v, (int, float)) or not (30 <= v <= 45):
                raise ValueError("Temperature must be between 30 and 45 degrees")
        
        elif data_type in ['weight', 'height']:
            if not isinstance(v, (int, float)) or v <= 0:
                raise ValueError("Weight/height must be positive numbers")
        
        elif data_type == 'blood_glucose':
            if not isinstance(v, (int, float)) or not (20 <= v <= 600):
                raise ValueError("Blood glucose must be between 20 and 600 mg/dL")
        
        elif data_type == 'oxygen_saturation':
            if not isinstance(v, (int, float)) or not (70 <= v <= 100):
                raise ValueError("Oxygen saturation must be between 70 and 100%")
        
        elif data_type == 'pain_level':
            if not isinstance(v, int) or not (0 <= v <= 10):
                raise ValueError("Pain level must be between 0 and 10")
        
        elif data_type == 'sleep_hours':
            if not isinstance(v, (int, float)) or not (0 <= v <= 24):
                raise ValueError("Sleep hours must be between 0 and 24")
        
        elif data_type == 'steps':
            if not isinstance(v, int) or v < 0:
                raise ValueError("Steps must be a non-negative integer")
        
        elif data_type == 'calories':
            if not isinstance(v, (int, float)) or v < 0:
                raise ValueError("Calories must be a non-negative number")
        
        return v

    model_config = {
        "json_json_schema_extra": {
            "example": {
                "user_id": 123,
                "data_type": "blood_pressure",
                "value": {"systolic": 120, "diastolic": 80},
                "unit": "mmHg",
                "timestamp": "2024-01-01T12:00:00Z",
                "notes": "Taken after morning walk",
                "source": "manual",
                "confidence": 0.95
            }
        }
    }

class HealthDataUpdate(BaseModel):
    """Health data update schema"""
    value: Optional[Any] = Field(None, description="Health data value")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")
    source: Optional[str] = Field(None, max_length=100, description="Data source")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Data confidence level")

    model_config = {
        "json_json_schema_extra": {
            "example": {
                "value": {"systolic": 118, "diastolic": 78},
                "unit": "mmHg",
                "notes": "Updated after re-measurement",
                "source": "manual",
                "confidence": 0.98
            }
        }
    }

class HealthDataResponse(BaseModel):
    """Health data response schema"""
    id: int = Field(..., description="Health data ID")
    user_id: int = Field(..., description="User ID")
    data_type: str = Field(..., description="Type of health data")
    value: Any = Field(..., description="Health data value")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    timestamp: datetime = Field(..., description="Data timestamp")
    notes: Optional[str] = Field(None, description="Additional notes")
    source: Optional[str] = Field(None, description="Data source")
    confidence: Optional[float] = Field(None, description="Data confidence level")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {
        "json_json_schema_extra": {
            "example": {
                "id": 456,
                "user_id": 123,
                "data_type": "blood_pressure",
                "value": {"systolic": 120, "diastolic": 80},
                "unit": "mmHg",
                "timestamp": "2024-01-01T12:00:00Z",
                "notes": "Taken after morning walk",
                "source": "manual",
                "confidence": 0.95,
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z"
            }
        }
    }

class HealthMetrics(BaseModel):
    """Health metrics summary schema"""
    user_id: int = Field(..., description="User ID")
    metrics_date: date = Field(..., description="Metrics date")
    blood_pressure_avg: Optional[Dict[str, float]] = Field(None, description="Average blood pressure")
    heart_rate_avg: Optional[float] = Field(None, description="Average heart rate")
    temperature_avg: Optional[float] = Field(None, description="Average temperature")
    weight_latest: Optional[float] = Field(None, description="Latest weight")
    blood_glucose_avg: Optional[float] = Field(None, description="Average blood glucose")
    oxygen_saturation_avg: Optional[float] = Field(None, description="Average oxygen saturation")
    sleep_hours_total: Optional[float] = Field(None, description="Total sleep hours")
    steps_total: Optional[int] = Field(None, description="Total steps")
    calories_total: Optional[float] = Field(None, description="Total calories")
    pain_level_avg: Optional[float] = Field(None, description="Average pain level")
    mood_avg: Optional[float] = Field(None, description="Average mood score")

    model_config = {
        "json_json_schema_extra": {
            "example": {
                "user_id": 123,
                "metrics_date": "2024-01-01",
                "blood_pressure_avg": {"systolic": 120.5, "diastolic": 80.2},
                "heart_rate_avg": 72.3,
                "temperature_avg": 98.6,
                "weight_latest": 70.5,
                "blood_glucose_avg": 95.2,
                "oxygen_saturation_avg": 98.1,
                "sleep_hours_total": 7.5,
                "steps_total": 8500,
                "calories_total": 2100.5,
                "pain_level_avg": 2.1,
                "mood_avg": 7.8
            }
        }
    }

class SymptomLog(BaseModel):
    """Symptom logging schema"""
    user_id: int = Field(..., description="User ID")
    symptom: str = Field(..., max_length=200, description="Symptom name")
    severity: SeverityLevel = Field(..., description="Symptom severity")
    description: Optional[str] = Field(None, max_length=1000, description="Symptom description")
    location: Optional[str] = Field(None, max_length=200, description="Symptom location")
    duration: Optional[str] = Field(None, max_length=100, description="Symptom duration")
    triggers: Optional[str] = Field(None, max_length=500, description="Symptom triggers")
    treatments: Optional[str] = Field(None, max_length=500, description="Applied treatments")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Symptom timestamp")
    pain_level: Optional[int] = Field(None, ge=0, le=10, description="Pain level (0-10)")

    @field_validator('symptom')
    def validate_symptom(cls, v):
        """Validate symptom name"""
        if not v.strip():
            raise ValueError("Symptom name cannot be empty")
        return v.strip()

    model_config = {
        "json_json_schema_extra": {
            "example": {
                "user_id": 123,
                "symptom": "Headache",
                "severity": "moderate",
                "description": "Dull pain in the forehead area",
                "location": "Forehead",
                "duration": "2 hours",
                "triggers": "Stress, lack of sleep",
                "treatments": "Rest, hydration",
                "timestamp": "2024-01-01T12:00:00Z",
                "pain_level": 5
            }
        }
    }

class MedicationLog(BaseModel):
    """Medication logging schema"""
    user_id: int = Field(..., description="User ID")
    medication_name: str = Field(..., max_length=200, description="Medication name")
    dosage: str = Field(..., max_length=100, description="Medication dosage")
    frequency: str = Field(..., max_length=100, description="Medication frequency")
    taken_at: datetime = Field(default_factory=datetime.utcnow, description="When medication was taken")
    prescribed_by: Optional[str] = Field(None, max_length=200, description="Prescribing doctor")
    prescription_date: Optional[date] = Field(None, description="Prescription date")
    expiry_date: Optional[date] = Field(None, description="Medication expiry date")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")
    side_effects: Optional[str] = Field(None, max_length=500, description="Side effects experienced")
    effectiveness: Optional[int] = Field(None, ge=1, le=10, description="Effectiveness rating (1-10)")

    @field_validator('medication_name')
    def validate_medication_name(cls, v):
        """Validate medication name"""
        if not v.strip():
            raise ValueError("Medication name cannot be empty")
        return v.strip()

    @field_validator('dosage')
    def validate_dosage(cls, v):
        """Validate dosage format"""
        if not v.strip():
            raise ValueError("Dosage cannot be empty")
        return v.strip()

    @field_validator('frequency')
    def validate_frequency(cls, v):
        """Validate frequency format"""
        if not v.strip():
            raise ValueError("Frequency cannot be empty")
        return v.strip()

    model_config = {
        "json_json_schema_extra": {
            "example": {
                "user_id": 123,
                "medication_name": "Metformin",
                "dosage": "500mg",
                "frequency": "Twice daily",
                "taken_at": "2024-01-01T08:00:00Z",
                "prescribed_by": "Dr. Smith",
                "prescription_date": "2023-12-01",
                "expiry_date": "2024-12-01",
                "notes": "Take with food",
                "side_effects": "Mild nausea",
                "effectiveness": 8
            }
        }
    }

class HealthGoal(BaseModel):
    """Health goal schema"""
    user_id: int = Field(..., description="User ID")
    goal_type: str = Field(..., description="Type of health goal")
    target_value: Any = Field(..., description="Target value for the goal")
    current_value: Optional[Any] = Field(None, description="Current value")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    deadline: Optional[date] = Field(None, description="Goal deadline")
    description: str = Field(..., max_length=500, description="Goal description")
    progress: Optional[float] = Field(None, ge=0.0, le=100.0, description="Goal progress percentage")
    is_active: bool = Field(default=True, description="Goal status")

    @field_validator('goal_type')
    def validate_goal_type(cls, v):
        """Validate goal type"""
        valid_types = [
            'weight_loss', 'weight_gain', 'blood_pressure', 'blood_glucose',
            'heart_rate', 'steps', 'sleep', 'exercise', 'meditation',
            'water_intake', 'calorie_intake', 'medication_adherence'
        ]
        if v not in valid_types:
            raise ValueError(f"Invalid goal type. Must be one of: {', '.join(valid_types)}")
        return v

    @field_validator('progress')
    def validate_progress(cls, v):
        """Validate progress percentage"""
        if v is not None and (v < 0 or v > 100):
            raise ValueError("Progress must be between 0 and 100")
        return v

    model_config = {
        "json_json_schema_extra": {
            "example": {
                "user_id": 123,
                "goal_type": "weight_loss",
                "target_value": 65.0,
                "current_value": 70.5,
                "unit": "kg",
                "deadline": "2024-06-01",
                "description": "Lose 5kg to reach healthy weight",
                "progress": 45.0,
                "is_active": True
            }
        }
    }

class HealthAlert(BaseModel):
    """Health alert schema"""
    user_id: int = Field(..., description="User ID")
    alert_type: str = Field(..., description="Type of health alert")
    severity: SeverityLevel = Field(..., description="Alert severity")
    message: str = Field(..., max_length=500, description="Alert message")
    data_point: Optional[Dict[str, Any]] = Field(None, description="Related health data")
    triggered_at: datetime = Field(default_factory=datetime.utcnow, description="Alert trigger time")
    acknowledged: bool = Field(default=False, description="Whether alert was acknowledged")
    acknowledged_at: Optional[datetime] = Field(None, description="Acknowledgment time")
    action_taken: Optional[str] = Field(None, max_length=500, description="Action taken in response")

    @field_validator('alert_type')
    def validate_alert_type(cls, v):
        """Validate alert type"""
        valid_types = [
            'high_blood_pressure', 'low_blood_pressure', 'high_heart_rate',
            'low_heart_rate', 'high_blood_glucose', 'low_blood_glucose',
            'high_temperature', 'low_oxygen_saturation', 'medication_missed',
            'symptom_worsening', 'goal_milestone', 'appointment_reminder'
        ]
        if v not in valid_types:
            raise ValueError(f"Invalid alert type. Must be one of: {', '.join(valid_types)}")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": 123,
                "alert_type": "high_blood_pressure",
                "severity": "moderate",
                "message": "Blood pressure reading is above normal range",
                "data_point": {
                    "systolic": 145,
                    "diastolic": 95,
                    "timestamp": "2024-01-01T12:00:00Z"
                },
                "triggered_at": "2024-01-01T12:00:00Z",
                "acknowledged": False,
                "action_taken": "Scheduled follow-up with doctor"
            }
        }
    }


# Enhanced Health Profile Schemas
class UserHealthProfileCreate(BaseModel):
    """Enhanced user health profile creation schema"""
    user_id: int = Field(..., description="User ID")
    height_cm: Optional[float] = Field(None, ge=50, le=300, description="Height in centimeters")
    weight_kg: Optional[float] = Field(None, ge=10, le=500, description="Weight in kilograms")
    gender: Optional[Gender] = Field(None, description="Gender")
    blood_type: Optional[BloodType] = Field(None, description="Blood type")
    ethnicity: Optional[str] = Field(None, max_length=100, description="Ethnicity")
    occupation: Optional[str] = Field(None, max_length=200, description="Occupation")
    activity_level: Optional[ActivityLevel] = Field(None, description="Activity level")
    smoking_status: Optional[SmokingStatus] = Field(None, description="Smoking status")
    alcohol_consumption: Optional[AlcoholConsumption] = Field(None, description="Alcohol consumption")
    exercise_frequency: Optional[str] = Field(None, max_length=50, description="Exercise frequency")
    sleep_hours_per_night: Optional[float] = Field(None, ge=0, le=24, description="Sleep hours per night")
    primary_care_physician: Optional[str] = Field(None, max_length=200, description="Primary care physician")
    specialist_physicians: Optional[Dict[str, Any]] = Field(None, description="Specialist physicians")
    hospital_preferences: Optional[Dict[str, Any]] = Field(None, description="Hospital preferences")
    insurance_provider: Optional[str] = Field(None, max_length=200, description="Insurance provider")
    insurance_policy_number: Optional[str] = Field(None, max_length=100, description="Insurance policy number")
    family_medical_history: Optional[Dict[str, Any]] = Field(None, description="Family medical history")
    food_allergies: Optional[Dict[str, Any]] = Field(None, description="Food allergies")
    drug_allergies: Optional[Dict[str, Any]] = Field(None, description="Drug allergies")
    environmental_allergies: Optional[Dict[str, Any]] = Field(None, description="Environmental allergies")
    chronic_conditions: Optional[Dict[str, Any]] = Field(None, description="Chronic conditions")
    mental_health_conditions: Optional[Dict[str, Any]] = Field(None, description="Mental health conditions")
    emergency_contacts: Optional[Dict[str, Any]] = Field(None, description="Emergency contacts")
    advance_directives: Optional[Dict[str, Any]] = Field(None, description="Advance directives")
    organ_donor_status: Optional[bool] = Field(None, description="Organ donor status")
    health_goals: Optional[Dict[str, Any]] = Field(None, description="Health goals")
    treatment_preferences: Optional[Dict[str, Any]] = Field(None, description="Treatment preferences")
    communication_preferences: Optional[Dict[str, Any]] = Field(None, description="Communication preferences")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": 1,
                "height_cm": 175.0,
                "weight_kg": 70.0,
                "gender": "male",
                "blood_type": "O+",
                "activity_level": "moderately_active",
                "smoking_status": "never_smoked",
                "alcohol_consumption": "occasional",
                "sleep_hours_per_night": 7.5
            }
        }
    )


class UserHealthProfileUpdate(BaseModel):
    """Enhanced user health profile update schema"""
    height_cm: Optional[float] = Field(None, ge=50, le=300, description="Height in centimeters")
    weight_kg: Optional[float] = Field(None, ge=10, le=500, description="Weight in kilograms")
    gender: Optional[Gender] = Field(None, description="Gender")
    blood_type: Optional[BloodType] = Field(None, description="Blood type")
    ethnicity: Optional[str] = Field(None, max_length=100, description="Ethnicity")
    occupation: Optional[str] = Field(None, max_length=200, description="Occupation")
    activity_level: Optional[ActivityLevel] = Field(None, description="Activity level")
    smoking_status: Optional[SmokingStatus] = Field(None, description="Smoking status")
    alcohol_consumption: Optional[AlcoholConsumption] = Field(None, description="Alcohol consumption")
    exercise_frequency: Optional[str] = Field(None, max_length=50, description="Exercise frequency")
    sleep_hours_per_night: Optional[float] = Field(None, ge=0, le=24, description="Sleep hours per night")
    primary_care_physician: Optional[str] = Field(None, max_length=200, description="Primary care physician")
    specialist_physicians: Optional[Dict[str, Any]] = Field(None, description="Specialist physicians")
    hospital_preferences: Optional[Dict[str, Any]] = Field(None, description="Hospital preferences")
    insurance_provider: Optional[str] = Field(None, max_length=200, description="Insurance provider")
    insurance_policy_number: Optional[str] = Field(None, max_length=100, description="Insurance policy number")
    family_medical_history: Optional[Dict[str, Any]] = Field(None, description="Family medical history")
    food_allergies: Optional[Dict[str, Any]] = Field(None, description="Food allergies")
    drug_allergies: Optional[Dict[str, Any]] = Field(None, description="Drug allergies")
    environmental_allergies: Optional[Dict[str, Any]] = Field(None, description="Environmental allergies")
    chronic_conditions: Optional[Dict[str, Any]] = Field(None, description="Chronic conditions")
    mental_health_conditions: Optional[Dict[str, Any]] = Field(None, description="Mental health conditions")
    emergency_contacts: Optional[Dict[str, Any]] = Field(None, description="Emergency contacts")
    advance_directives: Optional[Dict[str, Any]] = Field(None, description="Advance directives")
    organ_donor_status: Optional[bool] = Field(None, description="Organ donor status")
    health_goals: Optional[Dict[str, Any]] = Field(None, description="Health goals")
    treatment_preferences: Optional[Dict[str, Any]] = Field(None, description="Treatment preferences")
    communication_preferences: Optional[Dict[str, Any]] = Field(None, description="Communication preferences")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "weight_kg": 68.0,
                "activity_level": "very_active",
                "sleep_hours_per_night": 8.0
            }
        }
    )


class UserHealthProfileResponse(BaseModel):
    """Enhanced user health profile response schema"""
    id: int = Field(..., description="Health profile ID")
    user_id: int = Field(..., description="User ID")
    height_cm: Optional[float] = Field(None, description="Height in centimeters")
    weight_kg: Optional[float] = Field(None, description="Weight in kilograms")
    bmi: Optional[float] = Field(None, description="BMI")
    body_fat_percentage: Optional[float] = Field(None, description="Body fat percentage")
    muscle_mass_kg: Optional[float] = Field(None, description="Muscle mass in kilograms")
    gender: Optional[Gender] = Field(None, description="Gender")
    blood_type: Optional[BloodType] = Field(None, description="Blood type")
    ethnicity: Optional[str] = Field(None, description="Ethnicity")
    occupation: Optional[str] = Field(None, description="Occupation")
    activity_level: Optional[ActivityLevel] = Field(None, description="Activity level")
    smoking_status: Optional[SmokingStatus] = Field(None, description="Smoking status")
    alcohol_consumption: Optional[AlcoholConsumption] = Field(None, description="Alcohol consumption")
    exercise_frequency: Optional[str] = Field(None, description="Exercise frequency")
    sleep_hours_per_night: Optional[float] = Field(None, description="Sleep hours per night")
    primary_care_physician: Optional[str] = Field(None, description="Primary care physician")
    specialist_physicians: Optional[Dict[str, Any]] = Field(None, description="Specialist physicians")
    hospital_preferences: Optional[Dict[str, Any]] = Field(None, description="Hospital preferences")
    insurance_provider: Optional[str] = Field(None, description="Insurance provider")
    insurance_policy_number: Optional[str] = Field(None, description="Insurance policy number")
    family_medical_history: Optional[Dict[str, Any]] = Field(None, description="Family medical history")
    food_allergies: Optional[Dict[str, Any]] = Field(None, description="Food allergies")
    drug_allergies: Optional[Dict[str, Any]] = Field(None, description="Drug allergies")
    environmental_allergies: Optional[Dict[str, Any]] = Field(None, description="Environmental allergies")
    chronic_conditions: Optional[Dict[str, Any]] = Field(None, description="Chronic conditions")
    mental_health_conditions: Optional[Dict[str, Any]] = Field(None, description="Mental health conditions")
    emergency_contacts: Optional[Dict[str, Any]] = Field(None, description="Emergency contacts")
    advance_directives: Optional[Dict[str, Any]] = Field(None, description="Advance directives")
    organ_donor_status: Optional[bool] = Field(None, description="Organ donor status")
    health_goals: Optional[Dict[str, Any]] = Field(None, description="Health goals")
    treatment_preferences: Optional[Dict[str, Any]] = Field(None, description="Treatment preferences")
    communication_preferences: Optional[Dict[str, Any]] = Field(None, description="Communication preferences")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_health_assessment: Optional[datetime] = Field(None, description="Last health assessment timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "user_id": 1,
                "height_cm": 175.0,
                "weight_kg": 70.0,
                "bmi": 22.9,
                "gender": "male",
                "blood_type": "O+",
                "activity_level": "moderately_active",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }
    ) 
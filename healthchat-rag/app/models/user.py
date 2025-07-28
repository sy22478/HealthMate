from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.base import Base
from app.utils.encryption_utils import field_encryption
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    HEALTHCARE_PROVIDER = "healthcare_provider"
    PATIENT = "patient"
    DOCTOR = "doctor"
    RESEARCHER = "researcher"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)  # Encrypted PII
    age = Column(Integer)
    medical_conditions = Column(Text)  # Encrypted health data
    medications = Column(Text)  # Encrypted health data
    role = Column(String, default="patient")  # patient, doctor, admin, researcher
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    reset_token = Column(String, nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)
    
    # Additional PII fields (encrypted)
    phone = Column(String, nullable=True)  # Encrypted
    address = Column(Text, nullable=True)  # Encrypted
    date_of_birth = Column(String, nullable=True)  # Encrypted
    emergency_contact = Column(Text, nullable=True)  # Encrypted JSON
    insurance_info = Column(Text, nullable=True)  # Encrypted JSON
    
    # Additional health data fields (encrypted)
    blood_type = Column(String, nullable=True)  # Encrypted
    allergies = Column(Text, nullable=True)  # Encrypted JSON
    family_history = Column(Text, nullable=True)  # Encrypted JSON
    diagnoses = Column(Text, nullable=True)  # Encrypted JSON
    symptoms = Column(Text, nullable=True)  # Encrypted JSON
    
    # Relationships to health data models
    health_data = relationship("HealthData", back_populates="user", cascade="all, delete-orphan")
    symptom_logs = relationship("SymptomLog", back_populates="user", cascade="all, delete-orphan")
    medication_logs = relationship("MedicationLog", back_populates="user", cascade="all, delete-orphan")
    health_goals = relationship("HealthGoal", back_populates="user", cascade="all, delete-orphan")
    health_alerts = relationship("HealthAlert", back_populates="user", cascade="all, delete-orphan")
    
    # Enhanced health profile relationship
    health_profile = relationship("UserHealthProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    # Enhanced conversation and AI interaction relationships
    conversation_history = relationship("ConversationHistory", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    feedbacks = relationship("UserFeedback", back_populates="user", cascade="all, delete-orphan")
    
    # Notification relationships
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    notification_preferences = relationship("UserNotificationPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._encrypt_sensitive_fields()
    
    def _encrypt_sensitive_fields(self):
        """Encrypt sensitive fields before saving"""
        sensitive_fields = [
            'full_name', 'phone', 'address', 'date_of_birth',
            'emergency_contact', 'insurance_info', 'medical_conditions',
            'medications', 'blood_type', 'allergies', 'family_history',
            'diagnoses', 'symptoms'
        ]
        field_encryption.encrypt_model_fields(self, sensitive_fields)
    
    def decrypt_sensitive_fields(self):
        """Decrypt sensitive fields for display"""
        sensitive_fields = [
            'full_name', 'phone', 'address', 'date_of_birth',
            'emergency_contact', 'insurance_info', 'medical_conditions',
            'medications', 'blood_type', 'allergies', 'family_history',
            'diagnoses', 'symptoms'
        ]
        field_encryption.decrypt_model_fields(self, sensitive_fields)
    
    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary, optionally including decrypted sensitive data"""
        user_dict = {
            'id': self.id,
            'email': self.email,
            'age': self.age,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if include_sensitive:
            # Decrypt sensitive fields for the response
            self.decrypt_sensitive_fields()
            user_dict.update({
                'full_name': self.full_name,
                'phone': self.phone,
                'address': self.address,
                'date_of_birth': self.date_of_birth,
                'emergency_contact': self.emergency_contact,
                'insurance_info': self.insurance_info,
                'medical_conditions': self.medical_conditions,
                'medications': self.medications,
                'blood_type': self.blood_type,
                'allergies': self.allergies,
                'family_history': self.family_history,
                'diagnoses': self.diagnoses,
                'symptoms': self.symptoms
            })
        
        return user_dict

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(Text)
    response = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    context_used = Column(Text)  # RAG sources 
    feedback = Column(String, nullable=True)  # 'up', 'down', or None 
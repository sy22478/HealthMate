"""
Health Data Models for HealthMate
Provides database models for health data with encryption for sensitive fields
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.base import Base
from app.utils.encryption_utils import field_encryption

class HealthData(Base):
    """Health data model for tracking various health metrics"""
    __tablename__ = "health_data"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    data_type = Column(String(50), nullable=False, index=True)  # blood_pressure, heart_rate, etc.
    value = Column(Text, nullable=False)  # Encrypted JSON or string value
    unit = Column(String(20), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    notes = Column(Text, nullable=True)  # Encrypted
    source = Column(String(100), nullable=True)  # manual, device, api
    confidence = Column(Float, nullable=True)  # 0.0 to 1.0
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="health_data")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._encrypt_sensitive_fields()
    
    def _encrypt_sensitive_fields(self):
        """Encrypt sensitive fields before saving"""
        sensitive_fields = ['value', 'notes']
        field_encryption.encrypt_model_fields(self, sensitive_fields)
    
    def decrypt_sensitive_fields(self):
        """Decrypt sensitive fields for display"""
        sensitive_fields = ['value', 'notes']
        field_encryption.decrypt_model_fields(self, sensitive_fields)
    
    def to_dict(self, include_sensitive=False):
        """Convert to dictionary, optionally including decrypted sensitive data"""
        health_dict = {
            'id': self.id,
            'user_id': self.user_id,
            'data_type': self.data_type,
            'unit': self.unit,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'source': self.source,
            'confidence': self.confidence,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_sensitive:
            self.decrypt_sensitive_fields()
            health_dict.update({
                'value': self.value,
                'notes': self.notes
            })
        
        return health_dict

class SymptomLog(Base):
    """Symptom logging model"""
    __tablename__ = "symptom_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    symptom = Column(String(200), nullable=False)
    severity = Column(String(20), nullable=False)  # mild, moderate, severe
    description = Column(Text, nullable=True)  # Encrypted
    location = Column(String(200), nullable=True)  # Encrypted
    duration = Column(String(100), nullable=True)  # Encrypted
    triggers = Column(Text, nullable=True)  # Encrypted
    treatments = Column(Text, nullable=True)  # Encrypted
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    pain_level = Column(Integer, nullable=True)  # 0-10 scale
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="symptom_logs")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._encrypt_sensitive_fields()
    
    def _encrypt_sensitive_fields(self):
        """Encrypt sensitive fields before saving"""
        sensitive_fields = ['description', 'location', 'duration', 'triggers', 'treatments']
        field_encryption.encrypt_model_fields(self, sensitive_fields)
    
    def decrypt_sensitive_fields(self):
        """Decrypt sensitive fields for display"""
        sensitive_fields = ['description', 'location', 'duration', 'triggers', 'treatments']
        field_encryption.decrypt_model_fields(self, sensitive_fields)
    
    def to_dict(self, include_sensitive=False):
        """Convert to dictionary, optionally including decrypted sensitive data"""
        symptom_dict = {
            'id': self.id,
            'user_id': self.user_id,
            'symptom': self.symptom,
            'severity': self.severity,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'pain_level': self.pain_level,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if include_sensitive:
            self.decrypt_sensitive_fields()
            symptom_dict.update({
                'description': self.description,
                'location': self.location,
                'duration': self.duration,
                'triggers': self.triggers,
                'treatments': self.treatments
            })
        
        return symptom_dict

class MedicationLog(Base):
    """Medication logging model"""
    __tablename__ = "medication_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    medication_name = Column(String(200), nullable=False)
    dosage = Column(String(100), nullable=False)
    frequency = Column(String(100), nullable=False)
    taken_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    prescribed_by = Column(String(200), nullable=True)  # Encrypted
    prescription_date = Column(DateTime, nullable=True)
    expiry_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)  # Encrypted
    side_effects = Column(Text, nullable=True)  # Encrypted
    effectiveness = Column(Integer, nullable=True)  # 1-10 scale
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="medication_logs")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._encrypt_sensitive_fields()
    
    def _encrypt_sensitive_fields(self):
        """Encrypt sensitive fields before saving"""
        sensitive_fields = ['prescribed_by', 'notes', 'side_effects']
        field_encryption.encrypt_model_fields(self, sensitive_fields)
    
    def decrypt_sensitive_fields(self):
        """Decrypt sensitive fields for display"""
        sensitive_fields = ['prescribed_by', 'notes', 'side_effects']
        field_encryption.decrypt_model_fields(self, sensitive_fields)
    
    def to_dict(self, include_sensitive=False):
        """Convert to dictionary, optionally including decrypted sensitive data"""
        medication_dict = {
            'id': self.id,
            'user_id': self.user_id,
            'medication_name': self.medication_name,
            'dosage': self.dosage,
            'frequency': self.frequency,
            'taken_at': self.taken_at.isoformat() if self.taken_at else None,
            'prescription_date': self.prescription_date.isoformat() if self.prescription_date else None,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'effectiveness': self.effectiveness,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if include_sensitive:
            self.decrypt_sensitive_fields()
            medication_dict.update({
                'prescribed_by': self.prescribed_by,
                'notes': self.notes,
                'side_effects': self.side_effects
            })
        
        return medication_dict

class HealthGoal(Base):
    """Health goal tracking model"""
    __tablename__ = "health_goals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    goal_type = Column(String(50), nullable=False)
    target_value = Column(Text, nullable=False)  # Encrypted JSON or string
    current_value = Column(Text, nullable=True)  # Encrypted JSON or string
    unit = Column(String(20), nullable=True)
    deadline = Column(DateTime, nullable=True)
    description = Column(String(500), nullable=False)  # Encrypted
    progress = Column(Float, nullable=True)  # 0.0 to 100.0
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="health_goals")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._encrypt_sensitive_fields()
    
    def _encrypt_sensitive_fields(self):
        """Encrypt sensitive fields before saving"""
        sensitive_fields = ['target_value', 'current_value', 'description']
        field_encryption.encrypt_model_fields(self, sensitive_fields)
    
    def decrypt_sensitive_fields(self):
        """Decrypt sensitive fields for display"""
        sensitive_fields = ['target_value', 'current_value', 'description']
        field_encryption.decrypt_model_fields(self, sensitive_fields)
    
    def to_dict(self, include_sensitive=False):
        """Convert to dictionary, optionally including decrypted sensitive data"""
        goal_dict = {
            'id': self.id,
            'user_id': self.user_id,
            'goal_type': self.goal_type,
            'unit': self.unit,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'progress': self.progress,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_sensitive:
            self.decrypt_sensitive_fields()
            goal_dict.update({
                'target_value': self.target_value,
                'current_value': self.current_value,
                'description': self.description
            })
        
        return goal_dict

class HealthAlert(Base):
    """Health alert model"""
    __tablename__ = "health_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    alert_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)  # mild, moderate, severe
    message = Column(String(500), nullable=False)  # Encrypted
    data_point = Column(Text, nullable=True)  # Encrypted JSON
    triggered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime, nullable=True)
    action_taken = Column(Text, nullable=True)  # Encrypted
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="health_alerts")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._encrypt_sensitive_fields()
    
    def _encrypt_sensitive_fields(self):
        """Encrypt sensitive fields before saving"""
        sensitive_fields = ['message', 'data_point', 'action_taken']
        field_encryption.encrypt_model_fields(self, sensitive_fields)
    
    def decrypt_sensitive_fields(self):
        """Decrypt sensitive fields for display"""
        sensitive_fields = ['message', 'data_point', 'action_taken']
        field_encryption.decrypt_model_fields(self, sensitive_fields)
    
    def to_dict(self, include_sensitive=False):
        """Convert to dictionary, optionally including decrypted sensitive data"""
        alert_dict = {
            'id': self.id,
            'user_id': self.user_id,
            'alert_type': self.alert_type,
            'severity': self.severity,
            'triggered_at': self.triggered_at.isoformat() if self.triggered_at else None,
            'acknowledged': self.acknowledged,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if include_sensitive:
            self.decrypt_sensitive_fields()
            alert_dict.update({
                'message': self.message,
                'data_point': self.data_point,
                'action_taken': self.action_taken
            })
        
        return alert_dict 
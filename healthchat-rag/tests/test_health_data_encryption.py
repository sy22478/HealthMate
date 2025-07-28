"""
Tests for Health Data Encryption
Tests encryption/decryption of health data models and utilities
"""
import pytest
import json
from datetime import datetime, date
from app.utils.encryption_utils import EncryptionManager, FieldLevelEncryption
from app.models.health_data import HealthData, SymptomLog, MedicationLog, HealthGoal, HealthAlert
from app.models.user import User
from app.base import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Test database setup
TEST_DATABASE_URL = "sqlite:///./test_health_data.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db_session():
    """Create test database session"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def encryption_manager():
    """Create encryption manager for testing"""
    return EncryptionManager(master_key="test_secret_key_123")

@pytest.fixture
def field_encryption(encryption_manager):
    """Create field-level encryption for testing"""
    return FieldLevelEncryption(encryption_manager)

@pytest.fixture
def test_user(db_session):
    """Create test user"""
    user = User(
        email="test@example.com",
        hashed_password="hashed_password",
        full_name="Test User",
        age=30,
        role="patient"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

class TestHealthDataEncryption:
    """Test health data encryption functionality"""
    
    def test_encryption_manager_initialization(self, encryption_manager):
        """Test encryption manager initialization"""
        assert encryption_manager is not None
        assert encryption_manager.master_key == "test_secret_key_123"
    
    def test_encrypt_decrypt_field(self, encryption_manager):
        """Test basic field encryption and decryption"""
        test_data = "sensitive_health_data"
        encrypted = encryption_manager.encrypt_field(test_data)
        decrypted = encryption_manager.decrypt_field(encrypted)
        
        assert encrypted != test_data
        assert decrypted == test_data
    
    def test_encrypt_decrypt_json_data(self, encryption_manager):
        """Test encryption and decryption of JSON data"""
        test_data = {"blood_pressure": {"systolic": 120, "diastolic": 80}}
        encrypted = encryption_manager.encrypt_field(test_data)
        decrypted = encryption_manager.decrypt_field(encrypted)
        
        assert encrypted != json.dumps(test_data)
        assert decrypted == test_data
    
    def test_encrypt_health_data(self, encryption_manager):
        """Test health data encryption"""
        health_data = {
            "medical_conditions": "Hypertension, Diabetes",
            "medications": "Lisinopril, Metformin",
            "blood_type": "A+",
            "allergies": "Penicillin",
            "value": {"systolic": 140, "diastolic": 90},
            "notes": "Patient reported feeling dizzy"
        }
        
        encrypted_data = encryption_manager.encrypt_health_data(health_data)
        
        # Check that sensitive fields are encrypted
        assert encrypted_data["medical_conditions"] != health_data["medical_conditions"]
        assert encrypted_data["medications"] != health_data["medications"]
        assert encrypted_data["blood_type"] != health_data["blood_type"]
        assert encrypted_data["allergies"] != health_data["allergies"]
        assert encrypted_data["value"] != health_data["value"]
        assert encrypted_data["notes"] != health_data["notes"]
    
    def test_decrypt_health_data(self, encryption_manager):
        """Test health data decryption"""
        health_data = {
            "medical_conditions": "Hypertension, Diabetes",
            "medications": "Lisinopril, Metformin",
            "blood_type": "A+",
            "allergies": "Penicillin",
            "value": {"systolic": 140, "diastolic": 90},
            "notes": "Patient reported feeling dizzy"
        }
        
        encrypted_data = encryption_manager.encrypt_health_data(health_data)
        decrypted_data = encryption_manager.decrypt_health_data(encrypted_data)
        
        assert decrypted_data == health_data
    
    def test_encrypt_health_metrics(self, encryption_manager):
        """Test health metrics encryption"""
        metrics = {
            "blood_pressure_avg": {"systolic": 120.5, "diastolic": 80.2},
            "heart_rate_avg": 72.3,
            "temperature_avg": 98.6,
            "weight_latest": 70.5,
            "blood_glucose_avg": 95.2
        }
        
        encrypted_metrics = encryption_manager.encrypt_health_metrics(metrics)
        
        # Check that sensitive metrics are encrypted
        assert encrypted_metrics["blood_pressure_avg"] != metrics["blood_pressure_avg"]
        assert encrypted_metrics["heart_rate_avg"] != metrics["heart_rate_avg"]
        assert encrypted_metrics["temperature_avg"] != metrics["temperature_avg"]
        assert encrypted_metrics["weight_latest"] != metrics["weight_latest"]
        assert encrypted_metrics["blood_glucose_avg"] != metrics["blood_glucose_avg"]
    
    def test_decrypt_health_metrics(self, encryption_manager):
        """Test health metrics decryption"""
        metrics = {
            "blood_pressure_avg": {"systolic": 120.5, "diastolic": 80.2},
            "heart_rate_avg": 72.3,
            "temperature_avg": 98.6,
            "weight_latest": 70.5,
            "blood_glucose_avg": 95.2
        }
        
        encrypted_metrics = encryption_manager.encrypt_health_metrics(metrics)
        decrypted_metrics = encryption_manager.decrypt_health_metrics(encrypted_metrics)
        
        assert decrypted_metrics == metrics
    
    def test_validate_encryption_key(self, encryption_manager):
        """Test encryption key validation"""
        assert encryption_manager.validate_encryption_key() is True
    
    def test_is_encrypted_detection(self, encryption_manager):
        """Test encrypted data detection"""
        test_data = "sensitive_data"
        encrypted = encryption_manager.encrypt_field(test_data)
        
        assert encryption_manager.is_encrypted(encrypted) is True
        assert encryption_manager.is_encrypted(test_data) is False

class TestHealthDataModels:
    """Test health data models with encryption"""
    
    def test_health_data_model_encryption(self, db_session, test_user):
        """Test HealthData model encryption"""
        health_data = HealthData(
            user_id=test_user.id,
            data_type="blood_pressure",
            value=json.dumps({"systolic": 120, "diastolic": 80}),
            unit="mmHg",
            notes="Taken after morning walk",
            source="manual",
            confidence=0.95
        )
        
        db_session.add(health_data)
        db_session.commit()
        db_session.refresh(health_data)
        
        # Check that sensitive fields are encrypted in database
        assert health_data.value != json.dumps({"systolic": 120, "diastolic": 80})
        assert health_data.notes != "Taken after morning walk"
        
        # Decrypt for display
        health_data.decrypt_sensitive_fields()
        assert health_data.value == {"systolic": 120, "diastolic": 80}  # JSON is parsed back to dict
        assert health_data.notes == "Taken after morning walk"
    
    def test_symptom_log_model_encryption(self, db_session, test_user):
        """Test SymptomLog model encryption"""
        symptom_log = SymptomLog(
            user_id=test_user.id,
            symptom="Headache",
            severity="moderate",
            description="Dull pain in the forehead area",
            location="Forehead",
            duration="2 hours",
            triggers="Stress, lack of sleep",
            treatments="Rest, hydration",
            pain_level=5
        )
        
        db_session.add(symptom_log)
        db_session.commit()
        db_session.refresh(symptom_log)
        
        # Check that sensitive fields are encrypted
        assert symptom_log.description != "Dull pain in the forehead area"
        assert symptom_log.location != "Forehead"
        assert symptom_log.duration != "2 hours"
        assert symptom_log.triggers != "Stress, lack of sleep"
        assert symptom_log.treatments != "Rest, hydration"
        
        # Decrypt for display
        symptom_log.decrypt_sensitive_fields()
        assert symptom_log.description == "Dull pain in the forehead area"
        assert symptom_log.location == "Forehead"
        assert symptom_log.duration == "2 hours"
        assert symptom_log.triggers == "Stress, lack of sleep"
        assert symptom_log.treatments == "Rest, hydration"
    
    def test_medication_log_model_encryption(self, db_session, test_user):
        """Test MedicationLog model encryption"""
        medication_log = MedicationLog(
            user_id=test_user.id,
            medication_name="Lisinopril",
            dosage="10mg",
            frequency="Once daily",
            prescribed_by="Dr. Smith",
            notes="Take with food",
            side_effects="Mild dizziness"
        )
        
        db_session.add(medication_log)
        db_session.commit()
        db_session.refresh(medication_log)
        
        # Check that sensitive fields are encrypted
        assert medication_log.prescribed_by != "Dr. Smith"
        assert medication_log.notes != "Take with food"
        assert medication_log.side_effects != "Mild dizziness"
        
        # Decrypt for display
        medication_log.decrypt_sensitive_fields()
        assert medication_log.prescribed_by == "Dr. Smith"
        assert medication_log.notes == "Take with food"
        assert medication_log.side_effects == "Mild dizziness"
    
    def test_health_goal_model_encryption(self, db_session, test_user):
        """Test HealthGoal model encryption"""
        health_goal = HealthGoal(
            user_id=test_user.id,
            goal_type="weight_loss",
            target_value=json.dumps(65.0),
            current_value=json.dumps(70.5),
            unit="kg",
            description="Lose 5kg to reach healthy weight"
        )
        
        db_session.add(health_goal)
        db_session.commit()
        db_session.refresh(health_goal)
        
        # Check that sensitive fields are encrypted
        assert health_goal.target_value != json.dumps(65.0)
        assert health_goal.current_value != json.dumps(70.5)
        assert health_goal.description != "Lose 5kg to reach healthy weight"
        
        # Decrypt for display
        health_goal.decrypt_sensitive_fields()
        assert health_goal.target_value == 65.0  # JSON is parsed back to float
        assert health_goal.current_value == 70.5  # JSON is parsed back to float
        assert health_goal.description == "Lose 5kg to reach healthy weight"
    
    def test_health_alert_model_encryption(self, db_session, test_user):
        """Test HealthAlert model encryption"""
        health_alert = HealthAlert(
            user_id=test_user.id,
            alert_type="high_blood_pressure",
            severity="moderate",
            message="Blood pressure reading is above normal range",
            data_point=json.dumps({"systolic": 145, "diastolic": 95}),
            action_taken="Scheduled follow-up with doctor"
        )
        
        db_session.add(health_alert)
        db_session.commit()
        db_session.refresh(health_alert)
        
        # Check that sensitive fields are encrypted
        assert health_alert.message != "Blood pressure reading is above normal range"
        assert health_alert.data_point != json.dumps({"systolic": 145, "diastolic": 95})
        assert health_alert.action_taken != "Scheduled follow-up with doctor"
        
        # Decrypt for display
        health_alert.decrypt_sensitive_fields()
        assert health_alert.message == "Blood pressure reading is above normal range"
        assert health_alert.data_point == {"systolic": 145, "diastolic": 95}  # JSON is parsed back to dict
        assert health_alert.action_taken == "Scheduled follow-up with doctor"
    
    def test_model_to_dict_with_encryption(self, db_session, test_user):
        """Test model to_dict method with encryption handling"""
        health_data = HealthData(
            user_id=test_user.id,
            data_type="blood_pressure",
            value=json.dumps({"systolic": 120, "diastolic": 80}),
            notes="Test notes"
        )
        
        db_session.add(health_data)
        db_session.commit()
        db_session.refresh(health_data)
        
        # Test without sensitive data
        health_dict = health_data.to_dict(include_sensitive=False)
        assert "value" not in health_dict
        assert "notes" not in health_dict
        
        # Test with sensitive data
        health_dict_sensitive = health_data.to_dict(include_sensitive=True)
        assert "value" in health_dict_sensitive
        assert "notes" in health_dict_sensitive
        assert health_dict_sensitive["value"] == {"systolic": 120, "diastolic": 80}  # JSON is parsed back to dict
        assert health_dict_sensitive["notes"] == "Test notes"

class TestFieldLevelEncryption:
    """Test field-level encryption functionality"""
    
    def test_encrypt_model_fields(self, field_encryption):
        """Test field-level encryption on model instances"""
        class TestModel:
            def __init__(self):
                self.name = "John Doe"
                self.medical_notes = "Patient has hypertension"
                self.age = 30
        
        model = TestModel()
        fields_to_encrypt = ["name", "medical_notes"]
        
        field_encryption.encrypt_model_fields(model, fields_to_encrypt)
        
        assert model.name != "John Doe"
        assert model.medical_notes != "Patient has hypertension"
        assert model.age == 30  # Should not be encrypted
    
    def test_decrypt_model_fields(self, field_encryption):
        """Test field-level decryption on model instances"""
        class TestModel:
            def __init__(self):
                self.name = "John Doe"
                self.medical_notes = "Patient has hypertension"
                self.age = 30
        
        model = TestModel()
        fields_to_encrypt = ["name", "medical_notes"]
        
        # First encrypt
        field_encryption.encrypt_model_fields(model, fields_to_encrypt)
        encrypted_name = model.name
        encrypted_notes = model.medical_notes
        
        # Then decrypt
        field_encryption.decrypt_model_fields(model, fields_to_encrypt)
        
        assert model.name == "John Doe"
        assert model.medical_notes == "Patient has hypertension"
        assert model.age == 30  # Should not be affected

class TestEncryptionErrorHandling:
    """Test encryption error handling"""
    
    def test_encryption_with_invalid_data(self, encryption_manager):
        """Test encryption with invalid data types"""
        # Test with None
        encrypted = encryption_manager.encrypt_field(None)
        decrypted = encryption_manager.decrypt_field(encrypted)
        assert decrypted == ""
        
        # Test with empty string
        encrypted = encryption_manager.encrypt_field("")
        decrypted = encryption_manager.decrypt_field(encrypted)
        assert decrypted == ""
    
    def test_decryption_with_invalid_data(self, encryption_manager):
        """Test decryption with invalid data"""
        with pytest.raises(ValueError):
            encryption_manager.decrypt_field("invalid_encrypted_data")
    
    def test_health_data_encryption_with_missing_fields(self, encryption_manager):
        """Test health data encryption with missing fields"""
        health_data = {
            "medical_conditions": "Hypertension",
            # Missing other fields
        }
        
        encrypted_data = encryption_manager.encrypt_health_data(health_data)
        decrypted_data = encryption_manager.decrypt_health_data(encrypted_data)
        
        assert decrypted_data == health_data 
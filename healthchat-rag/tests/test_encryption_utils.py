"""
Encryption Utilities Tests
Tests for data encryption and decryption functionality
"""
import pytest
import json
import base64
from app.utils.encryption_utils import EncryptionManager, FieldLevelEncryption
from app.models.user import User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import get_db, Base

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_encryption.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(autouse=True)
def setup_database():
    """Setup test database before each test"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

class TestEncryptionManager:
    """Test encryption manager functionality"""
    
    def test_encryption_manager_initialization(self):
        """Test encryption manager initialization"""
        manager = EncryptionManager("test_secret_key")
        assert manager.master_key == "test_secret_key"
        assert manager._fernet is not None
    
    def test_field_encryption_decryption(self):
        """Test basic field encryption and decryption"""
        manager = EncryptionManager("test_secret_key")
        
        # Test string encryption
        original_data = "sensitive health information"
        encrypted = manager.encrypt_field(original_data)
        decrypted = manager.decrypt_field(encrypted)
        
        assert encrypted != original_data
        assert decrypted == original_data
        assert manager.is_encrypted(encrypted)
        assert not manager.is_encrypted(original_data)
    
    def test_dict_encryption_decryption(self):
        """Test dictionary encryption and decryption"""
        manager = EncryptionManager("test_secret_key")
        
        original_data = {"condition": "diabetes", "severity": "moderate"}
        encrypted = manager.encrypt_field(original_data)
        decrypted = manager.decrypt_field(encrypted)
        
        assert encrypted != str(original_data)
        assert decrypted == original_data
        assert isinstance(decrypted, dict)
    
    def test_list_encryption_decryption(self):
        """Test list encryption and decryption"""
        manager = EncryptionManager("test_secret_key")
        
        original_data = ["allergy1", "allergy2", "allergy3"]
        encrypted = manager.encrypt_field(original_data)
        decrypted = manager.decrypt_field(encrypted)
        
        assert encrypted != str(original_data)
        assert decrypted == original_data
        assert isinstance(decrypted, list)
    
    def test_health_data_encryption(self):
        """Test health data encryption"""
        manager = EncryptionManager("test_secret_key")
        
        health_data = {
            "medical_conditions": "diabetes, hypertension",
            "medications": ["insulin", "metformin"],
            "allergies": ["penicillin", "sulfa drugs"],
            "blood_type": "O+",
            "family_history": {"diabetes": "father", "heart_disease": "mother"},
            "diagnoses": ["Type 2 Diabetes", "Hypertension"],
            "symptoms": ["fatigue", "thirst", "frequent urination"],
            "non_sensitive": "this should not be encrypted"
        }
        
        encrypted_data = manager.encrypt_health_data(health_data)
        
        # Check that sensitive fields are encrypted
        assert encrypted_data["medical_conditions"] != health_data["medical_conditions"]
        assert encrypted_data["medications"] != health_data["medications"]
        assert encrypted_data["allergies"] != health_data["allergies"]
        assert encrypted_data["blood_type"] != health_data["blood_type"]
        assert encrypted_data["family_history"] != health_data["family_history"]
        assert encrypted_data["diagnoses"] != health_data["diagnoses"]
        assert encrypted_data["symptoms"] != health_data["symptoms"]
        
        # Check that non-sensitive fields are not encrypted
        assert encrypted_data["non_sensitive"] == health_data["non_sensitive"]
        
        # Verify all encrypted fields are actually encrypted
        for field in ["medical_conditions", "medications", "allergies", "blood_type", 
                     "family_history", "diagnoses", "symptoms"]:
            assert manager.is_encrypted(encrypted_data[field])
    
    def test_health_data_decryption(self):
        """Test health data decryption"""
        manager = EncryptionManager("test_secret_key")
        
        health_data = {
            "medical_conditions": "diabetes, hypertension",
            "medications": ["insulin", "metformin"],
            "allergies": ["penicillin", "sulfa drugs"],
            "blood_type": "O+",
            "family_history": {"diabetes": "father", "heart_disease": "mother"},
            "diagnoses": ["Type 2 Diabetes", "Hypertension"],
            "symptoms": ["fatigue", "thirst", "frequent urination"]
        }
        
        encrypted_data = manager.encrypt_health_data(health_data)
        decrypted_data = manager.decrypt_health_data(encrypted_data)
        
        # Verify all fields are correctly decrypted
        assert decrypted_data["medical_conditions"] == health_data["medical_conditions"]
        assert decrypted_data["medications"] == health_data["medications"]
        assert decrypted_data["allergies"] == health_data["allergies"]
        assert decrypted_data["blood_type"] == health_data["blood_type"]
        assert decrypted_data["family_history"] == health_data["family_history"]
        assert decrypted_data["diagnoses"] == health_data["diagnoses"]
        assert decrypted_data["symptoms"] == health_data["symptoms"]
    
    def test_pii_encryption(self):
        """Test PII encryption"""
        manager = EncryptionManager("test_secret_key")
        
        pii_data = {
            "full_name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "+1-555-123-4567",
            "address": "123 Main St, Anytown, USA",
            "date_of_birth": "1985-03-15",
            "ssn": "123-45-6789",
            "insurance_number": "INS123456789"
        }
        
        encrypted_data = manager.encrypt_pii(pii_data)
        
        # Check that PII fields are encrypted
        assert encrypted_data["full_name"] != pii_data["full_name"]
        assert encrypted_data["phone"] != pii_data["phone"]
        assert encrypted_data["address"] != pii_data["address"]
        assert encrypted_data["date_of_birth"] != pii_data["date_of_birth"]
        assert encrypted_data["ssn"] != pii_data["ssn"]
        assert encrypted_data["insurance_number"] != pii_data["insurance_number"]
        
        # Email should not be encrypted (it's used for login)
        assert encrypted_data["email"] == pii_data["email"]
        
        # Verify all encrypted fields are actually encrypted
        for field in ["full_name", "phone", "address", "date_of_birth", "ssn", "insurance_number"]:
            assert manager.is_encrypted(encrypted_data[field])
    
    def test_pii_decryption(self):
        """Test PII decryption"""
        manager = EncryptionManager("test_secret_key")
        
        pii_data = {
            "full_name": "John Doe",
            "phone": "+1-555-123-4567",
            "address": "123 Main St, Anytown, USA",
            "date_of_birth": "1985-03-15",
            "ssn": "123-45-6789",
            "insurance_number": "INS123456789"
        }
        
        encrypted_data = manager.encrypt_pii(pii_data)
        decrypted_data = manager.decrypt_pii(encrypted_data)
        
        # Verify all fields are correctly decrypted
        assert decrypted_data["full_name"] == pii_data["full_name"]
        assert decrypted_data["phone"] == pii_data["phone"]
        assert decrypted_data["address"] == pii_data["address"]
        assert decrypted_data["date_of_birth"] == pii_data["date_of_birth"]
        assert decrypted_data["ssn"] == pii_data["ssn"]
        assert decrypted_data["insurance_number"] == pii_data["insurance_number"]
    
    def test_encryption_key_generation(self):
        """Test encryption key generation"""
        manager = EncryptionManager("test_secret_key")
        key = manager.generate_encryption_key()
        
        assert isinstance(key, str)
        assert len(key) > 0
        # Should be valid base64
        try:
            decoded_key = base64.urlsafe_b64decode(key.encode('utf-8'))
            assert len(decoded_key) == 44  # Fernet keys are 44 bytes when base64 decoded
        except Exception:
            pytest.fail("Generated key is not valid base64")
    
    def test_empty_field_handling(self):
        """Test handling of empty fields"""
        manager = EncryptionManager("test_secret_key")
        
        health_data = {
            "medical_conditions": "",
            "medications": None,
            "allergies": [],
            "blood_type": "O+"
        }
        
        encrypted_data = manager.encrypt_health_data(health_data)
        
        # Empty fields should not be encrypted
        assert encrypted_data["medical_conditions"] == ""
        assert encrypted_data["medications"] is None
        assert encrypted_data["allergies"] == []
        assert encrypted_data["blood_type"] != "O+"  # This should be encrypted
    
    def test_encryption_error_handling(self):
        """Test error handling during encryption"""
        manager = EncryptionManager("test_secret_key")
        
        # Test with invalid data type
        with pytest.raises(ValueError):
            manager.encrypt_field(object())  # Cannot serialize object
    
    def test_decryption_error_handling(self):
        """Test error handling during decryption"""
        manager = EncryptionManager("test_secret_key")
        
        # Test with invalid encrypted data
        with pytest.raises(ValueError):
            manager.decrypt_field("invalid_encrypted_data")

class TestFieldLevelEncryption:
    """Test field-level encryption for database models"""
    
    def test_model_field_encryption(self):
        """Test encryption of model fields"""
        manager = EncryptionManager("test_secret_key")
        field_encryption = FieldLevelEncryption(manager)
        
        # Create a test user
        user = User(
            email="test@example.com",
            hashed_password="hashed_password",
            full_name="John Doe",
            age=30,
            medical_conditions="diabetes",
            medications="insulin"
        )
        
        # Fields should be automatically encrypted in __init__
        assert user.full_name != "John Doe"
        assert user.medical_conditions != "diabetes"
        assert user.medications != "insulin"
        
        # Verify fields are encrypted
        assert manager.is_encrypted(user.full_name)
        assert manager.is_encrypted(user.medical_conditions)
        assert manager.is_encrypted(user.medications)
    
    def test_model_field_decryption(self):
        """Test decryption of model fields"""
        manager = EncryptionManager("test_secret_key")
        
        # Create a test user
        user = User(
            email="test@example.com",
            hashed_password="hashed_password",
            full_name="John Doe",
            age=30,
            medical_conditions="diabetes",
            medications="insulin"
        )
        
        # Decrypt fields
        user.decrypt_sensitive_fields()
        
        # Verify fields are decrypted
        assert user.full_name == "John Doe"
        assert user.medical_conditions == "diabetes"
        assert user.medications == "insulin"
    
    def test_user_to_dict_with_sensitive_data(self):
        """Test user to_dict method with sensitive data"""
        user = User(
            email="test@example.com",
            hashed_password="hashed_password",
            full_name="John Doe",
            age=30,
            medical_conditions="diabetes",
            medications="insulin",
            phone="+1-555-123-4567",
            blood_type="O+"
        )
        
        # Test without sensitive data
        user_dict = user.to_dict(include_sensitive=False)
        assert "full_name" not in user_dict
        assert "medical_conditions" not in user_dict
        assert "phone" not in user_dict
        assert "blood_type" not in user_dict
        assert user_dict["email"] == "test@example.com"
        assert user_dict["age"] == 30
        
        # Test with sensitive data
        user_dict = user.to_dict(include_sensitive=True)
        assert user_dict["full_name"] == "John Doe"
        assert user_dict["medical_conditions"] == "diabetes"
        assert user_dict["phone"] == "+1-555-123-4567"
        assert user_dict["blood_type"] == "O+"
    
    def test_encryption_consistency(self):
        """Test that encryption is consistent across multiple instances"""
        manager1 = EncryptionManager("test_secret_key")
        manager2 = EncryptionManager("test_secret_key")
        
        data = "sensitive data"
        encrypted1 = manager1.encrypt_field(data)
        encrypted2 = manager2.encrypt_field(data)
        
        # Both should be able to decrypt each other's data
        assert manager1.decrypt_field(encrypted2) == data
        assert manager2.decrypt_field(encrypted1) == data
    
    def test_different_keys_produce_different_encryption(self):
        """Test that different keys produce different encryption"""
        manager1 = EncryptionManager("key1")
        manager2 = EncryptionManager("key2")
        
        data = "sensitive data"
        encrypted1 = manager1.encrypt_field(data)
        encrypted2 = manager2.encrypt_field(data)
        
        # Different keys should produce different encrypted data
        assert encrypted1 != encrypted2
        
        # Each should only be able to decrypt its own data
        assert manager1.decrypt_field(encrypted1) == data
        assert manager2.decrypt_field(encrypted2) == data
        
        # Should not be able to decrypt each other's data
        with pytest.raises(ValueError):
            manager1.decrypt_field(encrypted2)
        with pytest.raises(ValueError):
            manager2.decrypt_field(encrypted1)

if __name__ == "__main__":
    pytest.main([__file__]) 
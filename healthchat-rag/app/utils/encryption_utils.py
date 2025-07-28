"""
Encryption Utilities for HealthMate
Provides encryption and decryption for sensitive health data
"""
import os
import base64
import json
from typing import Dict, Any, Optional, Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import logging
from app.config import settings

logger = logging.getLogger(__name__)

class EncryptionManager:
    """Manages encryption and decryption of sensitive data"""
    
    def __init__(self, master_key: Optional[str] = None):
        """
        Initialize encryption manager
        
        Args:
            master_key: Master encryption key (if not provided, will use SECRET_KEY)
        """
        self.master_key = master_key or settings.secret_key
        self._fernet = None
        self._initialize_fernet()
    
    def _initialize_fernet(self):
        """Initialize Fernet cipher with master key"""
        try:
            # Derive a key from the master key using PBKDF2
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'healthmate_salt',  # In production, use a random salt per user
                iterations=100000,
                backend=default_backend()
            )
            key = base64.urlsafe_b64encode(kdf.derive(self.master_key.encode()))
            self._fernet = Fernet(key)
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            raise
    
    def encrypt_field(self, data: Union[str, dict, list, None]) -> str:
        """
        Encrypt a single field or data structure
        
        Args:
            data: Data to encrypt (string, dict, list, or None)
            
        Returns:
            Encrypted data as base64 string
        """
        try:
            # Handle None and empty values
            if data is None:
                return ""
            
            # Convert data to JSON string if it's not already a string
            if not isinstance(data, str):
                data_str = json.dumps(data, ensure_ascii=False)
            else:
                data_str = data
            
            # Encrypt the data
            encrypted_data = self._fernet.encrypt(data_str.encode('utf-8'))
            return base64.urlsafe_b64encode(encrypted_data).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise ValueError(f"Failed to encrypt data: {e}")
    
    def decrypt_field(self, encrypted_data: str) -> Union[str, dict, list]:
        """
        Decrypt a single field or data structure
        
        Args:
            encrypted_data: Encrypted data as base64 string
            
        Returns:
            Decrypted data (string, dict, or list)
        """
        try:
            # Handle empty strings
            if not encrypted_data:
                return ""
            
            # Decode from base64
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            
            # Decrypt the data
            decrypted_bytes = self._fernet.decrypt(encrypted_bytes)
            decrypted_str = decrypted_bytes.decode('utf-8')
            
            # Try to parse as JSON, fallback to string
            try:
                return json.loads(decrypted_str)
            except json.JSONDecodeError:
                return decrypted_str
                
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError(f"Failed to decrypt data: {e}")
    
    def encrypt_health_data(self, health_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encrypt sensitive health data fields
        
        Args:
            health_data: Dictionary containing health data
            
        Returns:
            Dictionary with sensitive fields encrypted
        """
        encrypted_data = health_data.copy()
        
        # Define sensitive fields that should be encrypted
        sensitive_fields = [
            'medical_conditions', 'medications', 'diagnoses',
            'symptoms', 'allergies', 'family_history',
            'blood_type', 'emergency_contact', 'insurance_info',
            'prescriptions', 'lab_results', 'vital_signs',
            'value', 'notes', 'description', 'location', 'duration',
            'triggers', 'treatments', 'prescribed_by', 'side_effects',
            'target_value', 'current_value', 'message', 'data_point',
            'action_taken'
        ]
        
        for field in sensitive_fields:
            if field in encrypted_data and encrypted_data[field]:
                try:
                    encrypted_data[field] = self.encrypt_field(encrypted_data[field])
                except Exception as e:
                    logger.error(f"Failed to encrypt field {field}: {e}")
                    # Keep original data if encryption fails
                    continue
        
        return encrypted_data
    
    def decrypt_health_data(self, encrypted_health_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decrypt sensitive health data fields
        
        Args:
            encrypted_health_data: Dictionary containing encrypted health data
            
        Returns:
            Dictionary with sensitive fields decrypted
        """
        decrypted_data = encrypted_health_data.copy()
        
        # Define sensitive fields that should be decrypted
        sensitive_fields = [
            'medical_conditions', 'medications', 'diagnoses',
            'symptoms', 'allergies', 'family_history',
            'blood_type', 'emergency_contact', 'insurance_info',
            'prescriptions', 'lab_results', 'vital_signs',
            'value', 'notes', 'description', 'location', 'duration',
            'triggers', 'treatments', 'prescribed_by', 'side_effects',
            'target_value', 'current_value', 'message', 'data_point',
            'action_taken'
        ]
        
        for field in sensitive_fields:
            if field in decrypted_data and decrypted_data[field]:
                try:
                    decrypted_data[field] = self.decrypt_field(decrypted_data[field])
                except Exception as e:
                    logger.error(f"Failed to decrypt field {field}: {e}")
                    # Keep encrypted data if decryption fails
                    continue
        
        return decrypted_data
    
    def encrypt_pii(self, pii_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encrypt personally identifiable information
        
        Args:
            pii_data: Dictionary containing PII data
            
        Returns:
            Dictionary with PII fields encrypted
        """
        encrypted_data = pii_data.copy()
        
        # Define PII fields that should be encrypted (excluding email for login purposes)
        pii_fields = [
            'full_name', 'phone', 'address',
            'date_of_birth', 'ssn', 'passport_number',
            'driver_license', 'insurance_number'
        ]
        
        for field in pii_fields:
            if field in encrypted_data and encrypted_data[field]:
                try:
                    encrypted_data[field] = self.encrypt_field(encrypted_data[field])
                except Exception as e:
                    logger.error(f"Failed to encrypt PII field {field}: {e}")
                    continue
        
        return encrypted_data
    
    def decrypt_pii(self, encrypted_pii_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decrypt personally identifiable information
        
        Args:
            encrypted_pii_data: Dictionary containing encrypted PII data
            
        Returns:
            Dictionary with PII fields decrypted
        """
        decrypted_data = encrypted_pii_data.copy()
        
        # Define PII fields that should be decrypted (excluding email for login purposes)
        pii_fields = [
            'full_name', 'phone', 'address',
            'date_of_birth', 'ssn', 'passport_number',
            'driver_license', 'insurance_number'
        ]
        
        for field in pii_fields:
            if field in decrypted_data and decrypted_data[field]:
                try:
                    decrypted_data[field] = self.decrypt_field(decrypted_data[field])
                except Exception as e:
                    logger.error(f"Failed to decrypt PII field {field}: {e}")
                    continue
        
        return decrypted_data
    
    def generate_encryption_key(self) -> str:
        """
        Generate a new encryption key
        
        Returns:
            Base64 encoded encryption key
        """
        key = Fernet.generate_key()
        return base64.urlsafe_b64encode(key).decode('utf-8')
    
    def is_encrypted(self, data: str) -> bool:
        """
        Check if data appears to be encrypted
        
        Args:
            data: Data to check
            
        Returns:
            True if data appears to be encrypted
        """
        try:
            # Try to decode as base64
            decoded = base64.urlsafe_b64decode(data.encode('utf-8'))
            # Check if it looks like Fernet encrypted data
            return len(decoded) > 32 and decoded.startswith(b'gAAAAA')
        except Exception:
            return False
    
    def encrypt_health_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encrypt health metrics data
        
        Args:
            metrics: Dictionary containing health metrics
            
        Returns:
            Dictionary with sensitive metrics encrypted
        """
        encrypted_metrics = metrics.copy()
        
        # Define sensitive health metrics fields
        sensitive_metrics = [
            'blood_pressure_avg', 'heart_rate_avg', 'temperature_avg',
            'weight_latest', 'blood_glucose_avg', 'oxygen_saturation_avg',
            'sleep_hours_total', 'steps_total', 'calories_total',
            'pain_level_avg', 'mood_avg'
        ]
        
        for field in sensitive_metrics:
            if field in encrypted_metrics and encrypted_metrics[field]:
                try:
                    encrypted_metrics[field] = self.encrypt_field(encrypted_metrics[field])
                except Exception as e:
                    logger.error(f"Failed to encrypt health metric {field}: {e}")
                    continue
        
        return encrypted_metrics
    
    def decrypt_health_metrics(self, encrypted_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decrypt health metrics data
        
        Args:
            encrypted_metrics: Dictionary containing encrypted health metrics
            
        Returns:
            Dictionary with sensitive metrics decrypted
        """
        decrypted_metrics = encrypted_metrics.copy()
        
        # Define sensitive health metrics fields
        sensitive_metrics = [
            'blood_pressure_avg', 'heart_rate_avg', 'temperature_avg',
            'weight_latest', 'blood_glucose_avg', 'oxygen_saturation_avg',
            'sleep_hours_total', 'steps_total', 'calories_total',
            'pain_level_avg', 'mood_avg'
        ]
        
        for field in sensitive_metrics:
            if field in decrypted_metrics and decrypted_metrics[field]:
                try:
                    decrypted_metrics[field] = self.decrypt_field(decrypted_metrics[field])
                except Exception as e:
                    logger.error(f"Failed to decrypt health metric {field}: {e}")
                    continue
        
        return decrypted_metrics
    
    def validate_encryption_key(self) -> bool:
        """
        Validate that the encryption key is working properly
        
        Returns:
            True if encryption/decryption test passes
        """
        try:
            test_data = "test_health_data_123"
            encrypted = self.encrypt_field(test_data)
            decrypted = self.decrypt_field(encrypted)
            return decrypted == test_data
        except Exception as e:
            logger.error(f"Encryption key validation failed: {e}")
            return False

class FieldLevelEncryption:
    """Handles field-level encryption for database models"""
    
    def __init__(self, encryption_manager: EncryptionManager):
        self.encryption_manager = encryption_manager
    
    def encrypt_model_fields(self, model_instance, fields_to_encrypt: list):
        """
        Encrypt specific fields of a model instance
        
        Args:
            model_instance: SQLAlchemy model instance
            fields_to_encrypt: List of field names to encrypt
        """
        for field_name in fields_to_encrypt:
            if hasattr(model_instance, field_name):
                field_value = getattr(model_instance, field_name)
                if field_value and not self.encryption_manager.is_encrypted(str(field_value)):
                    try:
                        encrypted_value = self.encryption_manager.encrypt_field(field_value)
                        setattr(model_instance, field_name, encrypted_value)
                    except Exception as e:
                        logger.error(f"Failed to encrypt field {field_name}: {e}")
    
    def decrypt_model_fields(self, model_instance, fields_to_decrypt: list):
        """
        Decrypt specific fields of a model instance
        
        Args:
            model_instance: SQLAlchemy model instance
            fields_to_decrypt: List of field names to decrypt
        """
        for field_name in fields_to_decrypt:
            if hasattr(model_instance, field_name):
                field_value = getattr(model_instance, field_name)
                if field_value and self.encryption_manager.is_encrypted(str(field_value)):
                    try:
                        decrypted_value = self.encryption_manager.decrypt_field(field_value)
                        setattr(model_instance, field_name, decrypted_value)
                    except Exception as e:
                        logger.error(f"Failed to decrypt field {field_name}: {e}")

# Global encryption manager instance
encryption_manager = EncryptionManager()

# Global field-level encryption instance
field_encryption = FieldLevelEncryption(encryption_manager) 
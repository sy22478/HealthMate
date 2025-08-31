"""
Password Security Utilities
Provides password hashing, validation, and strength checking
"""
import re
import hashlib
import secrets
from typing import Dict, List, Tuple
from passlib.context import CryptContext
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)

class PasswordValidator:
    """Password strength validator"""
    
    def __init__(self):
        self.min_length = 8
        self.max_length = 128
        self.require_uppercase = True
        self.require_lowercase = True
        self.require_digits = True
        self.require_special_chars = True
        self.special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        
        # Common weak passwords to check against
        self.common_passwords = {
            "password", "123456", "123456789", "qwerty", "abc123",
            "password123", "admin", "letmein", "welcome", "monkey",
            "dragon", "master", "hello", "freedom", "whatever",
            "qazwsx", "trustno1", "jordan", "harley", "ranger",
            "iwantu", "jennifer", "hunter", "buster", "soccer",
            "baseball", "tequiero", "princess", "merlin", "diamond",
            "ncc1701", "computer", "amanda", "summer", "love",
            "ashley", "nicole", "chelsea", "biteme", "matthew",
            "access", "yankees", "987654321", "dallas", "austin",
            "thunder", "taylor", "matrix", "mobilemail", "mom",
            "monitor", "monitoring", "montana", "moon", "moscow"
        }
    
    def validate_password(self, password: str) -> Tuple[bool, List[str]]:
        """
        Validate password strength
        
        Args:
            password: Password to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check length
        if len(password) < self.min_length:
            errors.append(f"Password must be at least {self.min_length} characters long")
        
        if len(password) > self.max_length:
            errors.append(f"Password must be no more than {self.max_length} characters long")
        
        # Check for uppercase letters
        if self.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        # Check for lowercase letters
        if self.require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        # Check for digits
        if self.require_digits and not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")
        
        # Check for special characters
        if self.require_special_chars and not re.search(f'[{re.escape(self.special_chars)}]', password):
            errors.append("Password must contain at least one special character")
        
        # Check against common passwords
        if password.lower() in self.common_passwords:
            errors.append("Password is too common. Please choose a more unique password")
        
        # Check for repeated characters
        if re.search(r'(.)\1{2,}', password):
            errors.append("Password contains too many repeated characters")
        
        # (Removed overly strict sequential character check)
        
        return len(errors) == 0, errors
    
    def get_password_strength(self, password: str) -> Dict[str, any]:
        """
        Get detailed password strength analysis
        
        Args:
            password: Password to analyze
            
        Returns:
            Dictionary with strength analysis
        """
        is_valid, errors = self.validate_password(password)
        
        # Calculate entropy
        charset_size = 0
        if re.search(r'[a-z]', password):
            charset_size += 26
        if re.search(r'[A-Z]', password):
            charset_size += 26
        if re.search(r'\d', password):
            charset_size += 10
        if re.search(f'[{re.escape(self.special_chars)}]', password):
            charset_size += len(self.special_chars)
        
        entropy = len(password) * (charset_size ** 0.5)
        
        # Determine strength level
        if entropy < 20:
            strength = "very_weak"
        elif entropy < 30:
            strength = "weak"
        elif entropy < 40:
            strength = "medium"
        elif entropy < 50:
            strength = "strong"
        else:
            strength = "very_strong"
        
        return {
            "is_valid": is_valid,
            "errors": errors,
            "entropy": entropy,
            "strength": strength,
            "length": len(password),
            "has_uppercase": bool(re.search(r'[A-Z]', password)),
            "has_lowercase": bool(re.search(r'[a-z]', password)),
            "has_digits": bool(re.search(r'\d', password)),
            "has_special_chars": bool(re.search(f'[{re.escape(self.special_chars)}]', password)),
            "is_common": password.lower() in self.common_passwords
        }

class PasswordManager:
    """Password management utilities"""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.validator = PasswordValidator()
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password
            
        Returns:
            True if password matches, False otherwise
        """
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def validate_and_hash_password(self, password: str) -> Tuple[str, List[str]]:
        """
        Validate password strength and hash it if valid
        
        Args:
            password: Plain text password
            
        Returns:
            Tuple of (hashed_password, list_of_errors)
        """
        is_valid, errors = self.validator.validate_password(password)
        
        if not is_valid:
            return "", errors
        
        hashed_password = self.hash_password(password)
        return hashed_password, []
    
    def generate_secure_password(self, length: int = 16) -> str:
        """
        Generate a secure random password
        
        Args:
            length: Password length
            
        Returns:
            Secure random password
        """
        if length < 8:
            length = 8
        
        # Ensure at least one character from each required category
        password_parts = [
            secrets.choice("abcdefghijklmnopqrstuvwxyz"),  # lowercase
            secrets.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ"),  # uppercase
            secrets.choice("0123456789"),  # digits
            secrets.choice("!@#$%^&*()_+-=[]{}|;:,.<>?")  # special chars
        ]
        
        # Fill the rest with random characters
        remaining_length = length - len(password_parts)
        all_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?"
        
        for _ in range(remaining_length):
            password_parts.append(secrets.choice(all_chars))
        
        # Shuffle the password
        password_list = list(password_parts)
        secrets.SystemRandom().shuffle(password_list)
        
        return ''.join(password_list)
    
    def create_password_reset_token(self) -> str:
        """
        Create a secure password reset token
        
        Returns:
            Secure random token
        """
        return secrets.token_urlsafe(32)
    
    def hash_reset_token(self, token: str) -> str:
        """
        Hash a reset token for storage
        
        Args:
            token: Plain reset token
            
        Returns:
            Hashed reset token
        """
        return hashlib.sha256(token.encode()).hexdigest()
    
    def verify_reset_token(self, plain_token: str, hashed_token: str) -> bool:
        """
        Verify a reset token
        
        Args:
            plain_token: Plain reset token
            hashed_token: Hashed reset token
            
        Returns:
            True if token matches, False otherwise
        """
        return self.hash_reset_token(plain_token) == hashed_token

def validate_password_strength(password: str) -> bool:
    """
    Validate password strength.

    Args:
        password: Password to validate

    Returns:
        True if password is valid, False otherwise
    """
    is_valid, _ = password_manager.validator.validate_password(password)
    return is_valid

# Global password manager instance
password_manager = PasswordManager() 
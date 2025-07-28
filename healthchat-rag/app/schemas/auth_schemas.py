"""
Authentication Pydantic Schemas
Comprehensive schemas for user authentication and authorization
"""
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, EmailStr
from datetime import datetime
from enum import Enum
from app.utils.rbac import UserRole

class UserRoleEnum(str, Enum):
    """User role enumeration"""
    PATIENT = "patient"
    DOCTOR = "doctor"
    ADMIN = "admin"
    RESEARCHER = "researcher"

class UserRegister(BaseModel):
    """User registration schema"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=128, description="User password")
    full_name: str = Field(..., min_length=2, max_length=100, description="User full name")
    age: Optional[int] = Field(None, ge=0, le=150, description="User age")
    role: UserRoleEnum = Field(default=UserRoleEnum.PATIENT, description="User role")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    address: Optional[str] = Field(None, max_length=200, description="Address")
    date_of_birth: Optional[datetime] = Field(None, description="Date of birth")
    emergency_contact: Optional[str] = Field(None, max_length=200, description="Emergency contact")
    insurance_info: Optional[str] = Field(None, max_length=500, description="Insurance information")
    medical_conditions: Optional[str] = Field(None, max_length=1000, description="Medical conditions")
    medications: Optional[str] = Field(None, max_length=1000, description="Current medications")
    blood_type: Optional[str] = Field(None, max_length=10, description="Blood type")
    allergies: Optional[str] = Field(None, max_length=500, description="Allergies")
    family_history: Optional[str] = Field(None, max_length=1000, description="Family medical history")
    diagnoses: Optional[str] = Field(None, max_length=1000, description="Medical diagnoses")
    symptoms: Optional[str] = Field(None, max_length=1000, description="Current symptoms")

    @field_validator('password')
    def validate_password_strength(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError("Password must contain at least one special character")
        return v

    @field_validator('full_name')
    def validate_full_name(cls, v):
        """Validate full name format"""
        if not v.strip():
            raise ValueError("Full name cannot be empty")
        if len(v.strip().split()) < 2:
            raise ValueError("Full name must contain at least first and last name")
        return v.strip()

    @field_validator('phone')
    def validate_phone(cls, v):
        """Validate phone number format"""
        if v is None:
            return v
        # Remove all non-digit characters
        digits_only = ''.join(filter(str.isdigit, v))
        if len(digits_only) < 10 or len(digits_only) > 15:
            raise ValueError("Phone number must be between 10 and 15 digits")
        return v

    @field_validator('age')
    def validate_age(cls, v):
        """Validate age range"""
        if v is not None and (v < 0 or v > 150):
            raise ValueError("Age must be between 0 and 150")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "email": "john.doe@example.com",
                "password": "SecurePass123!",
                "full_name": "John Doe",
                "age": 30,
                "role": "patient",
                "phone": "+1-555-123-4567",
                "address": "123 Main St, City, State 12345",
                "date_of_birth": "1994-01-01T00:00:00Z",
                "emergency_contact": "Jane Doe, +1-555-987-6543",
                "insurance_info": "Blue Cross Blue Shield, Policy #123456",
                "medical_conditions": "Hypertension, Type 2 Diabetes",
                "medications": "Metformin 500mg twice daily, Lisinopril 10mg daily",
                "blood_type": "O+",
                "allergies": "Penicillin, Peanuts",
                "family_history": "Father: Heart disease, Mother: Diabetes",
                "diagnoses": "Type 2 Diabetes (2020), Hypertension (2019)",
                "symptoms": "Frequent urination, increased thirst"
            }
        }

class UserLogin(BaseModel):
    """User login schema"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "john.doe@example.com",
                "password": "SecurePass123!"
            }
        }

class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user_id: int = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    role: UserRoleEnum = Field(..., description="User role")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600,
                "user_id": 123,
                "email": "john.doe@example.com",
                "role": "patient"
            }
        }

class UserResponse(BaseModel):
    """User response schema (without sensitive data)"""
    id: int = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    full_name: str = Field(..., description="User full name")
    role: UserRoleEnum = Field(..., description="User role")
    age: Optional[int] = Field(None, description="User age")
    phone: Optional[str] = Field(None, description="Phone number")
    address: Optional[str] = Field(None, description="Address")
    date_of_birth: Optional[datetime] = Field(None, description="Date of birth")
    emergency_contact: Optional[str] = Field(None, description="Emergency contact")
    insurance_info: Optional[str] = Field(None, description="Insurance information")
    medical_conditions: Optional[str] = Field(None, description="Medical conditions")
    medications: Optional[str] = Field(None, description="Current medications")
    blood_type: Optional[str] = Field(None, description="Blood type")
    allergies: Optional[str] = Field(None, description="Allergies")
    family_history: Optional[str] = Field(None, description="Family medical history")
    diagnoses: Optional[str] = Field(None, description="Medical diagnoses")
    symptoms: Optional[str] = Field(None, description="Current symptoms")
    is_active: bool = Field(..., description="User account status")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 123,
                "email": "john.doe@example.com",
                "full_name": "John Doe",
                "role": "patient",
                "age": 30,
                "phone": "+1-555-123-4567",
                "address": "123 Main St, City, State 12345",
                "date_of_birth": "1994-01-01T00:00:00Z",
                "emergency_contact": "Jane Doe, +1-555-987-6543",
                "insurance_info": "Blue Cross Blue Shield, Policy #123456",
                "medical_conditions": "Hypertension, Type 2 Diabetes",
                "medications": "Metformin 500mg twice daily, Lisinopril 10mg daily",
                "blood_type": "O+",
                "allergies": "Penicillin, Peanuts",
                "family_history": "Father: Heart disease, Mother: Diabetes",
                "diagnoses": "Type 2 Diabetes (2020), Hypertension (2019)",
                "symptoms": "Frequent urination, increased thirst",
                "is_active": True,
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z"
            }
        }

class PasswordChange(BaseModel):
    """Password change schema"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    confirm_password: str = Field(..., description="Password confirmation")

    @field_validator('new_password')
    def validate_new_password_strength(cls, v):
        """Validate new password strength"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError("Password must contain at least one special character")
        return v

    @field_validator('confirm_password')
    def validate_password_confirmation(cls, v, values):
        """Validate password confirmation"""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError("Password confirmation does not match")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "current_password": "OldPass123!",
                "new_password": "NewSecurePass456!",
                "confirm_password": "NewSecurePass456!"
            }
        }

class PasswordReset(BaseModel):
    """Password reset request schema"""
    email: EmailStr = Field(..., description="User email address")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "john.doe@example.com"
            }
        }

class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema"""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    confirm_password: str = Field(..., description="Password confirmation")

    @field_validator('new_password')
    def validate_new_password_strength(cls, v):
        """Validate new password strength"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError("Password must contain at least one special character")
        return v

    @field_validator('confirm_password')
    def validate_password_confirmation(cls, v, values):
        """Validate password confirmation"""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError("Password confirmation does not match")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "token": "reset_token_123456",
                "new_password": "NewSecurePass456!",
                "confirm_password": "NewSecurePass456!"
            }
        }

class UserProfile(BaseModel):
    """User profile update schema"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100, description="User full name")
    age: Optional[int] = Field(None, ge=0, le=150, description="User age")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    address: Optional[str] = Field(None, max_length=200, description="Address")
    date_of_birth: Optional[datetime] = Field(None, description="Date of birth")
    emergency_contact: Optional[str] = Field(None, max_length=200, description="Emergency contact")
    insurance_info: Optional[str] = Field(None, max_length=500, description="Insurance information")
    medical_conditions: Optional[str] = Field(None, max_length=1000, description="Medical conditions")
    medications: Optional[str] = Field(None, max_length=1000, description="Current medications")
    blood_type: Optional[str] = Field(None, max_length=10, description="Blood type")
    allergies: Optional[str] = Field(None, max_length=500, description="Allergies")
    family_history: Optional[str] = Field(None, max_length=1000, description="Family medical history")
    diagnoses: Optional[str] = Field(None, max_length=1000, description="Medical diagnoses")
    symptoms: Optional[str] = Field(None, max_length=1000, description="Current symptoms")

    @field_validator('full_name')
    def validate_full_name(cls, v):
        """Validate full name format"""
        if v is not None:
            if not v.strip():
                raise ValueError("Full name cannot be empty")
            if len(v.strip().split()) < 2:
                raise ValueError("Full name must contain at least first and last name")
            return v.strip()
        return v

    @field_validator('phone')
    def validate_phone(cls, v):
        """Validate phone number format"""
        if v is not None:
            digits_only = ''.join(filter(str.isdigit, v))
            if len(digits_only) < 10 or len(digits_only) > 15:
                raise ValueError("Phone number must be between 10 and 15 digits")
        return v

    @field_validator('age')
    def validate_age(cls, v):
        """Validate age range"""
        if v is not None and (v < 0 or v > 150):
            raise ValueError("Age must be between 0 and 150")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "full_name": "John Doe",
                "age": 30,
                "phone": "+1-555-123-4567",
                "address": "123 Main St, City, State 12345",
                "date_of_birth": "1994-01-01T00:00:00Z",
                "emergency_contact": "Jane Doe, +1-555-987-6543",
                "insurance_info": "Blue Cross Blue Shield, Policy #123456",
                "medical_conditions": "Hypertension, Type 2 Diabetes",
                "medications": "Metformin 500mg twice daily, Lisinopril 10mg daily",
                "blood_type": "O+",
                "allergies": "Penicillin, Peanuts",
                "family_history": "Father: Heart disease, Mother: Diabetes",
                "diagnoses": "Type 2 Diabetes (2020), Hypertension (2019)",
                "symptoms": "Frequent urination, increased thirst"
            }
        }

class TokenRefresh(BaseModel):
    """Token refresh schema"""
    refresh_token: str = Field(..., description="JWT refresh token")

    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }

class LogoutRequest(BaseModel):
    """Logout request schema"""
    refresh_token: str = Field(..., description="JWT refresh token to invalidate")

    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        } 
"""
Health Data Exceptions for HealthMate Application

This module provides health data-related exception classes for handling
health data processing, encryption, and medical data errors.
"""

import logging
from typing import Any, Dict, Optional

from .base_exceptions import HealthMateException, ErrorCode


class HealthDataError(HealthMateException):
    """Exception raised for health data related errors."""
    
    def __init__(
        self,
        message: str,
        data_type: Optional[str] = None,
        user_id: Optional[int] = None,
        error_code: ErrorCode = ErrorCode.HEALTH_DATA_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=500,
            details=details or {
                "data_type": data_type,
                "user_id": user_id
            },
            log_level=logging.ERROR
        )
        self.data_type = data_type
        self.user_id = user_id


class MedicalDataError(HealthDataError):
    """Exception raised for medical data specific errors."""
    
    def __init__(
        self,
        message: str,
        medical_data_type: Optional[str] = None,
        user_id: Optional[int] = None,
        severity: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            data_type=medical_data_type,
            user_id=user_id,
            error_code=ErrorCode.INVALID_HEALTH_DATA,
            details=details or {"severity": severity}
        )
        self.medical_data_type = medical_data_type
        self.severity = severity 


class BusinessIntelligenceError(HealthMateException):
    """Exception raised for business intelligence related errors"""
    def __init__(self, message: str, error_code: str = "BI_ERROR", details: Dict[str, Any] = None):
        super().__init__(message, error_code, details)
        self.error_type = "BusinessIntelligenceError"


class MLDataPreparationError(HealthMateException):
    """Exception raised for ML data preparation related errors"""
    def __init__(self, message: str, error_code: str = "ML_DATA_PREP_ERROR", details: Dict[str, Any] = None):
        super().__init__(message, error_code, details)
        self.error_type = "MLDataPreparationError" 
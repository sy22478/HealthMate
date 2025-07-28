"""
Validation Exceptions for HealthMate Application

This module provides validation-related exception classes for handling
input validation, schema validation, and data validation errors.
"""

import logging
from typing import Any, Dict, Optional

from .base_exceptions import HealthMateException, ErrorCode


class ValidationError(HealthMateException):
    """Exception raised for validation errors."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.VALIDATION_ERROR,
            status_code=422,
            details=details or {"field": field, "value": value},
            log_level=logging.WARNING
        )
        self.field = field
        self.value = value


class SchemaValidationError(ValidationError):
    """Exception raised for schema validation errors."""
    
    def __init__(
        self,
        message: str,
        schema_name: Optional[str] = None,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            field=field,
            value=value,
            details=details or {"schema_name": schema_name}
        )
        self.schema_name = schema_name


class InputValidationError(ValidationError):
    """Exception raised for input validation errors."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        validation_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            field=field,
            value=value,
            details=details or {"validation_type": validation_type}
        )
        self.validation_type = validation_type 
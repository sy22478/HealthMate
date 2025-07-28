"""
Base Exceptions for HealthMate Application

This module provides the foundation exception classes and error codes
for the HealthMate application.
"""

import logging
from typing import Any, Dict, Optional, Union
from enum import Enum
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class ErrorCode(Enum):
    """Standard error codes for HealthMate application."""
    
    # General errors (1000-1999)
    UNKNOWN_ERROR = 1000
    INVALID_REQUEST = 1001
    RESOURCE_NOT_FOUND = 1002
    PERMISSION_DENIED = 1003
    RATE_LIMIT_EXCEEDED = 1004
    SERVICE_UNAVAILABLE = 1005
    
    # Authentication errors (2000-2999)
    AUTHENTICATION_FAILED = 2000
    INVALID_TOKEN = 2001
    TOKEN_EXPIRED = 2002
    INSUFFICIENT_PERMISSIONS = 2003
    ACCOUNT_LOCKED = 2004
    INVALID_CREDENTIALS = 2005
    
    # Validation errors (3000-3999)
    VALIDATION_ERROR = 3000
    INVALID_INPUT = 3001
    MISSING_REQUIRED_FIELD = 3002
    INVALID_FORMAT = 3003
    DUPLICATE_ENTRY = 3004
    CONSTRAINT_VIOLATION = 3005
    
    # Database errors (4000-4999)
    DATABASE_ERROR = 4000
    CONNECTION_ERROR = 4001
    QUERY_ERROR = 4002
    TRANSACTION_ERROR = 4003
    INTEGRITY_ERROR = 4004
    
    # External API errors (5000-5999)
    EXTERNAL_API_ERROR = 5000
    API_TIMEOUT = 5001
    API_RATE_LIMIT = 5002
    API_AUTHENTICATION_ERROR = 5003
    API_SERVICE_UNAVAILABLE = 5004
    
    # Health data errors (6000-6999)
    HEALTH_DATA_ERROR = 6000
    INVALID_HEALTH_DATA = 6001
    ENCRYPTION_ERROR = 6002
    DECRYPTION_ERROR = 6003
    DATA_CORRUPTION = 6004
    
    # Chat/AI errors (7000-7999)
    CHAT_ERROR = 7000
    AI_SERVICE_ERROR = 7001
    VECTOR_STORE_ERROR = 7002
    KNOWLEDGE_BASE_ERROR = 7003
    RESPONSE_GENERATION_ERROR = 7004


class HealthMateException(Exception):
    """
    Base exception class for all HealthMate application exceptions.
    
    This class provides a standardized way to handle errors across the application
    with proper error codes, messages, and additional context.
    """
    
    def __init__(
        self,
        message: str,
        error_code: Union[ErrorCode, int] = ErrorCode.UNKNOWN_ERROR,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        log_level: int = logging.ERROR
    ):
        """
        Initialize the HealthMateException.
        
        Args:
            message: Human-readable error message
            error_code: Application-specific error code
            status_code: HTTP status code for API responses
            details: Additional error details
            context: Context information for debugging
            log_level: Logging level for this exception
        """
        super().__init__(message)
        
        self.message = message
        self.error_code = error_code if isinstance(error_code, ErrorCode) else ErrorCode(error_code)
        self.status_code = status_code
        self.details = details or {}
        self.context = context or {}
        self.timestamp = datetime.now(timezone.utc)
        self.log_level = log_level
        
        # Log the exception
        self._log_exception()
    
    def _log_exception(self):
        """Log the exception with appropriate level and context."""
        log_message = f"HealthMateException: {self.message} (Code: {self.error_code.value})"
        
        if self.context:
            log_message += f" | Context: {self.context}"
        
        if self.details:
            log_message += f" | Details: {self.details}"
        
        logger.log(self.log_level, log_message, exc_info=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": {
                "code": self.error_code.value,
                "message": self.message,
                "status_code": self.status_code,
                "timestamp": self.timestamp.isoformat(),
                "details": self.details,
                "type": self.__class__.__name__
            }
        }
    
    def __str__(self) -> str:
        """String representation of the exception."""
        return f"{self.__class__.__name__}: {self.message} (Code: {self.error_code.value})"
    
    def __repr__(self) -> str:
        """Detailed string representation for debugging."""
        return (
            f"{self.__class__.__name__}("
            f"message='{self.message}', "
            f"error_code={self.error_code}, "
            f"status_code={self.status_code}, "
            f"details={self.details}, "
            f"context={self.context}"
            f")"
        )


class ResourceNotFoundError(HealthMateException):
    """Exception raised when a requested resource is not found."""
    
    def __init__(
        self,
        resource_type: str,
        resource_id: Optional[Union[str, int]] = None,
        message: Optional[str] = None
    ):
        if not message:
            if resource_id:
                message = f"{resource_type} with id '{resource_id}' not found"
            else:
                message = f"{resource_type} not found"
        
        super().__init__(
            message=message,
            error_code=ErrorCode.RESOURCE_NOT_FOUND,
            status_code=404,
            details={"resource_type": resource_type, "resource_id": resource_id},
            log_level=logging.INFO
        )
        self.resource_type = resource_type
        self.resource_id = resource_id 
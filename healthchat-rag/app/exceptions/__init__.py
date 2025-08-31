"""
Custom Exceptions for HealthMate Application

This module provides comprehensive exception handling for the HealthMate application,
including custom exception classes and global exception handlers.
"""

from .base_exceptions import HealthMateException, ResourceNotFoundError, ErrorCode
from .validation_exceptions import ValidationError, SchemaValidationError, InputValidationError
from .auth_exceptions import AuthenticationError, AuthorizationError, TokenError
from .database_exceptions import DatabaseError, ConnectionError, QueryError
from .external_api_exceptions import ExternalAPIError, APIError, RateLimitError
from .health_exceptions import HealthDataError, MedicalDataError
from .chat_exceptions import ChatError, ConversationError
from .notification_exceptions import NotificationError, EmailError, SMSError
from .vector_store_exceptions import VectorStoreError

__all__ = [
    # Base exceptions
    "HealthMateException",
    "ResourceNotFoundError",
    "ErrorCode",
    
    # Validation exceptions
    "ValidationError",
    "SchemaValidationError", 
    "InputValidationError",
    
    # Authentication exceptions
    "AuthenticationError",
    "AuthorizationError",
    "TokenError",
    
    # Database exceptions
    "DatabaseError",
    "ConnectionError",
    "QueryError",
    
    # External API exceptions
    "ExternalAPIError",
    "APIError",
    "RateLimitError",
    
    # Health exceptions
    "HealthDataError",
    "MedicalDataError",
    
    # Chat exceptions
    "ChatError",
    "ConversationError",
    "VectorStoreError",
    
    # Notification exceptions
    "NotificationError",
    "EmailError",
    "SMSError",
] 
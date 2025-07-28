"""
Authentication Exceptions for HealthMate Application

This module provides authentication and authorization related exception classes
for handling login, token, and permission errors.
"""

import logging
from typing import Any, Dict, Optional, List

from .base_exceptions import HealthMateException, ErrorCode


class AuthenticationError(HealthMateException):
    """Exception raised for authentication errors."""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.AUTHENTICATION_FAILED,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=401,
            details=details,
            log_level=logging.WARNING
        )


class AuthorizationError(HealthMateException):
    """Exception raised for authorization errors."""
    
    def __init__(
        self,
        message: str,
        required_permissions: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.INSUFFICIENT_PERMISSIONS,
            status_code=403,
            details=details or {"required_permissions": required_permissions},
            log_level=logging.WARNING
        )
        self.required_permissions = required_permissions


class TokenError(AuthenticationError):
    """Exception raised for token-related errors."""
    
    def __init__(
        self,
        message: str,
        token_type: Optional[str] = None,
        error_code: ErrorCode = ErrorCode.INVALID_TOKEN,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            details=details or {"token_type": token_type}
        )
        self.token_type = token_type 
"""
External API Exceptions for HealthMate Application

This module provides external API-related exception classes for handling
API integration errors, timeouts, and rate limiting.
"""

import logging
from typing import Any, Dict, Optional

from .base_exceptions import HealthMateException, ErrorCode


class ExternalAPIError(HealthMateException):
    """Exception raised for external API errors."""
    
    def __init__(
        self,
        message: str,
        api_name: str,
        error_code: ErrorCode = ErrorCode.EXTERNAL_API_ERROR,
        response_status: Optional[int] = None,
        response_body: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=502,  # Bad Gateway
            details=details or {
                "api_name": api_name,
                "response_status": response_status,
                "response_body": response_body
            },
            log_level=logging.ERROR
        )
        self.api_name = api_name
        self.response_status = response_status
        self.response_body = response_body


class APIError(ExternalAPIError):
    """Exception raised for general API errors."""
    
    def __init__(
        self,
        message: str,
        api_name: str,
        endpoint: Optional[str] = None,
        response_status: Optional[int] = None,
        response_body: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            api_name=api_name,
            response_status=response_status,
            response_body=response_body,
            details=details or {"endpoint": endpoint}
        )
        self.endpoint = endpoint


class RateLimitError(HealthMateException):
    """Exception raised when rate limits are exceeded."""
    
    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        limit: Optional[int] = None,
        window: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
            status_code=429,
            details=details or {
                "retry_after": retry_after,
                "limit": limit,
                "window": window
            },
            log_level=logging.WARNING
        )
        self.retry_after = retry_after
        self.limit = limit
        self.window = window 
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


class APIConnectionError(ExternalAPIError):
    """Exception raised for API connection errors."""

    def __init__(
        self,
        message: str = "API connection failed",
        api_name: str = "unknown",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            api_name=api_name,
            error_code=ErrorCode.CONNECTION_ERROR,
            details=details
        )


class APIRateLimitError(ExternalAPIError):
    """Exception raised for API rate limit errors."""

    def __init__(
        self,
        message: str,
        api_name: str,
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            api_name=api_name,
            error_code=ErrorCode.API_RATE_LIMIT,
            details=details or {"retry_after": retry_after}
        )
        self.retry_after = retry_after


class APIAuthenticationError(ExternalAPIError):
    """Exception raised for API authentication errors."""

    def __init__(
        self,
        message: str,
        api_name: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            api_name=api_name,
            error_code=ErrorCode.API_AUTHENTICATION_ERROR,
            details=details
        )

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


class StorageServiceError(ExternalAPIError):
    """Exception raised for storage service errors (e.g., S3)."""

    def __init__(
        self,
        message: str,
        storage_provider: str = "unknown",
        bucket_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            api_name=f"storage-service-{storage_provider}",
            error_code=ErrorCode.STORAGE_SERVICE_ERROR,
            details=details or {"storage_provider": storage_provider, "bucket_name": bucket_name}
        )
        self.storage_provider = storage_provider
        self.bucket_name = bucket_name


class APIResponseError(ExternalAPIError):
    """Exception raised for invalid or unexpected API responses."""

    def __init__(
        self,
        message: str,
        api_name: str,
        response_status: Optional[int] = None,
        response_body: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            api_name=api_name,
            error_code=ErrorCode.API_RESPONSE_ERROR,
            response_status=response_status,
            response_body=response_body,
            details=details
        )


class InfrastructureError(ExternalAPIError):
    """Exception raised for infrastructure-related errors."""

    def __init__(
        self,
        message: str,
        service_name: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            api_name=f"infrastructure-service-{service_name}",
            error_code=ErrorCode.INFRASTRUCTURE_ERROR,
            details=details
        )
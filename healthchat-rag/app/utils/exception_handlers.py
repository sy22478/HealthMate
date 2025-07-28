"""
FastAPI Exception Handlers

This module provides exception handlers for FastAPI to integrate with the custom
HealthMate exception system and provide consistent error responses.
"""

import logging
from typing import Any, Dict, Union
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.exceptions import (
    HealthMateException,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    DatabaseError,
    ExternalAPIError,
    HealthDataError,
    ChatError,
    ResourceNotFoundError,
    RateLimitError,
    ErrorCode
)

logger = logging.getLogger(__name__)


def setup_exception_handlers(app: FastAPI) -> None:
    """
    Setup all exception handlers for the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    
    @app.exception_handler(HealthMateException)
    async def healthmate_exception_handler(request: Request, exc: HealthMateException) -> JSONResponse:
        """Handle HealthMate exceptions."""
        logger.error(
            f"HealthMateException: {exc.message} (Code: {exc.error_code.value})",
            extra={
                "error_code": exc.error_code.value,
                "status_code": exc.status_code,
                "path": request.url.path,
                "method": request.method,
                "details": exc.details,
                "context": exc.context
            }
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict()
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """Handle Pydantic validation errors from FastAPI."""
        errors = []
        for error in exc.errors():
            errors.append({
                "field": " -> ".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
                "value": error.get("input")
            })
        
        validation_error = ValidationError(
            message="Request validation failed",
            details={"validation_errors": errors}
        )
        
        logger.warning(
            f"Request validation failed: {len(errors)} errors",
            extra={
                "path": request.url.path,
                "method": request.method,
                "validation_errors": errors
            }
        )
        
        return JSONResponse(
            status_code=validation_error.status_code,
            content=validation_error.to_dict()
        )
    
    @app.exception_handler(PydanticValidationError)
    async def pydantic_validation_exception_handler(request: Request, exc: PydanticValidationError) -> JSONResponse:
        """Handle Pydantic validation errors."""
        errors = []
        for error in exc.errors():
            errors.append({
                "field": " -> ".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
                "value": error.get("input")
            })
        
        validation_error = ValidationError(
            message="Data validation failed",
            details={"validation_errors": errors}
        )
        
        logger.warning(
            f"Pydantic validation failed: {len(errors)} errors",
            extra={
                "path": request.url.path,
                "method": request.method,
                "validation_errors": errors
            }
        )
        
        return JSONResponse(
            status_code=validation_error.status_code,
            content=validation_error.to_dict()
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """Handle FastAPI HTTP exceptions."""
        # Map common HTTP status codes to HealthMate error codes
        error_code_map = {
            400: ErrorCode.INVALID_REQUEST,
            401: ErrorCode.AUTHENTICATION_FAILED,
            403: ErrorCode.INSUFFICIENT_PERMISSIONS,
            404: ErrorCode.RESOURCE_NOT_FOUND,
            409: ErrorCode.DUPLICATE_ENTRY,
            422: ErrorCode.VALIDATION_ERROR,
            429: ErrorCode.RATE_LIMIT_EXCEEDED,
            500: ErrorCode.UNKNOWN_ERROR,
            502: ErrorCode.EXTERNAL_API_ERROR,
            503: ErrorCode.SERVICE_UNAVAILABLE
        }
        
        error_code = error_code_map.get(exc.status_code, ErrorCode.UNKNOWN_ERROR)
        
        healthmate_exc = HealthMateException(
            message=exc.detail,
            error_code=error_code,
            status_code=exc.status_code
        )
        
        logger.warning(
            f"HTTPException: {exc.detail} (Status: {exc.status_code})",
            extra={
                "path": request.url.path,
                "method": request.method,
                "status_code": exc.status_code
            }
        )
        
        return JSONResponse(
            status_code=healthmate_exc.status_code,
            content=healthmate_exc.to_dict()
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        """Handle Starlette HTTP exceptions."""
        # Map common HTTP status codes to HealthMate error codes
        error_code_map = {
            400: ErrorCode.INVALID_REQUEST,
            401: ErrorCode.AUTHENTICATION_FAILED,
            403: ErrorCode.INSUFFICIENT_PERMISSIONS,
            404: ErrorCode.RESOURCE_NOT_FOUND,
            409: ErrorCode.DUPLICATE_ENTRY,
            422: ErrorCode.VALIDATION_ERROR,
            429: ErrorCode.RATE_LIMIT_EXCEEDED,
            500: ErrorCode.UNKNOWN_ERROR,
            502: ErrorCode.EXTERNAL_API_ERROR,
            503: ErrorCode.SERVICE_UNAVAILABLE
        }
        
        error_code = error_code_map.get(exc.status_code, ErrorCode.UNKNOWN_ERROR)
        
        healthmate_exc = HealthMateException(
            message=str(exc.detail),
            error_code=error_code,
            status_code=exc.status_code
        )
        
        logger.warning(
            f"StarletteHTTPException: {exc.detail} (Status: {exc.status_code})",
            extra={
                "path": request.url.path,
                "method": request.method,
                "status_code": exc.status_code
            }
        )
        
        return JSONResponse(
            status_code=healthmate_exc.status_code,
            content=healthmate_exc.to_dict()
        )
    
    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        """Handle SQLAlchemy database errors."""
        # Determine specific error type
        if "UNIQUE constraint failed" in str(exc) or "duplicate key" in str(exc).lower():
            error_code = ErrorCode.DUPLICATE_ENTRY
            status_code = 409
            message = "Resource already exists"
        elif "FOREIGN KEY constraint failed" in str(exc):
            error_code = ErrorCode.CONSTRAINT_VIOLATION
            status_code = 400
            message = "Referenced resource does not exist"
        elif "NOT NULL constraint failed" in str(exc):
            error_code = ErrorCode.CONSTRAINT_VIOLATION
            status_code = 400
            message = "Required field is missing"
        else:
            error_code = ErrorCode.DATABASE_ERROR
            status_code = 500
            message = "Database operation failed"
        
        db_error = DatabaseError(
            message=message,
            error_code=error_code,
            query=getattr(exc, 'statement', None),
            details={"original_error": str(exc)}
        )
        
        logger.error(
            f"Database error: {message}",
            extra={
                "path": request.url.path,
                "method": request.method,
                "error_code": error_code.value,
                "original_error": str(exc)
            },
            exc_info=True
        )
        
        return JSONResponse(
            status_code=status_code,
            content=db_error.to_dict()
        )
    
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle all other unhandled exceptions."""
        # Convert to HealthMateException
        healthmate_exc = HealthMateException(
            message="An unexpected error occurred",
            error_code=ErrorCode.UNKNOWN_ERROR,
            status_code=500,
            context={
                "exception_type": exc.__class__.__name__,
                "original_message": str(exc),
                "path": request.url.path,
                "method": request.method
            }
        )
        
        logger.error(
            f"Unhandled exception: {exc.__class__.__name__}: {str(exc)}",
            extra={
                "path": request.url.path,
                "method": request.method,
                "exception_type": exc.__class__.__name__,
                "original_message": str(exc)
            },
            exc_info=True
        )
        
        return JSONResponse(
            status_code=healthmate_exc.status_code,
            content=healthmate_exc.to_dict()
        )


def create_error_response(
    message: str,
    error_code: Union[ErrorCode, int],
    status_code: int = 500,
    details: Dict[str, Any] = None
) -> JSONResponse:
    """
    Create a standardized error response.
    
    Args:
        message: Error message
        error_code: Application error code
        status_code: HTTP status code
        details: Additional error details
        
    Returns:
        JSONResponse with standardized error format
    """
    error = HealthMateException(
        message=message,
        error_code=error_code,
        status_code=status_code,
        details=details or {}
    )
    
    return JSONResponse(
        status_code=status_code,
        content=error.to_dict()
    )


def handle_validation_error(
    field: str,
    message: str,
    value: Any = None,
    error_type: str = "validation_error"
) -> ValidationError:
    """
    Create a standardized validation error.
    
    Args:
        field: Field that failed validation
        message: Validation error message
        value: Invalid value
        error_type: Type of validation error
        
    Returns:
        ValidationError instance
    """
    return ValidationError(
        message=message,
        field=field,
        value=value,
        details={"error_type": error_type}
    )


def handle_authentication_error(
    message: str = "Authentication failed",
    error_code: ErrorCode = ErrorCode.AUTHENTICATION_FAILED,
    details: Dict[str, Any] = None
) -> AuthenticationError:
    """
    Create a standardized authentication error.
    
    Args:
        message: Authentication error message
        error_code: Specific authentication error code
        details: Additional error details
        
    Returns:
        AuthenticationError instance
    """
    return AuthenticationError(
        message=message,
        error_code=error_code,
        details=details
    )


def handle_authorization_error(
    message: str = "Insufficient permissions",
    required_permissions: list = None,
    details: Dict[str, Any] = None
) -> AuthorizationError:
    """
    Create a standardized authorization error.
    
    Args:
        message: Authorization error message
        required_permissions: List of required permissions
        details: Additional error details
        
    Returns:
        AuthorizationError instance
    """
    return AuthorizationError(
        message=message,
        required_permissions=required_permissions,
        details=details
    )


def handle_database_error(
    message: str,
    error_code: ErrorCode = ErrorCode.DATABASE_ERROR,
    query: str = None,
    details: Dict[str, Any] = None
) -> DatabaseError:
    """
    Create a standardized database error.
    
    Args:
        message: Database error message
        error_code: Specific database error code
        query: SQL query that caused the error
        details: Additional error details
        
    Returns:
        DatabaseError instance
    """
    return DatabaseError(
        message=message,
        error_code=error_code,
        query=query,
        details=details
    )


def handle_resource_not_found_error(
    resource_type: str,
    resource_id: Union[str, int] = None,
    message: str = None
) -> ResourceNotFoundError:
    """
    Create a standardized resource not found error.
    
    Args:
        resource_type: Type of resource that was not found
        resource_id: ID of the resource that was not found
        message: Custom error message
        
    Returns:
        ResourceNotFoundError instance
    """
    return ResourceNotFoundError(
        resource_type=resource_type,
        resource_id=resource_id,
        message=message
    )


def handle_rate_limit_error(
    message: str = "Rate limit exceeded",
    retry_after: int = None,
    limit: int = None,
    window: int = None
) -> RateLimitError:
    """
    Create a standardized rate limit error.
    
    Args:
        message: Rate limit error message
        retry_after: Seconds to wait before retrying
        limit: Rate limit value
        window: Time window for the rate limit
        
    Returns:
        RateLimitError instance
    """
    return RateLimitError(
        message=message,
        retry_after=retry_after,
        limit=limit,
        window=window
    ) 
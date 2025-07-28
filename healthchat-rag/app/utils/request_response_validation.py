"""
Request/Response Validation Middleware

This module provides middleware for validating incoming requests and outgoing responses
to ensure data integrity and consistent API behavior.
"""

import json
import logging
from typing import Any, Dict, Optional, Union
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError, BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class RequestResponseValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for validating requests and responses.
    
    This middleware:
    1. Validates incoming request bodies against expected schemas
    2. Validates query parameters and path parameters
    3. Ensures consistent response format
    4. Logs validation errors for debugging
    """
    
    def __init__(
        self,
        app: ASGIApp,
        enable_request_validation: bool = True,
        enable_response_validation: bool = True,
        log_validation_errors: bool = True
    ):
        super().__init__(app)
        self.enable_request_validation = enable_request_validation
        self.enable_response_validation = enable_response_validation
        self.log_validation_errors = log_validation_errors
        
        # Schema mapping for different endpoints
        self.request_schemas: Dict[str, Dict[str, BaseModel]] = {}
        self.response_schemas: Dict[str, BaseModel] = {}
        
    def add_request_schema(
        self, 
        path: str, 
        method: str, 
        schema: BaseModel,
        param_type: str = "body"
    ):
        """Add a request schema for a specific endpoint and method."""
        key = f"{method.upper()}:{path}"
        if key not in self.request_schemas:
            self.request_schemas[key] = {}
        self.request_schemas[key][param_type] = schema
        
    def add_response_schema(self, path: str, method: str, schema: BaseModel):
        """Add a response schema for a specific endpoint and method."""
        key = f"{method.upper()}:{path}"
        self.response_schemas[key] = schema
        
    async def dispatch(self, request: Request, call_next):
        """Process the request and response through validation."""
        try:
            # Validate incoming request
            if self.enable_request_validation:
                await self._validate_request(request)
            
            # Process the request
            response = await call_next(request)
            
            # Validate outgoing response
            if self.enable_response_validation:
                response = await self._validate_response(request, response)
                
            return response
            
        except ValidationError as e:
            if self.log_validation_errors:
                logger.error(f"Validation error: {e}")
            return self._create_validation_error_response(e)
        except Exception as e:
            if self.log_validation_errors:
                logger.error(f"Unexpected error in validation middleware: {e}")
            raise
            
    async def _validate_request(self, request: Request):
        """Validate incoming request data."""
        path = request.url.path
        method = request.method
        
        # Check if we have schemas for this endpoint
        key = f"{method}:{path}"
        if key not in self.request_schemas:
            return  # No validation schemas defined for this endpoint
            
        schemas = self.request_schemas[key]
        
        # Validate request body
        if "body" in schemas and request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    body_data = json.loads(body)
                    schemas["body"](**body_data)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid JSON in request body"
                )
                
        # Validate query parameters
        if "query" in schemas:
            query_params = dict(request.query_params)
            if query_params:
                schemas["query"](**query_params)
                
        # Validate path parameters
        if "path" in schemas:
            path_params = dict(request.path_params)
            if path_params:
                schemas["path"](**path_params)
                
    async def _validate_response(self, request: Request, response: Response) -> Response:
        """Validate outgoing response data."""
        path = request.url.path
        method = request.method
        
        # Check if we have a response schema for this endpoint
        key = f"{method}:{path}"
        if key not in self.response_schemas:
            return response  # No validation schema defined
            
        schema = self.response_schemas[key]
        
        # Only validate JSON responses
        if response.headers.get("content-type", "").startswith("application/json"):
            try:
                # Get response body
                response_body = b""
                async for chunk in response.body_iterator:
                    response_body += chunk
                    
                # Parse and validate
                if response_body:
                    response_data = json.loads(response_body)
                    schema(**response_data)
                    
                # Reconstruct response
                return Response(
                    content=response_body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type
                )
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON in response for {path}")
                return response
                
        return response
        
    def _create_validation_error_response(self, validation_error: ValidationError) -> JSONResponse:
        """Create a standardized validation error response."""
        error_details = []
        for error in validation_error.errors():
            error_details.append({
                "field": " -> ".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            })
            
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "message": "Validation error",
                "errors": error_details
            }
        )


class ValidationConfig:
    """Configuration class for request/response validation."""
    
    def __init__(self):
        self.enable_request_validation = True
        self.enable_response_validation = True
        self.log_validation_errors = True
        self.strict_mode = False  # If True, requires schemas for all endpoints
        
    def get_middleware(self, app: ASGIApp) -> RequestResponseValidationMiddleware:
        """Create and configure the validation middleware."""
        return RequestResponseValidationMiddleware(
            app=app,
            enable_request_validation=self.enable_request_validation,
            enable_response_validation=self.enable_response_validation,
            log_validation_errors=self.log_validation_errors
        )


# Global validation configuration
validation_config = ValidationConfig()


def validate_request_body(schema: BaseModel):
    """Decorator to validate request body against a schema."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # This would be implemented in the actual endpoint
            # For now, it's a placeholder for the validation logic
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def validate_response(schema: BaseModel):
    """Decorator to validate response against a schema."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # This would be implemented in the actual endpoint
            # For now, it's a placeholder for the validation logic
            return await func(*args, **kwargs)
        return wrapper
    return decorator 
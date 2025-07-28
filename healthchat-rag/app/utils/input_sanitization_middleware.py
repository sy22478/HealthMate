"""
Input Sanitization Middleware
Automatically sanitizes and validates all incoming request data
"""
import json
import logging
from typing import Any, Dict, List, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from .sql_injection_utils import sql_injection_prevention
from .html_sanitization import html_sanitizer

logger = logging.getLogger(__name__)

class InputSanitizationMiddleware(BaseHTTPMiddleware):
    """Middleware for automatic input sanitization and validation"""
    
    def __init__(self, app, exclude_paths: List[str] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/docs",
            "/openapi.json",
            "/health",
            "/metrics"
        ]
    
    async def dispatch(self, request: Request, call_next):
        """Process request and sanitize input data"""
        
        # Skip sanitization for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        try:
            # Sanitize query parameters
            sanitized_query_params = self._sanitize_query_params(request.query_params)
            
            # Sanitize path parameters
            sanitized_path_params = self._sanitize_path_params(request.path_params)
            
            # Sanitize request body for POST/PUT/PATCH requests
            sanitized_body = None
            if request.method in ["POST", "PUT", "PATCH"]:
                sanitized_body = await self._sanitize_request_body(request)
            
            # Create sanitized request
            sanitized_request = self._create_sanitized_request(
                request, sanitized_query_params, sanitized_path_params, sanitized_body
            )
            
            # Process the sanitized request
            response = await call_next(sanitized_request)
            return response
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            logger.error(f"Error in input sanitization middleware: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Invalid input data"}
            )
    
    def _sanitize_query_params(self, query_params) -> Dict[str, str]:
        """Sanitize query parameters"""
        sanitized = {}
        
        for key, value in query_params.items():
            try:
                # Determine input type based on parameter name
                input_type = self._get_input_type_for_param(key)
                sanitized_value = sql_injection_prevention.sanitize_input(
                    value, input_type, max_length=500
                )
                
                # Apply HTML sanitization for text content
                if input_type in ['text', 'name']:
                    sanitized_value = html_sanitizer.sanitize_text(sanitized_value)
                
                sanitized[key] = sanitized_value
            except HTTPException:
                # Instead of skipping, sanitize with basic text sanitization
                logger.warning(f"Invalid query parameter: {key}={value}, applying basic sanitization")
                try:
                    # Apply basic HTML sanitization to remove dangerous content
                    sanitized_value = html_sanitizer.sanitize_text(str(value))
                    sanitized[key] = sanitized_value
                except Exception:
                    # If even basic sanitization fails, use empty string
                    sanitized[key] = ""
        
        return sanitized
    
    def _sanitize_path_params(self, path_params: Dict[str, Any]) -> Dict[str, str]:
        """Sanitize path parameters"""
        sanitized = {}
        
        for key, value in path_params.items():
            try:
                # Path parameters are typically IDs or slugs
                input_type = 'alphanumeric' if key.endswith('_id') else 'text'
                sanitized_value = sql_injection_prevention.sanitize_input(
                    value, input_type, max_length=100
                )
                
                # Apply HTML sanitization for text content
                if input_type == 'text':
                    sanitized_value = html_sanitizer.sanitize_text(sanitized_value)
                
                sanitized[key] = sanitized_value
            except HTTPException:
                # Instead of skipping, sanitize with basic text sanitization
                logger.warning(f"Invalid path parameter: {key}={value}, applying basic sanitization")
                try:
                    # Apply basic HTML sanitization to remove dangerous content
                    sanitized_value = html_sanitizer.sanitize_text(str(value))
                    sanitized[key] = sanitized_value
                except Exception:
                    # If even basic sanitization fails, use empty string
                    sanitized[key] = ""
        
        return sanitized
    
    async def _sanitize_request_body(self, request: Request) -> Optional[Dict[str, Any]]:
        """Sanitize request body"""
        try:
            # Get content type
            content_type = request.headers.get("content-type", "")
            
            if "application/json" in content_type:
                body = await request.json()
                return self._sanitize_json_body(body)
            elif "application/x-www-form-urlencoded" in content_type:
                form_data = await request.form()
                return self._sanitize_form_data(form_data)
            else:
                # For other content types, return None (no sanitization)
                return None
                
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON in request body"
            )
        except Exception as e:
            logger.error(f"Error sanitizing request body: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error processing request body"
            )
    
    def _sanitize_json_body(self, body: Any) -> Any:
        """Sanitize JSON request body"""
        if isinstance(body, dict):
            return self._sanitize_dict_recursive(body)
        elif isinstance(body, list):
            return [self._sanitize_json_body(item) for item in body]
        elif isinstance(body, str):
            # Apply both SQL injection and HTML sanitization
            sanitized = sql_injection_prevention.sanitize_input(body, 'text')
            return html_sanitizer.sanitize_text(sanitized)
        else:
            return body
    
    def _sanitize_dict_recursive(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively sanitize dictionary values"""
        sanitized = {}
        
        for key, value in data.items():
            try:
                if isinstance(value, dict):
                    sanitized[key] = self._sanitize_dict_recursive(value)
                elif isinstance(value, list):
                    sanitized[key] = [self._sanitize_json_body(item) for item in value]
                elif isinstance(value, str):
                    input_type = self._get_input_type_for_field(key)
                    
                    # Apply SQL injection prevention first
                    sanitized_value = sql_injection_prevention.sanitize_input(
                        value, input_type
                    )
                    
                    # Apply HTML sanitization for text content
                    if input_type in ['text', 'name']:
                        sanitized_value = html_sanitizer.sanitize_text(sanitized_value)
                    elif key.lower() in ['content', 'message', 'description', 'notes', 'comment']:
                        # For content fields, apply HTML sanitization
                        sanitized_value = html_sanitizer.sanitize_html(sanitized_value)
                    
                    sanitized[key] = sanitized_value
                else:
                    sanitized[key] = value
            except HTTPException:
                # Instead of skipping, sanitize with basic text sanitization
                logger.warning(f"Invalid field in request body: {key}={value}, applying basic sanitization")
                try:
                    if isinstance(value, str):
                        # Apply basic HTML sanitization to remove dangerous content
                        sanitized_value = html_sanitizer.sanitize_text(value)
                        sanitized[key] = sanitized_value
                    else:
                        # For non-string values, keep as is
                        sanitized[key] = value
                except Exception:
                    # If even basic sanitization fails, use empty string for strings, original for others
                    sanitized[key] = "" if isinstance(value, str) else value
        
        return sanitized
    
    def _sanitize_form_data(self, form_data) -> Dict[str, str]:
        """Sanitize form data"""
        sanitized = {}
        
        for key, value in form_data.items():
            try:
                input_type = self._get_input_type_for_field(key)
                
                # Apply SQL injection prevention first
                sanitized_value = sql_injection_prevention.sanitize_input(
                    str(value), input_type
                )
                
                # Apply HTML sanitization for text content
                if input_type in ['text', 'name']:
                    sanitized_value = html_sanitizer.sanitize_text(sanitized_value)
                elif key.lower() in ['content', 'message', 'description', 'notes', 'comment']:
                    # For content fields, apply HTML sanitization
                    sanitized_value = html_sanitizer.sanitize_html(sanitized_value)
                
                sanitized[key] = sanitized_value
            except HTTPException:
                # Instead of skipping, sanitize with basic text sanitization
                logger.warning(f"Invalid form field: {key}={value}, applying basic sanitization")
                try:
                    # Apply basic HTML sanitization to remove dangerous content
                    sanitized_value = html_sanitizer.sanitize_text(str(value))
                    sanitized[key] = sanitized_value
                except Exception:
                    # If even basic sanitization fails, use empty string
                    sanitized[key] = ""
        
        return sanitized
    
    def _get_input_type_for_param(self, param_name: str) -> str:
        """Determine input type for query parameter"""
        param_lower = param_name.lower()
        
        if any(keyword in param_lower for keyword in ['email', 'mail']):
            return 'email'
        elif any(keyword in param_lower for keyword in ['name', 'title']):
            return 'name'
        elif any(keyword in param_lower for keyword in ['phone', 'tel']):
            return 'phone'
        elif any(keyword in param_lower for keyword in ['id', 'num', 'count']):
            return 'numeric'
        else:
            return 'text'
    
    def _get_input_type_for_field(self, field_name: str) -> str:
        """Determine input type for request body field"""
        field_lower = field_name.lower()
        
        if any(keyword in field_lower for keyword in ['email', 'mail']):
            return 'email'
        elif any(keyword in field_lower for keyword in ['name', 'title', 'full_name']):
            return 'name'
        elif any(keyword in field_lower for keyword in ['phone', 'tel', 'mobile']):
            return 'phone'
        elif any(keyword in field_lower for keyword in ['password', 'pass']):
            return 'text'  # Don't over-sanitize passwords
        elif any(keyword in field_lower for keyword in ['id', 'num', 'count', 'age']):
            return 'numeric'
        else:
            return 'text'
    
    def _create_sanitized_request(self, original_request: Request, 
                                query_params: Dict[str, str],
                                path_params: Dict[str, str],
                                body: Optional[Dict[str, Any]]) -> Request:
        """Create a new request with sanitized data"""
        # This is a simplified approach - in a real implementation,
        # you'd need to create a custom request class or use a different approach
        # For now, we'll modify the request object directly
        
        # Store sanitized data in request state for access in route handlers
        original_request.state.sanitized_query_params = query_params
        original_request.state.sanitized_path_params = path_params
        original_request.state.sanitized_body = body
        
        return original_request 
"""
API Audit Middleware for HealthMate

This middleware automatically logs all API calls for audit and monitoring purposes.
It captures request/response information and logs it using the AuditLogger.
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from app.utils.audit_logging import AuditLogger
from app.utils.auth_middleware import get_current_user_optional

logger = logging.getLogger(__name__)

class APIAuditMiddleware(BaseHTTPMiddleware):
    """Middleware to audit all API calls."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Get request information
        method = request.method
        path = request.url.path
        query_params = str(request.query_params) if request.query_params else ""
        
        # Get user information if available
        user_id = None
        user_email = None
        try:
            user = await get_current_user_optional(request)
            if user:
                user_id = user.id
                user_email = user.email
        except Exception:
            # User not authenticated or token invalid
            pass
        
        # Get request size
        request_size = 0
        if request.body:
            body = await request.body()
            request_size = len(body)
        
        # Process the request
        try:
            response = await call_next(request)
            response_time = time.time() - start_time
            
            # Get response size
            response_size = 0
            if hasattr(response, 'body'):
                response_size = len(response.body)
            
            # Determine success based on status code
            success = 200 <= response.status_code < 400
            
            # Log the API call
            AuditLogger.log_api_call(
                method=method,
                path=path,
                user_id=user_id,
                user_email=user_email,
                status_code=response.status_code,
                response_time=response_time,
                request_size=request_size,
                response_size=response_size,
                success=success,
                details={
                    "query_params": query_params,
                    "user_agent": request.headers.get("user-agent", "unknown")
                },
                request=request
            )
            
            return response
            
        except Exception as e:
            response_time = time.time() - start_time
            
            # Log failed API call
            AuditLogger.log_api_call(
                method=method,
                path=path,
                user_id=user_id,
                user_email=user_email,
                response_time=response_time,
                request_size=request_size,
                success=False,
                details={
                    "error": str(e),
                    "query_params": query_params,
                    "user_agent": request.headers.get("user-agent", "unknown")
                },
                request=request
            )
            
            # Re-raise the exception
            raise 
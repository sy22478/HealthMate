"""
Audit Logging Utility for HealthMate

This module provides structured audit logging for security and compliance purposes.
It logs authentication events, health data access, and API calls with detailed context.
"""

import logging
from typing import Optional, Dict, Any, Union
from datetime import datetime, timezone
from fastapi import Request
from app.utils.correlation_id_middleware import get_correlation_id

logger = logging.getLogger(__name__)

class AuditLogger:
    """Audit logger for security and compliance events."""
    
    @staticmethod
    def log_auth_event(
        event_type: str,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        success: bool = True,
        details: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ):
        """
        Log authentication events with detailed context.
        
        Args:
            event_type: Type of authentication event (login, logout, register, etc.)
            user_id: User ID (if available)
            user_email: User email (if available)
            ip_address: Client IP address
            success: Whether the action was successful
            details: Additional event details
            request: FastAPI request object (for extracting additional context)
        """
        if request:
            ip_address = ip_address or request.client.host if request.client else "unknown"
            user_agent = request.headers.get("user-agent", "unknown")
        else:
            user_agent = "unknown"
        
        log_data = {
            "event_type": "authentication",
            "auth_action": event_type,
            "user_id": user_id,
            "user_email": user_email,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "success": success,
            "correlation_id": get_correlation_id(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": details or {}
        }
        
        if success:
            logger.info(f"Authentication event: {event_type}", extra=log_data)
        else:
            logger.warning(f"Authentication event failed: {event_type}", extra=log_data)
    
    @staticmethod
    def log_health_data_access(
        action: str,
        user_id: int,
        user_email: str,
        data_type: str,
        data_id: Optional[Union[int, str]] = None,
        ip_address: Optional[str] = None,
        success: bool = True,
        details: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ):
        """
        Log health data access and modifications.
        
        Args:
            action: Type of action (read, create, update, delete)
            user_id: User ID
            user_email: User email
            data_type: Type of health data (blood_pressure, weight, etc.)
            data_id: ID of the specific data record
            ip_address: Client IP address
            success: Whether the action was successful
            details: Additional event details
            request: FastAPI request object
        """
        if request:
            ip_address = ip_address or request.client.host if request.client else "unknown"
            user_agent = request.headers.get("user-agent", "unknown")
        else:
            user_agent = "unknown"
        
        log_data = {
            "event_type": "health_data_access",
            "action": action,
            "user_id": user_id,
            "user_email": user_email,
            "data_type": data_type,
            "data_id": data_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "success": success,
            "correlation_id": get_correlation_id(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": details or {}
        }
        
        if success:
            logger.info(f"Health data {action}: {data_type}", extra=log_data)
        else:
            logger.warning(f"Health data {action} failed: {data_type}", extra=log_data)
    
    @staticmethod
    def log_api_call(
        method: str,
        path: str,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        status_code: Optional[int] = None,
        response_time: Optional[float] = None,
        request_size: Optional[int] = None,
        response_size: Optional[int] = None,
        success: bool = True,
        details: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ):
        """
        Log API calls with sanitized request/response information.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: API endpoint path
            user_id: User ID (if authenticated)
            user_email: User email (if authenticated)
            ip_address: Client IP address
            status_code: HTTP status code
            response_time: Response time in seconds
            request_size: Size of request in bytes
            response_size: Size of response in bytes
            success: Whether the request was successful
            details: Additional event details
            request: FastAPI request object
        """
        if request:
            ip_address = ip_address or request.client.host if request.client else "unknown"
            user_agent = request.headers.get("user-agent", "unknown")
        else:
            user_agent = "unknown"
        
        log_data = {
            "event_type": "api_call",
            "method": method,
            "path": path,
            "user_id": user_id,
            "user_email": user_email,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "status_code": status_code,
            "response_time": response_time,
            "request_size": request_size,
            "response_size": response_size,
            "success": success,
            "correlation_id": get_correlation_id(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": details or {}
        }
        
        if success:
            logger.info(f"API call: {method} {path}", extra=log_data)
        else:
            logger.warning(f"API call failed: {method} {path}", extra=log_data) 
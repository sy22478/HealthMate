"""
Notification Exceptions for HealthMate Application

This module provides notification-related exception classes for handling
email, SMS, and push notification errors.
"""

import logging
from typing import Any, Dict, Optional

from .base_exceptions import HealthMateException, ErrorCode


class NotificationError(HealthMateException):
    """Exception raised for notification errors."""
    
    def __init__(
        self,
        message: str,
        notification_type: Optional[str] = None,
        user_id: Optional[int] = None,
        error_code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=500,
            details=details or {
                "notification_type": notification_type,
                "user_id": user_id
            },
            log_level=logging.ERROR
        )
        self.notification_type = notification_type
        self.user_id = user_id


class EmailError(NotificationError):
    """Exception raised for email notification errors."""
    
    def __init__(
        self,
        message: str,
        recipient: Optional[str] = None,
        subject: Optional[str] = None,
        user_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            notification_type="email",
            user_id=user_id,
            details=details or {
                "recipient": recipient,
                "subject": subject
            }
        )
        self.recipient = recipient
        self.subject = subject


class SMSError(NotificationError):
    """Exception raised for SMS notification errors."""
    
    def __init__(
        self,
        message: str,
        phone_number: Optional[str] = None,
        user_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            notification_type="sms",
            user_id=user_id,
            details=details or {"phone_number": phone_number}
        )
        self.phone_number = phone_number 
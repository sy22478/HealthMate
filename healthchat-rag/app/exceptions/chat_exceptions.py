"""
Chat and AI Exceptions for HealthMate Application

This module provides chat and AI-related exception classes for handling
conversation errors, AI service errors, and response generation issues.
"""

import logging
from typing import Any, Dict, Optional

from .base_exceptions import HealthMateException, ErrorCode


class ChatError(HealthMateException):
    """Exception raised for chat/AI related errors."""
    
    def __init__(
        self,
        message: str,
        chat_session_id: Optional[str] = None,
        error_code: ErrorCode = ErrorCode.CHAT_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=500,
            details=details or {"chat_session_id": chat_session_id},
            log_level=logging.ERROR
        )
        self.chat_session_id = chat_session_id


class ConversationError(ChatError):
    """Exception raised for conversation-specific errors."""
    
    def __init__(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        user_id: Optional[int] = None,
        error_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            chat_session_id=conversation_id,
            error_code=ErrorCode.RESPONSE_GENERATION_ERROR,
            details=details or {
                "user_id": user_id,
                "error_type": error_type
            }
        )
        self.conversation_id = conversation_id
        self.user_id = user_id
        self.error_type = error_type 
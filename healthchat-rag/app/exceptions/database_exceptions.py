"""
Database Exceptions for HealthMate Application

This module provides database-related exception classes for handling
database connection, query, and transaction errors.
"""

import logging
from typing import Any, Dict, Optional

from .base_exceptions import HealthMateException, ErrorCode


class DatabaseError(HealthMateException):
    """Exception raised for database errors."""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.DATABASE_ERROR,
        query: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=500,
            details=details or {"query": query},
            log_level=logging.ERROR
        )
        self.query = query


class ConnectionError(DatabaseError):
    """Exception raised for database connection errors."""
    
    def __init__(
        self,
        message: str,
        database_url: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.CONNECTION_ERROR,
            details=details or {"database_url": database_url}
        )
        self.database_url = database_url


class QueryError(DatabaseError):
    """Exception raised for database query errors."""
    
    def __init__(
        self,
        message: str,
        query: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.QUERY_ERROR,
            query=query,
            details=details or {"parameters": parameters}
        )
        self.parameters = parameters 
"""
Unit tests for Custom Exception System
"""

import pytest
import logging
from datetime import datetime
from unittest.mock import patch, MagicMock

from app.utils.exceptions import (
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
    ErrorCode,
    handle_exception,
    async_handle_exception
)


class TestErrorCode:
    """Test the ErrorCode enum."""
    
    def test_error_code_values(self):
        """Test that error codes have expected values."""
        assert ErrorCode.UNKNOWN_ERROR.value == 1000
        assert ErrorCode.AUTHENTICATION_FAILED.value == 2000
        assert ErrorCode.VALIDATION_ERROR.value == 3000
        assert ErrorCode.DATABASE_ERROR.value == 4000
        assert ErrorCode.EXTERNAL_API_ERROR.value == 5000
        assert ErrorCode.HEALTH_DATA_ERROR.value == 6000
        assert ErrorCode.CHAT_ERROR.value == 7000
    
    def test_error_code_categories(self):
        """Test that error codes are properly categorized."""
        # General errors (1000-1999)
        assert 1000 <= ErrorCode.UNKNOWN_ERROR.value <= 1999
        assert 1000 <= ErrorCode.INVALID_REQUEST.value <= 1999
        
        # Authentication errors (2000-2999)
        assert 2000 <= ErrorCode.AUTHENTICATION_FAILED.value <= 2999
        assert 2000 <= ErrorCode.INVALID_TOKEN.value <= 2999
        
        # Validation errors (3000-3999)
        assert 3000 <= ErrorCode.VALIDATION_ERROR.value <= 3999
        assert 3000 <= ErrorCode.INVALID_INPUT.value <= 3999
        
        # Database errors (4000-4999)
        assert 4000 <= ErrorCode.DATABASE_ERROR.value <= 4999
        assert 4000 <= ErrorCode.CONNECTION_ERROR.value <= 4999
        
        # External API errors (5000-5999)
        assert 5000 <= ErrorCode.EXTERNAL_API_ERROR.value <= 5999
        assert 5000 <= ErrorCode.API_TIMEOUT.value <= 5999
        
        # Health data errors (6000-6999)
        assert 6000 <= ErrorCode.HEALTH_DATA_ERROR.value <= 6999
        assert 6000 <= ErrorCode.ENCRYPTION_ERROR.value <= 6999
        
        # Chat/AI errors (7000-7999)
        assert 7000 <= ErrorCode.CHAT_ERROR.value <= 7999
        assert 7000 <= ErrorCode.AI_SERVICE_ERROR.value <= 7999


class TestHealthMateException:
    """Test the base HealthMateException class."""
    
    def test_basic_exception_creation(self):
        """Test basic exception creation with default values."""
        exc = HealthMateException("Test error message")
        
        assert exc.message == "Test error message"
        assert exc.error_code == ErrorCode.UNKNOWN_ERROR
        assert exc.status_code == 500
        assert exc.details == {}
        assert exc.context == {}
        assert exc.log_level == logging.ERROR
        assert isinstance(exc.timestamp, datetime)
    
    def test_exception_with_custom_values(self):
        """Test exception creation with custom values."""
        details = {"field": "email", "value": "invalid"}
        context = {"user_id": 123, "action": "login"}
        
        exc = HealthMateException(
            message="Custom error",
            error_code=ErrorCode.VALIDATION_ERROR,
            status_code=422,
            details=details,
            context=context,
            log_level=logging.WARNING
        )
        
        assert exc.message == "Custom error"
        assert exc.error_code == ErrorCode.VALIDATION_ERROR
        assert exc.status_code == 422
        assert exc.details == details
        assert exc.context == context
        assert exc.log_level == logging.WARNING
    
    def test_exception_with_int_error_code(self):
        """Test exception creation with integer error code."""
        exc = HealthMateException(
            message="Test error",
            error_code=3001  # INVALID_INPUT
        )
        
        assert exc.error_code == ErrorCode.INVALID_INPUT
    
    @patch('app.utils.exceptions.logger')
    def test_exception_logging(self, mock_logger):
        """Test that exceptions are properly logged."""
        exc = HealthMateException("Test error", log_level=logging.WARNING)
        
        mock_logger.log.assert_called_once_with(
            logging.WARNING,
            "HealthMateException: Test error (Code: 1000)",
            exc_info=True
        )
    
    def test_to_dict_method(self):
        """Test the to_dict method for API responses."""
        exc = HealthMateException(
            message="Test error",
            error_code=ErrorCode.VALIDATION_ERROR,
            status_code=422,
            details={"field": "email"}
        )
        
        result = exc.to_dict()
        
        assert "error" in result
        error = result["error"]
        assert error["code"] == 3000
        assert error["message"] == "Test error"
        assert error["status_code"] == 422
        assert error["details"] == {"field": "email"}
        assert error["type"] == "HealthMateException"
        assert "timestamp" in error
    
    def test_string_representation(self):
        """Test string representation of exception."""
        exc = HealthMateException("Test error", error_code=ErrorCode.VALIDATION_ERROR)
        
        assert str(exc) == "HealthMateException: Test error (Code: 3000)"
    
    def test_repr_representation(self):
        """Test detailed string representation for debugging."""
        exc = HealthMateException(
            message="Test error",
            error_code=ErrorCode.VALIDATION_ERROR,
            status_code=422,
            details={"field": "email"},
            context={"user_id": 123}
        )
        
        repr_str = repr(exc)
        assert "HealthMateException(" in repr_str
        assert "message='Test error'" in repr_str
        assert "error_code=ErrorCode.VALIDATION_ERROR" in repr_str
        assert "status_code=422" in repr_str


class TestValidationError:
    """Test the ValidationError class."""
    
    def test_validation_error_creation(self):
        """Test validation error creation."""
        exc = ValidationError(
            message="Invalid email format",
            field="email",
            value="invalid-email"
        )
        
        assert exc.message == "Invalid email format"
        assert exc.error_code == ErrorCode.VALIDATION_ERROR
        assert exc.status_code == 422
        assert exc.field == "email"
        assert exc.value == "invalid-email"
        assert exc.log_level == logging.WARNING
        assert exc.details["field"] == "email"
        assert exc.details["value"] == "invalid-email"
    
    def test_validation_error_with_custom_details(self):
        """Test validation error with custom details."""
        custom_details = {"constraint": "email_format", "pattern": r"^[^@]+@[^@]+\.[^@]+$"}
        
        exc = ValidationError(
            message="Invalid email",
            field="email",
            value="invalid",
            details=custom_details
        )
        
        assert exc.details == custom_details


class TestAuthenticationError:
    """Test the AuthenticationError class."""
    
    def test_authentication_error_creation(self):
        """Test authentication error creation."""
        exc = AuthenticationError("Invalid credentials")
        
        assert exc.message == "Invalid credentials"
        assert exc.error_code == ErrorCode.AUTHENTICATION_FAILED
        assert exc.status_code == 401
        assert exc.log_level == logging.WARNING
    
    def test_authentication_error_with_custom_code(self):
        """Test authentication error with custom error code."""
        exc = AuthenticationError(
            message="Token expired",
            error_code=ErrorCode.TOKEN_EXPIRED
        )
        
        assert exc.error_code == ErrorCode.TOKEN_EXPIRED


class TestAuthorizationError:
    """Test the AuthorizationError class."""
    
    def test_authorization_error_creation(self):
        """Test authorization error creation."""
        required_permissions = ["read:health_data", "write:health_data"]
        
        exc = AuthorizationError(
            message="Insufficient permissions",
            required_permissions=required_permissions
        )
        
        assert exc.message == "Insufficient permissions"
        assert exc.error_code == ErrorCode.INSUFFICIENT_PERMISSIONS
        assert exc.status_code == 403
        assert exc.required_permissions == required_permissions
        assert exc.details["required_permissions"] == required_permissions


class TestDatabaseError:
    """Test the DatabaseError class."""
    
    def test_database_error_creation(self):
        """Test database error creation."""
        query = "SELECT * FROM users WHERE id = ?"
        
        exc = DatabaseError(
            message="Database connection failed",
            error_code=ErrorCode.CONNECTION_ERROR,
            query=query
        )
        
        assert exc.message == "Database connection failed"
        assert exc.error_code == ErrorCode.CONNECTION_ERROR
        assert exc.status_code == 500
        assert exc.query == query
        assert exc.details["query"] == query


class TestExternalAPIError:
    """Test the ExternalAPIError class."""
    
    def test_external_api_error_creation(self):
        """Test external API error creation."""
        exc = ExternalAPIError(
            message="API timeout",
            api_name="OpenAI",
            error_code=ErrorCode.API_TIMEOUT,
            response_status=408,
            response_body="Request timeout"
        )
        
        assert exc.message == "API timeout"
        assert exc.error_code == ErrorCode.API_TIMEOUT
        assert exc.status_code == 502
        assert exc.api_name == "OpenAI"
        assert exc.response_status == 408
        assert exc.response_body == "Request timeout"
        assert exc.details["api_name"] == "OpenAI"
        assert exc.details["response_status"] == 408
        assert exc.details["response_body"] == "Request timeout"


class TestHealthDataError:
    """Test the HealthDataError class."""
    
    def test_health_data_error_creation(self):
        """Test health data error creation."""
        exc = HealthDataError(
            message="Encryption failed",
            data_type="blood_pressure",
            user_id=123,
            error_code=ErrorCode.ENCRYPTION_ERROR
        )
        
        assert exc.message == "Encryption failed"
        assert exc.error_code == ErrorCode.ENCRYPTION_ERROR
        assert exc.status_code == 500
        assert exc.data_type == "blood_pressure"
        assert exc.user_id == 123
        assert exc.details["data_type"] == "blood_pressure"
        assert exc.details["user_id"] == 123


class TestChatError:
    """Test the ChatError class."""
    
    def test_chat_error_creation(self):
        """Test chat error creation."""
        exc = ChatError(
            message="AI service unavailable",
            chat_session_id="session_123",
            error_code=ErrorCode.AI_SERVICE_ERROR
        )
        
        assert exc.message == "AI service unavailable"
        assert exc.error_code == ErrorCode.AI_SERVICE_ERROR
        assert exc.status_code == 500
        assert exc.chat_session_id == "session_123"
        assert exc.details["chat_session_id"] == "session_123"


class TestResourceNotFoundError:
    """Test the ResourceNotFoundError class."""
    
    def test_resource_not_found_error_creation(self):
        """Test resource not found error creation."""
        exc = ResourceNotFoundError("User", 123)
        
        assert exc.message == "User with id '123' not found"
        assert exc.error_code == ErrorCode.RESOURCE_NOT_FOUND
        assert exc.status_code == 404
        assert exc.resource_type == "User"
        assert exc.resource_id == 123
        assert exc.log_level == logging.INFO
    
    def test_resource_not_found_error_without_id(self):
        """Test resource not found error without resource ID."""
        exc = ResourceNotFoundError("HealthData")
        
        assert exc.message == "HealthData not found"
        assert exc.resource_type == "HealthData"
        assert exc.resource_id is None
    
    def test_resource_not_found_error_with_custom_message(self):
        """Test resource not found error with custom message."""
        exc = ResourceNotFoundError(
            "User",
            123,
            message="User account has been deleted"
        )
        
        assert exc.message == "User account has been deleted"


class TestRateLimitError:
    """Test the RateLimitError class."""
    
    def test_rate_limit_error_creation(self):
        """Test rate limit error creation."""
        exc = RateLimitError(
            message="Rate limit exceeded",
            retry_after=60,
            limit=100,
            window=3600
        )
        
        assert exc.message == "Rate limit exceeded"
        assert exc.error_code == ErrorCode.RATE_LIMIT_EXCEEDED
        assert exc.status_code == 429
        assert exc.retry_after == 60
        assert exc.limit == 100
        assert exc.window == 3600
        assert exc.details["retry_after"] == 60
        assert exc.details["limit"] == 100
        assert exc.details["window"] == 3600


class TestExceptionDecorators:
    """Test the exception handling decorators."""
    
    def test_handle_exception_decorator_success(self):
        """Test handle_exception decorator with successful function."""
        @handle_exception
        def test_function():
            return "success"
        
        result = test_function()
        assert result == "success"
    
    def test_handle_exception_decorator_with_healthmate_exception(self):
        """Test handle_exception decorator with HealthMateException."""
        @handle_exception
        def test_function():
            raise ValidationError("Test validation error")
        
        with pytest.raises(ValidationError) as exc_info:
            test_function()
        
        assert str(exc_info.value) == "ValidationError: Test validation error (Code: 3000)"
    
    @patch('app.utils.exceptions.logger')
    def test_handle_exception_decorator_with_generic_exception(self, mock_logger):
        """Test handle_exception decorator with generic exception."""
        @handle_exception
        def test_function():
            raise ValueError("Test value error")
        
        with pytest.raises(HealthMateException) as exc_info:
            test_function()
        
        assert exc_info.value.error_code == ErrorCode.UNKNOWN_ERROR
        assert "An unexpected error occurred" in exc_info.value.message
        assert exc_info.value.context["function"] == "test_function"
        assert exc_info.value.context["original_exception"] == "Test value error"
        
        mock_logger.error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_async_handle_exception_decorator_success(self):
        """Test async_handle_exception decorator with successful function."""
        @async_handle_exception
        async def test_function():
            return "success"
        
        result = await test_function()
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_async_handle_exception_decorator_with_healthmate_exception(self):
        """Test async_handle_exception decorator with HealthMateException."""
        @async_handle_exception
        async def test_function():
            raise ValidationError("Test validation error")
        
        with pytest.raises(ValidationError) as exc_info:
            await test_function()
        
        assert str(exc_info.value) == "ValidationError: Test validation error (Code: 3000)"
    
    @pytest.mark.asyncio
    @patch('app.utils.exceptions.logger')
    async def test_async_handle_exception_decorator_with_generic_exception(self, mock_logger):
        """Test async_handle_exception decorator with generic exception."""
        @async_handle_exception
        async def test_function():
            raise ValueError("Test value error")
        
        with pytest.raises(HealthMateException) as exc_info:
            await test_function()
        
        assert exc_info.value.error_code == ErrorCode.UNKNOWN_ERROR
        assert "An unexpected error occurred" in exc_info.value.message
        assert exc_info.value.context["function"] == "test_function"
        assert exc_info.value.context["original_exception"] == "Test value error"
        
        mock_logger.error.assert_called_once()


class TestExceptionIntegration:
    """Integration tests for the exception system."""
    
    def test_exception_hierarchy(self):
        """Test that all exceptions inherit from HealthMateException."""
        exceptions = [
            ValidationError("test"),
            AuthenticationError("test"),
            AuthorizationError("test"),
            DatabaseError("test"),
            ExternalAPIError("test", "test_api"),
            HealthDataError("test"),
            ChatError("test"),
            ResourceNotFoundError("test"),
            RateLimitError("test")
        ]
        
        for exc in exceptions:
            assert isinstance(exc, HealthMateException)
            assert isinstance(exc, Exception)
    
    def test_exception_serialization(self):
        """Test that all exceptions can be serialized to dict."""
        exceptions = [
            ValidationError("test", field="test_field"),
            AuthenticationError("test"),
            AuthorizationError("test", required_permissions=["test"]),
            DatabaseError("test", query="SELECT * FROM test"),
            ExternalAPIError("test", "test_api", response_status=500),
            HealthDataError("test", data_type="test", user_id=123),
            ChatError("test", chat_session_id="test_session"),
            ResourceNotFoundError("test", 123),
            RateLimitError("test", retry_after=60)
        ]
        
        for exc in exceptions:
            result = exc.to_dict()
            assert "error" in result
            assert "code" in result["error"]
            assert "message" in result["error"]
            assert "status_code" in result["error"]
            assert "timestamp" in result["error"]
            assert "type" in result["error"]
    
    def test_error_code_consistency(self):
        """Test that error codes are consistent across exception types."""
        assert ValidationError("test").error_code == ErrorCode.VALIDATION_ERROR
        assert AuthenticationError("test").error_code == ErrorCode.AUTHENTICATION_FAILED
        assert AuthorizationError("test").error_code == ErrorCode.INSUFFICIENT_PERMISSIONS
        assert DatabaseError("test").error_code == ErrorCode.DATABASE_ERROR
        assert ExternalAPIError("test", "test_api").error_code == ErrorCode.EXTERNAL_API_ERROR
        assert HealthDataError("test").error_code == ErrorCode.HEALTH_DATA_ERROR
        assert ChatError("test").error_code == ErrorCode.CHAT_ERROR
        assert ResourceNotFoundError("test").error_code == ErrorCode.RESOURCE_NOT_FOUND
        assert RateLimitError("test").error_code == ErrorCode.RATE_LIMIT_EXCEEDED 
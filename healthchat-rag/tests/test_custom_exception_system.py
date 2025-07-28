"""
Comprehensive Tests for Custom Exception System

This module tests the complete custom exception system including all exception classes,
error codes, and exception handlers.
"""

import pytest
import logging
from datetime import datetime
from unittest.mock import patch, MagicMock

from app.exceptions import (
    HealthMateException,
    ValidationError,
    SchemaValidationError,
    InputValidationError,
    AuthenticationError,
    AuthorizationError,
    TokenError,
    DatabaseError,
    ConnectionError,
    QueryError,
    ExternalAPIError,
    APIError,
    RateLimitError,
    HealthDataError,
    MedicalDataError,
    ChatError,
    ConversationError,
    NotificationError,
    EmailError,
    SMSError,
    ResourceNotFoundError,
    ErrorCode
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
    
    @patch('app.exceptions.base_exceptions.logger')
    def test_exception_logging(self, mock_logger):
        """Test that exceptions are properly logged."""
        exc = HealthMateException("Test error")
        
        # Verify that the logger was called
        mock_logger.log.assert_called_once()
        call_args = mock_logger.log.call_args
        assert call_args[0][0] == logging.ERROR  # log level
        assert "Test error" in call_args[0][1]  # message
    
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
        assert error["code"] == ErrorCode.VALIDATION_ERROR.value
        assert error["message"] == "Test error"
        assert error["status_code"] == 422
        assert error["details"] == {"field": "email"}
        assert error["type"] == "HealthMateException"
        assert "timestamp" in error
    
    def test_string_representation(self):
        """Test string representation of exception."""
        exc = HealthMateException("Test error", ErrorCode.VALIDATION_ERROR)
        assert str(exc) == "HealthMateException: Test error (Code: 3000)"
    
    def test_repr_representation(self):
        """Test detailed string representation for debugging."""
        exc = HealthMateException("Test error", ErrorCode.VALIDATION_ERROR)
        repr_str = repr(exc)
        assert "HealthMateException(" in repr_str
        assert "message='Test error'" in repr_str
        assert "error_code=ErrorCode.VALIDATION_ERROR" in repr_str


class TestValidationExceptions:
    """Test validation-related exception classes."""
    
    def test_validation_error_creation(self):
        """Test ValidationError creation."""
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
        assert exc.details["field"] == "email"
        assert exc.details["value"] == "invalid-email"
        assert exc.log_level == logging.WARNING
    
    def test_schema_validation_error_creation(self):
        """Test SchemaValidationError creation."""
        exc = SchemaValidationError(
            message="Schema validation failed",
            schema_name="UserSchema",
            field="email",
            value="invalid"
        )
        
        assert exc.message == "Schema validation failed"
        assert exc.schema_name == "UserSchema"
        assert exc.field == "email"
        assert exc.value == "invalid"
        assert exc.details["schema_name"] == "UserSchema"
    
    def test_input_validation_error_creation(self):
        """Test InputValidationError creation."""
        exc = InputValidationError(
            message="Invalid input format",
            field="phone",
            value="123",
            validation_type="phone_format"
        )
        
        assert exc.message == "Invalid input format"
        assert exc.field == "phone"
        assert exc.value == "123"
        assert exc.validation_type == "phone_format"
        assert exc.details["validation_type"] == "phone_format"


class TestAuthenticationExceptions:
    """Test authentication-related exception classes."""
    
    def test_authentication_error_creation(self):
        """Test AuthenticationError creation."""
        exc = AuthenticationError("Invalid credentials")
        
        assert exc.message == "Invalid credentials"
        assert exc.error_code == ErrorCode.AUTHENTICATION_FAILED
        assert exc.status_code == 401
        assert exc.log_level == logging.WARNING
    
    def test_authentication_error_with_custom_code(self):
        """Test AuthenticationError with custom error code."""
        exc = AuthenticationError(
            "Token expired",
            error_code=ErrorCode.TOKEN_EXPIRED
        )
        
        assert exc.error_code == ErrorCode.TOKEN_EXPIRED
    
    def test_authorization_error_creation(self):
        """Test AuthorizationError creation."""
        required_permissions = ["read:health_data", "write:health_data"]
        exc = AuthorizationError(
            "Insufficient permissions",
            required_permissions=required_permissions
        )
        
        assert exc.message == "Insufficient permissions"
        assert exc.error_code == ErrorCode.INSUFFICIENT_PERMISSIONS
        assert exc.status_code == 403
        assert exc.required_permissions == required_permissions
        assert exc.details["required_permissions"] == required_permissions
    
    def test_token_error_creation(self):
        """Test TokenError creation."""
        exc = TokenError(
            "Invalid access token",
            token_type="access",
            error_code=ErrorCode.INVALID_TOKEN
        )
        
        assert exc.message == "Invalid access token"
        assert exc.token_type == "access"
        assert exc.error_code == ErrorCode.INVALID_TOKEN
        assert exc.details["token_type"] == "access"


class TestDatabaseExceptions:
    """Test database-related exception classes."""
    
    def test_database_error_creation(self):
        """Test DatabaseError creation."""
        exc = DatabaseError(
            "Database connection failed",
            query="SELECT * FROM users"
        )
        
        assert exc.message == "Database connection failed"
        assert exc.error_code == ErrorCode.DATABASE_ERROR
        assert exc.status_code == 500
        assert exc.query == "SELECT * FROM users"
        assert exc.details["query"] == "SELECT * FROM users"
        assert exc.log_level == logging.ERROR
    
    def test_connection_error_creation(self):
        """Test ConnectionError creation."""
        exc = ConnectionError(
            "Failed to connect to database",
            database_url="postgresql://localhost:5432/healthmate"
        )
        
        assert exc.message == "Failed to connect to database"
        assert exc.error_code == ErrorCode.CONNECTION_ERROR
        assert exc.database_url == "postgresql://localhost:5432/healthmate"
        assert exc.details["database_url"] == "postgresql://localhost:5432/healthmate"
    
    def test_query_error_creation(self):
        """Test QueryError creation."""
        exc = QueryError(
            "SQL syntax error",
            query="SELECT * FROM users WHERE id = ?",
            parameters={"id": 123}
        )
        
        assert exc.message == "SQL syntax error"
        assert exc.error_code == ErrorCode.QUERY_ERROR
        assert exc.query == "SELECT * FROM users WHERE id = ?"
        assert exc.parameters == {"id": 123}
        assert exc.details["parameters"] == {"id": 123}


class TestExternalAPIExceptions:
    """Test external API-related exception classes."""
    
    def test_external_api_error_creation(self):
        """Test ExternalAPIError creation."""
        exc = ExternalAPIError(
            "API request failed",
            api_name="OpenAI",
            response_status=500,
            response_body="Internal server error"
        )
        
        assert exc.message == "API request failed"
        assert exc.error_code == ErrorCode.EXTERNAL_API_ERROR
        assert exc.status_code == 502
        assert exc.api_name == "OpenAI"
        assert exc.response_status == 500
        assert exc.response_body == "Internal server error"
        assert exc.details["api_name"] == "OpenAI"
        assert exc.details["response_status"] == 500
        assert exc.details["response_body"] == "Internal server error"
    
    def test_api_error_creation(self):
        """Test APIError creation."""
        exc = APIError(
            "Endpoint not found",
            api_name="HealthAPI",
            endpoint="/v1/health-data",
            response_status=404
        )
        
        assert exc.message == "Endpoint not found"
        assert exc.api_name == "HealthAPI"
        assert exc.endpoint == "/v1/health-data"
        assert exc.response_status == 404
        assert exc.details["endpoint"] == "/v1/health-data"
    
    def test_rate_limit_error_creation(self):
        """Test RateLimitError creation."""
        exc = RateLimitError(
            "Rate limit exceeded",
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
        assert exc.log_level == logging.WARNING


class TestHealthExceptions:
    """Test health data-related exception classes."""
    
    def test_health_data_error_creation(self):
        """Test HealthDataError creation."""
        exc = HealthDataError(
            "Failed to process health data",
            data_type="blood_pressure",
            user_id=123
        )
        
        assert exc.message == "Failed to process health data"
        assert exc.error_code == ErrorCode.HEALTH_DATA_ERROR
        assert exc.status_code == 500
        assert exc.data_type == "blood_pressure"
        assert exc.user_id == 123
        assert exc.details["data_type"] == "blood_pressure"
        assert exc.details["user_id"] == 123
        assert exc.log_level == logging.ERROR
    
    def test_medical_data_error_creation(self):
        """Test MedicalDataError creation."""
        exc = MedicalDataError(
            "Invalid medical data format",
            medical_data_type="lab_results",
            user_id=456,
            severity="high"
        )
        
        assert exc.message == "Invalid medical data format"
        assert exc.medical_data_type == "lab_results"
        assert exc.user_id == 456
        assert exc.severity == "high"
        assert exc.error_code == ErrorCode.INVALID_HEALTH_DATA
        assert exc.details["severity"] == "high"


class TestChatExceptions:
    """Test chat and AI-related exception classes."""
    
    def test_chat_error_creation(self):
        """Test ChatError creation."""
        exc = ChatError(
            "Failed to generate response",
            chat_session_id="session_123"
        )
        
        assert exc.message == "Failed to generate response"
        assert exc.error_code == ErrorCode.CHAT_ERROR
        assert exc.status_code == 500
        assert exc.chat_session_id == "session_123"
        assert exc.details["chat_session_id"] == "session_123"
        assert exc.log_level == logging.ERROR
    
    def test_conversation_error_creation(self):
        """Test ConversationError creation."""
        exc = ConversationError(
            "Conversation context lost",
            conversation_id="conv_456",
            user_id=789,
            error_type="context_loss"
        )
        
        assert exc.message == "Conversation context lost"
        assert exc.conversation_id == "conv_456"
        assert exc.user_id == 789
        assert exc.error_type == "context_loss"
        assert exc.error_code == ErrorCode.RESPONSE_GENERATION_ERROR
        assert exc.details["user_id"] == 789
        assert exc.details["error_type"] == "context_loss"


class TestNotificationExceptions:
    """Test notification-related exception classes."""
    
    def test_notification_error_creation(self):
        """Test NotificationError creation."""
        exc = NotificationError(
            "Failed to send notification",
            notification_type="email",
            user_id=123
        )
        
        assert exc.message == "Failed to send notification"
        assert exc.notification_type == "email"
        assert exc.user_id == 123
        assert exc.error_code == ErrorCode.UNKNOWN_ERROR
        assert exc.status_code == 500
        assert exc.details["notification_type"] == "email"
        assert exc.details["user_id"] == 123
        assert exc.log_level == logging.ERROR
    
    def test_email_error_creation(self):
        """Test EmailError creation."""
        exc = EmailError(
            "Failed to send email",
            recipient="user@example.com",
            subject="Health Alert",
            user_id=456
        )
        
        assert exc.message == "Failed to send email"
        assert exc.recipient == "user@example.com"
        assert exc.subject == "Health Alert"
        assert exc.user_id == 456
        assert exc.notification_type == "email"
        assert exc.details["recipient"] == "user@example.com"
        assert exc.details["subject"] == "Health Alert"
    
    def test_sms_error_creation(self):
        """Test SMSError creation."""
        exc = SMSError(
            "Failed to send SMS",
            phone_number="+1234567890",
            user_id=789
        )
        
        assert exc.message == "Failed to send SMS"
        assert exc.phone_number == "+1234567890"
        assert exc.user_id == 789
        assert exc.notification_type == "sms"
        assert exc.details["phone_number"] == "+1234567890"


class TestResourceNotFoundError:
    """Test ResourceNotFoundError class."""
    
    def test_resource_not_found_error_with_id(self):
        """Test ResourceNotFoundError creation with resource ID."""
        exc = ResourceNotFoundError("User", 123)
        
        assert exc.message == "User with id '123' not found"
        assert exc.error_code == ErrorCode.RESOURCE_NOT_FOUND
        assert exc.status_code == 404
        assert exc.resource_type == "User"
        assert exc.resource_id == 123
        assert exc.details["resource_type"] == "User"
        assert exc.details["resource_id"] == 123
        assert exc.log_level == logging.INFO
    
    def test_resource_not_found_error_without_id(self):
        """Test ResourceNotFoundError creation without resource ID."""
        exc = ResourceNotFoundError("HealthData")
        
        assert exc.message == "HealthData not found"
        assert exc.resource_type == "HealthData"
        assert exc.resource_id is None
        assert exc.details["resource_id"] is None
    
    def test_resource_not_found_error_with_custom_message(self):
        """Test ResourceNotFoundError creation with custom message."""
        exc = ResourceNotFoundError(
            "User",
            123,
            message="User account not found in database"
        )
        
        assert exc.message == "User account not found in database"
        assert exc.resource_type == "User"
        assert exc.resource_id == 123


class TestExceptionIntegration:
    """Test exception system integration."""
    
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
            NotificationError("test"),
            ResourceNotFoundError("test")
        ]
        
        for exc in exceptions:
            assert isinstance(exc, HealthMateException)
    
    def test_exception_serialization(self):
        """Test that all exceptions can be serialized to dict."""
        exceptions = [
            ValidationError("test", field="test_field"),
            AuthenticationError("test"),
            DatabaseError("test"),
            ExternalAPIError("test", "test_api"),
            HealthDataError("test"),
            ChatError("test"),
            ResourceNotFoundError("test")
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
        # Test that each exception type has the expected error code
        assert ValidationError("test").error_code == ErrorCode.VALIDATION_ERROR
        assert AuthenticationError("test").error_code == ErrorCode.AUTHENTICATION_FAILED
        assert AuthorizationError("test").error_code == ErrorCode.INSUFFICIENT_PERMISSIONS
        assert DatabaseError("test").error_code == ErrorCode.DATABASE_ERROR
        assert ExternalAPIError("test", "api").error_code == ErrorCode.EXTERNAL_API_ERROR
        assert HealthDataError("test").error_code == ErrorCode.HEALTH_DATA_ERROR
        assert ChatError("test").error_code == ErrorCode.CHAT_ERROR
        assert ResourceNotFoundError("test").error_code == ErrorCode.RESOURCE_NOT_FOUND
        assert RateLimitError("test").error_code == ErrorCode.RATE_LIMIT_EXCEEDED 
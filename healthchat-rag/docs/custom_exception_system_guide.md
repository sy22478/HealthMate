# HealthMate Custom Exception System Guide

## Overview

The HealthMate application implements a comprehensive custom exception system that provides standardized error handling across the entire application. This system ensures consistent error responses, proper logging, and type-safe exception handling.

## Architecture

### Exception Hierarchy

```
HealthMateException (Base)
├── ValidationError
│   ├── SchemaValidationError
│   └── InputValidationError
├── AuthenticationError
│   └── TokenError
├── AuthorizationError
├── DatabaseError
│   ├── ConnectionError
│   └── QueryError
├── ExternalAPIError
│   └── APIError
├── HealthDataError
│   └── MedicalDataError
├── ChatError
│   └── ConversationError
├── NotificationError
│   ├── EmailError
│   └── SMSError
├── ResourceNotFoundError
└── RateLimitError
```

### Error Code System

The system uses a structured error code numbering scheme:

- **1000-1999**: General errors
- **2000-2999**: Authentication errors
- **3000-3999**: Validation errors
- **4000-4999**: Database errors
- **5000-5999**: External API errors
- **6000-6999**: Health data errors
- **7000-7999**: Chat/AI errors

## Usage Examples

### 1. Basic Exception Creation

```python
from app.exceptions import HealthMateException, ErrorCode

# Simple exception
exc = HealthMateException("Something went wrong")

# With custom error code
exc = HealthMateException(
    message="Custom error message",
    error_code=ErrorCode.INVALID_REQUEST,
    status_code=400
)
```

### 2. Validation Errors

```python
from app.exceptions import ValidationError, SchemaValidationError, InputValidationError

# Basic validation error
exc = ValidationError(
    message="Invalid email format",
    field="email",
    value="invalid-email"
)

# Schema validation error
exc = SchemaValidationError(
    message="Schema validation failed",
    schema_name="UserSchema",
    field="email"
)

# Input validation error
exc = InputValidationError(
    message="Invalid phone number format",
    field="phone",
    value="123",
    validation_type="phone_format"
)
```

### 3. Authentication & Authorization

```python
from app.exceptions import AuthenticationError, AuthorizationError, TokenError

# Authentication error
exc = AuthenticationError(
    "Invalid credentials",
    error_code=ErrorCode.INVALID_CREDENTIALS
)

# Authorization error
exc = AuthorizationError(
    "Insufficient permissions",
    required_permissions=["read:health_data", "write:health_data"]
)

# Token error
exc = TokenError(
    "Invalid access token",
    token_type="access",
    error_code=ErrorCode.INVALID_TOKEN
)
```

### 4. Database Errors

```python
from app.exceptions import DatabaseError, ConnectionError, QueryError

# Database error
exc = DatabaseError(
    "Database connection failed",
    query="SELECT * FROM users WHERE id = 123"
)

# Connection error
exc = ConnectionError(
    "Failed to connect to database",
    database_url="postgresql://localhost:5432/healthmate"
)

# Query error
exc = QueryError(
    "SQL syntax error",
    query="SELECT * FROM users WHERE id = ?",
    parameters={"id": 123}
)
```

### 5. External API Errors

```python
from app.exceptions import ExternalAPIError, APIError, RateLimitError

# External API error
exc = ExternalAPIError(
    "OpenAI API request failed",
    api_name="OpenAI",
    response_status=500,
    response_body="Internal server error"
)

# API error
exc = APIError(
    "Endpoint not found",
    api_name="HealthAPI",
    endpoint="/v1/health-data",
    response_status=404
)

# Rate limit error
exc = RateLimitError(
    "Rate limit exceeded",
    retry_after=60,
    limit=100,
    window=3600
)
```

### 6. Health Data Errors

```python
from app.exceptions import HealthDataError, MedicalDataError

# Health data error
exc = HealthDataError(
    "Failed to process blood pressure data",
    data_type="blood_pressure",
    user_id=123
)

# Medical data error
exc = MedicalDataError(
    "Invalid medical data format",
    medical_data_type="lab_results",
    user_id=456,
    severity="high"
)
```

### 7. Chat & AI Errors

```python
from app.exceptions import ChatError, ConversationError

# Chat error
exc = ChatError(
    "Failed to generate AI response",
    chat_session_id="session_123"
)

# Conversation error
exc = ConversationError(
    "Conversation context lost",
    conversation_id="conv_456",
    user_id=789,
    error_type="context_loss"
)
```

### 8. Notification Errors

```python
from app.exceptions import NotificationError, EmailError, SMSError

# Notification error
exc = NotificationError(
    "Failed to send notification",
    notification_type="email",
    user_id=123
)

# Email error
exc = EmailError(
    "Failed to send email",
    recipient="user@example.com",
    subject="Health Alert",
    user_id=456
)

# SMS error
exc = SMSError(
    "Failed to send SMS",
    phone_number="+1234567890",
    user_id=789
)
```

### 9. Resource Not Found

```python
from app.exceptions import ResourceNotFoundError

# Resource not found with ID
exc = ResourceNotFoundError("User", 123)

# Resource not found without ID
exc = ResourceNotFoundError("HealthData")

# With custom message
exc = ResourceNotFoundError(
    "User",
    123,
    message="User account not found in database"
)
```

## FastAPI Integration

### Exception Handlers

The system includes comprehensive FastAPI exception handlers that automatically convert exceptions to standardized JSON responses:

```python
from app.utils.exception_handlers import setup_exception_handlers
from fastapi import FastAPI

app = FastAPI()
setup_exception_handlers(app)
```

### API Response Format

All exceptions are automatically converted to this JSON format:

```json
{
  "error": {
    "code": 3000,
    "message": "Invalid email format",
    "status_code": 422,
    "timestamp": "2024-01-01T12:00:00Z",
    "details": {
      "field": "email",
      "value": "invalid-email"
    },
    "type": "ValidationError"
  }
}
```

### Using in API Endpoints

```python
from fastapi import APIRouter
from app.exceptions import ValidationError, ResourceNotFoundError

router = APIRouter()

@router.get("/users/{user_id}")
async def get_user(user_id: int):
    # Simulate user not found
    if user_id == 999:
        raise ResourceNotFoundError("User", user_id)
    
    # Simulate validation error
    if user_id < 0:
        raise ValidationError(
            "User ID must be positive",
            field="user_id",
            value=user_id
        )
    
    return {"user_id": user_id, "name": "John Doe"}
```

## Logging

All exceptions are automatically logged with appropriate log levels:

- **ERROR**: Database errors, external API errors, health data errors, chat errors
- **WARNING**: Validation errors, authentication errors, authorization errors, rate limit errors
- **INFO**: Resource not found errors

### Log Format

```
HealthMateException: Invalid email format (Code: 3000) | Context: {'user_id': 123, 'action': 'registration'} | Details: {'field': 'email', 'value': 'invalid-email'}
```

## Best Practices

### 1. Use Specific Exception Types

```python
# Good: Use specific exception type
raise ValidationError("Invalid email", field="email", value=email)

# Avoid: Use generic exception
raise HealthMateException("Invalid email")
```

### 2. Provide Rich Context

```python
# Good: Include relevant details
raise DatabaseError(
    "Failed to create user",
    query="INSERT INTO users (email, name) VALUES (?, ?)",
    details={"email": email, "name": name}
)

# Avoid: Minimal information
raise DatabaseError("Database error")
```

### 3. Use Appropriate Error Codes

```python
# Good: Use specific error codes
raise AuthenticationError(
    "Token expired",
    error_code=ErrorCode.TOKEN_EXPIRED
)

# Avoid: Use generic error codes
raise AuthenticationError("Authentication failed")
```

### 4. Handle Exceptions Gracefully

```python
from app.exceptions import HealthMateException, handle_exception

@handle_exception
def process_health_data(data):
    # Your code here
    if not data:
        raise ValidationError("Health data is required")
    return process_data(data)
```

### 5. Test Exception Handling

```python
import pytest
from app.exceptions import ValidationError

def test_validation_error():
    with pytest.raises(ValidationError) as exc_info:
        raise ValidationError("Invalid input", field="test")
    
    assert exc_info.value.field == "test"
    assert exc_info.value.error_code.value == 3000
    assert exc_info.value.status_code == 422
```

## Error Code Reference

### General Errors (1000-1999)
- `UNKNOWN_ERROR` (1000): Generic unknown error
- `INVALID_REQUEST` (1001): Invalid request format
- `RESOURCE_NOT_FOUND` (1002): Requested resource not found
- `PERMISSION_DENIED` (1003): Permission denied
- `RATE_LIMIT_EXCEEDED` (1004): Rate limit exceeded
- `SERVICE_UNAVAILABLE` (1005): Service temporarily unavailable

### Authentication Errors (2000-2999)
- `AUTHENTICATION_FAILED` (2000): Authentication failed
- `INVALID_TOKEN` (2001): Invalid token
- `TOKEN_EXPIRED` (2002): Token expired
- `INSUFFICIENT_PERMISSIONS` (2003): Insufficient permissions
- `ACCOUNT_LOCKED` (2004): Account locked
- `INVALID_CREDENTIALS` (2005): Invalid credentials

### Validation Errors (3000-3999)
- `VALIDATION_ERROR` (3000): General validation error
- `INVALID_INPUT` (3001): Invalid input format
- `MISSING_REQUIRED_FIELD` (3002): Required field missing
- `INVALID_FORMAT` (3003): Invalid data format
- `DUPLICATE_ENTRY` (3004): Duplicate entry
- `CONSTRAINT_VIOLATION` (3005): Constraint violation

### Database Errors (4000-4999)
- `DATABASE_ERROR` (4000): General database error
- `CONNECTION_ERROR` (4001): Database connection error
- `QUERY_ERROR` (4002): Database query error
- `TRANSACTION_ERROR` (4003): Transaction error
- `INTEGRITY_ERROR` (4004): Data integrity error

### External API Errors (5000-5999)
- `EXTERNAL_API_ERROR` (5000): General external API error
- `API_TIMEOUT` (5001): API timeout
- `API_RATE_LIMIT` (5002): API rate limit
- `API_AUTHENTICATION_ERROR` (5003): API authentication error
- `API_SERVICE_UNAVAILABLE` (5004): API service unavailable

### Health Data Errors (6000-6999)
- `HEALTH_DATA_ERROR` (6000): General health data error
- `INVALID_HEALTH_DATA` (6001): Invalid health data
- `ENCRYPTION_ERROR` (6002): Encryption error
- `DECRYPTION_ERROR` (6003): Decryption error
- `DATA_CORRUPTION` (6004): Data corruption

### Chat/AI Errors (7000-7999)
- `CHAT_ERROR` (7000): General chat error
- `AI_SERVICE_ERROR` (7001): AI service error
- `VECTOR_STORE_ERROR` (7002): Vector store error
- `KNOWLEDGE_BASE_ERROR` (7003): Knowledge base error
- `RESPONSE_GENERATION_ERROR` (7004): Response generation error

## Migration Guide

### From Generic Exceptions

If you're currently using generic exceptions, here's how to migrate:

```python
# Before
raise Exception("User not found")

# After
from app.exceptions import ResourceNotFoundError
raise ResourceNotFoundError("User", user_id)
```

### From HTTP Exceptions

```python
# Before
from fastapi import HTTPException
raise HTTPException(status_code=404, detail="User not found")

# After
from app.exceptions import ResourceNotFoundError
raise ResourceNotFoundError("User", user_id)
```

### From Custom Exceptions

```python
# Before
class UserNotFoundError(Exception):
    pass

# After
from app.exceptions import ResourceNotFoundError
# Use ResourceNotFoundError directly
```

## Testing

### Running Tests

```bash
# Run all exception tests
pytest tests/test_custom_exception_system.py -v

# Run specific test class
pytest tests/test_custom_exception_system.py::TestValidationExceptions -v

# Run with coverage
pytest tests/test_custom_exception_system.py --cov=app.exceptions
```

### Test Examples

```python
import pytest
from app.exceptions import ValidationError, ErrorCode

def test_validation_error_creation():
    exc = ValidationError(
        message="Invalid email",
        field="email",
        value="invalid"
    )
    
    assert exc.message == "Invalid email"
    assert exc.field == "email"
    assert exc.value == "invalid"
    assert exc.error_code == ErrorCode.VALIDATION_ERROR
    assert exc.status_code == 422

def test_exception_serialization():
    exc = ValidationError("Test error", field="test")
    result = exc.to_dict()
    
    assert "error" in result
    assert result["error"]["code"] == 3000
    assert result["error"]["message"] == "Test error"
    assert result["error"]["type"] == "ValidationError"
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure you're importing from `app.exceptions`
2. **Missing Error Codes**: Check that the error code exists in the `ErrorCode` enum
3. **Logging Issues**: Ensure logging is properly configured
4. **FastAPI Integration**: Verify that exception handlers are set up in your FastAPI app

### Debug Mode

Enable debug logging to see detailed exception information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Conclusion

The HealthMate custom exception system provides a robust, type-safe, and consistent way to handle errors across the application. By following the patterns and best practices outlined in this guide, you can ensure reliable error handling and improve the overall quality of your application. 
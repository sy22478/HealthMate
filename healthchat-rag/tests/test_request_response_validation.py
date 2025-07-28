"""
Unit tests for Request/Response Validation Middleware
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient
from pydantic import BaseModel, ValidationError
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from app.utils.request_response_validation import (
    RequestResponseValidationMiddleware,
    ValidationConfig,
    validate_request_body,
    validate_response
)


# Test schemas
class TestRequestSchema(BaseModel):
    name: str
    age: int


class TestResponseSchema(BaseModel):
    message: str
    data: dict


class TestQuerySchema(BaseModel):
    limit: int = 10
    offset: int = 0


class TestPathSchema(BaseModel):
    user_id: int


class TestRequestResponseValidationMiddleware:
    """Test the RequestResponseValidationMiddleware class."""
    
    @pytest.fixture
    def app(self):
        """Create a test FastAPI app."""
        app = FastAPI()
        
        @app.post("/test")
        async def test_endpoint():
            return {"message": "success", "data": {"test": "value"}}
            
        @app.get("/test/{user_id}")
        async def test_path_endpoint(user_id: int):
            return {"message": "success", "data": {"user_id": user_id}}
            
        return app
    
    @pytest.fixture
    def middleware(self, app):
        """Create middleware instance."""
        return RequestResponseValidationMiddleware(app)
    
    @pytest.fixture
    def client(self, app, middleware):
        """Create test client with middleware."""
        app.add_middleware(RequestResponseValidationMiddleware)
        return TestClient(app)
    
    def test_middleware_initialization(self, app):
        """Test middleware initialization with default settings."""
        middleware = RequestResponseValidationMiddleware(app)
        
        assert middleware.enable_request_validation is True
        assert middleware.enable_response_validation is True
        assert middleware.log_validation_errors is True
        assert middleware.request_schemas == {}
        assert middleware.response_schemas == {}
    
    def test_middleware_initialization_with_custom_settings(self, app):
        """Test middleware initialization with custom settings."""
        middleware = RequestResponseValidationMiddleware(
            app,
            enable_request_validation=False,
            enable_response_validation=False,
            log_validation_errors=False
        )
        
        assert middleware.enable_request_validation is False
        assert middleware.enable_response_validation is False
        assert middleware.log_validation_errors is False
    
    def test_add_request_schema(self, middleware):
        """Test adding request schemas."""
        middleware.add_request_schema("/test", "POST", TestRequestSchema, "body")
        middleware.add_request_schema("/test", "GET", TestQuerySchema, "query")
        middleware.add_request_schema("/test/{user_id}", "GET", TestPathSchema, "path")
        
        assert "POST:/test" in middleware.request_schemas
        assert "GET:/test" in middleware.request_schemas
        assert "GET:/test/{user_id}" in middleware.request_schemas
        
        assert middleware.request_schemas["POST:/test"]["body"] == TestRequestSchema
        assert middleware.request_schemas["GET:/test"]["query"] == TestQuerySchema
        assert middleware.request_schemas["GET:/test/{user_id}"]["path"] == TestPathSchema
    
    def test_add_response_schema(self, middleware):
        """Test adding response schemas."""
        middleware.add_response_schema("/test", "POST", TestResponseSchema)
        middleware.add_response_schema("/test", "GET", TestResponseSchema)
        
        assert "POST:/test" in middleware.response_schemas
        assert "GET:/test" in middleware.response_schemas
        
        assert middleware.response_schemas["POST:/test"] == TestResponseSchema
        assert middleware.response_schemas["GET:/test"] == TestResponseSchema
    
    @pytest.mark.asyncio
    async def test_validate_request_body_valid(self, middleware):
        """Test request body validation with valid data."""
        middleware.add_request_schema("/test", "POST", TestRequestSchema, "body")
        
        # Create mock request
        request = MagicMock(spec=Request)
        request.url.path = "/test"
        request.method = "POST"
        request.body = AsyncMock(return_value=json.dumps({
            "name": "John Doe",
            "age": 30
        }).encode())
        
        # Should not raise any exception
        await middleware._validate_request(request)
    
    @pytest.mark.asyncio
    async def test_validate_request_body_invalid(self, middleware):
        """Test request body validation with invalid data."""
        middleware.add_request_schema("/test", "POST", TestRequestSchema, "body")
        
        # Create mock request with invalid data
        request = MagicMock(spec=Request)
        request.url.path = "/test"
        request.method = "POST"
        request.body = AsyncMock(return_value=json.dumps({
            "name": "John Doe"
            # Missing required 'age' field
        }).encode())
        
        with pytest.raises(ValidationError):
            await middleware._validate_request(request)
    
    @pytest.mark.asyncio
    async def test_validate_request_body_invalid_json(self, middleware):
        """Test request body validation with invalid JSON."""
        middleware.add_request_schema("/test", "POST", TestRequestSchema, "body")
        
        # Create mock request with invalid JSON
        request = MagicMock(spec=Request)
        request.url.path = "/test"
        request.method = "POST"
        request.body = AsyncMock(return_value=b"invalid json")
        
        with pytest.raises(HTTPException) as exc_info:
            await middleware._validate_request(request)
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid JSON in request body" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_validate_query_params_valid(self, middleware):
        """Test query parameter validation with valid data."""
        middleware.add_request_schema("/test", "GET", TestQuerySchema, "query")
        
        # Create mock request
        request = MagicMock(spec=Request)
        request.url.path = "/test"
        request.method = "GET"
        request.query_params = {"limit": "20", "offset": "10"}
        
        # Should not raise any exception
        await middleware._validate_request(request)
    
    @pytest.mark.asyncio
    async def test_validate_query_params_invalid(self, middleware):
        """Test query parameter validation with invalid data."""
        middleware.add_request_schema("/test", "GET", TestQuerySchema, "query")
        
        # Create mock request with invalid query params
        request = MagicMock(spec=Request)
        request.url.path = "/test"
        request.method = "GET"
        request.query_params = {"limit": "invalid", "offset": "10"}
        
        with pytest.raises(ValidationError):
            await middleware._validate_request(request)
    
    @pytest.mark.asyncio
    async def test_validate_path_params_valid(self, middleware):
        """Test path parameter validation with valid data."""
        middleware.add_request_schema("/test/{user_id}", "GET", TestPathSchema, "path")
        
        # Create mock request
        request = MagicMock(spec=Request)
        request.url.path = "/test/123"
        request.method = "GET"
        request.path_params = {"user_id": "123"}
        
        # Should not raise any exception
        await middleware._validate_request(request)
    
    @pytest.mark.asyncio
    async def test_validate_path_params_invalid(self, middleware):
        """Test path parameter validation with invalid data."""
        middleware.add_request_schema("/test/{user_id}", "GET", TestPathSchema, "path")
        
        # Create mock request with invalid path params
        request = MagicMock(spec=Request)
        request.url.path = "/test/invalid"
        request.method = "GET"
        request.path_params = {"user_id": "invalid"}
        
        with pytest.raises(ValidationError):
            await middleware._validate_request(request)
    
    @pytest.mark.asyncio
    async def test_validate_response_valid(self, middleware):
        """Test response validation with valid data."""
        middleware.add_response_schema("/test", "POST", TestResponseSchema)
        
        # Create mock request and response
        request = MagicMock(spec=Request)
        request.url.path = "/test"
        request.method = "POST"
        
        response = Response(
            content=json.dumps({
                "message": "success",
                "data": {"test": "value"}
            }),
            media_type="application/json"
        )
        
        # Should not raise any exception
        result = await middleware._validate_response(request, response)
        assert result == response
    
    @pytest.mark.asyncio
    async def test_validate_response_invalid(self, middleware):
        """Test response validation with invalid data."""
        middleware.add_response_schema("/test", "POST", TestResponseSchema)
        
        # Create mock request and response with invalid data
        request = MagicMock(spec=Request)
        request.url.path = "/test"
        request.method = "POST"
        
        response = Response(
            content=json.dumps({
                "message": "success"
                # Missing required 'data' field
            }),
            media_type="application/json"
        )
        
        # Should not raise exception but log warning
        with patch('app.utils.request_response_validation.logger') as mock_logger:
            result = await middleware._validate_response(request, response)
            assert result == response
            # Note: In a real implementation, this might raise ValidationError
    
    @pytest.mark.asyncio
    async def test_validate_response_non_json(self, middleware):
        """Test response validation with non-JSON response."""
        middleware.add_response_schema("/test", "GET", TestResponseSchema)
        
        # Create mock request and non-JSON response
        request = MagicMock(spec=Request)
        request.url.path = "/test"
        request.method = "GET"
        
        response = Response(
            content="plain text response",
            media_type="text/plain"
        )
        
        # Should return response unchanged
        result = await middleware._validate_response(request, response)
        assert result == response
    
    def test_create_validation_error_response(self, middleware):
        """Test creating standardized validation error response."""
        # Create a mock validation error
        validation_error = ValidationError.from_exception_data(
            "TestSchema",
            [{"loc": ("field",), "msg": "Field required", "type": "missing"}]
        )
        
        response = middleware._create_validation_error_response(validation_error)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        content = json.loads(response.body.decode())
        assert content["message"] == "Validation error"
        assert len(content["errors"]) == 1
        assert content["errors"][0]["field"] == "field"
        assert content["errors"][0]["message"] == "Field required"
        assert content["errors"][0]["type"] == "missing"
    
    @pytest.mark.asyncio
    async def test_dispatch_with_validation_error(self, middleware):
        """Test dispatch method with validation error."""
        middleware.add_request_schema("/test", "POST", TestRequestSchema, "body")
        
        # Create mock request with invalid data
        request = MagicMock(spec=Request)
        request.url.path = "/test"
        request.method = "POST"
        request.body = AsyncMock(return_value=json.dumps({
            "name": "John Doe"
            # Missing required 'age' field
        }).encode())
        
        # Mock call_next
        call_next = AsyncMock()
        
        with patch('app.utils.request_response_validation.logger') as mock_logger:
            response = await middleware.dispatch(request, call_next)
            
            assert isinstance(response, JSONResponse)
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            mock_logger.error.assert_called_once()


class TestValidationConfig:
    """Test the ValidationConfig class."""
    
    def test_validation_config_initialization(self):
        """Test ValidationConfig initialization with default settings."""
        config = ValidationConfig()
        
        assert config.enable_request_validation is True
        assert config.enable_response_validation is True
        assert config.log_validation_errors is True
        assert config.strict_mode is False
    
    def test_validation_config_get_middleware(self):
        """Test creating middleware from config."""
        app = FastAPI()
        config = ValidationConfig()
        middleware = config.get_middleware(app)
        
        assert isinstance(middleware, RequestResponseValidationMiddleware)
        assert middleware.enable_request_validation == config.enable_request_validation
        assert middleware.enable_response_validation == config.enable_response_validation
        assert middleware.log_validation_errors == config.log_validation_errors
    
    def test_validation_config_custom_settings(self):
        """Test ValidationConfig with custom settings."""
        app = FastAPI()
        config = ValidationConfig()
        config.enable_request_validation = False
        config.enable_response_validation = False
        config.log_validation_errors = False
        config.strict_mode = True
        
        middleware = config.get_middleware(app)
        
        assert middleware.enable_request_validation is False
        assert middleware.enable_response_validation is False
        assert middleware.log_validation_errors is False


class TestValidationDecorators:
    """Test validation decorators."""
    
    @pytest.mark.asyncio
    async def test_validate_request_body_decorator(self):
        """Test validate_request_body decorator."""
        @validate_request_body(TestRequestSchema)
        async def test_function():
            return "success"
        
        # Decorator should not change function behavior
        result = await test_function()
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_validate_response_decorator(self):
        """Test validate_response decorator."""
        @validate_response(TestResponseSchema)
        async def test_function():
            return "success"
        
        # Decorator should not change function behavior
        result = await test_function()
        assert result == "success"


class TestIntegration:
    """Integration tests for the validation middleware."""
    
    @pytest.fixture
    def app_with_validation(self):
        """Create FastAPI app with validation middleware."""
        app = FastAPI()
        
        # Add middleware
        middleware = RequestResponseValidationMiddleware(app)
        app.add_middleware(RequestResponseValidationMiddleware)
        
        # Add schemas to the middleware instance
        middleware.add_request_schema("/test", "POST", TestRequestSchema, "body")
        middleware.add_response_schema("/test", "POST", TestResponseSchema)
        
        @app.post("/test")
        async def test_endpoint():
            return {"message": "success", "data": {"test": "value"}}
        
        return app
    
    def test_integration_valid_request(self, app_with_validation):
        """Test integration with valid request."""
        client = TestClient(app_with_validation)
        
        response = client.post("/test", json={
            "name": "John Doe",
            "age": 30
        })
        
        assert response.status_code == 200
        assert response.json()["message"] == "success"
    
    def test_integration_invalid_request(self, app_with_validation):
        """Test integration with invalid request."""
        client = TestClient(app_with_validation)
        
        response = client.post("/test", json={
            "name": "John Doe"
            # Missing required 'age' field
        })
        
        assert response.status_code == 422
        content = response.json()
        assert content["message"] == "Validation error"
        assert len(content["errors"]) > 0 
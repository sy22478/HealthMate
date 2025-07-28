"""
Unit tests for secure communication features

This module tests:
- HTTPS/TLS enforcement
- Security headers
- CORS configuration
- Request/response validation
"""

import pytest
import json
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from app.main import app
from app.config import settings
from app.utils.security_middleware import SecurityMiddleware, TLSCheckMiddleware
from app.utils.request_response_validation import RequestResponseValidationMiddleware


class TestSecurityMiddleware:
    """Test cases for SecurityMiddleware"""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.app = FastAPI()
        self.middleware = SecurityMiddleware(
            app=self.app,
            enforce_https=True,
            security_headers=True,
            hsts_enabled=True,
            csp_enabled=True
        )
    
    def test_is_secure_request_https_scheme(self):
        """Test HTTPS scheme detection."""
        request = Mock()
        request.url.scheme = "https"
        request.headers = {}
        
        assert self.middleware._is_secure_request(request) is True
    
    def test_is_secure_request_forwarded_proto(self):
        """Test forwarded protocol detection."""
        request = Mock()
        request.url.scheme = "http"
        request.headers = {"x-forwarded-proto": "https"}
        
        assert self.middleware._is_secure_request(request) is True
    
    def test_is_secure_request_forwarded_ssl(self):
        """Test forwarded SSL detection."""
        request = Mock()
        request.url.scheme = "http"
        request.headers = {"x-forwarded-ssl": "on"}
        
        assert self.middleware._is_secure_request(request) is True
    
    def test_is_secure_request_insecure(self):
        """Test insecure request detection."""
        request = Mock()
        request.url.scheme = "http"
        request.headers = {}
        
        assert self.middleware._is_secure_request(request) is False
    
    def test_is_https_excluded_health_endpoint(self):
        """Test HTTPS exclusion for health endpoint."""
        assert self.middleware._is_https_excluded("/health") is True
    
    def test_is_https_excluded_docs_endpoint(self):
        """Test HTTPS exclusion for docs endpoint."""
        assert self.middleware._is_https_excluded("/docs") is True
    
    def test_is_https_excluded_api_endpoint(self):
        """Test HTTPS exclusion for API endpoint."""
        assert self.middleware._is_https_excluded("/auth/login") is False
    
    def test_create_https_redirect_response(self):
        """Test HTTPS redirect response creation."""
        request = Mock()
        request.url = "http://localhost:8000/api/test"
        
        response = self.middleware._create_https_redirect_response(request)
        
        assert response.status_code == 301
        assert "https://localhost:8000/api/test" in response.headers["Location"]
        assert "Strict-Transport-Security" in response.headers
    
    def test_add_security_headers(self):
        """Test security headers addition."""
        response = Response()
        
        modified_response = self.middleware._add_security_headers(response)
        
        # Check for security headers
        assert "Strict-Transport-Security" in modified_response.headers
        assert "Content-Security-Policy" in modified_response.headers
        assert "X-Frame-Options" in modified_response.headers
        assert "X-Content-Type-Options" in modified_response.headers
        assert "X-XSS-Protection" in modified_response.headers
        assert "Referrer-Policy" in modified_response.headers
        assert "X-Permitted-Cross-Domain-Policies" in modified_response.headers
    
    def test_build_hsts_header(self):
        """Test HSTS header building."""
        header = self.middleware._build_hsts_header()
        
        assert "max-age=" in header
        assert "includeSubDomains" in header
    
    @patch('app.utils.security_middleware.settings')
    def test_build_hsts_header_without_subdomains(self, mock_settings):
        """Test HSTS header without subdomains."""
        mock_settings.hsts_max_age = 31536000
        mock_settings.hsts_include_subdomains = False
        mock_settings.hsts_preload = False
        
        middleware = SecurityMiddleware(app=self.app, hsts_enabled=True)
        header = middleware._build_hsts_header()
        
        assert "max-age=31536000" in header
        assert "includeSubDomains" not in header


class TestTLSCheckMiddleware:
    """Test cases for TLSCheckMiddleware"""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.app = FastAPI()
        self.middleware = TLSCheckMiddleware(app=self.app)
    
    @patch('app.utils.security_middleware.settings')
    def test_check_tls_config_production_with_certs(self, mock_settings):
        """Test TLS config check in production with certificates."""
        mock_settings.is_production = True
        mock_settings.ssl_certfile = "/path/to/cert.pem"
        mock_settings.ssl_keyfile = "/path/to/key.pem"
        
        with patch('os.path.exists', return_value=True):
            with patch('app.utils.security_middleware.logger') as mock_logger:
                middleware = TLSCheckMiddleware(app=self.app)
                middleware._check_tls_config()
                
                mock_logger.info.assert_called_with(
                    "SSL certificate and key files configured for production"
                )
    
    @patch('app.utils.security_middleware.settings')
    def test_check_tls_config_production_without_certs(self, mock_settings):
        """Test TLS config check in production without certificates."""
        mock_settings.is_production = True
        mock_settings.ssl_certfile = None
        mock_settings.ssl_keyfile = None
        
        with patch('app.utils.security_middleware.logger') as mock_logger:
            middleware = TLSCheckMiddleware(app=self.app)
            middleware._check_tls_config()
            
            mock_logger.warning.assert_called()


class TestCORSConfiguration:
    """Test cases for CORS configuration"""
    
    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)
    
    def test_cors_headers_present(self):
        """Test that CORS headers are present in responses."""
        # Test with Origin header to trigger CORS
        response = self.client.get("/", headers={"Origin": "http://localhost:3000"})
        
        # Check for CORS headers (only origin and credentials are set for GET requests)
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-credentials" in response.headers
    
    def test_cors_preflight_request(self):
        """Test CORS preflight request handling."""
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type"
        }
        
        response = self.client.options("/auth/login", headers=headers)
        
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
    
    @patch('app.config.settings')
    def test_cors_restricted_origins(self, mock_settings):
        """Test CORS with restricted origins."""
        mock_settings.cors_origins_list = ["https://trusted-domain.com"]
        mock_settings.cors_allow_credentials = True
        mock_settings.cors_methods_list = ["GET", "POST"]
        mock_settings.cors_headers_list = ["Content-Type"]
        mock_settings.cors_expose_headers_list = []
        mock_settings.cors_max_age = 600
        
        # Create a new app with restricted CORS
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        
        test_app = FastAPI()
        test_app.add_middleware(
            CORSMiddleware,
            allow_origins=mock_settings.cors_origins_list,
            allow_credentials=mock_settings.cors_allow_credentials,
            allow_methods=mock_settings.cors_methods_list,
            allow_headers=mock_settings.cors_headers_list,
            expose_headers=mock_settings.cors_expose_headers_list,
            max_age=mock_settings.cors_max_age,
        )
        
        @test_app.get("/")
        def root():
            return {"message": "test"}
        
        client = TestClient(test_app)
        
        # Test allowed origin
        response = client.get("/", headers={"Origin": "https://trusted-domain.com"})
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "https://trusted-domain.com"
        
        # Test disallowed origin
        response = client.get("/", headers={"Origin": "https://malicious-site.com"})
        assert response.status_code == 200
        assert "access-control-allow-origin" not in response.headers


class TestSecurityHeaders:
    """Test cases for security headers"""
    
    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)
    
    def test_security_headers_present(self):
        """Test that security headers are present in responses."""
        response = self.client.get("/")
        
        # Check for security headers
        assert "x-frame-options" in response.headers
        assert "x-content-type-options" in response.headers
        assert "x-xss-protection" in response.headers
        assert "referrer-policy" in response.headers
        assert "x-permitted-cross-domain-policies" in response.headers
    
    @patch('app.config.settings')
    def test_hsts_header_in_production(self, mock_settings):
        """Test HSTS header in production environment."""
        mock_settings.is_production = True
        mock_settings.hsts_max_age = 31536000
        mock_settings.hsts_include_subdomains = True
        mock_settings.hsts_preload = False
        
        # Create a new app with production settings
        from fastapi import FastAPI
        from app.utils.security_middleware import SecurityMiddleware
        
        test_app = FastAPI()
        test_app.add_middleware(SecurityMiddleware, hsts_enabled=True)
        
        @test_app.get("/")
        def root():
            return {"message": "test"}
        
        client = TestClient(test_app)
        response = client.get("/")
        
        assert "strict-transport-security" in response.headers
        hsts_header = response.headers["strict-transport-security"]
        assert "max-age=31536000" in hsts_header
        assert "includeSubDomains" in hsts_header
    
    @patch('app.config.settings')
    def test_csp_header_in_production(self, mock_settings):
        """Test Content Security Policy header in production."""
        mock_settings.is_production = True
        mock_settings.content_security_policy = "default-src 'self'"
        
        # Create a new app with production settings
        from fastapi import FastAPI
        from app.utils.security_middleware import SecurityMiddleware
        
        test_app = FastAPI()
        test_app.add_middleware(SecurityMiddleware, csp_enabled=True)
        
        @test_app.get("/")
        def root():
            return {"message": "test"}
        
        client = TestClient(test_app)
        response = client.get("/")
        
        assert "content-security-policy" in response.headers
        # Check that the CSP header contains the expected value
        csp_header = response.headers["content-security-policy"]
        assert "default-src 'self'" in csp_header


class TestRequestResponseValidation:
    """Test cases for request/response validation"""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.app = FastAPI()
        self.middleware = RequestResponseValidationMiddleware(
            app=self.app,
            enable_request_validation=True,
            enable_response_validation=True,
            log_validation_errors=True
        )
    
    def test_add_request_schema(self):
        """Test adding request schema."""
        from pydantic import BaseModel
        
        class TestSchema(BaseModel):
            name: str
            age: int
        
        self.middleware.add_request_schema("/test", "POST", TestSchema)
        
        key = "POST:/test"
        assert key in self.middleware.request_schemas
        assert "body" in self.middleware.request_schemas[key]
    
    def test_add_response_schema(self):
        """Test adding response schema."""
        from pydantic import BaseModel
        
        class TestSchema(BaseModel):
            message: str
        
        self.middleware.add_response_schema("/test", "GET", TestSchema)
        
        key = "GET:/test"
        assert key in self.middleware.response_schemas
    
    def test_create_validation_error_response(self):
        """Test validation error response creation."""
        from pydantic import ValidationError
        
        # Create a mock validation error
        try:
            error = ValidationError.from_exception_data(
                "TestModel",
                [{"loc": ("field",), "msg": "field required", "type": "missing"}]
            )
        except KeyError:
            # Fallback for different Pydantic versions
            error = ValidationError.from_exception_data(
                "TestModel",
                [{"loc": ("field",), "msg": "field required", "type": "value_error"}]
            )
        
        response = self.middleware._create_validation_error_response(error)
        
        assert response.status_code == 422
        content = json.loads(response.body.decode())
        assert "message" in content
        assert "errors" in content


class TestSecureCommunicationIntegration:
    """Integration tests for secure communication features"""
    
    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)
    
    def test_health_endpoint_security(self):
        """Test health endpoint with security features."""
        response = self.client.get("/health")
        
        assert response.status_code == 200
        assert "x-frame-options" in response.headers
        assert "x-content-type-options" in response.headers
    
    def test_security_info_endpoint(self):
        """Test security info endpoint."""
        response = self.client.get("/security-info")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "https_enforced" in data
        assert "security_headers_enabled" in data
        assert "hsts_enabled" in data
        assert "cors_origins" in data
        assert "rate_limiting_enabled" in data
        assert "request_validation_enabled" in data
        assert "response_validation_enabled" in data
    
    def test_api_endpoints_with_security(self):
        """Test API endpoints with security features."""
        # Test root endpoint
        response = self.client.get("/")
        assert response.status_code == 200
        assert "x-frame-options" in response.headers
        
        # Test auth endpoint (should have security headers)
        response = self.client.get("/auth/")
        assert "x-frame-options" in response.headers
        
        # Test chat endpoint (should have security headers)
        response = self.client.get("/chat/")
        assert "x-frame-options" in response.headers
        
        # Test health endpoint (should have security headers)
        response = self.client.get("/health/")
        assert "x-frame-options" in response.headers


if __name__ == "__main__":
    pytest.main([__file__]) 
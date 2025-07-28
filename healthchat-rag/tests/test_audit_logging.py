"""
Test suite for audit logging functionality.

This module tests the AuditLogger class and related middleware functionality.
"""

import pytest
import logging
from unittest.mock import Mock, patch
from datetime import datetime
from app.utils.audit_logging import AuditLogger
from app.utils.api_audit_middleware import APIAuditMiddleware
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

class TestAuditLogger:
    """Test cases for AuditLogger class."""
    
    def test_log_auth_event_success(self):
        """Test successful authentication event logging."""
        with patch('app.utils.audit_logging.logger') as mock_logger:
            AuditLogger.log_auth_event(
                event_type="login",
                user_id=1,
                user_email="test@example.com",
                ip_address="127.0.0.1",
                success=True
            )
            
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args
            assert "Authentication event: login" in call_args[0][0]
            
            # Check extra data
            extra_data = call_args[1]['extra']
            assert extra_data['event_type'] == 'authentication'
            assert extra_data['auth_action'] == 'login'
            assert extra_data['user_id'] == 1
            assert extra_data['user_email'] == 'test@example.com'
            assert extra_data['ip_address'] == '127.0.0.1'
            assert extra_data['success'] is True
    
    def test_log_auth_event_failure(self):
        """Test failed authentication event logging."""
        with patch('app.utils.audit_logging.logger') as mock_logger:
            AuditLogger.log_auth_event(
                event_type="login",
                user_email="test@example.com",
                success=False,
                details={"reason": "Invalid credentials"}
            )
            
            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args
            assert "Authentication event failed: login" in call_args[0][0]
            
            # Check extra data
            extra_data = call_args[1]['extra']
            assert extra_data['success'] is False
            assert extra_data['details']['reason'] == 'Invalid credentials'
    
    def test_log_health_data_access(self):
        """Test health data access logging."""
        with patch('app.utils.audit_logging.logger') as mock_logger:
            AuditLogger.log_health_data_access(
                action="read",
                user_id=1,
                user_email="test@example.com",
                data_type="blood_pressure",
                data_id=123,
                ip_address="127.0.0.1",
                success=True
            )
            
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args
            assert "Health data read: blood_pressure" in call_args[0][0]
            
            # Check extra data
            extra_data = call_args[1]['extra']
            assert extra_data['event_type'] == 'health_data_access'
            assert extra_data['action'] == 'read'
            assert extra_data['data_type'] == 'blood_pressure'
            assert extra_data['data_id'] == 123
    
    def test_log_api_call(self):
        """Test API call logging."""
        with patch('app.utils.audit_logging.logger') as mock_logger:
            AuditLogger.log_api_call(
                method="POST",
                path="/api/health",
                user_id=1,
                user_email="test@example.com",
                status_code=200,
                response_time=0.5,
                success=True
            )
            
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args
            assert "API call: POST /api/health" in call_args[0][0]
            
            # Check extra data
            extra_data = call_args[1]['extra']
            assert extra_data['event_type'] == 'api_call'
            assert extra_data['method'] == 'POST'
            assert extra_data['path'] == '/api/health'
            assert extra_data['status_code'] == 200
            assert extra_data['response_time'] == 0.5
    
    def test_log_with_request_object(self):
        """Test logging with FastAPI Request object."""
        mock_request = Mock()
        mock_request.client.host = "192.168.1.1"
        mock_request.headers.get.return_value = "TestUserAgent"
        
        with patch('app.utils.audit_logging.logger') as mock_logger:
            AuditLogger.log_auth_event(
                event_type="login",
                user_id=1,
                user_email="test@example.com",
                request=mock_request
            )
            
            mock_logger.info.assert_called_once()
            extra_data = mock_logger.info.call_args[1]['extra']
            assert extra_data['ip_address'] == "192.168.1.1"
            assert extra_data['user_agent'] == "TestUserAgent"

class TestAPIAuditMiddleware:
    """Test cases for APIAuditMiddleware."""
    
    @pytest.fixture
    def app(self):
        """Create a test FastAPI app."""
        app = FastAPI()
        
        @app.get("/test")
        def test_endpoint():
            return {"message": "test"}
        
        @app.get("/error")
        def error_endpoint():
            raise ValueError("Test error")
        
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        return TestClient(app)
    
    def test_middleware_logs_successful_request(self, app, client):
        """Test that middleware logs successful API calls."""
        with patch('app.utils.audit_logging.AuditLogger.log_api_call') as mock_log:
            app.add_middleware(APIAuditMiddleware)
            
            response = client.get("/test")
            assert response.status_code == 200
            
            # Verify logging was called
            mock_log.assert_called_once()
            call_args = mock_log.call_args[1]
            assert call_args['method'] == 'GET'
            assert call_args['path'] == '/test'
            assert call_args['success'] is True
    
    def test_middleware_logs_failed_request(self, app, client):
        """Test that middleware logs failed API calls."""
        with patch('app.utils.audit_logging.AuditLogger.log_api_call') as mock_log:
            app.add_middleware(APIAuditMiddleware)
            
            with pytest.raises(ValueError):
                client.get("/error")
            
            # Verify logging was called
            mock_log.assert_called_once()
            call_args = mock_log.call_args[1]
            assert call_args['method'] == 'GET'
            assert call_args['path'] == '/error'
            assert call_args['success'] is False
    
    def test_middleware_captures_response_time(self, app, client):
        """Test that middleware captures response time."""
        with patch('app.utils.audit_logging.AuditLogger.log_api_call') as mock_log:
            app.add_middleware(APIAuditMiddleware)
            
            response = client.get("/test")
            
            # Verify response time was captured
            call_args = mock_log.call_args[1]
            assert 'response_time' in call_args
            assert isinstance(call_args['response_time'], float)
            assert call_args['response_time'] > 0

class TestAuditLoggingIntegration:
    """Integration tests for audit logging."""
    
    def test_correlation_id_integration(self):
        """Test that correlation ID is included in audit logs."""
        with patch('app.utils.audit_logging.get_correlation_id') as mock_get_correlation:
            mock_get_correlation.return_value = "test-correlation-id"
            
            with patch('app.utils.audit_logging.logger') as mock_logger:
                AuditLogger.log_auth_event(
                    event_type="login",
                    user_id=1,
                    user_email="test@example.com"
                )
                
                extra_data = mock_logger.info.call_args[1]['extra']
                assert extra_data['correlation_id'] == "test-correlation-id"
    
    def test_timestamp_format(self):
        """Test that timestamps are in ISO format."""
        with patch('app.utils.audit_logging.logger') as mock_logger:
            AuditLogger.log_auth_event(
                event_type="login",
                user_id=1,
                user_email="test@example.com"
            )
            
            extra_data = mock_logger.info.call_args[1]['extra']
            timestamp = extra_data['timestamp']
            
            # Verify it's a valid ISO timestamp
            datetime.fromisoformat(timestamp) 
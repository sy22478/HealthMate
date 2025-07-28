"""
Tests for External API Communication Framework

This module tests:
- External API client functionality
- OAuth2 authentication
- Rate limiting and retry logic
- Webhook management system
- Webhook delivery and failure handling
"""

import pytest
import asyncio
import json
import time
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from app.services.external_api_client import (
    ExternalAPIClient, APIConfig, OAuth2Config, AuthenticationType,
    HTTPMethod, RateLimiter, RetryHandler, OAuth2Handler, WebhookManager,
    WebhookEvent, APIResponse
)
from app.exceptions.external_api_exceptions import (
    ExternalAPIError, APIConnectionError, APIResponseError,
    APIRateLimitError, APIAuthenticationError
)


class TestRateLimiter:
    """Test rate limiting functionality."""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_acquire(self):
        """Test rate limiter acquire functionality."""
        limiter = RateLimiter(requests_per_minute=2, requests_per_hour=5)
        
        # First two requests should succeed
        assert await limiter.acquire() is True
        assert await limiter.acquire() is True
        
        # Third request should fail (minute limit)
        assert await limiter.acquire() is False
    
    @pytest.mark.asyncio
    async def test_rate_limiter_wait_for_permission(self):
        """Test rate limiter wait functionality."""
        limiter = RateLimiter(requests_per_minute=1, requests_per_hour=10)
        
        # First request should succeed immediately
        start_time = time.time()
        await limiter.wait_for_permission()
        elapsed = time.time() - start_time
        
        assert elapsed < 0.1  # Should be immediate
        
        # Second request should wait
        start_time = time.time()
        await limiter.wait_for_permission()
        elapsed = time.time() - start_time
        
        assert elapsed >= 1.0  # Should wait at least 1 second


class TestRetryHandler:
    """Test retry logic functionality."""
    
    @pytest.mark.asyncio
    async def test_retry_handler_success_on_first_attempt(self):
        """Test retry handler with immediate success."""
        handler = RetryHandler(max_retries=3, base_delay=0.1)
        
        async def successful_operation():
            return "success"
        
        result = await handler.execute_with_retry(successful_operation)
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_retry_handler_success_after_retries(self):
        """Test retry handler with success after retries."""
        handler = RetryHandler(max_retries=3, base_delay=0.1)
        attempt_count = 0
        
        async def failing_then_successful_operation():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise APIConnectionError("Connection failed")
            return "success"
        
        result = await handler.execute_with_retry(failing_then_successful_operation)
        assert result == "success"
        assert attempt_count == 3
    
    @pytest.mark.asyncio
    async def test_retry_handler_max_retries_exceeded(self):
        """Test retry handler with max retries exceeded."""
        handler = RetryHandler(max_retries=2, base_delay=0.1)
        
        async def always_failing_operation():
            raise APIConnectionError("Always fails")
        
        with pytest.raises(APIConnectionError):
            await handler.execute_with_retry(always_failing_operation)
    
    @pytest.mark.asyncio
    async def test_retry_handler_rate_limit_handling(self):
        """Test retry handler with rate limit errors."""
        handler = RetryHandler(max_retries=2, base_delay=0.1)
        attempt_count = 0
        
        async def rate_limited_operation():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise APIRateLimitError("Rate limited")
            return "success"
        
        result = await handler.execute_with_retry(rate_limited_operation)
        assert result == "success"
        assert attempt_count == 3


class TestOAuth2Handler:
    """Test OAuth2 authentication functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.api_config = APIConfig(
            base_url="https://api.example.com",
            client_id="test_client_id",
            client_secret="test_client_secret",
            auth_type=AuthenticationType.OAUTH2
        )
        
        self.oauth2_config = OAuth2Config(
            authorization_url="https://auth.example.com/authorize",
            token_url="https://auth.example.com/token",
            scope="read write",
            redirect_uri="https://app.example.com/callback"
        )
        
        self.handler = OAuth2Handler(self.oauth2_config, self.api_config)
    
    def test_get_authorization_url(self):
        """Test OAuth2 authorization URL generation."""
        url = self.handler.get_authorization_url()
        
        assert "https://auth.example.com/authorize" in url
        assert "client_id=test_client_id" in url
        assert "response_type=code" in url
        assert "redirect_uri=https%3A//app.example.com/callback" in url
        assert "scope=read+write" in url
    
    def test_get_authorization_url_with_state(self):
        """Test OAuth2 authorization URL with custom state."""
        url = self.handler.get_authorization_url(state="custom_state")
        
        assert "state=custom_state" in url
    
    @pytest.mark.asyncio
    async def test_exchange_code_for_token(self):
        """Test OAuth2 code exchange."""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_in": 3600
        })
        
        mock_session = Mock()
        mock_session.post = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            result = await self.handler.exchange_code_for_token("test_code")
            
            assert result["access_token"] == "test_access_token"
            assert result["refresh_token"] == "test_refresh_token"
            assert self.handler.access_token == "test_access_token"
            assert self.handler.refresh_token == "test_refresh_token"
    
    @pytest.mark.asyncio
    async def test_exchange_code_for_token_failure(self):
        """Test OAuth2 code exchange failure."""
        mock_response = Mock()
        mock_response.status = 400
        
        mock_session = Mock()
        mock_session.post = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            with pytest.raises(APIAuthenticationError):
                await self.handler.exchange_code_for_token("test_code")
    
    def test_get_auth_headers_no_token(self):
        """Test getting auth headers without token."""
        with pytest.raises(APIAuthenticationError):
            self.handler.get_auth_headers()
    
    def test_get_auth_headers_with_token(self):
        """Test getting auth headers with token."""
        self.handler.access_token = "test_token"
        self.handler.token_expires_at = datetime.now() + timedelta(hours=1)
        
        headers = self.handler.get_auth_headers()
        assert headers["Authorization"] == "Bearer test_token"
    
    def test_get_auth_headers_expired_token(self):
        """Test getting auth headers with expired token."""
        self.handler.access_token = "test_token"
        self.handler.token_expires_at = datetime.now() - timedelta(hours=1)
        
        with pytest.raises(APIAuthenticationError):
            self.handler.get_auth_headers()


class TestWebhookManager:
    """Test webhook management functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.manager = WebhookManager(secret="test_secret")
    
    def test_verify_signature_valid(self):
        """Test webhook signature verification with valid signature."""
        payload = '{"test": "data"}'
        signature = "sha256=valid_signature"
        
        # Mock the signature generation
        with patch('hmac.new') as mock_hmac:
            mock_hmac.return_value.hexdigest.return_value = "valid_signature"
            
            result = self.manager.verify_signature(payload, signature)
            assert result is True
    
    def test_verify_signature_invalid(self):
        """Test webhook signature verification with invalid signature."""
        payload = '{"test": "data"}'
        signature = "sha256=invalid_signature"
        
        # Mock the signature generation
        with patch('hmac.new') as mock_hmac:
            mock_hmac.return_value.hexdigest.return_value = "valid_signature"
            
            result = self.manager.verify_signature(payload, signature)
            assert result is False
    
    def test_verify_signature_no_secret(self):
        """Test webhook signature verification without secret."""
        manager = WebhookManager(secret=None)
        payload = '{"test": "data"}'
        signature = "sha256=test"
        
        result = manager.verify_signature(payload, signature)
        assert result is True  # Should skip verification
    
    def test_parse_webhook_event(self):
        """Test webhook event parsing."""
        payload = json.dumps({
            "event_type": "test.event",
            "event_id": "test_id",
            "timestamp": "2024-01-01T00:00:00Z",
            "data": {"key": "value"},
            "source": "test_source"
        })
        
        headers = {"X-Webhook-Signature": "sha256=test"}
        
        event = self.manager.parse_webhook_event(payload, headers)
        
        assert event.event_type == "test.event"
        assert event.event_id == "test_id"
        assert event.source == "test_source"
        assert event.signature == "sha256=test"
    
    @pytest.mark.asyncio
    async def test_process_webhook_event_health_data(self):
        """Test processing health data webhook event."""
        event = WebhookEvent(
            event_type="health_data_updated",
            event_id="test_id",
            timestamp=datetime.now(),
            data={"user_id": 1, "metric": "heart_rate"},
            source="test_source"
        )
        
        result = await self.manager.process_webhook_event(event)
        
        assert result["status"] == "processed"
        assert result["type"] == "health_data"
    
    @pytest.mark.asyncio
    async def test_process_webhook_event_unknown(self):
        """Test processing unknown webhook event."""
        event = WebhookEvent(
            event_type="unknown.event",
            event_id="test_id",
            timestamp=datetime.now(),
            data={},
            source="test_source"
        )
        
        result = await self.manager.process_webhook_event(event)
        
        assert result["status"] == "ignored"
        assert result["event_type"] == "unknown.event"


class TestExternalAPIClient:
    """Test external API client functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.config = APIConfig(
            base_url="https://api.example.com",
            api_key="test_api_key",
            auth_type=AuthenticationType.API_KEY,
            timeout_seconds=30,
            max_retries=3,
            rate_limit_per_minute=60
        )
        
        self.client = ExternalAPIClient(self.config)
    
    @pytest.mark.asyncio
    async def test_request_success(self):
        """Test successful API request."""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.headers = {"X-Request-ID": "test_id"}
        mock_response.json = AsyncMock(return_value={"success": True})
        
        mock_session = Mock()
        mock_session.request = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            response = await self.client.request(
                HTTPMethod.GET,
                "/test",
                params={"key": "value"}
            )
            
            assert response.status_code == 200
            assert response.data["success"] is True
            assert response.request_id == "test_id"
    
    @pytest.mark.asyncio
    async def test_request_authentication_error(self):
        """Test API request with authentication error."""
        mock_response = Mock()
        mock_response.status = 401
        mock_response.text = AsyncMock(return_value="Unauthorized")
        
        mock_session = Mock()
        mock_session.request = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            with pytest.raises(APIAuthenticationError):
                await self.client.request(HTTPMethod.GET, "/test")
    
    @pytest.mark.asyncio
    async def test_request_rate_limit_error(self):
        """Test API request with rate limit error."""
        mock_response = Mock()
        mock_response.status = 429
        mock_response.headers = {"Retry-After": "60"}
        mock_response.text = AsyncMock(return_value="Rate limited")
        
        mock_session = Mock()
        mock_session.request = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            with pytest.raises(APIRateLimitError):
                await self.client.request(HTTPMethod.GET, "/test")
    
    @pytest.mark.asyncio
    async def test_get_request(self):
        """Test GET request convenience method."""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.headers = {}
        mock_response.json = AsyncMock(return_value={"data": "test"})
        
        mock_session = Mock()
        mock_session.request = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            response = await self.client.get("/test", params={"id": 1})
            
            assert response.status_code == 200
            assert response.data["data"] == "test"
    
    @pytest.mark.asyncio
    async def test_post_request(self):
        """Test POST request convenience method."""
        mock_response = Mock()
        mock_response.status = 201
        mock_response.headers = {}
        mock_response.json = AsyncMock(return_value={"created": True})
        
        mock_session = Mock()
        mock_session.request = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            response = await self.client.post("/test", data={"name": "test"})
            
            assert response.status_code == 201
            assert response.data["created"] is True
    
    @pytest.mark.asyncio
    async def test_process_webhook(self):
        """Test webhook processing."""
        payload = json.dumps({
            "event_type": "test.event",
            "event_id": "test_id",
            "timestamp": "2024-01-01T00:00:00Z",
            "data": {"key": "value"}
        })
        
        headers = {"X-Webhook-Signature": "sha256=test"}
        
        # Mock signature verification
        with patch.object(self.client.webhook_manager, 'verify_signature', return_value=True):
            with patch.object(self.client.webhook_manager, 'parse_webhook_event') as mock_parse:
                with patch.object(self.client.webhook_manager, 'process_webhook_event') as mock_process:
                    mock_event = Mock()
                    mock_parse.return_value = mock_event
                    mock_process.return_value = {"status": "processed"}
                    
                    result = await self.client.process_webhook(payload, headers)
                    
                    assert result["status"] == "processed"
                    mock_parse.assert_called_once()
                    mock_process.assert_called_once_with(mock_event)
    
    def test_get_oauth2_authorization_url_not_configured(self):
        """Test OAuth2 authorization URL without OAuth2 configuration."""
        with pytest.raises(APIAuthenticationError):
            self.client.get_oauth2_authorization_url()
    
    def test_get_oauth2_authorization_url_configured(self):
        """Test OAuth2 authorization URL with OAuth2 configuration."""
        oauth2_config = OAuth2Config(
            authorization_url="https://auth.example.com/authorize",
            token_url="https://auth.example.com/token",
            redirect_uri="https://app.example.com/callback"
        )
        
        oauth2_client = ExternalAPIClient(self.config, oauth2_config)
        
        url = oauth2_client.get_oauth2_authorization_url()
        assert "https://auth.example.com/authorize" in url


class TestWebhookIntegration:
    """Test webhook integration functionality."""
    
    @pytest.mark.asyncio
    async def test_webhook_delivery_flow(self):
        """Test complete webhook delivery flow."""
        # This would test the integration between webhook management
        # and external API client for webhook delivery
        
        # Mock the webhook delivery process
        with patch('app.routers.webhook_management._deliver_webhook') as mock_deliver:
            mock_deliver.return_value = True
            
            # Test webhook event dispatch
            from app.routers.webhook_management import dispatch_webhook_event
            
            await dispatch_webhook_event(
                "health_metric.added",
                {"user_id": 1, "metric": "heart_rate", "value": 75},
                1
            )
            
            # Verify webhook delivery was attempted
            # (This would require setting up test webhook registrations)
            pass


# Integration tests
class TestExternalAPICommunicationIntegration:
    """Integration tests for external API communication."""
    
    @pytest.mark.asyncio
    async def test_fitbit_integration_example(self):
        """Test Fitbit API integration example."""
        config = APIConfig(
            base_url="https://api.fitbit.com/1",
            auth_type=AuthenticationType.OAUTH2,
            rate_limit_per_minute=150,
            timeout_seconds=30
        )
        
        oauth2_config = OAuth2Config(
            authorization_url="https://www.fitbit.com/oauth2/authorize",
            token_url="https://api.fitbit.com/oauth2/token",
            scope="activity heartrate sleep",
            redirect_uri="https://healthmate.com/oauth/callback"
        )
        
        client = ExternalAPIClient(config, oauth2_config)
        
        # Test OAuth2 flow
        auth_url = client.get_oauth2_authorization_url()
        assert "fitbit.com/oauth2/authorize" in auth_url
        assert "activity+heartrate+sleep" in auth_url
    
    @pytest.mark.asyncio
    async def test_webhook_registration_flow(self):
        """Test webhook registration and delivery flow."""
        # This would test the complete webhook registration and delivery process
        # including database operations and actual HTTP delivery
        
        # Mock the webhook delivery process
        with patch('app.routers.webhook_management._attempt_delivery') as mock_delivery:
            mock_delivery.return_value = True
            
            # Test webhook registration
            # Test webhook delivery
            # Test webhook failure handling
            # Test webhook retry mechanism
            pass


if __name__ == "__main__":
    pytest.main([__file__]) 
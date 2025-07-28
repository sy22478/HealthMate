"""
Tests for Rate Limiting Functionality
"""
import pytest
import time
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from app.utils.rate_limiting import RateLimiter, RateLimitingMiddleware

class TestRateLimiter:
    """Test rate limiting functionality"""
    
    def test_client_identifier_generation(self):
        """Test client identifier generation"""
        rate_limiter = RateLimiter()
        
        # Mock request
        request = Mock()
        request.client.host = "192.168.1.1"
        request.headers = {"User-Agent": "Test Browser"}
        
        identifier = rate_limiter._get_client_identifier(request)
        assert "192.168.1.1" in identifier
        assert "Test Browser" in identifier
    
    def test_endpoint_key_generation(self):
        """Test endpoint key generation"""
        rate_limiter = RateLimiter()
        
        # Test auth endpoints
        request = Mock()
        request.url.path = "/auth/login"
        request.method = "POST"
        
        key = rate_limiter._get_endpoint_key(request)
        assert key == "auth:login"
        
        # Test chat endpoints
        request.url.path = "/chat/send_message"
        key = rate_limiter._get_endpoint_key(request)
        assert key == "chat:send_message"
        
        # Test health endpoints
        request.url.path = "/health/status"
        key = rate_limiter._get_endpoint_key(request)
        assert key == "health:default"
        
        # Test general API endpoints
        request.url.path = "/api/users"
        key = rate_limiter._get_endpoint_key(request)
        assert key == "api:default"
    
    def test_rate_limit_retrieval(self):
        """Test rate limit retrieval for different endpoints"""
        rate_limiter = RateLimiter()
        
        # Test specific limits
        assert rate_limiter._get_rate_limit("auth:login") == 5
        assert rate_limiter._get_rate_limit("auth:register") == 3
        assert rate_limiter._get_rate_limit("chat:send_message") == 30
        assert rate_limiter._get_rate_limit("health:default") == 120
        
        # Test default limits
        assert rate_limiter._get_rate_limit("auth:default") == 10
        assert rate_limiter._get_rate_limit("chat:default") == 60
        assert rate_limiter._get_rate_limit("api:default") == 100
        
        # Test fallback
        assert rate_limiter._get_rate_limit("unknown:endpoint") == 60
    
    def test_memory_rate_limiting(self):
        """Test in-memory rate limiting"""
        rate_limiter = RateLimiter()
        
        # Mock request
        request = Mock()
        request.client.host = "192.168.1.1"
        request.headers = {"User-Agent": "Test Browser"}
        request.url.path = "/auth/login"
        request.method = "POST"
        
        # Test within limit
        for i in range(5):
            is_allowed, info = rate_limiter.check_rate_limit(request)
            assert is_allowed == True
            assert info["limit"] == 5
            assert info["remaining"] == 4 - i
            assert info["current"] == i + 1
        
        # Test exceeding limit
        is_allowed, info = rate_limiter.check_rate_limit(request)
        assert is_allowed == False
        assert info["limit"] == 5
        assert info["remaining"] == 0
        assert info["current"] == 6
    
    def test_rate_limit_headers(self):
        """Test rate limit header generation"""
        rate_limiter = RateLimiter()
        
        rate_limit_info = {
            "limit": 10,
            "remaining": 5,
            "reset": 1234567890,
            "current": 5
        }
        
        headers = rate_limiter.get_rate_limit_headers(rate_limit_info)
        
        assert headers["X-RateLimit-Limit"] == "10"
        assert headers["X-RateLimit-Remaining"] == "5"
        assert headers["X-RateLimit-Reset"] == "1234567890"
        assert headers["X-RateLimit-Current"] == "5"
    
    def test_time_window_rotation(self):
        """Test that rate limits reset after time window"""
        rate_limiter = RateLimiter()
        
        # Mock request
        request = Mock()
        request.client.host = "192.168.1.1"
        request.headers = {"User-Agent": "Test Browser"}
        request.url.path = "/auth/login"
        request.method = "POST"
        
        # Use up the limit
        for i in range(5):
            rate_limiter.check_rate_limit(request)
        
        # Should be blocked
        is_allowed, _ = rate_limiter.check_rate_limit(request)
        assert is_allowed == False
        
        # Clear memory store and advance time
        rate_limiter.memory_store.clear()
        
        # Should be allowed again (fresh start)
        is_allowed, info = rate_limiter.check_rate_limit(request)
        assert is_allowed == True
        assert info["current"] == 1

class TestRateLimitingMiddleware:
    """Test rate limiting middleware"""
    
    def test_middleware_initialization(self):
        """Test middleware initialization"""
        app = Mock()
        rate_limiter = RateLimiter()
        middleware = RateLimitingMiddleware(app, rate_limiter)
        
        assert middleware.rate_limiter == rate_limiter
        assert "/docs" in middleware.exclude_paths
        assert "/health" in middleware.exclude_paths
    
    @pytest.mark.asyncio
    async def test_excluded_paths_bypass_rate_limiting(self):
        """Test that excluded paths bypass rate limiting"""
        app = Mock()
        rate_limiter = RateLimiter()
        middleware = RateLimitingMiddleware(app, rate_limiter)
        
        # Mock request to excluded path
        request = Mock()
        request.url.path = "/docs"
        
        # Mock call_next
        call_next = AsyncMock()
        call_next.return_value = JSONResponse(content={"test": "data"})
        
        # Should bypass rate limiting
        response = await middleware.dispatch(request, call_next)
        call_next.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_rate_limit_exceeded_response(self):
        """Test response when rate limit is exceeded"""
        app = Mock()
        rate_limiter = RateLimiter()
        middleware = RateLimitingMiddleware(app, rate_limiter)
        
        # Mock request
        request = Mock()
        request.client.host = "192.168.1.1"
        request.headers = {"User-Agent": "Test Browser"}
        request.url.path = "/auth/login"
        request.method = "POST"
        
        # Mock rate limiter to return exceeded
        with patch.object(rate_limiter, 'check_rate_limit') as mock_check:
            mock_check.return_value = (False, {
                "limit": 5,
                "remaining": 0,
                "reset": int(time.time()) + 60,
                "current": 6
            })
            
            call_next = AsyncMock()
            response = await middleware.dispatch(request, call_next)
            
            # Should return 429 response
            assert response.status_code == 429
            assert "Rate limit exceeded" in response.body.decode()
            
            # Should include rate limit headers
            assert "X-RateLimit-Limit" in response.headers
            assert "X-RateLimit-Remaining" in response.headers
    
    @pytest.mark.asyncio
    async def test_successful_request_with_headers(self):
        """Test successful request includes rate limit headers"""
        app = Mock()
        rate_limiter = RateLimiter()
        middleware = RateLimitingMiddleware(app, rate_limiter)
        
        # Mock request
        request = Mock()
        request.client.host = "192.168.1.1"
        request.headers = {"User-Agent": "Test Browser"}
        request.url.path = "/auth/login"
        request.method = "POST"
        
        # Mock rate limiter to return allowed
        with patch.object(rate_limiter, 'check_rate_limit') as mock_check:
            mock_check.return_value = (True, {
                "limit": 5,
                "remaining": 4,
                "reset": int(time.time()) + 60,
                "current": 1
            })
            
            # Mock response
            mock_response = JSONResponse(content={"test": "data"})
            call_next = AsyncMock()
            call_next.return_value = mock_response
            
            response = await middleware.dispatch(request, call_next)
            
            # Should include rate limit headers
            assert "X-RateLimit-Limit" in response.headers
            assert "X-RateLimit-Remaining" in response.headers
            assert "X-RateLimit-Reset" in response.headers
            assert "X-RateLimit-Current" in response.headers
    
    @pytest.mark.asyncio
    async def test_middleware_error_handling(self):
        """Test middleware handles errors gracefully"""
        app = Mock()
        rate_limiter = RateLimiter()
        middleware = RateLimitingMiddleware(app, rate_limiter)
        
        # Mock request
        request = Mock()
        request.client.host = "192.168.1.1"
        request.headers = {"User-Agent": "Test Browser"}
        request.url.path = "/auth/login"
        request.method = "POST"
        
        # Mock rate limiter to raise exception
        with patch.object(rate_limiter, 'check_rate_limit') as mock_check:
            mock_check.side_effect = Exception("Rate limiting error")
            
            call_next = AsyncMock()
            call_next.return_value = JSONResponse(content={"test": "data"})
            
            # Should continue without rate limiting
            response = await middleware.dispatch(request, call_next)
            call_next.assert_called_once()

class TestRateLimitingIntegration:
    """Test rate limiting integration with different endpoint types"""
    
    def test_auth_endpoint_limits(self):
        """Test rate limits for authentication endpoints"""
        rate_limiter = RateLimiter()
        
        # Test login endpoint
        request = Mock()
        request.client.host = "192.168.1.1"
        request.headers = {"User-Agent": "Test Browser"}
        request.url.path = "/auth/login"
        request.method = "POST"
        
        # Should allow 5 requests
        for i in range(5):
            is_allowed, info = rate_limiter.check_rate_limit(request)
            assert is_allowed == True
            assert info["limit"] == 5
        
        # 6th request should be blocked
        is_allowed, info = rate_limiter.check_rate_limit(request)
        assert is_allowed == False
        assert info["limit"] == 5
    
    def test_chat_endpoint_limits(self):
        """Test rate limits for chat endpoints"""
        rate_limiter = RateLimiter()
        
        # Test send message endpoint
        request = Mock()
        request.client.host = "192.168.1.1"
        request.headers = {"User-Agent": "Test Browser"}
        request.url.path = "/chat/send_message"
        request.method = "POST"
        
        # Should allow 30 requests
        for i in range(30):
            is_allowed, info = rate_limiter.check_rate_limit(request)
            assert is_allowed == True
            assert info["limit"] == 30
        
        # 31st request should be blocked
        is_allowed, info = rate_limiter.check_rate_limit(request)
        assert is_allowed == False
        assert info["limit"] == 30
    
    def test_different_clients_separate_limits(self):
        """Test that different clients have separate rate limits"""
        rate_limiter = RateLimiter()
        
        # Client 1
        request1 = Mock()
        request1.client.host = "192.168.1.1"
        request1.headers = {"User-Agent": "Browser1"}
        request1.url.path = "/auth/login"
        request1.method = "POST"
        
        # Client 2
        request2 = Mock()
        request2.client.host = "192.168.1.2"
        request2.headers = {"User-Agent": "Browser2"}
        request2.url.path = "/auth/login"
        request2.method = "POST"
        
        # Use up limit for client 1
        for i in range(5):
            rate_limiter.check_rate_limit(request1)
        
        # Client 1 should be blocked
        is_allowed, _ = rate_limiter.check_rate_limit(request1)
        assert is_allowed == False
        
        # Client 2 should still be allowed
        is_allowed, info = rate_limiter.check_rate_limit(request2)
        assert is_allowed == True
        assert info["current"] == 1 
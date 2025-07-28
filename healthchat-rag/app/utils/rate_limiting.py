"""
Rate Limiting Utilities
Provides comprehensive rate limiting with per-endpoint support
"""
import time
import logging
from typing import Dict, Optional, Tuple, Any
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import redis
from app.config import settings

logger = logging.getLogger(__name__)

class RateLimiter:
    """Advanced rate limiting with Redis support"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None, disabled: bool = False):
        self.redis_client = redis_client
        self.memory_store = {}  # Fallback for when Redis is not available
        self.disabled = disabled  # For testing purposes
        
        # Default rate limits (requests per minute)
        self.default_limits = {
            "auth": {
                "login": 5,      # 5 login attempts per minute
                "register": 3,   # 3 registration attempts per minute
                "password_reset": 2,  # 2 password reset attempts per minute
                "default": 10    # 10 requests per minute for other auth endpoints
            },
            "chat": {
                "send_message": 30,  # 30 messages per minute
                "default": 60        # 60 requests per minute for other chat endpoints
            },
            "health": {
                "default": 120       # 120 requests per minute for health endpoints
            },
            "api": {
                "default": 100       # 100 requests per minute for general API endpoints
            }
        }
    
    def _get_client_identifier(self, request: Request) -> str:
        """Get unique identifier for the client"""
        # Try to get real IP from headers (for proxy/load balancer setups)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"
        
        # Add user agent for additional uniqueness
        user_agent = request.headers.get("User-Agent", "unknown")
        return f"{client_ip}:{user_agent[:50]}"
    
    def _get_endpoint_key(self, request: Request) -> str:
        """Get rate limit key for the endpoint"""
        path = request.url.path
        method = request.method
        
        # Determine endpoint category
        if path.startswith("/auth"):
            category = "auth"
            if "login" in path:
                endpoint = "login"
            elif "register" in path:
                endpoint = "register"
            elif "password" in path or "reset" in path:
                endpoint = "password_reset"
            else:
                endpoint = "default"
        elif path.startswith("/chat"):
            category = "chat"
            if "send" in path or "message" in path:
                endpoint = "send_message"
            else:
                endpoint = "default"
        elif path.startswith("/health"):
            category = "health"
            endpoint = "default"
        else:
            category = "api"
            endpoint = "default"
        
        return f"{category}:{endpoint}"
    
    def _get_rate_limit(self, endpoint_key: str) -> int:
        """Get rate limit for the endpoint"""
        category, endpoint = endpoint_key.split(":", 1)
        
        if category in self.default_limits:
            if endpoint in self.default_limits[category]:
                return self.default_limits[category][endpoint]
            elif "default" in self.default_limits[category]:
                return self.default_limits[category]["default"]
        
        return 60  # Default fallback
    
    def _get_current_window(self) -> int:
        """Get current time window (1-minute intervals)"""
        return int(time.time() // 60)
    
    def _get_redis_key(self, client_id: str, endpoint_key: str, window: int) -> str:
        """Generate Redis key for rate limiting"""
        return f"rate_limit:{client_id}:{endpoint_key}:{window}"
    
    def check_rate_limit(self, request: Request) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if request is within rate limits
        
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        # Skip rate limiting if disabled (for testing)
        if self.disabled:
            return True, {
                "limit": 1000,
                "remaining": 999,
                "reset": int(time.time()) + 60,
                "current": 1
            }
        
        client_id = self._get_client_identifier(request)
        endpoint_key = self._get_endpoint_key(request)
        window = self._get_current_window()
        rate_limit = self._get_rate_limit(endpoint_key)
        
        if self.redis_client:
            return self._check_redis_rate_limit(client_id, endpoint_key, window, rate_limit)
        else:
            return self._check_memory_rate_limit(client_id, endpoint_key, window, rate_limit)
    
    def _check_redis_rate_limit(self, client_id: str, endpoint_key: str, 
                               window: int, rate_limit: int) -> Tuple[bool, Dict[str, Any]]:
        """Check rate limit using Redis"""
        try:
            redis_key = self._get_redis_key(client_id, endpoint_key, window)
            
            # Use Redis pipeline for atomic operations
            pipe = self.redis_client.pipeline()
            pipe.incr(redis_key)
            pipe.expire(redis_key, 60)  # Expire after 1 minute
            results = pipe.execute()
            
            current_count = results[0]
            
            is_allowed = current_count <= rate_limit
            remaining = max(0, rate_limit - current_count)
            reset_time = (window + 1) * 60  # Next window start time
            
            return is_allowed, {
                "limit": rate_limit,
                "remaining": remaining,
                "reset": reset_time,
                "current": current_count
            }
            
        except Exception as e:
            logger.error(f"Redis rate limiting error: {e}")
            # Fallback to memory-based rate limiting
            return self._check_memory_rate_limit(client_id, endpoint_key, window, rate_limit)
    
    def _check_memory_rate_limit(self, client_id: str, endpoint_key: str, 
                                window: int, rate_limit: int) -> Tuple[bool, Dict[str, Any]]:
        """Check rate limit using in-memory storage"""
        key = f"{client_id}:{endpoint_key}:{window}"
        
        # Clean up old entries
        current_time = time.time()
        self.memory_store = {
            k: v for k, v in self.memory_store.items() 
            if current_time - v["timestamp"] < 60
        }
        
        if key not in self.memory_store:
            self.memory_store[key] = {"count": 0, "timestamp": current_time}
        
        self.memory_store[key]["count"] += 1
        current_count = self.memory_store[key]["count"]
        
        is_allowed = current_count <= rate_limit
        remaining = max(0, rate_limit - current_count)
        reset_time = (window + 1) * 60
        
        return is_allowed, {
            "limit": rate_limit,
            "remaining": remaining,
            "reset": reset_time,
            "current": current_count
        }
    
    def get_rate_limit_headers(self, rate_limit_info: Dict[str, Any]) -> Dict[str, str]:
        """Generate rate limit headers for response"""
        return {
            "X-RateLimit-Limit": str(rate_limit_info["limit"]),
            "X-RateLimit-Remaining": str(rate_limit_info["remaining"]),
            "X-RateLimit-Reset": str(rate_limit_info["reset"]),
            "X-RateLimit-Current": str(rate_limit_info["current"])
        }

class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Enhanced rate limiting middleware with per-endpoint support"""
    
    def __init__(self, app, rate_limiter: Optional[RateLimiter] = None):
        super().__init__(app)
        self.rate_limiter = rate_limiter or RateLimiter()
        
        # Endpoints to exclude from rate limiting
        self.exclude_paths = [
            "/docs",
            "/openapi.json",
            "/health",
            "/metrics"
        ]
    
    async def dispatch(self, request: Request, call_next):
        """Apply rate limiting to requests"""
        
        # Skip rate limiting for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        try:
            # Check rate limit
            is_allowed, rate_limit_info = self.rate_limiter.check_rate_limit(request)
            
            if not is_allowed:
                # Rate limit exceeded
                headers = self.rate_limiter.get_rate_limit_headers(rate_limit_info)
                
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": "Rate limit exceeded",
                        "retry_after": rate_limit_info["reset"] - int(time.time())
                    },
                    headers=headers
                )
            
            # Process the request
            response = await call_next(request)
            
            # Add rate limit headers to successful responses
            headers = self.rate_limiter.get_rate_limit_headers(rate_limit_info)
            for key, value in headers.items():
                response.headers[key] = value
            
            return response
            
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Continue without rate limiting on error
            return await call_next(request)

# Global rate limiter instance
rate_limiter = RateLimiter() 
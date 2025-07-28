"""
External API Client Framework for HealthMate

This module provides:
- Generic REST API client framework
- OAuth2 and API key authentication
- Retry logic with exponential backoff
- API rate limit handling
- Webhook management system
- Comprehensive error handling and logging
"""

import asyncio
import aiohttp
import json
import logging
import time
import hashlib
import hmac
from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import jwt
from urllib.parse import urlencode, urljoin

from app.exceptions.external_api_exceptions import (
    ExternalAPIError, APIError, RateLimitError
)
from app.utils.audit_logging import AuditLogger

logger = logging.getLogger(__name__)


class AuthenticationType(str, Enum):
    """Supported authentication types."""
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    BEARER_TOKEN = "bearer_token"
    BASIC_AUTH = "basic_auth"
    CUSTOM = "custom"


class HTTPMethod(str, Enum):
    """HTTP methods."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


@dataclass
class APIConfig:
    """Configuration for external API client."""
    base_url: str
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    auth_type: AuthenticationType = AuthenticationType.API_KEY
    timeout_seconds: int = 30
    max_retries: int = 3
    retry_delay_seconds: int = 1
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000
    custom_headers: Dict[str, str] = field(default_factory=dict)
    custom_params: Dict[str, Any] = field(default_factory=dict)
    webhook_secret: Optional[str] = None
    webhook_endpoint: Optional[str] = None


@dataclass
class OAuth2Config:
    """OAuth2 configuration."""
    authorization_url: str
    token_url: str
    refresh_token_url: Optional[str] = None
    scope: Optional[str] = None
    redirect_uri: Optional[str] = None
    state: Optional[str] = None


@dataclass
class APIResponse:
    """Standardized API response."""
    status_code: int
    data: Any
    headers: Dict[str, str]
    url: str
    method: str
    timestamp: datetime
    request_id: Optional[str] = None
    rate_limit_remaining: Optional[int] = None
    rate_limit_reset: Optional[datetime] = None


@dataclass
class WebhookEvent:
    """Webhook event structure."""
    event_type: str
    event_id: str
    timestamp: datetime
    data: Dict[str, Any]
    source: str
    signature: Optional[str] = None
    raw_payload: Optional[str] = None


class RateLimiter:
    """Rate limiting implementation."""
    
    def __init__(self, requests_per_minute: int = 60, requests_per_hour: int = 1000):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.minute_requests = []
        self.hour_requests = []
        self.lock = asyncio.Lock()
    
    async def acquire(self) -> bool:
        """Acquire rate limit permission."""
        async with self.lock:
            now = time.time()
            
            # Clean old requests
            self.minute_requests = [req for req in self.minute_requests if now - req < 60]
            self.hour_requests = [req for req in self.hour_requests if now - req < 3600]
            
            # Check limits
            if len(self.minute_requests) >= self.requests_per_minute:
                return False
            
            if len(self.hour_requests) >= self.requests_per_hour:
                return False
            
            # Add current request
            self.minute_requests.append(now)
            self.hour_requests.append(now)
            
            return True
    
    async def wait_for_permission(self) -> None:
        """Wait until rate limit allows request."""
        while not await self.acquire():
            await asyncio.sleep(1)


class RetryHandler:
    """Retry logic with exponential backoff."""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
    
    async def execute_with_retry(
        self, 
        operation: Callable, 
        *args, 
        **kwargs
    ) -> Any:
        """Execute operation with retry logic."""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return await operation(*args, **kwargs)
            except RateLimitError as e:
                # For rate limits, wait longer
                if attempt < self.max_retries:
                    wait_time = self.base_delay * (2 ** attempt) * 2
                    logger.warning(f"Rate limited, waiting {wait_time}s before retry {attempt + 1}")
                    await asyncio.sleep(wait_time)
                    continue
                raise
            except (ExternalAPIError, APIError) as e:
                last_exception = e
                if attempt < self.max_retries:
                    wait_time = self.base_delay * (2 ** attempt)
                    logger.warning(f"Request failed, retrying in {wait_time}s (attempt {attempt + 1})")
                    await asyncio.sleep(wait_time)
                    continue
                break
        
        raise last_exception


class OAuth2Handler:
    """OAuth2 authentication handler."""
    
    def __init__(self, config: OAuth2Config, api_config: APIConfig):
        self.config = config
        self.api_config = api_config
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Get OAuth2 authorization URL."""
        params = {
            'client_id': self.api_config.client_id,
            'response_type': 'code',
            'redirect_uri': self.config.redirect_uri,
        }
        
        if self.config.scope:
            params['scope'] = self.config.scope
        
        if state:
            params['state'] = state
        elif self.config.state:
            params['state'] = self.config.state
        
        return f"{self.config.authorization_url}?{urlencode(params)}"
    
    async def exchange_code_for_token(self, authorization_code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token."""
        async with aiohttp.ClientSession() as session:
            data = {
                'grant_type': 'authorization_code',
                'client_id': self.api_config.client_id,
                'client_secret': self.api_config.client_secret,
                'code': authorization_code,
                'redirect_uri': self.config.redirect_uri,
            }
            
            async with session.post(self.config.token_url, data=data) as response:
                if response.status != 200:
                    raise ExternalAPIError(f"Token exchange failed: {response.status}", api_name="oauth2")
                
                token_data = await response.json()
                self._store_tokens(token_data)
                return token_data
    
    async def refresh_access_token(self) -> Dict[str, Any]:
        """Refresh access token using refresh token."""
        if not self.refresh_token:
            raise ExternalAPIError("No refresh token available", api_name="oauth2")
        
        async with aiohttp.ClientSession() as session:
            data = {
                'grant_type': 'refresh_token',
                'client_id': self.api_config.client_id,
                'client_secret': self.api_config.client_secret,
                'refresh_token': self.refresh_token,
            }
            
            url = self.config.refresh_token_url or self.config.token_url
            
            async with session.post(url, data=data) as response:
                if response.status != 200:
                    raise ExternalAPIError(f"Token refresh failed: {response.status}", api_name="oauth2")
                
                token_data = await response.json()
                self._store_tokens(token_data)
                return token_data
    
    def _store_tokens(self, token_data: Dict[str, Any]) -> None:
        """Store tokens from response."""
        self.access_token = token_data.get('access_token')
        self.refresh_token = token_data.get('refresh_token')
        
        expires_in = token_data.get('expires_in', 3600)
        self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers."""
        if not self.access_token:
            raise ExternalAPIError("No access token available", api_name="oauth2")
        
        if self.token_expires_at and datetime.now() >= self.token_expires_at:
            raise ExternalAPIError("Access token expired", api_name="oauth2")
        
        return {'Authorization': f'Bearer {self.access_token}'}


class WebhookManager:
    """Webhook management system."""
    
    def __init__(self, secret: Optional[str] = None):
        self.secret = secret
        self.audit_logger = AuditLogger()
    
    def verify_signature(self, payload: str, signature: str, method: str = "sha256") -> bool:
        """Verify webhook signature."""
        if not self.secret:
            logger.warning("No webhook secret configured, skipping signature verification")
            return True
        
        if method == "sha256":
            expected_signature = hmac.new(
                self.secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
        elif method == "sha1":
            expected_signature = hmac.new(
                self.secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha1
            ).hexdigest()
        else:
            raise ValueError(f"Unsupported signature method: {method}")
        
        return hmac.compare_digest(signature, expected_signature)
    
    def parse_webhook_event(self, payload: str, headers: Dict[str, str]) -> WebhookEvent:
        """Parse webhook event from payload and headers."""
        try:
            data = json.loads(payload)
            
            # Extract common webhook fields
            event_type = data.get('event_type') or data.get('type') or data.get('event')
            event_id = data.get('event_id') or data.get('id') or str(hash(payload))
            timestamp_str = data.get('timestamp') or data.get('created_at')
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00')) if timestamp_str else datetime.now()
            
            # Get signature from headers
            signature = headers.get('X-Webhook-Signature') or headers.get('X-Signature') or headers.get('Signature')
            
            return WebhookEvent(
                event_type=event_type,
                event_id=event_id,
                timestamp=timestamp,
                data=data,
                source=data.get('source', 'unknown'),
                signature=signature,
                raw_payload=payload
            )
            
        except Exception as e:
            logger.error(f"Failed to parse webhook event: {e}")
            raise ExternalAPIError(f"Invalid webhook payload: {e}")
    
    async def process_webhook_event(self, event: WebhookEvent) -> Dict[str, Any]:
        """Process webhook event."""
        # Log webhook event
        self.audit_logger.log_system_action(
            action="webhook_received",
            details={
                "event_type": event.event_type,
                "event_id": event.event_id,
                "source": event.source,
                "timestamp": event.timestamp.isoformat()
            }
        )
        
        # Process based on event type
        if event.event_type == "health_data_updated":
            return await self._process_health_data_event(event)
        elif event.event_type == "user_registered":
            return await self._process_user_event(event)
        elif event.event_type == "notification_sent":
            return await self._process_notification_event(event)
        else:
            logger.info(f"Unhandled webhook event type: {event.event_type}")
            return {"status": "ignored", "event_type": event.event_type}
    
    async def _process_health_data_event(self, event: WebhookEvent) -> Dict[str, Any]:
        """Process health data webhook event."""
        # TODO: Implement health data processing
        return {"status": "processed", "type": "health_data"}
    
    async def _process_user_event(self, event: WebhookEvent) -> Dict[str, Any]:
        """Process user webhook event."""
        # TODO: Implement user event processing
        return {"status": "processed", "type": "user_event"}
    
    async def _process_notification_event(self, event: WebhookEvent) -> Dict[str, Any]:
        """Process notification webhook event."""
        # TODO: Implement notification event processing
        return {"status": "processed", "type": "notification"}


class ExternalAPIClient:
    """Generic external API client with comprehensive features."""
    
    def __init__(self, config: APIConfig, oauth2_config: Optional[OAuth2Config] = None):
        self.config = config
        self.oauth2_config = oauth2_config
        self.rate_limiter = RateLimiter(
            requests_per_minute=config.rate_limit_per_minute,
            requests_per_hour=config.rate_limit_per_hour
        )
        self.retry_handler = RetryHandler(
            max_retries=config.max_retries,
            base_delay=config.retry_delay_seconds
        )
        self.webhook_manager = WebhookManager(config.webhook_secret)
        self.audit_logger = AuditLogger()
        
        # OAuth2 handler if configured
        self.oauth2_handler = None
        if oauth2_config and config.auth_type == AuthenticationType.OAUTH2:
            self.oauth2_handler = OAuth2Handler(oauth2_config, config)
    
    async def request(
        self,
        method: HTTPMethod,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> APIResponse:
        """Make HTTP request with full feature set."""
        return await self.retry_handler.execute_with_retry(
            self._make_request,
            method,
            endpoint,
            params,
            data,
            headers,
            timeout
        )
    
    async def _make_request(
        self,
        method: HTTPMethod,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> APIResponse:
        """Make HTTP request with rate limiting and authentication."""
        # Wait for rate limit permission
        await self.rate_limiter.wait_for_permission()
        
        # Prepare URL
        url = urljoin(self.config.base_url, endpoint)
        
        # Prepare headers
        request_headers = self._prepare_headers(headers)
        
        # Prepare parameters
        request_params = self._prepare_params(params)
        
        # Prepare data
        request_data = self._prepare_data(data)
        
        # Make request
        timeout_obj = aiohttp.ClientTimeout(total=timeout or self.config.timeout_seconds)
        
        async with aiohttp.ClientSession(timeout=timeout_obj) as session:
            try:
                async with session.request(
                    method.value,
                    url,
                    params=request_params,
                    json=request_data if method in [HTTPMethod.POST, HTTPMethod.PUT, HTTPMethod.PATCH] else None,
                    headers=request_headers
                ) as response:
                    return await self._process_response(response, method, url)
                    
            except aiohttp.ClientError as e:
                raise ExternalAPIError(f"Connection error: {e}", api_name="external_api")
    
    def _prepare_headers(self, headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Prepare request headers with authentication."""
        request_headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'HealthMate-API-Client/1.0',
            **self.config.custom_headers
        }
        
        if headers:
            request_headers.update(headers)
        
        # Add authentication
        if self.config.auth_type == AuthenticationType.API_KEY and self.config.api_key:
            request_headers['X-API-Key'] = self.config.api_key
        elif self.config.auth_type == AuthenticationType.BEARER_TOKEN and self.config.api_key:
            request_headers['Authorization'] = f'Bearer {self.config.api_key}'
        elif self.config.auth_type == AuthenticationType.BASIC_AUTH and self.config.api_key and self.config.api_secret:
            import base64
            credentials = base64.b64encode(f"{self.config.api_key}:{self.config.api_secret}".encode()).decode()
            request_headers['Authorization'] = f'Basic {credentials}'
        elif self.config.auth_type == AuthenticationType.OAUTH2 and self.oauth2_handler:
            try:
                auth_headers = self.oauth2_handler.get_auth_headers()
                request_headers.update(auth_headers)
            except ExternalAPIError as e:
                logger.warning(f"OAuth2 authentication failed: {e}")
        
        return request_headers
    
    def _prepare_params(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Prepare request parameters."""
        request_params = self.config.custom_params.copy()
        
        if params:
            request_params.update(params)
        
        return request_params
    
    def _prepare_data(self, data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Prepare request data."""
        if not data:
            return None
        
        # Add any common data fields
        request_data = {
            'timestamp': datetime.now().isoformat(),
            **data
        }
        
        return request_data
    
    async def _process_response(self, response: aiohttp.ClientResponse, method: HTTPMethod, url: str) -> APIResponse:
        """Process API response."""
        # Check for rate limiting
        if response.status == 429:
            retry_after = int(response.headers.get('Retry-After', 60))
            raise RateLimitError(f"Rate limited, retry after {retry_after} seconds", retry_after=retry_after)
        
        # Parse response
        try:
            response_data = await response.json()
        except:
            response_data = await response.text()
        
        # Create API response object
        api_response = APIResponse(
            status_code=response.status,
            data=response_data,
            headers=dict(response.headers),
            url=url,
            method=method.value,
            timestamp=datetime.now(),
            request_id=response.headers.get('X-Request-ID'),
            rate_limit_remaining=response.headers.get('X-RateLimit-Remaining'),
            rate_limit_reset=response.headers.get('X-RateLimit-Reset')
        )
        
        # Log request
        self.audit_logger.log_system_action(
            action="external_api_request",
            details={
                "method": method.value,
                "url": url,
                "status_code": response.status,
                "request_id": api_response.request_id
            }
        )
        
        # Handle errors
        if response.status >= 400:
            if response.status == 401:
                raise ExternalAPIError(f"Authentication failed: {response_data}", api_name="external_api")
            elif response.status == 403:
                raise ExternalAPIError(f"Access forbidden: {response_data}")
            elif response.status == 404:
                raise ExternalAPIError(f"Resource not found: {response_data}")
            elif response.status >= 500:
                            raise APIError(f"Server error: {response_data}", api_name="external_api")
        else:
            raise APIError(f"Request failed: {response_data}", api_name="external_api")
        
        return api_response
    
    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> APIResponse:
        """Make GET request."""
        return await self.request(HTTPMethod.GET, endpoint, params=params, **kwargs)
    
    async def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> APIResponse:
        """Make POST request."""
        return await self.request(HTTPMethod.POST, endpoint, data=data, **kwargs)
    
    async def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> APIResponse:
        """Make PUT request."""
        return await self.request(HTTPMethod.PUT, endpoint, data=data, **kwargs)
    
    async def patch(self, endpoint: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> APIResponse:
        """Make PATCH request."""
        return await self.request(HTTPMethod.PATCH, endpoint, data=data, **kwargs)
    
    async def delete(self, endpoint: str, **kwargs) -> APIResponse:
        """Make DELETE request."""
        return await self.request(HTTPMethod.DELETE, endpoint, **kwargs)
    
    async def process_webhook(self, payload: str, headers: Dict[str, str]) -> Dict[str, Any]:
        """Process incoming webhook."""
        # Verify signature if secret is configured
        signature = headers.get('X-Webhook-Signature') or headers.get('X-Signature')
        if signature and not self.webhook_manager.verify_signature(payload, signature):
            raise ExternalAPIError("Invalid webhook signature")
        
        # Parse webhook event
        event = self.webhook_manager.parse_webhook_event(payload, headers)
        
        # Process event
        return await self.webhook_manager.process_webhook_event(event)
    
    def get_oauth2_authorization_url(self, state: Optional[str] = None) -> str:
        """Get OAuth2 authorization URL."""
        if not self.oauth2_handler:
            raise ExternalAPIError("OAuth2 not configured", api_name="oauth2")
        
        return self.oauth2_handler.get_authorization_url(state)
    
    async def exchange_oauth2_code(self, authorization_code: str) -> Dict[str, Any]:
        """Exchange OAuth2 authorization code for tokens."""
        if not self.oauth2_handler:
            raise ExternalAPIError("OAuth2 not configured", api_name="oauth2")
        
        return await self.oauth2_handler.exchange_code_for_token(authorization_code)
    
    async def refresh_oauth2_token(self) -> Dict[str, Any]:
        """Refresh OAuth2 access token."""
        if not self.oauth2_handler:
            raise ExternalAPIError("OAuth2 not configured", api_name="oauth2")
        
        return await self.oauth2_handler.refresh_access_token() 
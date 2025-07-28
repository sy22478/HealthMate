"""
Security Middleware for HealthMate

This module provides comprehensive security middleware including:
- HTTPS/TLS enforcement
- Security headers
- HSTS (HTTP Strict Transport Security)
- Content Security Policy
- XSS protection
- Frame options
- Content type options
- Referrer policy
"""

import logging
from typing import Optional
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from ..config import settings

logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive security middleware for HealthMate application.
    
    This middleware enforces:
    1. HTTPS/TLS in production
    2. Security headers
    3. HSTS (HTTP Strict Transport Security)
    4. Content Security Policy
    5. XSS protection
    6. Frame options
    7. Content type options
    8. Referrer policy
    """
    
    def __init__(
        self,
        app: ASGIApp,
        enforce_https: bool = None,
        security_headers: bool = None,
        hsts_enabled: bool = None,
        csp_enabled: bool = None
    ):
        super().__init__(app)
        
        # Use settings or provided parameters
        self.enforce_https = enforce_https if enforce_https is not None else settings.is_production
        self.security_headers = security_headers if security_headers is not None else settings.security_headers_enabled
        self.hsts_enabled = hsts_enabled if hsts_enabled is not None else settings.is_production
        self.csp_enabled = csp_enabled if csp_enabled is not None else settings.is_production
        
        # Paths to exclude from HTTPS enforcement
        self.https_exclude_paths = [
            "/health",
            "/metrics",
            "/docs",
            "/openapi.json",
            "/favicon.ico"
        ]
        
        logger.info(f"Security middleware initialized - HTTPS: {self.enforce_https}, Headers: {self.security_headers}")
    
    async def dispatch(self, request: Request, call_next):
        """Process the request through security checks and add security headers."""
        try:
            # Enforce HTTPS in production
            if self.enforce_https and not self._is_https_excluded(request.url.path):
                if not self._is_secure_request(request):
                    return self._create_https_redirect_response(request)
            
            # Process the request
            response = await call_next(request)
            
            # Add security headers
            if self.security_headers:
                response = self._add_security_headers(response)
            
            return response
            
        except Exception as e:
            logger.error(f"Security middleware error: {e}")
            # Continue without security features on error
            return await call_next(request)
    
    def _is_secure_request(self, request: Request) -> bool:
        """Check if the request is using HTTPS/TLS."""
        # Check for HTTPS scheme
        if request.url.scheme == "https":
            return True
        
        # Check for forwarded headers (when behind a proxy)
        forwarded_proto = request.headers.get("x-forwarded-proto")
        if forwarded_proto == "https":
            return True
        
        # Check for other security indicators
        if request.headers.get("x-forwarded-ssl") == "on":
            return True
        
        return False
    
    def _is_https_excluded(self, path: str) -> bool:
        """Check if the path is excluded from HTTPS enforcement."""
        return any(path.startswith(exclude_path) for exclude_path in self.https_exclude_paths)
    
    def _create_https_redirect_response(self, request: Request) -> JSONResponse:
        """Create a redirect response to HTTPS."""
        https_url = str(request.url).replace("http://", "https://", 1)
        
        return JSONResponse(
            status_code=301,
            content={
                "detail": "HTTPS required",
                "message": "This endpoint requires HTTPS. Please use HTTPS to access this resource.",
                "https_url": https_url
            },
            headers={
                "Location": https_url,
                "Strict-Transport-Security": self._build_hsts_header()
            }
        )
    
    def _add_security_headers(self, response: Response) -> Response:
        """Add comprehensive security headers to the response."""
        
        # HSTS (HTTP Strict Transport Security)
        if self.hsts_enabled:
            response.headers["Strict-Transport-Security"] = self._build_hsts_header()
        
        # Content Security Policy
        if self.csp_enabled:
            response.headers["Content-Security-Policy"] = settings.content_security_policy
        
        # X-Frame-Options
        response.headers["X-Frame-Options"] = settings.x_frame_options
        
        # X-Content-Type-Options
        response.headers["X-Content-Type-Options"] = settings.x_content_type_options
        
        # X-XSS-Protection
        response.headers["X-XSS-Protection"] = settings.x_xss_protection
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = settings.referrer_policy
        
        # Additional security headers
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        response.headers["X-Download-Options"] = "noopen"
        response.headers["X-DNS-Prefetch-Control"] = "off"
        
        # Remove server information
        if "server" in response.headers:
            del response.headers["server"]
        
        return response
    
    def _build_hsts_header(self) -> str:
        """Build the HSTS header value."""
        hsts_parts = [f"max-age={settings.hsts_max_age}"]
        
        if settings.hsts_include_subdomains:
            hsts_parts.append("includeSubDomains")
        
        if settings.hsts_preload:
            hsts_parts.append("preload")
        
        return "; ".join(hsts_parts)


class TLSCheckMiddleware(BaseHTTPMiddleware):
    """
    Middleware to check TLS/SSL configuration and provide warnings.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self._check_tls_config()
    
    def _check_tls_config(self):
        """Check TLS configuration and log warnings if needed."""
        if settings.is_production:
            if not settings.ssl_certfile or not settings.ssl_keyfile:
                logger.warning(
                    "Production environment detected but SSL certificate/key files not configured. "
                    "Consider using a reverse proxy (nginx, traefik) for HTTPS termination."
                )
            else:
                logger.info("SSL certificate and key files configured for production")
    
    async def dispatch(self, request: Request, call_next):
        """Process the request and add TLS information headers."""
        response = await call_next(request)
        
        # Add TLS information headers (for debugging)
        if settings.debug:
            response.headers["X-TLS-Version"] = request.headers.get("ssl-protocol", "unknown")
            response.headers["X-TLS-Cipher"] = request.headers.get("ssl-cipher", "unknown")
        
        return response


def create_security_middleware(app: ASGIApp) -> SecurityMiddleware:
    """Factory function to create security middleware with default settings."""
    return SecurityMiddleware(
        app=app,
        enforce_https=settings.is_production,
        security_headers=settings.security_headers_enabled,
        hsts_enabled=settings.is_production,
        csp_enabled=settings.is_production
    )


def create_tls_check_middleware(app: ASGIApp) -> TLSCheckMiddleware:
    """Factory function to create TLS check middleware."""
    return TLSCheckMiddleware(app=app) 
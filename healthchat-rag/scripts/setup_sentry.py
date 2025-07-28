#!/usr/bin/env python3
"""
Sentry Integration Setup Script for HealthMate

This script helps configure Sentry for error tracking and performance monitoring
in the HealthMate application.
"""

import os
import sys
import json
import requests
from typing import Dict, Any, Optional
import argparse

class SentrySetup:
    def __init__(self, sentry_dsn: str, environment: str = "production"):
        self.sentry_dsn = sentry_dsn
        self.environment = environment
        self.sentry_url = "https://sentry.io"
        
    def validate_dsn(self) -> bool:
        """Validate the Sentry DSN format."""
        if not self.sentry_dsn.startswith("https://"):
            print("❌ Invalid Sentry DSN format. Should start with 'https://'")
            return False
        return True
    
    def create_sentry_config(self) -> Dict[str, Any]:
        """Create Sentry configuration for the application."""
        return {
            "sentry": {
                "dsn": self.sentry_dsn,
                "environment": self.environment,
                "traces_sample_rate": 0.1,
                "profiles_sample_rate": 0.1,
                "send_default_pii": False,
                "before_send": "app.utils.sentry_utils.before_send",
                "before_breadcrumb": "app.utils.sentry_utils.before_breadcrumb",
                "integrations": [
                    "sentry_sdk.integrations.fastapi.FastApiIntegration",
                    "sentry_sdk.integrations.sqlalchemy.SqlalchemyIntegration",
                    "sentry_sdk.integrations.redis.RedisIntegration",
                    "sentry_sdk.integrations.celery.CeleryIntegration",
                    "sentry_sdk.integrations.httpx.HttpxIntegration"
                ]
            }
        }
    
    def create_sentry_utils(self) -> str:
        """Create Sentry utility functions."""
        return '''
"""
Sentry utility functions for HealthMate application.
"""

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.httpx import HttpxIntegration
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)

def init_sentry(dsn: str, environment: str = "production") -> None:
    """Initialize Sentry SDK with proper configuration."""
    try:
        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            traces_sample_rate=0.1,
            profiles_sample_rate=0.1,
            send_default_pii=False,
            before_send=before_send,
            before_breadcrumb=before_breadcrumb,
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
                RedisIntegration(),
                CeleryIntegration(),
                HttpxIntegration()
            ]
        )
        logger.info(f"Sentry initialized for environment: {environment}")
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")

def before_send(event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Filter events before sending to Sentry."""
    # Don't send events for certain error types
    if "exception" in hint:
        exc_type = type(hint["exception"]).__name__
        if exc_type in ["ValidationError", "HTTPException"]:
            return None
    
    # Don't send events for 4xx errors
    if "status_code" in event:
        if 400 <= event["status_code"] < 500:
            return None
    
    # Sanitize sensitive data
    if "request" in event:
        if "headers" in event["request"]:
            # Remove sensitive headers
            sensitive_headers = ["authorization", "cookie", "x-api-key"]
            for header in sensitive_headers:
                if header in event["request"]["headers"]:
                    event["request"]["headers"][header] = "[REDACTED]"
    
    return event

def before_breadcrumb(breadcrumb: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Filter breadcrumbs before sending to Sentry."""
    # Don't send breadcrumbs for certain categories
    if breadcrumb.get("category") in ["http", "console"]:
        return None
    
    # Sanitize sensitive data in breadcrumbs
    if "data" in breadcrumb:
        sensitive_keys = ["password", "token", "secret", "key"]
        for key in sensitive_keys:
            if key in breadcrumb["data"]:
                breadcrumb["data"][key] = "[REDACTED]"
    
    return breadcrumb

def capture_exception(exception: Exception, context: Optional[Dict[str, Any]] = None) -> None:
    """Capture an exception with additional context."""
    if context:
        with sentry_sdk.configure_scope() as scope:
            for key, value in context.items():
                scope.set_tag(key, value)
    
    sentry_sdk.capture_exception(exception)

def capture_message(message: str, level: str = "info", context: Optional[Dict[str, Any]] = None) -> None:
    """Capture a message with additional context."""
    if context:
        with sentry_sdk.configure_scope() as scope:
            for key, value in context.items():
                scope.set_tag(key, value)
    
    sentry_sdk.capture_message(message, level=level)

def set_user_context(user_id: str, email: Optional[str] = None, username: Optional[str] = None) -> None:
    """Set user context for Sentry events."""
    sentry_sdk.set_user({
        "id": user_id,
        "email": email,
        "username": username
    })

def set_tag(key: str, value: str) -> None:
    """Set a tag for Sentry events."""
    sentry_sdk.set_tag(key, value)

def set_context(name: str, data: Dict[str, Any]) -> None:
    """Set context data for Sentry events."""
    sentry_sdk.set_context(name, data)
'''
    
    def create_sentry_middleware(self) -> str:
        """Create Sentry middleware for FastAPI."""
        return '''
"""
Sentry middleware for FastAPI application.
"""

from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint
import sentry_sdk
import time
import logging

logger = logging.getLogger(__name__)

class SentryMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Set user context if available
        if hasattr(request.state, "user"):
            sentry_sdk.set_user({
                "id": str(request.state.user.id),
                "email": request.state.user.email,
                "username": request.state.user.username
            })
        
        # Set request context
        sentry_sdk.set_context("request", {
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent")
        })
        
        # Set tags
        sentry_sdk.set_tag("endpoint", request.url.path)
        sentry_sdk.set_tag("method", request.method)
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Set response context
            sentry_sdk.set_context("response", {
                "status_code": response.status_code,
                "headers": dict(response.headers)
            })
            
            # Set performance metrics
            duration = time.time() - start_time
            sentry_sdk.set_tag("duration", f"{duration:.3f}")
            
            return response
            
        except Exception as e:
            # Capture the exception
            sentry_sdk.capture_exception(e)
            raise
'''
    
    def create_requirements_update(self) -> str:
        """Create requirements update for Sentry dependencies."""
        return '''
# Sentry SDK for error tracking and performance monitoring
sentry-sdk[fastapi]==1.40.0
'''
    
    def create_docker_env_update(self) -> str:
        """Create Docker environment variable updates."""
        return f'''
# Sentry Configuration
SENTRY_DSN={self.sentry_dsn}
SENTRY_ENVIRONMENT={self.environment}
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_PROFILES_SAMPLE_RATE=0.1
'''
    
    def create_kubernetes_secret(self) -> str:
        """Create Kubernetes secret for Sentry configuration."""
        import base64
        dsn_encoded = base64.b64encode(self.sentry_dsn.encode()).decode()
        env_encoded = base64.b64encode(self.environment.encode()).decode()
        
        return f'''
apiVersion: v1
kind: Secret
metadata:
  name: sentry-secrets
  namespace: healthmate
type: Opaque
data:
  sentry-dsn: {dsn_encoded}
  sentry-environment: {env_encoded}
'''
    
    def setup_sentry(self) -> bool:
        """Complete Sentry setup process."""
        print("🚀 Setting up Sentry integration for HealthMate...")
        
        if not self.validate_dsn():
            return False
        
        try:
            # Create configuration
            config = self.create_sentry_config()
            
            # Create files
            files_to_create = {
                "app/utils/sentry_utils.py": self.create_sentry_utils(),
                "app/middleware/sentry_middleware.py": self.create_sentry_middleware(),
                "sentry_requirements.txt": self.create_requirements_update(),
                "sentry_env.txt": self.create_docker_env_update(),
                "k8s/sentry-secret.yaml": self.create_kubernetes_secret()
            }
            
            for file_path, content in files_to_create.items():
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'w') as f:
                    f.write(content)
                print(f"✅ Created {file_path}")
            
            # Create configuration file
            with open("sentry_config.json", 'w') as f:
                json.dump(config, f, indent=2)
            print("✅ Created sentry_config.json")
            
            print("\\n🎉 Sentry setup completed successfully!")
            print("\\n📋 Next steps:")
            print("1. Add sentry-sdk[fastapi] to your requirements.txt")
            print("2. Import and initialize Sentry in your main.py")
            print("3. Add SentryMiddleware to your FastAPI app")
            print("4. Set SENTRY_DSN environment variable in your deployment")
            print("5. Test error tracking by triggering an error")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to setup Sentry: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description="Setup Sentry integration for HealthMate")
    parser.add_argument("--dsn", required=True, help="Sentry DSN")
    parser.add_argument("--environment", default="production", help="Environment name")
    
    args = parser.parse_args()
    
    sentry_setup = SentrySetup(args.dsn, args.environment)
    success = sentry_setup.setup_sentry()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 
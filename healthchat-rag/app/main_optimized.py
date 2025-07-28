"""
Optimized FastAPI application with versioned APIs and performance enhancements.

This module provides the main FastAPI application with API versioning,
response optimization, caching, pagination, and compression features.
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import time
import logging
from contextvars import ContextVar
import uuid

from app.config import settings
from app.database import engine, Base
from app.utils.cache import init_redis_client
from app.utils.compression import get_acceptable_encoding, CompressionManager
from app.utils.audit_logging import AuditLogger
from app.exceptions.base_exceptions import HealthMateException
from app.exceptions.validation_exceptions import ValidationError
from app.exceptions.auth_exceptions import AuthenticationError, AuthorizationError
from app.exceptions.database_exceptions import DatabaseError
from app.exceptions.external_api_exceptions import ExternalAPIError

# Import versioned API routers
from app.api.v1 import auth, health, chat

# Import legacy routers for backward compatibility
from app.routers import auth as legacy_auth, health as legacy_health, chat as legacy_chat

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="HealthMate API",
    description="Optimized HealthMate API with versioning and performance enhancements",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Initialize Redis client for caching
init_redis_client(settings.REDIS_URL)

# Create database tables
Base.metadata.create_all(bind=engine)

# Correlation ID for request tracking
correlation_id: ContextVar[str] = ContextVar('correlation_id', default=None)

@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    """Add correlation ID to track requests across the application."""
    # Generate correlation ID
    corr_id = str(uuid.uuid4())
    correlation_id.set(corr_id)
    
    # Add correlation ID to request headers
    request.headers.__dict__["_list"].append(
        (b"x-correlation-id", corr_id.encode())
    )
    
    # Process request
    response = await call_next(request)
    
    # Add correlation ID to response headers
    response.headers["X-Correlation-ID"] = corr_id
    
    return response

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header to responses."""
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

@app.middleware("http")
async def compression_middleware(request: Request, call_next):
    """Apply compression to responses."""
    # Get the best acceptable encoding
    encoding = get_acceptable_encoding(request)
    
    # Call the next middleware/endpoint
    response = await call_next(request)
    
    # Check if response should be compressed
    if encoding and response.status_code == 200:
        content = response.body
        if len(content) >= 1024:  # Only compress if content is >= 1KB
            compression_manager = CompressionManager()
            compressed_content = compression_manager.compress_content(content, encoding)
            
            # Update response
            response.body = compressed_content
            response.headers["Content-Encoding"] = encoding
            response.headers["Content-Length"] = str(len(compressed_content))
            response.headers["Vary"] = "Accept-Encoding"
    
    return response

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gzip middleware for additional compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Global exception handlers
@app.exception_handler(HealthMateException)
async def healthmate_exception_handler(request: Request, exc: HealthMateException):
    """Handle custom HealthMate exceptions."""
    error_response = {
        "error": {
            "code": exc.error_code.value,
            "message": exc.message,
            "details": exc.details,
            "timestamp": exc.timestamp.isoformat(),
            "correlation_id": correlation_id.get()
        },
        "metadata": {
            "version": "v1",
            "endpoint": request.url.path,
            "method": request.method
        }
    }
    
    # Audit log the error
    AuditLogger.log_api_call(
        method=request.method,
        path=request.url.path,
        status_code=exc.status_code,
        success=False,
        details={
            "error_code": exc.error_code.value,
            "error_message": exc.message,
            "correlation_id": correlation_id.get()
        },
        request=request
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
    )

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle validation errors."""
    error_response = {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Validation failed",
            "details": exc.details,
            "timestamp": exc.timestamp.isoformat(),
            "correlation_id": correlation_id.get()
        },
        "metadata": {
            "version": "v1",
            "endpoint": request.url.path,
            "method": request.method
        }
    }
    
    return JSONResponse(
        status_code=422,
        content=error_response
    )

@app.exception_handler(AuthenticationError)
async def authentication_exception_handler(request: Request, exc: AuthenticationError):
    """Handle authentication errors."""
    error_response = {
        "error": {
            "code": "AUTHENTICATION_ERROR",
            "message": "Authentication failed",
            "details": exc.details,
            "timestamp": exc.timestamp.isoformat(),
            "correlation_id": correlation_id.get()
        },
        "metadata": {
            "version": "v1",
            "endpoint": request.url.path,
            "method": request.method
        }
    }
    
    return JSONResponse(
        status_code=401,
        content=error_response
    )

@app.exception_handler(AuthorizationError)
async def authorization_exception_handler(request: Request, exc: AuthorizationError):
    """Handle authorization errors."""
    error_response = {
        "error": {
            "code": "AUTHORIZATION_ERROR",
            "message": "Access denied",
            "details": exc.details,
            "timestamp": exc.timestamp.isoformat(),
            "correlation_id": correlation_id.get()
        },
        "metadata": {
            "version": "v1",
            "endpoint": request.url.path,
            "method": request.method
        }
    }
    
    return JSONResponse(
        status_code=403,
        content=error_response
    )

@app.exception_handler(DatabaseError)
async def database_exception_handler(request: Request, exc: DatabaseError):
    """Handle database errors."""
    error_response = {
        "error": {
            "code": "DATABASE_ERROR",
            "message": "Database operation failed",
            "details": exc.details,
            "timestamp": exc.timestamp.isoformat(),
            "correlation_id": correlation_id.get()
        },
        "metadata": {
            "version": "v1",
            "endpoint": request.url.path,
            "method": request.method
        }
    }
    
    return JSONResponse(
        status_code=500,
        content=error_response
    )

@app.exception_handler(ExternalAPIError)
async def external_api_exception_handler(request: Request, exc: ExternalAPIError):
    """Handle external API errors."""
    error_response = {
        "error": {
            "code": "EXTERNAL_API_ERROR",
            "message": "External service error",
            "details": exc.details,
            "timestamp": exc.timestamp.isoformat(),
            "correlation_id": correlation_id.get()
        },
        "metadata": {
            "version": "v1",
            "endpoint": request.url.path,
            "method": request.method
        }
    }
    
    return JSONResponse(
        status_code=502,
        content=error_response
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    error_response = {
        "error": {
            "code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
            "details": str(exc) if settings.DEBUG else "Internal server error",
            "timestamp": time.time(),
            "correlation_id": correlation_id.get()
        },
        "metadata": {
            "version": "v1",
            "endpoint": request.url.path,
            "method": request.method
        }
    }
    
    # Log the error
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    # Audit log the error
    AuditLogger.log_api_call(
        method=request.method,
        path=request.url.path,
        status_code=500,
        success=False,
        details={
            "error": str(exc),
            "correlation_id": correlation_id.get()
        },
        request=request
    )
    
    return JSONResponse(
        status_code=500,
        content=error_response
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": time.time(),
        "metadata": {
            "api_version": "v1",
            "features": [
                "api_versioning",
                "response_caching",
                "pagination",
                "compression",
                "rate_limiting",
                "audit_logging"
            ]
        }
    }

# API versioning endpoints
@app.get("/api")
async def api_info():
    """API information and available versions."""
    return {
        "name": "HealthMate API",
        "version": "2.0.0",
        "available_versions": {
            "v1": {
                "status": "stable",
                "base_url": "/api/v1",
                "features": [
                    "authentication",
                    "health_data",
                    "chat",
                    "caching",
                    "pagination",
                    "compression"
                ]
            }
        },
        "deprecated_versions": [],
        "metadata": {
            "timestamp": time.time(),
            "documentation": "/docs"
        }
    }

# Include versioned API routers
app.include_router(
    auth.router,
    prefix="/api/v1",
    tags=["Authentication v1"]
)

app.include_router(
    health.router,
    prefix="/api/v1",
    tags=["Health v1"]
)

app.include_router(
    chat.router,
    prefix="/api/v1",
    tags=["Chat v1"]
)

# Include legacy routers for backward compatibility
app.include_router(
    legacy_auth.router,
    prefix="/auth",
    tags=["Authentication (Legacy)"]
)

app.include_router(
    legacy_health.router,
    prefix="/health",
    tags=["Health (Legacy)"]
)

app.include_router(
    legacy_chat.router,
    prefix="/chat",
    tags=["Chat (Legacy)"]
)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("HealthMate API v2.0.0 starting up...")
    logger.info("Features enabled: API versioning, caching, pagination, compression")
    
    # Initialize Redis connection
    try:
        init_redis_client(settings.REDIS_URL)
        logger.info("Redis client initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize Redis client: {e}")
    
    # Log startup information
    AuditLogger.log_api_call(
        method="STARTUP",
        path="/",
        success=True,
        details={
            "version": "2.0.0",
            "features": [
                "api_versioning",
                "response_caching",
                "pagination",
                "compression",
                "rate_limiting",
                "audit_logging"
            ]
        }
    )

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("HealthMate API shutting down...")
    
    # Log shutdown information
    AuditLogger.log_api_call(
        method="SHUTDOWN",
        path="/",
        success=True,
        details={
            "version": "2.0.0",
            "reason": "normal_shutdown"
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main_optimized:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 
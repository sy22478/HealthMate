from dotenv import load_dotenv
import os
import logging
from pythonjsonlogger import jsonlogger

# JSON logging configuration
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    fmt='%(asctime)s %(levelname)s %(name)s %(message)s %(correlation_id)s',
    rename_fields={"asctime": "timestamp", "levelname": "level", "name": "logger", "message": "message"}
)
logHandler.setFormatter(formatter)
rootLogger = logging.getLogger()
rootLogger.handlers = []  # Remove any default handlers
rootLogger.addHandler(logHandler)
rootLogger.setLevel(logging.INFO)

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

# Set default values for required environment variables
os.environ.setdefault("OPENAI_API_KEY", "dummy_key")
os.environ.setdefault("PINECONE_API_KEY", "dummy_key")
os.environ.setdefault("PINECONE_ENVIRONMENT", "dummy_env")
os.environ.setdefault("PINECONE_INDEX_NAME", "dummy_index")
os.environ.setdefault("POSTGRES_URI", "sqlite:///./test.db")
os.environ.setdefault("SECRET_KEY", "dummy_secret_key_for_development")

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from app.database import get_db
from app.routers import auth_router, chat_router, enhanced_chat_router, health_router, health_data_router, analytics_router, advanced_analytics_router, visualization_router, websocket_router, database_optimization_router, health_data_processing_router, vector_store_optimization_router, ai_processing_pipeline_router, user_modeling_router, predictive_analytics_router, performance_monitoring_router
from app.routers.webhook_management import webhook_router
from app.routers.data_pipeline import data_pipeline_router
from app.routers.compliance import router as compliance_router
from app.routers.business_intelligence import bi_router
from app.routers.ml_data_preparation import ml_data_router
from app.routers.backup_disaster_recovery import router as backup_dr_router
from app.services.vector_store import VectorStore
from app.services.knowledge_base import MedicalKnowledgeBase
from app.config import settings
from app.utils.input_sanitization_middleware import InputSanitizationMiddleware
from app.utils.rate_limiting import RateLimitingMiddleware, RateLimiter
from app.utils.request_response_validation import RequestResponseValidationMiddleware
from app.utils.security_middleware import SecurityMiddleware, TLSCheckMiddleware
from app.utils.exception_handlers import setup_exception_handlers
from contextlib import asynccontextmanager
from app.utils.correlation_id_middleware import CorrelationIdMiddleware
from app.utils.api_audit_middleware import APIAuditMiddleware

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app):
    logger.info("Starting HealthMate application...")
    try:
        logger.info("Initializing vector store and knowledge base...")
        vector_store = VectorStore(settings.pinecone_api_key, settings.pinecone_environment, settings.pinecone_index_name)
        knowledge_base = MedicalKnowledgeBase(vector_store)
        knowledge_base.load_medical_sources()
        app.state.knowledge_base = knowledge_base
        logger.info("Vector store and knowledge base initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize vector store/knowledge base: {e}")
        app.state.knowledge_base = None
        logger.info("Application will continue without AI features")
    
    logger.info("HealthMate application started successfully")
    yield
    logger.info("Shutting down HealthMate application...")

app = FastAPI(title="HealthChat RAG API", version="1.0.0", lifespan=lifespan)

# Add correlation ID middleware first
app.add_middleware(CorrelationIdMiddleware)

# Add API audit middleware
app.add_middleware(APIAuditMiddleware)

# Setup exception handlers
setup_exception_handlers(app)

# Add security middleware first (order matters)
app.add_middleware(SecurityMiddleware)

# Add TLS check middleware
app.add_middleware(TLSCheckMiddleware)

# Add input sanitization middleware
app.add_middleware(InputSanitizationMiddleware)

# Add request/response validation middleware
app.add_middleware(RequestResponseValidationMiddleware)

# Global rate limiter instance (disabled for testing)
rate_limiter = RateLimiter(disabled=True)
app.add_middleware(RateLimitingMiddleware, rate_limiter=rate_limiter)

# Enhanced CORS configuration with security considerations
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_methods_list,
    allow_headers=settings.cors_headers_list,
    expose_headers=settings.cors_expose_headers_list,
    max_age=settings.cors_max_age,
)

# Global vector store and knowledge base
vector_store = None
knowledge_base = None

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(chat_router, prefix="/chat", tags=["chat"])
app.include_router(enhanced_chat_router, tags=["enhanced-chat"])
app.include_router(health_router, prefix="/health", tags=["health"])
app.include_router(health_data_router, tags=["health-data"])
app.include_router(analytics_router, tags=["analytics"])
app.include_router(advanced_analytics_router, tags=["advanced-analytics"])
app.include_router(visualization_router, tags=["visualization"])
app.include_router(websocket_router, tags=["websocket"])
app.include_router(database_optimization_router, prefix="/database", tags=["database-optimization"])
app.include_router(health_data_processing_router, tags=["health-data-processing"])
app.include_router(vector_store_optimization_router, tags=["vector-store-optimization"])
app.include_router(ai_processing_pipeline_router, tags=["ai-processing-pipeline"])
app.include_router(user_modeling_router, tags=["user-modeling"])
app.include_router(predictive_analytics_router, tags=["predictive-analytics"])
app.include_router(performance_monitoring_router, tags=["performance-monitoring"])
app.include_router(webhook_router, tags=["webhook-management"])
app.include_router(data_pipeline_router, tags=["data-pipeline"])
app.include_router(compliance_router, tags=["compliance"])
app.include_router(bi_router, tags=["business-intelligence"])
app.include_router(ml_data_router, tags=["ml-data-preparation"])
app.include_router(backup_dr_router, tags=["backup-disaster-recovery"])

@app.get("/")
async def root():
    return {"message": "HealthChat RAG API is running"}

@app.get("/test")
async def test_endpoint():
    """Simple test endpoint for debugging."""
    return {"status": "ok", "message": "Test endpoint working"}

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring and load balancers."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.environment,
        "timestamp": "2024-01-01T00:00:00Z"  # In production, use actual timestamp
    }

@app.get("/health/simple")
async def simple_health_check():
    """Simple health check that doesn't depend on external services."""
    return {"status": "ok"}

@app.get("/health/debug")
async def debug_health_check():
    """Debug health check with more information."""
    return {
        "status": "ok",
        "port": os.getenv("PORT", "8000"),
        "environment": os.getenv("ENVIRONMENT", "unknown"),
        "timestamp": "2024-01-01T00:00:00Z"
    }

@app.get("/security-info")
async def security_info():
    """Security information endpoint for debugging and compliance."""
    return {
        "https_enforced": settings.is_production,
        "security_headers_enabled": settings.security_headers_enabled,
        "hsts_enabled": settings.is_production,
        "cors_origins": settings.cors_origins_list,
        "rate_limiting_enabled": settings.rate_limit_enabled,
        "request_validation_enabled": settings.request_validation_enabled,
        "response_validation_enabled": settings.response_validation_enabled
    } 
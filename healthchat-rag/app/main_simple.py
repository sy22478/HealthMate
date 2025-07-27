from dotenv import load_dotenv
import os
import logging
from contextlib import asynccontextmanager
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from app.database import get_db
from app.routers import auth_router, chat_router, health_router
from app.config import settings
from app.utils.request_response_validation import RequestResponseValidationMiddleware
from app.services.vector_store import VectorStore
from app.services.knowledge_base import MedicalKnowledgeBase

logger = logging.getLogger(__name__)

# CORS configuration
CORS_ALLOW_ORIGINS = os.getenv("CORS_ALLOW_ORIGINS", "*")
if CORS_ALLOW_ORIGINS == "*":
    allow_origins = ["*"]
    if os.getenv("ENV", "development") == "production":
        logger.warning("CORS is set to '*' in production! This is insecure. Set CORS_ALLOW_ORIGINS to a comma-separated list of allowed origins.")
else:
    allow_origins = [origin.strip() for origin in CORS_ALLOW_ORIGINS.split(",") if origin.strip()]

@asynccontextmanager
async def lifespan(app):
    """Initialize knowledge base on startup"""
    try:
        logger.info("Initializing knowledge base...")
        vector_store = VectorStore(settings.pinecone_api_key, settings.pinecone_environment, settings.pinecone_index_name)
        knowledge_base = MedicalKnowledgeBase(vector_store)
        knowledge_base.load_medical_sources()
        app.state.knowledge_base = knowledge_base
        logger.info("Knowledge base initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize knowledge base: {e}")
        app.state.knowledge_base = None
    yield
    # Cleanup if needed

app = FastAPI(title="HealthChat RAG API", version="1.0.0", lifespan=lifespan)

# Add request/response validation middleware
app.add_middleware(RequestResponseValidationMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(chat_router, prefix="/chat", tags=["chat"])
app.include_router(health_router, prefix="/health", tags=["health"])

@app.get("/")
async def root():
    return {"message": "HealthChat RAG API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is running"} 
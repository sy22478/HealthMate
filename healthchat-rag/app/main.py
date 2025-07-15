from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from app.database import get_db
from app.routers import auth_router, chat_router, health_router
from app.services.vector_store import VectorStore
from app.services.knowledge_base import MedicalKnowledgeBase
from app.config import settings
from app.utils.encryption import EncryptionManager

app = FastAPI(title="HealthChat RAG API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global vector store and knowledge base
vector_store = None
knowledge_base = None

@app.on_event("startup")
def startup_event():
    global vector_store, knowledge_base
    vector_store = VectorStore(settings.pinecone_api_key, settings.pinecone_environment, settings.pinecone_index_name)
    knowledge_base = MedicalKnowledgeBase(vector_store)
    knowledge_base.load_medical_sources()
    app.state.knowledge_base = knowledge_base
    # Initialize encryption manager
    app.state.encryption_manager = EncryptionManager(settings.encryption_key)

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(chat_router, prefix="/chat", tags=["chat"])
app.include_router(health_router, prefix="/health", tags=["health"])

@app.get("/")
async def root():
    return {"message": "HealthChat RAG API is running"} 
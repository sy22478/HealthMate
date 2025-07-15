from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, Conversation
from app.services.openai_agent import HealthAgent
from app.config import settings
from jose import jwt, JWTError
from pydantic import BaseModel
import json
import openai
from typing import List
from app.utils.audit_log import log_audit_event
from app.routers.auth import get_current_user

router = APIRouter()
security = HTTPBearer()
health_agent = HealthAgent(settings.openai_api_key)

DISCLAIMER = "\n\n**Disclaimer:** This response is for informational purposes only and is not a substitute for professional medical advice. Always consult a healthcare provider for serious concerns."

class ChatMessage(BaseModel):
    message: str

def moderate_response(response_text: str) -> bool:
    """Returns True if the response is safe, False if flagged as unsafe."""
    client = openai.OpenAI(api_key=settings.openai_api_key)
    moderation = client.moderations.create(input=response_text)
    flagged = moderation.results[0].flagged
    return not flagged

@router.post("/message")
async def chat_message(data: ChatMessage, user: User = Depends(get_current_user), request: Request = None, db: Session = Depends(get_db)):
    encryption_manager = request.app.state.encryption_manager if request else None
    # Build user profile dict
    user_profile = {
        "email": user.email,
        "full_name": user.full_name,
        "age": user.age,
        "medical_conditions": user.medical_conditions,
        "medications": user.medications
    }
    # Get knowledge_base from app state
    knowledge_base = request.app.state.knowledge_base
    # Get relevant context
    context = knowledge_base.get_relevant_context(data.message, user_profile)
    # Get AI response
    response = health_agent.chat_with_context(data.message, context, user_profile)
    # Moderate response using OpenAI moderation endpoint
    is_safe = moderate_response(response)
    if not is_safe:
        log_audit_event(user.email, "chat_blocked", "Response blocked by moderation")
        return {"response": "⚠️ This response was blocked for safety by our moderation system. Please consult a healthcare professional." + DISCLAIMER}
    # Encrypt before saving
    encrypted_message = encryption_manager.encrypt(data.message) if encryption_manager else data.message
    encrypted_response = encryption_manager.encrypt(response) if encryption_manager else response
    encrypted_context = encryption_manager.encrypt(context) if encryption_manager else context
    new_convo = Conversation(
        user_id=user.id,
        message=encrypted_message,
        response=encrypted_response,
        context_used=encrypted_context
    )
    db.add(new_convo)
    db.commit()
    log_audit_event(user.email, "chat_message", f"User sent message: {data.message}")
    return {"response": response + DISCLAIMER}

@router.get("/history", response_model=List[dict])
async def get_history(user: User = Depends(get_current_user), db: Session = Depends(get_db), request: Request = None):
    encryption_manager = request.app.state.encryption_manager if request else None
    history = (
        db.query(Conversation)
        .filter(Conversation.user_id == user.id)
        .order_by(Conversation.timestamp.asc())
        .all()
    )
    # Decrypt fields for frontend
    result = []
    for i, convo in enumerate(history):
        message = encryption_manager.decrypt(convo.message) if encryption_manager else convo.message
        response = encryption_manager.decrypt(convo.response) if encryption_manager else convo.response
        # Only include decrypted content
        if i % 2 == 0:
            result.append({
                "role": "user",
                "content": message,
                "timestamp": convo.timestamp.isoformat()
            })
        else:
            result.append({
                "role": "assistant",
                "content": response,
                "timestamp": convo.timestamp.isoformat()
            })
    log_audit_event(user.email, "chat_history_access", f"User accessed chat history, {len(result)} messages")
    return result 
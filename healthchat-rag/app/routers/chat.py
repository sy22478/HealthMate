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

router = APIRouter()
security = HTTPBearer()
health_agent = HealthAgent(settings.openai_api_key)

DISCLAIMER = "\n\n**Disclaimer:** This response is for informational purposes only and is not a substitute for professional medical advice. Always consult a healthcare provider for serious concerns."

class ChatMessage(BaseModel):
    message: str

# Helper to get user from JWT
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def moderate_response(response_text: str) -> bool:
    """Returns True if the response is safe, False if flagged as unsafe."""
    client = openai.OpenAI(api_key=settings.openai_api_key)
    moderation = client.moderations.create(input=response_text)
    flagged = moderation.results[0].flagged
    return not flagged

@router.post("/message")
async def chat_message(data: ChatMessage, user: User = Depends(get_current_user), request: Request = None, db: Session = Depends(get_db)):
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
        return {"response": "⚠️ This response was blocked for safety by our moderation system. Please consult a healthcare professional." + DISCLAIMER}
    # Save conversation to database
    new_convo = Conversation(
        user_id=user.id,
        message=data.message,
        response=response,
        context_used=context
    )
    db.add(new_convo)
    db.commit()
    return {"response": response + DISCLAIMER}

@router.get("/history", response_model=List[dict])
async def get_history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    history = (
        db.query(Conversation)
        .filter(Conversation.user_id == user.id)
        .order_by(Conversation.timestamp.asc())
        .all()
    )
    # Return as list of dicts for frontend
    return [
        {
            "role": "user",
            "content": convo.message,
            "timestamp": convo.timestamp.isoformat()
        }
        if i % 2 == 0 else
        {
            "role": "assistant",
            "content": convo.response,
            "timestamp": convo.timestamp.isoformat()
        }
        for i, convo in enumerate(history)
    ] 
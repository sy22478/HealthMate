"""
Enhanced Chat Router
Advanced chat endpoints with health data integration
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from app.database import get_db
from app.models.user import User
from app.utils.auth_middleware import get_current_user
from app.services.enhanced_chat_service import EnhancedChatService
from app.utils.audit_logging import AuditLogger
from app.config import settings
from sqlalchemy import and_

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/enhanced-chat", tags=["Enhanced Chat"])

# Pydantic schemas
class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000, description="User's message")

class ChatResponse(BaseModel):
    response: str
    conversation_id: Optional[int] = None
    health_context_used: bool = False
    function_call: bool = False
    timestamp: str
    suggestions: Optional[List[str]] = None

class ConversationHistoryResponse(BaseModel):
    conversations: List[Dict[str, Any]]
    total_count: int
    has_more: bool

class ChatSuggestionsResponse(BaseModel):
    suggestions: List[str]
    personalized: bool = True

# Enhanced Chat Endpoints

@router.post("/message", response_model=ChatResponse)
async def enhanced_chat_message(
    data: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Send a message to the enhanced health assistant"""
    try:
        # Check if knowledge base is available
        knowledge_base = getattr(request.app.state, "knowledge_base", None)
        medical_context = ""
        
        if knowledge_base:
            # Get medical knowledge context
            medical_context = knowledge_base.get_relevant_context(data.message, {})
        else:
            logger.warning("Knowledge base not available, proceeding without medical context")
        
        # Initialize enhanced chat service
        chat_service = EnhancedChatService(db, settings.openai_api_key)
        
        # Get enhanced response with health context
        chat_result = chat_service.chat_with_health_context(
            current_user, 
            data.message, 
            medical_context
        )
        
        # Save conversation
        conversation_id = chat_service.save_conversation(
            current_user.id,
            data.message,
            chat_result["response"],
            medical_context
        )
        
        # Get personalized suggestions
        suggestions = chat_service.get_chat_suggestions(current_user.id)
        
        AuditLogger.log_health_event(
            event_type="enhanced_chat_message",
            user_id=current_user.id,
            message_length=len(data.message),
            health_context_used=chat_result.get("health_context_used", False),
            success=True
        )
        
        return ChatResponse(
            response=chat_result["response"],
            conversation_id=conversation_id,
            health_context_used=chat_result.get("health_context_used", False),
            function_call=chat_result.get("function_call", False),
            timestamp=chat_result["timestamp"],
            suggestions=suggestions
        )
        
    except Exception as e:
        logger.error(f"Error in enhanced chat message: {e}")
        AuditLogger.log_health_event(
            event_type="enhanced_chat_message",
            user_id=current_user.id,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to process chat message")

@router.get("/history", response_model=ConversationHistoryResponse)
async def get_enhanced_chat_history(
    limit: int = Query(20, ge=1, le=100, description="Number of conversations to return"),
    offset: int = Query(0, ge=0, description="Number of conversations to skip"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get enhanced chat history with health context"""
    try:
        from app.models.user import Conversation
        
        # Get total count
        total_count = db.query(Conversation).filter(
            Conversation.user_id == current_user.id
        ).count()
        
        # Get conversations with pagination
        conversations = db.query(Conversation).filter(
            Conversation.user_id == current_user.id
        ).order_by(Conversation.timestamp.desc()).offset(offset).limit(limit + 1).all()
        
        # Check if there are more conversations
        has_more = len(conversations) > limit
        if has_more:
            conversations = conversations[:-1]  # Remove the extra one
        
        # Format conversation data
        conversation_data = []
        for conv in conversations:
            conversation_data.append({
                "id": conv.id,
                "message": conv.message,
                "response": conv.response,
                "timestamp": conv.timestamp.isoformat(),
                "context_used": bool(conv.context_used),
                "feedback": conv.feedback
            })
        
        AuditLogger.log_health_event(
            event_type="enhanced_chat_history_requested",
            user_id=current_user.id,
            limit=limit,
            offset=offset,
            success=True
        )
        
        return ConversationHistoryResponse(
            conversations=conversation_data,
            total_count=total_count,
            has_more=has_more
        )
        
    except Exception as e:
        logger.error(f"Error getting enhanced chat history: {e}")
        AuditLogger.log_health_event(
            event_type="enhanced_chat_history_requested",
            user_id=current_user.id,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to get chat history")

@router.get("/suggestions", response_model=ChatSuggestionsResponse)
async def get_chat_suggestions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get personalized chat suggestions based on user's health data"""
    try:
        chat_service = EnhancedChatService(db, settings.openai_api_key)
        suggestions = chat_service.get_chat_suggestions(current_user.id)
        
        AuditLogger.log_health_event(
            event_type="chat_suggestions_requested",
            user_id=current_user.id,
            suggestions_count=len(suggestions),
            success=True
        )
        
        return ChatSuggestionsResponse(
            suggestions=suggestions,
            personalized=True
        )
        
    except Exception as e:
        logger.error(f"Error getting chat suggestions: {e}")
        AuditLogger.log_health_event(
            event_type="chat_suggestions_requested",
            user_id=current_user.id,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to get chat suggestions")

@router.post("/feedback/{conversation_id}")
async def submit_chat_feedback(
    conversation_id: int,
    feedback: str = Query(..., regex="^(up|down)$", description="Feedback type: up or down"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit feedback for a chat conversation"""
    try:
        from app.models.user import Conversation
        
        # Find the conversation
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        ).first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Update feedback
        conversation.feedback = feedback
        db.commit()
        
        AuditLogger.log_health_event(
            event_type="chat_feedback_submitted",
            user_id=current_user.id,
            conversation_id=conversation_id,
            feedback=feedback,
            success=True
        )
        
        return {"message": "Feedback submitted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting chat feedback: {e}")
        AuditLogger.log_health_event(
            event_type="chat_feedback_submitted",
            user_id=current_user.id,
            conversation_id=conversation_id,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to submit feedback")

@router.get("/health-context")
async def get_user_health_context(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's health context for chat (summary only)"""
    try:
        chat_service = EnhancedChatService(db, settings.openai_api_key)
        health_context = chat_service.get_user_health_context(current_user.id)
        
        # Return only summary data for privacy
        summary = {
            "data_summary": health_context.get("data_summary", {}),
            "has_recent_symptoms": bool(health_context.get("recent_symptoms")),
            "has_recent_medications": bool(health_context.get("recent_medications")),
            "has_health_data": bool(health_context.get("recent_health_data"))
        }
        
        AuditLogger.log_health_event(
            event_type="health_context_requested",
            user_id=current_user.id,
            success=True
        )
        
        return summary
        
    except Exception as e:
        logger.error(f"Error getting health context: {e}")
        AuditLogger.log_health_event(
            event_type="health_context_requested",
            user_id=current_user.id,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to get health context")

@router.delete("/conversation/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a specific conversation"""
    try:
        from app.models.user import Conversation
        
        # Find the conversation
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        ).first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Delete the conversation
        db.delete(conversation)
        db.commit()
        
        AuditLogger.log_health_event(
            event_type="conversation_deleted",
            user_id=current_user.id,
            conversation_id=conversation_id,
            success=True
        )
        
        return {"message": "Conversation deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        AuditLogger.log_health_event(
            event_type="conversation_deleted",
            user_id=current_user.id,
            conversation_id=conversation_id,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to delete conversation")

@router.get("/stats")
async def get_chat_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get chat statistics for the user"""
    try:
        from app.models.user import Conversation
        from sqlalchemy import func
        
        # Get total conversations
        total_conversations = db.query(Conversation).filter(
            Conversation.user_id == current_user.id
        ).count()
        
        # Get conversations in last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_conversations = db.query(Conversation).filter(
            and_(
                Conversation.user_id == current_user.id,
                Conversation.timestamp >= thirty_days_ago
            )
        ).count()
        
        # Get feedback statistics
        feedback_stats = db.query(
            Conversation.feedback,
            func.count(Conversation.id)
        ).filter(
            and_(
                Conversation.user_id == current_user.id,
                Conversation.feedback.isnot(None)
            )
        ).group_by(Conversation.feedback).all()
        
        feedback_summary = {feedback: count for feedback, count in feedback_stats}
        
        stats = {
            "total_conversations": total_conversations,
            "recent_conversations_30_days": recent_conversations,
            "feedback_summary": feedback_summary,
            "average_conversations_per_month": recent_conversations
        }
        
        AuditLogger.log_health_event(
            event_type="chat_statistics_requested",
            user_id=current_user.id,
            success=True
        )
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting chat statistics: {e}")
        AuditLogger.log_health_event(
            event_type="chat_statistics_requested",
            user_id=current_user.id,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to get chat statistics") 
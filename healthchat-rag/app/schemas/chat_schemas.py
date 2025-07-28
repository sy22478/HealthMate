"""
Chat Pydantic Schemas
Comprehensive schemas for chat messaging and conversation management
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from enum import Enum

class MessageType(str, Enum):
    """Message type enumeration"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    ERROR = "error"

class MessageStatus(str, Enum):
    """Message status enumeration"""
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    PENDING = "pending"

class ChatMessageCreate(BaseModel):
    """Chat message creation schema"""
    user_id: int = Field(..., description="User ID")
    session_id: Optional[int] = Field(None, description="Chat session ID")
    message_type: MessageType = Field(default=MessageType.USER, description="Message type")
    content: str = Field(..., min_length=1, max_length=5000, description="Message content")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Message context")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Message metadata")
    parent_message_id: Optional[int] = Field(None, description="Parent message ID for threading")
    attachments: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Message attachments")

    @field_validator('content')
    def validate_content(cls, v):
        """Validate message content"""
        if not v.strip():
            raise ValueError("Message content cannot be empty")
        return v.strip()

    @field_validator('attachments')
    def validate_attachments(cls, v):
        """Validate attachments"""
        if v:
            for attachment in v:
                if 'type' not in attachment or 'url' not in attachment:
                    raise ValueError("Attachments must have 'type' and 'url' fields")
                if attachment['type'] not in ['image', 'document', 'audio', 'video']:
                    raise ValueError("Invalid attachment type")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 123,
                "session_id": 456,
                "message_type": "user",
                "content": "I have been experiencing headaches for the past week",
                "context": {
                    "symptoms": ["headache"],
                    "duration": "1 week",
                    "severity": "moderate"
                },
                "metadata": {
                    "platform": "web",
                    "user_agent": "Mozilla/5.0...",
                    "location": "US"
                },
                "parent_message_id": None,
                "attachments": []
            }
        }

class ChatMessageResponse(BaseModel):
    """Chat message response schema"""
    id: int = Field(..., description="Message ID")
    user_id: int = Field(..., description="User ID")
    session_id: Optional[int] = Field(None, description="Chat session ID")
    message_type: MessageType = Field(..., description="Message type")
    content: str = Field(..., description="Message content")
    context: Optional[Dict[str, Any]] = Field(None, description="Message context")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Message metadata")
    parent_message_id: Optional[int] = Field(None, description="Parent message ID")
    attachments: Optional[List[Dict[str, Any]]] = Field(None, description="Message attachments")
    status: MessageStatus = Field(..., description="Message status")
    created_at: datetime = Field(..., description="Message creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    read_at: Optional[datetime] = Field(None, description="Message read timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 789,
                "user_id": 123,
                "session_id": 456,
                "message_type": "assistant",
                "content": "I understand you've been experiencing headaches. Let me ask you a few questions to better understand your situation.",
                "context": {
                    "symptoms": ["headache"],
                    "duration": "1 week",
                    "severity": "moderate"
                },
                "metadata": {
                    "ai_model": "gpt-4",
                    "response_time": 1.2,
                    "confidence": 0.95
                },
                "parent_message_id": 788,
                "attachments": [],
                "status": "delivered",
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
                "read_at": "2024-01-01T12:01:00Z"
            }
        }

class ChatSessionCreate(BaseModel):
    """Chat session creation schema"""
    user_id: int = Field(..., description="User ID")
    title: Optional[str] = Field(None, max_length=200, description="Session title")
    description: Optional[str] = Field(None, max_length=500, description="Session description")
    category: Optional[str] = Field(None, max_length=100, description="Session category")
    tags: Optional[List[str]] = Field(default_factory=list, description="Session tags")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Session metadata")

    @field_validator('title')
    def validate_title(cls, v):
        """Validate session title"""
        if v is not None and not v.strip():
            raise ValueError("Session title cannot be empty if provided")
        return v.strip() if v else v

    @field_validator('tags')
    def validate_tags(cls, v):
        """Validate session tags"""
        if v:
            # Remove duplicates and empty tags
            unique_tags = list(set(tag.strip() for tag in v if tag.strip()))
            if len(unique_tags) > 10:
                raise ValueError("Maximum 10 tags allowed")
            return unique_tags
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 123,
                "title": "Headache Consultation",
                "description": "Discussion about persistent headaches",
                "category": "symptoms",
                "tags": ["headache", "consultation", "symptoms"],
                "metadata": {
                    "priority": "medium",
                    "source": "user_initiated"
                }
            }
        }

class ChatSessionResponse(BaseModel):
    """Chat session response schema"""
    id: int = Field(..., description="Session ID")
    user_id: int = Field(..., description="User ID")
    title: Optional[str] = Field(None, description="Session title")
    description: Optional[str] = Field(None, description="Session description")
    category: Optional[str] = Field(None, description="Session category")
    tags: Optional[List[str]] = Field(None, description="Session tags")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Session metadata")
    message_count: int = Field(..., description="Number of messages in session")
    last_message_at: Optional[datetime] = Field(None, description="Last message timestamp")
    is_active: bool = Field(..., description="Session status")
    created_at: datetime = Field(..., description="Session creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 456,
                "user_id": 123,
                "title": "Headache Consultation",
                "description": "Discussion about persistent headaches",
                "category": "symptoms",
                "tags": ["headache", "consultation", "symptoms"],
                "metadata": {
                    "priority": "medium",
                    "source": "user_initiated"
                },
                "message_count": 15,
                "last_message_at": "2024-01-01T12:30:00Z",
                "is_active": True,
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:30:00Z"
            }
        }

class ChatHistoryResponse(BaseModel):
    """Chat history response schema"""
    session_id: int = Field(..., description="Session ID")
    messages: List[ChatMessageResponse] = Field(..., description="List of messages")
    total_messages: int = Field(..., description="Total number of messages")
    has_more: bool = Field(..., description="Whether there are more messages")
    next_cursor: Optional[str] = Field(None, description="Cursor for next page")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": 456,
                "messages": [],
                "total_messages": 15,
                "has_more": False,
                "next_cursor": None
            }
        }

class ChatSearchQuery(BaseModel):
    """Chat search query schema"""
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    session_id: Optional[int] = Field(None, description="Limit search to specific session")
    message_type: Optional[MessageType] = Field(None, description="Filter by message type")
    date_from: Optional[datetime] = Field(None, description="Search from date")
    date_to: Optional[datetime] = Field(None, description="Search to date")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum results to return")
    offset: int = Field(default=0, ge=0, description="Results offset")

    @field_validator('query')
    def validate_query(cls, v):
        """Validate search query"""
        if not v.strip():
            raise ValueError("Search query cannot be empty")
        return v.strip()

    @field_validator('date_to')
    def validate_date_range(cls, v, values):
        """Validate date range"""
        if v and 'date_from' in values and values['date_from']:
            if v < values['date_from']:
                raise ValueError("End date must be after start date")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "query": "headache symptoms",
                "session_id": 456,
                "message_type": "user",
                "date_from": "2024-01-01T00:00:00Z",
                "date_to": "2024-01-31T23:59:59Z",
                "limit": 20,
                "offset": 0
            }
        }

class ChatAnalytics(BaseModel):
    """Chat analytics schema"""
    session_id: int = Field(..., description="Session ID")
    total_messages: int = Field(..., description="Total messages")
    user_messages: int = Field(..., description="User messages count")
    assistant_messages: int = Field(..., description="Assistant messages count")
    system_messages: int = Field(..., description="System messages count")
    average_response_time: Optional[float] = Field(None, description="Average response time in seconds")
    session_duration: Optional[float] = Field(None, description="Session duration in minutes")
    topics_discussed: List[str] = Field(default_factory=list, description="Topics discussed")
    sentiment_score: Optional[float] = Field(None, ge=-1.0, le=1.0, description="Overall sentiment score")
    satisfaction_score: Optional[float] = Field(None, ge=1.0, le=5.0, description="User satisfaction score")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": 456,
                "total_messages": 15,
                "user_messages": 8,
                "assistant_messages": 6,
                "system_messages": 1,
                "average_response_time": 2.5,
                "session_duration": 45.2,
                "topics_discussed": ["headache", "symptoms", "treatment"],
                "sentiment_score": 0.3,
                "satisfaction_score": 4.2
            }
        }

class MessageFeedback(BaseModel):
    """Message feedback schema"""
    message_id: int = Field(..., description="Message ID")
    user_id: int = Field(..., description="User ID")
    rating: int = Field(..., ge=1, le=5, description="Feedback rating (1-5)")
    feedback_type: str = Field(..., pattern="^(helpful|unhelpful|accurate|inaccurate|relevant|irrelevant)$", description="Feedback type")
    comment: Optional[str] = Field(None, max_length=500, description="Feedback comment")
    tags: Optional[List[str]] = Field(default_factory=list, description="Feedback tags")

    @field_validator('comment')
    def validate_comment(cls, v):
        """Validate feedback comment"""
        if v is not None and not v.strip():
            raise ValueError("Feedback comment cannot be empty if provided")
        return v.strip() if v else v

    class Config:
        json_schema_extra = {
            "example": {
                "message_id": 789,
                "user_id": 123,
                "rating": 5,
                "feedback_type": "helpful",
                "comment": "Very informative and helpful response",
                "tags": ["helpful", "informative", "accurate"]
            }
        }

class ConversationSummary(BaseModel):
    """Conversation summary schema"""
    session_id: int = Field(..., description="Session ID")
    summary: str = Field(..., max_length=2000, description="Conversation summary")
    key_points: List[str] = Field(..., description="Key points from conversation")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")
    follow_up_actions: List[str] = Field(default_factory=list, description="Follow-up actions")
    medical_notes: Optional[str] = Field(None, max_length=1000, description="Medical notes")
    risk_level: Optional[str] = Field(None, pattern="^(low|medium|high)$", description="Risk level assessment")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Summary generation timestamp")

    @field_validator('summary')
    def validate_summary(cls, v):
        """Validate summary content"""
        if not v.strip():
            raise ValueError("Summary cannot be empty")
        return v.strip()

    @field_validator('key_points')
    def validate_key_points(cls, v):
        """Validate key points"""
        if not v:
            raise ValueError("At least one key point must be provided")
        return [point.strip() for point in v if point.strip()]

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": 456,
                "summary": "Patient reported persistent headaches for one week with moderate severity. Discussed potential causes and recommended lifestyle changes.",
                "key_points": [
                    "Headaches for 1 week",
                    "Moderate severity",
                    "No previous history",
                    "Stress-related triggers identified"
                ],
                "recommendations": [
                    "Reduce screen time",
                    "Improve sleep hygiene",
                    "Practice stress management",
                    "Monitor headache patterns"
                ],
                "follow_up_actions": [
                    "Schedule follow-up in 1 week",
                    "Keep headache diary",
                    "Contact if symptoms worsen"
                ],
                "medical_notes": "No red flags identified. Recommend conservative management initially.",
                "risk_level": "low",
                "generated_at": "2024-01-01T12:30:00Z"
            }
        } 
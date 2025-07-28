"""
AI Processing Pipeline Router
FastAPI router for multi-modal AI processing including text analysis, image analysis, and conversation memory
"""

import time
import logging
import base64
from typing import List, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import HTTPBearer

from app.schemas.enhanced_health_schemas import (
    TextProcessingRequest, TextProcessingResponse, ProcessingType,
    ImageProcessingRequest, ImageAnalysisResponse, ImageType,
    DocumentProcessingRequest, ConversationMemoryRequest, ConversationMemoryResponse
)
from app.services.enhanced.ai_processing_pipeline import (
    get_ai_processing_pipeline, ProcessingResult, ImageAnalysisResult
)
from app.utils.auth_middleware import get_current_user
from app.models.user import User
from app.config import settings

logger = logging.getLogger(__name__)
security = HTTPBearer()

router = APIRouter(prefix="/ai-processing", tags=["AI Processing Pipeline"])

# Initialize AI processing pipeline
ai_pipeline = get_ai_processing_pipeline(
    openai_api_key=settings.openai_api_key,
    computer_vision_api_key=getattr(settings, 'COMPUTER_VISION_API_KEY', None)
)

@router.post("/text", response_model=TextProcessingResponse)
async def process_text(
    request: TextProcessingRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Process text with advanced NLP capabilities
    
    Supports:
    - Medical text analysis with entity extraction
    - Medical terminology identification
    - Context generation for medical queries
    - Medical content classification
    """
    try:
        start_time = time.time()
        
        # Process text
        result = await ai_pipeline.process_text(
            text=request.text,
            processing_type=request.processing_type
        )
        
        processing_time = time.time() - start_time
        
        logger.info(f"Text processing completed for user {current_user.id} in {processing_time:.3f}s")
        
        return TextProcessingResponse(
            content=result.content,
            confidence=result.confidence,
            processing_type=result.processing_type,
            metadata=result.metadata,
            processing_time=result.processing_time,
            model_used=result.model_used
        )
        
    except Exception as e:
        logger.error(f"Error in text processing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Text processing failed: {str(e)}"
        )

@router.post("/image", response_model=ImageAnalysisResponse)
async def process_image(
    request: ImageProcessingRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Process images with computer vision capabilities
    
    Supports:
    - Medical image analysis (X-rays, MRIs, etc.)
    - Document OCR and text extraction
    - General image analysis and description
    - Object detection and medical findings identification
    """
    try:
        start_time = time.time()
        
        # Decode base64 image data
        try:
            image_data = base64.b64decode(request.image_data)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid image data format: {str(e)}"
            )
        
        # Process image
        result = await ai_pipeline.process_image(
            image_data=image_data,
            image_type=request.image_type
        )
        
        processing_time = time.time() - start_time
        
        logger.info(f"Image processing completed for user {current_user.id} in {processing_time:.3f}s")
        
        return ImageAnalysisResponse(
            description=result.description,
            detected_objects=result.detected_objects,
            medical_findings=result.medical_findings,
            confidence=result.confidence,
            bounding_boxes=result.bounding_boxes,
            metadata=result.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in image processing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image processing failed: {str(e)}"
        )

@router.post("/image/upload", response_model=ImageAnalysisResponse)
async def process_uploaded_image(
    file: UploadFile = File(...),
    image_type: ImageType = ImageType.MEDICAL_SCAN,
    current_user: User = Depends(get_current_user)
):
    """
    Process uploaded image file
    
    Supports various image formats: PNG, JPG, JPEG, etc.
    """
    try:
        start_time = time.time()
        
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image"
            )
        
        # Read image data
        image_data = await file.read()
        
        # Process image
        result = await ai_pipeline.process_image(
            image_data=image_data,
            image_type=image_type
        )
        
        processing_time = time.time() - start_time
        
        logger.info(f"Uploaded image processing completed for user {current_user.id} in {processing_time:.3f}s")
        
        return ImageAnalysisResponse(
            description=result.description,
            detected_objects=result.detected_objects,
            medical_findings=result.medical_findings,
            confidence=result.confidence,
            bounding_boxes=result.bounding_boxes,
            metadata=result.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in uploaded image processing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image processing failed: {str(e)}"
        )

@router.post("/document", response_model=TextProcessingResponse)
async def process_document(
    request: DocumentProcessingRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Process documents with OCR and analysis
    
    Supports:
    - PDF text extraction
    - Image-based document OCR
    - Medical document analysis
    - Content classification and entity extraction
    """
    try:
        start_time = time.time()
        
        # Decode base64 document data
        try:
            document_data = base64.b64decode(request.document_data)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid document data format: {str(e)}"
            )
        
        # Process document
        result = await ai_pipeline.process_document(
            document_data=document_data,
            file_type=request.file_type
        )
        
        processing_time = time.time() - start_time
        
        logger.info(f"Document processing completed for user {current_user.id} in {processing_time:.3f}s")
        
        return TextProcessingResponse(
            content=result.content,
            confidence=result.confidence,
            processing_type=result.processing_type,
            metadata=result.metadata,
            processing_time=result.processing_time,
            model_used=result.model_used
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in document processing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document processing failed: {str(e)}"
        )

@router.post("/document/upload", response_model=TextProcessingResponse)
async def process_uploaded_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Process uploaded document file
    
    Supports: PDF, PNG, JPG, JPEG, etc.
    """
    try:
        start_time = time.time()
        
        # Validate file type
        allowed_types = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg']
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_types)}"
            )
        
        # Read document data
        document_data = await file.read()
        
        # Determine file type
        file_type = file.filename.split('.')[-1].lower() if '.' in file.filename else 'pdf'
        
        # Process document
        result = await ai_pipeline.process_document(
            document_data=document_data,
            file_type=file_type
        )
        
        processing_time = time.time() - start_time
        
        logger.info(f"Uploaded document processing completed for user {current_user.id} in {processing_time:.3f}s")
        
        return TextProcessingResponse(
            content=result.content,
            confidence=result.confidence,
            processing_type=result.processing_type,
            metadata=result.metadata,
            processing_time=result.processing_time,
            model_used=result.model_used
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in uploaded document processing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document processing failed: {str(e)}"
        )

@router.post("/conversation/memory", response_model=ConversationMemoryResponse)
async def manage_conversation_memory(
    request: ConversationMemoryRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Manage conversation memory for context-aware responses
    
    Actions:
    - add: Add message to conversation memory
    - get: Retrieve conversation memory
    - update: Update conversation memory
    - clear: Clear conversation memory
    """
    try:
        # Verify user owns the conversation
        if request.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to conversation memory"
            )
        
        # Manage conversation memory
        memory = await ai_pipeline.manage_conversation_memory(
            conversation_id=request.conversation_id,
            user_id=request.user_id,
            message=request.message,
            action=request.action
        )
        
        logger.info(f"Conversation memory {request.action} completed for user {current_user.id}")
        
        return ConversationMemoryResponse(
            conversation_id=memory.conversation_id,
            user_id=memory.user_id,
            messages=memory.messages,
            context_summary=memory.context_summary,
            medical_context=memory.medical_context,
            last_updated=memory.last_updated,
            memory_score=memory.memory_score
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in conversation memory management: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Conversation memory management failed: {str(e)}"
        )

@router.get("/conversation/memory/{conversation_id}", response_model=ConversationMemoryResponse)
async def get_conversation_memory(
    conversation_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get conversation memory by ID
    """
    try:
        memory = await ai_pipeline.manage_conversation_memory(
            conversation_id=conversation_id,
            user_id=current_user.id,
            message={},
            action="get"
        )
        
        return ConversationMemoryResponse(
            conversation_id=memory.conversation_id,
            user_id=memory.user_id,
            messages=memory.messages,
            context_summary=memory.context_summary,
            medical_context=memory.medical_context,
            last_updated=memory.last_updated,
            memory_score=memory.memory_score
        )
        
    except Exception as e:
        logger.error(f"Error getting conversation memory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve conversation memory: {str(e)}"
        )

@router.delete("/conversation/memory/{conversation_id}")
async def clear_conversation_memory(
    conversation_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Clear conversation memory
    """
    try:
        await ai_pipeline.manage_conversation_memory(
            conversation_id=conversation_id,
            user_id=current_user.id,
            message={},
            action="clear"
        )
        
        logger.info(f"Conversation memory cleared for user {current_user.id}: {conversation_id}")
        
        return {"message": "Conversation memory cleared successfully"}
        
    except Exception as e:
        logger.error(f"Error clearing conversation memory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear conversation memory: {str(e)}"
        )

@router.post("/conversation/memory/cleanup")
async def cleanup_old_memories(
    current_user: User = Depends(get_current_user)
):
    """
    Clean up old conversation memories (admin function)
    """
    try:
        # Check if user has admin privileges (simplified check)
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required"
            )
        
        cleaned_count = await ai_pipeline.cleanup_old_memories()
        
        logger.info(f"Memory cleanup completed by admin {current_user.id}: {cleaned_count} memories removed")
        
        return {
            "message": f"Memory cleanup completed",
            "cleaned_count": cleaned_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in memory cleanup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Memory cleanup failed: {str(e)}"
        )

@router.get("/capabilities")
async def get_ai_capabilities():
    """
    Get available AI processing capabilities
    """
    return {
        "text_processing": {
            "medical_text_analysis": "Extract medical entities and terminology",
            "context_generation": "Generate context-aware medical information",
            "medical_classification": "Classify medical content types",
            "entity_extraction": "Extract medical entities and relationships"
        },
        "image_processing": {
            "medical_image_analysis": "Analyze medical images (X-rays, MRIs, etc.)",
            "document_ocr": "Extract text from document images",
            "object_detection": "Detect objects in medical images",
            "image_description": "Generate detailed image descriptions"
        },
        "document_processing": {
            "pdf_extraction": "Extract text from PDF documents",
            "ocr_processing": "OCR for image-based documents",
            "medical_analysis": "Analyze medical document content",
            "content_classification": "Classify document content types"
        },
        "conversation_memory": {
            "memory_management": "Manage conversation context and history",
            "medical_context": "Extract medical context from conversations",
            "context_summarization": "Generate conversation summaries",
            "memory_scoring": "Score conversation importance"
        },
        "supported_formats": {
            "text": ["plain text", "markdown"],
            "images": ["PNG", "JPG", "JPEG", "BMP"],
            "documents": ["PDF", "PNG", "JPG", "JPEG"]
        }
    }

@router.get("/health")
async def ai_pipeline_health_check():
    """
    Health check endpoint for AI processing pipeline
    """
    try:
        # Test basic functionality
        test_result = await ai_pipeline.process_text(
            text="Test medical query",
            processing_type=ProcessingType.TEXT_ANALYSIS
        )
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "text_processing": "available",
            "image_processing": "available" if ai_pipeline.medical_image_classifier else "limited",
            "document_processing": "available",
            "conversation_memory": "available",
            "test_result": "successful"
        }
        
    except Exception as e:
        logger.error(f"AI pipeline health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI processing pipeline unavailable: {str(e)}"
        ) 
"""
Advanced AI Processing Pipeline
Multi-modal AI integration, medical image analysis, and enhanced NLP capabilities
"""

import asyncio
import logging
import base64
import io
import json
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import hashlib
import tempfile
import os

import aiohttp
import numpy as np
from PIL import Image
import cv2
import pytesseract
from transformers import pipeline, AutoTokenizer, AutoModel
import torch
from openai import AsyncOpenAI
import fitz  # PyMuPDF

from app.exceptions.external_api_exceptions import ExternalAPIError
from app.utils.encryption_utils import field_encryption

logger = logging.getLogger(__name__)

class ProcessingType(str, Enum):
    """AI processing type enumeration"""
    TEXT_ANALYSIS = "text_analysis"
    IMAGE_ANALYSIS = "image_analysis"
    DOCUMENT_OCR = "document_ocr"
    MEDICAL_IMAGE = "medical_image"
    CONVERSATION_MEMORY = "conversation_memory"
    CONTEXT_GENERATION = "context_generation"

class ImageType(str, Enum):
    """Image type enumeration"""
    MEDICAL_SCAN = "medical_scan"
    DOCUMENT = "document"
    PHOTO = "photo"
    DIAGRAM = "diagram"
    CHART = "chart"

class AnalysisConfidence(str, Enum):
    """Analysis confidence levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class ProcessingResult:
    """AI processing result"""
    content: str
    confidence: float
    processing_type: ProcessingType
    metadata: Dict[str, Any]
    processing_time: float
    model_used: str

@dataclass
class ImageAnalysisResult:
    """Medical image analysis result"""
    description: str
    detected_objects: List[str]
    medical_findings: List[str]
    confidence: AnalysisConfidence
    bounding_boxes: List[Dict[str, Any]]
    metadata: Dict[str, Any]

@dataclass
class ConversationMemory:
    """Conversation memory structure"""
    conversation_id: str
    user_id: int
    messages: List[Dict[str, Any]]
    context_summary: str
    medical_context: Dict[str, Any]
    last_updated: datetime
    memory_score: float

class AIProcessingPipeline:
    """Advanced AI processing pipeline for multi-modal medical analysis"""
    
    def __init__(self, openai_api_key: str, 
                 computer_vision_api_key: Optional[str] = None,
                 max_conversation_length: int = 50,
                 memory_retention_days: int = 30):
        self.openai_client = AsyncOpenAI(api_key=openai_api_key)
        self.computer_vision_api_key = computer_vision_api_key
        
        # Conversation memory settings
        self.max_conversation_length = max_conversation_length
        self.memory_retention_days = memory_retention_days
        
        # Initialize NLP models
        self._initialize_nlp_models()
        
        # Initialize computer vision models
        self._initialize_cv_models()
        
        # Conversation memory storage
        self.conversation_memories: Dict[str, ConversationMemory] = {}
        
        logger.info("AI Processing Pipeline initialized successfully")
    
    def _initialize_nlp_models(self):
        """Initialize NLP models for medical text processing"""
        try:
            # Medical NER model for entity extraction
            self.medical_ner = pipeline(
                "ner",
                model="emilyalsentzer/Bio_ClinicalBERT",
                aggregation_strategy="simple"
            )
            
            # Medical text classification
            self.medical_classifier = pipeline(
                "text-classification",
                model="microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract"
            )
            
            # Medical question answering
            self.medical_qa = pipeline(
                "question-answering",
                model="microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract"
            )
            
            logger.info("NLP models initialized successfully")
            
        except Exception as e:
            logger.warning(f"Could not initialize some NLP models: {e}")
            self.medical_ner = None
            self.medical_classifier = None
            self.medical_qa = None
    
    def _initialize_cv_models(self):
        """Initialize computer vision models for medical image analysis"""
        try:
            # Medical image classification
            self.medical_image_classifier = pipeline(
                "image-classification",
                model="microsoft/BiomedCLIP-PubMedBERT_256-vit_base_patch16_224"
            )
            
            # Object detection for medical images
            self.medical_object_detector = pipeline(
                "object-detection",
                model="facebook/detr-resnet-50"
            )
            
            logger.info("Computer vision models initialized successfully")
            
        except Exception as e:
            logger.warning(f"Could not initialize some CV models: {e}")
            self.medical_image_classifier = None
            self.medical_object_detector = None
    
    async def process_text(self, text: str, processing_type: ProcessingType = ProcessingType.TEXT_ANALYSIS) -> ProcessingResult:
        """Process text with advanced NLP capabilities"""
        start_time = datetime.utcnow()
        
        try:
            if processing_type == ProcessingType.TEXT_ANALYSIS:
                result = await self._analyze_medical_text(text)
            elif processing_type == ProcessingType.CONTEXT_GENERATION:
                result = await self._generate_context(text)
            else:
                raise ExternalAPIError(f"Unsupported text processing type: {processing_type}")
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return ProcessingResult(
                content=result['content'],
                confidence=result['confidence'],
                processing_type=processing_type,
                metadata=result['metadata'],
                processing_time=processing_time,
                model_used=result['model_used']
            )
            
        except Exception as e:
            logger.error(f"Error processing text: {e}")
            raise ExternalAPIError(f"Text processing failed: {str(e)}")
    
    async def _analyze_medical_text(self, text: str) -> Dict[str, Any]:
        """Analyze medical text with advanced NLP"""
        results = {
            'content': text,
            'confidence': 0.0,
            'metadata': {},
            'model_used': 'medical_nlp_pipeline'
        }
        
        # Extract medical entities
        if self.medical_ner:
            try:
                entities = self.medical_ner(text)
                results['metadata']['entities'] = entities
                results['confidence'] += 0.3
            except Exception as e:
                logger.warning(f"NER processing failed: {e}")
        
        # Classify medical content
        if self.medical_classifier:
            try:
                classification = self.medical_classifier(text)
                results['metadata']['classification'] = classification
                results['confidence'] += 0.2
            except Exception as e:
                logger.warning(f"Classification failed: {e}")
        
        # Extract medical terminology
        medical_terms = self._extract_medical_terminology(text)
        results['metadata']['medical_terms'] = medical_terms
        results['confidence'] += 0.2
        
        # Generate medical context
        context = await self._generate_medical_context(text, medical_terms)
        results['metadata']['medical_context'] = context
        results['confidence'] += 0.3
        
        return results
    
    async def _generate_context(self, text: str) -> Dict[str, Any]:
        """Generate context-aware content"""
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a medical AI assistant. Generate context-aware medical information based on the input."},
                    {"role": "user", "content": text}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            
            return {
                'content': content,
                'confidence': 0.8,
                'metadata': {'generated_context': True},
                'model_used': 'gpt-4'
            }
            
        except Exception as e:
            logger.error(f"Context generation failed: {e}")
            raise ExternalAPIError(f"Context generation failed: {str(e)}")
    
    def _extract_medical_terminology(self, text: str) -> List[str]:
        """Extract medical terminology from text"""
        medical_terms = []
        
        # Basic medical terminology patterns
        medical_patterns = [
            r'\b(diabetes|hypertension|asthma|arthritis|depression|anxiety)\b',
            r'\b(aspirin|ibuprofen|acetaminophen|insulin|antibiotics)\b',
            r'\b(blood pressure|heart rate|temperature|weight|height)\b',
            r'\b(symptoms|diagnosis|treatment|medication|prescription)\b'
        ]
        
        import re
        for pattern in medical_patterns:
            matches = re.findall(pattern, text.lower())
            medical_terms.extend(matches)
        
        return list(set(medical_terms))
    
    async def _generate_medical_context(self, text: str, medical_terms: List[str]) -> Dict[str, Any]:
        """Generate medical context from text and terms"""
        context = {
            'medical_terms': medical_terms,
            'severity_level': 'unknown',
            'urgency': 'normal',
            'specialties': [],
            'recommendations': []
        }
        
        # Determine severity based on medical terms
        urgent_terms = ['emergency', 'severe', 'critical', 'acute', 'pain']
        if any(term in text.lower() for term in urgent_terms):
            context['urgency'] = 'high'
        
        # Identify medical specialties
        specialty_keywords = {
            'cardiology': ['heart', 'cardiac', 'cardiovascular'],
            'endocrinology': ['diabetes', 'thyroid', 'hormone'],
            'neurology': ['brain', 'nerve', 'neurological'],
            'oncology': ['cancer', 'tumor', 'malignant']
        }
        
        for specialty, keywords in specialty_keywords.items():
            if any(keyword in text.lower() for keyword in keywords):
                context['specialties'].append(specialty)
        
        return context
    
    async def process_image(self, image_data: bytes, image_type: ImageType = ImageType.MEDICAL_SCAN) -> ImageAnalysisResult:
        """Process medical images with computer vision"""
        start_time = datetime.utcnow()
        
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            if image_type == ImageType.MEDICAL_SCAN:
                result = await self._analyze_medical_image(image)
            elif image_type == ImageType.DOCUMENT:
                result = await self._process_document_image(image)
            else:
                result = await self._analyze_general_image(image)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            result.metadata['processing_time'] = processing_time
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            raise ExternalAPIError(f"Image processing failed: {str(e)}")
    
    async def _analyze_medical_image(self, image: Image.Image) -> ImageAnalysisResult:
        """Analyze medical images (X-rays, MRIs, etc.)"""
        description = "Medical image analysis"
        detected_objects = []
        medical_findings = []
        confidence = AnalysisConfidence.MEDIUM
        bounding_boxes = []
        
        try:
            # Use medical image classifier
            if self.medical_image_classifier:
                classification = self.medical_image_classifier(image)
                medical_findings = [item['label'] for item in classification[:3]]
                confidence = AnalysisConfidence.HIGH if classification[0]['score'] > 0.8 else AnalysisConfidence.MEDIUM
            
            # Use object detector for anatomical structures
            if self.medical_object_detector:
                detection = self.medical_object_detector(image)
                detected_objects = [item['label'] for item in detection]
                bounding_boxes = [
                    {
                        'label': item['label'],
                        'score': item['score'],
                        'box': item['box']
                    }
                    for item in detection
                ]
            
            # Generate description using OpenAI Vision
            description = await self._generate_image_description(image, "medical scan")
            
        except Exception as e:
            logger.warning(f"Medical image analysis failed: {e}")
            description = "Unable to analyze medical image"
        
        return ImageAnalysisResult(
            description=description,
            detected_objects=detected_objects,
            medical_findings=medical_findings,
            confidence=confidence,
            bounding_boxes=bounding_boxes,
            metadata={'image_type': 'medical_scan'}
        )
    
    async def _process_document_image(self, image: Image.Image) -> ImageAnalysisResult:
        """Process document images with OCR"""
        try:
            # Convert to OpenCV format for better OCR
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Preprocess image for better OCR
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            
            # Extract text using OCR
            text = pytesseract.image_to_string(thresh)
            
            # Extract medical entities from OCR text
            medical_terms = self._extract_medical_terminology(text)
            
            return ImageAnalysisResult(
                description=f"Document containing medical information: {text[:200]}...",
                detected_objects=["text", "document"],
                medical_findings=medical_terms,
                confidence=AnalysisConfidence.HIGH if len(text) > 50 else AnalysisConfidence.MEDIUM,
                bounding_boxes=[],
                metadata={
                    'image_type': 'document',
                    'ocr_text': text,
                    'text_length': len(text)
                }
            )
            
        except Exception as e:
            logger.error(f"Document OCR failed: {e}")
            return ImageAnalysisResult(
                description="Unable to process document image",
                detected_objects=[],
                medical_findings=[],
                confidence=AnalysisConfidence.LOW,
                bounding_boxes=[],
                metadata={'error': str(e)}
            )
    
    async def _analyze_general_image(self, image: Image.Image) -> ImageAnalysisResult:
        """Analyze general images"""
        try:
            # Use OpenAI Vision for general image analysis
            description = await self._generate_image_description(image, "general image")
            
            return ImageAnalysisResult(
                description=description,
                detected_objects=["image"],
                medical_findings=[],
                confidence=AnalysisConfidence.MEDIUM,
                bounding_boxes=[],
                metadata={'image_type': 'general'}
            )
            
        except Exception as e:
            logger.error(f"General image analysis failed: {e}")
            return ImageAnalysisResult(
                description="Unable to analyze image",
                detected_objects=[],
                medical_findings=[],
                confidence=AnalysisConfidence.LOW,
                bounding_boxes=[],
                metadata={'error': str(e)}
            )
    
    async def _generate_image_description(self, image: Image.Image, context: str) -> str:
        """Generate image description using OpenAI Vision"""
        try:
            # Convert image to base64
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Describe this {context} in detail, focusing on any medical or health-related information."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Image description generation failed: {e}")
            return f"Unable to generate description for {context}"
    
    async def process_document(self, document_data: bytes, file_type: str) -> ProcessingResult:
        """Process documents (PDF, images) with OCR and analysis"""
        start_time = datetime.utcnow()
        
        try:
            if file_type.lower() == 'pdf':
                content = await self._extract_pdf_content(document_data)
            else:
                # Treat as image
                image = Image.open(io.BytesIO(document_data))
                ocr_result = await self._process_document_image(image)
                content = ocr_result.metadata.get('ocr_text', '')
            
            # Analyze extracted content
            analysis_result = await self._analyze_medical_text(content)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return ProcessingResult(
                content=content,
                confidence=analysis_result['confidence'],
                processing_type=ProcessingType.DOCUMENT_OCR,
                metadata={
                    'file_type': file_type,
                    'content_length': len(content),
                    'analysis': analysis_result['metadata']
                },
                processing_time=processing_time,
                model_used='document_processing_pipeline'
            )
            
        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            raise ExternalAPIError(f"Document processing failed: {str(e)}")
    
    async def _extract_pdf_content(self, pdf_data: bytes) -> str:
        """Extract text content from PDF"""
        try:
            # Save PDF to temporary file
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(pdf_data)
                temp_file_path = temp_file.name
            
            # Extract text using PyMuPDF
            doc = fitz.open(temp_file_path)
            text_content = ""
            
            for page in doc:
                text_content += page.get_text()
            
            doc.close()
            
            # Clean up temporary file
            os.unlink(temp_file_path)
            
            return text_content
            
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            raise ExternalAPIError(f"PDF content extraction failed: {str(e)}")
    
    async def manage_conversation_memory(self, conversation_id: str, user_id: int, 
                                       message: Dict[str, Any], 
                                       action: str = "add") -> ConversationMemory:
        """Manage conversation memory for context-aware responses"""
        try:
            if action == "add":
                return await self._add_to_conversation_memory(conversation_id, user_id, message)
            elif action == "get":
                return await self._get_conversation_memory(conversation_id)
            elif action == "update":
                return await self._update_conversation_memory(conversation_id, message)
            elif action == "clear":
                return await self._clear_conversation_memory(conversation_id)
            else:
                raise ExternalAPIError(f"Unsupported memory action: {action}")
                
        except Exception as e:
            logger.error(f"Conversation memory management failed: {e}")
            raise ExternalAPIError(f"Memory management failed: {str(e)}")
    
    async def _add_to_conversation_memory(self, conversation_id: str, user_id: int, 
                                        message: Dict[str, Any]) -> ConversationMemory:
        """Add message to conversation memory"""
        if conversation_id not in self.conversation_memories:
            self.conversation_memories[conversation_id] = ConversationMemory(
                conversation_id=conversation_id,
                user_id=user_id,
                messages=[],
                context_summary="",
                medical_context={},
                last_updated=datetime.utcnow(),
                memory_score=0.0
            )
        
        memory = self.conversation_memories[conversation_id]
        memory.messages.append(message)
        
        # Limit conversation length
        if len(memory.messages) > self.max_conversation_length:
            memory.messages = memory.messages[-self.max_conversation_length:]
        
        # Update context summary
        memory.context_summary = await self._generate_conversation_summary(memory.messages)
        
        # Update medical context
        memory.medical_context = await self._extract_conversation_medical_context(memory.messages)
        
        # Update memory score
        memory.memory_score = self._calculate_memory_score(memory)
        memory.last_updated = datetime.utcnow()
        
        return memory
    
    async def _get_conversation_memory(self, conversation_id: str) -> ConversationMemory:
        """Get conversation memory"""
        if conversation_id not in self.conversation_memories:
            raise ExternalAPIError(f"Conversation memory not found: {conversation_id}")
        
        return self.conversation_memories[conversation_id]
    
    async def _update_conversation_memory(self, conversation_id: str, 
                                        updates: Dict[str, Any]) -> ConversationMemory:
        """Update conversation memory"""
        if conversation_id not in self.conversation_memories:
            raise ExternalAPIError(f"Conversation memory not found: {conversation_id}")
        
        memory = self.conversation_memories[conversation_id]
        
        for key, value in updates.items():
            if hasattr(memory, key):
                setattr(memory, key, value)
        
        memory.last_updated = datetime.utcnow()
        return memory
    
    async def _clear_conversation_memory(self, conversation_id: str) -> ConversationMemory:
        """Clear conversation memory"""
        if conversation_id in self.conversation_memories:
            del self.conversation_memories[conversation_id]
        
        return ConversationMemory(
            conversation_id=conversation_id,
            user_id=0,
            messages=[],
            context_summary="",
            medical_context={},
            last_updated=datetime.utcnow(),
            memory_score=0.0
        )
    
    async def _generate_conversation_summary(self, messages: List[Dict[str, Any]]) -> str:
        """Generate conversation summary"""
        try:
            # Combine recent messages
            recent_text = " ".join([
                msg.get('content', '') for msg in messages[-10:]  # Last 10 messages
            ])
            
            if len(recent_text) < 50:
                return "Brief conversation"
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Summarize the key points of this medical conversation in 2-3 sentences."},
                    {"role": "user", "content": recent_text}
                ],
                max_tokens=150,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.warning(f"Conversation summary generation failed: {e}")
            return "Conversation summary unavailable"
    
    async def _extract_conversation_medical_context(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract medical context from conversation"""
        medical_context = {
            'symptoms_mentioned': [],
            'conditions_discussed': [],
            'medications_referenced': [],
            'concerns_raised': [],
            'recommendations_given': []
        }
        
        # Analyze all messages for medical content
        for message in messages:
            content = message.get('content', '')
            medical_terms = self._extract_medical_terminology(content)
            
            # Categorize medical terms
            for term in medical_terms:
                if term in ['fever', 'headache', 'pain', 'fatigue']:
                    medical_context['symptoms_mentioned'].append(term)
                elif term in ['diabetes', 'hypertension', 'asthma']:
                    medical_context['conditions_discussed'].append(term)
                elif term in ['aspirin', 'ibuprofen', 'insulin']:
                    medical_context['medications_referenced'].append(term)
        
        # Remove duplicates
        for key in medical_context:
            medical_context[key] = list(set(medical_context[key]))
        
        return medical_context
    
    def _calculate_memory_score(self, memory: ConversationMemory) -> float:
        """Calculate memory importance score"""
        score = 0.0
        
        # Score based on message count
        score += min(len(memory.messages) / 10.0, 1.0) * 0.3
        
        # Score based on medical content
        medical_terms_count = sum(len(context) for context in memory.medical_context.values())
        score += min(medical_terms_count / 20.0, 1.0) * 0.4
        
        # Score based on recency
        days_since_update = (datetime.utcnow() - memory.last_updated).days
        recency_score = max(0, 1 - (days_since_update / self.memory_retention_days))
        score += recency_score * 0.3
        
        return min(score, 1.0)
    
    async def cleanup_old_memories(self) -> int:
        """Clean up old conversation memories"""
        current_time = datetime.utcnow()
        memories_to_remove = []
        
        for conversation_id, memory in self.conversation_memories.items():
            days_old = (current_time - memory.last_updated).days
            if days_old > self.memory_retention_days:
                memories_to_remove.append(conversation_id)
        
        for conversation_id in memories_to_remove:
            del self.conversation_memories[conversation_id]
        
        logger.info(f"Cleaned up {len(memories_to_remove)} old conversation memories")
        return len(memories_to_remove)

# Global AI processing pipeline instance
ai_processing_pipeline = None

def get_ai_processing_pipeline(openai_api_key: str, 
                             computer_vision_api_key: Optional[str] = None) -> AIProcessingPipeline:
    """Get or create AI processing pipeline instance"""
    global ai_processing_pipeline
    if ai_processing_pipeline is None:
        ai_processing_pipeline = AIProcessingPipeline(openai_api_key, computer_vision_api_key)
    return ai_processing_pipeline 
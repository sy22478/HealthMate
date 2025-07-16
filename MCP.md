# MCP Server with Advanced RAG and Differential Diagnosis

## Overview
This document extends the HealthChat RAG project with a sophisticated MCP (Model Context Protocol) server that implements differential diagnosis capabilities and advanced RAG techniques for superior medical context retrieval.

## Enhanced Architecture

```
User Query
     ↓
Frontend Chat UI
     ↓
FastAPI Backend (Agent with MCP Client)
     ↓
MCP Server for Enhanced RAG:
   • Query Expansion & Rewriting
   • Advanced Chunking Strategies
   • Metadata Filtering & Enrichment
   • Knowledge Graph Integration
   • Reranking Pipeline
     ↓
Differential Diagnosis MCP Server:
   • Symptom Collection & Analysis
   • Condition Scoring & Ranking
   • Multi-turn Diagnostic Flow
     ↓
AI Agent with Deep Thinking
     ↓
LLM with Reasoning Traces
```

## MCP Server Implementation

### 1. Enhanced RAG MCP Server (app/mcp/rag_server.py)

```python
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from sentence_transformers import SentenceTransformer
import numpy as np
from openai import OpenAI
import json

@dataclass
class ChunkMetadata:
    source: str
    title: str
    author: str
    date: str
    credibility_score: float
    medical_specialty: str
    content_type: str  # "symptom", "condition", "treatment", "general"
    entities: List[str]
    relationships: List[Dict[str, str]]

class AdvancedRAGServer:
    def __init__(self, config: Dict):
        self.openai_client = OpenAI(api_key=config['openai_api_key'])
        self.embedding_model = SentenceTransformer('voyage-health-2')  # Domain-specific
        self.reranker = SentenceTransformer('ms-marco-MiniLM-L-6-v2')
        self.vector_store = self._initialize_vector_store(config)
        self.knowledge_graph = self._initialize_knowledge_graph(config)
        
    def expand_query(self, query: str, user_profile: Dict) -> str:
        """Expand query using synonyms, medical terms, and user context"""
        expansion_prompt = f"""
        Expand this medical query with relevant synonyms, medical terminology, and context:
        
        Original Query: {query}
        User Profile: Age {user_profile.get('age', 'N/A')}, Medical Conditions: {user_profile.get('medical_conditions', 'None')}
        
        Provide expanded query terms as comma-separated list:
        """
        
        response = self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": expansion_prompt}],
            max_tokens=200
        )
        
        expanded_terms = response.choices[0].message.content.strip()
        return f"{query} {expanded_terms}"
    
    def rewrite_query(self, query: str, conversation_history: List[Dict]) -> str:
        """Rewrite poor queries for better retrieval"""
        rewrite_prompt = f"""
        Rewrite this query to be more specific and medically accurate for information retrieval:
        
        Original: {query}
        Context: {json.dumps(conversation_history[-3:], indent=2)}
        
        Rewritten query:
        """
        
        response = self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": rewrite_prompt}],
            max_tokens=150
        )
        
        return response.choices[0].message.content.strip()
    
    def advanced_chunk_retrieval(self, query: str, filters: Dict = None, k: int = 10) -> List[Dict]:
        """Advanced chunking with metadata filtering"""
        # Metadata filtering
        filter_query = self._build_metadata_filter(filters) if filters else {}
        
        # Semantic search with expanded query
        expanded_query = self.expand_query(query, filters.get('user_profile', {}))
        
        # Vector search
        query_embedding = self.embedding_model.encode(expanded_query)
        results = self.vector_store.query(
            vector=query_embedding,
            top_k=k * 2,  # Get more for reranking
            filter=filter_query,
            include_metadata=True
        )
        
        # Extract chunks with metadata
        chunks = []
        for match in results.matches:
            chunk_data = {
                'text': match.metadata['text'],
                'score': match.score,
                'metadata': ChunkMetadata(**match.metadata)
            }
            chunks.append(chunk_data)
        
        # Rerank results
        reranked_chunks = self.rerank_chunks(query, chunks)
        
        # Knowledge graph enhancement
        enhanced_chunks = self.enhance_with_knowledge_graph(reranked_chunks)
        
        return enhanced_chunks[:k]
    
    def rerank_chunks(self, query: str, chunks: List[Dict]) -> List[Dict]:
        """Rerank chunks using cross-encoder model"""
        if not chunks:
            return chunks
        
        # Prepare query-document pairs
        pairs = [(query, chunk['text']) for chunk in chunks]
        
        # Get relevance scores
        relevance_scores = self.reranker.predict(pairs)
        
        # Combine with original scores
        for i, chunk in enumerate(chunks):
            chunk['rerank_score'] = relevance_scores[i]
            chunk['combined_score'] = (chunk['score'] + relevance_scores[i]) / 2
        
        # Sort by combined score
        return sorted(chunks, key=lambda x: x['combined_score'], reverse=True)
    
    def enhance_with_knowledge_graph(self, chunks: List[Dict]) -> List[Dict]:
        """Enhance chunks with knowledge graph relationships"""
        enhanced_chunks = []
        
        for chunk in chunks:
            # Extract entities from chunk
            entities = chunk['metadata'].entities
            
            # Query knowledge graph for related entities
            related_entities = self.knowledge_graph.get_related_entities(entities)
            
            # Add contextual information
            chunk['related_entities'] = related_entities
            chunk['relationship_context'] = self._build_relationship_context(entities, related_entities)
            
            enhanced_chunks.append(chunk)
        
        return enhanced_chunks
    
    def _build_metadata_filter(self, filters: Dict) -> Dict:
        """Build metadata filter for vector search"""
        filter_conditions = {}
        
        if 'medical_specialty' in filters:
            filter_conditions['medical_specialty'] = filters['medical_specialty']
        
        if 'content_type' in filters:
            filter_conditions['content_type'] = filters['content_type']
        
        if 'min_credibility' in filters:
            filter_conditions['credibility_score'] = {'$gte': filters['min_credibility']}
        
        if 'date_range' in filters:
            filter_conditions['date'] = {
                '$gte': filters['date_range']['start'],
                '$lte': filters['date_range']['end']
            }
        
        return filter_conditions
```

### 2. Differential Diagnosis MCP Server (app/mcp/diagnosis_server.py)

```python
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json

class DiagnosisUrgency(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EMERGENCY = "emergency"

@dataclass
class DiagnosisResult:
    condition: str
    confidence: float
    urgency: DiagnosisUrgency
    reasoning: str
    supporting_symptoms: List[str]
    contradicting_symptoms: List[str]
    next_questions: List[str]
    recommended_actions: List[str]

class DifferentialDiagnosisServer:
    def __init__(self, config: Dict):
        self.openai_client = OpenAI(api_key=config['openai_api_key'])
        self.rag_server = AdvancedRAGServer(config)
        self.symptom_database = self._load_symptom_database()
        self.emergency_keywords = self._load_emergency_keywords()
        
    def run_differential_diagnosis(self, 
                                 symptoms: List[str], 
                                 age: int,
                                 gender: str,
                                 medical_history: List[str] = None,
                                 current_medications: List[str] = None) -> List[DiagnosisResult]:
        """Run comprehensive differential diagnosis with deep thinking"""
        
        # Step 1: Emergency screening
        emergency_check = self._check_emergency_symptoms(symptoms)
        if emergency_check['is_emergency']:
            return [DiagnosisResult(
                condition="Emergency Medical Attention Required",
                confidence=0.95,
                urgency=DiagnosisUrgency.EMERGENCY,
                reasoning=emergency_check['reasoning'],
                supporting_symptoms=emergency_check['emergency_symptoms'],
                contradicting_symptoms=[],
                next_questions=[],
                recommended_actions=["Seek immediate medical attention", "Call emergency services"]
            )]
        
        # Step 2: Gather relevant medical context using RAG
        context = self._gather_diagnostic_context(symptoms, age, gender, medical_history)
        
        # Step 3: Generate differential diagnosis with reasoning
        diagnosis_results = self._generate_differential_with_reasoning(
            symptoms, age, gender, medical_history, current_medications, context
        )
        
        # Step 4: Validate and rank results
        validated_results = self._validate_and_rank_diagnoses(diagnosis_results)
        
        return validated_results
    
    def _check_emergency_symptoms(self, symptoms: List[str]) -> Dict:
        """Check for emergency symptoms requiring immediate attention"""
        emergency_symptoms = []
        
        for symptom in symptoms:
            if any(keyword in symptom.lower() for keyword in self.emergency_keywords):
                emergency_symptoms.append(symptom)
        
        is_emergency = len(emergency_symptoms) > 0
        
        reasoning = f"Emergency symptoms detected: {', '.join(emergency_symptoms)}" if is_emergency else "No emergency symptoms detected"
        
        return {
            'is_emergency': is_emergency,
            'emergency_symptoms': emergency_symptoms,
            'reasoning': reasoning
        }
    
    def _gather_diagnostic_context(self, symptoms: List[str], age: int, gender: str, medical_history: List[str]) -> str:
        """Gather relevant medical context using advanced RAG"""
        
        # Build comprehensive query
        query = f"differential diagnosis {' '.join(symptoms)} age {age} {gender}"
        
        # Set up filters for targeted retrieval
        filters = {
            'content_type': 'condition',
            'medical_specialty': 'internal_medicine',
            'min_credibility': 0.8,
            'user_profile': {
                'age': age,
                'gender': gender,
                'medical_conditions': medical_history or []
            }
        }
        
        # Retrieve relevant chunks
        relevant_chunks = self.rag_server.advanced_chunk_retrieval(query, filters, k=15)
        
        # Build context string
        context = "Relevant medical information for differential diagnosis:\n\n"
        
        for chunk in relevant_chunks:
            context += f"Source: {chunk['metadata'].source} (Credibility: {chunk['metadata'].credibility_score})\n"
            context += f"Content: {chunk['text']}\n"
            context += f"Related entities: {', '.join(chunk.get('related_entities', []))}\n\n"
        
        return context
    
    def _generate_differential_with_reasoning(self, 
                                            symptoms: List[str], 
                                            age: int, 
                                            gender: str,
                                            medical_history: List[str],
                                            current_medications: List[str],
                                            context: str) -> List[DiagnosisResult]:
        """Generate differential diagnosis with step-by-step reasoning"""
        
        reasoning_prompt = f"""
        As a medical diagnostic assistant, provide a differential diagnosis with detailed reasoning.
        
        PATIENT INFORMATION:
        - Age: {age}
        - Gender: {gender}
        - Symptoms: {', '.join(symptoms)}
        - Medical History: {', '.join(medical_history) if medical_history else 'None'}
        - Current Medications: {', '.join(current_medications) if current_medications else 'None'}
        
        MEDICAL CONTEXT:
        {context}
        
        INSTRUCTIONS:
        1. Think through each symptom systematically
        2. Consider age, gender, and medical history
        3. Provide top 5 differential diagnoses
        4. For each diagnosis, provide:
           - Confidence level (0.0-1.0)
           - Urgency level (low/medium/high/emergency)
           - Step-by-step reasoning
           - Supporting symptoms
           - Contradicting symptoms
           - Next questions to ask
           - Recommended actions
        
        IMPORTANT: Always include medical disclaimers and recommend professional consultation.
        
        Respond in JSON format with the following structure:
        {{
            "diagnoses": [
                {{
                    "condition": "string",
                    "confidence": float,
                    "urgency": "low|medium|high|emergency",
                    "reasoning": "string",
                    "supporting_symptoms": ["string"],
                    "contradicting_symptoms": ["string"],
                    "next_questions": ["string"],
                    "recommended_actions": ["string"]
                }}
            ]
        }}
        """
        
        response = self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": reasoning_prompt}],
            max_tokens=2000,
            temperature=0.3
        )
        
        try:
            result = json.loads(response.choices[0].message.content)
            diagnoses = []
            
            for diag in result['diagnoses']:
                diagnoses.append(DiagnosisResult(
                    condition=diag['condition'],
                    confidence=diag['confidence'],
                    urgency=DiagnosisUrgency(diag['urgency']),
                    reasoning=diag['reasoning'],
                    supporting_symptoms=diag['supporting_symptoms'],
                    contradicting_symptoms=diag['contradicting_symptoms'],
                    next_questions=diag['next_questions'],
                    recommended_actions=diag['recommended_actions']
                ))
            
            return diagnoses
            
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return [DiagnosisResult(
                condition="Analysis Error",
                confidence=0.0,
                urgency=DiagnosisUrgency.LOW,
                reasoning="Unable to process diagnostic analysis",
                supporting_symptoms=[],
                contradicting_symptoms=[],
                next_questions=["Please provide more specific symptoms"],
                recommended_actions=["Consult healthcare provider"]
            )]
    
    def _validate_and_rank_diagnoses(self, diagnoses: List[DiagnosisResult]) -> List[DiagnosisResult]:
        """Validate and rank differential diagnoses"""
        
        # Filter out low-confidence diagnoses
        valid_diagnoses = [d for d in diagnoses if d.confidence >= 0.3]
        
        # Sort by confidence and urgency
        urgency_weights = {
            DiagnosisUrgency.EMERGENCY: 4,
            DiagnosisUrgency.HIGH: 3,
            DiagnosisUrgency.MEDIUM: 2,
            DiagnosisUrgency.LOW: 1
        }
        
        def ranking_score(diagnosis):
            return (diagnosis.confidence * 0.7) + (urgency_weights[diagnosis.urgency] * 0.3)
        
        ranked_diagnoses = sorted(valid_diagnoses, key=ranking_score, reverse=True)
        
        return ranked_diagnoses[:5]  # Return top 5
```

### 3. Enhanced Medical Knowledge Base (app/services/enhanced_knowledge_base.py)

```python
from typing import Dict, List, Any
import spacy
from sentence_transformers import SentenceTransformer
import networkx as nx

class EnhancedMedicalKnowledgeBase:
    def __init__(self, vector_store, config: Dict):
        self.vector_store = vector_store
        self.nlp = spacy.load("en_core_web_sm")
        self.embedding_model = SentenceTransformer('voyage-health-2')
        self.knowledge_graph = nx.DiGraph()
        
    def advanced_document_processing(self, documents: List[Dict]) -> List[Dict]:
        """Process documents with advanced chunking and metadata extraction"""
        processed_docs = []
        
        for doc in documents:
            # Extract metadata
            metadata = self._extract_metadata(doc)
            
            # Advanced chunking
            chunks = self._advanced_chunking(doc['content'])
            
            # Entity extraction and relationship mapping
            entities = self._extract_entities(doc['content'])
            relationships = self._extract_relationships(doc['content'])
            
            # Metadata enrichment
            enriched_chunks = self._enrich_chunks_with_metadata(chunks, metadata, entities, relationships)
            
            processed_docs.extend(enriched_chunks)
        
        return processed_docs
    
    def _extract_metadata(self, document: Dict) -> ChunkMetadata:
        """Extract comprehensive metadata from document"""
        return ChunkMetadata(
            source=document.get('source', 'unknown'),
            title=document.get('title', ''),
            author=document.get('author', ''),
            date=document.get('date', ''),
            credibility_score=self._calculate_credibility_score(document),
            medical_specialty=self._classify_medical_specialty(document['content']),
            content_type=self._classify_content_type(document['content']),
            entities=[],
            relationships=[]
        )
    
    def _advanced_chunking(self, content: str) -> List[str]:
        """Advanced chunking using sentence and paragraph boundaries"""
        doc = self.nlp(content)
        
        chunks = []
        current_chunk = ""
        current_size = 0
        max_chunk_size = 800
        overlap_size = 100
        
        for sent in doc.sents:
            sent_text = sent.text.strip()
            sent_size = len(sent_text)
            
            if current_size + sent_size <= max_chunk_size:
                current_chunk += sent_text + " "
                current_size += sent_size
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                # Start new chunk with overlap
                overlap_text = current_chunk[-overlap_size:] if len(current_chunk) > overlap_size else ""
                current_chunk = overlap_text + sent_text + " "
                current_size = len(current_chunk)
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _extract_entities(self, content: str) -> List[str]:
        """Extract medical entities from content"""
        doc = self.nlp(content)
        entities = []
        
        for ent in doc.ents:
            if ent.label_ in ['PERSON', 'ORG', 'GPE', 'DISEASE', 'SYMPTOM', 'MEDICATION']:
                entities.append(ent.text)
        
        return entities
    
    def _extract_relationships(self, content: str) -> List[Dict[str, str]]:
        """Extract relationships between entities"""
        # Simplified relationship extraction
        relationships = []
        
        # Use pattern matching for common medical relationships
        patterns = [
            r"(\w+) causes (\w+)",
            r"(\w+) is associated with (\w+)",
            r"(\w+) treats (\w+)",
            r"(\w+) is a symptom of (\w+)"
        ]
        
        import re
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                relationships.append({
                    'subject': match[0],
                    'predicate': 'causes' if 'causes' in pattern else 'related_to',
                    'object': match[1]
                })
        
        return relationships
    
    def _calculate_credibility_score(self, document: Dict) -> float:
        """Calculate credibility score based on source"""
        source_scores = {
            'Mayo Clinic': 0.95,
            'CDC': 0.98,
            'NIH': 0.97,
            'WHO': 0.96,
            'WebMD': 0.75,
            'Healthline': 0.70,
            'Wikipedia': 0.60
        }
        
        source = document.get('source', '').lower()
        
        for trusted_source, score in source_scores.items():
            if trusted_source.lower() in source:
                return score
        
        return 0.50  # Default score for unknown sources
    
    def _classify_medical_specialty(self, content: str) -> str:
        """Classify medical specialty based on content"""
        specialties = {
            'cardiology': ['heart', 'cardiac', 'cardiovascular', 'arrhythmia'],
            'neurology': ['brain', 'neurological', 'seizure', 'stroke'],
            'dermatology': ['skin', 'rash', 'dermatitis', 'acne'],
            'endocrinology': ['diabetes', 'hormone', 'thyroid', 'insulin'],
            'gastroenterology': ['stomach', 'digestive', 'intestinal', 'liver'],
            'pulmonology': ['lung', 'respiratory', 'breathing', 'asthma'],
            'orthopedics': ['bone', 'joint', 'fracture', 'muscle'],
            'internal_medicine': ['general', 'internal', 'primary care']
        }
        
        content_lower = content.lower()
        specialty_scores = {}
        
        for specialty, keywords in specialties.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            specialty_scores[specialty] = score
        
        return max(specialty_scores, key=specialty_scores.get) if specialty_scores else 'internal_medicine'
    
    def _classify_content_type(self, content: str) -> str:
        """Classify content type"""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['symptom', 'sign', 'manifestation']):
            return 'symptom'
        elif any(word in content_lower for word in ['condition', 'disease', 'disorder']):
            return 'condition'
        elif any(word in content_lower for word in ['treatment', 'therapy', 'medication']):
            return 'treatment'
        else:
            return 'general'
```

### 4. Integration with FastAPI (app/routers/enhanced_chat.py)

```python
from fastapi import APIRouter, Depends, HTTPException
from app.mcp.rag_server import AdvancedRAGServer
from app.mcp.diagnosis_server import DifferentialDiagnosisServer
from app.services.auth import get_current_user
from typing import Dict, List

router = APIRouter()

@router.post("/enhanced_chat")
async def enhanced_chat(
    payload: Dict,
    current_user: User = Depends(get_current_user)
):
    """Enhanced chat with MCP servers"""
    
    message = payload.get('message', '')
    chat_type = payload.get('type', 'general')  # 'general' or 'diagnosis'
    
    # Initialize MCP servers
    config = {
        'openai_api_key': settings.OPENAI_API_KEY,
        'pinecone_api_key': settings.PINECONE_API_KEY,
        'pinecone_environment': settings.PINECONE_ENVIRONMENT
    }
    
    if chat_type == 'diagnosis':
        # Use differential diagnosis server
        diagnosis_server = DifferentialDiagnosisServer(config)
        
        symptoms = payload.get('symptoms', [])
        age = current_user.age
        gender = payload.get('gender', 'unknown')
        medical_history = json.loads(current_user.medical_conditions) if current_user.medical_conditions else []
        
        results = diagnosis_server.run_differential_diagnosis(
            symptoms=symptoms,
            age=age,
            gender=gender,
            medical_history=medical_history
        )
        
        return {
            'response': format_diagnosis_response(results),
            'diagnosis_results': [result.__dict__ for result in results],
            'type': 'diagnosis'
        }
    
    else:
        # Use enhanced RAG server
        rag_server = AdvancedRAGServer(config)
        
        # Get user profile
        user_profile = {
            'age': current_user.age,
            'medical_conditions': json.loads(current_user.medical_conditions) if current_user.medical_conditions else []
        }
        
        # Retrieve enhanced context
        relevant_chunks = rag_server.advanced_chunk_retrieval(
            query=message,
            filters={'user_profile': user_profile},
            k=10
        )
        
        # Generate response with context
        response = generate_contextual_response(message, relevant_chunks, user_profile)
        
        return {
            'response': response,
            'sources': [chunk['metadata'].source for chunk in relevant_chunks],
            'type': 'general'
        }

def format_diagnosis_response(results: List[DiagnosisResult]) -> str:
    """Format diagnosis results for user display"""
    if not results:
        return "I couldn't generate a differential diagnosis. Please consult a healthcare provider."
    
    response = "Based on the symptoms provided, here are the possible conditions to consider:\n\n"
    
    for i, result in enumerate(results, 1):
        response += f"{i}. **{result.condition}** (Confidence: {result.confidence:.0%})\n"
        response += f"   Urgency: {result.urgency.value.upper()}\n"
        response += f"   Reasoning: {result.reasoning}\n"
        
        if result.next_questions:
            response += f"   Additional questions: {', '.join(result.next_questions)}\n"
        
        if result.recommended_actions:
            response += f"   Recommended actions: {', '.join(result.recommended_actions)}\n"
        
        response += "\n"
    
    response += "⚠️ **Important Disclaimer**: This analysis is for informational purposes only and should not replace professional medical advice. Please consult with a healthcare provider for proper diagnosis and treatment."
    
    return response
```

## Implementation Steps

1. **Install Additional Dependencies**
```bash
pip install sentence-transformers spacy networkx
python -m spacy download en_core_web_sm
```

2. **Set Up Enhanced Vector Store**
- Configure Pinecone with metadata filtering
- Load domain-specific embedding models
- Implement advanced chunking strategies

3. **Build Knowledge Graph**
- Extract entities and relationships from medical texts
- Create knowledge graph structure
- Implement graph-based retrieval

4. **Deploy MCP Servers**
- Set up RAG server with advanced features
- Configure differential diagnosis server
- Integrate with FastAPI backend

5. **Frontend Integration**
- Add diagnosis mode to chat interface
- Display confidence scores and reasoning
- Implement feedback collection system

## Benefits of This Architecture

1. **Modular Design**: Separate MCP servers for different functionalities
2. **Advanced Retrieval**: Query expansion, reranking, and metadata filtering
3. **Deep Reasoning**: Step-by-step diagnostic reasoning with confidence scoring
4. **Safety Features**: Emergency detection and appropriate disclaimers
5. **Scalability**: Easy to add new medical domains and capabilities
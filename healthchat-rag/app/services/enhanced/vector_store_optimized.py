"""
Enhanced Vector Store Service
Advanced vector database optimization with hybrid search, metadata filtering, and medical knowledge base management
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
import hashlib
import numpy as np
from collections import defaultdict
import re

from pinecone import Pinecone, ServerlessSpec
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.exceptions.external_api_exceptions import ExternalAPIError
from app.exceptions import VectorStoreError
from app.utils.encryption_utils import field_encryption

logger = logging.getLogger(__name__)

class SearchType(str, Enum):
    """Search type enumeration"""
    VECTOR_ONLY = "vector_only"
    HYBRID = "hybrid"
    KEYWORD_ONLY = "keyword_only"
    SEMANTIC = "semantic"

class DocumentType(str, Enum):
    """Document type enumeration"""
    MEDICAL_GUIDELINE = "medical_guideline"
    DRUG_INFORMATION = "drug_information"
    SYMPTOM_DESCRIPTION = "symptom_description"
    TREATMENT_PROTOCOL = "treatment_protocol"
    DIAGNOSTIC_CRITERIA = "diagnostic_criteria"
    RESEARCH_PAPER = "research_paper"
    CLINICAL_TRIAL = "clinical_trial"
    PATIENT_EDUCATION = "patient_education"
    EMERGENCY_PROTOCOL = "emergency_protocol"

class CredibilityLevel(str, Enum):
    """Credibility level enumeration"""
    HIGH = "high"  # Peer-reviewed, official guidelines
    MEDIUM = "medium"  # Reputable sources, clinical studies
    LOW = "low"  # General information, user-generated

@dataclass
class SearchResult:
    """Enhanced search result"""
    text: str
    source: str
    title: str
    score: float
    document_type: DocumentType
    credibility_level: CredibilityLevel
    last_updated: datetime
    relevance_score: float
    confidence_score: float
    metadata: Dict[str, Any]

@dataclass
class SearchQuery:
    """Enhanced search query"""
    query: str
    search_type: SearchType
    filters: Dict[str, Any]
    max_results: int
    min_score: float
    include_metadata: bool

class EnhancedVectorStore:
    """Enhanced vector store with advanced optimization features"""
    
    def __init__(self, api_key: str, environment: str, index_name: str, 
                 chunk_size: int = 1000, chunk_overlap: int = 200,
                 embedding_dimensions: int = 1536):
        self.pc = Pinecone(api_key=api_key)
        self.environment = environment
        self.index_name = index_name
        self.embedding_dimensions = embedding_dimensions
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings()
        
        # Text processing
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        
        # Initialize spaCy for advanced text processing
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("spaCy model loaded successfully")
        except Exception as e:
            logger.warning(f"Could not load spaCy model: {e}")
            self.nlp = None
        
        # TF-IDF for keyword search
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=10000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.tfidf_matrix = None
        self.document_texts = []
        
        # Initialize index
        self._initialize_index()
        self.index = self.pc.Index(self.index_name)
        
        # Search optimization
        self.search_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
        # Medical terminology extraction
        self.medical_terms = self._load_medical_terminology()
        
        logger.info(f"Enhanced Vector Store initialized for index: {index_name}")
    
    def _initialize_index(self):
        """Initialize Pinecone index with optimized configuration"""
        try:
            # Check if index exists
            existing_indexes = [index.name for index in self.pc.list_indexes()]
            
            if self.index_name not in existing_indexes:
                # Create optimized index
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.embedding_dimensions,
                    metric='cosine',
                    spec=ServerlessSpec(
                        cloud='aws',
                        region='us-east-1'
                    )
                )
                logger.info(f"Created new optimized index: {self.index_name}")
            else:
                logger.info(f"Using existing index: {self.index_name}")
                
        except Exception as e:
            logger.error(f"Error initializing index: {e}")
            raise VectorStoreError(f"Failed to initialize vector store: {str(e)}")
    
    def _load_medical_terminology(self) -> Dict[str, List[str]]:
        """Load medical terminology for enhanced search"""
        return {
            'symptoms': [
                'fever', 'headache', 'nausea', 'vomiting', 'diarrhea', 'constipation',
                'chest_pain', 'shortness_of_breath', 'fatigue', 'dizziness',
                'cough', 'sore_throat', 'runny_nose', 'congestion', 'body_aches'
            ],
            'conditions': [
                'hypertension', 'diabetes', 'asthma', 'arthritis', 'depression',
                'anxiety', 'heart_disease', 'cancer', 'stroke', 'kidney_disease'
            ],
            'medications': [
                'aspirin', 'ibuprofen', 'acetaminophen', 'antibiotics', 'insulin',
                'blood_pressure_medication', 'cholesterol_medication'
            ],
            'procedures': [
                'blood_test', 'x_ray', 'mri', 'ct_scan', 'surgery', 'vaccination',
                'physical_examination', 'biopsy'
            ]
        }
    
    async def add_documents_enhanced(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Add documents with enhanced processing and metadata"""
        results = {
            'total_documents': len(documents),
            'successful_uploads': 0,
            'failed_uploads': 0,
            'errors': [],
            'processing_time': 0
        }
        
        start_time = datetime.utcnow()
        
        try:
            # Process documents in batches
            batch_size = 100
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                batch_results = await self._process_document_batch(batch)
                
                results['successful_uploads'] += batch_results['successful']
                results['failed_uploads'] += batch_results['failed']
                results['errors'].extend(batch_results['errors'])
                
                # Add delay between batches to respect rate limits
                if i + batch_size < len(documents):
                    await asyncio.sleep(0.1)
            
            # Update TF-IDF matrix
            await self._update_tfidf_matrix()
            
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            results['errors'].append(str(e))
        
        results['processing_time'] = (datetime.utcnow() - start_time).total_seconds()
        return results
    
    async def _process_document_batch(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process a batch of documents"""
        results = {
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        vectors_to_upsert = []
        
        for doc in documents:
            try:
                # Enhanced document processing
                processed_chunks = self._process_document_enhanced(doc)
                
                for chunk in processed_chunks:
                    # Generate vector embedding
                    vector = await self._get_embedding_async(chunk['text'])
                    
                    # Create metadata
                    metadata = {
                        'text': chunk['text'],
                        'source': doc.get('source', 'unknown'),
                        'title': doc.get('title', ''),
                        'document_type': doc.get('document_type', DocumentType.MEDICAL_GUIDELINE.value),
                        'credibility_level': doc.get('credibility_level', CredibilityLevel.MEDIUM.value),
                        'last_updated': doc.get('last_updated', datetime.utcnow().isoformat()),
                        'medical_terms': chunk.get('medical_terms', []),
                        'key_concepts': chunk.get('key_concepts', []),
                        'chunk_id': chunk['chunk_id'],
                        'chunk_index': chunk['chunk_index']
                    }
                    
                    # Create vector record
                    vector_id = f"{doc['source']}_{chunk['chunk_id']}"
                    vectors_to_upsert.append((vector_id, vector, metadata))
                
                results['successful'] += 1
                
            except Exception as e:
                logger.error(f"Error processing document {doc.get('source', 'unknown')}: {e}")
                results['failed'] += 1
                results['errors'].append(f"Document {doc.get('source', 'unknown')}: {str(e)}")
        
        # Upsert vectors to Pinecone
        if vectors_to_upsert:
            try:
                self.index.upsert(vectors=vectors_to_upsert)
                logger.info(f"Successfully upserted {len(vectors_to_upsert)} vectors")
            except Exception as e:
                logger.error(f"Error upserting vectors: {e}")
                results['failed'] += len(vectors_to_upsert)
                results['errors'].append(f"Upsert error: {str(e)}")
        
        return results
    
    def _process_document_enhanced(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Enhanced document processing with medical terminology extraction"""
        content = document.get('content', '')
        source = document.get('source', 'unknown')
        
        # Advanced text chunking
        chunks = self._advanced_chunking(content)
        
        processed_chunks = []
        for i, chunk in enumerate(chunks):
            # Extract medical terminology
            medical_terms = self._extract_medical_terms(chunk)
            
            # Extract key concepts
            key_concepts = self._extract_key_concepts(chunk)
            
            # Generate chunk ID
            chunk_id = hashlib.md5(f"{source}_{i}_{chunk[:100]}".encode()).hexdigest()[:12]
            
            processed_chunks.append({
                'text': chunk,
                'medical_terms': medical_terms,
                'key_concepts': key_concepts,
                'chunk_id': chunk_id,
                'chunk_index': i
            })
        
        return processed_chunks
    
    def _advanced_chunking(self, text: str) -> List[str]:
        """Advanced text chunking with medical context awareness"""
        if self.nlp:
            return self._spacy_medical_chunking(text)
        else:
            return self.text_splitter.split_text(text)
    
    def _spacy_medical_chunking(self, text: str) -> List[str]:
        """SpaCy-based chunking optimized for medical text"""
        doc = self.nlp(text)
        
        # Split by sentences but respect medical context
        sentences = []
        current_sentence = ""
        
        for sent in doc.sents:
            sent_text = sent.text.strip()
            
            # Check if sentence contains medical terminology
            has_medical_content = any(term in sent_text.lower() for term in 
                                    self.medical_terms['symptoms'] + 
                                    self.medical_terms['conditions'] + 
                                    self.medical_terms['medications'])
            
            # If sentence is too long, split it further
            if len(sent_text) > self.chunk_size:
                # Split by medical terms or punctuation
                sub_sentences = self._split_long_sentence(sent_text)
                sentences.extend(sub_sentences)
            else:
                sentences.append(sent_text)
        
        # Group sentences into chunks
        chunks = []
        current_chunk = ""
        current_size = 0
        
        for sentence in sentences:
            if current_size + len(sentence) <= self.chunk_size:
                current_chunk += sentence + " "
                current_size += len(sentence)
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + " "
                current_size = len(sentence)
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _split_long_sentence(self, sentence: str) -> List[str]:
        """Split long sentences while preserving medical context"""
        # Split by medical terminology or punctuation
        split_patterns = [
            r'\.\s+',  # Period followed by space
            r';\s+',   # Semicolon followed by space
            r',\s+(?=but|however|although|though)',  # Comma before conjunctions
            r'\s+(?=and|or|but)\s+'  # Conjunctions
        ]
        
        parts = [sentence]
        for pattern in split_patterns:
            new_parts = []
            for part in parts:
                if len(part) > self.chunk_size:
                    split_parts = re.split(pattern, part)
                    new_parts.extend(split_parts)
                else:
                    new_parts.append(part)
            parts = new_parts
        
        return [part.strip() for part in parts if part.strip()]
    
    def _extract_medical_terms(self, text: str) -> List[str]:
        """Extract medical terminology from text"""
        medical_terms = []
        text_lower = text.lower()
        
        for category, terms in self.medical_terms.items():
            for term in terms:
                if term.replace('_', ' ') in text_lower:
                    medical_terms.append(term)
        
        return list(set(medical_terms))
    
    def _extract_key_concepts(self, text: str) -> List[str]:
        """Extract key concepts from text using NLP"""
        if not self.nlp:
            return []
        
        doc = self.nlp(text)
        key_concepts = []
        
        # Extract named entities
        for ent in doc.ents:
            if ent.label_ in ['CONDITION', 'DISEASE', 'SYMPTOM', 'MEDICATION', 'PROCEDURE']:
                key_concepts.append(ent.text)
        
        # Extract noun phrases
        for chunk in doc.noun_chunks:
            if len(chunk.text.split()) <= 3:  # Limit to 3-word phrases
                key_concepts.append(chunk.text)
        
        return list(set(key_concepts))
    
    async def _get_embedding_async(self, text: str) -> List[float]:
        """Get embedding asynchronously"""
        try:
            # Use a thread pool for embedding generation
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None, 
                self.embeddings.embed_query, 
                text
            )
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise VectorStoreError(f"Failed to generate embedding: {str(e)}")
    
    async def _update_tfidf_matrix(self):
        """Update TF-IDF matrix for keyword search"""
        try:
            # Get all document texts from vector store
            # This is a simplified version - in production, you'd maintain a separate document store
            if self.document_texts:
                self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(self.document_texts)
                logger.info("TF-IDF matrix updated successfully")
        except Exception as e:
            logger.error(f"Error updating TF-IDF matrix: {e}")
    
    async def search_enhanced(self, query: SearchQuery) -> List[SearchResult]:
        """Enhanced search with multiple search strategies"""
        try:
            # Check cache first
            cache_key = self._generate_cache_key(query)
            if cache_key in self.search_cache:
                cached_result = self.search_cache[cache_key]
                if datetime.utcnow() - cached_result['timestamp'] < timedelta(seconds=self.cache_ttl):
                    return cached_result['results']
            
            results = []
            
            if query.search_type == SearchType.VECTOR_ONLY:
                results = await self._vector_search(query)
            elif query.search_type == SearchType.HYBRID:
                results = await self._hybrid_search(query)
            elif query.search_type == SearchType.KEYWORD_ONLY:
                results = await self._keyword_search(query)
            elif query.search_type == SearchType.SEMANTIC:
                results = await self._semantic_search(query)
            
            # Apply filters
            results = self._apply_filters(results, query.filters)
            
            # Sort by relevance
            results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            # Limit results
            results = results[:query.max_results]
            
            # Cache results
            self.search_cache[cache_key] = {
                'results': results,
                'timestamp': datetime.utcnow()
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Error in enhanced search: {e}")
            raise VectorStoreError(f"Search failed: {str(e)}")
    
    async def _vector_search(self, query: SearchQuery) -> List[SearchResult]:
        """Pure vector similarity search"""
        try:
            query_vector = await self._get_embedding_async(query.query)
            
            # Build filter dict for Pinecone
            filter_dict = self._build_pinecone_filter(query.filters)
            
            response = self.index.query(
                vector=query_vector,
                top_k=query.max_results * 2,  # Get more results for filtering
                include_metadata=True,
                filter=filter_dict
            )
            
            results = []
            for match in response.matches:
                if match.score >= query.min_score:
                    results.append(SearchResult(
                        text=match.metadata['text'],
                        source=match.metadata['source'],
                        title=match.metadata.get('title', ''),
                        score=match.score,
                        document_type=DocumentType(match.metadata.get('document_type', DocumentType.MEDICAL_GUIDELINE.value)),
                        credibility_level=CredibilityLevel(match.metadata.get('credibility_level', CredibilityLevel.MEDIUM.value)),
                        last_updated=datetime.fromisoformat(match.metadata.get('last_updated', datetime.utcnow().isoformat())),
                        relevance_score=match.score,
                        confidence_score=self._calculate_confidence_score(match),
                        metadata=match.metadata
                    ))
            
            return results
            
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            return []
    
    async def _hybrid_search(self, query: SearchQuery) -> List[SearchResult]:
        """Hybrid search combining vector and keyword search"""
        try:
            # Perform both searches
            vector_results = await self._vector_search(query)
            keyword_results = await self._keyword_search(query)
            
            # Combine and re-rank results
            combined_results = self._combine_search_results(vector_results, keyword_results)
            
            return combined_results
            
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            return []
    
    async def _keyword_search(self, query: SearchQuery) -> List[SearchResult]:
        """Keyword-based search using TF-IDF"""
        try:
            if self.tfidf_matrix is None:
                return []
            
            # Transform query using TF-IDF
            query_vector = self.tfidf_vectorizer.transform([query.query])
            
            # Calculate similarities
            similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
            
            # Get top results
            top_indices = similarities.argsort()[-query.max_results:][::-1]
            
            results = []
            for idx in top_indices:
                if similarities[idx] >= query.min_score:
                    # This is a simplified version - you'd need to map back to actual documents
                    results.append(SearchResult(
                        text=self.document_texts[idx][:200] + "...",  # Truncated for demo
                        source="keyword_search",
                        title="",
                        score=similarities[idx],
                        document_type=DocumentType.MEDICAL_GUIDELINE,
                        credibility_level=CredibilityLevel.MEDIUM,
                        last_updated=datetime.utcnow(),
                        relevance_score=similarities[idx],
                        confidence_score=0.7,
                        metadata={}
                    ))
            
            return results
            
        except Exception as e:
            logger.error(f"Error in keyword search: {e}")
            return []
    
    async def _semantic_search(self, query: SearchQuery) -> List[SearchResult]:
        """Semantic search with medical context awareness"""
        try:
            # Extract medical terms from query
            query_medical_terms = self._extract_medical_terms(query.query)
            
            # Enhance query with medical context
            enhanced_query = self._enhance_query_with_context(query.query, query_medical_terms)
            
            # Perform vector search with enhanced query
            enhanced_query_obj = SearchQuery(
                query=enhanced_query,
                search_type=SearchType.VECTOR_ONLY,
                filters=query.filters,
                max_results=query.max_results,
                min_score=query.min_score,
                include_metadata=query.include_metadata
            )
            
            results = await self._vector_search(enhanced_query_obj)
            
            # Boost results with matching medical terms
            for result in results:
                result_medical_terms = result.metadata.get('medical_terms', [])
                term_overlap = len(set(query_medical_terms) & set(result_medical_terms))
                if term_overlap > 0:
                    result.relevance_score *= (1 + term_overlap * 0.1)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    def _enhance_query_with_context(self, query: str, medical_terms: List[str]) -> str:
        """Enhance query with medical context"""
        enhanced_parts = [query]
        
        # Add medical terminology context
        for term in medical_terms:
            if term in self.medical_terms['symptoms']:
                enhanced_parts.append(f"symptom {term}")
            elif term in self.medical_terms['conditions']:
                enhanced_parts.append(f"condition {term}")
            elif term in self.medical_terms['medications']:
                enhanced_parts.append(f"medication {term}")
        
        return " ".join(enhanced_parts)
    
    def _combine_search_results(self, vector_results: List[SearchResult], 
                              keyword_results: List[SearchResult]) -> List[SearchResult]:
        """Combine and re-rank search results"""
        # Create a dictionary to track combined results
        combined_dict = {}
        
        # Add vector results
        for result in vector_results:
            key = f"{result.source}_{result.text[:100]}"
            combined_dict[key] = {
                'result': result,
                'vector_score': result.score,
                'keyword_score': 0.0,
                'combined_score': result.score
            }
        
        # Add keyword results
        for result in keyword_results:
            key = f"{result.source}_{result.text[:100]}"
            if key in combined_dict:
                combined_dict[key]['keyword_score'] = result.score
                combined_dict[key]['combined_score'] = (
                    combined_dict[key]['vector_score'] * 0.7 + 
                    result.score * 0.3
                )
            else:
                combined_dict[key] = {
                    'result': result,
                    'vector_score': 0.0,
                    'keyword_score': result.score,
                    'combined_score': result.score * 0.3
                }
        
        # Convert back to results and sort by combined score
        combined_results = []
        for data in combined_dict.values():
            result = data['result']
            result.relevance_score = data['combined_score']
            combined_results.append(result)
        
        combined_results.sort(key=lambda x: x.relevance_score, reverse=True)
        return combined_results
    
    def _apply_filters(self, results: List[SearchResult], filters: Dict[str, Any]) -> List[SearchResult]:
        """Apply filters to search results"""
        if not filters:
            return results
        
        filtered_results = []
        
        for result in results:
            include_result = True
            
            # Document type filter
            if 'document_type' in filters:
                if result.document_type.value not in filters['document_type']:
                    include_result = False
            
            # Credibility level filter
            if 'credibility_level' in filters:
                if result.credibility_level.value not in filters['credibility_level']:
                    include_result = False
            
            # Date filter
            if 'date_from' in filters:
                if result.last_updated < datetime.fromisoformat(filters['date_from']):
                    include_result = False
            
            if 'date_to' in filters:
                if result.last_updated > datetime.fromisoformat(filters['date_to']):
                    include_result = False
            
            # Source filter
            if 'source' in filters:
                if result.source not in filters['source']:
                    include_result = False
            
            if include_result:
                filtered_results.append(result)
        
        return filtered_results
    
    def _build_pinecone_filter(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Build Pinecone filter dictionary"""
        pinecone_filter = {}
        
        if 'document_type' in filters:
            pinecone_filter['document_type'] = {'$in': filters['document_type']}
        
        if 'credibility_level' in filters:
            pinecone_filter['credibility_level'] = {'$in': filters['credibility_level']}
        
        if 'source' in filters:
            pinecone_filter['source'] = {'$in': filters['source']}
        
        return pinecone_filter if pinecone_filter else None
    
    def _calculate_confidence_score(self, match) -> float:
        """Calculate confidence score for search result"""
        base_score = match.score
        
        # Boost based on credibility level
        credibility_boost = {
            CredibilityLevel.HIGH.value: 0.2,
            CredibilityLevel.MEDIUM.value: 0.1,
            CredibilityLevel.LOW.value: 0.0
        }
        
        credibility = match.metadata.get('credibility_level', CredibilityLevel.MEDIUM.value)
        boost = credibility_boost.get(credibility, 0.0)
        
        return min(base_score + boost, 1.0)
    
    def _generate_cache_key(self, query: SearchQuery) -> str:
        """Generate cache key for search query"""
        query_string = f"{query.query}_{query.search_type.value}_{query.max_results}_{query.min_score}"
        filters_string = json.dumps(query.filters, sort_keys=True)
        return hashlib.md5(f"{query_string}_{filters_string}".encode()).hexdigest()
    
    async def get_index_statistics(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        try:
            stats = self.index.describe_index_stats()
            return {
                'total_vector_count': stats.total_vector_count,
                'dimension': stats.dimension,
                'index_fullness': stats.index_fullness,
                'namespaces': stats.namespaces
            }
        except Exception as e:
            logger.error(f"Error getting index statistics: {e}")
            return {}
    
    async def delete_documents(self, source: str) -> bool:
        """Delete documents by source"""
        try:
            # Get all vectors for the source
            response = self.index.query(
                vector=[0] * self.embedding_dimensions,  # Dummy vector
                top_k=10000,
                include_metadata=True,
                filter={'source': {'$eq': source}}
            )
            
            # Delete vectors
            vector_ids = [match.id for match in response.matches]
            if vector_ids:
                self.index.delete(ids=vector_ids)
                logger.info(f"Deleted {len(vector_ids)} vectors for source: {source}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting documents: {e}")
            return False
    
    async def update_document_metadata(self, source: str, updates: Dict[str, Any]) -> bool:
        """Update document metadata"""
        try:
            # Get all vectors for the source
            response = self.index.query(
                vector=[0] * self.embedding_dimensions,  # Dummy vector
                top_k=10000,
                include_metadata=True,
                filter={'source': {'$eq': source}}
            )
            
            # Update metadata
            for match in response.matches:
                new_metadata = match.metadata.copy()
                new_metadata.update(updates)
                
                self.index.update(
                    id=match.id,
                    set_metadata=new_metadata
                )
            
            logger.info(f"Updated metadata for {len(response.matches)} vectors from source: {source}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating document metadata: {e}")
            return False

# Global enhanced vector store instance
enhanced_vector_store = None

def get_enhanced_vector_store(api_key: str, environment: str, index_name: str) -> EnhancedVectorStore:
    """Get or create enhanced vector store instance"""
    global enhanced_vector_store
    if enhanced_vector_store is None:
        enhanced_vector_store = EnhancedVectorStore(api_key, environment, index_name)
    return enhanced_vector_store 
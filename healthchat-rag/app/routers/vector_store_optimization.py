"""
Vector Store Optimization Router
FastAPI router for enhanced vector store operations including search, document management, and analytics
"""

import time
import logging
from typing import List, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer

from app.schemas.enhanced_health_schemas import (
    VectorSearchQuery, VectorSearchResponse, VectorSearchResult,
    DocumentUploadRequest, DocumentUploadResponse,
    IndexStatisticsResponse, DocumentDeleteRequest, DocumentUpdateRequest,
    VectorStoreOperationResponse, SearchType, DocumentType, CredibilityLevel
)
from app.services.enhanced.vector_store_optimized import (
    get_enhanced_vector_store, SearchQuery, SearchResult
)
from app.utils.auth_middleware import get_current_user
from app.models.user import User
from app.config import settings

logger = logging.getLogger(__name__)
security = HTTPBearer()

router = APIRouter(prefix="/vector-store", tags=["Vector Store Optimization"])

# Initialize enhanced vector store
vector_store = get_enhanced_vector_store(
    api_key=settings.pinecone_api_key,
    environment=settings.pinecone_environment,
    index_name=settings.pinecone_index_name
)

@router.post("/search", response_model=VectorSearchResponse)
async def search_medical_knowledge(
    search_query: VectorSearchQuery,
    current_user: User = Depends(get_current_user)
):
    """
    Enhanced medical knowledge search with multiple search strategies
    
    Supports:
    - Vector-only search for semantic similarity
    - Hybrid search combining vector and keyword search
    - Keyword-only search for exact term matching
    - Semantic search with medical context awareness
    """
    try:
        start_time = time.time()
        
        # Convert to internal search query format
        internal_query = SearchQuery(
            query=search_query.query,
            search_type=SearchType(search_query.search_type.value),
            filters=search_query.filters,
            max_results=search_query.max_results,
            min_score=search_query.min_score,
            include_metadata=search_query.include_metadata
        )
        
        # Perform search
        search_results = await vector_store.search_enhanced(internal_query)
        
        # Convert to response format
        results = []
        for result in search_results:
            results.append(VectorSearchResult(
                text=result.text,
                source=result.source,
                title=result.title,
                score=result.score,
                document_type=DocumentType(result.document_type.value),
                credibility_level=CredibilityLevel(result.credibility_level.value),
                last_updated=result.last_updated,
                relevance_score=result.relevance_score,
                confidence_score=result.confidence_score,
                metadata=result.metadata
            ))
        
        search_time = time.time() - start_time
        
        logger.info(f"Vector search completed for user {current_user.id} in {search_time:.3f}s")
        
        return VectorSearchResponse(
            results=results,
            total_results=len(results),
            search_time=search_time,
            query=search_query
        )
        
    except Exception as e:
        logger.error(f"Error in vector search: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )

@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_documents(
    upload_request: DocumentUploadRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Upload medical documents to the vector store
    
    Documents are processed with:
    - Advanced text chunking optimized for medical content
    - Medical terminology extraction
    - Key concept identification
    - Metadata enrichment
    """
    try:
        start_time = time.time()
        
        # Upload documents
        result = await vector_store.add_documents_enhanced(upload_request.documents)
        
        processing_time = time.time() - start_time
        
        logger.info(f"Document upload completed for user {current_user.id}: "
                   f"{result['successful_uploads']}/{result['total_documents']} successful")
        
        return DocumentUploadResponse(
            total_documents=result['total_documents'],
            successful_uploads=result['successful_uploads'],
            failed_uploads=result['failed_uploads'],
            errors=result['errors'],
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error uploading documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document upload failed: {str(e)}"
        )

@router.get("/statistics", response_model=IndexStatisticsResponse)
async def get_index_statistics(
    current_user: User = Depends(get_current_user)
):
    """
    Get vector store index statistics
    
    Returns:
    - Total vector count
    - Index dimensions
    - Index fullness
    - Namespace information
    """
    try:
        stats = await vector_store.get_index_statistics()
        
        logger.info(f"Index statistics retrieved for user {current_user.id}")
        
        return IndexStatisticsResponse(
            total_vector_count=stats.get('total_vector_count', 0),
            dimension=stats.get('dimension', 1536),
            index_fullness=stats.get('index_fullness', 0.0),
            namespaces=stats.get('namespaces', {})
        )
        
    except Exception as e:
        logger.error(f"Error getting index statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve index statistics: {str(e)}"
        )

@router.delete("/documents", response_model=VectorStoreOperationResponse)
async def delete_documents(
    delete_request: DocumentDeleteRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Delete documents by source identifier
    
    Removes all vectors associated with the specified source
    """
    try:
        start_time = time.time()
        
        success = await vector_store.delete_documents(delete_request.source)
        
        operation_time = time.time() - start_time
        
        if success:
            logger.info(f"Documents deleted for user {current_user.id}: {delete_request.source}")
            return VectorStoreOperationResponse(
                success=True,
                message=f"Documents from source '{delete_request.source}' deleted successfully",
                operation_time=operation_time
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete documents"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document deletion failed: {str(e)}"
        )

@router.put("/documents/metadata", response_model=VectorStoreOperationResponse)
async def update_document_metadata(
    update_request: DocumentUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Update document metadata by source identifier
    
    Updates metadata for all vectors associated with the specified source
    """
    try:
        start_time = time.time()
        
        success = await vector_store.update_document_metadata(
            update_request.source, 
            update_request.updates
        )
        
        operation_time = time.time() - start_time
        
        if success:
            logger.info(f"Document metadata updated for user {current_user.id}: {update_request.source}")
            return VectorStoreOperationResponse(
                success=True,
                message=f"Metadata updated successfully for source '{update_request.source}'",
                operation_time=operation_time
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update document metadata"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating document metadata: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Metadata update failed: {str(e)}"
        )

@router.get("/search/types")
async def get_search_types():
    """
    Get available search types and their descriptions
    """
    return {
        "search_types": [
            {
                "type": "vector_only",
                "name": "Vector-Only Search",
                "description": "Pure semantic similarity search using vector embeddings",
                "best_for": "Semantic understanding and context-aware queries"
            },
            {
                "type": "hybrid",
                "name": "Hybrid Search",
                "description": "Combines vector similarity with keyword matching",
                "best_for": "Balanced search with both semantic and exact matching"
            },
            {
                "type": "keyword_only",
                "name": "Keyword-Only Search",
                "description": "Traditional keyword-based search using TF-IDF",
                "best_for": "Exact term matching and specific medical terminology"
            },
            {
                "type": "semantic",
                "name": "Semantic Search",
                "description": "Medical context-aware search with terminology enhancement",
                "best_for": "Medical queries requiring domain-specific understanding"
            }
        ]
    }

@router.get("/document/types")
async def get_document_types():
    """
    Get available document types and their descriptions
    """
    return {
        "document_types": [
            {
                "type": "medical_guideline",
                "name": "Medical Guidelines",
                "description": "Official medical guidelines and protocols",
                "credibility": "high"
            },
            {
                "type": "drug_information",
                "name": "Drug Information",
                "description": "Medication details, side effects, and interactions",
                "credibility": "high"
            },
            {
                "type": "symptom_description",
                "name": "Symptom Descriptions",
                "description": "Detailed symptom information and characteristics",
                "credibility": "medium"
            },
            {
                "type": "treatment_protocol",
                "name": "Treatment Protocols",
                "description": "Standard treatment procedures and protocols",
                "credibility": "high"
            },
            {
                "type": "diagnostic_criteria",
                "name": "Diagnostic Criteria",
                "description": "Diagnostic standards and criteria",
                "credibility": "high"
            },
            {
                "type": "research_paper",
                "name": "Research Papers",
                "description": "Peer-reviewed medical research and studies",
                "credibility": "high"
            },
            {
                "type": "clinical_trial",
                "name": "Clinical Trials",
                "description": "Clinical trial results and findings",
                "credibility": "high"
            },
            {
                "type": "patient_education",
                "name": "Patient Education",
                "description": "Patient-friendly medical information",
                "credibility": "medium"
            },
            {
                "type": "emergency_protocol",
                "name": "Emergency Protocols",
                "description": "Emergency medical procedures and protocols",
                "credibility": "high"
            }
        ]
    }

@router.get("/health")
async def vector_store_health_check():
    """
    Health check endpoint for vector store service
    """
    try:
        # Test basic connectivity
        stats = await vector_store.get_index_statistics()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "index_name": vector_store.index_name,
            "total_vectors": stats.get('total_vector_count', 0),
            "dimension": stats.get('dimension', 1536)
        }
        
    except Exception as e:
        logger.error(f"Vector store health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Vector store service unavailable: {str(e)}"
        ) 
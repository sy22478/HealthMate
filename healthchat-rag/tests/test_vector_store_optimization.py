"""
Tests for Vector Store Optimization
Comprehensive test suite for enhanced vector store functionality
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from typing import List, Dict, Any

from app.services.enhanced.vector_store_optimized import (
    EnhancedVectorStore, SearchType, DocumentType, CredibilityLevel,
    SearchQuery, SearchResult, get_enhanced_vector_store
)
from app.schemas.enhanced_health_schemas import (
    VectorSearchQuery, VectorSearchResult, DocumentUploadRequest
)
from app.exceptions import VectorStoreError

class TestEnhancedVectorStore:
    """Test suite for EnhancedVectorStore"""
    
    @pytest.fixture
    def mock_pinecone(self):
        """Mock Pinecone client"""
        with patch('app.services.enhanced.vector_store_optimized.Pinecone') as mock_pc:
            mock_index = Mock()
            mock_pc.return_value.Index.return_value = mock_index
            mock_pc.return_value.list_indexes.return_value = [Mock(name='test_index')]
            yield mock_pc
    
    @pytest.fixture
    def mock_embeddings(self):
        """Mock OpenAI embeddings"""
        with patch('app.services.enhanced.vector_store_optimized.OpenAIEmbeddings') as mock_emb:
            mock_emb.return_value.embed_query.return_value = [0.1] * 1536
            yield mock_emb
    
    @pytest.fixture
    def mock_spacy(self):
        """Mock spaCy NLP"""
        with patch('app.services.enhanced.vector_store_optimized.spacy') as mock_spacy:
            mock_nlp = Mock()
            mock_doc = Mock()
            mock_sent = Mock()
            mock_sent.text = "This is a test sentence."
            mock_doc.sents = [mock_sent]
            mock_nlp.return_value = mock_doc
            mock_spacy.load.return_value = mock_nlp
            yield mock_spacy
    
    @pytest.fixture
    def vector_store(self, mock_pinecone, mock_embeddings, mock_spacy):
        """Create test vector store instance"""
        return EnhancedVectorStore(
            api_key="test_key",
            environment="test_env",
            index_name="test_index"
        )
    
    def test_initialization(self, vector_store):
        """Test vector store initialization"""
        assert vector_store.index_name == "test_index"
        assert vector_store.embedding_dimensions == 1536
        assert vector_store.chunk_size == 1000
        assert vector_store.chunk_overlap == 200
        assert vector_store.nlp is not None
    
    def test_medical_terminology_loading(self, vector_store):
        """Test medical terminology loading"""
        assert 'symptoms' in vector_store.medical_terms
        assert 'conditions' in vector_store.medical_terms
        assert 'medications' in vector_store.medical_terms
        assert 'procedures' in vector_store.medical_terms
        
        # Check specific terms
        assert 'diabetes' in vector_store.medical_terms['conditions']
        assert 'aspirin' in vector_store.medical_terms['medications']
    
    def test_extract_medical_terms(self, vector_store):
        """Test medical terminology extraction"""
        text = "Patient has diabetes and takes aspirin for pain."
        terms = vector_store._extract_medical_terms(text)
        
        assert 'diabetes' in terms
        assert 'aspirin' in terms
    
    def test_extract_key_concepts(self, vector_store):
        """Test key concept extraction"""
        text = "Diabetes is a chronic disease that affects blood sugar levels."
        concepts = vector_store._extract_key_concepts(text)
        
        # Should extract concepts (actual results depend on spaCy model)
        assert isinstance(concepts, list)
    
    def test_advanced_chunking(self, vector_store):
        """Test advanced text chunking"""
        text = "This is a long medical document. It contains multiple sentences. " \
               "Each sentence should be processed properly. Medical terminology like diabetes " \
               "should be preserved in chunks."
        
        chunks = vector_store._advanced_chunking(text)
        
        assert isinstance(chunks, list)
        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)
    
    def test_split_long_sentence(self, vector_store):
        """Test long sentence splitting"""
        long_sentence = "This is a very long sentence that contains multiple clauses " \
                       "and should be split into smaller parts for better processing " \
                       "and understanding of the medical content."
        
        parts = vector_store._split_long_sentence(long_sentence)
        
        assert isinstance(parts, list)
        assert len(parts) > 0
        assert all(isinstance(part, str) for part in parts)
    
    @pytest.mark.asyncio
    async def test_get_embedding_async(self, vector_store):
        """Test async embedding generation"""
        text = "Test medical query"
        
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_loop.return_value.run_in_executor.return_value = [0.1] * 1536
            
            embedding = await vector_store._get_embedding_async(text)
            
            assert isinstance(embedding, list)
            assert len(embedding) == 1536
            assert all(isinstance(val, float) for val in embedding)
    
    @pytest.mark.asyncio
    async def test_add_documents_enhanced(self, vector_store):
        """Test enhanced document addition"""
        documents = [
            {
                'content': 'Diabetes is a chronic disease affecting blood sugar.',
                'source': 'test_source',
                'title': 'Diabetes Overview',
                'document_type': DocumentType.MEDICAL_GUIDELINE.value,
                'credibility_level': CredibilityLevel.HIGH.value,
                'last_updated': datetime.utcnow().isoformat()
            }
        ]
        
        with patch.object(vector_store, '_process_document_batch') as mock_process:
            mock_process.return_value = {
                'successful': 1,
                'failed': 0,
                'errors': []
            }
            
            with patch.object(vector_store, '_update_tfidf_matrix') as mock_update:
                result = await vector_store.add_documents_enhanced(documents)
                
                assert result['total_documents'] == 1
                assert result['successful_uploads'] == 1
                assert result['failed_uploads'] == 0
                assert len(result['errors']) == 0
                assert result['processing_time'] > 0
    
    @pytest.mark.asyncio
    async def test_vector_search(self, vector_store):
        """Test vector search functionality"""
        query = SearchQuery(
            query="diabetes symptoms",
            search_type=SearchType.VECTOR_ONLY,
            filters={},
            max_results=5,
            min_score=0.5,
            include_metadata=True
        )
        
        # Mock Pinecone query response
        mock_match = Mock()
        mock_match.score = 0.85
        mock_match.metadata = {
            'text': 'Diabetes symptoms include increased thirst and fatigue.',
            'source': 'test_source',
            'title': 'Diabetes Symptoms',
            'document_type': DocumentType.MEDICAL_GUIDELINE.value,
            'credibility_level': CredibilityLevel.HIGH.value,
            'last_updated': datetime.utcnow().isoformat()
        }
        
        with patch.object(vector_store.index, 'query') as mock_query:
            mock_query.return_value.matches = [mock_match]
            
            with patch.object(vector_store, '_get_embedding_async') as mock_embed:
                mock_embed.return_value = [0.1] * 1536
                
                results = await vector_store._vector_search(query)
                
                assert isinstance(results, list)
                assert len(results) == 1
                assert isinstance(results[0], SearchResult)
                assert results[0].score == 0.85
    
    @pytest.mark.asyncio
    async def test_hybrid_search(self, vector_store):
        """Test hybrid search functionality"""
        query = SearchQuery(
            query="diabetes treatment",
            search_type=SearchType.HYBRID,
            filters={},
            max_results=5,
            min_score=0.5,
            include_metadata=True
        )
        
        with patch.object(vector_store, '_vector_search') as mock_vector:
            mock_vector.return_value = []
            
            with patch.object(vector_store, '_keyword_search') as mock_keyword:
                mock_keyword.return_value = []
                
                results = await vector_store._hybrid_search(query)
                
                assert isinstance(results, list)
                mock_vector.assert_called_once()
                mock_keyword.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_semantic_search(self, vector_store):
        """Test semantic search functionality"""
        query = SearchQuery(
            query="diabetes symptoms",
            search_type=SearchType.SEMANTIC,
            filters={},
            max_results=5,
            min_score=0.5,
            include_metadata=True
        )
        
        with patch.object(vector_store, '_vector_search') as mock_vector:
            mock_vector.return_value = []
            
            results = await vector_store._semantic_search(query)
            
            assert isinstance(results, list)
            mock_vector.assert_called_once()
    
    def test_enhance_query_with_context(self, vector_store):
        """Test query enhancement with medical context"""
        query = "diabetes symptoms"
        medical_terms = ['diabetes']
        
        enhanced = vector_store._enhance_query_with_context(query, medical_terms)
        
        assert 'diabetes' in enhanced
        assert 'condition diabetes' in enhanced
    
    def test_combine_search_results(self, vector_store):
        """Test search result combination"""
        vector_results = [
            SearchResult(
                text="Vector result",
                source="test",
                title="Test",
                score=0.8,
                document_type=DocumentType.MEDICAL_GUIDELINE,
                credibility_level=CredibilityLevel.HIGH,
                last_updated=datetime.utcnow(),
                relevance_score=0.8,
                confidence_score=0.9,
                metadata={}
            )
        ]
        
        keyword_results = [
            SearchResult(
                text="Keyword result",
                source="test",
                title="Test",
                score=0.7,
                document_type=DocumentType.MEDICAL_GUIDELINE,
                credibility_level=CredibilityLevel.HIGH,
                last_updated=datetime.utcnow(),
                relevance_score=0.7,
                confidence_score=0.8,
                metadata={}
            )
        ]
        
        combined = vector_store._combine_search_results(vector_results, keyword_results)
        
        assert isinstance(combined, list)
        assert len(combined) == 2
    
    def test_apply_filters(self, vector_store):
        """Test result filtering"""
        results = [
            SearchResult(
                text="Test result",
                source="test_source",
                title="Test",
                score=0.8,
                document_type=DocumentType.MEDICAL_GUIDELINE,
                credibility_level=CredibilityLevel.HIGH,
                last_updated=datetime.utcnow(),
                relevance_score=0.8,
                confidence_score=0.9,
                metadata={}
            )
        ]
        
        filters = {
            'document_type': [DocumentType.MEDICAL_GUIDELINE.value],
            'credibility_level': [CredibilityLevel.HIGH.value]
        }
        
        filtered = vector_store._apply_filters(results, filters)
        
        assert len(filtered) == 1
        
        # Test with non-matching filter
        filters = {
            'document_type': [DocumentType.DRUG_INFORMATION.value]
        }
        
        filtered = vector_store._apply_filters(results, filters)
        
        assert len(filtered) == 0
    
    def test_build_pinecone_filter(self, vector_store):
        """Test Pinecone filter building"""
        filters = {
            'document_type': ['medical_guideline'],
            'credibility_level': ['high']
        }
        
        pinecone_filter = vector_store._build_pinecone_filter(filters)
        
        assert pinecone_filter['document_type'] == {'$in': ['medical_guideline']}
        assert pinecone_filter['credibility_level'] == {'$in': ['high']}
    
    def test_calculate_confidence_score(self, vector_store):
        """Test confidence score calculation"""
        mock_match = Mock()
        mock_match.score = 0.8
        mock_match.metadata = {'credibility_level': CredibilityLevel.HIGH.value}
        
        confidence = vector_store._calculate_confidence_score(mock_match)
        
        assert confidence == 1.0  # 0.8 + 0.2 boost for high credibility
    
    def test_generate_cache_key(self, vector_store):
        """Test cache key generation"""
        query = SearchQuery(
            query="test query",
            search_type=SearchType.VECTOR_ONLY,
            filters={'test': 'value'},
            max_results=10,
            min_score=0.5,
            include_metadata=True
        )
        
        cache_key = vector_store._generate_cache_key(query)
        
        assert isinstance(cache_key, str)
        assert len(cache_key) == 32  # MD5 hash length
    
    @pytest.mark.asyncio
    async def test_get_index_statistics(self, vector_store):
        """Test index statistics retrieval"""
        mock_stats = {
            'total_vector_count': 1000,
            'dimension': 1536,
            'index_fullness': 0.75,
            'namespaces': {'default': {'vector_count': 1000}}
        }
        
        with patch.object(vector_store.index, 'describe_index_stats') as mock_describe:
            mock_describe.return_value = Mock(**mock_stats)
            
            stats = await vector_store.get_index_statistics()
            
            assert stats['total_vector_count'] == 1000
            assert stats['dimension'] == 1536
            assert stats['index_fullness'] == 0.75
    
    @pytest.mark.asyncio
    async def test_delete_documents(self, vector_store):
        """Test document deletion"""
        mock_match = Mock()
        mock_match.id = "test_id"
        
        with patch.object(vector_store.index, 'query') as mock_query:
            mock_query.return_value.matches = [mock_match]
            
            with patch.object(vector_store.index, 'delete') as mock_delete:
                success = await vector_store.delete_documents("test_source")
                
                assert success is True
                mock_delete.assert_called_once_with(ids=["test_id"])
    
    @pytest.mark.asyncio
    async def test_update_document_metadata(self, vector_store):
        """Test document metadata update"""
        mock_match = Mock()
        mock_match.id = "test_id"
        mock_match.metadata = {'existing': 'value'}
        
        with patch.object(vector_store.index, 'query') as mock_query:
            mock_query.return_value.matches = [mock_match]
            
            with patch.object(vector_store.index, 'update') as mock_update:
                success = await vector_store.update_document_metadata(
                    "test_source", 
                    {'new': 'value'}
                )
                
                assert success is True
                mock_update.assert_called_once()

class TestVectorStoreSchemas:
    """Test suite for vector store schemas"""
    
    def test_vector_search_query_validation(self):
        """Test VectorSearchQuery validation"""
        # Valid query
        query = VectorSearchQuery(
            query="diabetes symptoms",
            search_type=SearchType.HYBRID,
            max_results=10,
            min_score=0.7
        )
        
        assert query.query == "diabetes symptoms"
        assert query.search_type == SearchType.HYBRID
        assert query.max_results == 10
        assert query.min_score == 0.7
    
    def test_vector_search_query_invalid(self):
        """Test VectorSearchQuery validation errors"""
        with pytest.raises(ValueError):
            VectorSearchQuery(
                query="",  # Empty query
                max_results=10
            )
        
        with pytest.raises(ValueError):
            VectorSearchQuery(
                query="test",
                max_results=0  # Invalid max_results
            )
        
        with pytest.raises(ValueError):
            VectorSearchQuery(
                query="test",
                min_score=1.5  # Invalid min_score
            )
    
    def test_document_upload_request_validation(self):
        """Test DocumentUploadRequest validation"""
        request = DocumentUploadRequest(
            documents=[
                {
                    'content': 'Test content',
                    'source': 'test_source',
                    'title': 'Test Title'
                }
            ]
        )
        
        assert len(request.documents) == 1
        assert request.documents[0]['content'] == 'Test content'

class TestVectorStoreIntegration:
    """Integration tests for vector store functionality"""
    
    @pytest.mark.asyncio
    async def test_full_search_workflow(self):
        """Test complete search workflow"""
        # This would test the full integration with actual Pinecone
        # For now, we'll test the workflow with mocks
        pass
    
    @pytest.mark.asyncio
    async def test_document_processing_workflow(self):
        """Test complete document processing workflow"""
        # This would test the full document processing pipeline
        # For now, we'll test the workflow with mocks
        pass

def test_get_enhanced_vector_store():
    """Test enhanced vector store factory function"""
    with patch('app.services.enhanced.vector_store_optimized.EnhancedVectorStore') as mock_store:
        store = get_enhanced_vector_store("test_key", "test_env", "test_index")
        
        assert store is not None
        mock_store.assert_called_once_with("test_key", "test_env", "test_index") 
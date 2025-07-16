#!/usr/bin/env python3
"""
Test script to verify all MCP modules can be imported successfully
"""

def test_imports():
    """Test importing all MCP modules"""
    try:
        print("Testing imports...")
        
        # Test basic imports
        print("✓ Importing sentence_transformers...")
        from sentence_transformers import SentenceTransformer
        
        print("✓ Importing spacy...")
        import spacy
        
        print("✓ Importing networkx...")
        import networkx as nx
        
        print("✓ Importing MCP types...")
        from app.mcp.types import ChunkMetadata, DiagnosisResult, DiagnosisUrgency
        
        print("✓ Importing MCP medical data...")
        from app.mcp.medical_data import EMERGENCY_KEYWORDS, SYMPTOM_DATABASE
        
        print("✓ Importing MCP RAG server...")
        from app.mcp.rag_server import AdvancedRAGServer
        
        print("✓ Importing MCP diagnosis server...")
        from app.mcp.diagnosis_server import DifferentialDiagnosisServer
        
        print("✓ Importing enhanced knowledge base...")
        from app.services.enhanced_knowledge_base import EnhancedMedicalKnowledgeBase
        
        print("✓ Importing enhanced chat router...")
        from app.routers.enhanced_chat import router as enhanced_chat_router
        
        print("\n🎉 All imports successful!")
        return True
        
    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_spacy_model():
    """Test spaCy model loading"""
    try:
        print("\nTesting spaCy model...")
        import spacy
        nlp = spacy.load("en_core_web_sm")
        doc = nlp("This is a test sentence.")
        print(f"✓ spaCy model loaded successfully. Processed text: {doc.text}")
        return True
    except Exception as e:
        print(f"❌ spaCy model failed: {e}")
        return False

def test_sentence_transformers():
    """Test sentence transformers"""
    try:
        print("\nTesting sentence transformers...")
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        embeddings = model.encode("This is a test sentence.")
        print(f"✓ Sentence transformers working. Embedding shape: {embeddings.shape}")
        return True
    except Exception as e:
        print(f"❌ Sentence transformers failed: {e}")
        return False

if __name__ == "__main__":
    print("HealthMate MCP Import Test")
    print("=" * 40)
    
    success = True
    success &= test_imports()
    success &= test_spacy_model()
    success &= test_sentence_transformers()
    
    if success:
        print("\n✅ All tests passed! The MCP system is ready to use.")
    else:
        print("\n❌ Some tests failed. Please check the errors above.") 
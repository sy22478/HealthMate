#!/usr/bin/env python3
"""
Test setup script to verify environment configuration before running tests.
"""

import os
import sys

def setup_test_environment():
    """Set up test environment variables."""
    # Set required environment variables
    os.environ["OPENAI_API_KEY"] = "test-openai-key"
    os.environ["PINECONE_API_KEY"] = "test-pinecone-key"
    os.environ["PINECONE_ENVIRONMENT"] = "test-environment"
    os.environ["PINECONE_INDEX_NAME"] = "test-index"
    os.environ["POSTGRES_URI"] = "sqlite:///./test.db"
    os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
    os.environ["HEALTHMATE_ENVIRONMENT"] = "test"
    
    print("✅ Test environment variables set successfully")
    
    # Test imports
    try:
        import pythonjsonlogger
        print("✅ pythonjsonlogger imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import pythonjsonlogger: {e}")
        return False
    
    try:
        from app.config import settings
        print("✅ Settings imported successfully")
        print(f"   Environment: {settings.environment}")
        print(f"   Database URI: {settings.postgres_uri}")
    except Exception as e:
        print(f"❌ Failed to import settings: {e}")
        return False
    
    try:
        from app.database import engine
        print("✅ Database engine created successfully")
    except Exception as e:
        print(f"❌ Failed to create database engine: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = setup_test_environment()
    sys.exit(0 if success else 1) 
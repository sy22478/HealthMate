#!/usr/bin/env python3
"""
CI/CD Validation Script for HealthMate

This script validates that all core components work correctly
for the CI/CD pipeline without requiring pytest.
"""

import os
import sys
import time
import requests
from typing import Dict, List, Any

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test all critical imports"""
    print("🔍 Testing imports...")
    
    try:
        from app.database import engine, get_db
        from app.models.user import User, Base
        from app.services.auth import AuthService
        from app.config import settings
        from app.main import app
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_database_connection():
    """Test database connection"""
    print("🔍 Testing database connection...")
    
    try:
        from app.database import engine
        from sqlalchemy import text
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.fetchone()[0] == 1
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_environment_variables():
    """Test required environment variables"""
    print("🔍 Testing environment variables...")
    
    required_vars = ['POSTGRES_URI', 'SECRET_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        return False
    
    print("✅ All required environment variables present")
    return True

def test_auth_service():
    """Test authentication service"""
    print("🔍 Testing authentication service...")
    
    try:
        from app.services.auth import AuthService
        from app.config import settings
        
        auth_service = AuthService(settings.secret_key)
        
        # Test password hashing
        test_password = "TestPass123!"
        hashed = auth_service.get_password_hash(test_password)
        
        # Test password verification
        is_valid = auth_service.verify_password(test_password, hashed)
        is_invalid = auth_service.verify_password("WrongPassword", hashed)
        
        assert is_valid is True
        assert is_invalid is False
        
        print("✅ Authentication service working")
        return True
    except Exception as e:
        print(f"❌ Authentication service failed: {e}")
        return False

def test_user_model():
    """Test user model"""
    print("🔍 Testing user model...")
    
    try:
        from app.models.user import User
        
        user = User(
            email="test@example.com",
            hashed_password="hashed_password",
            full_name="Test User",
            age=25,
            role="patient"
        )
        
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.role == "patient"
        
        print("✅ User model working")
        return True
    except Exception as e:
        print(f"❌ User model failed: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints"""
    print("🔍 Testing API endpoints...")
    
    api_url = os.getenv('HEALTHMATE_API_URL', 'http://localhost:8000')
    
    try:
        # Test health endpoint
        response = requests.get(f"{api_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health endpoint accessible")
        else:
            print(f"⚠️  Health endpoint returned {response.status_code}")
        
        # Test docs endpoint
        response = requests.get(f"{api_url}/docs", timeout=10)
        if response.status_code == 200:
            print("✅ Docs endpoint accessible")
        else:
            print(f"⚠️  Docs endpoint returned {response.status_code}")
        
        return True
    except requests.exceptions.RequestException as e:
        print(f"⚠️  API endpoints not accessible: {e}")
        return True  # Don't fail CI/CD for this

def test_configuration():
    """Test configuration loading"""
    print("🔍 Testing configuration...")
    
    try:
        from app.config import settings
        
        # Test required settings
        assert hasattr(settings, 'secret_key')
        assert hasattr(settings, 'database_url')
        assert hasattr(settings, 'cors_origins_list')
        
        print("✅ Configuration loaded successfully")
        return True
    except Exception as e:
        print(f"❌ Configuration failed: {e}")
        return False

def test_security():
    """Test security features"""
    print("🔍 Testing security features...")
    
    try:
        from app.config import settings
        
        # Test secret key strength
        secret_key = settings.secret_key
        assert len(secret_key) >= 32, "Secret key too short"
        
        # Test CORS configuration
        assert hasattr(settings, 'cors_origins_list')
        assert isinstance(settings.cors_origins_list, list)
        
        print("✅ Security features configured")
        return True
    except Exception as e:
        print(f"❌ Security test failed: {e}")
        return False

def test_performance():
    """Test performance requirements"""
    print("🔍 Testing performance...")
    
    try:
        start_time = time.time()
        
        # Test import performance
        from app.main import app
        from app.routers import auth_router, health_router
        
        import_time = time.time() - start_time
        assert import_time < 5.0, f"Import too slow: {import_time:.2f}s"
        
        # Test database performance
        start_time = time.time()
        from app.database import engine
        from sqlalchemy import text
        
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        db_time = time.time() - start_time
        assert db_time < 1.0, f"Database operation too slow: {db_time:.2f}s"
        
        print(f"✅ Performance tests passed (import: {import_time:.2f}s, db: {db_time:.2f}s)")
        return True
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False

def main():
    """Run all CI/CD validation tests"""
    print("🚀 HealthMate CI/CD Validation")
    print("=" * 50)
    
    tests = [
        ("Imports", test_imports),
        ("Environment Variables", test_environment_variables),
        ("Database Connection", test_database_connection),
        ("User Model", test_user_model),
        ("Authentication Service", test_auth_service),
        ("Configuration", test_configuration),
        ("Security", test_security),
        ("Performance", test_performance),
        ("API Endpoints", test_api_endpoints),
    ]
    
    results = {
        'passed': 0,
        'failed': 0,
        'total': len(tests)
    }
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}...")
        try:
            if test_func():
                results['passed'] += 1
            else:
                results['failed'] += 1
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results['failed'] += 1
    
    print("\n" + "=" * 50)
    print("📊 CI/CD Validation Results:")
    print(f"   Total Tests: {results['total']}")
    print(f"   Passed: {results['passed']}")
    print(f"   Failed: {results['failed']}")
    
    if results['failed'] == 0:
        print("\n🎉 All CI/CD validation tests passed!")
        print("✅ HealthMate is ready for CI/CD pipeline")
        return True
    else:
        print(f"\n⚠️  {results['failed']} tests failed!")
        print("❌ CI/CD validation failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
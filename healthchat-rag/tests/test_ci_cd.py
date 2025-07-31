#!/usr/bin/env python3
"""
CI/CD Pipeline Test Suite for HealthMate

This module contains tests specifically designed to validate
the CI/CD pipeline and ensure all components work correctly
in automated environments.
"""

import pytest
import requests
import time
import os
import sys
from typing import Dict, Any

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from app.database import get_db, engine
from app.models.user import User, Base
from app.services.auth import AuthService
from app.config import settings


class TestCICDPipeline:
    """Test suite for CI/CD pipeline validation"""

    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Set up test database"""
        # Create all tables
        Base.metadata.create_all(bind=engine)
        yield
        # Clean up
        Base.metadata.drop_all(bind=engine)

    def test_database_connection(self):
        """Test database connection in CI environment"""
        try:
            with engine.connect() as conn:
                result = conn.execute("SELECT 1")
                assert result.fetchone()[0] == 1
            print("✅ Database connection test passed")
        except Exception as e:
            pytest.fail(f"Database connection failed: {e}")

    def test_user_model_creation(self):
        """Test user model creation and validation"""
        try:
            # Test user creation
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
            print("✅ User model creation test passed")
        except Exception as e:
            pytest.fail(f"User model creation failed: {e}")

    def test_auth_service_initialization(self):
        """Test authentication service initialization"""
        try:
            auth_service = AuthService(settings.secret_key)
            assert auth_service is not None
            assert hasattr(auth_service, 'get_password_hash')
            assert hasattr(auth_service, 'verify_password')
            print("✅ Auth service initialization test passed")
        except Exception as e:
            pytest.fail(f"Auth service initialization failed: {e}")

    def test_password_hashing(self):
        """Test password hashing functionality"""
        try:
            auth_service = AuthService(settings.secret_key)
            test_password = "TestPass123!"
            
            # Hash password
            hashed = auth_service.get_password_hash(test_password)
            assert hashed != test_password
            assert len(hashed) > 0
            
            # Verify password
            is_valid = auth_service.verify_password(test_password, hashed)
            assert is_valid is True
            
            # Test invalid password
            is_invalid = auth_service.verify_password("WrongPassword", hashed)
            assert is_invalid is False
            
            print("✅ Password hashing test passed")
        except Exception as e:
            pytest.fail(f"Password hashing test failed: {e}")

    def test_environment_variables(self):
        """Test required environment variables are set"""
        required_vars = [
            'POSTGRES_URI',
            'SECRET_KEY'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            pytest.fail(f"Missing required environment variables: {missing_vars}")
        
        print("✅ Environment variables test passed")

    def test_imports(self):
        """Test all critical imports work correctly"""
        try:
            # Test core imports
            from app.main import app
            from app.routers import auth_router, health_router
            from app.models.user import User
            from app.services.auth import AuthService
            from app.utils.security_middleware import SecurityMiddleware
            from app.utils.correlation_id_middleware import CorrelationIdMiddleware
            
            assert app is not None
            assert auth_router is not None
            assert health_router is not None
            
            print("✅ Import test passed")
        except ImportError as e:
            pytest.fail(f"Import test failed: {e}")

    def test_configuration(self):
        """Test configuration loading"""
        try:
            from app.config import settings
            
            # Test required settings
            assert hasattr(settings, 'secret_key')
            assert hasattr(settings, 'database_url')
            assert hasattr(settings, 'cors_origins_list')
            
            print("✅ Configuration test passed")
        except Exception as e:
            pytest.fail(f"Configuration test failed: {e}")


class TestAPIIntegration:
    """Test API integration for CI/CD"""

    @pytest.fixture
    def api_base_url(self):
        """Get API base URL from environment or use default"""
        return os.getenv('HEALTHMATE_API_URL', 'http://localhost:8000')

    def test_health_endpoint(self, api_base_url):
        """Test health endpoint is accessible"""
        try:
            response = requests.get(f"{api_base_url}/health", timeout=10)
            assert response.status_code == 200
            data = response.json()
            assert 'status' in data
            print("✅ Health endpoint test passed")
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Health endpoint not accessible: {e}")

    def test_docs_endpoint(self, api_base_url):
        """Test API documentation endpoint"""
        try:
            response = requests.get(f"{api_base_url}/docs", timeout=10)
            assert response.status_code == 200
            assert 'text/html' in response.headers.get('content-type', '')
            print("✅ Docs endpoint test passed")
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Docs endpoint not accessible: {e}")

    def test_openapi_endpoint(self, api_base_url):
        """Test OpenAPI specification endpoint"""
        try:
            response = requests.get(f"{api_base_url}/openapi.json", timeout=10)
            assert response.status_code == 200
            data = response.json()
            assert 'openapi' in data
            assert 'paths' in data
            print("✅ OpenAPI endpoint test passed")
        except requests.exceptions.RequestException as e:
            pytest.skip(f"OpenAPI endpoint not accessible: {e}")


class TestSecurity:
    """Test security features for CI/CD"""

    def test_secret_key_strength(self):
        """Test secret key meets minimum requirements"""
        secret_key = os.getenv('SECRET_KEY', '')
        
        # Check minimum length
        assert len(secret_key) >= 32, "Secret key should be at least 32 characters"
        
        # Check for common weak patterns
        weak_patterns = ['test', 'dummy', 'default', 'secret']
        for pattern in weak_patterns:
            assert pattern not in secret_key.lower(), f"Secret key contains weak pattern: {pattern}"
        
        print("✅ Secret key strength test passed")

    def test_cors_configuration(self):
        """Test CORS configuration"""
        try:
            from app.config import settings
            
            # Check CORS origins are configured
            assert hasattr(settings, 'cors_origins_list')
            assert isinstance(settings.cors_origins_list, list)
            
            print("✅ CORS configuration test passed")
        except Exception as e:
            pytest.fail(f"CORS configuration test failed: {e}")


class TestPerformance:
    """Test performance requirements for CI/CD"""

    def test_import_performance(self):
        """Test that imports complete within reasonable time"""
        import time
        
        start_time = time.time()
        
        # Import all major modules
        from app.main import app
        from app.routers import auth_router, health_router
        from app.models.user import User
        from app.services.auth import AuthService
        
        end_time = time.time()
        import_time = end_time - start_time
        
        # Import should complete within 5 seconds
        assert import_time < 5.0, f"Import time too slow: {import_time:.2f}s"
        
        print(f"✅ Import performance test passed ({import_time:.2f}s)")

    def test_database_performance(self):
        """Test database operations performance"""
        import time
        
        start_time = time.time()
        
        # Test database connection
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        
        end_time = time.time()
        db_time = end_time - start_time
        
        # Database operation should complete within 1 second
        assert db_time < 1.0, f"Database operation too slow: {db_time:.2f}s"
        
        print(f"✅ Database performance test passed ({db_time:.2f}s)")


def run_ci_cd_tests():
    """Run all CI/CD tests and return results"""
    print("🧪 Running CI/CD Pipeline Tests...")
    print("=" * 50)
    
    # Test categories
    test_categories = [
        TestCICDPipeline,
        TestAPIIntegration,
        TestSecurity,
        TestPerformance
    ]
    
    results = {
        'passed': 0,
        'failed': 0,
        'skipped': 0,
        'total': 0
    }
    
    for test_class in test_categories:
        print(f"\n📋 Running {test_class.__name__}...")
        
        # Get all test methods
        test_methods = [method for method in dir(test_class) 
                       if method.startswith('test_')]
        
        for method_name in test_methods:
            results['total'] += 1
            try:
                # Create test instance and run method
                test_instance = test_class()
                if hasattr(test_instance, 'setup_database'):
                    test_instance.setup_database()
                
                method = getattr(test_instance, method_name)
                method()
                results['passed'] += 1
                print(f"  ✅ {method_name}")
                
            except Exception as e:
                results['failed'] += 1
                print(f"  ❌ {method_name}: {e}")
    
    print("\n" + "=" * 50)
    print("📊 CI/CD Test Results:")
    print(f"   Total Tests: {results['total']}")
    print(f"   Passed: {results['passed']}")
    print(f"   Failed: {results['failed']}")
    print(f"   Skipped: {results['skipped']}")
    
    if results['failed'] == 0:
        print("\n🎉 All CI/CD tests passed!")
        return True
    else:
        print(f"\n⚠️  {results['failed']} tests failed!")
        return False


if __name__ == "__main__":
    success = run_ci_cd_tests()
    sys.exit(0 if success else 1) 
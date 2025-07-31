"""
Pytest configuration and fixtures for HealthMate tests.

This module provides test fixtures, database setup, and utility functions
for running comprehensive tests across the HealthMate application.
"""

import pytest
import asyncio
import tempfile
import os
import shutil
from typing import Generator, Dict, Any
from unittest.mock import Mock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient
from fastapi import FastAPI

# Set up test environment variables before importing app
import os
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("PINECONE_API_KEY", "test-pinecone-key")
os.environ.setdefault("PINECONE_ENVIRONMENT", "test-environment")
os.environ.setdefault("PINECONE_INDEX_NAME", "test-index")
os.environ.setdefault("POSTGRES_URI", "sqlite:///./test.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")  # pragma: allowlist secret
os.environ.setdefault("HEALTHMATE_ENVIRONMENT", "test")

# Import application components
from app.database import get_db, Base
from app.main import app
from app.models.user import User
from app.models.health_data import HealthData
from app.services.auth import AuthService
from app.utils.jwt_utils import jwt_manager
from app.utils.encryption_utils import encryption_manager

# Test database configuration
TEST_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    yield engine
    engine.dispose()

@pytest.fixture(scope="session")
def test_db_setup(test_engine):
    """Setup test database tables."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def db_session(test_engine, test_db_setup):
    """Create a new database session for a test."""
    TestingSessionLocal = sessionmaker(
        autocommit=False, 
        autoflush=False, 
        bind=test_engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def client(db_session) -> Generator[TestClient, None, None]:
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def auth_service():
    """Create an AuthService instance for testing."""
    return AuthService(secret_key="test-secret-key-for-testing-only")

@pytest.fixture
def sample_user_data() -> Dict[str, Any]:
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User",
        "age": 30,
        "medical_conditions": "None",
        "medications": "None",
        "role": "patient"
    }

@pytest.fixture
def sample_user(db_session, sample_user_data, auth_service) -> User:
    """Create a sample user in the test database."""
    user = User(
        email=sample_user_data["email"],
        hashed_password=auth_service.get_password_hash(sample_user_data["password"]),
        full_name=sample_user_data["full_name"],
        age=sample_user_data["age"],
        medical_conditions=sample_user_data["medical_conditions"],
        medications=sample_user_data["medications"],
        role=sample_user_data["role"]
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def admin_user_data() -> Dict[str, Any]:
    """Admin user data for testing."""
    return {
        "email": "admin@example.com",
        "password": "AdminPassword123!",
        "full_name": "Admin User",
        "age": 35,
        "medical_conditions": "None",
        "medications": "None",
        "role": "admin"
    }

@pytest.fixture
def admin_user(db_session, admin_user_data, auth_service) -> User:
    """Create an admin user in the test database."""
    user = User(
        email=admin_user_data["email"],
        hashed_password=auth_service.get_password_hash(admin_user_data["password"]),
        full_name=admin_user_data["full_name"],
        age=admin_user_data["age"],
        medical_conditions=admin_user_data["medical_conditions"],
        medications=admin_user_data["medications"],
        role=admin_user_data["role"]
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def authenticated_client(client, sample_user) -> TestClient:
    """Create a test client with authenticated user."""
    # Login to get tokens
    login_data = {
        "email": sample_user.email,
        "password": "TestPassword123!"
    }
    response = client.post("/auth/login", json=login_data)
    tokens = response.json()
    
    # Set authorization header
    client.headers.update({
        "Authorization": f"Bearer {tokens['access_token']}"
    })
    return client

@pytest.fixture
def admin_client(client, admin_user) -> TestClient:
    """Create a test client with authenticated admin user."""
    # Login to get tokens
    login_data = {
        "email": admin_user.email,
        "password": "AdminPassword123!"
    }
    response = client.post("/auth/login", json=login_data)
    tokens = response.json()
    
    # Set authorization header
    client.headers.update({
        "Authorization": f"Bearer {tokens['access_token']}"
    })
    return client

@pytest.fixture
def sample_health_data() -> Dict[str, Any]:
    """Sample health data for testing."""
    return {
        "user_id": 1,
        "data_type": "blood_pressure",
        "value": "120/80",
        "unit": "mmHg",
        "timestamp": "2024-01-01T10:00:00Z",
        "notes": "Normal reading"
    }

@pytest.fixture
def sample_health_record(db_session, sample_user, sample_health_data) -> HealthData:
    """Create a sample health data record in the test database."""
    health_data = HealthData(
        user_id=sample_user.id,
        data_type=sample_health_data["data_type"],
        value=sample_health_data["value"],
        unit=sample_health_data["unit"],
        timestamp=sample_health_data["timestamp"],
        notes=sample_health_data["notes"]
    )
    db_session.add(health_data)
    db_session.commit()
    db_session.refresh(health_data)
    return health_data

@pytest.fixture
def mock_redis():
    """Mock Redis for testing."""
    with patch('app.utils.jwt_utils.redis_client') as mock_redis:
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True
        mock_redis.delete.return_value = 1
        mock_redis.exists.return_value = 0
        yield mock_redis

@pytest.fixture
def mock_openai():
    """Mock OpenAI API for testing."""
    with patch('app.services.openai_agent.openai') as mock_openai:
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "This is a test response"
        mock_openai.ChatCompletion.create.return_value = mock_response
        yield mock_openai

@pytest.fixture
def temp_dir():
    """Create a temporary directory for file-based tests."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing."""
    env_vars = {
        "SECRET_KEY": "test-secret-key-for-testing-only",  # pragma: allowlist secret
        "ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "30",
        "REFRESH_TOKEN_EXPIRE_DAYS": "7",
        "DATABASE_URL": TEST_DATABASE_URL,
        "REDIS_URL": "redis://localhost:6379/0",
        "OPENAI_API_KEY": "test-openai-key",  # pragma: allowlist secret
        "PINECONE_API_KEY": "test-pinecone-key",  # pragma: allowlist secret
        "PINECONE_ENVIRONMENT": "test-environment",
        "ENCRYPTION_KEY": "test-encryption-key-32-bytes-long",
        "CORS_ALLOW_ORIGINS": "*"
    }
    
    with patch.dict(os.environ, env_vars):
        yield env_vars

# Test utilities
class TestUtils:
    """Utility functions for tests."""
    
    @staticmethod
    def create_test_user(db_session: Session, **kwargs) -> User:
        """Create a test user with custom attributes."""
        default_data = {
            "email": f"test{kwargs.get('id', 1)}@example.com",
            "password": "TestPassword123!",
            "full_name": f"Test User {kwargs.get('id', 1)}",
            "age": 30,
            "medical_conditions": "None",
            "medications": "None",
            "role": "patient"
        }
        default_data.update(kwargs)
        
        user = User(
            email=default_data["email"],
            hashed_password=AuthService().get_password_hash(default_data["password"]),
            full_name=default_data["full_name"],
            age=default_data["age"],
            medical_conditions=default_data["medical_conditions"],
            medications=default_data["medications"],
            role=default_data["role"]
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    
    @staticmethod
    def create_test_health_data(db_session: Session, user_id: int, **kwargs) -> HealthData:
        """Create test health data with custom attributes."""
        default_data = {
            "data_type": "blood_pressure",
            "value": "120/80",
            "unit": "mmHg",
            "timestamp": "2024-01-01T10:00:00Z",
            "notes": "Test reading"
        }
        default_data.update(kwargs)
        
        health_data = HealthData(
            user_id=user_id,
            data_type=default_data["data_type"],
            value=default_data["value"],
            unit=default_data["unit"],
            timestamp=default_data["timestamp"],
            notes=default_data["notes"]
        )
        db_session.add(health_data)
        db_session.commit()
        db_session.refresh(health_data)
        return health_data
    
    @staticmethod
    def get_auth_headers(client: TestClient, email: str, password: str) -> Dict[str, str]:
        """Get authentication headers for a user."""
        response = client.post("/auth/login", json={"email": email, "password": password})
        tokens = response.json()
        return {"Authorization": f"Bearer {tokens['access_token']}"}

# Make TestUtils available as a fixture
@pytest.fixture
def test_utils():
    """Provide TestUtils class for tests."""
    return TestUtils 
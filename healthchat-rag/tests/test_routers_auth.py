import pytest
from fastapi.testclient import TestClient
from app.main import app
import random

client = TestClient(app)

def test_register_and_login():
    # Use a random email to avoid conflicts
    email = f"testuser_{random.randint(1000,9999)}@example.com"
    password = "testpassword123"  # pragma: allowlist secret
    data = {
        "email": email,
        "password": password,  # pragma: allowlist secret
        "full_name": "Test User",
        "age": 30,
        "medical_conditions": "hypertension",
        "medications": "aspirin"
    }
    # Register
    response = client.post("/auth/register", json=data)
    assert response.status_code == 200 or response.status_code == 409  # 409 if already exists
    # Login
    login_data = {"email": email, "password": password}  # pragma: allowlist secret
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 200
    result = response.json()
    assert "access_token" in result
    assert result["token_type"] == "bearer" 
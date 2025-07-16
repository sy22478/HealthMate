import pytest
from fastapi.testclient import TestClient
from app.main import app
import random
from unittest.mock import MagicMock

client = TestClient(app)

def get_token():
    email = f"testchat_{random.randint(1000,9999)}@example.com"
    password = "testpassword123"  # pragma: allowlist secret
    data = {
        "email": email,
        "password": password,  # pragma: allowlist secret
        "full_name": "Chat User",
        "age": 25,
        "medical_conditions": "none",
        "medications": "none"
    }
    client.post("/auth/register", json=data)
    response = client.post("/auth/login", json={"email": email, "password": password})
    return response.json()["access_token"]

def setup_module(module):
    # Patch app.state.knowledge_base with a mock for testing
    mock_kb = MagicMock()
    mock_kb.get_relevant_context.return_value = "Test context"
    app.state.knowledge_base = mock_kb

def test_chat_message():
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    data = {"message": "What should I do if I have a headache?"}
    response = client.post("/chat/message", json=data, headers=headers)
    assert response.status_code == 200
    result = response.json()
    # Accept either dict or string response
    assert isinstance(result, dict) or isinstance(result, str)
    if isinstance(result, dict):
        assert "message" in result or "response" in result
    else:
        assert "headache" in result.lower() or "consult" in result.lower() or "response" in result.lower() 
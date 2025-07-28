"""
Integration tests for API workflows.

This module tests complete API workflows including user registration,
authentication, health data operations, and chat functionality.
"""

import pytest
import json
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.user import User
from app.models.health_data import HealthData
from app.services.auth import AuthService

class TestUserRegistrationAndLogin:
    """Test complete user registration and login workflows."""
    
    def test_user_registration_workflow(self, client: TestClient):
        """Test complete user registration workflow."""
        # Test user registration
        registration_data = {
            "email": "newuser@example.com",
            "password": "StrongPassword123!",
            "full_name": "New Test User",
            "age": 25,
            "medical_conditions": "None",
            "medications": "None",
            "role": "patient"
        }
        
        response = client.post("/auth/register", json=registration_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert data["message"] == "User registered successfully"
        assert "user_id" in data
        assert "email" in data
        assert data["email"] == "newuser@example.com"
    
    def test_user_login_workflow(self, client: TestClient, sample_user):
        """Test complete user login workflow."""
        # Test user login
        login_data = {
            "email": sample_user.email,
            "password": "TestPassword123!"
        }
        
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == sample_user.email
    
    def test_user_login_invalid_credentials(self, client: TestClient):
        """Test login with invalid credentials."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "WrongPassword"
        }
        
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]
    
    def test_user_registration_duplicate_email(self, client: TestClient, sample_user):
        """Test registration with duplicate email."""
        registration_data = {
            "email": sample_user.email,  # Use existing email
            "password": "StrongPassword123!",
            "full_name": "Duplicate User",
            "age": 30,
            "medical_conditions": "None",
            "medications": "None",
            "role": "patient"
        }
        
        response = client.post("/auth/register", json=registration_data)
        assert response.status_code == 409
        assert "User already exists" in response.json()["detail"]
    
    def test_password_change_workflow(self, authenticated_client: TestClient):
        """Test password change workflow."""
        # Change password
        password_change_data = {
            "current_password": "TestPassword123!",
            "new_password": "NewStrongPassword123!"
        }
        
        response = authenticated_client.post("/auth/change-password", json=password_change_data)
        assert response.status_code == 200
        assert "Password changed successfully" in response.json()["message"]
        
        # Try to login with old password (should fail)
        login_data = {
            "email": "test@example.com",
            "password": "TestPassword123!"
        }
        
        response = authenticated_client.post("/auth/login", json=login_data)
        assert response.status_code == 401
        
        # Login with new password (should succeed)
        login_data["password"] = "NewStrongPassword123!"
        response = authenticated_client.post("/auth/login", json=login_data)
        assert response.status_code == 200

class TestHealthDataWorkflows:
    """Test health data CRUD operations workflows."""
    
    def test_health_data_creation_workflow(self, authenticated_client: TestClient):
        """Test complete health data creation workflow."""
        health_data = {
            "data_type": "blood_pressure",
            "value": "120/80",
            "unit": "mmHg",
            "timestamp": "2024-01-01T10:00:00Z",
            "notes": "Normal reading"
        }
        
        # Create health data
        response = authenticated_client.post("/health/data", json=health_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert data["data_type"] == "blood_pressure"
        assert data["value"] == "120/80"
    
    def test_health_data_retrieval_workflow(self, authenticated_client: TestClient, sample_health_record):
        """Test health data retrieval workflow."""
        # Get all health data
        response = authenticated_client.get("/health/data")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Get specific health data
        response = authenticated_client.get(f"/health/data/{sample_health_record.id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == sample_health_record.id
        assert data["data_type"] == sample_health_record.data_type
    
    def test_health_data_update_workflow(self, authenticated_client: TestClient, sample_health_record):
        """Test health data update workflow."""
        update_data = {
            "value": "130/85",
            "notes": "Updated reading"
        }
        
        response = authenticated_client.put(f"/health/data/{sample_health_record.id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["value"] == "130/85"
        assert data["notes"] == "Updated reading"
    
    def test_health_data_deletion_workflow(self, authenticated_client: TestClient, sample_health_record):
        """Test health data deletion workflow."""
        # Delete health data
        response = authenticated_client.delete(f"/health/data/{sample_health_record.id}")
        assert response.status_code == 200
        
        # Verify it's deleted
        response = authenticated_client.get(f"/health/data/{sample_health_record.id}")
        assert response.status_code == 404
    
    def test_health_data_unauthorized_access(self, client: TestClient, sample_health_record):
        """Test unauthorized access to health data."""
        # Try to access health data without authentication
        response = client.get(f"/health/data/{sample_health_record.id}")
        assert response.status_code == 401
    
    def test_health_data_cross_user_access(self, authenticated_client: TestClient, admin_client: TestClient, sample_health_record):
        """Test that users can't access other users' health data."""
        # Try to access health data from different user
        response = authenticated_client.get(f"/health/data/{sample_health_record.id}")
        # This should either return 404 or 403 depending on implementation
        assert response.status_code in [403, 404]

class TestChatWorkflows:
    """Test chat and AI conversation workflows."""
    
    def test_chat_message_workflow(self, authenticated_client: TestClient, mock_openai):
        """Test complete chat message workflow."""
        chat_data = {
            "message": "What are the symptoms of diabetes?",
            "conversation_id": None  # New conversation
        }
        
        response = authenticated_client.post("/chat/send", json=chat_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "response" in data
        assert "conversation_id" in data
        assert "message_id" in data
        
        # Verify the response contains the expected content
        assert "This is a test response" in data["response"]
    
    def test_chat_conversation_history(self, authenticated_client: TestClient, mock_openai):
        """Test chat conversation history workflow."""
        # Send first message
        chat_data1 = {
            "message": "Hello, I have a question about my health.",
            "conversation_id": None
        }
        
        response1 = authenticated_client.post("/chat/send", json=chat_data1)
        assert response1.status_code == 200
        
        conversation_id = response1.json()["conversation_id"]
        
        # Send follow-up message
        chat_data2 = {
            "message": "Can you tell me more about that?",
            "conversation_id": conversation_id
        }
        
        response2 = authenticated_client.post("/chat/send", json=chat_data2)
        assert response2.status_code == 200
        
        # Get conversation history
        response = authenticated_client.get(f"/chat/conversation/{conversation_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "messages" in data
        assert len(data["messages"]) >= 2
    
    def test_chat_conversation_list(self, authenticated_client: TestClient):
        """Test getting list of user conversations."""
        response = authenticated_client.get("/chat/conversations")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_chat_unauthorized_access(self, client: TestClient):
        """Test unauthorized access to chat endpoints."""
        chat_data = {
            "message": "Test message",
            "conversation_id": None
        }
        
        response = client.post("/chat/send", json=chat_data)
        assert response.status_code == 401

class TestHealthCalculations:
    """Test health calculation endpoints."""
    
    def test_bmi_calculation_workflow(self, client: TestClient):
        """Test BMI calculation workflow."""
        bmi_data = {
            "weight_kg": 70,
            "height_m": 1.75
        }
        
        response = client.post("/health/bmi", json=bmi_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "bmi" in data
        assert "category" in data
        assert isinstance(data["bmi"], float)
        assert data["bmi"] > 0
    
    def test_symptom_check_workflow(self, client: TestClient):
        """Test symptom check workflow."""
        symptom_data = {
            "symptoms": ["headache", "fever"],
            "severity": "moderate"
        }
        
        response = client.post("/health/symptoms", json=symptom_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "analysis" in data
        assert "recommendations" in data
    
    def test_drug_interaction_workflow(self, client: TestClient):
        """Test drug interaction check workflow."""
        drug_data = {
            "medications": ["aspirin", "ibuprofen"]
        }
        
        response = client.post("/health/drug-interactions", json=drug_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "interactions" in data
        assert "warnings" in data

class TestAuthenticationWorkflows:
    """Test authentication-related workflows."""
    
    def test_token_refresh_workflow(self, client: TestClient, sample_user):
        """Test token refresh workflow."""
        # First login to get tokens
        login_data = {
            "email": sample_user.email,
            "password": "TestPassword123!"
        }
        
        login_response = client.post("/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        refresh_token = login_response.json()["refresh_token"]
        
        # Refresh the token
        refresh_data = {
            "refresh_token": refresh_token
        }
        
        response = client.post("/auth/refresh", json=refresh_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    def test_logout_workflow(self, authenticated_client: TestClient):
        """Test logout workflow."""
        # Get current token (this would be from the authenticated client)
        # For this test, we'll assume the client has a valid token
        
        logout_data = {
            "token": "current_token_here"  # In real test, extract from client
        }
        
        response = authenticated_client.post("/auth/logout", json=logout_data)
        assert response.status_code == 200
        
        # Try to use the same token (should fail)
        # This would require extracting the token from the authenticated client
        # For now, we just verify the logout endpoint works
    
    def test_user_profile_workflow(self, authenticated_client: TestClient):
        """Test user profile management workflow."""
        # Get current user info
        response = authenticated_client.get("/auth/me")
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert "full_name" in data
        assert "role" in data
    
    def test_admin_workflows(self, admin_client: TestClient):
        """Test admin-specific workflows."""
        # Get token statistics (admin only)
        response = admin_client.get("/auth/token-stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "blacklisted_tokens" in data
        assert "active_refresh_tokens" in data
        
        # Get authentication stats (admin only)
        response = admin_client.get("/auth/auth-stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_users" in data
        assert "active_sessions" in data

class TestErrorHandling:
    """Test error handling in API workflows."""
    
    def test_invalid_json_request(self, authenticated_client: TestClient):
        """Test handling of invalid JSON requests."""
        response = authenticated_client.post(
            "/health/data",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_missing_required_fields(self, authenticated_client: TestClient):
        """Test handling of missing required fields."""
        health_data = {
            "data_type": "blood_pressure"
            # Missing required fields
        }
        
        response = authenticated_client.post("/health/data", json=health_data)
        assert response.status_code == 422
    
    def test_invalid_data_types(self, authenticated_client: TestClient):
        """Test handling of invalid data types."""
        health_data = {
            "data_type": "blood_pressure",
            "value": 123,  # Should be string
            "unit": "mmHg",
            "timestamp": "2024-01-01T10:00:00Z",
            "notes": "Test"
        }
        
        response = authenticated_client.post("/health/data", json=health_data)
        # This might be 422 (validation error) or 200 (if the API accepts it)
        assert response.status_code in [200, 422]
    
    def test_nonexistent_resource(self, authenticated_client: TestClient):
        """Test handling of requests for nonexistent resources."""
        response = authenticated_client.get("/health/data/99999")
        assert response.status_code == 404

class TestPerformance:
    """Test API performance characteristics."""
    
    def test_concurrent_requests(self, client: TestClient):
        """Test handling of concurrent requests."""
        import threading
        import time
        
        results = []
        
        def make_request():
            response = client.get("/health/bmi")
            results.append(response.status_code)
        
        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        assert all(status == 200 for status in results)
    
    def test_large_payload_handling(self, authenticated_client: TestClient):
        """Test handling of large payloads."""
        # Create a large health data payload
        large_notes = "x" * 10000  # 10KB of data
        
        health_data = {
            "data_type": "notes",
            "value": "Large data test",
            "unit": "text",
            "timestamp": "2024-01-01T10:00:00Z",
            "notes": large_notes
        }
        
        response = authenticated_client.post("/health/data", json=health_data)
        # Should either succeed or return a reasonable error
        assert response.status_code in [200, 413, 422] 
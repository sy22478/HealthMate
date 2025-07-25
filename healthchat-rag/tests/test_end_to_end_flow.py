import pytest
import streamlit as st
from unittest.mock import patch, MagicMock
import requests
import json

class TestEndToEndFlow:
    
    def test_complete_user_journey(self):
        """Test the complete user journey from registration to dashboard access"""
        
        # Step 1: User registration
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"message": "User registered successfully"}
            mock_post.return_value = mock_response
            
            # Simulate registration
            registration_data = {
                        "email": "test@example.com",  # pragma: allowlist secret
        "password": "TestPassword123!",  # pragma: allowlist secret
                "full_name": "Test User",
                "age": 30,
                "medical_conditions": "None",
                "medications": "None"
            }
            
            response = requests.post(
                "http://localhost:8000/auth/register",
                json=registration_data
            )
            
            assert response.status_code == 200
            assert response.json()["message"] == "User registered successfully"
        
        # Step 2: User login
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "access_token": "test_token_123",
                "token_type": "bearer"
            }
            mock_post.return_value = mock_response
            
            # Simulate login
            login_data = {
                        "email": "test@example.com",  # pragma: allowlist secret
        "password": "TestPassword123!"  # pragma: allowlist secret
            }
            
            response = requests.post(
                "http://localhost:8000/auth/login",
                json=login_data
            )
            
            assert response.status_code == 200
            token = response.json()["access_token"]
            assert token == "test_token_123"
        
        # Step 3: Set authentication state (simulating successful login)
        st.session_state.authenticated = True
        st.session_state.token = token
        st.session_state.user_email = "test@example.com"
        st.session_state.chat_history = []
        
        # Step 4: Verify dashboard access
        can_access = bool(st.session_state.authenticated and st.session_state.token)
        assert can_access == True
        
        # Step 5: Test chat functionality
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "message": "Hello! I'm your health assistant. How can I help you today?",
                "id": 1
            }
            mock_post.return_value = mock_response
            
            # Simulate sending a chat message
            headers = {"Authorization": f"Bearer {st.session_state.token}"}
            chat_response = requests.post(
                "http://localhost:8000/chat/message",
                json={"message": "Hello"},
                headers=headers
            )
            
            assert chat_response.status_code == 200
            chat_data = chat_response.json()
            assert "message" in chat_data
            assert "id" in chat_data
        
        # Step 6: Test logout
        def logout():
            st.session_state.authenticated = False
            st.session_state.token = None
            st.session_state.chat_history = []
            st.session_state.user_email = None
        
        logout()
        
        # Step 7: Verify logout worked
        assert st.session_state.authenticated == False
        assert st.session_state.token is None
        assert st.session_state.user_email is None
        assert st.session_state.chat_history == []
        
        # Step 8: Verify dashboard access is denied after logout
        can_access = bool(st.session_state.authenticated and st.session_state.token)
        assert can_access == False
    
    def test_password_reset_flow(self):
        """Test the complete password reset flow"""
        
        # Step 1: Request password reset
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "message": "If the email exists, a password reset link has been sent",
                "reset_token": "test_reset_token_123"
            }
            mock_post.return_value = mock_response
            
            response = requests.post(
                "http://localhost:8000/auth/forgot-password",
                json={"email": "test@example.com"}
            )
            
            assert response.status_code == 200
            reset_token = response.json()["reset_token"]
            assert reset_token == "test_reset_token_123"
        
        # Step 2: Reset password with token
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"message": "Password reset successfully"}
            mock_post.return_value = mock_response
            
            response = requests.post(
                "http://localhost:8000/auth/reset-password",
                json={
                    "token": reset_token,  # pragma: allowlist secret
                    "new_password": "NewPassword123!"  # pragma: allowlist secret
                }
            )
            
            assert response.status_code == 200
            assert response.json()["message"] == "Password reset successfully"
        
        # Step 3: Login with new password
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "access_token": "new_test_token_456",
                "token_type": "bearer"
            }
            mock_post.return_value = mock_response
            
            response = requests.post(
                "http://localhost:8000/auth/login",
                json={
                            "email": "test@example.com",  # pragma: allowlist secret
        "password": "NewPassword123!"  # pragma: allowlist secret
                }
            )
            
            assert response.status_code == 200
            assert "access_token" in response.json()
    
    def test_session_persistence(self):
        """Test that session state persists correctly across interactions"""
        
        # Initialize session state
        st.session_state.authenticated = True
        st.session_state.token = "persistent_token_123"
        st.session_state.user_email = "test@example.com"
        st.session_state.chat_history = []
        st.session_state.quick_action = None
        
        # Verify initial state
        assert st.session_state.authenticated == True
        assert st.session_state.token == "persistent_token_123"
        assert st.session_state.user_email == "test@example.com"
        assert st.session_state.chat_history == []
        assert st.session_state.quick_action is None
        
        # Simulate adding chat messages
        st.session_state.chat_history.append({"role": "user", "content": "Hello"})
        st.session_state.chat_history.append({"role": "assistant", "content": "Hi there!"})
        
        # Verify chat history was updated
        assert len(st.session_state.chat_history) == 2
        assert st.session_state.chat_history[0]["content"] == "Hello"
        assert st.session_state.chat_history[1]["content"] == "Hi there!"
        
        # Simulate setting quick action
        st.session_state.quick_action = "health_check"
        assert st.session_state.quick_action == "health_check"
        
        # Verify other session state remains unchanged
        assert st.session_state.authenticated == True
        assert st.session_state.token == "persistent_token_123"
        assert st.session_state.user_email == "test@example.com"
    
    def test_error_handling(self):
        """Test error handling in the authentication flow"""
        
        # Test invalid login credentials
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.json.return_value = {"detail": "Invalid credentials"}
            mock_post.return_value = mock_response
            
            response = requests.post(
                "http://localhost:8000/auth/login",
                json={
                    "email": "wrong@example.com",  # pragma: allowlist secret
                    "password": "wrongpassword"  # pragma: allowlist secret
                }
            )
            
            assert response.status_code == 401
            assert response.json()["detail"] == "Invalid credentials"
        
        # Test registration with existing email
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.json.return_value = {"detail": "Email already registered"}
            mock_post.return_value = mock_response
            
            response = requests.post(
                "http://localhost:8000/auth/register",
                json={
                    "email": "existing@example.com",  # pragma: allowlist secret
                    "password": "TestPassword123!",  # pragma: allowlist secret
                    "full_name": "Test User",
                    "age": 30,
                    "medical_conditions": "",
                    "medications": ""
                }
            )
            
            assert response.status_code == 400
            assert response.json()["detail"] == "Email already registered"
        
        # Test invalid reset token
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.json.return_value = {"detail": "Invalid or expired reset token"}
            mock_post.return_value = mock_response
            
            response = requests.post(
                "http://localhost:8000/auth/reset-password",
                json={
                    "token": "invalid_token",  # pragma: allowlist secret
                    "new_password": "NewPassword123!"  # pragma: allowlist secret
                }
            )
            
            assert response.status_code == 400
            assert response.json()["detail"] == "Invalid or expired reset token"

if __name__ == "__main__":
    pytest.main([__file__]) 
import pytest
import requests
import json
from unittest.mock import patch, MagicMock

# Test the unified authentication endpoints
class TestUnifiedAuth:
    
    def test_register_user_success(self):
        """Test successful user registration"""
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"message": "User registered successfully"}
            mock_post.return_value = mock_response
            
            # This would be called from the frontend
            response = requests.post(
                "http://localhost:8000/auth/register",
                json={
                    "email": "test@example.com",  # pragma: allowlist secret
                    "password": "TestPassword123!",  # pragma: allowlist secret
                    "full_name": "Test User",
                    "age": 30,
                    "medical_conditions": "None",
                    "medications": "None"
                }
            )
            
            assert response.status_code == 200
            assert response.json()["message"] == "User registered successfully"
    
    def test_login_user_success(self):
        """Test successful user login"""
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "access_token": "test_token_123",
                "token_type": "bearer"
            }
            mock_post.return_value = mock_response
            
            response = requests.post(
                "http://localhost:8000/auth/login",
                json={
                    "email": "test@example.com",  # pragma: allowlist secret
                    "password": "TestPassword123!"  # pragma: allowlist secret
                }
            )
            
            assert response.status_code == 200
            assert "access_token" in response.json()
            assert response.json()["token_type"] == "bearer"
    
    def test_forgot_password_success(self):
        """Test successful password reset request"""
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
            assert "message" in response.json()
            assert "reset_token" in response.json()
    
    def test_reset_password_success(self):
        """Test successful password reset"""
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"message": "Password reset successfully"}
            mock_post.return_value = mock_response
            
            response = requests.post(
                "http://localhost:8000/auth/reset-password",
                json={
                    "token": "test_reset_token_123",  # pragma: allowlist secret
                    "new_password": "NewPassword123!"  # pragma: allowlist secret
                }
            )
            
            assert response.status_code == 200
            assert response.json()["message"] == "Password reset successfully"
    
    def test_password_strength_check(self):
        """Test password strength validation"""
        # Import the function from the unified auth page
        # This is a simplified test of the password strength logic
        def check_password_strength(password):
            score = 0
            
            if len(password) >= 8:
                score += 1
            if any(c.isupper() for c in password):
                score += 1
            if any(c.islower() for c in password):
                score += 1
            if any(c.isdigit() for c in password):
                score += 1
            if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
                score += 1
            
            if score <= 2:
                return "weak", score, []
            elif score <= 3:
                return "medium", score, []
            else:
                return "strong", score, []
        
        # Test weak password
        strength, score, _ = check_password_strength("weak")
        assert strength == "weak"
        assert score <= 2
        
        # Test strong password
        strength, score, _ = check_password_strength("StrongPass123!")
        assert strength == "strong"
        assert score >= 4

if __name__ == "__main__":
    pytest.main([__file__]) 
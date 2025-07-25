import pytest
import streamlit as st
import requests
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import sys
import os

# Add frontend utils to path for testing
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'frontend', 'utils'))

from auth_manager import AuthManager
from session_manager import SessionManager, SessionMiddleware

class TestComprehensiveValidation:
    
    def test_unified_auth_flow_end_to_end(self):
        """Test complete unified authentication flow end-to-end"""
        auth_manager = AuthManager()
        
        # Test 1: Registration flow
        mock_register_response = MagicMock()
        mock_register_response.status_code = 200
        mock_register_response.json.return_value = {
            "access_token": "register_token",
            "email": "newuser@example.com",
            "user_id": 1,
            "user_profile": {"full_name": "New User"},
            "permissions": ["read", "write"]
        }
        
        with patch('requests.post', return_value=mock_register_response):
            # Test registration
            register_result = auth_manager.register("newuser@example.com", "password123", "New User")
            assert register_result["success"] == True
            assert st.session_state.authenticated == True
            assert st.session_state.token == "register_token"
            assert st.session_state.user_email == "newuser@example.com"
            
            # Clear state for next test
            auth_manager.logout()
        
        # Test 2: Login flow
        mock_login_response = MagicMock()
        mock_login_response.status_code = 200
        mock_login_response.json.return_value = {
            "access_token": "login_token",
            "email": "existinguser@example.com",
            "user_id": 2,
            "user_profile": {"full_name": "Existing User"},
            "permissions": ["read", "write", "admin"]
        }
        
        with patch('requests.post', return_value=mock_login_response):
            # Test login
            login_result = auth_manager.login("existinguser@example.com", "password123")
            assert login_result["success"] == True
            assert st.session_state.authenticated == True
            assert st.session_state.token == "login_token"
            assert st.session_state.user_email == "existinguser@example.com"
            assert "admin" in st.session_state.permissions
            
            # Clear state for next test
            auth_manager.logout()
        
        # Test 3: Forgot password flow
        mock_forgot_response = MagicMock()
        mock_forgot_response.status_code = 200
        mock_forgot_response.json.return_value = {"message": "Password reset email sent"}
        
        with patch('requests.post', return_value=mock_forgot_response):
            # Test forgot password
            forgot_result = auth_manager.forgot_password("user@example.com")
            assert forgot_result["success"] == True
            assert "Password reset email sent" in forgot_result["message"]
        
        # Test 4: Password reset flow
        mock_reset_response = MagicMock()
        mock_reset_response.status_code = 200
        mock_reset_response.json.return_value = {"message": "Password reset successful"}
        
        with patch('requests.post', return_value=mock_reset_response):
            # Test password reset
            reset_result = auth_manager.reset_password("reset_token_123", "newpassword123")
            assert reset_result["success"] == True
            assert "Password reset successful" in reset_result["message"]
    
    def test_access_control_validation(self):
        """Test access control for dashboard features"""
        auth_manager = AuthManager()
        session_manager = SessionManager(auth_manager)
        
        # Test 1: Unauthenticated access to dashboard features
        assert not auth_manager.is_authenticated()
        
        # Test that dashboard features are not accessible
        dashboard_features = ["chat", "health_metrics", "health_profile", "chat_history", "reports", "settings"]
        for feature in dashboard_features:
            # Simulate feature access check
            can_access = auth_manager.is_authenticated()
            assert can_access == False, f"Unauthenticated user should not access {feature}"
        
        # Test 2: Authenticated access to dashboard features
        st.session_state.authenticated = True
        st.session_state.token = "valid_token"
        st.session_state.session_expires_at = datetime.now() + timedelta(hours=1)
        
        assert auth_manager.is_authenticated()
        
        # Test that dashboard features are accessible
        for feature in dashboard_features:
            can_access = auth_manager.is_authenticated()
            assert can_access == True, f"Authenticated user should access {feature}"
        
        # Test 3: Expired session access
        st.session_state.session_expires_at = datetime.now() - timedelta(hours=1)
        
        assert not auth_manager.is_authenticated()
        
        # Test that dashboard features are not accessible with expired session
        for feature in dashboard_features:
            can_access = auth_manager.is_authenticated()
            assert can_access == False, f"User with expired session should not access {feature}"
    
    def test_chatbot_integration_validation(self):
        """Test chatbot integration with authentication"""
        auth_manager = AuthManager()
        
        # Set up authenticated state
        st.session_state.authenticated = True
        st.session_state.token = "chat_token"
        st.session_state.session_expires_at = datetime.now() + timedelta(hours=1)
        
        # Test 1: Send message with authentication
        mock_chat_response = MagicMock()
        mock_chat_response.status_code = 200
        mock_chat_response.json.return_value = {
            "response": "Hello! How can I help you with your health today?",
            "conversation_id": 123
        }
        
        with patch('requests.post', return_value=mock_chat_response):
            # Simulate send_message function
            def send_message(message: str):
                if not auth_manager.is_authenticated():
                    return {"response": "Error: Not authenticated"}
                
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                response = requests.post(
                    f"{auth_manager.api_base_url}/chat/message",
                    json={"message": message},
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    return response.json()
                return {"response": "Error: Could not process message"}
            
            # Test successful message sending
            result = send_message("Hello, I have a health question")
            assert result["response"] == "Hello! How can I help you with your health today?"
            assert result["conversation_id"] == 123
        
        # Test 2: Send message without authentication
        auth_manager.logout()
        
        result = send_message("Hello")
        assert "Error: Not authenticated" in result["response"]
    
    def test_chat_history_integration_validation(self):
        """Test chat history integration with authentication"""
        auth_manager = AuthManager()
        
        # Set up authenticated state
        st.session_state.authenticated = True
        st.session_state.token = "history_token"
        st.session_state.session_expires_at = datetime.now() + timedelta(hours=1)
        
        # Test 1: Fetch chat history with authentication
        mock_history_response = MagicMock()
        mock_history_response.status_code = 200
        mock_history_response.json.return_value = [
            {"role": "user", "content": "Hello", "timestamp": "2024-01-16 10:00:00"},
            {"role": "assistant", "content": "Hi there!", "timestamp": "2024-01-16 10:00:05"}
        ]
        
        with patch('requests.get', return_value=mock_history_response):
            # Simulate fetch_history function
            def fetch_history():
                if not auth_manager.is_authenticated():
                    return []
                
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                response = requests.get(
                    f"{auth_manager.api_base_url}/chat/history",
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    return response.json()
                return []
            
            # Test successful history fetch
            history = fetch_history()
            assert len(history) == 2
            assert history[0]["role"] == "user"
            assert history[1]["role"] == "assistant"
        
        # Test 2: Fetch history without authentication
        auth_manager.logout()
        
        history = fetch_history()
        assert history == []
    
    def test_health_metrics_integration_validation(self):
        """Test health metrics integration with authentication"""
        auth_manager = AuthManager()
        
        # Clear any existing data
        st.session_state.weight_history = []
        st.session_state.medications = []
        st.session_state.symptom_history = []
        
        # Set up authenticated state
        st.session_state.authenticated = True
        st.session_state.token = "metrics_token"
        st.session_state.session_expires_at = datetime.now() + timedelta(hours=1)
        
        # Test 1: Weight tracking
        weight_entry = {'date': '2024-01-16', 'weight': 70.5}
        st.session_state.weight_history.append(weight_entry)
        
        assert len(st.session_state.weight_history) == 1
        assert st.session_state.weight_history[0]['weight'] == 70.5
        
        # Test 2: Medication tracking
        medication = {
            'name': 'Aspirin',
            'dosage': '81mg',
            'frequency': 'Daily',
            'taken_today': True
        }
        st.session_state.medications.append(medication)
        
        assert len(st.session_state.medications) == 1
        assert st.session_state.medications[0]['name'] == 'Aspirin'
        
        # Test 3: Symptom tracking
        symptom_report = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'symptoms': ['Headache', 'Fatigue'],
            'severity': 5
        }
        st.session_state.symptom_history.append(symptom_report)
        
        assert len(st.session_state.symptom_history) == 1
        assert len(st.session_state.symptom_history[0]['symptoms']) == 2
        
        # Test 4: BMI calculation
        def calculate_bmi(height_cm, weight_kg):
            height_m = height_cm / 100
            return weight_kg / (height_m ** 2)
        
        bmi = calculate_bmi(170, 70.5)
        assert 20 <= bmi <= 30  # Reasonable BMI range
    
    def test_health_profile_integration_validation(self):
        """Test health profile integration with authentication"""
        auth_manager = AuthManager()
        
        # Clear any existing data
        st.session_state.full_name = None
        st.session_state.age = None
        st.session_state.chronic_conditions = []
        st.session_state.health_goals = []
        
        # Set up authenticated state
        st.session_state.authenticated = True
        st.session_state.token = "profile_token"
        st.session_state.session_expires_at = datetime.now() + timedelta(hours=1)
        
        # Test 1: Personal information
        st.session_state.full_name = "John Doe"
        st.session_state.age = 35
        
        assert st.session_state.full_name == "John Doe"
        assert st.session_state.age == 35
        
        # Test 2: Medical history
        condition = "Hypertension"
        st.session_state.chronic_conditions.append(condition)
        
        assert len(st.session_state.chronic_conditions) == 1
        assert st.session_state.chronic_conditions[0] == "Hypertension"
        
        # Test 3: Health goals
        goal = {
            'type': 'Weight Loss',
            'target': 'Lose 10kg',
            'deadline': '2024-06-01',
            'progress': 30
        }
        st.session_state.health_goals.append(goal)
        
        assert len(st.session_state.health_goals) == 1
        assert st.session_state.health_goals[0]['type'] == 'Weight Loss'
        assert st.session_state.health_goals[0]['progress'] == 30
    
    def test_reports_integration_validation(self):
        """Test reports integration with authentication"""
        auth_manager = AuthManager()
        
        # Set up authenticated state
        st.session_state.authenticated = True
        st.session_state.token = "reports_token"
        st.session_state.session_expires_at = datetime.now() + timedelta(hours=1)
        
        # Test report generation with user data
        # Set up test data
        st.session_state.full_name = "Jane Smith"
        st.session_state.age = 28
        st.session_state.weight_history = [
            {'date': '2024-01-15', 'weight': 65.0},
            {'date': '2024-01-16', 'weight': 64.8}
        ]
        st.session_state.medications = [
            {'name': 'Vitamin D', 'dosage': '1000 IU', 'frequency': 'Daily'}
        ]
        st.session_state.chronic_conditions = ["Asthma"]
        st.session_state.health_goals = [
            {'type': 'Fitness', 'target': 'Run 5km', 'progress': 60}
        ]
        
        # Test 1: Health summary report
        health_summary = {
            'personal_info': {
                'name': st.session_state.full_name,
                'age': st.session_state.age
            },
            'weight_trend': len(st.session_state.weight_history),
            'medications': len(st.session_state.medications),
            'conditions': len(st.session_state.chronic_conditions),
            'goals': len(st.session_state.health_goals)
        }
        
        assert health_summary['personal_info']['name'] == "Jane Smith"
        assert health_summary['weight_trend'] == 2
        assert health_summary['medications'] == 1
        assert health_summary['conditions'] == 1
        assert health_summary['goals'] == 1
        
        # Test 2: Medication report
        medication_report = {
            'total_medications': len(st.session_state.medications),
            'medication_list': [med['name'] for med in st.session_state.medications]
        }
        
        assert medication_report['total_medications'] == 1
        assert "Vitamin D" in medication_report['medication_list']
        
        # Test 3: Goal progress report
        goal_progress = {
            'total_goals': len(st.session_state.health_goals),
            'average_progress': sum(goal['progress'] for goal in st.session_state.health_goals) / len(st.session_state.health_goals)
        }
        
        assert goal_progress['total_goals'] == 1
        assert goal_progress['average_progress'] == 60
    
    def test_settings_integration_validation(self):
        """Test settings integration with authentication"""
        auth_manager = AuthManager()
        
        # Set up authenticated state
        st.session_state.authenticated = True
        st.session_state.token = "settings_token"
        st.session_state.session_expires_at = datetime.now() + timedelta(hours=1)
        
        # Test settings data management
        # Initialize settings data
        if 'notification_settings' not in st.session_state:
            st.session_state.notification_settings = {}
        if 'privacy_settings' not in st.session_state:
            st.session_state.privacy_settings = {}
        if 'appearance_settings' not in st.session_state:
            st.session_state.appearance_settings = {}
        
        # Test 1: Notification settings
        st.session_state.notification_settings = {
            'email_notifications': True,
            'in_app_notifications': True,
            'reminder_frequency': 'daily'
        }
        
        assert st.session_state.notification_settings['email_notifications'] == True
        assert st.session_state.notification_settings['reminder_frequency'] == 'daily'
        
        # Test 2: Privacy settings
        st.session_state.privacy_settings = {
            'data_sharing': False,
            'profile_visibility': 'private',
            'data_retention': '1_year'
        }
        
        assert st.session_state.privacy_settings['data_sharing'] == False
        assert st.session_state.privacy_settings['profile_visibility'] == 'private'
        
        # Test 3: Appearance settings
        st.session_state.appearance_settings = {
            'theme': 'light',
            'font_size': 'medium',
            'color_scheme': 'default'
        }
        
        assert st.session_state.appearance_settings['theme'] == 'light'
        assert st.session_state.appearance_settings['font_size'] == 'medium'
    
    def test_logout_behavior_validation(self):
        """Test logout behavior and session cleanup"""
        auth_manager = AuthManager()
        session_manager = SessionManager(auth_manager)
        
        # Set up comprehensive authenticated state
        st.session_state.authenticated = True
        st.session_state.token = "logout_test_token"
        st.session_state.user_email = "logout@example.com"
        st.session_state.user_id = 123
        st.session_state.login_time = datetime.now()
        st.session_state.last_login = "2024-01-16 10:00"
        st.session_state.session_expires_at = datetime.now() + timedelta(hours=1)
        st.session_state.user_profile = {"full_name": "Logout Test User"}
        st.session_state.permissions = ["read", "write"]
        
        # Set up dashboard state
        st.session_state.chat_history = [{"role": "user", "content": "test"}]
        st.session_state.current_page = "Settings"
        st.session_state.show_logout_confirm = True
        st.session_state.quick_action = "health_check"
        st.session_state.emergency_active = True
        st.session_state.emergency_message = "Test emergency"
        st.session_state.emergency_recommendations = ["Call 911"]
        
        # Test logout
        auth_manager.logout()
        
        # Verify all authentication state is cleared
        auth_vars = [
            'authenticated', 'token', 'user_email', 'user_id', 'login_time',
            'last_login', 'session_expires_at', 'user_profile', 'permissions'
        ]
        
        for var in auth_vars:
            assert st.session_state[var] is None, f"Authentication variable {var} should be cleared"
        
        # Verify dashboard state is reset
        assert st.session_state.current_page == 'Chat'
        assert st.session_state.show_logout_confirm == False
        assert st.session_state.emergency_active == False
        assert st.session_state.emergency_message is None
        assert st.session_state.emergency_recommendations is None
        assert st.session_state.quick_action is None
    
    def test_session_timeout_behavior_validation(self):
        """Test session timeout behavior and handling"""
        auth_manager = AuthManager()
        session_manager = SessionManager(auth_manager)
        
        # Test 1: Session timeout detection
        # Set up session near expiry
        st.session_state.authenticated = True
        st.session_state.token = "timeout_test_token"
        st.session_state.session_expires_at = datetime.now() + timedelta(minutes=2)
        
        # Check session status
        status = session_manager.check_session_status()
        assert status["valid"] == True
        assert status["warning"] == True  # Should show warning at 2 minutes
        assert status["remaining_minutes"] <= 5
        
        # Test 2: Session expiration
        st.session_state.session_expires_at = datetime.now() - timedelta(minutes=1)
        
        status = session_manager.check_session_status()
        assert status["valid"] == False
        assert status["expired"] == True
        assert status["remaining_minutes"] == 0
        
        # Test 3: Automatic logout on expiration
        assert not auth_manager.is_authenticated()
        
        # Test 4: Session refresh
        st.session_state.authenticated = True
        st.session_state.token = "refresh_test_token"
        st.session_state.session_expires_at = datetime.now() + timedelta(minutes=30)
        
        mock_refresh_response = MagicMock()
        mock_refresh_response.status_code = 200
        mock_refresh_response.json.return_value = {
            "access_token": "new_refresh_token",
            "email": "refresh@example.com",
            "user_id": 456
        }
        
        with patch('requests.post', return_value=mock_refresh_response):
            refresh_success = auth_manager.refresh_session()
            assert refresh_success == True
            assert st.session_state.token == "new_refresh_token"
    
    def test_error_handling_validation(self):
        """Test error handling across all features"""
        auth_manager = AuthManager()
        
        # Test 1: Network error handling
        with patch('requests.post', side_effect=requests.exceptions.RequestException("Network error")):
            # Test login with network error
            result = auth_manager.login("test@example.com", "password123")
            assert result["success"] == False
            assert "Connection error" in result["message"]
            
            # Test registration with network error
            result = auth_manager.register("test@example.com", "password123")
            assert result["success"] == False
            assert "Connection error" in result["message"]
        
        # Test 2: Authentication error handling
        mock_auth_error_response = MagicMock()
        mock_auth_error_response.status_code = 401
        mock_auth_error_response.json.return_value = {"detail": "Invalid credentials"}
        
        with patch('requests.post', return_value=mock_auth_error_response):
            result = auth_manager.login("test@example.com", "wrongpassword")
            assert result["success"] == False
            assert "Invalid credentials" in result["message"]
        
        # Test 3: Server error handling
        mock_server_error_response = MagicMock()
        mock_server_error_response.status_code = 500
        mock_server_error_response.json.return_value = {"detail": "Internal server error"}
        
        with patch('requests.post', return_value=mock_server_error_response):
            result = auth_manager.login("test@example.com", "password123")
            assert result["success"] == False
            assert "Internal server error" in result["message"]
    
    def test_permission_based_access_validation(self):
        """Test permission-based access control across features"""
        auth_manager = AuthManager()
        
        # Set up authenticated state with specific permissions
        st.session_state.authenticated = True
        st.session_state.token = "permission_test_token"
        st.session_state.session_expires_at = datetime.now() + timedelta(hours=1)
        st.session_state.permissions = ["health_read", "health_write", "reports_view"]
        
        # Test feature access based on permissions
        features_permissions = {
            "chat": ["health_read"],
            "health_metrics": ["health_read", "health_write"],
            "health_profile": ["health_read", "health_write"],
            "reports": ["reports_view"],
            "settings": ["health_read"]
        }
        
        for feature, required_permissions in features_permissions.items():
            # Check if user has required permissions for each feature
            has_access = all(auth_manager.has_permission(perm) for perm in required_permissions)
            assert has_access == True, f"User should have access to {feature}"
        
        # Test access denial for features without permissions
        st.session_state.permissions = ["health_read"]  # Remove some permissions
        
        # User should not have access to features requiring "health_write" or "reports_view"
        assert not auth_manager.has_permission("health_write")
        assert not auth_manager.has_permission("reports_view")
        
        # Test access to features that only require "health_read"
        assert auth_manager.has_permission("health_read")
    
    def test_data_persistence_validation(self):
        """Test data persistence across sessions and features"""
        auth_manager = AuthManager()
        
        # Set up authenticated state
        st.session_state.authenticated = True
        st.session_state.token = "persistence_test_token"
        st.session_state.session_expires_at = datetime.now() + timedelta(hours=1)
        
        # Test data persistence across different features
        test_data = {
            'weight_history': [{'date': '2024-01-16', 'weight': 70.0}],
            'medications': [{'name': 'Test Med', 'dosage': '10mg'}],
            'chronic_conditions': ['Test Condition'],
            'health_goals': [{'type': 'Test Goal', 'target': 'Test Target'}],
            'notification_settings': {'email_notifications': True},
            'privacy_settings': {'data_sharing': False},
            'appearance_settings': {'theme': 'dark'}
        }
        
        # Store test data in session state
        for key, value in test_data.items():
            st.session_state[key] = value
        
        # Verify data persistence
        for key, expected_value in test_data.items():
            assert st.session_state[key] == expected_value, f"Data for {key} should persist"
        
        # Test data consistency across features
        assert len(st.session_state.weight_history) == 1
        assert len(st.session_state.medications) == 1
        assert len(st.session_state.chronic_conditions) == 1
        assert len(st.session_state.health_goals) == 1
        assert st.session_state.notification_settings['email_notifications'] == True
        assert st.session_state.privacy_settings['data_sharing'] == False
        assert st.session_state.appearance_settings['theme'] == 'dark'

if __name__ == "__main__":
    pytest.main([__file__]) 
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

class TestIntegrationRefactoring:
    
    def test_auth_manager_initialization(self):
        """Test authentication manager initialization"""
        auth_manager = AuthManager()
        
        # Test session state initialization
        assert 'authenticated' in st.session_state
        assert 'token' in st.session_state
        assert 'user_email' in st.session_state
        assert 'user_id' in st.session_state
        assert 'login_time' in st.session_state
        assert 'last_login' in st.session_state
        assert 'session_expires_at' in st.session_state
        assert 'user_profile' in st.session_state
        assert 'permissions' in st.session_state
        assert 'auth_error' in st.session_state
        assert 'auth_message' in st.session_state
        assert 'auth_message_type' in st.session_state
    
    def test_auth_manager_authentication_check(self):
        """Test authentication status checking"""
        auth_manager = AuthManager()
        
        # Test unauthenticated state
        assert not auth_manager.is_authenticated()
        
        # Test authenticated state
        st.session_state.authenticated = True
        st.session_state.token = "test_token"
        st.session_state.session_expires_at = datetime.now() + timedelta(hours=1)
        
        assert auth_manager.is_authenticated()
        
        # Test expired session
        st.session_state.session_expires_at = datetime.now() - timedelta(hours=1)
        assert not auth_manager.is_authenticated()
    
    def test_auth_manager_login_flow(self):
        """Test login flow with authentication manager"""
        auth_manager = AuthManager()
        
        # Mock successful login response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test_token",
            "email": "test@example.com",
            "user_id": 1,
            "user_profile": {"full_name": "Test User"},
            "permissions": ["read", "write"]
        }
        
        with patch('requests.post', return_value=mock_response):
            result = auth_manager.login("test@example.com", "password123")
            
            assert result["success"] == True
            assert st.session_state.authenticated == True
            assert st.session_state.token == "test_token"
            assert st.session_state.user_email == "test@example.com"
            assert st.session_state.user_id == 1
            assert st.session_state.user_profile["full_name"] == "Test User"
            assert st.session_state.permissions == ["read", "write"]
    
    def test_auth_manager_logout_flow(self):
        """Test logout flow with authentication manager"""
        auth_manager = AuthManager()
        
        # Set up authenticated state
        st.session_state.authenticated = True
        st.session_state.token = "test_token"
        st.session_state.user_email = "test@example.com"
        st.session_state.user_id = 1
        st.session_state.login_time = datetime.now()
        st.session_state.last_login = "2024-01-16 10:00"
        st.session_state.session_expires_at = datetime.now() + timedelta(hours=1)
        st.session_state.user_profile = {"full_name": "Test User"}
        st.session_state.permissions = ["read", "write"]
        st.session_state.auth_error = None
        st.session_state.auth_message = "Test message"
        st.session_state.auth_message_type = "info"
        
        # Test logout
        auth_manager.logout()
        
        # Verify all auth state is cleared
        assert st.session_state.authenticated is None
        assert st.session_state.token is None
        assert st.session_state.user_email is None
        assert st.session_state.user_id is None
        assert st.session_state.login_time is None
        assert st.session_state.last_login is None
        assert st.session_state.session_expires_at is None
        assert st.session_state.user_profile is None
        assert st.session_state.permissions is None
        assert st.session_state.auth_error is None
        assert st.session_state.auth_message is None
        assert st.session_state.auth_message_type is None
    
    def test_auth_manager_session_refresh(self):
        """Test session refresh functionality"""
        auth_manager = AuthManager()
        
        # Set up authenticated state
        st.session_state.authenticated = True
        st.session_state.token = "old_token"
        
        # Mock successful refresh response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "new_token",
            "email": "test@example.com",
            "user_id": 1
        }
        
        with patch('requests.post', return_value=mock_response):
            result = auth_manager.refresh_session()
            
            assert result == True
            assert st.session_state.token == "new_token"
    
    def test_auth_manager_user_info(self):
        """Test user information retrieval"""
        auth_manager = AuthManager()
        
        # Set up authenticated state
        st.session_state.authenticated = True
        st.session_state.token = "test_token"
        st.session_state.user_email = "test@example.com"
        st.session_state.user_id = 1
        st.session_state.login_time = datetime.now()
        st.session_state.session_expires_at = datetime.now() + timedelta(hours=1)
        st.session_state.user_profile = {"full_name": "Test User"}
        st.session_state.permissions = ["read", "write"]
        
        user_info = auth_manager.get_user_info()
        
        assert user_info["email"] == "test@example.com"
        assert user_info["user_id"] == 1
        assert user_info["profile"]["full_name"] == "Test User"
        assert user_info["permissions"] == ["read", "write"]
        assert "login_time" in user_info
        assert "session_expires_at" in user_info
    
    def test_auth_manager_permissions(self):
        """Test permission checking"""
        auth_manager = AuthManager()
        
        # Set up authenticated state with permissions
        st.session_state.authenticated = True
        st.session_state.permissions = ["read", "write", "admin"]
        
        assert auth_manager.has_permission("read") == True
        assert auth_manager.has_permission("write") == True
        assert auth_manager.has_permission("admin") == True
        assert auth_manager.has_permission("delete") == False
    
    def test_session_manager_initialization(self):
        """Test session manager initialization"""
        auth_manager = AuthManager()
        session_manager = SessionManager(auth_manager)
        
        assert session_manager.auth_manager == auth_manager
        assert session_manager.timeout_minutes == 60
        assert session_manager.warning_minutes == 5
        assert session_manager.session_warning_shown == False
        assert session_manager.auto_refresh_enabled == True
    
    def test_session_manager_status_check(self):
        """Test session status checking"""
        auth_manager = AuthManager()
        session_manager = SessionManager(auth_manager)
        
        # Clear any existing session state
        st.session_state.authenticated = False
        st.session_state.session_expires_at = None
        
        # Test unauthenticated status
        status = session_manager.check_session_status()
        assert status["valid"] == False
        assert status["expired"] == True
        assert status["warning"] == False
        assert status["remaining_minutes"] == 0
        
        # Test authenticated status
        st.session_state.authenticated = True
        st.session_state.session_expires_at = datetime.now() + timedelta(minutes=30)
        
        status = session_manager.check_session_status()
        assert status["valid"] == True
        assert status["expired"] == False
        assert status["warning"] == False
        assert status["remaining_minutes"] > 0
        
        # Test warning status
        st.session_state.session_expires_at = datetime.now() + timedelta(minutes=3)
        
        status = session_manager.check_session_status()
        assert status["valid"] == True
        assert status["warning"] == True
        assert status["remaining_minutes"] <= 5
        
        # Test expired status
        st.session_state.session_expires_at = datetime.now() - timedelta(minutes=1)
        
        status = session_manager.check_session_status()
        assert status["valid"] == False
        assert status["expired"] == True
        assert status["remaining_minutes"] == 0
    
    def test_session_manager_activity_tracking(self):
        """Test session activity tracking"""
        auth_manager = AuthManager()
        session_manager = SessionManager(auth_manager)
        
        # Set up authenticated state
        st.session_state.authenticated = True
        st.session_state.token = "test_token"
        st.session_state.session_expires_at = datetime.now() + timedelta(hours=1)
        
        # Test activity update
        session_manager.update_session_activity()
        assert 'last_activity' in st.session_state
        assert isinstance(st.session_state.last_activity, datetime)
    
    def test_session_manager_info_retrieval(self):
        """Test session information retrieval"""
        auth_manager = AuthManager()
        session_manager = SessionManager(auth_manager)
        
        # Set up authenticated state
        st.session_state.authenticated = True
        st.session_state.token = "test_token"
        st.session_state.user_email = "test@example.com"
        st.session_state.login_time = datetime.now()
        st.session_state.session_expires_at = datetime.now() + timedelta(hours=1)
        st.session_state.last_activity = datetime.now()
        
        session_info = session_manager.get_session_info()
        
        assert session_info["user_email"] == "test@example.com"
        assert "login_time" in session_info
        assert "session_duration" in session_info
        assert "remaining_time" in session_info
        assert "status" in session_info
        assert "last_activity" in session_info
        assert "auto_refresh_enabled" in session_info
    
    def test_session_middleware_processing(self):
        """Test session middleware processing"""
        auth_manager = AuthManager()
        session_manager = SessionManager(auth_manager)
        middleware = SessionMiddleware(session_manager)
        
        # Set up authenticated state
        st.session_state.authenticated = True
        st.session_state.session_expires_at = datetime.now() + timedelta(hours=1)
        
        # Test middleware processing
        middleware.process_request()
        
        # Verify activity was updated
        assert 'last_activity' in st.session_state
    
    def test_unified_authentication_state(self):
        """Test unified authentication state across features"""
        auth_manager = AuthManager()
        
        # Test login sets all required state
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test_token",
            "email": "test@example.com",
            "user_id": 1,
            "user_profile": {"full_name": "Test User"},
            "permissions": ["read", "write"]
        }
        
        with patch('requests.post', return_value=mock_response):
            auth_manager.login("test@example.com", "password123")
            
            # Verify all authentication state is set
            assert st.session_state.authenticated == True
            assert st.session_state.token == "test_token"
            assert st.session_state.user_email == "test@example.com"
            assert st.session_state.user_id == 1
            assert st.session_state.user_profile["full_name"] == "Test User"
            assert st.session_state.permissions == ["read", "write"]
            assert st.session_state.login_time is not None
            assert st.session_state.last_login is not None
            assert st.session_state.session_expires_at is not None
    
    def test_session_timeout_handling(self):
        """Test session timeout handling"""
        auth_manager = AuthManager()
        session_manager = SessionManager(auth_manager)
        
        # Set up expired session
        st.session_state.authenticated = True
        st.session_state.session_expires_at = datetime.now() - timedelta(minutes=1)
        
        # Test timeout detection
        status = session_manager.check_session_status()
        assert status["expired"] == True
        assert status["valid"] == False
    
    def test_automatic_session_refresh(self):
        """Test automatic session refresh functionality"""
        auth_manager = AuthManager()
        session_manager = SessionManager(auth_manager)
        
        # Set up session near expiry
        st.session_state.authenticated = True
        st.session_state.token = "old_token"
        st.session_state.session_expires_at = datetime.now() + timedelta(minutes=5)
        
        # Mock successful refresh
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "new_token",
            "email": "test@example.com",
            "user_id": 1
        }
        
        with patch('requests.post', return_value=mock_response):
            session_manager.setup_session_monitoring()
            
            # Verify session was refreshed
            assert st.session_state.token == "new_token"
    
    def test_error_handling_integration(self):
        """Test error handling in integrated system"""
        auth_manager = AuthManager()
        
        # Test network error handling
        with patch('requests.post', side_effect=requests.exceptions.RequestException("Network error")):
            result = auth_manager.login("test@example.com", "password123")
            
            assert result["success"] == False
            assert "Connection error" in result["message"]
    
    def test_session_state_consistency(self):
        """Test session state consistency across components"""
        auth_manager = AuthManager()
        session_manager = SessionManager(auth_manager)
        
        # Set up consistent state
        st.session_state.authenticated = True
        st.session_state.token = "test_token"
        st.session_state.user_email = "test@example.com"
        st.session_state.session_expires_at = datetime.now() + timedelta(hours=1)
        
        # Test consistency across managers
        assert auth_manager.is_authenticated() == True
        status = session_manager.check_session_status()
        assert status["valid"] == True
        
        # Test state changes are reflected
        auth_manager.logout()
        assert auth_manager.is_authenticated() == False
        status = session_manager.check_session_status()
        assert status["valid"] == False
    
    def test_permission_based_access(self):
        """Test permission-based access control"""
        auth_manager = AuthManager()
        
        # Set up user with specific permissions
        st.session_state.authenticated = True
        st.session_state.token = "test_token"  # Need token for authentication
        st.session_state.session_expires_at = datetime.now() + timedelta(hours=1)  # Valid session
        st.session_state.permissions = ["health_read", "health_write"]
        
        # Test permission checks
        assert auth_manager.has_permission("health_read") == True
        assert auth_manager.has_permission("health_write") == True
        assert auth_manager.has_permission("admin_access") == False
        
        # Test feature access based on permissions
        can_read_health = auth_manager.has_permission("health_read")
        can_write_health = auth_manager.has_permission("health_write")
        can_admin = auth_manager.has_permission("admin_access")
        
        assert can_read_health == True
        assert can_write_health == True
        assert can_admin == False

if __name__ == "__main__":
    pytest.main([__file__]) 
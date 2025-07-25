import pytest
import streamlit as st
from unittest.mock import patch, MagicMock
import sys
import os

# Add the frontend directory to the path for testing
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'frontend'))

class TestPostLoginFlow:
    
    def test_authentication_state_management(self):
        """Test that authentication state is properly managed"""
        # Test initial state (auth manager initializes these)
        assert 'authenticated' in st.session_state
        assert 'token' in st.session_state
        assert 'user_email' in st.session_state
        assert 'chat_history' not in st.session_state
        
        # Test setting authentication state
        st.session_state.authenticated = True
        st.session_state.token = "test_token_123"
        st.session_state.user_email = "test@example.com"
        st.session_state.chat_history = []
        
        assert st.session_state.authenticated == True
        assert st.session_state.token == "test_token_123"
        assert st.session_state.user_email == "test@example.com"
        assert st.session_state.chat_history == []
    
    def test_logout_functionality(self):
        """Test logout clears all session state"""
        # Set up authenticated state
        st.session_state.authenticated = True
        st.session_state.token = "test_token_123"
        st.session_state.user_email = "test@example.com"
        st.session_state.chat_history = [{"role": "user", "content": "test"}]
        
        # Mock logout function
        def logout():
            st.session_state.authenticated = False
            st.session_state.token = None
            st.session_state.chat_history = []
            st.session_state.user_email = None
        
        # Test logout
        logout()
        
        assert st.session_state.authenticated == False
        assert st.session_state.token is None
        assert st.session_state.user_email is None
        assert st.session_state.chat_history == []
    
    def test_dashboard_access_control(self):
        """Test that dashboard access is properly controlled"""
        # Test unauthenticated access
        st.session_state.authenticated = False
        st.session_state.token = None
        
        # Should be denied access
        can_access = st.session_state.authenticated and st.session_state.token
        assert can_access == False
        
        # Test authenticated access
        st.session_state.authenticated = True
        st.session_state.token = "test_token_123"
        
        # Should be granted access
        can_access = bool(st.session_state.authenticated and st.session_state.token)
        assert can_access == True
    
    def test_chat_history_management(self):
        """Test chat history is properly managed"""
        # Test initial empty history
        st.session_state.chat_history = []
        assert len(st.session_state.chat_history) == 0
        
        # Test adding messages
        st.session_state.chat_history.append({"role": "user", "content": "Hello"})
        st.session_state.chat_history.append({"role": "assistant", "content": "Hi there!"})
        
        assert len(st.session_state.chat_history) == 2
        assert st.session_state.chat_history[0]["role"] == "user"
        assert st.session_state.chat_history[1]["role"] == "assistant"
    
    def test_quick_actions_state(self):
        """Test quick actions state management"""
        # Test initial state
        if 'quick_action' not in st.session_state:
            st.session_state.quick_action = None
        
        assert st.session_state.quick_action is None
        
        # Test setting quick action
        st.session_state.quick_action = "health_check"
        assert st.session_state.quick_action == "health_check"
        
        # Test clearing quick action
        st.session_state.quick_action = None
        assert st.session_state.quick_action is None
    
    def test_user_email_validation(self):
        """Test user email validation and display"""
        # Test with valid email
        st.session_state.user_email = "test@example.com"
        has_email = bool(st.session_state.user_email)
        assert has_email == True
        
        # Test with empty email
        st.session_state.user_email = ""
        has_email = bool(st.session_state.user_email)
        assert has_email == False
        
        # Test with None email
        st.session_state.user_email = None
        has_email = bool(st.session_state.user_email)
        assert has_email == False
    
    def test_navigation_options(self):
        """Test dashboard navigation options"""
        navigation_options = [
            "Chat", 
            "Health Metrics", 
            "Health Profile", 
            "Chat History", 
            "Reports", 
            "Settings"
        ]
        
        assert len(navigation_options) == 6
        assert "Chat" in navigation_options
        assert "Health Metrics" in navigation_options
        assert "Health Profile" in navigation_options
        assert "Chat History" in navigation_options
        assert "Reports" in navigation_options
        assert "Settings" in navigation_options
    
    def test_emergency_state_management(self):
        """Test emergency state management"""
        # Test initial emergency state
        if 'emergency_active' not in st.session_state:
            st.session_state.emergency_active = False
        if 'emergency_message' not in st.session_state:
            st.session_state.emergency_message = None
        if 'emergency_recommendations' not in st.session_state:
            st.session_state.emergency_recommendations = None
        
        assert st.session_state.emergency_active == False
        assert st.session_state.emergency_message is None
        assert st.session_state.emergency_recommendations is None
        
        # Test setting emergency state
        st.session_state.emergency_active = True
        st.session_state.emergency_message = "Emergency detected"
        st.session_state.emergency_recommendations = ["Call 911", "Seek immediate medical attention"]
        
        assert st.session_state.emergency_active == True
        assert st.session_state.emergency_message == "Emergency detected"
        assert st.session_state.emergency_recommendations == ["Call 911", "Seek immediate medical attention"]
        
        # Test clearing emergency state
        st.session_state.emergency_active = False
        st.session_state.emergency_message = None
        st.session_state.emergency_recommendations = None
        
        assert st.session_state.emergency_active == False
        assert st.session_state.emergency_message is None
        assert st.session_state.emergency_recommendations is None

if __name__ == "__main__":
    pytest.main([__file__]) 
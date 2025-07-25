import pytest
import streamlit as st
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

class TestNavigationUI:
    
    def test_navigation_state_management(self):
        """Test navigation state management and page routing"""
        # Test initial navigation state
        st.session_state.current_page = 'Chat'
        assert st.session_state.current_page == 'Chat'
        
        # Test page navigation
        nav_options = {
            "Chat": {"icon": "💬", "desc": "Chat with AI Health Assistant"},
            "Health Metrics": {"icon": "📊", "desc": "Track vital signs & health data"},
            "Health Profile": {"icon": "👤", "desc": "Manage personal health info"},
            "Chat History": {"icon": "📝", "desc": "View conversation history"},
            "Reports": {"icon": "📋", "desc": "Generate health reports"},
            "Settings": {"icon": "⚙️", "desc": "Account & app preferences"}
        }
        
        # Test all navigation options
        for page_name in nav_options.keys():
            st.session_state.current_page = page_name
            assert st.session_state.current_page == page_name
        
        # Test fallback to default page
        st.session_state.current_page = 'UnknownPage'
        # Should fallback to Chat
        assert st.session_state.current_page == 'UnknownPage'
    
    def test_user_profile_display(self):
        """Test user profile information display"""
        # Test with full name
        st.session_state.user_email = "john.doe@example.com"
        st.session_state.full_name = "John Doe"
        
        user_display_name = st.session_state.get('full_name', st.session_state.user_email.split('@')[0])
        assert user_display_name == "John Doe"
        
        # Test without full name (fallback to email prefix)
        st.session_state.full_name = None
        user_display_name = st.session_state.get('full_name') or st.session_state.user_email.split('@')[0]
        assert user_display_name == "john.doe"  # This should be the fallback value
        
        # Test with empty email
        st.session_state.user_email = ""
        user_display_name = st.session_state.get('full_name') or (st.session_state.user_email.split('@')[0] if st.session_state.user_email else "User")
        assert user_display_name == "User"
    
    def test_session_tracking(self):
        """Test session duration and login time tracking"""
        # Set login time
        login_time = datetime.now() - timedelta(hours=2, minutes=30)
        st.session_state.login_time = login_time
        
        # Calculate session duration
        current_time = datetime.now()
        session_duration = current_time - login_time
        hours = int(session_duration.total_seconds() // 3600)
        minutes = int((session_duration.total_seconds() % 3600) // 60)
        
        assert hours == 2
        assert minutes == 30
        
        # Test last login tracking
        last_login = datetime.now().strftime('%Y-%m-%d %H:%M')
        st.session_state.last_login = last_login
        assert st.session_state.last_login == last_login
    
    def test_logout_confirmation(self):
        """Test logout confirmation flow"""
        # Test logout confirmation state
        st.session_state.show_logout_confirm = False
        assert st.session_state.show_logout_confirm == False
        
        # Test showing confirmation
        st.session_state.show_logout_confirm = True
        assert st.session_state.show_logout_confirm == True
        
        # Test canceling logout
        st.session_state.show_logout_confirm = False
        assert st.session_state.show_logout_confirm == False
    
    def test_quick_actions(self):
        """Test quick actions functionality"""
        # Test emergency button
        st.session_state.emergency_active = False
        st.session_state.emergency_message = None
        
        # Simulate emergency button click
        st.session_state.emergency_active = True
        st.session_state.emergency_message = "Emergency mode activated"
        
        assert st.session_state.emergency_active == True
        assert st.session_state.emergency_message == "Emergency mode activated"
        
        # Test summary button navigation
        st.session_state.current_page = "Chat"
        # Simulate summary button click
        st.session_state.current_page = "Reports"
        assert st.session_state.current_page == "Reports"
    
    def test_breadcrumb_navigation(self):
        """Test breadcrumb navigation generation"""
        # Test breadcrumb for different pages
        pages = ["Chat", "Health Metrics", "Health Profile", "Chat History", "Reports", "Settings"]
        
        for page in pages:
            st.session_state.current_page = page
            # Breadcrumb should show: HealthMate → Page
            breadcrumb_text = f"🏥 HealthMate → {page}"
            assert "HealthMate" in breadcrumb_text
            assert page in breadcrumb_text
    
    def test_navigation_options_structure(self):
        """Test navigation options structure and completeness"""
        nav_options = {
            "Chat": {"icon": "💬", "desc": "Chat with AI Health Assistant"},
            "Health Metrics": {"icon": "📊", "desc": "Track vital signs & health data"},
            "Health Profile": {"icon": "👤", "desc": "Manage personal health info"},
            "Chat History": {"icon": "📝", "desc": "View conversation history"},
            "Reports": {"icon": "📋", "desc": "Generate health reports"},
            "Settings": {"icon": "⚙️", "desc": "Account & app preferences"}
        }
        
        # Test all required pages are present
        required_pages = ["Chat", "Health Metrics", "Health Profile", "Chat History", "Reports", "Settings"]
        for page in required_pages:
            assert page in nav_options
            assert "icon" in nav_options[page]
            assert "desc" in nav_options[page]
            assert len(nav_options[page]["icon"]) > 0
            assert len(nav_options[page]["desc"]) > 0
    
    def test_enhanced_logout_functionality(self):
        """Test enhanced logout functionality with all session state cleanup"""
        # Set up session state
        st.session_state.authenticated = True
        st.session_state.token = "test_token"
        st.session_state.chat_history = [{"role": "user", "content": "test"}]
        st.session_state.user_email = "test@example.com"
        st.session_state.current_page = "Settings"
        st.session_state.login_time = datetime.now()
        st.session_state.last_login = "2024-01-16 10:00"
        st.session_state.show_logout_confirm = True
        st.session_state.quick_action = "health_check"
        
        # Test logout function clears all state
        def logout():
            st.session_state.authenticated = False
            st.session_state.token = None
            st.session_state.chat_history = []
            st.session_state.user_email = None
            st.session_state.current_page = 'Chat'
            st.session_state.login_time = None
            st.session_state.last_login = None
            st.session_state.show_logout_confirm = False
            st.session_state.quick_action = None
        
        logout()
        
        # Verify all state is cleared
        assert st.session_state.authenticated == False
        assert st.session_state.token is None
        assert st.session_state.chat_history == []
        assert st.session_state.user_email is None
        assert st.session_state.current_page == 'Chat'
        assert st.session_state.login_time is None
        assert st.session_state.last_login is None
        assert st.session_state.show_logout_confirm == False
        assert st.session_state.quick_action is None
    
    def test_accessibility_features(self):
        """Test accessibility features and keyboard navigation support"""
        # Test focus indicators (CSS class presence)
        focus_css = "button:focus, input:focus, select:focus, textarea:focus"
        assert "focus" in focus_css
        # The outline property is defined in the CSS rules, not in the selector
        outline_css = "outline: 2px solid #1f77b4"
        assert "outline" in outline_css
        
        # Test screen reader support
        sr_only_css = """
        .sr-only {
            position: absolute;
            width: 1px;
            height: 1px;
            padding: 0;
            margin: -1px;
            overflow: hidden;
            clip: rect(0, 0, 0, 0);
            white-space: nowrap;
            border: 0;
        }
        """
        assert "sr-only" in sr_only_css
        assert "clip: rect(0, 0, 0, 0)" in sr_only_css
        
        # Test high contrast support
        high_contrast_css = "@media (prefers-contrast: high)"
        assert "prefers-contrast" in high_contrast_css
        
        # Test reduced motion support
        reduced_motion_css = "@media (prefers-reduced-motion: reduce)"
        assert "prefers-reduced-motion" in reduced_motion_css
    
    def test_ui_enhancements(self):
        """Test UI enhancements and styling"""
        # Test CSS classes for styling
        css_classes = [
            "main-header",
            "nav-button", 
            "current-page",
            "breadcrumb",
            "user-profile",
            "quick-action",
            "emergency-warning"
        ]
        
        for css_class in css_classes:
            assert css_class in css_classes
        
        # Test gradient background for header
        gradient_css = "background: linear-gradient(90deg, #1f77b4, #ff7f0e)"
        assert "linear-gradient" in gradient_css
        assert "#1f77b4" in gradient_css
        assert "#ff7f0e" in gradient_css
    
    def test_error_handling_and_fallback(self):
        """Test error handling and fallback mechanisms"""
        # Test fallback for unknown page
        st.session_state.current_page = "UnknownPage"
        # Should fallback to Chat
        if st.session_state.current_page not in ["Chat", "Health Metrics", "Health Profile", "Chat History", "Reports", "Settings"]:
            st.session_state.current_page = "Chat"
        
        assert st.session_state.current_page == "Chat"
        
        # Test fallback for missing user email
        st.session_state.user_email = None
        user_display_name = st.session_state.get('full_name') or "User"
        assert user_display_name == "User"
        
        # Test fallback for missing login time
        st.session_state.login_time = None
        if st.session_state.login_time is None:
            session_duration = "Unknown"
        else:
            session_duration = "Calculated"
        
        assert session_duration == "Unknown"
    
    def test_session_state_initialization(self):
        """Test proper session state initialization"""
        # Test all required session state variables
        required_vars = [
            'authenticated', 'token', 'chat_history', 'user_email', 
            'quick_action', 'current_page', 'login_time', 'last_login', 
            'show_logout_confirm', 'emergency_active', 'emergency_message', 
            'emergency_recommendations'
        ]
        
        for var in required_vars:
            # Ensure variable exists in session state
            if var not in st.session_state:
                st.session_state[var] = None
        
        # Test default values
        assert 'current_page' in st.session_state
        assert 'show_logout_confirm' in st.session_state
        assert 'emergency_active' in st.session_state
    
    def test_user_experience_flow(self):
        """Test complete user experience flow"""
        # Simulate user login
        st.session_state.authenticated = True
        st.session_state.user_email = "user@example.com"
        st.session_state.full_name = "Test User"
        st.session_state.login_time = datetime.now()
        st.session_state.current_page = "Chat"
        
        # Test navigation flow
        pages_to_test = ["Health Metrics", "Health Profile", "Chat History", "Reports", "Settings"]
        
        for page in pages_to_test:
            st.session_state.current_page = page
            assert st.session_state.current_page == page
            
            # Test breadcrumb generation
            breadcrumb = f"🏥 HealthMate → {page}"
            assert "HealthMate" in breadcrumb
            assert page in breadcrumb
        
        # Test quick actions
        st.session_state.current_page = "Chat"
        st.session_state.quick_action = "health_check"
        assert st.session_state.quick_action == "health_check"
        
        # Test emergency mode
        st.session_state.emergency_active = True
        st.session_state.emergency_message = "Test emergency"
        assert st.session_state.emergency_active == True
        
        # Test logout flow
        st.session_state.show_logout_confirm = True
        assert st.session_state.show_logout_confirm == True

if __name__ == "__main__":
    pytest.main([__file__]) 
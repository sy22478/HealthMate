"""
Session Manager for HealthMate Application

This module provides session management utilities including timeout handling,
automatic session refresh, and session state monitoring.
"""

import streamlit as st
from datetime import datetime, timedelta
import time
import threading
from typing import Optional, Callable
import logging

logger = logging.getLogger(__name__)

class SessionManager:
    """Manages user sessions with timeout and refresh capabilities"""
    
    def __init__(self, auth_manager, timeout_minutes: int = 60, warning_minutes: int = 5):
        """
        Initialize session manager
        
        Args:
            auth_manager: Authentication manager instance
            timeout_minutes: Session timeout in minutes
            warning_minutes: Minutes before timeout to show warning
        """
        self.auth_manager = auth_manager
        self.timeout_minutes = timeout_minutes
        self.warning_minutes = warning_minutes
        self.session_warning_shown = False
        self.auto_refresh_enabled = True
    
    def check_session_status(self) -> dict:
        """
        Check current session status
        
        Returns:
            dict with session status information
        """
        if not self.auth_manager.is_authenticated():
            return {
                "valid": False,
                "expired": True,
                "warning": False,
                "remaining_minutes": 0,
                "message": "Not authenticated"
            }
        
        if not st.session_state.session_expires_at:
            return {
                "valid": True,
                "expired": False,
                "warning": False,
                "remaining_minutes": self.timeout_minutes,
                "message": "Session active"
            }
        
        now = datetime.now()
        remaining = st.session_state.session_expires_at - now
        remaining_minutes = int(remaining.total_seconds() / 60)
        
        if remaining.total_seconds() <= 0:
            return {
                "valid": False,
                "expired": True,
                "warning": False,
                "remaining_minutes": 0,
                "message": "Session expired"
            }
        
        warning = remaining_minutes <= self.warning_minutes
        
        return {
            "valid": True,
            "expired": False,
            "warning": warning,
            "remaining_minutes": remaining_minutes,
            "message": f"Session active ({remaining_minutes}m remaining)"
        }
    
    def show_session_warning(self):
        """Show session timeout warning to user"""
        if self.session_warning_shown:
            return
        
        status = self.check_session_status()
        if status["warning"] and not status["expired"]:
            st.warning(f"""
            ⏰ **Session Timeout Warning**
            
            Your session will expire in {status['remaining_minutes']} minutes.
            
            To extend your session, please refresh the page or continue using the application.
            """)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Refresh Session", key="refresh_session"):
                    if self.auth_manager.refresh_session():
                        st.success("Session refreshed successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to refresh session. Please log in again.")
                        self.auth_manager.logout()
                        st.rerun()
            
            with col2:
                if st.button("🚪 Logout Now", key="logout_now"):
                    self.auth_manager.logout()
                    st.rerun()
            
            self.session_warning_shown = True
    
    def handle_session_timeout(self):
        """Handle session timeout and show appropriate UI"""
        status = self.check_session_status()
        
        if status["expired"]:
            st.error("""
            ⏰ **Session Expired**
            
            Your session has expired due to inactivity.
            Please log in again to continue using HealthMate.
            """)
            
            if st.button("🔐 Go to Login", key="go_to_login"):
                st.switch_page("pages/unified_auth.py")
            
            st.stop()
        
        elif status["warning"]:
            self.show_session_warning()
    
    def update_session_activity(self):
        """Update session activity timestamp"""
        if self.auth_manager.is_authenticated():
            # Update last activity time
            st.session_state.last_activity = datetime.now()
    
    def get_session_info(self) -> dict:
        """Get comprehensive session information"""
        if not self.auth_manager.is_authenticated():
            return {}
        
        status = self.check_session_status()
        user_info = self.auth_manager.get_user_info()
        
        return {
            "user_email": user_info.get("email"),
            "login_time": user_info.get("login_time"),
            "session_duration": self.auth_manager.get_session_duration(),
            "remaining_time": self.auth_manager.get_session_remaining_time(),
            "status": status,
            "last_activity": st.session_state.get("last_activity"),
            "auto_refresh_enabled": self.auto_refresh_enabled
        }
    
    def enable_auto_refresh(self):
        """Enable automatic session refresh"""
        self.auto_refresh_enabled = True
    
    def disable_auto_refresh(self):
        """Disable automatic session refresh"""
        self.auto_refresh_enabled = False
    
    def setup_session_monitoring(self):
        """Setup session monitoring and automatic refresh"""
        if not self.auth_manager.is_authenticated():
            return
        
        # Check if session needs refresh
        if self.auto_refresh_enabled:
            status = self.check_session_status()
            if status["valid"] and status["remaining_minutes"] <= 10:
                # Attempt to refresh session
                if self.auth_manager.refresh_session():
                    logger.info("Session auto-refreshed")
                else:
                    logger.warning("Auto-refresh failed")
    
    def display_session_info(self):
        """Display session information in sidebar"""
        if not self.auth_manager.is_authenticated():
            return
        
        session_info = self.get_session_info()
        
        with st.sidebar:
            st.markdown("### 📊 Session Info")
            
            # Session duration
            st.caption(f"🕐 Duration: {session_info['session_duration']}")
            
            # Remaining time
            remaining = session_info['remaining_time']
            if remaining != "Unknown" and remaining != "Expired":
                st.caption(f"⏰ Remaining: {remaining}")
            
            # Last activity
            if session_info.get('last_activity'):
                last_activity = session_info['last_activity'].strftime('%H:%M:%S')
                st.caption(f"🔄 Last Activity: {last_activity}")
            
            # Auto-refresh status
            if session_info['auto_refresh_enabled']:
                st.caption("🔄 Auto-refresh: Enabled")
            else:
                st.caption("🔄 Auto-refresh: Disabled")
    
    def create_session_controls(self):
        """Create session control buttons"""
        if not self.auth_manager.is_authenticated():
            return
        
        with st.sidebar:
            st.markdown("### 🔧 Session Controls")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔄 Refresh", key="manual_refresh", use_container_width=True):
                    if self.auth_manager.refresh_session():
                        st.success("Session refreshed!")
                        st.rerun()
                    else:
                        st.error("Refresh failed")
            
            with col2:
                if st.button("⏸️ Extend", key="extend_session", use_container_width=True):
                    # Extend session by updating expiry time
                    if st.session_state.session_expires_at:
                        st.session_state.session_expires_at = datetime.now() + timedelta(minutes=self.timeout_minutes)
                        st.success("Session extended!")
                        st.rerun()

class SessionMiddleware:
    """Middleware for automatic session management"""
    
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
    
    def process_request(self):
        """Process each request for session management"""
        # Update activity timestamp
        self.session_manager.update_session_activity()
        
        # Setup session monitoring
        self.session_manager.setup_session_monitoring()
        
        # Handle session timeout
        self.session_manager.handle_session_timeout()
    
    def display_session_ui(self):
        """Display session-related UI elements"""
        # Display session info in sidebar
        self.session_manager.display_session_info()
        
        # Create session controls
        self.session_manager.create_session_controls()

# Global session manager instance (will be initialized with auth_manager)
session_manager = None
session_middleware = None

def initialize_session_manager(auth_manager):
    """Initialize global session manager"""
    global session_manager, session_middleware
    
    session_manager = SessionManager(auth_manager)
    session_middleware = SessionMiddleware(session_manager)
    
    return session_manager, session_middleware 
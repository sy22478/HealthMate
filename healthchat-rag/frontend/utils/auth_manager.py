"""
Authentication Manager for HealthMate Application

This module provides centralized authentication state management,
session handling, and authentication utilities for the HealthMate application.
"""

import streamlit as st
import requests
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthManager:
    """Centralized authentication manager for HealthMate application"""
    
    def __init__(self):
        """Initialize the authentication manager"""
        self.api_base_url = "http://localhost:8003"
        self.session_timeout_minutes = 60  # 1 hour session timeout
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize all authentication-related session state variables"""
        auth_vars = {
            'authenticated': False,
            'token': None,
            'user_email': None,
            'user_id': None,
            'login_time': None,
            'last_login': None,
            'session_expires_at': None,
            'user_profile': {},
            'permissions': [],
            'auth_error': None,
            'auth_message': None,
            'auth_message_type': 'info'
        }
        
        for var, default_value in auth_vars.items():
            if var not in st.session_state:
                st.session_state[var] = default_value
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated and session is valid"""
        # Ensure session state is initialized first
        self._initialize_session_state()
        
        if not st.session_state.authenticated or not st.session_state.token:
            return False
        
        # Check session timeout
        if self._is_session_expired():
            logger.info("Session expired, logging out user")
            self.logout()
            return False
        
        return True
    
    def _is_session_expired(self) -> bool:
        """Check if the current session has expired"""
        if not st.session_state.session_expires_at:
            return False
        
        return datetime.now() > st.session_state.session_expires_at
    
    def login(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate user with email and password"""
        try:
            response = requests.post(
                f"{self.api_base_url}/auth/login",
                json={"email": email, "password": password},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self._set_auth_state(data)
                logger.info(f"User {email} logged in successfully")
                return {"success": True, "message": "Login successful"}
            else:
                error_msg = response.json().get("detail", "Login failed")
                logger.warning(f"Login failed for {email}: {error_msg}")
                return {"success": False, "message": error_msg}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Login request failed: {e}")
            return {"success": False, "message": "Connection error. Please try again."}
    
    def register(self, email: str, password: str, full_name: str = None) -> Dict[str, Any]:
        """Register a new user"""
        try:
            user_data = {"email": email, "password": password}
            if full_name:
                user_data["full_name"] = full_name
            
            response = requests.post(
                f"{self.api_base_url}/auth/register",
                json=user_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self._set_auth_state(data)
                logger.info(f"User {email} registered successfully")
                return {"success": True, "message": "Registration successful"}
            else:
                error_msg = response.json().get("detail", "Registration failed")
                logger.warning(f"Registration failed for {email}: {error_msg}")
                return {"success": False, "message": error_msg}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Registration request failed: {e}")
            return {"success": False, "message": "Connection error. Please try again."}
    
    def forgot_password(self, email: str) -> Dict[str, Any]:
        """Request password reset for user"""
        try:
            response = requests.post(
                f"{self.api_base_url}/auth/forgot-password",
                json={"email": email},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Password reset requested for {email}")
                return {"success": True, "message": "Password reset email sent"}
            else:
                error_msg = response.json().get("detail", "Password reset failed")
                logger.warning(f"Password reset failed for {email}: {error_msg}")
                return {"success": False, "message": error_msg}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Password reset request failed: {e}")
            return {"success": False, "message": "Connection error. Please try again."}
    
    def reset_password(self, token: str, new_password: str) -> Dict[str, Any]:
        """Reset password using reset token"""
        try:
            response = requests.post(
                f"{self.api_base_url}/auth/reset-password",
                json={"token": token, "new_password": new_password},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("Password reset successful")
                return {"success": True, "message": "Password reset successful"}
            else:
                error_msg = response.json().get("detail", "Password reset failed")
                logger.warning(f"Password reset failed: {error_msg}")
                return {"success": False, "message": error_msg}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Password reset request failed: {e}")
            return {"success": False, "message": "Connection error. Please try again."}
    
    def _set_auth_state(self, auth_data: Dict[str, Any]):
        """Set authentication state from API response"""
        st.session_state.authenticated = True
        st.session_state.token = auth_data.get("access_token")
        st.session_state.user_email = auth_data.get("email")
        st.session_state.user_id = auth_data.get("user_id")
        st.session_state.login_time = datetime.now()
        st.session_state.last_login = datetime.now().strftime('%Y-%m-%d %H:%M')
        st.session_state.session_expires_at = datetime.now() + timedelta(minutes=self.session_timeout_minutes)
        st.session_state.user_profile = auth_data.get("user_profile", {})
        st.session_state.permissions = auth_data.get("permissions", [])
        st.session_state.auth_error = None
        st.session_state.auth_message = "Authentication successful"
        st.session_state.auth_message_type = "success"
    
    def logout(self):
        """Logout user and clear all authentication state"""
        logger.info(f"Logging out user {st.session_state.user_email}")
        
        # Clear all authentication state
        auth_vars = [
            'authenticated', 'token', 'user_email', 'user_id', 'login_time',
            'last_login', 'session_expires_at', 'user_profile', 'permissions',
            'auth_error', 'auth_message', 'auth_message_type'
        ]
        
        for var in auth_vars:
            st.session_state[var] = None
        
        # Clear dashboard state
        dashboard_vars = [
            'chat_history', 'current_page', 'show_logout_confirm', 'quick_action',
            'emergency_active', 'emergency_message', 'emergency_recommendations'
        ]
        
        for var in dashboard_vars:
            if var in st.session_state:
                if var == 'current_page':
                    st.session_state[var] = 'Chat'
                elif var in ['chat_history', 'show_logout_confirm', 'emergency_active']:
                    st.session_state[var] = False
                elif var in ['emergency_message', 'emergency_recommendations', 'quick_action']:
                    st.session_state[var] = None
    
    def refresh_session(self) -> bool:
        """Refresh the current session if possible"""
        if not st.session_state.token:
            return False
        
        try:
            response = requests.post(
                f"{self.api_base_url}/auth/refresh",
                headers={"Authorization": f"Bearer {st.session_state.token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self._set_auth_state(data)
                logger.info("Session refreshed successfully")
                return True
            else:
                logger.warning("Session refresh failed")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Session refresh request failed: {e}")
            return False
    
    def get_user_info(self) -> Dict[str, Any]:
        """Get current user information"""
        if not self.is_authenticated():
            return {}
        
        return {
            "email": st.session_state.user_email,
            "user_id": st.session_state.user_id,
            "profile": st.session_state.user_profile,
            "permissions": st.session_state.permissions,
            "login_time": st.session_state.login_time,
            "session_expires_at": st.session_state.session_expires_at
        }
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission"""
        if not self.is_authenticated():
            return False
        
        return permission in st.session_state.permissions
    
    def get_session_duration(self) -> str:
        """Get current session duration as formatted string"""
        if not st.session_state.login_time:
            return "Unknown"
        
        duration = datetime.now() - st.session_state.login_time
        hours = int(duration.total_seconds() // 3600)
        minutes = int((duration.total_seconds() % 3600) // 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    
    def get_session_remaining_time(self) -> str:
        """Get remaining session time as formatted string"""
        if not st.session_state.session_expires_at:
            return "Unknown"
        
        remaining = st.session_state.session_expires_at - datetime.now()
        if remaining.total_seconds() <= 0:
            return "Expired"
        
        hours = int(remaining.total_seconds() // 3600)
        minutes = int((remaining.total_seconds() % 3600) // 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    
    def validate_token(self) -> bool:
        """Validate current token with backend"""
        if not st.session_state.token:
            return False
        
        try:
            response = requests.get(
                f"{self.api_base_url}/auth/validate",
                headers={"Authorization": f"Bearer {st.session_state.token}"},
                timeout=10
            )
            
            return response.status_code == 200
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Token validation failed: {e}")
            return False
    
    def set_auth_message(self, message: str, message_type: str = "info"):
        """Set authentication message for user feedback"""
        st.session_state.auth_message = message
        st.session_state.auth_message_type = message_type
    
    def clear_auth_message(self):
        """Clear authentication message"""
        st.session_state.auth_message = None
        st.session_state.auth_message_type = "info"

# Global authentication manager instance
auth_manager = AuthManager() 
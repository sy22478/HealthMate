"""
Authentication Manager for HealthMate Application

This module provides centralized authentication state management,
session handling, and authentication utilities for the HealthMate application.
"""

import streamlit as st
import requests
import json
import os
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
        # Get API URL from environment variable or use default
        self.api_base_url = os.environ.get("HEALTHMATE_API_URL", "http://localhost:8003")
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
                # Handle different error response formats
                response_data = response.json()
                if "error" in response_data:
                    error_msg = response_data["error"].get("message", "Login failed")
                elif "detail" in response_data:
                    error_msg = response_data["detail"]
                else:
                    error_msg = "Login failed"
                
                logger.warning(f"Login failed for {email}: {error_msg}")
                return {"success": False, "message": error_msg}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Login request failed: {e}")
            return {"success": False, "message": "Connection error. Please try again."}
    
    def register(self, email: str, password: str, full_name: str = None, age: int = None, role: str = "patient") -> Dict[str, Any]:
        """Register a new user"""
        try:
            user_data = {"email": email, "password": password, "role": role}
            if full_name:
                user_data["full_name"] = full_name
            if age:
                user_data["age"] = age
            
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
                # Handle different error response formats
                response_data = response.json()
                if "error" in response_data:
                    error_msg = response_data["error"].get("message", "Registration failed")
                elif "detail" in response_data:
                    error_msg = response_data["detail"]
                else:
                    error_msg = "Registration failed"
                
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
                # Handle different error response formats
                response_data = response.json()
                if "error" in response_data:
                    error_msg = response_data["error"].get("message", "Password reset failed")
                elif "detail" in response_data:
                    error_msg = response_data["detail"]
                else:
                    error_msg = "Password reset failed"
                
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
                # Handle different error response formats
                response_data = response.json()
                if "error" in response_data:
                    error_msg = response_data["error"].get("message", "Password reset failed")
                elif "detail" in response_data:
                    error_msg = response_data["detail"]
                else:
                    error_msg = "Password reset failed"
                
                logger.warning(f"Password reset failed: {error_msg}")
                return {"success": False, "message": error_msg}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Password reset request failed: {e}")
            return {"success": False, "message": "Connection error. Please try again."}
    
    def _set_auth_state(self, auth_data: Dict[str, Any]):
        """Set authentication state in session"""
        st.session_state.authenticated = True
        st.session_state.token = auth_data.get("access_token")
        st.session_state.refresh_token = auth_data.get("refresh_token")
        st.session_state.user_email = auth_data.get("user", {}).get("email")
        st.session_state.user_id = auth_data.get("user", {}).get("id")
        st.session_state.user_role = auth_data.get("user", {}).get("role")
        st.session_state.login_time = datetime.now()
        st.session_state.session_start = datetime.now()
        
        # Store user profile information
        if "user" in auth_data:
            st.session_state.user_profile = auth_data["user"]
    
    def logout(self):
        """Logout user and clear session state"""
        # Clear all authentication-related session state
        auth_keys = [
            'authenticated', 'token', 'refresh_token', 'user_email', 'user_id', 
            'user_role', 'login_time', 'session_start', 'user_profile',
            'just_logged_in', 'just_registered', 'current_page'
        ]
        
        for key in auth_keys:
            if key in st.session_state:
                del st.session_state[key]
        
        logger.info("User logged out successfully")
    
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
        
        # Handle case where login_time might be a string (backward compatibility)
        login_time = st.session_state.login_time
        if isinstance(login_time, str):
            try:
                login_time = datetime.strptime(login_time, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return "Unknown"
        
        duration = datetime.now() - login_time
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
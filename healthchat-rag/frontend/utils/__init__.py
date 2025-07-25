"""
Utils package for HealthMate frontend

This package contains utility modules for authentication, session management,
and other common functionality used across the HealthMate application.
"""

from .auth_manager import auth_manager
from .session_manager import initialize_session_manager

__all__ = ['auth_manager', 'initialize_session_manager'] 
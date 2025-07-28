from datetime import datetime, timedelta
from fastapi import HTTPException, status
from app.utils.jwt_utils import jwt_manager
from app.utils.password_utils import password_manager
from app.utils.rbac import UserRole
import logging

logger = logging.getLogger(__name__)

class AuthService:
    """Enhanced authentication service with security features"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return password_manager.verify_password(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password with validation"""
        hashed_password, errors = password_manager.validate_and_hash_password(password)
        if errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Password validation failed", "errors": errors}
            )
        return hashed_password
    
    def create_access_token(self, data: dict, expires_delta: timedelta = None) -> str:
        """Create an access token with proper expiration"""
        return jwt_manager.create_access_token(data, expires_delta)
    
    def create_refresh_token(self, data: dict) -> str:
        """Create a refresh token"""
        return jwt_manager.create_refresh_token(data)
    
    def verify_token(self, token: str) -> dict:
        """Verify and decode a token"""
        return jwt_manager.verify_token(token, "access")
    
    def refresh_access_token(self, refresh_token: str) -> dict:
        """Create a new access token using a refresh token"""
        return jwt_manager.refresh_access_token(refresh_token)
    
    def blacklist_token(self, token: str) -> bool:
        """Blacklist a token"""
        return jwt_manager.blacklist_token(token)
    
    def revoke_user_tokens(self, user_id: int) -> bool:
        """Revoke all tokens for a user"""
        return jwt_manager.revoke_user_tokens(user_id) 
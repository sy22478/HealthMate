"""
Version 1 Authentication API endpoints.

This module provides versioned authentication endpoints with improved
response optimization, caching, and error handling.
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import time
import json
import gzip
from datetime import datetime, timedelta

from app.database import get_db
from app.models.user import User
from app.schemas.auth_schemas import (
    UserRegister, UserLogin, UserResponse, TokenResponse,
    PasswordChange, UserProfile, TokenRefresh
)
from app.services.auth import AuthService
from app.utils.rate_limiting import rate_limit
from app.utils.cache import cache_response, get_cached_response
from app.utils.pagination import paginate_response
from app.utils.compression import compress_response
from app.utils.audit_logging import audit_log

router = APIRouter(prefix="/auth", tags=["Authentication v1"])
security = HTTPBearer()

@router.post("/register", response_model=Dict[str, Any])
@rate_limit(max_requests=5, window_seconds=300)  # 5 requests per 5 minutes
async def register_user(
    user_data: UserRegister,
    db: Session = Depends(get_db),
    response: Response = None
) -> Dict[str, Any]:
    """
    Register a new user with improved response optimization.
    
    Args:
        user_data: User registration data
        db: Database session
        response: FastAPI response object for headers
        
    Returns:
        Optimized registration response with user info and metadata
    """
    start_time = time.time()
    
    try:
        auth_service = AuthService(db)
        
        # Check if user already exists
        existing_user = auth_service.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already exists"
            )
        
        # Create new user
        user = auth_service.create_user(user_data)
        
        # Generate tokens
        access_token = auth_service.create_access_token(user.id)
        refresh_token = auth_service.create_refresh_token(user.id)
        
        # Prepare optimized response
        response_data = {
            "message": "User registered successfully",
            "user_id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "created_at": user.created_at.isoformat(),
            "metadata": {
                "version": "v1",
                "timestamp": datetime.utcnow().isoformat(),
                "processing_time_ms": round((time.time() - start_time) * 1000, 2)
            }
        }
        
        # Add cache headers
        if response:
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        
        # Audit log
        audit_log(
            event_type="user_registration",
            user_id=user.id,
            user_email=user.email,
            details={"registration_method": "api_v1"}
        )
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        audit_log(
            event_type="user_registration_failed",
            details={"error": str(e), "email": user_data.email}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.post("/login", response_model=Dict[str, Any])
@rate_limit(max_requests=10, window_seconds=300)  # 10 requests per 5 minutes
async def login_user(
    user_data: UserLogin,
    db: Session = Depends(get_db),
    response: Response = None
) -> Dict[str, Any]:
    """
    Authenticate user and return tokens with optimized response.
    
    Args:
        user_data: User login credentials
        db: Database session
        response: FastAPI response object for headers
        
    Returns:
        Optimized login response with tokens and user info
    """
    start_time = time.time()
    
    try:
        auth_service = AuthService(db)
        
        # Authenticate user
        user = auth_service.authenticate_user(user_data.email, user_data.password)
        if not user:
            audit_log(
                event_type="login_failed",
                details={"email": user_data.email, "reason": "invalid_credentials"}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Generate tokens
        access_token = auth_service.create_access_token(user.id)
        refresh_token = auth_service.create_refresh_token(user.id)
        
        # Prepare optimized response
        response_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 1800,  # 30 minutes
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "last_login": datetime.utcnow().isoformat()
            },
            "metadata": {
                "version": "v1",
                "timestamp": datetime.utcnow().isoformat(),
                "processing_time_ms": round((time.time() - start_time) * 1000, 2)
            }
        }
        
        # Add security headers
        if response:
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        
        # Audit log
        audit_log(
            event_type="user_login",
            user_id=user.id,
            user_email=user.email,
            details={"login_method": "api_v1"}
        )
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        audit_log(
            event_type="login_failed",
            details={"error": str(e), "email": user_data.email}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post("/refresh", response_model=Dict[str, Any])
@rate_limit(max_requests=20, window_seconds=300)  # 20 requests per 5 minutes
async def refresh_token(
    token_data: TokenRefresh,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Refresh access token with improved validation.
    
    Args:
        token_data: Refresh token data
        db: Database session
        
    Returns:
        New access and refresh tokens
    """
    try:
        auth_service = AuthService(db)
        
        # Validate refresh token
        user_id = auth_service.verify_refresh_token(token_data.refresh_token)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Generate new tokens
        new_access_token = auth_service.create_access_token(user_id)
        new_refresh_token = auth_service.create_refresh_token(user_id)
        
        # Blacklist old refresh token
        auth_service.blacklist_token(token_data.refresh_token)
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": 1800,
            "metadata": {
                "version": "v1",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

@router.post("/logout")
@rate_limit(max_requests=50, window_seconds=300)  # 50 requests per 5 minutes
async def logout_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Logout user and blacklist tokens.
    
    Args:
        credentials: HTTP bearer token
        db: Database session
        
    Returns:
        Logout confirmation
    """
    try:
        auth_service = AuthService(db)
        
        # Extract token
        token = credentials.credentials
        
        # Blacklist token
        auth_service.blacklist_token(token)
        
        # Audit log
        user_id = auth_service.get_user_id_from_token(token)
        if user_id:
            audit_log(
                event_type="user_logout",
                user_id=user_id,
                details={"logout_method": "api_v1"}
            )
        
        return {"message": "Successfully logged out"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@router.get("/me", response_model=Dict[str, Any])
@cache_response(expire_seconds=300)  # Cache for 5 minutes
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get current user profile with caching.
    
    Args:
        credentials: HTTP bearer token
        db: Database session
        
    Returns:
        Current user profile with metadata
    """
    try:
        auth_service = AuthService(db)
        
        # Get user from token
        user_id = auth_service.get_user_id_from_token(credentials.credentials)
        user = auth_service.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "age": user.age,
            "role": user.role,
            "medical_conditions": user.medical_conditions,
            "medications": user.medications,
            "created_at": user.created_at.isoformat(),
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "metadata": {
                "version": "v1",
                "timestamp": datetime.utcnow().isoformat(),
                "cached": False
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user profile"
        )

@router.post("/change-password")
@rate_limit(max_requests=5, window_seconds=300)  # 5 requests per 5 minutes
async def change_password(
    password_data: PasswordChange,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Change user password with rate limiting.
    
    Args:
        password_data: Password change data
        credentials: HTTP bearer token
        db: Database session
        
    Returns:
        Password change confirmation
    """
    try:
        auth_service = AuthService(db)
        
        # Get user from token
        user_id = auth_service.get_user_id_from_token(credentials.credentials)
        user = auth_service.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify current password
        if not auth_service.verify_password(password_data.current_password, user.hashed_password):
            audit_log(
                event_type="password_change_failed",
                user_id=user.id,
                details={"reason": "invalid_current_password"}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Update password
        auth_service.update_user_password(user.id, password_data.new_password)
        
        # Audit log
        audit_log(
            event_type="password_changed",
            user_id=user.id,
            user_email=user.email,
            details={"change_method": "api_v1"}
        )
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )

@router.get("/token-stats")
async def get_token_statistics(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get token statistics (admin only).
    
    Args:
        credentials: HTTP bearer token
        db: Database session
        
    Returns:
        Token statistics
    """
    try:
        auth_service = AuthService(db)
        
        # Get user and check admin role
        user_id = auth_service.get_user_id_from_token(credentials.credentials)
        user = auth_service.get_user_by_id(user_id)
        
        if not user or user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        # Get statistics
        stats = auth_service.get_token_statistics()
        
        return {
            "blacklisted_tokens": stats.get("blacklisted_tokens", 0),
            "active_refresh_tokens": stats.get("active_refresh_tokens", 0),
            "total_users": stats.get("total_users", 0),
            "active_sessions": stats.get("active_sessions", 0),
            "metadata": {
                "version": "v1",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get token statistics"
        )

@router.get("/auth-stats")
async def get_auth_statistics(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get authentication statistics (admin only).
    
    Args:
        credentials: HTTP bearer token
        db: Database session
        
    Returns:
        Authentication statistics
    """
    try:
        auth_service = AuthService(db)
        
        # Get user and check admin role
        user_id = auth_service.get_user_id_from_token(credentials.credentials)
        user = auth_service.get_user_by_id(user_id)
        
        if not user or user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        # Get statistics
        stats = auth_service.get_auth_statistics()
        
        return {
            "total_users": stats.get("total_users", 0),
            "active_sessions": stats.get("active_sessions", 0),
            "logins_today": stats.get("logins_today", 0),
            "registrations_today": stats.get("registrations_today", 0),
            "failed_attempts_today": stats.get("failed_attempts_today", 0),
            "metadata": {
                "version": "v1",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get auth statistics"
        ) 
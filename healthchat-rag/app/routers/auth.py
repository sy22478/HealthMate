from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, Conversation
from app.services.auth import AuthService
from app.config import settings
from app.utils.auth_middleware import get_current_user, validate_refresh_token
from app.utils.password_utils import password_manager
from app.utils.rbac import UserRole, Permission, require_permission
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime, timedelta, timezone
import logging
from app.utils.encryption_utils import encryption_manager
from app.utils.jwt_utils import jwt_manager
import secrets
from app.utils.audit_logging import AuditLogger

logger = logging.getLogger(__name__)

router = APIRouter()
auth_service = AuthService(settings.secret_key)

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    age: int
    medical_conditions: str = ""
    medications: str = ""
    role: Optional[str] = "patient"
    
    @field_validator('password')
    def validate_password(cls, v):
        is_valid, errors = password_manager.validator.validate_password(v)
        if not is_valid:
            raise ValueError(f"Password validation failed: {'; '.join(errors)}")
        return v
    
    @field_validator('age')
    def validate_age(cls, v):
        if v < 0 or v > 150:
            raise ValueError("Age must be between 0 and 150")
        return v
    
    @field_validator('role')
    def validate_role(cls, v):
        valid_roles = [role.value for role in UserRole]
        if v not in valid_roles:
            raise ValueError(f"Role must be one of: {', '.join(valid_roles)}")
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ForgotPassword(BaseModel):
    email: EmailStr

class ResetPassword(BaseModel):
    token: str
    new_password: str
    
    @field_validator('new_password')
    def validate_password(cls, v):
        is_valid, errors = password_manager.validator.validate_password(v)
        if not is_valid:
            raise ValueError(f"Password validation failed: {'; '.join(errors)}")
        return v

class TokenRefresh(BaseModel):
    refresh_token: str

class PasswordChange(BaseModel):
    current_password: str
    new_password: str
    
    @field_validator('new_password')
    def validate_password(cls, v):
        is_valid, errors = password_manager.validator.validate_password(v)
        if not is_valid:
            raise ValueError(f"Password validation failed: {'; '.join(errors)}")
        return v

class LogoutRequest(BaseModel):
    token: str

# Authentication endpoints

@router.post("/register")
def register(user: UserRegister, db: Session = Depends(get_db), request: Request = None):
    """Register a new user"""
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user.email).first()
        if existing_user:
            AuditLogger.log_auth_event(
                event_type="register",
                user_email=user.email,
                success=False,
                details={"reason": "User already exists"},
                request=request
            )
            raise HTTPException(status_code=409, detail="User already exists")
        
        # Create new user
        hashed_password = auth_service.get_password_hash(user.password)
        db_user = User(
            email=user.email,
            hashed_password=hashed_password,
            full_name=user.full_name,
            age=user.age,
            medical_conditions=user.medical_conditions,
            medications=user.medications,
            role=user.role
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        AuditLogger.log_auth_event(
            event_type="register",
            user_id=db_user.id,
            user_email=db_user.email,
            success=True,
            details={"role": db_user.role},
            request=request
        )
        
        return {
            "message": "User registered successfully",
            "user_id": db_user.id,
            "email": db_user.email,
            "role": db_user.role
        }
        
    except HTTPException:
        raise
    except Exception as e:
        AuditLogger.log_auth_event(
            event_type="register",
            user_email=user.email if 'user' in locals() else None,
            success=False,
            details={"error": str(e)},
            request=request
        )
        raise HTTPException(status_code=500, detail="Registration failed")

@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db), request: Request = None):
    """Login user with access and refresh tokens"""
    try:
        db_user = db.query(User).filter(User.email == user.email).first()
        if not db_user or not auth_service.verify_password(user.password, db_user.hashed_password):
            AuditLogger.log_auth_event(
                event_type="login",
                user_email=user.email,
                success=False,
                details={"reason": "Invalid credentials"},
                request=request
            )
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if not db_user.is_active:
            AuditLogger.log_auth_event(
                event_type="login",
                user_id=db_user.id,
                user_email=db_user.email,
                success=False,
                details={"reason": "Account deactivated"},
                request=request
            )
            raise HTTPException(status_code=401, detail="Account is deactivated")
        
        # Create token data
        token_data = {
            "sub": db_user.email,
            "user_id": db_user.id,
            "email": db_user.email,
            "role": db_user.role
        }
        
        # Create access and refresh tokens
        access_token = auth_service.create_access_token(token_data)
        refresh_token = auth_service.create_refresh_token(token_data)
        
        AuditLogger.log_auth_event(
            event_type="login",
            user_id=db_user.id,
            user_email=db_user.email,
            success=True,
            details={"role": db_user.role},
            request=request
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": db_user.id,
                "email": db_user.email,
                "full_name": db_user.full_name,
                "role": db_user.role
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        AuditLogger.log_auth_event(
            event_type="login",
            user_email=user.email if 'user' in locals() else None,
            success=False,
            details={"error": str(e)},
            request=request
        )
        raise HTTPException(status_code=500, detail="Login failed")

@router.post("/forgot-password")
def forgot_password(request: ForgotPassword, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        # Don't reveal if email exists or not for security
        return {"message": "If the email exists, a password reset link has been sent"}
    
    # Generate reset token
    reset_token = jwt_manager.create_reset_token(user.id, user.email)
    user.reset_token = reset_token
    user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
    db.commit()
    
    # In a real application, you would send an email here
    # For now, we'll just return the token (in production, this should be sent via email)
    return {"message": "Password reset link sent", "reset_token": reset_token}

@router.post("/reset-password")
def reset_password(request: ResetPassword, db: Session = Depends(get_db)):
    """Reset password using JWT reset token"""
    try:
        # Verify the JWT reset token
        payload = jwt_manager.verify_reset_token(request.token)
        
        # Get user from token payload
        user_id = payload.get("user_id")
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(status_code=400, detail="User not found")
        
        # Update password
        user.hashed_password = auth_service.get_password_hash(request.new_password)
        
        # Clear any old reset token fields (for backward compatibility)
        user.reset_token = None
        user.reset_token_expires = None
        
        db.commit()
        
        # Revoke all existing tokens for security
        jwt_manager.revoke_user_tokens(user.id)
        
        logger.info(f"Password reset successful for user: {user.email}")
        
        return {"message": "Password reset successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset error: {str(e)}")
        raise HTTPException(status_code=500, detail="Password reset failed")

@router.post("/refresh")
def refresh_token(request: TokenRefresh):
    """Refresh access token using refresh token"""
    try:
        result = auth_service.refresh_access_token(request.refresh_token)
        logger.info("Token refreshed successfully")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(status_code=500, detail="Token refresh failed")

@router.post("/change-password")
def change_password(
    request: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    http_request: Request = None
):
    """Change password for authenticated user"""
    try:
        # Verify current password
        if not auth_service.verify_password(request.current_password, current_user.hashed_password):
            AuditLogger.log_auth_event(
                event_type="change_password",
                user_id=current_user.id,
                user_email=current_user.email,
                success=False,
                details={"reason": "Current password incorrect"},
                request=http_request
            )
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        
        # Update password
        current_user.hashed_password = auth_service.get_password_hash(request.new_password)
        db.commit()
        
        AuditLogger.log_auth_event(
            event_type="change_password",
            user_id=current_user.id,
            user_email=current_user.email,
            success=True,
            request=http_request
        )
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        AuditLogger.log_auth_event(
            event_type="change_password",
            user_id=current_user.id,
            user_email=current_user.email,
            success=False,
            details={"error": str(e)},
            request=http_request
        )
        raise HTTPException(status_code=500, detail="Password change failed")

@router.post("/logout")
def logout(request: LogoutRequest, http_request: Request = None):
    """Logout user by blacklisting token"""
    try:
        success = auth_service.blacklist_token(request.token)
        if success:
            AuditLogger.log_auth_event(
                event_type="logout",
                success=True,
                details={"token_blacklisted": True},
                request=http_request
            )
            return {"message": "Logged out successfully"}
        else:
            AuditLogger.log_auth_event(
                event_type="logout",
                success=True,
                details={"token_blacklisted": False, "reason": "Blacklisting unavailable"},
                request=http_request
            )
            return {"message": "Logout completed (token blacklisting unavailable)"}
            
    except Exception as e:
        AuditLogger.log_auth_event(
            event_type="logout",
            success=False,
            details={"error": str(e)},
            request=http_request
        )
        return {"message": "Logout completed"}

@router.post("/revoke-all-tokens")
def revoke_all_tokens(current_user: User = Depends(get_current_user), http_request: Request = None):
    """Revoke all tokens for the current user"""
    try:
        success = jwt_manager.revoke_user_tokens(current_user.id)
        if success:
            AuditLogger.log_auth_event(
                event_type="revoke_all_tokens",
                user_id=current_user.id,
                user_email=current_user.email,
                success=True,
                request=http_request
            )
            return {"message": "All tokens revoked successfully"}
        else:
            AuditLogger.log_auth_event(
                event_type="revoke_all_tokens",
                user_id=current_user.id,
                user_email=current_user.email,
                success=False,
                details={"reason": "Failed to revoke tokens"},
                request=http_request
            )
            raise HTTPException(status_code=500, detail="Failed to revoke tokens")
    except HTTPException:
        raise
    except Exception as e:
        AuditLogger.log_auth_event(
            event_type="revoke_all_tokens",
            user_id=current_user.id,
            user_email=current_user.email,
            success=False,
            details={"error": str(e)},
            request=http_request
        )
        raise HTTPException(status_code=500, detail="Token revocation failed")

@router.get("/me")
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "age": current_user.age,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at
    }

@router.post("/revoke-all-tokens")
def revoke_all_tokens(current_user: User = Depends(get_current_user)):
    """Revoke all tokens for the current user"""
    try:
        success = jwt_manager.revoke_user_tokens(current_user.id)
        if success:
            logger.info(f"All tokens revoked for user {current_user.email}")
            return {"message": "All tokens revoked successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to revoke tokens")
    except Exception as e:
        logger.error(f"Error revoking tokens: {str(e)}")
        raise HTTPException(status_code=500, detail="Token revocation failed")

@router.get("/token-stats")
def get_token_statistics(current_user: User = Depends(get_current_user)):
    """Get JWT token usage statistics (admin only)"""
    try:
        # Check if user has admin role
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        stats = jwt_manager.get_token_statistics()
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting token statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get token statistics")

@router.get("/auth-stats")
def get_authentication_stats(current_user: User = Depends(get_current_user)):
    """Get authentication statistics for the current user"""
    try:
        stats = jwt_manager.get_authentication_stats(current_user.id)
        return stats
    except Exception as e:
        logger.error(f"Error getting authentication stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get authentication statistics")

@router.post("/validate-token")
def validate_token(request: LogoutRequest):
    """Validate a token without requiring authentication"""
    try:
        # Decode token to get basic info (without full verification)
        payload = jwt_manager.get_token_payload(request.token)
        
        if not payload:
            return {"valid": False, "reason": "Invalid token format"}
        
        # Check if token is expired
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
            return {"valid": False, "reason": "Token expired"}
        
        # Check if token is blacklisted
        if jwt_manager._is_token_blacklisted(request.token):
            return {"valid": False, "reason": "Token blacklisted"}
        
        return {
            "valid": True,
            "user_id": payload.get("user_id"),
            "email": payload.get("email"),
            "role": payload.get("role"),
            "type": payload.get("type"),
            "expires_at": exp
        }
        
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        return {"valid": False, "reason": "Validation failed"}

@router.post("/logout-all-devices")
def logout_all_devices(current_user: User = Depends(get_current_user)):
    """Logout from all devices by revoking all tokens"""
    try:
        # Revoke all tokens
        success = jwt_manager.revoke_user_tokens(current_user.id)
        
        if success:
            logger.info(f"User {current_user.email} logged out from all devices")
            return {"message": "Logged out from all devices successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to logout from all devices")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error logging out from all devices: {str(e)}")
        raise HTTPException(status_code=500, detail="Logout failed")

@router.get("/session-info")
def get_session_info(current_user: User = Depends(get_current_user)):
    """Get current session information"""
    try:
        # Get authentication stats
        auth_stats = jwt_manager.get_authentication_stats(current_user.id)
        
        return {
            "user_id": current_user.id,
            "email": current_user.email,
            "role": current_user.role,
            "active_sessions": auth_stats.get("active_sessions", 0),
            "refresh_locations": auth_stats.get("refresh_locations", []),
            "last_login": current_user.last_login.isoformat() if current_user.last_login else None
        }
        
    except Exception as e:
        logger.error(f"Error getting session info: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get session information") 
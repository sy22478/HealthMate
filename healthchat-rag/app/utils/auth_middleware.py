"""
Authentication Middleware
Provides token validation and user extraction for FastAPI routes with enhanced security
"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from app.database import get_db
from app.models.user import User
from app.utils.jwt_utils import jwt_manager
import logging
import time
import hashlib
from datetime import datetime, timezone

# Setup logging
logger = logging.getLogger(__name__)
security = HTTPBearer()

class AuthMiddleware:
    """Enhanced authentication middleware for FastAPI routes"""
    
    def __init__(self):
        self.rate_limit_window = 3600  # 1 hour
        self.max_requests_per_hour = 1000
        self.suspicious_activity_threshold = 10
    
    @staticmethod
    async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db),
        request: Request = None
    ) -> User:
        """
        Extract and validate current user from JWT token with enhanced security
        
        Args:
            credentials: HTTP Bearer credentials
            db: Database session
            request: FastAPI request object for additional security checks
            
        Returns:
            Current authenticated user
            
        Raises:
            HTTPException: If token is invalid or user not found
        """
        try:
            token = credentials.credentials
            
            # Rate limiting check
            if request:
                await AuthMiddleware._check_rate_limit(request)
            
            # Verify token
            payload = jwt_manager.verify_token(token, "access")
            
            # Extract user ID
            user_id = payload.get("user_id")
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload"
                )
            
            # Get user from database
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            # Check if user is active
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User account is deactivated"
                )
            
            # Additional security checks
            if request:
                await AuthMiddleware._perform_security_checks(request, user, payload)
            
            # Log successful authentication
            logger.info(f"User {user.email} authenticated successfully from {request.client.host if request else 'unknown'}")
            
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed"
            )
    
    @staticmethod
    async def get_current_user_optional(
        request: Request,
        db: Session = Depends(get_db)
    ) -> Optional[User]:
        """
        Extract current user from JWT token (optional authentication) with security checks
        
        Args:
            request: FastAPI request object
            db: Database session
            
        Returns:
            Current authenticated user or None if not authenticated
        """
        try:
            # Check if Authorization header exists
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return None
            
            # Extract token
            token = auth_header.split(" ")[1]
            
            # Verify token
            payload = jwt_manager.verify_token(token, "access")
            
            # Extract user ID
            user_id = payload.get("user_id")
            if user_id is None:
                return None
            
            # Get user from database
            user = db.query(User).filter(User.id == user_id).first()
            if not user or not user.is_active:
                return None
            
            return user
            
        except Exception:
            return None
    
    @staticmethod
    async def validate_refresh_token(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        request: Request = None
    ) -> dict:
        """
        Validate refresh token with enhanced security
        
        Args:
            credentials: HTTP Bearer credentials
            request: FastAPI request object
            
        Returns:
            Token payload if valid
            
        Raises:
            HTTPException: If token is invalid
        """
        try:
            token = credentials.credentials
            
            # Rate limiting for refresh token requests
            if request:
                await AuthMiddleware._check_rate_limit(request, endpoint="refresh")
            
            payload = jwt_manager.verify_token(token, "refresh")
            
            # Additional security checks for refresh tokens
            if request:
                await AuthMiddleware._check_refresh_token_security(request, payload)
            
            return payload
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Refresh token validation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
    
    @staticmethod
    async def _check_rate_limit(request: Request, endpoint: str = "auth") -> None:
        """
        Check rate limiting for authentication requests
        
        Args:
            request: FastAPI request object
            endpoint: Endpoint type for rate limiting
            
        Raises:
            HTTPException: If rate limit exceeded
        """
        if not jwt_manager.redis_client:
            return
        
        try:
            # Get client IP
            client_ip = request.client.host
            user_agent = request.headers.get("User-Agent", "")
            
            # Create rate limit key
            current_hour = int(time.time() // 3600)
            rate_limit_key = f"rate_limit:{endpoint}:{client_ip}:{current_hour}"
            
            # Check current request count
            current_count = int(jwt_manager.redis_client.get(rate_limit_key) or 0)
            
            if current_count >= AuthMiddleware().max_requests_per_hour:
                logger.warning(f"Rate limit exceeded for IP {client_ip} on endpoint {endpoint}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Please try again later."
                )
            
            # Increment request count
            jwt_manager.redis_client.incr(rate_limit_key)
            jwt_manager.redis_client.expire(rate_limit_key, 3600)  # Expire in 1 hour
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Don't block request if rate limiting fails
    
    @staticmethod
    async def _perform_security_checks(request: Request, user: User, payload: Dict[str, Any]) -> None:
        """
        Perform additional security checks on authentication
        
        Args:
            request: FastAPI request object
            user: Authenticated user
            payload: Token payload
        """
        try:
            # Check for suspicious activity
            client_ip = request.client.host
            user_agent = request.headers.get("User-Agent", "")
            
            # Create activity tracking key
            activity_key = f"auth_activity:{user.id}:{client_ip}"
            
            if jwt_manager.redis_client:
                # Track authentication attempts
                current_attempts = int(jwt_manager.redis_client.get(activity_key) or 0)
                jwt_manager.redis_client.incr(activity_key)
                jwt_manager.redis_client.expire(activity_key, 3600)  # 1 hour window
                
                # Check for suspicious activity
                if current_attempts > AuthMiddleware().suspicious_activity_threshold:
                    logger.warning(f"Suspicious activity detected for user {user.email} from IP {client_ip}")
                    
                    # Log suspicious activity
                    suspicious_key = f"suspicious:{user.id}:{int(time.time())}"
                    suspicious_data = {
                        "ip": client_ip,
                        "user_agent": user_agent,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "attempts": current_attempts + 1
                    }
                    jwt_manager.redis_client.setex(suspicious_key, 86400, str(suspicious_data))  # 24 hours
            
            # Validate token fingerprint if present
            if "fingerprint" in payload:
                expected_fingerprint = AuthMiddleware._generate_request_fingerprint(request, user)
                if payload["fingerprint"] != expected_fingerprint:
                    logger.warning(f"Token fingerprint mismatch for user {user.email}")
                    # Don't block for now, but log the issue
            
        except Exception as e:
            logger.error(f"Security check error: {e}")
            # Don't block authentication if security checks fail
    
    @staticmethod
    async def _check_refresh_token_security(request: Request, payload: Dict[str, Any]) -> None:
        """
        Perform security checks specific to refresh tokens
        
        Args:
            request: FastAPI request object
            payload: Token payload
        """
        try:
            # Check if refresh token is being used from a new location
            client_ip = request.client.host
            user_id = payload.get("user_id")
            
            if jwt_manager.redis_client and user_id:
                # Track refresh token usage by location
                location_key = f"refresh_locations:{user_id}"
                jwt_manager.redis_client.sadd(location_key, client_ip)
                jwt_manager.redis_client.expire(location_key, 86400)  # 24 hours
                
                # Check for unusual locations
                locations = jwt_manager.redis_client.smembers(location_key)
                if len(locations) > 5:  # More than 5 different locations
                    logger.warning(f"Multiple refresh token locations for user {user_id}: {locations}")
            
        except Exception as e:
            logger.error(f"Refresh token security check error: {e}")
    
    @staticmethod
    def _generate_request_fingerprint(request: Request, user: User) -> str:
        """
        Generate a fingerprint for the current request
        
        Args:
            request: FastAPI request object
            user: Authenticated user
            
        Returns:
            Request fingerprint
        """
        # Create fingerprint based on user data and request characteristics
        fingerprint_data = f"{user.id}{user.email}{request.client.host}{request.headers.get('User-Agent', '')}"
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()[:16]
    
    @staticmethod
    async def get_authentication_stats(user_id: int) -> Dict[str, Any]:
        """
        Get authentication statistics for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Authentication statistics
        """
        if not jwt_manager.redis_client:
            return {"error": "Redis not available"}
        
        try:
            stats = {
                "active_sessions": 0,
                "recent_activity": [],
                "suspicious_activity": [],
                "refresh_locations": []
            }
            
            # Count active refresh tokens
            refresh_key = f"refresh_tokens:{user_id}"
            stats["active_sessions"] = jwt_manager.redis_client.scard(refresh_key)
            
            # Get recent suspicious activity
            suspicious_pattern = f"suspicious:{user_id}:*"
            suspicious_keys = jwt_manager.redis_client.keys(suspicious_pattern)
            for key in suspicious_keys[-10:]:  # Last 10 entries
                data = jwt_manager.redis_client.get(key)
                if data:
                    stats["suspicious_activity"].append(data)
            
            # Get refresh token locations
            location_key = f"refresh_locations:{user_id}"
            stats["refresh_locations"] = list(jwt_manager.redis_client.smembers(location_key))
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting authentication stats: {e}")
            return {"error": str(e)}

# Create global instances
auth_middleware = AuthMiddleware()

# Convenience functions for backward compatibility
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    request: Request = None
) -> User:
    """Get current authenticated user"""
    return await AuthMiddleware.get_current_user(credentials, db, request)

async def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user (optional authentication)"""
    return await AuthMiddleware.get_current_user_optional(request, db)

async def validate_refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    request: Request = None
) -> dict:
    """Validate refresh token"""
    return await AuthMiddleware.validate_refresh_token(credentials, request) 
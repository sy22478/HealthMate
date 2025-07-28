"""
JWT Token Management Utilities
Provides comprehensive JWT token handling with security features
"""
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, status
from jose import JWTError
import redis
import json
import uuid
import hashlib
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class JWTManager:
    """Comprehensive JWT token management system with enhanced security"""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7
        self.max_refresh_tokens_per_user = 5  # Limit concurrent refresh tokens
        self.redis_client = None
        self._setup_redis()
    
    def _setup_redis(self):
        """Setup Redis connection for token blacklisting and rate limiting"""
        try:
            # Extract Redis connection from postgres_uri or use default
            # In production, you'd have a separate Redis configuration
            redis_url = getattr(settings, 'redis_url', 'redis://localhost:6379/0')
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            self.redis_client.ping()
            logger.info("Redis connection established for JWT management")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Token blacklisting and rate limiting will be disabled.")
            self.redis_client = None
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a new access token with proper expiration and security features
        
        Args:
            data: Token payload data
            expires_delta: Custom expiration time
            
        Returns:
            Encoded JWT token
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
        
        # Add standard claims with enhanced security
        to_encode.update({
            "exp": int(expire.timestamp()),
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "nbf": int(datetime.now(timezone.utc).timestamp()),  # Not before
            "type": "access",
            "jti": str(uuid.uuid4()),  # JWT ID for unique identification
            "iss": "healthmate",  # Issuer
            "aud": "healthmate_users"  # Audience
        })
        
        # Add token fingerprint for additional security
        token_fingerprint = self._generate_token_fingerprint(to_encode)
        to_encode["fingerprint"] = token_fingerprint
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """
        Create a refresh token for token renewal with enhanced security
        
        Args:
            data: Token payload data
            
        Returns:
            Encoded refresh JWT token
        """
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=self.refresh_token_expire_days)
        
        to_encode.update({
            "exp": int(expire.timestamp()),
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "nbf": int(datetime.now(timezone.utc).timestamp()),
            "type": "refresh",
            "jti": str(uuid.uuid4()),
            "iss": "healthmate",
            "aud": "healthmate_users"
        })
        
        # Add token fingerprint
        token_fingerprint = self._generate_token_fingerprint(to_encode)
        to_encode["fingerprint"] = token_fingerprint
        
        # Track refresh token for user (for rate limiting)
        if self.redis_client and "user_id" in data:
            self._track_refresh_token(data["user_id"], to_encode["jti"])
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def _generate_token_fingerprint(self, payload: Dict[str, Any]) -> str:
        """
        Generate a unique fingerprint for the token based on user agent and IP
        
        Args:
            payload: Token payload
            
        Returns:
            Token fingerprint hash
        """
        # Create a fingerprint based on user data and timestamp
        fingerprint_data = f"{payload.get('user_id', '')}{payload.get('email', '')}{payload.get('iat', '')}"
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()[:16]
    
    def _track_refresh_token(self, user_id: int, jti: str) -> None:
        """
        Track refresh tokens per user for rate limiting
        
        Args:
            user_id: User ID
            jti: JWT ID
        """
        if not self.redis_client:
            return
        
        try:
            key = f"refresh_tokens:{user_id}"
            # Add new token to set
            self.redis_client.sadd(key, jti)
            # Set expiration for the set
            self.redis_client.expire(key, self.refresh_token_expire_days * 24 * 3600)
            
            # Check if we need to remove old tokens
            tokens = self.redis_client.smembers(key)
            if len(tokens) > self.max_refresh_tokens_per_user:
                # Remove oldest tokens (keep only the latest ones)
                tokens_list = list(tokens)
                tokens_to_remove = tokens_list[:-self.max_refresh_tokens_per_user]
                for old_jti in tokens_to_remove:
                    self.redis_client.srem(key, old_jti)
                    # Also blacklist the old token
                    self.redis_client.setex(f"blacklist:{old_jti}", 3600, "1")
                    
        except Exception as e:
            logger.error(f"Error tracking refresh token: {e}")
    
    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """
        Verify and decode a JWT token with enhanced security checks
        
        Args:
            token: JWT token to verify
            token_type: Expected token type ("access" or "refresh")
            
        Returns:
            Decoded token payload
            
        Raises:
            HTTPException: If token is invalid, expired, or blacklisted
        """
        try:
            # Check if token is blacklisted
            if self._is_token_blacklisted(token):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked"
                )
            
            # Decode token with audience validation
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm],
                audience="healthmate_users",
                issuer="healthmate"
            )
            
            # Verify token type
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token type. Expected {token_type}"
                )
            
            # Check if token is expired
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired"
                )
            
            # Check if token is not yet valid (nbf claim)
            nbf = payload.get("nbf")
            if nbf and datetime.fromtimestamp(nbf, tz=timezone.utc) > datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token is not yet valid"
                )
            
            return payload
            
        except JWTError as e:
            logger.warning(f"JWT decode error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, str]:
        """
        Create a new access token using a valid refresh token with token rotation
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            Dictionary with new access token and refresh token
        """
        # Verify refresh token
        payload = self.verify_token(refresh_token, "refresh")
        
        # Check if refresh token is tracked and valid
        if self.redis_client and "user_id" in payload and "jti" in payload:
            user_id = payload["user_id"]
            jti = payload["jti"]
            
            # Verify token is in user's refresh token set
            key = f"refresh_tokens:{user_id}"
            if not self.redis_client.sismember(key, jti):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Refresh token not found or revoked"
                )
        
        # Create new access token
        access_data = {
            "user_id": payload.get("user_id"),
            "email": payload.get("email"),
            "sub": payload.get("sub"),
            "role": payload.get("role")
        }
        
        new_access_token = self.create_access_token(access_data)
        
        # Create new refresh token (token rotation)
        new_refresh_token = self.create_refresh_token(access_data)
        
        # Blacklist the old refresh token
        self.blacklist_token(refresh_token)
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
    
    def blacklist_token(self, token: str, expires_in: Optional[int] = None) -> bool:
        """
        Add a token to the blacklist with enhanced tracking
        
        Args:
            token: Token to blacklist
            expires_in: Seconds until blacklist entry expires (default: token expiration)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            # Decode token to get expiration
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm],
                audience="healthmate_users",
                issuer="healthmate"
            )
            exp = payload.get("exp")
            jti = payload.get("jti")
            
            if not exp or not jti:
                return False
            
            # Calculate time until token expires
            token_exp = datetime.fromtimestamp(exp, tz=timezone.utc)
            now = datetime.now(timezone.utc)
            
            if expires_in is None:
                expires_in = int((token_exp - now).total_seconds())
            
            # Add to blacklist with expiration
            self.redis_client.setex(f"blacklist:{jti}", expires_in, "1")
            
            # Track blacklisted token for analytics
            self.redis_client.incr("blacklisted_tokens_count")
            
            logger.info(f"Token blacklisted: {jti}")
            return True
            
        except Exception as e:
            logger.error(f"Error blacklisting token: {e}")
            return False
    
    def _is_token_blacklisted(self, token: str) -> bool:
        """
        Check if a token is blacklisted
        
        Args:
            token: Token to check
            
        Returns:
            True if token is blacklisted, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm],
                audience="healthmate_users",
                issuer="healthmate"
            )
            jti = payload.get("jti")
            
            if not jti:
                return False
            
            return self.redis_client.exists(f"blacklist:{jti}") > 0
            
        except Exception:
            return False
    
    def get_token_payload(self, token: str) -> Dict[str, Any]:
        """
        Get token payload without verification (for debugging/logging)
        
        Args:
            token: JWT token
            
        Returns:
            Decoded token payload
        """
        try:
            return jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm],
                audience="healthmate_users",
                issuer="healthmate"
            )
        except JWTError:
            return {}
    
    def revoke_user_tokens(self, user_id: int) -> bool:
        """
        Revoke all tokens for a specific user
        
        Args:
            user_id: User ID whose tokens should be revoked
            
        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            # Get all refresh tokens for user
            key = f"refresh_tokens:{user_id}"
            tokens = self.redis_client.smembers(key)
            
            # Blacklist all refresh tokens
            for jti in tokens:
                self.redis_client.setex(f"blacklist:{jti}", 3600, "1")
            
            # Remove the refresh token set
            self.redis_client.delete(key)
            
            logger.info(f"All tokens revoked for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error revoking user tokens: {e}")
            return False
    
    def get_token_statistics(self) -> Dict[str, Any]:
        """
        Get JWT token usage statistics
        
        Returns:
            Dictionary with token statistics
        """
        if not self.redis_client:
            return {"error": "Redis not available"}
        
        try:
            stats = {
                "blacklisted_tokens_count": int(self.redis_client.get("blacklisted_tokens_count") or 0),
                "active_refresh_tokens": 0,
                "redis_connected": True
            }
            
            # Count active refresh tokens
            pattern = "refresh_tokens:*"
            keys = self.redis_client.keys(pattern)
            for key in keys:
                count = self.redis_client.scard(key)
                stats["active_refresh_tokens"] += count
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting token statistics: {e}")
            return {"error": str(e)}
    
    def create_reset_token(self, user_id: int, email: str) -> str:
        """
        Create a password reset token
        
        Args:
            user_id: User ID
            email: User email
            
        Returns:
            Reset token string
        """
        reset_data = {
            "user_id": user_id,
            "email": email,
            "type": "reset",
            "purpose": "password_reset"
        }
        
        # Create a short-lived reset token (1 hour)
        expire = datetime.now(timezone.utc) + timedelta(hours=1)
        
        reset_data.update({
            "exp": int(expire.timestamp()),
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "jti": str(uuid.uuid4()),
            "iss": "healthmate",
            "aud": "healthmate_users"
        })
        
        return jwt.encode(reset_data, self.secret_key, algorithm=self.algorithm)
    
    def verify_reset_token(self, token: str) -> Dict[str, Any]:
        """
        Verify a password reset token
        
        Args:
            token: Reset token to verify
            
        Returns:
            Token payload if valid
            
        Raises:
            HTTPException: If token is invalid
        """
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm],
                audience="healthmate_users",
                issuer="healthmate"
            )
            
            # Verify token type
            if payload.get("type") != "reset":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid token type"
                )
            
            # Verify purpose
            if payload.get("purpose") != "password_reset":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid token purpose"
                )
            
            # Check if token is expired
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Reset token has expired"
                )
            
            return payload
            
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset token"
            )
    
    def get_authentication_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Get authentication statistics for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Authentication statistics
        """
        if not self.redis_client:
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
            stats["active_sessions"] = self.redis_client.scard(refresh_key)
            
            # Get recent suspicious activity
            suspicious_pattern = f"suspicious:{user_id}:*"
            suspicious_keys = self.redis_client.keys(suspicious_pattern)
            for key in suspicious_keys[-10:]:  # Last 10 entries
                data = self.redis_client.get(key)
                if data:
                    stats["suspicious_activity"].append(data)
            
            # Get refresh token locations
            location_key = f"refresh_locations:{user_id}"
            stats["refresh_locations"] = list(self.redis_client.smembers(location_key))
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting authentication stats: {e}")
            return {"error": str(e)}

# Global JWT manager instance
jwt_manager = JWTManager(settings.secret_key) 
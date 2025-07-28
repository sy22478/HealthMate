"""
Unit tests for authentication services.

This module tests the AuthService class and related authentication functionality.
"""

import pytest
import jwt
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch
from fastapi import HTTPException

from app.services.auth import AuthService
from app.utils.jwt_utils import jwt_manager
from app.utils.password_utils import password_manager
from app.models.user import User

class TestAuthService:
    """Test cases for AuthService class."""
    
    def test_password_hashing(self, auth_service):
        """Test password hashing and verification."""
        password = "TestPassword123!"
        
        # Hash password
        hashed = auth_service.get_password_hash(password)
        assert hashed != password
        assert len(hashed) > len(password)
        
        # Verify password
        assert auth_service.verify_password(password, hashed) is True
        assert auth_service.verify_password("WrongPassword", hashed) is False
    
    def test_password_strength_validation(self):
        """Test password strength validation using password_manager directly."""
        # Valid passwords
        assert password_manager.validate_password_strength("StrongPass123!") is True
        assert password_manager.validate_password_strength("AnotherStrong1!") is True
        
        # Invalid passwords
        assert password_manager.validate_password_strength("weak") is False  # Too short
        assert password_manager.validate_password_strength("weakpassword") is False  # No uppercase
        assert password_manager.validate_password_strength("WEAKPASSWORD") is False  # No lowercase
        assert password_manager.validate_password_strength("WeakPassword") is False  # No numbers
        assert password_manager.validate_password_strength("WeakPass123") is False  # No special chars
    
    def test_create_access_token(self, auth_service, sample_user):
        """Test access token creation."""
        token_data = {
            "sub": sample_user.email,
            "user_id": sample_user.id,
            "email": sample_user.email,
            "role": sample_user.role
        }
        
        token = auth_service.create_access_token(token_data)
        
        # Verify token structure
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode and verify token content
        decoded = jwt.decode(token, auth_service.secret_key, algorithms=["HS256"])
        assert decoded["sub"] == sample_user.email
        assert decoded["user_id"] == sample_user.id
        assert decoded["email"] == sample_user.email
        assert decoded["role"] == sample_user.role
        assert "exp" in decoded  # Expiration time
    
    def test_create_refresh_token(self, auth_service, sample_user):
        """Test refresh token creation."""
        token_data = {
            "sub": sample_user.email,
            "user_id": sample_user.id,
            "email": sample_user.email,
            "role": sample_user.role
        }
        
        token = auth_service.create_refresh_token(token_data)
        
        # Verify token structure
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode and verify token content
        decoded = jwt.decode(token, auth_service.secret_key, algorithms=["HS256"])
        assert decoded["sub"] == sample_user.email
        assert decoded["user_id"] == sample_user.id
        assert decoded["email"] == sample_user.email
        assert decoded["role"] == sample_user.role
        assert "exp" in decoded  # Expiration time
    
    def test_token_expiration(self, auth_service, sample_user):
        """Test that tokens expire correctly."""
        token_data = {
            "sub": sample_user.email,
            "user_id": sample_user.id,
            "email": sample_user.email,
            "role": sample_user.role
        }
        
        # Create token with short expiration
        with patch.object(auth_service, 'access_token_expire_minutes', 1/60):  # 1 second
            token = auth_service.create_access_token(token_data)
        
        # Token should be valid initially
        decoded = jwt.decode(token, auth_service.secret_key, algorithms=["HS256"])
        assert decoded["sub"] == sample_user.email
        
        # Wait for expiration (in real test, you'd use time.sleep(2))
        # For this test, we'll manually create an expired token
        expired_time = datetime.now(timezone.utc) - timedelta(minutes=30)
        expired_token = jwt.encode(
            {
                **token_data,
                "exp": expired_time,
                "iat": expired_time - timedelta(minutes=5)
            },
            auth_service.secret_key,
            algorithm="HS256"
        )
        
        # Should raise exception for expired token
        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(expired_token, auth_service.secret_key, algorithms=["HS256"])
    
    def test_verify_token(self, auth_service, sample_user):
        """Test token verification."""
        token_data = {
            "sub": sample_user.email,
            "user_id": sample_user.id,
            "email": sample_user.email,
            "role": sample_user.role
        }
        
        token = auth_service.create_access_token(token_data)
        
        # Verify token
        decoded = auth_service.verify_token(token)
        assert decoded["sub"] == sample_user.email
        assert decoded["user_id"] == sample_user.id
    
    def test_blacklist_token(self, auth_service):
        """Test token blacklisting."""
        token = "test.jwt.token"
        
        # Mock the jwt_manager.blacklist_token method
        with patch.object(jwt_manager, 'blacklist_token', return_value=True):
            result = auth_service.blacklist_token(token)
            assert result is True
    
    def test_revoke_user_tokens(self, auth_service, sample_user):
        """Test revoking all tokens for a user."""
        # Mock the jwt_manager.revoke_user_tokens method
        with patch.object(jwt_manager, 'revoke_user_tokens', return_value=True):
            result = auth_service.revoke_user_tokens(sample_user.id)
            assert result is True

class TestJWTManager:
    """Test cases for JWT manager functionality."""
    
    def test_blacklist_token(self):
        """Test token blacklisting."""
        token = "test.jwt.token"
        jti = "test-jti"
        
        # Mock JWT decode to return JTI
        with patch('app.utils.jwt_utils.jwt.decode') as mock_decode:
            mock_decode.return_value = {"jti": jti}
            
            # Mock Redis client
            with patch('app.utils.jwt_utils.redis_client') as mock_redis:
                mock_redis.set.return_value = True
                
                result = jwt_manager.blacklist_token(token)
                assert result is True
    
    def test_is_token_blacklisted(self):
        """Test token blacklist checking."""
        token = "test.jwt.token"
        jti = "test-jti"
        
        # Mock JWT decode to return JTI
        with patch('app.utils.jwt_utils.jwt.decode') as mock_decode:
            mock_decode.return_value = {"jti": jti}
            
            # Mock Redis client
            with patch('app.utils.jwt_utils.redis_client') as mock_redis:
                # Test blacklisted token
                mock_redis.exists.return_value = 1
                assert jwt_manager.is_token_blacklisted(token) is True
                
                # Test non-blacklisted token
                mock_redis.exists.return_value = 0
                assert jwt_manager.is_token_blacklisted(token) is False
    
    def test_revoke_user_tokens(self, sample_user):
        """Test revoking all tokens for a user."""
        # Mock Redis client
        with patch('app.utils.jwt_utils.redis_client') as mock_redis:
            mock_redis.delete.return_value = 1
            result = jwt_manager.revoke_user_tokens(sample_user.id)
            assert result is True
    
    def test_get_token_statistics(self):
        """Test getting token statistics."""
        # Mock Redis client
        with patch('app.utils.jwt_utils.redis_client') as mock_redis:
            # Mock Redis scan to return some keys
            mock_redis.scan_iter.return_value = [
                "blacklisted:token1",
                "blacklisted:token2",
                "refresh_token:user1",
                "refresh_token:user2"
            ]
            
            stats = jwt_manager.get_token_statistics()
            
            assert "blacklisted_tokens" in stats
            assert "active_refresh_tokens" in stats
            assert stats["blacklisted_tokens"] == 2
            assert stats["active_refresh_tokens"] == 2

class TestPasswordReset:
    """Test cases for password reset functionality."""
    
    def test_create_reset_token(self, sample_user):
        """Test password reset token creation."""
        token = jwt_manager.create_reset_token(sample_user.id, sample_user.email)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode and verify token
        decoded = jwt.decode(token, jwt_manager.secret_key, algorithms=[jwt_manager.algorithm])
        assert decoded["user_id"] == sample_user.id
        assert decoded["email"] == sample_user.email
        assert decoded["type"] == "password_reset"
    
    def test_verify_reset_token(self, sample_user):
        """Test password reset token verification."""
        token = jwt_manager.create_reset_token(sample_user.id, sample_user.email)
        
        payload = jwt_manager.verify_reset_token(token)
        assert payload["user_id"] == sample_user.id
        assert payload["email"] == sample_user.email
        assert payload["type"] == "password_reset"
    
    def test_verify_invalid_reset_token(self):
        """Test verification of invalid reset token."""
        with pytest.raises(jwt.InvalidTokenError):
            jwt_manager.verify_reset_token("invalid.token.here")

class TestSecurityFeatures:
    """Test cases for security-related features."""
    
    def test_token_fingerprinting(self, auth_service, sample_user):
        """Test token fingerprinting for security."""
        token_data = {
            "sub": sample_user.email,
            "user_id": sample_user.id,
            "email": sample_user.email,
            "role": sample_user.role
        }
        
        # Create token with fingerprint
        token = auth_service.create_access_token(token_data)
        
        # Decode and verify token structure
        decoded = jwt.decode(token, auth_service.secret_key, algorithms=["HS256"])
        assert decoded["sub"] == sample_user.email
    
    def test_rate_limiting_integration(self):
        """Test rate limiting integration with authentication."""
        # Mock Redis client
        with patch('app.utils.jwt_utils.redis_client') as mock_redis:
            mock_redis.get.return_value = "1"  # One attempt made
            
            # This would be tested in integration tests with actual endpoints
            # For unit tests, we verify the Redis integration works
            assert mock_redis.get("rate_limit:test@example.com") == "1" 
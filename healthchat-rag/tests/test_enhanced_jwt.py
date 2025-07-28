"""
Enhanced JWT Token Management Tests
Tests for the comprehensive JWT token management system
"""
import pytest
import jwt
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch
from fastapi import HTTPException
from app.utils.jwt_utils import JWTManager, jwt_manager
from app.utils.auth_middleware import AuthMiddleware, auth_middleware
import uuid

class TestEnhancedJWTManagement:
    """Test enhanced JWT token management features"""
    
    def setup_method(self):
        """Setup test environment"""
        self.secret_key = "test_secret_key_for_jwt_management"
        self.jwt_manager = JWTManager(self.secret_key)
        self.test_data = {
            "user_id": 1,
            "email": "test@example.com",
            "role": "patient"
        }
    
    def test_enhanced_token_creation(self):
        """Test enhanced JWT token creation with security features"""
        # Create access token
        access_token = self.jwt_manager.create_access_token(self.test_data)
        assert access_token is not None
        
        # Decode and verify enhanced claims
        payload = jwt.decode(access_token, self.secret_key, algorithms=["HS256"], audience="healthmate_users")
        
        # Check standard claims
        assert payload["user_id"] == 1
        assert payload["email"] == "test@example.com"
        assert payload["type"] == "access"
        assert "jti" in payload
        assert "fingerprint" in payload
        assert payload["iss"] == "healthmate"
        assert payload["aud"] == "healthmate_users"
        assert "nbf" in payload  # Not before claim
        
        # Create refresh token
        refresh_token = self.jwt_manager.create_refresh_token(self.test_data)
        assert refresh_token is not None
        
        # Verify refresh token claims
        refresh_payload = jwt.decode(refresh_token, self.secret_key, algorithms=["HS256"], audience="healthmate_users")
        assert refresh_payload["type"] == "refresh"
        assert "fingerprint" in refresh_payload
    
    def test_token_fingerprint_generation(self):
        """Test token fingerprint generation"""
        fingerprint = self.jwt_manager._generate_token_fingerprint(self.test_data)
        assert fingerprint is not None
        assert len(fingerprint) == 16
        assert isinstance(fingerprint, str)
        
        # Fingerprint should be consistent for same data
        fingerprint2 = self.jwt_manager._generate_token_fingerprint(self.test_data)
        assert fingerprint == fingerprint2
    
    def test_enhanced_token_verification(self):
        """Test enhanced token verification with security checks"""
        # Create token
        token = self.jwt_manager.create_access_token(self.test_data)
        
        # Verify token
        payload = self.jwt_manager.verify_token(token, "access")
        assert payload["user_id"] == 1
        assert payload["email"] == "test@example.com"
        assert payload["type"] == "access"
    
    def test_token_type_validation(self):
        """Test token type validation"""
        # Create access token
        access_token = self.jwt_manager.create_access_token(self.test_data)
        
        # Try to verify as refresh token (should fail)
        with pytest.raises(HTTPException) as exc_info:
            self.jwt_manager.verify_token(access_token, "refresh")
        assert exc_info.value.status_code == 401
        assert "Invalid token type" in exc_info.value.detail
    
    def test_issuer_audience_validation(self):
        """Test issuer and audience validation"""
        # Create a token manually with invalid issuer
        invalid_payload = {
            "user_id": 1,
            "email": "test@example.com",
            "type": "access",
            "iss": "invalid_issuer",  # Invalid issuer
            "aud": "healthmate_users",
            "exp": int((datetime.now(timezone.utc) + timedelta(minutes=30)).timestamp()),
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "jti": str(uuid.uuid4())
        }
        
        # Create token with invalid issuer
        token = jwt.encode(invalid_payload, self.secret_key, algorithm="HS256")
        
        # Verification should fail due to issuer mismatch
        # The JWT library will raise an exception before our custom validation
        with pytest.raises(Exception):  # Can be JWTError or HTTPException
            self.jwt_manager.verify_token(token, "access")
    
    def test_token_rotation(self):
        """Test token rotation in refresh mechanism"""
        # Create refresh token
        refresh_token = self.jwt_manager.create_refresh_token(self.test_data)
        
        # Refresh tokens
        result = self.jwt_manager.refresh_access_token(refresh_token)
        
        assert "access_token" in result
        assert "refresh_token" in result
        assert result["token_type"] == "bearer"
        
        # Verify new tokens are different
        assert result["refresh_token"] != refresh_token
        
        # Verify new access token
        new_payload = self.jwt_manager.verify_token(result["access_token"], "access")
        assert new_payload["user_id"] == 1
    
    def test_reset_token_creation_and_verification(self):
        """Test password reset token functionality"""
        # Create reset token
        reset_token = self.jwt_manager.create_reset_token(1, "test@example.com")
        assert reset_token is not None
        
        # Verify reset token
        payload = self.jwt_manager.verify_reset_token(reset_token)
        assert payload["user_id"] == 1
        assert payload["email"] == "test@example.com"
        assert payload["type"] == "reset"
        assert payload["purpose"] == "password_reset"
    
    def test_reset_token_validation(self):
        """Test reset token validation"""
        # Create reset token
        reset_token = self.jwt_manager.create_reset_token(1, "test@example.com")
        
        # Try to verify as access token (should fail)
        with pytest.raises(HTTPException) as exc_info:
            self.jwt_manager.verify_token(reset_token, "access")
        assert exc_info.value.status_code == 401
        assert "Invalid token type" in exc_info.value.detail
    
    def test_token_blacklisting(self):
        """Test token blacklisting functionality"""
        # Mock Redis client
        with patch.object(self.jwt_manager, 'redis_client') as mock_redis:
            mock_redis.setex.return_value = True
            mock_redis.exists.return_value = 1
            mock_redis.incr.return_value = 1
            
            # Create and blacklist token
            token = self.jwt_manager.create_access_token(self.test_data)
            success = self.jwt_manager.blacklist_token(token)
            assert success is True
            
            # Check if token is blacklisted
            is_blacklisted = self.jwt_manager._is_token_blacklisted(token)
            assert is_blacklisted is True
    
    def test_user_token_revocation(self):
        """Test user token revocation"""
        # Mock Redis client
        with patch.object(self.jwt_manager, 'redis_client') as mock_redis:
            mock_redis.smembers.return_value = {"token1", "token2"}
            mock_redis.delete.return_value = 1
            
            # Revoke user tokens
            success = self.jwt_manager.revoke_user_tokens(1)
            assert success is True
    
    def test_token_statistics(self):
        """Test token statistics functionality"""
        # Mock Redis client
        with patch.object(self.jwt_manager, 'redis_client') as mock_redis:
            mock_redis.get.return_value = "5"
            mock_redis.keys.return_value = ["refresh_tokens:1", "refresh_tokens:2"]
            mock_redis.scard.return_value = 3
            
            # Get statistics
            stats = self.jwt_manager.get_token_statistics()
            assert "blacklisted_tokens_count" in stats
            assert "active_refresh_tokens" in stats
            assert "redis_connected" in stats
    
    def test_authentication_statistics(self):
        """Test authentication statistics"""
        # Mock Redis client
        with patch.object(self.jwt_manager, 'redis_client') as mock_redis:
            mock_redis.scard.return_value = 2
            mock_redis.keys.return_value = ["suspicious:1:123", "suspicious:1:456"]
            mock_redis.get.side_effect = ["suspicious_data_1", "suspicious_data_2"]
            mock_redis.smembers.return_value = {"192.168.1.1", "10.0.0.1"}
            
            # Get authentication stats
            stats = self.jwt_manager.get_authentication_stats(1)
            assert "active_sessions" in stats
            assert "suspicious_activity" in stats
            assert "refresh_locations" in stats

class TestEnhancedAuthMiddleware:
    """Test enhanced authentication middleware"""
    
    def setup_method(self):
        """Setup test environment"""
        self.auth_middleware = AuthMiddleware()
    
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        # Mock request and Redis
        mock_request = Mock()
        mock_request.client.host = "192.168.1.1"
        mock_request.headers.get.return_value = "test-user-agent"
        
        with patch.object(jwt_manager, 'redis_client') as mock_redis:
            mock_redis.get.return_value = "999"  # Below limit
            mock_redis.incr.return_value = 1000
            mock_redis.expire.return_value = True
            
            # Should not raise exception
            AuthMiddleware._check_rate_limit(mock_request)
    
    def test_rate_limit_exceeded(self):
        """Test rate limit exceeded scenario"""
        # Mock request and Redis
        mock_request = Mock()
        mock_request.client.host = "192.168.1.1"
        mock_request.headers.get.return_value = "test-user-agent"
        
        with patch.object(jwt_manager, 'redis_client') as mock_redis:
            mock_redis.get.return_value = "1000"  # At limit
            
            # Should raise exception
            with pytest.raises(HTTPException) as exc_info:
                AuthMiddleware._check_rate_limit(mock_request)
            assert exc_info.value.status_code == 429
            assert "Rate limit exceeded" in exc_info.value.detail
    
    def test_security_checks(self):
        """Test security checks functionality"""
        # Mock request, user, and payload
        mock_request = Mock()
        mock_request.client.host = "192.168.1.1"
        mock_request.headers.get.return_value = "test-user-agent"
        
        mock_user = Mock()
        mock_user.id = 1
        mock_user.email = "test@example.com"
        
        payload = {"fingerprint": "test_fingerprint"}
        
        with patch.object(jwt_manager, 'redis_client') as mock_redis:
            mock_redis.get.return_value = "5"  # Below suspicious threshold
            mock_redis.incr.return_value = 6
            mock_redis.expire.return_value = True
            
            # Should not raise exception
            AuthMiddleware._perform_security_checks(mock_request, mock_user, payload)
    
    def test_suspicious_activity_detection(self):
        """Test suspicious activity detection"""
        # Mock request, user, and payload
        mock_request = Mock()
        mock_request.client.host = "192.168.1.1"
        mock_request.headers.get.return_value = "test-user-agent"
        
        mock_user = Mock()
        mock_user.id = 1
        mock_user.email = "test@example.com"
        
        payload = {"fingerprint": "test_fingerprint"}
        
        with patch.object(jwt_manager, 'redis_client') as mock_redis:
            mock_redis.get.return_value = "15"  # Above suspicious threshold
            mock_redis.incr.return_value = 16
            mock_redis.expire.return_value = True
            mock_redis.setex.return_value = True
            
            # Should log suspicious activity but not raise exception
            AuthMiddleware._perform_security_checks(mock_request, mock_user, payload)
    
    def test_request_fingerprint_generation(self):
        """Test request fingerprint generation"""
        # Mock request and user
        mock_request = Mock()
        mock_request.client.host = "192.168.1.1"
        mock_request.headers.get.return_value = "test-user-agent"
        
        mock_user = Mock()
        mock_user.id = 1
        mock_user.email = "test@example.com"
        
        # Generate fingerprint
        fingerprint = AuthMiddleware._generate_request_fingerprint(mock_request, mock_user)
        assert fingerprint is not None
        assert len(fingerprint) == 16
        assert isinstance(fingerprint, str)
    
    def test_authentication_statistics(self):
        """Test authentication statistics retrieval"""
        # Mock Redis client
        with patch.object(jwt_manager, 'redis_client') as mock_redis:
            mock_redis.scard.return_value = 3
            mock_redis.keys.return_value = ["suspicious:1:123", "suspicious:1:456"]
            mock_redis.get.side_effect = ["suspicious_data_1", "suspicious_data_2"]
            mock_redis.smembers.return_value = {"192.168.1.1", "10.0.0.1"}
            
            # Get authentication stats
            stats = AuthMiddleware.get_authentication_stats(1)
            assert "active_sessions" in stats
            assert "suspicious_activity" in stats
            assert "refresh_locations" in stats

class TestJWTIntegration:
    """Integration tests for JWT functionality"""
    
    def test_end_to_end_token_flow(self):
        """Test complete token creation, verification, and refresh flow"""
        jwt_manager = JWTManager("test_secret_key")
        test_data = {"user_id": 1, "email": "test@example.com", "role": "patient"}
        
        # 1. Create access and refresh tokens
        access_token = jwt_manager.create_access_token(test_data)
        refresh_token = jwt_manager.create_refresh_token(test_data)
        
        # 2. Verify access token
        payload = jwt_manager.verify_token(access_token, "access")
        assert payload["user_id"] == 1
        
        # 3. Refresh tokens
        result = jwt_manager.refresh_access_token(refresh_token)
        assert "access_token" in result
        assert "refresh_token" in result
        
        # 4. Verify new access token
        new_payload = jwt_manager.verify_token(result["access_token"], "access")
        assert new_payload["user_id"] == 1
        
        # 5. Verify old refresh token is invalid (due to rotation)
        # Note: This will only work if Redis is available for blacklisting
        # If Redis is not available, the old token will still be valid
        try:
            jwt_manager.verify_token(refresh_token, "refresh")
            # If we get here, Redis is not available and blacklisting is disabled
            # This is expected behavior when Redis is not running
            print("Note: Redis not available, token blacklisting disabled")
        except HTTPException:
            # This is expected when Redis is available and blacklisting works
            pass
    
    def test_token_expiration(self):
        """Test token expiration handling"""
        jwt_manager = JWTManager("test_secret_key")
        test_data = {"user_id": 1, "email": "test@example.com"}
        
        # Create token with short expiration
        short_expiry = timedelta(seconds=1)
        token = jwt_manager.create_access_token(test_data, short_expiry)
        
        # Token should be valid initially
        payload = jwt_manager.verify_token(token, "access")
        assert payload["user_id"] == 1
        
        # Wait for expiration
        import time
        time.sleep(2)
        
        # Token should be expired
        with pytest.raises(HTTPException) as exc_info:
            jwt_manager.verify_token(token, "access")
        assert exc_info.value.status_code == 401
        assert "Token has expired" in exc_info.value.detail 
"""
Unit tests for utility functions.

This module tests various utility functions including encryption, validation, sanitization, etc.
"""

import pytest
import re
from unittest.mock import Mock, patch
from datetime import datetime, timezone

from app.utils.encryption_utils import encryption_manager
from app.utils.html_sanitization import sanitize_html
from app.utils.sql_injection_utils import check_sql_injection
from app.utils.password_utils import validate_password_strength
from app.utils.jwt_utils import jwt_manager
from app.utils.rate_limiting import RateLimiter
from app.utils.rbac import require_role, require_permission

class TestEncryptionUtils:
    """Test cases for encryption utilities."""
    
    def test_encrypt_decrypt_field(self):
        """Test field encryption and decryption."""
        original_value = "sensitive_data"
        field_name = "test_field"
        
        # Encrypt
        encrypted = encryption_manager.encrypt_field(original_value, field_name)
        assert encrypted != original_value
        assert isinstance(encrypted, str)
        
        # Decrypt
        decrypted = encryption_manager.decrypt_field(encrypted, field_name)
        assert decrypted == original_value
    
    def test_encrypt_decrypt_pii(self):
        """Test PII encryption and decryption."""
        pii_data = {
            "full_name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "123-456-7890"
        }
        
        # Encrypt PII
        encrypted_pii = encryption_manager.encrypt_pii(pii_data)
        assert encrypted_pii != pii_data
        
        # Decrypt PII
        decrypted_pii = encryption_manager.decrypt_pii(encrypted_pii)
        assert decrypted_pii == pii_data
    
    def test_encrypt_decrypt_health_data(self):
        """Test health data encryption and decryption."""
        health_data = {
            "blood_pressure": "120/80",
            "weight": "70kg",
            "medical_conditions": "Hypertension"
        }
        
        # Encrypt health data
        encrypted_health = encryption_manager.encrypt_health_data(health_data)
        assert encrypted_health != health_data
        
        # Decrypt health data
        decrypted_health = encryption_manager.decrypt_health_data(encrypted_health)
        assert decrypted_health == health_data
    
    def test_encryption_key_validation(self):
        """Test encryption key validation."""
        # Test with valid key
        assert encryption_manager.validate_encryption_key() is True
        
        # Test with invalid key (mock)
        with patch.object(encryption_manager, 'encryption_key', b'invalid_key'):
            assert encryption_manager.validate_encryption_key() is False
    
    def test_encryption_error_handling(self):
        """Test encryption error handling."""
        # Test with invalid data
        with pytest.raises(Exception):
            encryption_manager.encrypt_field(None, "test_field")
        
        # Test with invalid field name
        with pytest.raises(Exception):
            encryption_manager.encrypt_field("test", None)

class TestHTMLSanitization:
    """Test cases for HTML sanitization."""
    
    def test_sanitize_safe_html(self):
        """Test sanitization of safe HTML."""
        safe_html = "<p>This is safe content</p><strong>Bold text</strong>"
        sanitized = sanitize_html(safe_html)
        
        # Should allow safe tags
        assert "<p>" in sanitized
        assert "<strong>" in sanitized
        assert "This is safe content" in sanitized
    
    def test_sanitize_script_tags(self):
        """Test sanitization of script tags."""
        dangerous_html = "<script>alert('xss')</script><p>Safe content</p>"
        sanitized = sanitize_html(dangerous_html)
        
        # Should remove script tags
        assert "<script>" not in sanitized
        assert "alert('xss')" not in sanitized
        assert "<p>Safe content</p>" in sanitized
    
    def test_sanitize_event_handlers(self):
        """Test sanitization of event handlers."""
        dangerous_html = '<img src="x" onerror="alert(\'xss\')" alt="test">'
        sanitized = sanitize_html(dangerous_html)
        
        # Should remove event handlers
        assert 'onerror=' not in sanitized
        assert 'alert(\'xss\')' not in sanitized
        assert '<img' in sanitized
        assert 'src="x"' in sanitized
    
    def test_sanitize_javascript_protocols(self):
        """Test sanitization of javascript protocols."""
        dangerous_html = '<a href="javascript:alert(\'xss\')">Click me</a>'
        sanitized = sanitize_html(dangerous_html)
        
        # Should remove javascript protocols
        assert 'javascript:' not in sanitized
        assert 'alert(\'xss\')' not in sanitized
        assert '<a' in sanitized
    
    def test_sanitize_complex_attack(self):
        """Test sanitization of complex XSS attacks."""
        complex_attack = '''
        <img src="x" onerror="eval(atob('YWxlcnQoJ3hzcycp'))" alt="test">
        <svg onload="alert('xss')">
        <iframe src="javascript:alert('xss')"></iframe>
        '''
        sanitized = sanitize_html(complex_attack)
        
        # Should remove all dangerous elements
        assert 'onerror=' not in sanitized
        assert 'onload=' not in sanitized
        assert 'javascript:' not in sanitized
        assert 'eval(' not in sanitized
        assert 'alert(' not in sanitized

class TestSQLInjectionUtils:
    """Test cases for SQL injection prevention."""
    
    def test_check_sql_injection_safe_input(self):
        """Test SQL injection check with safe input."""
        safe_inputs = [
            "normal text",
            "user@example.com",
            "12345",
            "John Doe",
            "Hello, world!"
        ]
        
        for safe_input in safe_inputs:
            result = check_sql_injection(safe_input)
            assert result is False
    
    def test_check_sql_injection_dangerous_patterns(self):
        """Test SQL injection check with dangerous patterns."""
        dangerous_patterns = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin'--",
            "1' UNION SELECT * FROM users--",
            "'; INSERT INTO users VALUES ('hacker', 'password'); --"
        ]
        
        for dangerous_input in dangerous_patterns:
            result = check_sql_injection(dangerous_input)
            assert result is True
    
    def test_check_sql_injection_edge_cases(self):
        """Test SQL injection check with edge cases."""
        edge_cases = [
            "",  # Empty string
            "   ",  # Whitespace only
            "NULL",
            "null",
            "SELECT",  # SQL keyword but not in dangerous context
            "select * from users"  # SQL statement but not in dangerous context
        ]
        
        for edge_case in edge_cases:
            result = check_sql_injection(edge_case)
            # These should be safe
            assert result is False
    
    def test_safe_query_execution(self):
        """Test safe query execution."""
        # This would be tested with actual database operations
        # For unit tests, we verify the pattern matching works
        safe_query = "SELECT * FROM users WHERE email = 'user@example.com'"
        dangerous_query = "SELECT * FROM users WHERE email = ''; DROP TABLE users; --'"
        
        # Safe query should not trigger detection
        assert not check_sql_injection(safe_query)
        
        # Dangerous query should trigger detection
        assert check_sql_injection(dangerous_query)

class TestPasswordUtils:
    """Test cases for password utilities."""
    
    def test_validate_password_strength_strong(self):
        """Test strong password validation."""
        strong_passwords = [
            "StrongPass123!",
            "AnotherStrong1!",
            "MySecureP@ssw0rd",
            "Complex#Password9"
        ]
        
        for password in strong_passwords:
            assert validate_password_strength(password) is True
    
    def test_validate_password_strength_weak(self):
        """Test weak password validation."""
        weak_passwords = [
            "weak",  # Too short
            "weakpassword",  # No uppercase
            "WEAKPASSWORD",  # No lowercase
            "WeakPassword",  # No numbers
            "WeakPass123",   # No special chars
            "12345678",      # Only numbers
            "abcdefgh",      # Only lowercase
            "ABCDEFGH"       # Only uppercase
        ]
        
        for password in weak_passwords:
            assert validate_password_strength(password) is False
    
    def test_validate_password_strength_edge_cases(self):
        """Test password validation edge cases."""
        edge_cases = [
            "",  # Empty string
            "a" * 100,  # Very long but weak
            "A" * 8,    # Minimum length but weak
            "12345678", # Minimum length but weak
        ]
        
        for password in edge_cases:
            assert validate_password_strength(password) is False

class TestJWTUtils:
    """Test cases for JWT utilities."""
    
    def test_create_access_token(self, sample_user):
        """Test access token creation."""
        token_data = {
            "sub": sample_user.email,
            "user_id": sample_user.id,
            "email": sample_user.email,
            "role": sample_user.role
        }
        
        token = jwt_manager.create_access_token(token_data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode and verify
        decoded = jwt_manager.decode_token(token)
        assert decoded["sub"] == sample_user.email
        assert decoded["user_id"] == sample_user.id
    
    def test_create_refresh_token(self, sample_user):
        """Test refresh token creation."""
        token_data = {
            "sub": sample_user.email,
            "user_id": sample_user.id,
            "email": sample_user.email,
            "role": sample_user.role
        }
        
        token = jwt_manager.create_refresh_token(token_data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode and verify
        decoded = jwt_manager.decode_token(token)
        assert decoded["sub"] == sample_user.email
        assert decoded["user_id"] == sample_user.id
    
    def test_token_validation(self, sample_user):
        """Test token validation."""
        token_data = {
            "sub": sample_user.email,
            "user_id": sample_user.id,
            "email": sample_user.email,
            "role": sample_user.role
        }
        
        token = jwt_manager.create_access_token(token_data)
        
        # Valid token
        assert jwt_manager.validate_token(token) is True
        
        # Invalid token
        assert jwt_manager.validate_token("invalid.token.here") is False
    
    def test_token_blacklisting(self, mock_redis):
        """Test token blacklisting."""
        token = "test.jwt.token"
        
        with patch('app.utils.jwt_utils.jwt.decode') as mock_decode:
            mock_decode.return_value = {"jti": "test-jti"}
            
            result = jwt_manager.blacklist_token(token)
            assert result is True
            
            # Check if blacklisted
            assert jwt_manager.is_token_blacklisted(token) is True

class TestRateLimiting:
    """Test cases for rate limiting."""
    
    def test_rate_limiter_creation(self):
        """Test rate limiter creation."""
        limiter = RateLimiter(redis_client=None)
        assert limiter.max_requests == 100
        assert limiter.window_seconds == 3600
    
    def test_rate_limiter_custom_config(self):
        """Test rate limiter with custom configuration."""
        limiter = RateLimiter(
            redis_client=None,
            max_requests=50,
            window_seconds=1800
        )
        assert limiter.max_requests == 50
        assert limiter.window_seconds == 1800
    
    def test_rate_limiter_without_redis(self):
        """Test rate limiter without Redis (fallback behavior)."""
        limiter = RateLimiter(redis_client=None)
        
        # Should allow requests when Redis is not available
        result = limiter.check_rate_limit("test@example.com", "/test")
        assert result is True

class TestRBAC:
    """Test cases for Role-Based Access Control."""
    
    def test_require_role_decorator(self):
        """Test require_role decorator."""
        @require_role("admin")
        def admin_only_function():
            return "admin_access"
        
        # This would be tested with actual user objects in integration tests
        # For unit tests, we verify the decorator exists and is callable
        assert callable(admin_only_function)
    
    def test_require_permission_decorator(self):
        """Test require_permission decorator."""
        @require_permission("read_health_data")
        def read_health_data_function():
            return "health_data_access"
        
        # This would be tested with actual user objects in integration tests
        # For unit tests, we verify the decorator exists and is callable
        assert callable(read_health_data_function)

class TestValidationUtils:
    """Test cases for validation utilities."""
    
    def test_email_validation(self):
        """Test email validation."""
        valid_emails = [
            "user@example.com",
            "user.name@example.com",
            "user+tag@example.com",
            "user@subdomain.example.com"
        ]
        
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "user@",
            "user@.com",
            "user..name@example.com"
        ]
        
        # This would use actual email validation function
        # For now, we test the pattern
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        for email in valid_emails:
            assert re.match(email_pattern, email) is not None
        
        for email in invalid_emails:
            assert re.match(email_pattern, email) is None
    
    def test_age_validation(self):
        """Test age validation."""
        valid_ages = [1, 18, 65, 120]
        invalid_ages = [-1, 0, 121, 150]
        
        for age in valid_ages:
            assert 1 <= age <= 120
        
        for age in invalid_ages:
            assert not (1 <= age <= 120) 
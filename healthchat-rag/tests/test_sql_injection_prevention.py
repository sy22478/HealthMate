"""
Tests for SQL Injection Prevention Utilities
"""
import pytest
from fastapi import HTTPException
from app.utils.sql_injection_utils import SQLInjectionPrevention, sql_injection_prevention

class TestSQLInjectionPrevention:
    """Test SQL injection prevention functionality"""
    
    def test_safe_input_sanitization(self):
        """Test that safe input passes sanitization"""
        safe_inputs = [
            ("john.doe@example.com", "email"),
            ("John Doe", "name"),
            ("+1-555-123-4567", "phone"),
            ("123", "numeric"),
            ("Hello World", "text"),
            ("user123", "alphanumeric")
        ]
        
        for value, input_type in safe_inputs:
            result = sql_injection_prevention.sanitize_input(value, input_type)
            assert result == value
    
    def test_dangerous_pattern_detection(self):
        """Test detection of dangerous SQL patterns"""
        # Test a single dangerous input first
        dangerous_input = "'; DROP TABLE users; --"
        
        try:
            result = sql_injection_prevention.sanitize_input(dangerous_input, "text")
            assert False, f"Expected exception but got result: {result}"
        except HTTPException as exc_info:
            assert exc_info.status_code == 400
            assert "dangerous content" in exc_info.detail
        
        # Test a few more patterns
        dangerous_inputs = [
            "1' OR '1'='1",
            "admin'--",
            "1; SELECT * FROM users",
        ]
        
        for dangerous_input in dangerous_inputs:
            try:
                result = sql_injection_prevention.sanitize_input(dangerous_input, "text")
                assert False, f"Expected exception but got result: {result}"
            except HTTPException as exc_info:
                assert exc_info.status_code == 400
                # Check for either dangerous content or invalid format
                assert any(msg in exc_info.value.detail for msg in ["dangerous content", "Invalid text format"])
    
    def test_input_length_validation(self):
        """Test input length validation"""
        long_input = "a" * 1001
        
        with pytest.raises(HTTPException) as exc_info:
            sql_injection_prevention.sanitize_input(long_input, "text", max_length=1000)
        assert exc_info.value.status_code == 400
        assert "too long" in exc_info.value.detail
    
    def test_email_validation(self):
        """Test email format validation"""
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "user@",
            "user@.com",
            "user@example"
        ]
        
        for invalid_email in invalid_emails:
            try:
                result = sql_injection_prevention.sanitize_input(invalid_email, "email")
                assert False, f"Expected exception but got result: {result}"
            except HTTPException as exc_info:
                assert exc_info.status_code == 400
                assert "email format" in exc_info.detail
    
    def test_name_validation(self):
        """Test name format validation"""
        invalid_names = [
            "John123",
            "John@Doe",
            "John_Doe",
            "John;Doe",
            "John'Doe"
        ]
        
        for invalid_name in invalid_names:
            with pytest.raises(HTTPException) as exc_info:
                sql_injection_prevention.sanitize_input(invalid_name, "name")
            assert exc_info.value.status_code == 400
            assert "name format" in exc_info.value.detail
    
    def test_phone_validation(self):
        """Test phone format validation"""
        invalid_phones = [
            "abc-def-ghij",
            "123-456-789a",
            "123@456-7890",
            "123;456-7890"
        ]
        
        for invalid_phone in invalid_phones:
            with pytest.raises(HTTPException) as exc_info:
                sql_injection_prevention.sanitize_input(invalid_phone, "phone")
            assert exc_info.value.status_code == 400
            assert "phone format" in exc_info.value.detail
    
    def test_dict_sanitization(self):
        """Test dictionary sanitization"""
        test_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+1-555-123-4567",
            "age": "30"
        }
        
        field_types = {
            "name": "name",
            "email": "email",
            "phone": "phone",
            "age": "numeric"
        }
        
        result = sql_injection_prevention.sanitize_dict(test_data, field_types)
        assert result == test_data
    
    def test_sql_parameter_validation(self):
        """Test SQL parameter validation"""
        safe_params = {
            "user_id": 123,
            "name": "John Doe",
            "email": "john@example.com",
            "is_active": True,
            "score": 95.5
        }
        
        result = sql_injection_prevention.validate_sql_parameters(safe_params)
        assert result == safe_params
    
    def test_safe_raw_query(self):
        """Test safe raw query validation"""
        safe_query = "SELECT * FROM users WHERE id = :user_id"
        params = {"user_id": 123}
        
        result = sql_injection_prevention.safe_raw_query(safe_query, params)
        assert result == safe_query
    
    def test_dangerous_query_detection(self):
        """Test detection of dangerous queries"""
        dangerous_queries = [
            "SELECT * FROM users; DROP TABLE users",
            "SELECT * FROM users UNION SELECT * FROM passwords",
            "SELECT * FROM users--",
            "SELECT * FROM users/*",
            "SELECT * FROM users WHERE id = 1 OR 1=1"
        ]
        
        for dangerous_query in dangerous_queries:
            try:
                result = sql_injection_prevention.safe_raw_query(dangerous_query)
                assert False, f"Expected exception but got result: {result}"
            except HTTPException as exc_info:
                assert exc_info.status_code == 400
                assert "dangerous content" in exc_info.detail
    
    def test_none_input_handling(self):
        """Test handling of None input"""
        result = sql_injection_prevention.sanitize_input(None, "text")
        assert result == ""
    
    def test_empty_string_handling(self):
        """Test handling of empty strings"""
        result = sql_injection_prevention.sanitize_input("", "text")
        assert result == ""
    
    def test_whitespace_handling(self):
        """Test handling of whitespace"""
        result = sql_injection_prevention.sanitize_input("  hello world  ", "text")
        assert result == "hello world" 
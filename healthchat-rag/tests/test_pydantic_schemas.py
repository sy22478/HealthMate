"""
Tests for Pydantic Schemas
Comprehensive tests for all Pydantic schemas
"""
import pytest
from datetime import datetime, date
from pydantic import ValidationError
from app.schemas.auth_schemas import (
    UserRegister, UserLogin, TokenResponse, UserResponse, 
    PasswordChange, PasswordReset, UserProfile, UserRoleEnum
)
from app.schemas.health_schemas import (
    HealthDataCreate, HealthDataUpdate, HealthDataResponse,
    HealthMetrics, SymptomLog, MedicationLog, HealthGoal,
    HealthAlert, BloodType, SeverityLevel
)
from app.schemas.chat_schemas import (
    ChatMessageCreate, ChatMessageResponse, ChatSessionCreate,
    ChatSessionResponse, ChatHistoryResponse, ChatSearchQuery,
    ChatAnalytics, MessageFeedback, ConversationSummary,
    MessageType, MessageStatus
)
from app.schemas.common_schemas import (
    ErrorResponse, SuccessResponse, PaginatedResponse,
    HealthStatus, SearchQuery, BulkOperation, ExportRequest,
    ErrorCode
)

class TestAuthSchemas:
    """Test authentication schemas"""
    
    def test_user_register_valid(self):
        """Test valid user registration"""
        data = {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "full_name": "John Doe",
            "age": 30,
            "role": "patient"
        }
        user = UserRegister(**data)
        assert user.email == "test@example.com"
        assert user.password == "SecurePass123!"
        assert user.full_name == "John Doe"
        assert user.age == 30
        assert user.role == UserRoleEnum.PATIENT
    
    def test_user_register_invalid_password(self):
        """Test invalid password validation"""
        data = {
            "email": "test@example.com",
            "password": "weak",
            "full_name": "John Doe"
        }
        with pytest.raises(ValidationError) as exc_info:
            UserRegister(**data)
        assert "Password must be at least 8 characters long" in str(exc_info.value)
    
    def test_user_register_invalid_email(self):
        """Test invalid email validation"""
        data = {
            "email": "invalid-email",
            "password": "SecurePass123!",
            "full_name": "John Doe"
        }
        with pytest.raises(ValidationError) as exc_info:
            UserRegister(**data)
        assert "value is not a valid email address" in str(exc_info.value)
    
    def test_user_register_invalid_name(self):
        """Test invalid name validation"""
        data = {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "full_name": "John"  # Only one name
        }
        with pytest.raises(ValidationError) as exc_info:
            UserRegister(**data)
        assert "Full name must contain at least first and last name" in str(exc_info.value)
    
    def test_user_login_valid(self):
        """Test valid user login"""
        data = {
            "email": "test@example.com",
            "password": "SecurePass123!"
        }
        login = UserLogin(**data)
        assert login.email == "test@example.com"
        assert login.password == "SecurePass123!"
    
    def test_password_change_valid(self):
        """Test valid password change"""
        data = {
            "current_password": "OldPass123!",
            "new_password": "NewSecurePass456!",
            "confirm_password": "NewSecurePass456!"
        }
        change = PasswordChange(**data)
        assert change.current_password == "OldPass123!"
        assert change.new_password == "NewSecurePass456!"
        assert change.confirm_password == "NewSecurePass456!"
    
    def test_password_change_mismatch(self):
        """Test password confirmation mismatch"""
        data = {
            "current_password": "OldPass123!",
            "new_password": "NewSecurePass456!",
            "confirm_password": "DifferentPass789!"
        }
        with pytest.raises(ValidationError) as exc_info:
            PasswordChange(**data)
        assert "Password confirmation does not match" in str(exc_info.value)

class TestHealthSchemas:
    """Test health data schemas"""
    
    def test_health_data_create_valid(self):
        """Test valid health data creation"""
        data = {
            "user_id": 123,
            "data_type": "blood_pressure",
            "value": {"systolic": 120, "diastolic": 80},
            "unit": "mmHg",
            "notes": "Taken after exercise"
        }
        health_data = HealthDataCreate(**data)
        assert health_data.user_id == 123
        assert health_data.data_type == "blood_pressure"
        assert health_data.value == {"systolic": 120, "diastolic": 80}
        assert health_data.unit == "mmHg"
    
    def test_health_data_create_invalid_type(self):
        """Test invalid data type"""
        data = {
            "user_id": 123,
            "data_type": "invalid_type",
            "value": 120
        }
        with pytest.raises(ValidationError) as exc_info:
            HealthDataCreate(**data)
        assert "Invalid data type" in str(exc_info.value)
    
    def test_health_data_create_invalid_blood_pressure(self):
        """Test invalid blood pressure values"""
        data = {
            "user_id": 123,
            "data_type": "blood_pressure",
            "value": {"systolic": 300, "diastolic": 200}  # Invalid values
        }
        with pytest.raises(ValidationError) as exc_info:
            HealthDataCreate(**data)
        assert "Blood pressure values out of valid range" in str(exc_info.value)
    
    def test_symptom_log_valid(self):
        """Test valid symptom log"""
        data = {
            "user_id": 123,
            "symptom": "Headache",
            "severity": "moderate",
            "description": "Dull pain in forehead",
            "pain_level": 5
        }
        symptom = SymptomLog(**data)
        assert symptom.user_id == 123
        assert symptom.symptom == "Headache"
        assert symptom.severity == SeverityLevel.MODERATE
        assert symptom.pain_level == 5
    
    def test_medication_log_valid(self):
        """Test valid medication log"""
        data = {
            "user_id": 123,
            "medication_name": "Aspirin",
            "dosage": "100mg",
            "frequency": "Once daily"
        }
        medication = MedicationLog(**data)
        assert medication.user_id == 123
        assert medication.medication_name == "Aspirin"
        assert medication.dosage == "100mg"
        assert medication.frequency == "Once daily"
    
    def test_health_goal_valid(self):
        """Test valid health goal"""
        data = {
            "user_id": 123,
            "goal_type": "weight_loss",
            "target_value": 65.0,
            "current_value": 70.0,
            "unit": "kg",
            "description": "Lose 5kg",
            "progress": 50.0
        }
        goal = HealthGoal(**data)
        assert goal.user_id == 123
        assert goal.goal_type == "weight_loss"
        assert goal.target_value == 65.0
        assert goal.progress == 50.0

class TestChatSchemas:
    """Test chat schemas"""
    
    def test_chat_message_create_valid(self):
        """Test valid chat message creation"""
        data = {
            "user_id": 123,
            "session_id": 456,
            "message_type": "user",
            "content": "Hello, I have a question about my health"
        }
        message = ChatMessageCreate(**data)
        assert message.user_id == 123
        assert message.session_id == 456
        assert message.message_type == MessageType.USER
        assert message.content == "Hello, I have a question about my health"
    
    def test_chat_message_create_invalid_content(self):
        """Test invalid message content"""
        data = {
            "user_id": 123,
            "content": ""  # Empty content
        }
        with pytest.raises(ValidationError) as exc_info:
            ChatMessageCreate(**data)
        assert "Message content cannot be empty" in str(exc_info.value)
    
    def test_chat_session_create_valid(self):
        """Test valid chat session creation"""
        data = {
            "user_id": 123,
            "title": "Health Consultation",
            "description": "General health questions",
            "category": "consultation",
            "tags": ["health", "consultation"]
        }
        session = ChatSessionCreate(**data)
        assert session.user_id == 123
        assert session.title == "Health Consultation"
        assert session.tags == ["health", "consultation"]
    
    def test_chat_session_create_too_many_tags(self):
        """Test too many tags validation"""
        data = {
            "user_id": 123,
            "tags": [f"tag{i}" for i in range(15)]  # More than 10 tags
        }
        with pytest.raises(ValidationError) as exc_info:
            ChatSessionCreate(**data)
        assert "Maximum 10 tags allowed" in str(exc_info.value)
    
    def test_message_feedback_valid(self):
        """Test valid message feedback"""
        data = {
            "message_id": 789,
            "user_id": 123,
            "rating": 5,
            "feedback_type": "helpful",
            "comment": "Very informative response"
        }
        feedback = MessageFeedback(**data)
        assert feedback.message_id == 789
        assert feedback.rating == 5
        assert feedback.feedback_type == "helpful"
    
    def test_message_feedback_invalid_rating(self):
        """Test invalid feedback rating"""
        data = {
            "message_id": 789,
            "user_id": 123,
            "rating": 6,  # Invalid rating (should be 1-5)
            "feedback_type": "helpful"
        }
        with pytest.raises(ValidationError) as exc_info:
            MessageFeedback(**data)
        assert "ensure this value is less than or equal to 5" in str(exc_info.value)

class TestCommonSchemas:
    """Test common schemas"""
    
    def test_error_response_valid(self):
        """Test valid error response"""
        data = {
            "code": "VALIDATION_ERROR",
            "message": "Invalid input data"
        }
        error = ErrorResponse(**data)
        assert error.error is True
        assert error.code == ErrorCode.VALIDATION_ERROR
        assert error.message == "Invalid input data"
    
    def test_success_response_valid(self):
        """Test valid success response"""
        data = {
            "message": "Operation completed successfully",
            "data": {"id": 123, "status": "created"}
        }
        success = SuccessResponse(**data)
        assert success.success is True
        assert success.message == "Operation completed successfully"
        assert success.data == {"id": 123, "status": "created"}
    
    def test_paginated_response_valid(self):
        """Test valid paginated response"""
        data = {
            "items": [{"id": 1}, {"id": 2}],
            "total": 100,
            "page": 1,
            "size": 10
        }
        paginated = PaginatedResponse(**data)
        assert len(paginated.items) == 2
        assert paginated.total == 100
        assert paginated.page == 1
        assert paginated.size == 10
        assert paginated.pages == 10
        assert paginated.has_next is True
        assert paginated.has_prev is False
    
    def test_search_query_valid(self):
        """Test valid search query"""
        data = {
            "query": "diabetes symptoms",
            "filters": {"category": "symptoms"},
            "sort_by": "created_at",
            "sort_order": "desc",
            "page": 1,
            "size": 20
        }
        search = SearchQuery(**data)
        assert search.query == "diabetes symptoms"
        assert search.filters == {"category": "symptoms"}
        assert search.sort_order == "desc"
    
    def test_search_query_invalid_sort_order(self):
        """Test invalid sort order"""
        data = {
            "query": "test",
            "sort_order": "invalid"  # Invalid sort order
        }
        with pytest.raises(ValidationError) as exc_info:
            SearchQuery(**data)
        assert "string does not match pattern" in str(exc_info.value)
    
    def test_bulk_operation_valid(self):
        """Test valid bulk operation"""
        data = {
            "operation": "create",
            "items": [{"name": "Item 1"}, {"name": "Item 2"}],
            "batch_size": 10
        }
        bulk = BulkOperation(**data)
        assert bulk.operation == "create"
        assert len(bulk.items) == 2
        assert bulk.batch_size == 10
    
    def test_bulk_operation_invalid_operation(self):
        """Test invalid operation type"""
        data = {
            "operation": "invalid",
            "items": [{"name": "Item 1"}]
        }
        with pytest.raises(ValidationError) as exc_info:
            BulkOperation(**data)
        assert "string does not match pattern" in str(exc_info.value)
    
    def test_export_request_valid(self):
        """Test valid export request"""
        data = {
            "format": "csv",
            "date_from": datetime(2024, 1, 1),
            "date_to": datetime(2024, 1, 31),
            "fields": ["id", "name", "created_at"]
        }
        export = ExportRequest(**data)
        assert export.format == "csv"
        assert export.fields == ["id", "name", "created_at"]
    
    def test_export_request_invalid_date_range(self):
        """Test invalid date range"""
        data = {
            "format": "csv",
            "date_from": datetime(2024, 1, 31),
            "date_to": datetime(2024, 1, 1)  # End before start
        }
        with pytest.raises(ValidationError) as exc_info:
            ExportRequest(**data)
        assert "End date must be after start date" in str(exc_info.value)

class TestSchemaValidation:
    """Test schema validation edge cases"""
    
    def test_optional_fields_handling(self):
        """Test handling of optional fields"""
        # Test with minimal required fields
        user_data = {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "full_name": "John Doe"
        }
        user = UserRegister(**user_data)
        assert user.email == "test@example.com"
        assert user.age is None
        assert user.role == UserRoleEnum.PATIENT  # Default value
    
    def test_enum_validation(self):
        """Test enum field validation"""
        # Test valid enum values
        assert UserRoleEnum.PATIENT == "patient"
        assert UserRoleEnum.DOCTOR == "doctor"
        assert UserRoleEnum.ADMIN == "admin"
        assert UserRoleEnum.RESEARCHER == "researcher"
        
        # Test invalid enum value
        with pytest.raises(ValueError):
            UserRoleEnum("invalid_role")
    
    def test_datetime_handling(self):
        """Test datetime field handling"""
        now = datetime.utcnow()
        data = {
            "user_id": 123,
            "data_type": "temperature",
            "value": 98.6,
            "timestamp": now
        }
        health_data = HealthDataCreate(**data)
        assert health_data.timestamp == now
    
    def test_nested_dict_validation(self):
        """Test nested dictionary validation"""
        data = {
            "user_id": 123,
            "data_type": "blood_pressure",
            "value": {"systolic": 120, "diastolic": 80},
            "context": {"location": "home", "activity": "resting"}
        }
        health_data = HealthDataCreate(**data)
        assert health_data.value["systolic"] == 120
        assert health_data.context["location"] == "home"
    
    def test_list_validation(self):
        """Test list field validation"""
        data = {
            "user_id": 123,
            "title": "Test Session",
            "tags": ["health", "consultation", "general"]
        }
        session = ChatSessionCreate(**data)
        assert len(session.tags) == 3
        assert "health" in session.tags
    
    def test_field_length_validation(self):
        """Test field length validation"""
        # Test content too long
        long_content = "x" * 6000  # Exceeds 5000 character limit
        data = {
            "user_id": 123,
            "content": long_content
        }
        with pytest.raises(ValidationError) as exc_info:
            ChatMessageCreate(**data)
        assert "ensure this value has at most 5000 characters" in str(exc_info.value)
    
    def test_numeric_range_validation(self):
        """Test numeric range validation"""
        # Test age out of range
        data = {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "full_name": "John Doe",
            "age": 200  # Invalid age
        }
        with pytest.raises(ValidationError) as exc_info:
            UserRegister(**data)
        assert "ensure this value is less than or equal to 150" in str(exc_info.value) 
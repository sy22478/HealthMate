"""
Unit tests for database models and operations.

This module tests the database models, CRUD operations, and data validation.
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.health_data import HealthData
from app.services.auth import AuthService

class TestUserModel:
    """Test cases for User model."""
    
    def test_create_user(self, db_session):
        """Test creating a new user."""
        user = User(
            email="test@example.com",
            hashed_password="hashed_password",
            full_name="Test User",
            age=30,
            medical_conditions="None",
            medications="None",
            role="patient"
        )
        
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.age == 30
        assert user.role == "patient"
        assert user.is_active is True
        assert user.created_at is not None
    
    def test_user_email_uniqueness(self, db_session, sample_user):
        """Test that user email must be unique."""
        duplicate_user = User(
            email=sample_user.email,  # Same email as sample_user
            hashed_password="hashed_password",
            full_name="Duplicate User",
            age=25,
            medical_conditions="None",
            medications="None",
            role="patient"
        )
        
        db_session.add(duplicate_user)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
        
        db_session.rollback()
    
    def test_user_role_validation(self, db_session):
        """Test user role validation."""
        valid_roles = ["patient", "doctor", "admin"]
        
        for role in valid_roles:
            user = User(
                email=f"test_{role}@example.com",
                hashed_password="hashed_password",
                full_name=f"Test {role.title()}",
                age=30,
                medical_conditions="None",
                medications="None",
                role=role
            )
            
            db_session.add(user)
            db_session.commit()
            db_session.refresh(user)
            
            assert user.role == role
    
    def test_user_age_validation(self, db_session):
        """Test user age validation."""
        # Valid ages
        valid_ages = [1, 18, 65, 120]
        
        for age in valid_ages:
            user = User(
                email=f"test_age_{age}@example.com",
                hashed_password="hashed_password",
                full_name=f"Test User {age}",
                age=age,
                medical_conditions="None",
                medications="None",
                role="patient"
            )
            
            db_session.add(user)
            db_session.commit()
            db_session.refresh(user)
            
            assert user.age == age
    
    def test_user_string_representation(self, sample_user):
        """Test user string representation."""
        assert str(sample_user) == f"User(id={sample_user.id}, email={sample_user.email})"
        assert repr(sample_user) == f"User(id={sample_user.id}, email={sample_user.email})"
    
    def test_user_relationships(self, db_session, sample_user):
        """Test user relationships with health data."""
        # Create health data for the user
        health_data = HealthData(
            user_id=sample_user.id,
            data_type="blood_pressure",
            value="120/80",
            unit="mmHg",
            timestamp="2024-01-01T10:00:00Z",
            notes="Normal reading"
        )
        
        db_session.add(health_data)
        db_session.commit()
        db_session.refresh(health_data)
        
        # Query user and check relationship
        user = db_session.query(User).filter(User.id == sample_user.id).first()
        assert len(user.health_data) == 1
        assert user.health_data[0].data_type == "blood_pressure"
    
    def test_user_deactivation(self, db_session, sample_user):
        """Test user account deactivation."""
        # Deactivate user
        sample_user.is_active = False
        db_session.commit()
        db_session.refresh(sample_user)
        
        assert sample_user.is_active is False
    
    def test_user_password_update(self, db_session, sample_user):
        """Test user password update."""
        new_password_hash = AuthService().get_password_hash("NewPassword123!")
        sample_user.hashed_password = new_password_hash
        db_session.commit()
        db_session.refresh(sample_user)
        
        # Verify password was updated
        auth_service = AuthService()
        assert auth_service.verify_password("NewPassword123!", sample_user.hashed_password)
        assert not auth_service.verify_password("TestPassword123!", sample_user.hashed_password)

class TestHealthDataModel:
    """Test cases for HealthData model."""
    
    def test_create_health_data(self, db_session, sample_user):
        """Test creating new health data."""
        health_data = HealthData(
            user_id=sample_user.id,
            data_type="blood_pressure",
            value="120/80",
            unit="mmHg",
            timestamp="2024-01-01T10:00:00Z",
            notes="Normal reading"
        )
        
        db_session.add(health_data)
        db_session.commit()
        db_session.refresh(health_data)
        
        assert health_data.id is not None
        assert health_data.user_id == sample_user.id
        assert health_data.data_type == "blood_pressure"
        assert health_data.value == "120/80"
        assert health_data.unit == "mmHg"
        assert health_data.notes == "Normal reading"
        assert health_data.created_at is not None
    
    def test_health_data_types(self, db_session, sample_user):
        """Test different health data types."""
        data_types = [
            "blood_pressure",
            "weight",
            "height",
            "temperature",
            "heart_rate",
            "blood_sugar",
            "cholesterol",
            "bmi"
        ]
        
        for data_type in data_types:
            health_data = HealthData(
                user_id=sample_user.id,
                data_type=data_type,
                value="100",
                unit="test_unit",
                timestamp="2024-01-01T10:00:00Z",
                notes=f"Test {data_type}"
            )
            
            db_session.add(health_data)
            db_session.commit()
            db_session.refresh(health_data)
            
            assert health_data.data_type == data_type
    
    def test_health_data_foreign_key_constraint(self, db_session):
        """Test foreign key constraint for health data."""
        health_data = HealthData(
            user_id=99999,  # Non-existent user ID
            data_type="blood_pressure",
            value="120/80",
            unit="mmHg",
            timestamp="2024-01-01T10:00:00Z",
            notes="Test"
        )
        
        db_session.add(health_data)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
        
        db_session.rollback()
    
    def test_health_data_string_representation(self, sample_health_record):
        """Test health data string representation."""
        expected = f"HealthData(id={sample_health_record.id}, user_id={sample_health_record.user_id}, type={sample_health_record.data_type})"
        assert str(sample_health_record) == expected
        assert repr(sample_health_record) == expected
    
    def test_health_data_relationships(self, db_session, sample_user):
        """Test health data relationships with user."""
        # Create multiple health data records
        health_records = []
        for i in range(3):
            health_data = HealthData(
                user_id=sample_user.id,
                data_type=f"test_type_{i}",
                value=f"value_{i}",
                unit="test_unit",
                timestamp="2024-01-01T10:00:00Z",
                notes=f"Test record {i}"
            )
            health_records.append(health_data)
            db_session.add(health_data)
        
        db_session.commit()
        
        # Query user and check relationship
        user = db_session.query(User).filter(User.id == sample_user.id).first()
        assert len(user.health_data) == 3
        
        # Check that all records belong to the user
        for record in user.health_data:
            assert record.user_id == sample_user.id
    
    def test_health_data_update(self, db_session, sample_health_record):
        """Test updating health data."""
        # Update health data
        sample_health_record.value = "130/85"
        sample_health_record.notes = "Updated reading"
        db_session.commit()
        db_session.refresh(sample_health_record)
        
        assert sample_health_record.value == "130/85"
        assert sample_health_record.notes == "Updated reading"
    
    def test_health_data_deletion(self, db_session, sample_health_record):
        """Test deleting health data."""
        record_id = sample_health_record.id
        
        # Delete the record
        db_session.delete(sample_health_record)
        db_session.commit()
        
        # Verify it's deleted
        deleted_record = db_session.query(HealthData).filter(HealthData.id == record_id).first()
        assert deleted_record is None

class TestDatabaseOperations:
    """Test cases for database operations."""
    
    def test_user_query_operations(self, db_session, sample_user):
        """Test user query operations."""
        # Query by email
        user = db_session.query(User).filter(User.email == sample_user.email).first()
        assert user is not None
        assert user.id == sample_user.id
        
        # Query by role
        users = db_session.query(User).filter(User.role == "patient").all()
        assert len(users) >= 1
        assert all(user.role == "patient" for user in users)
        
        # Query active users
        active_users = db_session.query(User).filter(User.is_active == True).all()
        assert len(active_users) >= 1
        assert all(user.is_active for user in active_users)
    
    def test_health_data_query_operations(self, db_session, sample_user, sample_health_record):
        """Test health data query operations."""
        # Query by user
        user_health_data = db_session.query(HealthData).filter(HealthData.user_id == sample_user.id).all()
        assert len(user_health_data) >= 1
        assert all(data.user_id == sample_user.id for data in user_health_data)
        
        # Query by data type
        blood_pressure_data = db_session.query(HealthData).filter(HealthData.data_type == "blood_pressure").all()
        assert len(blood_pressure_data) >= 1
        assert all(data.data_type == "blood_pressure" for data in blood_pressure_data)
        
        # Query with date range
        from_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        recent_data = db_session.query(HealthData).filter(HealthData.created_at >= from_date).all()
        assert len(recent_data) >= 1
    
    def test_join_operations(self, db_session, sample_user, sample_health_record):
        """Test join operations between users and health data."""
        # Join query to get user with health data
        result = db_session.query(User, HealthData).join(HealthData).filter(User.id == sample_user.id).all()
        assert len(result) >= 1
        
        for user, health_data in result:
            assert user.id == sample_user.id
            assert health_data.user_id == sample_user.id
    
    def test_aggregation_operations(self, db_session, sample_user):
        """Test aggregation operations on health data."""
        # Create multiple health data records for aggregation
        for i in range(5):
            health_data = HealthData(
                user_id=sample_user.id,
                data_type="weight",
                value=str(70 + i),  # 70, 71, 72, 73, 74
                unit="kg",
                timestamp="2024-01-01T10:00:00Z",
                notes=f"Weight reading {i}"
            )
            db_session.add(health_data)
        
        db_session.commit()
        
        # Count records
        count = db_session.query(HealthData).filter(HealthData.user_id == sample_user.id).count()
        assert count >= 5
        
        # Count by data type
        weight_count = db_session.query(HealthData).filter(
            HealthData.user_id == sample_user.id,
            HealthData.data_type == "weight"
        ).count()
        assert weight_count >= 5
    
    def test_transaction_rollback(self, db_session, sample_user):
        """Test transaction rollback on error."""
        initial_count = db_session.query(User).count()
        
        # Try to create a user with duplicate email (should fail)
        duplicate_user = User(
            email=sample_user.email,  # Duplicate email
            hashed_password="hashed_password",
            full_name="Duplicate User",
            age=25,
            medical_conditions="None",
            medications="None",
            role="patient"
        )
        
        db_session.add(duplicate_user)
        
        try:
            db_session.commit()
        except IntegrityError:
            db_session.rollback()
        
        # Verify no new user was added
        final_count = db_session.query(User).count()
        assert final_count == initial_count 
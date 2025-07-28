"""
Enhanced Authentication System Tests
Tests for JWT management, RBAC, and password security features
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import get_db, Base
from app.main import app
from app.utils.jwt_utils import JWTManager
from app.utils.password_utils import PasswordManager, PasswordValidator
from app.utils.rbac import UserRole, Permission, RolePermissions, RBACMiddleware
from app.models.user import User
import jwt
from datetime import datetime, timedelta

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    """Setup test database before each test"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

class TestPasswordSecurity:
    """Test password security features"""
    
    def test_password_validation(self):
        """Test password strength validation"""
        validator = PasswordValidator()
        
        # Test valid password
        is_valid, errors = validator.validate_password("SecurePass123!")
        assert is_valid
        assert len(errors) == 0
        
        # Test weak password
        is_valid, errors = validator.validate_password("weak")
        assert not is_valid
        assert len(errors) > 0
        
        # Test common password
        is_valid, errors = validator.validate_password("password")
        assert not is_valid
        assert any("common" in error.lower() for error in errors)
    
    def test_password_strength_analysis(self):
        """Test password strength analysis"""
        validator = PasswordValidator()
        analysis = validator.get_password_strength("SecurePass123!")
        
        assert analysis["is_valid"] is True
        assert analysis["strength"] in ["strong", "very_strong"]
        assert analysis["has_uppercase"] is True
        assert analysis["has_lowercase"] is True
        assert analysis["has_digits"] is True
        assert analysis["has_special_chars"] is True
    
    def test_password_hashing(self):
        """Test password hashing and verification"""
        manager = PasswordManager()
        password = "SecurePass123!"
        
        # Hash password
        hashed = manager.hash_password(password)
        assert hashed != password
        assert hashed.startswith("$2b$")
        
        # Verify password
        assert manager.verify_password(password, hashed) is True
        assert manager.verify_password("wrongpassword", hashed) is False
    
    def test_secure_password_generation(self):
        """Test secure password generation"""
        manager = PasswordManager()
        password = manager.generate_secure_password(16)
        
        # Validate generated password
        is_valid, errors = manager.validator.validate_password(password)
        assert is_valid
        assert len(password) == 16

class TestJWTManagement:
    """Test JWT token management"""
    
    def test_token_creation(self):
        """Test JWT token creation"""
        jwt_manager = JWTManager("test_secret_key")
        data = {"user_id": 1, "email": "test@example.com"}
        
        # Create access token
        access_token = jwt_manager.create_access_token(data)
        assert access_token is not None
        
        # Create refresh token
        refresh_token = jwt_manager.create_refresh_token(data)
        assert refresh_token is not None
        
        # Verify tokens are different
        assert access_token != refresh_token
    
    def test_token_verification(self):
        """Test JWT token verification"""
        jwt_manager = JWTManager("test_secret_key")
        data = {"user_id": 1, "email": "test@example.com"}
        
        # Create and verify access token
        access_token = jwt_manager.create_access_token(data)
        payload = jwt_manager.verify_token(access_token, "access")
        
        assert payload["user_id"] == 1
        assert payload["email"] == "test@example.com"
        assert payload["type"] == "access"
    
    def test_token_refresh(self):
        """Test token refresh functionality"""
        jwt_manager = JWTManager("test_secret_key")
        data = {"user_id": 1, "email": "test@example.com"}
        
        # Create refresh token
        refresh_token = jwt_manager.create_refresh_token(data)
        
        # Refresh access token
        result = jwt_manager.refresh_access_token(refresh_token)
        
        assert "access_token" in result
        assert "refresh_token" in result
        assert result["token_type"] == "bearer"
        
        # Verify new access token
        new_payload = jwt_manager.verify_token(result["access_token"], "access")
        assert new_payload["user_id"] == 1
    
    def test_expired_token(self):
        """Test expired token handling"""
        jwt_manager = JWTManager("test_secret_key")
        data = {"user_id": 1, "email": "test@example.com"}
        
        # Create token with short expiration
        token = jwt_manager.create_access_token(data, timedelta(seconds=1))
        
        # Wait for expiration
        import time
        time.sleep(2)
        
        # Verify token is expired
        with pytest.raises(Exception):
            jwt_manager.verify_token(token, "access")

class TestRBAC:
    """Test Role-Based Access Control"""
    
    def test_role_permissions(self):
        """Test role permission mapping"""
        # Test patient permissions
        patient_perms = RolePermissions.get_permissions_for_role(UserRole.PATIENT)
        assert Permission.READ_OWN_PROFILE in patient_perms
        assert Permission.MANAGE_USERS not in patient_perms
        
        # Test admin permissions
        admin_perms = RolePermissions.get_permissions_for_role(UserRole.ADMIN)
        assert Permission.MANAGE_USERS in admin_perms
        assert Permission.VIEW_ANALYTICS in admin_perms
    
    def test_permission_checking(self):
        """Test permission checking"""
        # Test valid permission
        assert RolePermissions.has_permission(UserRole.DOCTOR, Permission.READ_PATIENT_DATA)
        
        # Test invalid permission
        assert not RolePermissions.has_permission(UserRole.PATIENT, Permission.MANAGE_USERS)
    
    def test_user_permission_checking(self):
        """Test user permission checking"""
        # Create test user
        user = User(
            email="test@example.com",
            role="doctor",
            hashed_password="hashed",
            full_name="Test User",
            age=30
        )
        
        # Test user permissions
        assert RBACMiddleware.has_permission(user, Permission.READ_PATIENT_DATA)
        assert not RBACMiddleware.has_permission(user, Permission.MANAGE_USERS)
        
        # Test invalid role
        user.role = "invalid_role"
        assert not RBACMiddleware.has_permission(user, Permission.READ_OWN_PROFILE)

class TestAuthenticationEndpoints:
    """Test authentication API endpoints"""
    
    def test_user_registration(self):
        """Test user registration with validation"""
        user_data = {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "full_name": "Test User",
            "age": 30,
            "role": "patient"
        }
        
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "User registered successfully"
        assert data["email"] == "test@example.com"
        assert data["role"] == "patient"
    
    def test_user_registration_weak_password(self):
        """Test user registration with weak password"""
        user_data = {
            "email": "test@example.com",
            "password": "weak",
            "full_name": "Test User",
            "age": 30
        }
        
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 422  # Validation error
    
    def test_user_login(self):
        """Test user login with tokens"""
        # Register user first
        user_data = {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "full_name": "Test User",
            "age": 30
        }
        client.post("/auth/register", json=user_data)
        
        # Login
        login_data = {
            "email": "test@example.com",
            "password": "SecurePass123!"
        }
        
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == "test@example.com"
    
    def test_token_refresh_endpoint(self):
        """Test token refresh endpoint"""
        # Register and login user
        user_data = {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "full_name": "Test User",
            "age": 30
        }
        client.post("/auth/register", json=user_data)
        
        login_data = {
            "email": "test@example.com",
            "password": "SecurePass123!"
        }
        login_response = client.post("/auth/login", json=login_data)
        refresh_token = login_response.json()["refresh_token"]
        
        # Refresh token
        refresh_data = {"refresh_token": refresh_token}
        response = client.post("/auth/refresh", json=refresh_data)
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert "refresh_token" in data
    
    def test_protected_endpoint(self):
        """Test protected endpoint access"""
        # Register and login user
        user_data = {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "full_name": "Test User",
            "age": 30
        }
        client.post("/auth/register", json=user_data)
        
        login_data = {
            "email": "test@example.com",
            "password": "SecurePass123!"
        }
        login_response = client.post("/auth/login", json=login_data)
        access_token = login_response.json()["access_token"]
        
        # Access protected endpoint
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
    
    def test_invalid_token_access(self):
        """Test access with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 401
    
    def test_password_change(self):
        """Test password change functionality"""
        # Register and login user
        user_data = {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "full_name": "Test User",
            "age": 30
        }
        client.post("/auth/register", json=user_data)
        
        login_data = {
            "email": "test@example.com",
            "password": "SecurePass123!"
        }
        login_response = client.post("/auth/login", json=login_data)
        access_token = login_response.json()["access_token"]
        
        # Change password
        headers = {"Authorization": f"Bearer {access_token}"}
        change_data = {
            "current_password": "SecurePass123!",
            "new_password": "NewSecurePass456!"
        }
        response = client.post("/auth/change-password", json=change_data, headers=headers)
        assert response.status_code == 200
        
        # Verify new password works
        new_login_data = {
            "email": "test@example.com",
            "password": "NewSecurePass456!"
        }
        response = client.post("/auth/login", json=new_login_data)
        assert response.status_code == 200

if __name__ == "__main__":
    pytest.main([__file__]) 
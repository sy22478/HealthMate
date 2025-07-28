# Enhanced Authentication System Documentation

## Overview

The HealthMate application now features a comprehensive authentication system with advanced security features including JWT token management, Role-Based Access Control (RBAC), and robust password security.

## Features

### 1. JWT Token Management

#### Token Types
- **Access Tokens**: Short-lived tokens (30 minutes) for API access
- **Refresh Tokens**: Long-lived tokens (7 days) for token renewal
- **Token Blacklisting**: Secure token revocation using Redis

#### Key Features
- Automatic token expiration handling
- Token refresh mechanism
- Token blacklisting for secure logout
- JWT ID (JTI) for unique token identification
- Token type validation

#### Usage Example
```python
from app.utils.jwt_utils import jwt_manager

# Create access token
access_token = jwt_manager.create_access_token({
    "user_id": user.id,
    "email": user.email,
    "role": user.role
})

# Create refresh token
refresh_token = jwt_manager.create_refresh_token({
    "user_id": user.id,
    "email": user.email
})

# Verify token
payload = jwt_manager.verify_token(token, "access")

# Refresh access token
new_tokens = jwt_manager.refresh_access_token(refresh_token)

# Blacklist token
jwt_manager.blacklist_token(token)
```

### 2. Role-Based Access Control (RBAC)

#### User Roles
- **Patient**: Basic user with access to own data
- **Doctor**: Healthcare provider with patient data access
- **Admin**: System administrator with full access
- **Researcher**: Research access to anonymized data

#### Permissions
Each role has specific permissions:

**Patient Permissions:**
- Read/update own profile
- Manage own health data
- Send messages and view conversations
- Delete own account

**Doctor Permissions:**
- All patient permissions
- Read/update patient data
- Create treatment plans
- View all conversations

**Admin Permissions:**
- All doctor permissions
- Manage users and system
- View analytics
- Manage roles

**Researcher Permissions:**
- Access anonymized data
- Conduct research
- Basic profile management

#### Usage Example
```python
from app.utils.rbac import require_permission, require_role, Permission, UserRole

# Require specific permission
@router.get("/patients")
@require_permission(Permission.READ_PATIENT_DATA)
def get_patients(current_user: User = Depends(get_current_user)):
    # Only users with READ_PATIENT_DATA permission can access
    pass

# Require specific role
@router.get("/admin/users")
@require_role(UserRole.ADMIN)
def get_all_users(current_user: User = Depends(get_current_user)):
    # Only admin users can access
    pass

# Check permissions programmatically
from app.utils.rbac import RBACMiddleware

if RBACMiddleware.has_permission(user, Permission.MANAGE_USERS):
    # User has permission to manage users
    pass
```

### 3. Password Security

#### Password Requirements
- Minimum 8 characters
- Maximum 128 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character
- Not a common password
- No repeated characters (3+)
- No sequential characters

#### Features
- Password strength analysis
- Secure password generation
- Bcrypt hashing with salt
- Password validation
- Reset token management

#### Usage Example
```python
from app.utils.password_utils import password_manager

# Validate and hash password
hashed_password, errors = password_manager.validate_and_hash_password(password)
if errors:
    # Handle validation errors
    pass

# Generate secure password
secure_password = password_manager.generate_secure_password(16)

# Check password strength
strength = password_manager.validator.get_password_strength(password)
print(f"Password strength: {strength['strength']}")

# Create reset token
reset_token = password_manager.create_password_reset_token()
```

## API Endpoints

### Authentication Endpoints

#### POST /auth/register
Register a new user with role assignment.

**Request Body:**
```json
{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "full_name": "John Doe",
    "age": 30,
    "medical_conditions": "",
    "medications": "",
    "role": "patient"
}
```

**Response:**
```json
{
    "message": "User registered successfully",
    "user_id": 1,
    "email": "user@example.com",
    "role": "patient"
}
```

#### POST /auth/login
Login user and receive access/refresh tokens.

**Request Body:**
```json
{
    "email": "user@example.com",
    "password": "SecurePass123!"
}
```

**Response:**
```json
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "user": {
        "id": 1,
        "email": "user@example.com",
        "full_name": "John Doe",
        "role": "patient"
    }
}
```

#### POST /auth/refresh
Refresh access token using refresh token.

**Request Body:**
```json
{
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response:**
```json
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer"
}
```

#### POST /auth/change-password
Change password for authenticated user.

**Request Body:**
```json
{
    "current_password": "OldPass123!",
    "new_password": "NewPass456!"
}
```

#### POST /auth/logout
Logout user by blacklisting token.

**Request Body:**
```json
{
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### GET /auth/me
Get current user information.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "age": 30,
    "role": "patient",
    "is_active": true,
    "created_at": "2024-01-01T12:00:00"
}
```

#### POST /auth/revoke-all-tokens
Revoke all tokens for current user.

**Headers:**
```
Authorization: Bearer <access_token>
```

## Security Features

### 1. Token Security
- JWT tokens with proper expiration
- Token blacklisting for secure logout
- Refresh token rotation
- Token type validation
- Unique JWT ID for each token

### 2. Password Security
- Strong password requirements
- Bcrypt hashing with salt
- Password strength analysis
- Common password detection
- Sequential character detection

### 3. Access Control
- Role-based permissions
- Granular permission system
- Permission decorators
- User role validation

### 4. Input Validation
- Pydantic schema validation
- Password strength validation
- Email format validation
- Age range validation
- Role validation

## Configuration

### Environment Variables
```bash
# JWT Configuration
SECRET_KEY=your-secret-key-here

# Redis Configuration (for token blacklisting)
REDIS_URL=redis://localhost:6379/0

# Database Configuration
POSTGRES_URI=postgresql://user:password@localhost/healthmate
```

### Database Migration
Run the following command to add the role field to the users table:
```bash
alembic upgrade head
```

## Testing

### Running Tests
```bash
# Run all authentication tests
pytest tests/test_enhanced_auth.py -v

# Run specific test class
pytest tests/test_enhanced_auth.py::TestPasswordSecurity -v

# Run specific test
pytest tests/test_enhanced_auth.py::TestPasswordSecurity::test_password_validation -v
```

### Test Coverage
The test suite covers:
- Password validation and strength analysis
- JWT token creation, verification, and refresh
- RBAC permission checking
- API endpoint functionality
- Error handling and edge cases

## Best Practices

### 1. Token Management
- Always use HTTPS in production
- Set appropriate token expiration times
- Implement token refresh before expiration
- Use token blacklisting for secure logout
- Validate token type for each endpoint

### 2. Password Security
- Enforce strong password requirements
- Use bcrypt for password hashing
- Implement password reset functionality
- Monitor for common password usage
- Provide password strength feedback

### 3. Access Control
- Use principle of least privilege
- Implement role-based permissions
- Validate permissions at endpoint level
- Log permission violations
- Regular permission audits

### 4. Security Monitoring
- Log authentication events
- Monitor failed login attempts
- Track token usage patterns
- Alert on suspicious activities
- Regular security assessments

## Troubleshooting

### Common Issues

#### 1. Token Expiration
**Problem:** Users getting 401 errors after 30 minutes
**Solution:** Implement automatic token refresh using refresh tokens

#### 2. Redis Connection Issues
**Problem:** Token blacklisting not working
**Solution:** Check Redis connection and fallback gracefully

#### 3. Permission Denied Errors
**Problem:** Users getting 403 errors
**Solution:** Verify user roles and permissions are correctly assigned

#### 4. Password Validation Failures
**Problem:** Users can't register with valid passwords
**Solution:** Check password requirements and provide clear error messages

### Debug Mode
Enable debug logging by setting the log level:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Migration Guide

### From Old Authentication System
1. Update database schema with new role field
2. Migrate existing users to have default 'patient' role
3. Update frontend to handle new token format
4. Implement token refresh logic
5. Update API calls to use new endpoints

### Database Changes
- Added `role` column to `users` table
- Default role is 'patient'
- Existing users will be assigned 'patient' role

### API Changes
- Login now returns both access and refresh tokens
- New endpoints for token refresh and password change
- Enhanced error responses with validation details
- Role-based access control on endpoints

## Future Enhancements

### Planned Features
1. **Multi-factor Authentication (MFA)**
   - SMS/email verification codes
   - TOTP support
   - Hardware token support

2. **Advanced Session Management**
   - Concurrent session limits
   - Device tracking
   - Geographic restrictions

3. **Enhanced Audit Logging**
   - Detailed activity logs
   - Compliance reporting
   - Real-time monitoring

4. **OAuth Integration**
   - Google OAuth
   - Apple Sign-In
   - Microsoft Azure AD

5. **API Rate Limiting**
   - Per-user rate limits
   - Endpoint-specific limits
   - DDoS protection 
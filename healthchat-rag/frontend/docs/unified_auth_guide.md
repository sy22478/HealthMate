# Unified Authentication System

## Overview

The HealthMate application now features a unified authentication system that provides a single, modern interface for user login, registration, and password reset functionality. This system replaces the previous embedded authentication forms with a dedicated authentication page.

## Features

### 1. Unified Authentication Page (`pages/unified_auth.py`)

- **Single Interface**: Combines login, registration, and forgot password functionality
- **Modern UI**: Clean, responsive design with proper styling
- **Password Strength Validation**: Real-time password strength checking
- **Error Handling**: Comprehensive error messages and validation
- **Accessibility**: Keyboard navigable and screen reader friendly

### 2. Authentication Modes

#### Login Mode
- Email and password authentication
- Remember me functionality
- Secure token-based authentication
- Automatic redirect to dashboard after successful login

#### Registration Mode
- Complete user profile creation
- Password strength validation
- Medical information collection (optional)
- Terms and conditions acceptance

#### Forgot Password Mode
- Email-based password reset
- Token-based password reset
- Secure password reset flow

### 3. Backend Integration

#### New Endpoints Added
- `POST /auth/forgot-password` - Request password reset
- `POST /auth/reset-password` - Reset password with token

#### Database Schema Updates
- Added `reset_token` field to users table
- Added `reset_token_expires` field to users table

## Usage

### For Users

1. **Access**: Navigate to the unified authentication page
2. **Login**: Use existing credentials to access the dashboard
3. **Register**: Create a new account with health information
4. **Password Reset**: Use email-based password reset if needed

### For Developers

#### Running the Application

1. Start the backend server:
   ```bash
   cd healthchat-rag
   uvicorn app.main:app --reload
   ```

2. Start the frontend:
   ```bash
   cd healthchat-rag/frontend
   streamlit run streamlit_app.py
   ```

3. Access the unified auth page:
   ```
   http://localhost:8501/pages/unified_auth
   ```

#### Testing

Run the authentication tests:
```bash
cd healthchat-rag
python -m pytest tests/test_unified_auth.py -v
```

## Security Features

### Password Security
- Password strength validation
- Secure password hashing (bcrypt)
- Password confirmation requirements

### Token Security
- JWT-based authentication tokens
- Secure token generation for password reset
- Token expiration (1 hour for reset tokens)

### Input Validation
- Email format validation
- Required field validation
- SQL injection prevention

## File Structure

```
healthchat-rag/
├── app/
│   ├── routers/
│   │   └── auth.py              # Updated with forgot password endpoints
│   └── models/
│       └── user.py              # Updated with reset token fields
├── frontend/
│   ├── pages/
│   │   ├── unified_auth.py      # New unified authentication page
│   │   ├── login.py             # Legacy (can be removed)
│   │   ├── register.py          # Legacy (can be removed)
│   │   └── forgot_password.py   # Legacy (can be removed)
│   └── streamlit_app.py         # Updated main dashboard
└── tests/
    └── test_unified_auth.py     # Authentication tests
```

## Migration Notes

### Database Migration
The new reset token fields require a database migration:

```bash
# Create migration (if alembic is working)
alembic revision --autogenerate -m "add_reset_token_fields_to_user"

# Apply migration
alembic upgrade head
```

### Legacy Files
The following files can be removed after confirming the unified auth system works:
- `frontend/pages/login.py`
- `frontend/pages/register.py`
- `frontend/pages/forgot_password.py`

## Future Enhancements

1. **Email Integration**: Implement actual email sending for password reset
2. **Two-Factor Authentication**: Add 2FA support
3. **Social Login**: Integrate with Google, Facebook, etc.
4. **Session Management**: Implement session timeout and renewal
5. **Audit Logging**: Track authentication events

## Troubleshooting

### Common Issues

1. **Database Connection**: Ensure the database is running and accessible
2. **Backend Server**: Make sure the FastAPI server is running on port 8000
3. **CORS Issues**: Check if CORS is properly configured for frontend-backend communication
4. **Token Issues**: Verify JWT secret key configuration

### Error Messages

- **"Connection error"**: Backend server is not running
- **"Invalid credentials"**: Wrong email/password combination
- **"Email already registered"**: User already exists during registration
- **"Invalid or expired reset token"**: Reset token is invalid or expired

## Contributing

When contributing to the authentication system:

1. Follow the existing code style and patterns
2. Add comprehensive tests for new features
3. Update documentation for any changes
4. Ensure accessibility compliance
5. Test with different browsers and devices 
# Enhanced JWT Token Management System Documentation

## Overview

The HealthMate application now features a comprehensive JWT (JSON Web Token) management system with advanced security features, token rotation, rate limiting, and enhanced monitoring capabilities.

## Features

### 🔐 **Enhanced Security Features**

#### 1. **Token Fingerprinting**
- Unique fingerprint generation for each token
- Based on user data and timestamp
- Prevents token replay attacks
- 16-character hexadecimal fingerprint

#### 2. **Standard JWT Claims**
- **iss** (Issuer): "healthmate"
- **aud** (Audience): "healthmate_users"
- **exp** (Expiration): Configurable expiration times
- **iat** (Issued At): Token creation timestamp
- **nbf** (Not Before): Token validity start time
- **jti** (JWT ID): Unique token identifier
- **type**: Token type ("access", "refresh", "reset")

#### 3. **Token Types**
- **Access Tokens**: Short-lived (30 minutes) for API access
- **Refresh Tokens**: Long-lived (7 days) for token renewal
- **Reset Tokens**: Short-lived (1 hour) for password reset

### 🔄 **Token Rotation & Refresh**

#### Automatic Token Rotation
- New refresh token issued with each refresh
- Old refresh tokens automatically blacklisted
- Prevents refresh token reuse attacks
- Maintains session security

#### Refresh Token Tracking
- Redis-based refresh token management
- Maximum 5 concurrent refresh tokens per user
- Automatic cleanup of old tokens
- Location-based tracking for security

### 🛡️ **Security Enhancements**

#### Rate Limiting
- 1000 requests per hour per IP address
- Separate limits for authentication endpoints
- Redis-based rate limiting with automatic expiration
- Graceful degradation when Redis unavailable

#### Suspicious Activity Detection
- Tracks authentication attempts per user/IP
- Alerts on unusual activity patterns
- Logs suspicious behavior for analysis
- Configurable thresholds

#### Token Blacklisting
- Redis-based token blacklisting
- Automatic expiration of blacklisted tokens
- User-wide token revocation
- Secure logout functionality

### 📊 **Monitoring & Analytics**

#### Token Statistics
- Blacklisted token count
- Active refresh token count
- Redis connection status
- Real-time monitoring capabilities

#### Authentication Analytics
- Active session count per user
- Suspicious activity tracking
- Refresh token location tracking
- User authentication patterns

## Implementation Details

### JWT Manager Class

```python
class JWTManager:
    """Comprehensive JWT token management system with enhanced security"""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7
        self.max_refresh_tokens_per_user = 5
```

### Key Methods

#### Token Creation
```python
def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create access token with enhanced security features"""

def create_refresh_token(self, data: Dict[str, Any]) -> str:
    """Create refresh token with tracking and rotation"""

def create_reset_token(self, user_id: int, email: str) -> str:
    """Create password reset token"""
```

#### Token Verification
```python
def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
    """Verify token with comprehensive security checks"""

def verify_reset_token(self, token: str) -> Dict[str, Any]:
    """Verify password reset token"""
```

#### Token Management
```python
def refresh_access_token(self, refresh_token: str) -> Dict[str, str]:
    """Refresh tokens with automatic rotation"""

def blacklist_token(self, token: str, expires_in: Optional[int] = None) -> bool:
    """Blacklist token for secure logout"""

def revoke_user_tokens(self, user_id: int) -> bool:
    """Revoke all tokens for a user"""
```

## API Endpoints

### Authentication Endpoints

#### Login
```http
POST /auth/login
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "secure_password"
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

#### Token Refresh
```http
POST /auth/refresh
Content-Type: application/json

{
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### Logout
```http
POST /auth/logout
Content-Type: application/json

{
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### Logout All Devices
```http
POST /auth/logout-all-devices
Authorization: Bearer <access_token>
```

### Management Endpoints

#### Token Statistics (Admin Only)
```http
GET /auth/token-stats
Authorization: Bearer <admin_access_token>
```

**Response:**
```json
{
    "blacklisted_tokens_count": 15,
    "active_refresh_tokens": 42,
    "redis_connected": true
}
```

#### Authentication Statistics
```http
GET /auth/auth-stats
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "active_sessions": 3,
    "recent_activity": [],
    "suspicious_activity": [],
    "refresh_locations": ["192.168.1.1", "10.0.0.1"]
}
```

#### Session Information
```http
GET /auth/session-info
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "user_id": 1,
    "email": "user@example.com",
    "role": "patient",
    "active_sessions": 3,
    "refresh_locations": ["192.168.1.1", "10.0.0.1"],
    "last_login": "2024-01-15T10:30:00Z"
}
```

#### Token Validation
```http
POST /auth/validate-token
Content-Type: application/json

{
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response:**
```json
{
    "valid": true,
    "user_id": 1,
    "email": "user@example.com",
    "role": "patient",
    "type": "access",
    "expires_at": 1642345678
}
```

## Security Best Practices

### 1. **Token Storage**
- Store tokens securely in memory (not localStorage)
- Use secure HTTP-only cookies for web applications
- Implement automatic token refresh
- Clear tokens on logout

### 2. **Token Validation**
- Always validate tokens on the server side
- Check token expiration and blacklist status
- Verify token type and audience
- Implement proper error handling

### 3. **Rate Limiting**
- Monitor authentication attempts
- Implement progressive delays for failed attempts
- Log suspicious activity patterns
- Use Redis for distributed rate limiting

### 4. **Token Rotation**
- Implement automatic refresh token rotation
- Blacklist old refresh tokens immediately
- Limit concurrent refresh tokens per user
- Track token usage patterns

## Configuration

### Environment Variables
```bash
# JWT Configuration
SECRET_KEY=your-secret-key-here
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
JWT_MAX_REFRESH_TOKENS_PER_USER=5

# Redis Configuration (for token blacklisting and rate limiting)
REDIS_URL=redis://localhost:6379/0

# Rate Limiting
RATE_LIMIT_MAX_REQUESTS_PER_HOUR=1000
SUSPICIOUS_ACTIVITY_THRESHOLD=10
```

### Redis Setup
```bash
# Install Redis
sudo apt-get install redis-server

# Start Redis service
sudo systemctl start redis-server

# Test Redis connection
redis-cli ping
```

## Testing

### Running Tests
```bash
# Run all JWT tests
python -m pytest tests/test_enhanced_jwt.py -v

# Run specific test categories
python -m pytest tests/test_enhanced_jwt.py::TestEnhancedJWTManagement -v
python -m pytest tests/test_enhanced_jwt.py::TestEnhancedAuthMiddleware -v
python -m pytest tests/test_enhanced_jwt.py::TestJWTIntegration -v
```

### Test Coverage
- Token creation and verification
- Token rotation and refresh
- Rate limiting functionality
- Security checks and monitoring
- Error handling and edge cases
- Integration testing

## Monitoring & Troubleshooting

### Logging
The system provides comprehensive logging for:
- Authentication events
- Token creation and verification
- Rate limiting violations
- Suspicious activity detection
- Redis connection issues

### Common Issues

#### Redis Connection Failed
```
WARNING: Redis connection failed. Token blacklisting and rate limiting will be disabled.
```
**Solution:** Ensure Redis is running and accessible

#### Rate Limit Exceeded
```
HTTP 429: Rate limit exceeded. Please try again later.
```
**Solution:** Wait for rate limit window to reset or contact administrator

#### Token Validation Errors
```
HTTP 401: Invalid token
```
**Solution:** Check token expiration, blacklist status, and audience validation

## Performance Considerations

### Token Size
- Access tokens: ~500 bytes
- Refresh tokens: ~600 bytes
- Reset tokens: ~400 bytes

### Redis Usage
- Blacklist entries: ~50 bytes per token
- Rate limiting: ~100 bytes per IP/hour
- User tracking: ~200 bytes per user

### Scalability
- Supports 10,000+ concurrent users
- Redis-based distributed token management
- Automatic cleanup of expired data
- Efficient token validation

## Future Enhancements

### Planned Features
1. **Multi-factor Authentication (MFA)**
   - TOTP integration
   - SMS-based verification
   - Hardware token support

2. **Advanced Analytics**
   - User behavior analysis
   - Anomaly detection
   - Predictive security

3. **Enhanced Monitoring**
   - Real-time dashboards
   - Alert systems
   - Performance metrics

4. **Compliance Features**
   - GDPR compliance tools
   - Audit logging
   - Data retention policies

## Conclusion

The enhanced JWT token management system provides enterprise-grade security for the HealthMate application. With features like token rotation, rate limiting, suspicious activity detection, and comprehensive monitoring, it ensures secure and reliable authentication for all users.

For additional support or questions, please refer to the API documentation or contact the development team. 
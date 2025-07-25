# HealthMate API Documentation

## 🏥 HealthMate API Reference

This document provides comprehensive API documentation for the HealthMate application, including all endpoints, request/response formats, authentication, and integration examples.

## 📋 Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Base URL and Headers](#base-url-and-headers)
4. [Error Handling](#error-handling)
5. [Authentication Endpoints](#authentication-endpoints)
6. [Chat Endpoints](#chat-endpoints)
7. [Health Metrics Endpoints](#health-metrics-endpoints)
8. [Health Profile Endpoints](#health-profile-endpoints)
9. [Reports Endpoints](#reports-endpoints)
10. [Settings Endpoints](#settings-endpoints)
11. [Webhooks](#webhooks)
12. [Rate Limiting](#rate-limiting)
13. [SDK Examples](#sdk-examples)

## 🌐 Overview

The HealthMate API is a RESTful API that provides access to health management features, AI-powered health assistance, and user data management. The API uses JSON for request and response bodies and follows standard HTTP status codes.

### API Versioning

- **Current Version**: v2.0
- **Base URL**: `https://api.healthmate.com/v2`
- **Content-Type**: `application/json`

### Supported HTTP Methods

- `GET` - Retrieve data
- `POST` - Create new resources
- `PUT` - Update existing resources
- `DELETE` - Remove resources
- `PATCH` - Partial updates

## 🔐 Authentication

### JWT Token Authentication

HealthMate uses JWT (JSON Web Tokens) for authentication. All API requests (except authentication endpoints) require a valid JWT token in the Authorization header.

#### Token Format

```
Authorization: Bearer <jwt_token>
```

#### Token Structure

```json
{
  "sub": "user_id",
  "email": "user@example.com",
  "permissions": ["read", "write"],
  "exp": 1642345678,
  "iat": 1642342078
}
```

#### Token Expiration

- **Access Token**: 60 minutes
- **Refresh Token**: 7 days
- **Auto-refresh**: Available for active sessions

### Authentication Flow

1. **Login/Register** to obtain access token
2. **Include token** in Authorization header
3. **Handle 401 responses** by refreshing token
4. **Logout** to invalidate token

## 🌍 Base URL and Headers

### Base URL

```
Production: https://api.healthmate.com/v2
Development: http://localhost:8000
```

### Required Headers

```http
Content-Type: application/json
Authorization: Bearer <jwt_token>
User-Agent: HealthMate-Client/2.0
```

### Optional Headers

```http
Accept: application/json
Accept-Language: en-US
X-Request-ID: unique-request-id
```

## ⚠️ Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "AUTH_001",
    "message": "Invalid credentials",
    "details": "Email or password is incorrect",
    "timestamp": "2024-01-16T10:00:00Z",
    "request_id": "req_123456789"
  }
}
```

### HTTP Status Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 422 | Validation Error |
| 429 | Rate Limited |
| 500 | Internal Server Error |

### Common Error Codes

| Error Code | Description |
|------------|-------------|
| `AUTH_001` | Invalid credentials |
| `AUTH_002` | Token expired |
| `AUTH_003` | Insufficient permissions |
| `VAL_001` | Validation error |
| `DB_001` | Database error |
| `API_001` | API rate limit exceeded |

## 🔐 Authentication Endpoints

### POST `/auth/register`

Register a new user account.

#### Request

```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",  # pragma: allowlist secret
  "password": "SecurePassword123!",  # pragma: allowlist secret
  "full_name": "John Doe",
  "age": 30,
  "accept_terms": true
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 1,
      "email": "user@example.com",
      "full_name": "John Doe",
      "age": 30,
      "created_at": "2024-01-16T10:00:00Z"
    },
    "permissions": ["read", "write"]
  },
  "message": "User registered successfully"
}
```

#### Validation Rules

- `email`: Valid email format, unique
- `password`: Minimum 8 characters, at least one uppercase, lowercase, number, and special character
- `full_name`: Required, 2-100 characters
- `age`: Optional, 13-120 years
- `accept_terms`: Required, must be true

### POST `/auth/login`

Authenticate existing user.

#### Request

```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",  # pragma: allowlist secret
  "password": "SecurePassword123!"  # pragma: allowlist secret
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 1,
      "email": "user@example.com",
      "full_name": "John Doe",
      "last_login": "2024-01-16T10:00:00Z"
    },
    "permissions": ["read", "write", "admin"]
  },
  "message": "Login successful"
}
```

### POST `/auth/refresh`

Refresh access token using refresh token.

#### Request

```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  },
  "message": "Token refreshed successfully"
}
```

### POST `/auth/forgot-password`

Request password reset email.

#### Request

```http
POST /auth/forgot-password
Content-Type: application/json

{
  "email": "user@example.com"
}
```

#### Response

```json
{
  "success": true,
  "message": "Password reset email sent",
  "data": {
    "email": "user@example.com",
    "expires_at": "2024-01-16T11:00:00Z"
  }
}
```

### POST `/auth/reset-password`

Reset password using reset token.

#### Request

```http
POST /auth/reset-password
Content-Type: application/json

{
  "token": "reset_token_here",
  "new_password": "NewSecurePassword123!"  # pragma: allowlist secret
}
```

#### Response

```json
{
  "success": true,
  "message": "Password reset successfully"
}
```

### POST `/auth/logout`

Logout user and invalidate tokens.

#### Request

```http
POST /auth/logout
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Response

```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

## 💬 Chat Endpoints

### POST `/chat/message`

Send message to AI health assistant.

#### Request

```http
POST /chat/message
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "message": "What are the symptoms of diabetes?",
  "conversation_id": null,
  "context": {
    "user_health_profile": {
      "age": 30,
      "conditions": ["hypertension"]
    }
  }
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "response": "Diabetes symptoms include increased thirst, frequent urination, extreme hunger, unexplained weight loss, fatigue, irritability, blurred vision, slow-healing sores, and frequent infections. However, these symptoms can vary and may not appear immediately. It's important to consult with a healthcare professional for proper diagnosis.",
    "conversation_id": 123,
    "message_id": 456,
    "timestamp": "2024-01-16T10:00:00Z",
    "suggestions": [
      "How can I prevent diabetes?",
      "What are the risk factors?",
      "When should I see a doctor?"
    ],
    "confidence_score": 0.95
  }
}
```

### GET `/chat/history`

Retrieve chat conversation history.

#### Request

```http
GET /chat/history?page=1&limit=20&conversation_id=123
Authorization: Bearer <jwt_token>
```

#### Response

```json
{
  "success": true,
  "data": {
    "conversations": [
      {
        "conversation_id": 123,
        "title": "Diabetes Symptoms Discussion",
        "created_at": "2024-01-16T09:30:00Z",
        "updated_at": "2024-01-16T10:00:00Z",
        "message_count": 4,
        "messages": [
          {
            "id": 456,
            "role": "user",
            "content": "What are the symptoms of diabetes?",
            "timestamp": "2024-01-16T09:30:00Z"
          },
          {
            "id": 457,
            "role": "assistant",
            "content": "Diabetes symptoms include...",
            "timestamp": "2024-01-16T09:30:05Z"
          }
        ]
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 5,
      "pages": 1
    }
  }
}
```

### POST `/chat/feedback`

Provide feedback on AI responses.

#### Request

```http
POST /chat/feedback
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "message_id": 456,
  "rating": 5,
  "feedback": "Very helpful and accurate information",
  "category": "helpful"
}
```

#### Response

```json
{
  "success": true,
  "message": "Feedback submitted successfully"
}
```

### DELETE `/chat/conversation/{conversation_id}`

Delete a conversation.

#### Request

```http
DELETE /chat/conversation/123
Authorization: Bearer <jwt_token>
```

#### Response

```json
{
  "success": true,
  "message": "Conversation deleted successfully"
}
```

## 📊 Health Metrics Endpoints

### POST `/health/metrics`

Add new health metric.

#### Request

```http
POST /health/metrics
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "metric_type": "weight",
  "value": 70.5,
  "unit": "kg",
  "date": "2024-01-16",
  "notes": "Morning weight after breakfast",
  "tags": ["morning", "post-meal"]
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "id": 789,
    "metric_type": "weight",
    "value": 70.5,
    "unit": "kg",
    "date": "2024-01-16",
    "notes": "Morning weight after breakfast",
    "tags": ["morning", "post-meal"],
    "created_at": "2024-01-16T10:00:00Z",
    "trend": {
      "change": -0.5,
      "change_percentage": -0.7,
      "period": "7_days"
    }
  }
}
```

### GET `/health/metrics`

Retrieve health metrics with filtering and pagination.

#### Request

```http
GET /health/metrics?metric_type=weight&start_date=2024-01-01&end_date=2024-01-16&page=1&limit=50
Authorization: Bearer <jwt_token>
```

#### Response

```json
{
  "success": true,
  "data": {
    "metrics": [
      {
        "id": 789,
        "metric_type": "weight",
        "value": 70.5,
        "unit": "kg",
        "date": "2024-01-16",
        "notes": "Morning weight after breakfast",
        "tags": ["morning", "post-meal"],
        "created_at": "2024-01-16T10:00:00Z"
      }
    ],
    "summary": {
      "total_count": 15,
      "average_value": 70.2,
      "min_value": 69.8,
      "max_value": 71.0,
      "trend": "decreasing"
    },
    "pagination": {
      "page": 1,
      "limit": 50,
      "total": 15,
      "pages": 1
    }
  }
}
```

### PUT `/health/metrics/{metric_id}`

Update existing health metric.

#### Request

```http
PUT /health/metrics/789
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "value": 70.3,
  "notes": "Updated morning weight",
  "tags": ["morning", "updated"]
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "id": 789,
    "metric_type": "weight",
    "value": 70.3,
    "unit": "kg",
    "date": "2024-01-16",
    "notes": "Updated morning weight",
    "tags": ["morning", "updated"],
    "updated_at": "2024-01-16T10:30:00Z"
  }
}
```

### DELETE `/health/metrics/{metric_id}`

Delete health metric.

#### Request

```http
DELETE /health/metrics/789
Authorization: Bearer <jwt_token>
```

#### Response

```json
{
  "success": true,
  "message": "Health metric deleted successfully"
}
```

### GET `/health/metrics/types`

Get available metric types and their configurations.

#### Request

```http
GET /health/metrics/types
Authorization: Bearer <jwt_token>
```

#### Response

```json
{
  "success": true,
  "data": {
    "metric_types": [
      {
        "type": "weight",
        "name": "Weight",
        "unit": "kg",
        "min_value": 20,
        "max_value": 300,
        "decimal_places": 1,
        "required": false
      },
      {
        "type": "blood_pressure",
        "name": "Blood Pressure",
        "unit": "mmHg",
        "components": ["systolic", "diastolic"],
        "min_value": 50,
        "max_value": 300,
        "required": false
      }
    ]
  }
}
```

## 👤 Health Profile Endpoints

### GET `/health/profile`

Get user's health profile.

#### Request

```http
GET /health/profile
Authorization: Bearer <jwt_token>
```

#### Response

```json
{
  "success": true,
  "data": {
    "personal_info": {
      "full_name": "John Doe",
      "age": 30,
      "gender": "male",
      "height": 175,
      "weight": 70.5,
      "bmi": 23.0
    },
    "medical_history": {
      "conditions": [
        {
          "id": 1,
          "name": "Hypertension",
          "diagnosed_date": "2020-01-15",
          "severity": "mild",
          "notes": "Controlled with medication"
        }
      ],
      "allergies": [
        {
          "id": 1,
          "allergen": "Penicillin",
          "reaction": "Rash",
          "severity": "moderate"
        }
      ]
    },
    "medications": [
      {
        "id": 1,
        "name": "Lisinopril",
        "dosage": "10mg",
        "frequency": "daily",
        "start_date": "2020-01-20",
        "prescribed_by": "Dr. Smith"
      }
    ],
    "emergency_contacts": [
      {
        "id": 1,
        "name": "Jane Doe",
        "relationship": "Spouse",
        "phone": "+1234567890",
        "email": "jane@example.com"
      }
    ]
  }
}
```

### PUT `/health/profile`

Update user's health profile.

#### Request

```http
PUT /health/profile
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "personal_info": {
    "full_name": "John Doe",
    "age": 31,
    "height": 175
  },
  "medical_history": {
    "conditions": [
      {
        "name": "Hypertension",
        "diagnosed_date": "2020-01-15",
        "severity": "mild"
      }
    ]
  }
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "personal_info": {
      "full_name": "John Doe",
      "age": 31,
      "height": 175,
      "updated_at": "2024-01-16T10:00:00Z"
    },
    "medical_history": {
      "conditions": [
        {
          "id": 1,
          "name": "Hypertension",
          "diagnosed_date": "2020-01-15",
          "severity": "mild"
        }
      ]
    }
  }
}
```

### POST `/health/profile/conditions`

Add medical condition to profile.

#### Request

```http
POST /health/profile/conditions
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "name": "Diabetes Type 2",
  "diagnosed_date": "2024-01-10",
  "severity": "moderate",
  "notes": "Recently diagnosed, monitoring blood sugar"
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "id": 2,
    "name": "Diabetes Type 2",
    "diagnosed_date": "2024-01-10",
    "severity": "moderate",
    "notes": "Recently diagnosed, monitoring blood sugar",
    "created_at": "2024-01-16T10:00:00Z"
  }
}
```

## 📋 Reports Endpoints

### POST `/reports/generate`

Generate health report.

#### Request

```http
POST /reports/generate
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "report_type": "health_summary",
  "date_range": {
    "start_date": "2024-01-01",
    "end_date": "2024-01-16"
  },
  "include_metrics": ["weight", "blood_pressure"],
  "include_chat_history": true,
  "format": "pdf"
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "report_id": "rep_123456789",
    "report_type": "health_summary",
    "status": "generating",
    "estimated_completion": "2024-01-16T10:05:00Z",
    "download_url": null
  }
}
```

### GET `/reports/{report_id}`

Get report status and download URL.

#### Request

```http
GET /reports/rep_123456789
Authorization: Bearer <jwt_token>
```

#### Response

```json
{
  "success": true,
  "data": {
    "report_id": "rep_123456789",
    "report_type": "health_summary",
    "status": "completed",
    "created_at": "2024-01-16T10:00:00Z",
    "completed_at": "2024-01-16T10:02:00Z",
    "download_url": "https://api.healthmate.com/v2/reports/rep_123456789/download",
    "expires_at": "2024-01-23T10:02:00Z",
    "summary": {
      "total_metrics": 15,
      "conversations": 8,
      "insights": 5
    }
  }
}
```

### GET `/reports/list`

List user's reports.

#### Request

```http
GET /reports/list?page=1&limit=20&status=completed
Authorization: Bearer <jwt_token>
```

#### Response

```json
{
  "success": true,
  "data": {
    "reports": [
      {
        "report_id": "rep_123456789",
        "report_type": "health_summary",
        "status": "completed",
        "created_at": "2024-01-16T10:00:00Z",
        "completed_at": "2024-01-16T10:02:00Z",
        "download_url": "https://api.healthmate.com/v2/reports/rep_123456789/download"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 5,
      "pages": 1
    }
  }
}
```

## ⚙️ Settings Endpoints

### GET `/settings`

Get user settings.

#### Request

```http
GET /settings
Authorization: Bearer <jwt_token>
```

#### Response

```json
{
  "success": true,
  "data": {
    "notifications": {
      "email_notifications": true,
      "in_app_notifications": true,
      "reminder_frequency": "daily",
      "health_alerts": true,
      "report_notifications": true
    },
    "privacy": {
      "data_sharing": false,
      "profile_visibility": "private",
      "data_retention": "1_year",
      "analytics_consent": true
    },
    "appearance": {
      "theme": "light",
      "font_size": "medium",
      "color_scheme": "default",
      "language": "en"
    },
    "security": {
      "two_factor_enabled": false,
      "session_timeout": 60,
      "login_notifications": true
    }
  }
}
```

### PUT `/settings`

Update user settings.

#### Request

```http
PUT /settings
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "notifications": {
    "email_notifications": false,
    "reminder_frequency": "weekly"
  },
  "appearance": {
    "theme": "dark",
    "font_size": "large"
  }
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "notifications": {
      "email_notifications": false,
      "in_app_notifications": true,
      "reminder_frequency": "weekly",
      "health_alerts": true,
      "report_notifications": true
    },
    "appearance": {
      "theme": "dark",
      "font_size": "large",
      "color_scheme": "default",
      "language": "en"
    }
  }
}
```

### POST `/settings/export-data`

Request data export.

#### Request

```http
POST /settings/export-data
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "data_types": ["profile", "metrics", "chat_history"],
  "format": "json",
  "date_range": {
    "start_date": "2024-01-01",
    "end_date": "2024-01-16"
  }
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "export_id": "exp_123456789",
    "status": "processing",
    "estimated_completion": "2024-01-16T10:10:00Z",
    "download_url": null
  }
}
```

## 🔗 Webhooks

### Webhook Configuration

HealthMate supports webhooks for real-time notifications.

#### Webhook Events

- `user.registered` - New user registration
- `user.login` - User login
- `health_metric.added` - New health metric added
- `chat.message.sent` - New chat message
- `report.generated` - Report generation completed

#### Webhook Payload Example

```json
{
  "event": "health_metric.added",
  "timestamp": "2024-01-16T10:00:00Z",
  "user_id": 1,
  "data": {
    "metric_id": 789,
    "metric_type": "weight",
    "value": 70.5,
    "date": "2024-01-16"
  }
}
```

### POST `/webhooks/register`

Register webhook endpoint.

#### Request

```http
POST /webhooks/register
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "url": "https://your-app.com/webhooks/healthmate",
  "events": ["health_metric.added", "chat.message.sent"],
  "secret": "your-webhook-secret"  # pragma: allowlist secret
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "webhook_id": "webhook_123456789",
    "url": "https://your-app.com/webhooks/healthmate",
    "events": ["health_metric.added", "chat.message.sent"],
    "status": "active",
    "created_at": "2024-01-16T10:00:00Z"
  }
}
```

## 🚦 Rate Limiting

### Rate Limits

- **Authentication endpoints**: 10 requests per minute
- **Chat endpoints**: 60 requests per minute
- **Health metrics**: 100 requests per minute
- **Reports**: 10 requests per hour
- **General endpoints**: 1000 requests per hour

### Rate Limit Headers

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642345678
```

### Rate Limit Response

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded",
    "details": "Too many requests. Try again in 60 seconds.",
    "retry_after": 60
  }
}
```

## 📚 SDK Examples

### Python SDK Example

```python
import requests
from typing import Dict, Any

class HealthMateAPI:
    def __init__(self, base_url: str, access_token: str = None):
        self.base_url = base_url
        self.access_token = access_token
        self.session = requests.Session()
        
        if access_token:
            self.session.headers.update({
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            })
    
    def login(self, email: str, password: str) -> Dict[str, Any]:
        """Login user and get access token"""
        response = self.session.post(f"{self.base_url}/auth/login", json={
            'email': email,
            'password': password
        })
        
        if response.status_code == 200:
            data = response.json()
            self.access_token = data['data']['access_token']
            self.session.headers.update({
                'Authorization': f'Bearer {self.access_token}'
            })
            return data
        else:
            raise Exception(f"Login failed: {response.text}")
    
    def send_chat_message(self, message: str) -> Dict[str, Any]:
        """Send message to AI assistant"""
        response = self.session.post(f"{self.base_url}/chat/message", json={
            'message': message
        })
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Chat failed: {response.text}")
    
    def add_health_metric(self, metric_type: str, value: float, 
                         unit: str, date: str) -> Dict[str, Any]:
        """Add health metric"""
        response = self.session.post(f"{self.base_url}/health/metrics", json={
            'metric_type': metric_type,
            'value': value,
            'unit': unit,
            'date': date
        })
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Add metric failed: {response.text}")

# Usage example
api = HealthMateAPI('https://api.healthmate.com/v2')

# Login
login_data = api.login('user@example.com', 'password123')
print(f"Logged in as: {login_data['data']['user']['full_name']}")

# Send chat message
chat_response = api.send_chat_message("What are the symptoms of diabetes?")
print(f"AI Response: {chat_response['data']['response']}")

# Add health metric
metric_response = api.add_health_metric("weight", 70.5, "kg", "2024-01-16")
print(f"Added metric: {metric_response['data']['id']}")
```

### JavaScript SDK Example

```javascript
class HealthMateAPI {
    constructor(baseUrl, accessToken = null) {
        this.baseUrl = baseUrl;
        this.accessToken = accessToken;
        this.headers = {
            'Content-Type': 'application/json'
        };
        
        if (accessToken) {
            this.headers['Authorization'] = `Bearer ${accessToken}`;
        }
    }
    
    async login(email, password) {
        const response = await fetch(`${this.baseUrl}/auth/login`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify({ email, password })
        });
        
        if (response.ok) {
            const data = await response.json();
            this.accessToken = data.data.access_token;
            this.headers['Authorization'] = `Bearer ${this.accessToken}`;
            return data;
        } else {
            throw new Error(`Login failed: ${response.statusText}`);
        }
    }
    
    async sendChatMessage(message) {
        const response = await fetch(`${this.baseUrl}/chat/message`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify({ message })
        });
        
        if (response.ok) {
            return await response.json();
        } else {
            throw new Error(`Chat failed: ${response.statusText}`);
        }
    }
    
    async addHealthMetric(metricType, value, unit, date) {
        const response = await fetch(`${this.baseUrl}/health/metrics`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify({
                metric_type: metricType,
                value,
                unit,
                date
            })
        });
        
        if (response.ok) {
            return await response.json();
        } else {
            throw new Error(`Add metric failed: ${response.statusText}`);
        }
    }
}

// Usage example
const api = new HealthMateAPI('https://api.healthmate.com/v2');

// Login
api.login('user@example.com', 'password123')
    .then(loginData => {
        console.log(`Logged in as: ${loginData.data.user.full_name}`);
        
        // Send chat message
        return api.sendChatMessage("What are the symptoms of diabetes?");
    })
    .then(chatResponse => {
        console.log(`AI Response: ${chatResponse.data.response}`);
        
        // Add health metric
        return api.addHealthMetric("weight", 70.5, "kg", "2024-01-16");
    })
    .then(metricResponse => {
        console.log(`Added metric: ${metricResponse.data.id}`);
    })
    .catch(error => {
        console.error('Error:', error);
    });
```

---

## 📄 Version Information

**HealthMate API Documentation v2.0**
- **Last Updated**: January 2024
- **API Version**: v2.0
- **Documentation Status**: Complete and Current

For the most up-to-date information, please visit our official API documentation website or contact the development team.

---

*This API documentation is designed to help developers integrate with the HealthMate platform. For additional support, please contact the development team or refer to the project's issue tracker.* 
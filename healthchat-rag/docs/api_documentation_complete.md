# HealthMate API Documentation

## 🏥 Complete API Reference

This document provides comprehensive API documentation for the HealthMate application, including all endpoints, authentication, compliance features, and integration examples.

## 📋 Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Base URL and Headers](#base-url-and-headers)
4. [Error Handling](#error-handling)
5. [Rate Limiting](#rate-limiting)
6. [Authentication Endpoints](#authentication-endpoints)
7. [Health Data Endpoints](#health-data-endpoints)
8. [Chat Endpoints](#chat-endpoints)
9. [Compliance Endpoints](#compliance-endpoints)
10. [User Management Endpoints](#user-management-endpoints)
11. [Analytics Endpoints](#analytics-endpoints)
12. [System Endpoints](#system-endpoints)
13. [WebSocket Endpoints](#websocket-endpoints)
14. [Integration Examples](#integration-examples)
15. [SDK Examples](#sdk-examples)
16. [Troubleshooting](#troubleshooting)

## 🌐 Overview

The HealthMate API is a RESTful API that provides comprehensive health management features, AI-powered health assistance, compliance management, and user data management. The API uses JSON for request and response bodies and follows standard HTTP status codes.

### API Versioning

- **Current Version**: v2.0
- **Base URL**: `https://api.healthmate.com/v2`
- **Content-Type**: `application/json`
- **Documentation**: `/docs` (Swagger UI)
- **OpenAPI Spec**: `/openapi.json`

### Supported HTTP Methods

- `GET` - Retrieve data
- `POST` - Create new resources
- `PUT` - Update existing resources
- `DELETE` - Remove resources
- `PATCH` - Partial updates

### Compliance Standards

- **HIPAA**: Full compliance for healthcare data
- **GDPR**: Complete data protection compliance
- **SOC 2**: Security and availability controls
- **ISO 27001**: Information security management

## 🔐 Authentication

### JWT Token Authentication

HealthMate uses JWT (JSON Web Tokens) for authentication with enhanced security features.

#### Token Types

- **Access Token**: Short-lived (30 minutes) for API access
- **Refresh Token**: Long-lived (7 days) for token renewal
- **Reset Token**: Short-lived (1 hour) for password reset

#### Token Structure

```json
{
  "sub": "user_id",
  "email": "user@example.com",
  "role": "patient",
  "permissions": ["read", "write"],
  "exp": 1642345678,
  "iat": 1642342078,
  "jti": "unique_token_id",
  "fingerprint": "abc123def456"
}
```

#### Authentication Flow

1. **Login/Register** to obtain access token
2. **Include token** in Authorization header
3. **Handle 401 responses** by refreshing token
4. **Logout** to invalidate token

### Token Security Features

- **Fingerprinting**: Unique token fingerprint for replay protection
- **Blacklisting**: Automatic token blacklisting on logout
- **Rate Limiting**: Authentication rate limiting
- **Suspicious Activity Detection**: Automatic detection of unusual patterns

## 🌍 Base URL and Headers

### Base URL

```
Production: https://api.healthmate.com/v2
Development: http://localhost:8000
Staging: https://staging-api.healthmate.com/v2
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
X-Correlation-ID: correlation-id
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
    "request_id": "req_123456789",
    "correlation_id": "corr_987654321"
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
| 503 | Service Unavailable |

### Common Error Codes

| Error Code | Description |
|------------|-------------|
| `AUTH_001` | Invalid credentials |
| `AUTH_002` | Token expired |
| `AUTH_003` | Insufficient permissions |
| `VAL_001` | Validation error |
| `DB_001` | Database error |
| `API_001` | API rate limit exceeded |
| `COMP_001` | Compliance violation |
| `SEC_001` | Security violation |

## 🚦 Rate Limiting

### Rate Limit Headers

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642345678
```

### Rate Limits by Endpoint

| Endpoint Category | Requests per Hour | Requests per Minute |
|------------------|-------------------|-------------------|
| Authentication | 100 | 10 |
| Health Data | 1000 | 20 |
| Chat | 500 | 10 |
| Compliance | 100 | 5 |
| Analytics | 200 | 10 |
| System | 500 | 20 |

## 🔐 Authentication Endpoints

### POST `/auth/register`

Register a new user account.

#### Request

```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "full_name": "John Doe",
  "age": 30,
  "accept_terms": true,
  "consent_marketing": false,
  "consent_data_processing": true
}
```

#### Response

```json
{
  "success": true,
  "message": "User registered successfully",
  "data": {
    "user_id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "patient",
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 1800
  }
}
```

### POST `/auth/login`

Authenticate existing user.

#### Request

```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 1800,
    "user": {
      "id": 1,
      "email": "user@example.com",
      "full_name": "John Doe",
      "role": "patient",
      "is_active": true
    }
  }
}
```

### POST `/auth/refresh`

Refresh access token using refresh token.

#### Request

```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 1800
  }
}
```

### POST `/auth/forgot-password`

Request password reset.

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
  "new_password": "NewSecurePassword123!"
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
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### Response

```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

### GET `/auth/me`

Get current user information.

#### Request

```http
GET /auth/me
Authorization: Bearer <jwt_token>
```

#### Response

```json
{
  "success": true,
  "data": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "age": 30,
    "role": "patient",
    "is_active": true,
    "created_at": "2024-01-01T12:00:00Z",
    "last_login": "2024-01-16T10:00:00Z"
  }
}
```

## 🏥 Health Data Endpoints

### POST `/health/data`

Create new health data entry.

#### Request

```http
POST /health/data
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "data_type": "blood_pressure",
  "value": {
    "systolic": 120,
    "diastolic": 80
  },
  "unit": "mmHg",
  "timestamp": "2024-01-16T10:00:00Z",
  "notes": "Taken after morning exercise",
  "source": "manual"
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "id": 123,
    "user_id": 1,
    "data_type": "blood_pressure",
    "value": {
      "systolic": 120,
      "diastolic": 80
    },
    "unit": "mmHg",
    "timestamp": "2024-01-16T10:00:00Z",
    "notes": "Taken after morning exercise",
    "source": "manual",
    "confidence": 1.0,
    "created_at": "2024-01-16T10:00:00Z"
  }
}
```

### GET `/health/data`

Retrieve health data with filtering and pagination.

#### Request

```http
GET /health/data?data_type=blood_pressure&start_date=2024-01-01&end_date=2024-01-16&page=1&limit=10
Authorization: Bearer <jwt_token>
```

#### Response

```json
{
  "success": true,
  "data": {
    "records": [
      {
        "id": 123,
        "data_type": "blood_pressure",
        "value": {
          "systolic": 120,
          "diastolic": 80
        },
        "unit": "mmHg",
        "timestamp": "2024-01-16T10:00:00Z",
        "notes": "Taken after morning exercise",
        "source": "manual"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 10,
      "total": 25,
      "pages": 3
    }
  }
}
```

### PUT `/health/data/{data_id}`

Update health data entry.

#### Request

```http
PUT /health/data/123
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "value": {
    "systolic": 118,
    "diastolic": 78
  },
  "notes": "Updated reading after recheck"
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "id": 123,
    "value": {
      "systolic": 118,
      "diastolic": 78
    },
    "notes": "Updated reading after recheck",
    "updated_at": "2024-01-16T10:30:00Z"
  }
}
```

### DELETE `/health/data/{data_id}`

Delete health data entry.

#### Request

```http
DELETE /health/data/123
Authorization: Bearer <jwt_token>
```

#### Response

```json
{
  "success": true,
  "message": "Health data deleted successfully"
}
```

### GET `/health/metrics/types`

Get available health metric types.

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
        "type": "blood_pressure",
        "name": "Blood Pressure",
        "unit": "mmHg",
        "description": "Systolic and diastolic blood pressure readings",
        "validation_rules": {
          "systolic": {"min": 70, "max": 200},
          "diastolic": {"min": 40, "max": 130}
        }
      },
      {
        "type": "heart_rate",
        "name": "Heart Rate",
        "unit": "bpm",
        "description": "Heart rate measurements",
        "validation_rules": {
          "value": {"min": 30, "max": 200}
        }
      }
    ]
  }
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
    "conversation_id": "conv_123456789",
    "message_id": "msg_987654321",
    "timestamp": "2024-01-16T10:00:00Z",
    "suggestions": [
      "How can I prevent diabetes?",
      "What are the risk factors?",
      "When should I see a doctor?"
    ],
    "confidence_score": 0.95,
    "sources": [
      {
        "title": "Diabetes Symptoms - Mayo Clinic",
        "url": "https://www.mayoclinic.org/diseases-conditions/diabetes/symptoms-causes/syc-20371444"
      }
    ]
  }
}
```

### GET `/chat/history`

Retrieve chat conversation history.

#### Request

```http
GET /chat/history?conversation_id=conv_123456789&page=1&limit=20
Authorization: Bearer <jwt_token>
```

#### Response

```json
{
  "success": true,
  "data": {
    "conversation_id": "conv_123456789",
    "messages": [
      {
        "id": "msg_987654321",
        "message_type": "user_message",
        "content": "What are the symptoms of diabetes?",
        "timestamp": "2024-01-16T10:00:00Z"
      },
      {
        "id": "msg_123456789",
        "message_type": "ai_response",
        "content": "Diabetes symptoms include increased thirst...",
        "timestamp": "2024-01-16T10:00:01Z",
        "confidence_score": 0.95
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 2,
      "pages": 1
    }
  }
}
```

### POST `/chat/feedback`

Provide feedback on AI response.

#### Request

```http
POST /chat/feedback
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "message_id": "msg_123456789",
  "rating": 5,
  "feedback_type": "helpful",
  "comment": "Very informative and accurate response"
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

Delete conversation.

#### Request

```http
DELETE /chat/conversation/conv_123456789
Authorization: Bearer <jwt_token>
```

#### Response

```json
{
  "success": true,
  "message": "Conversation deleted successfully"
}
```

## 🔒 Compliance Endpoints

### GET `/compliance/hipaa-compliance`

Check HIPAA compliance.

#### Request

```http
GET /compliance/hipaa-compliance
Authorization: Bearer <jwt_token>
```

#### Response

```json
{
  "success": true,
  "data": {
    "compliant": true,
    "compliance_score": 98.5,
    "checks": {
      "data_encryption": {
        "compliant": true,
        "details": {
          "encryption_configured": true,
          "sensitive_fields_encrypted": true
        }
      },
      "access_controls": {
        "compliant": true,
        "details": {
          "rbac_implemented": true,
          "jwt_configured": true,
          "rate_limiting_enabled": true
        }
      }
    },
    "timestamp": "2024-01-16T10:00:00Z"
  }
}
```

### GET `/compliance/gdpr-compliance`

Check GDPR compliance.

#### Request

```http
GET /compliance/gdpr-compliance
Authorization: Bearer <jwt_token>
```

#### Response

```json
{
  "success": true,
  "data": {
    "compliant": true,
    "compliance_score": 97.0,
    "checks": {
      "data_portability": {
        "compliant": true,
        "details": {
          "export_functionality": true,
          "multiple_formats": true
        }
      },
      "right_to_be_forgotten": {
        "compliant": true,
        "details": {
          "deletion_functionality": true,
          "cascade_deletion": true
        }
      }
    },
    "timestamp": "2024-01-16T10:00:00Z"
  }
}
```

### POST `/compliance/export-data`

Export user data (GDPR Article 20).

#### Request

```http
POST /compliance/export-data
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "format": "json",
  "include_health_data": true,
  "include_conversations": true,
  "include_analytics": false
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "user_profile": {
      "id": 1,
      "email": "user@example.com",
      "full_name": "John Doe",
      "age": 30,
      "role": "patient"
    },
    "health_data": [
      {
        "id": 123,
        "data_type": "blood_pressure",
        "value": {"systolic": 120, "diastolic": 80},
        "timestamp": "2024-01-16T10:00:00Z"
      }
    ],
    "conversation_history": [
      {
        "id": 456,
        "message_type": "user_message",
        "content": "What are the symptoms of diabetes?",
        "timestamp": "2024-01-16T10:00:00Z"
      }
    ],
    "export_metadata": {
      "exported_at": "2024-01-16T10:00:00Z",
      "format": "json",
      "compliance": "gdpr_article_20"
    }
  }
}
```

### POST `/compliance/delete-data`

Delete user data (GDPR Article 17).

#### Request

```http
POST /compliance/delete-data
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "data_categories": ["conversation_data", "analytics_data"],
  "confirm_deletion": true,
  "archive_before_delete": true
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "user_id": 1,
    "deleted_categories": ["conversation_data", "analytics_data"],
    "records_deleted": 150,
    "deletion_timestamp": "2024-01-16T10:00:00Z",
    "compliance": "gdpr_article_17"
  },
  "message": "Data deletion completed successfully"
}
```

### POST `/compliance/generate-report`

Generate compliance report (Admin only).

#### Request

```http
POST /compliance/generate-report
Authorization: Bearer <admin_jwt_token>
Content-Type: application/json

{
  "report_type": "monthly",
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-01-31T23:59:59Z",
  "include_recommendations": true
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "report_id": "compliance_monthly_20240101_20240131",
    "report_type": "monthly",
    "generated_at": "2024-01-16T10:00:00Z",
    "period_start": "2024-01-01T00:00:00Z",
    "period_end": "2024-01-31T23:59:59Z",
    "compliance_score": 97.5,
    "violations": [],
    "recommendations": [
      "Maintain current compliance standards"
    ],
    "data_retention_status": {
      "policies_configured": 6,
      "cleanup_scheduled": true,
      "last_cleanup": "2024-01-15T02:00:00Z"
    },
    "audit_summary": {
      "total_events": 15000,
      "compliance_score": 95.0
    }
  }
}
```

## 👤 User Management Endpoints

### GET `/users/profile`

Get user profile.

#### Request

```http
GET /users/profile
Authorization: Bearer <jwt_token>
```

#### Response

```json
{
  "success": true,
  "data": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "age": 30,
    "role": "patient",
    "phone": "+1234567890",
    "address": "123 Main St, City, State",
    "date_of_birth": "1994-01-01",
    "blood_type": "O+",
    "allergies": ["penicillin", "peanuts"],
    "emergency_contact": {
      "name": "Jane Doe",
      "relationship": "Spouse",
      "phone": "+1234567891"
    },
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-16T10:00:00Z"
  }
}
```

### PUT `/users/profile`

Update user profile.

#### Request

```http
PUT /users/profile
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "full_name": "John Smith",
  "phone": "+1234567890",
  "address": "456 Oak Ave, City, State",
  "emergency_contact": {
    "name": "Jane Smith",
    "relationship": "Spouse",
    "phone": "+1234567891"
  }
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "id": 1,
    "full_name": "John Smith",
    "phone": "+1234567890",
    "address": "456 Oak Ave, City, State",
    "emergency_contact": {
      "name": "Jane Smith",
      "relationship": "Spouse",
      "phone": "+1234567891"
    },
    "updated_at": "2024-01-16T10:00:00Z"
  }
}
```

### POST `/users/change-password`

Change user password.

#### Request

```http
POST /users/change-password
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "current_password": "OldPassword123!",
  "new_password": "NewPassword456!"
}
```

#### Response

```json
{
  "success": true,
  "message": "Password changed successfully"
}
```

## 📊 Analytics Endpoints

### GET `/analytics/health-summary`

Get health analytics summary.

#### Request

```http
GET /analytics/health-summary?period=30d
Authorization: Bearer <jwt_token>
```

#### Response

```json
{
  "success": true,
  "data": {
    "period": "30d",
    "health_score": 85.5,
    "metrics": {
      "blood_pressure": {
        "average_systolic": 120,
        "average_diastolic": 80,
        "trend": "stable",
        "readings_count": 15
      },
      "heart_rate": {
        "average": 72,
        "trend": "improving",
        "readings_count": 30
      },
      "steps": {
        "daily_average": 8500,
        "trend": "increasing",
        "goal_achievement": 85
      }
    },
    "insights": [
      "Your blood pressure has been stable over the last 30 days",
      "Your heart rate shows improvement trend",
      "You're achieving 85% of your daily step goal"
    ],
    "recommendations": [
      "Continue monitoring blood pressure weekly",
      "Maintain current exercise routine",
      "Consider increasing daily step goal to 10,000"
    ]
  }
}
```

### GET `/analytics/trends`

Get health trends analysis.

#### Request

```http
GET /analytics/trends?metric=blood_pressure&period=90d
Authorization: Bearer <jwt_token>
```

#### Response

```json
{
  "success": true,
  "data": {
    "metric": "blood_pressure",
    "period": "90d",
    "trend": "improving",
    "trend_strength": 0.75,
    "data_points": [
      {
        "date": "2024-01-01",
        "systolic": 125,
        "diastolic": 85
      },
      {
        "date": "2024-01-16",
        "systolic": 120,
        "diastolic": 80
      }
    ],
    "statistics": {
      "min_systolic": 115,
      "max_systolic": 130,
      "min_diastolic": 75,
      "max_diastolic": 88,
      "correlation": -0.3
    }
  }
}
```

## 🔧 System Endpoints

### GET `/system/health`

Get system health status.

#### Request

```http
GET /system/health
```

#### Response

```json
{
  "status": "healthy",
  "timestamp": "2024-01-16T10:00:00Z",
  "version": "2.0.0",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "vector_store": "healthy",
    "ai_service": "healthy"
  },
  "metrics": {
    "uptime": "7d 12h 30m",
    "memory_usage": "65%",
    "cpu_usage": "45%",
    "active_connections": 150
  }
}
```

### GET `/system/metrics`

Get system performance metrics.

#### Request

```http
GET /system/metrics
Authorization: Bearer <admin_jwt_token>
```

#### Response

```json
{
  "success": true,
  "data": {
    "performance": {
      "average_response_time": 150,
      "requests_per_second": 25,
      "error_rate": 0.1,
      "uptime_percentage": 99.9
    },
    "database": {
      "active_connections": 15,
      "query_performance": "good",
      "storage_usage": "45%"
    },
    "cache": {
      "hit_rate": 85,
      "memory_usage": "60%",
      "evictions": 0
    }
  }
}
```

## 🔌 WebSocket Endpoints

### WebSocket Connection

Connect to real-time updates.

#### Connection

```javascript
const ws = new WebSocket('wss://api.healthmate.com/v2/ws?token=<jwt_token>');
```

#### Message Format

```json
{
  "type": "health_update",
  "data": {
    "metric": "heart_rate",
    "value": 75,
    "timestamp": "2024-01-16T10:00:00Z"
  }
}
```

#### Event Types

- `health_update`: Real-time health data updates
- `chat_message`: New chat messages
- `notification`: System notifications
- `compliance_alert`: Compliance-related alerts

## 🔗 Integration Examples

### Python SDK Example

```python
import requests
import json

class HealthMateAPI:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    def get_health_data(self, data_type=None, start_date=None, end_date=None):
        params = {}
        if data_type:
            params['data_type'] = data_type
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        
        response = requests.get(
            f'{self.base_url}/health/data',
            headers=self.headers,
            params=params
        )
        return response.json()
    
    def create_health_data(self, data_type, value, unit=None, notes=None):
        data = {
            'data_type': data_type,
            'value': value
        }
        if unit:
            data['unit'] = unit
        if notes:
            data['notes'] = notes
        
        response = requests.post(
            f'{self.base_url}/health/data',
            headers=self.headers,
            json=data
        )
        return response.json()
    
    def send_chat_message(self, message, conversation_id=None):
        data = {
            'message': message
        }
        if conversation_id:
            data['conversation_id'] = conversation_id
        
        response = requests.post(
            f'{self.base_url}/chat/message',
            headers=self.headers,
            json=data
        )
        return response.json()

# Usage example
api = HealthMateAPI('https://api.healthmate.com/v2', 'your_jwt_token')

# Get blood pressure data
bp_data = api.get_health_data(data_type='blood_pressure')

# Create new health data
new_data = api.create_health_data(
    data_type='heart_rate',
    value=75,
    unit='bpm',
    notes='After morning walk'
)

# Send chat message
response = api.send_chat_message('What are the symptoms of diabetes?')
```

### JavaScript SDK Example

```javascript
class HealthMateAPI {
    constructor(baseUrl, apiKey) {
        this.baseUrl = baseUrl;
        this.headers = {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json'
        };
    }
    
    async getHealthData(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const response = await fetch(
            `${this.baseUrl}/health/data?${queryString}`,
            { headers: this.headers }
        );
        return response.json();
    }
    
    async createHealthData(data) {
        const response = await fetch(
            `${this.baseUrl}/health/data`,
            {
                method: 'POST',
                headers: this.headers,
                body: JSON.stringify(data)
            }
        );
        return response.json();
    }
    
    async sendChatMessage(message, conversationId = null) {
        const data = { message };
        if (conversationId) {
            data.conversation_id = conversationId;
        }
        
        const response = await fetch(
            `${this.baseUrl}/chat/message`,
            {
                method: 'POST',
                headers: this.headers,
                body: JSON.stringify(data)
            }
        );
        return response.json();
    }
}

// Usage example
const api = new HealthMateAPI('https://api.healthmate.com/v2', 'your_jwt_token');

// Get health data
const healthData = await api.getHealthData({
    data_type: 'blood_pressure',
    start_date: '2024-01-01',
    end_date: '2024-01-16'
});

// Create new health data
const newData = await api.createHealthData({
    data_type: 'heart_rate',
    value: 75,
    unit: 'bpm',
    notes: 'After morning walk'
});

// Send chat message
const chatResponse = await api.sendChatMessage('What are the symptoms of diabetes?');
```

## 🛠️ Troubleshooting

### Common Issues

#### 1. Authentication Errors

**Problem**: `401 Unauthorized` errors

**Solutions**:
- Check if JWT token is valid and not expired
- Ensure token is included in Authorization header
- Refresh token if expired
- Verify user account is active

#### 2. Rate Limiting

**Problem**: `429 Too Many Requests` errors

**Solutions**:
- Implement exponential backoff
- Check rate limit headers
- Reduce request frequency
- Use bulk endpoints when available

#### 3. Validation Errors

**Problem**: `422 Validation Error` responses

**Solutions**:
- Check request body format
- Verify required fields are present
- Ensure data types are correct
- Review validation error details

#### 4. Compliance Violations

**Problem**: `403 Forbidden` with compliance errors

**Solutions**:
- Check user permissions
- Verify data access rights
- Ensure compliance requirements are met
- Contact support for compliance issues

### Error Recovery

#### Token Refresh Flow

```python
def refresh_token_if_needed(api_client, response):
    if response.status_code == 401:
        try:
            refresh_response = api_client.refresh_token()
            if refresh_response['success']:
                api_client.update_token(refresh_response['data']['access_token'])
                return True
        except Exception as e:
            print(f"Token refresh failed: {e}")
    return False
```

#### Retry Logic

```python
import time
from requests.exceptions import RequestException

def api_request_with_retry(api_client, method, endpoint, data=None, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = api_client.request(method, endpoint, data)
            return response
        except RequestException as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(2 ** attempt)  # Exponential backoff
```

### Support

For additional support:

- **Documentation**: `/docs` (Swagger UI)
- **API Status**: `/system/health`
- **Support Email**: support@healthmate.com
- **Developer Portal**: https://developers.healthmate.com

---

**Last Updated**: January 16, 2024  
**API Version**: 2.0.0  
**Documentation Version**: 1.0.0 
# HealthMate Developer Guide

## 🏥 HealthMate Development Documentation

This guide provides comprehensive documentation for developers working on the HealthMate application, including architecture overview, authentication system, API documentation, and development best practices.

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Authentication System](#authentication-system)
3. [Frontend Architecture](#frontend-architecture)
4. [Backend Integration](#backend-integration)
5. [API Documentation](#api-documentation)
6. [Development Setup](#development-setup)
7. [Testing Framework](#testing-framework)
8. [Deployment Guide](#deployment-guide)
9. [Contributing Guidelines](#contributing-guidelines)
10. [Troubleshooting](#troubleshooting)

## 🏗️ Architecture Overview

### System Architecture

HealthMate follows a modern web application architecture with clear separation of concerns:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   Database      │
│   (Streamlit)   │◄──►│   (FastAPI)     │◄──►│   (PostgreSQL)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └──────────────►│   AI Services   │◄─────────────┘
                        │   (OpenAI)      │
                        └─────────────────┘
```

### Technology Stack

#### Frontend
- **Framework**: Streamlit (Python)
- **State Management**: Streamlit Session State
- **UI Components**: Custom Streamlit components
- **Styling**: Custom CSS with responsive design
- **Authentication**: JWT-based token management

#### Backend
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT tokens with refresh mechanism
- **API Documentation**: OpenAPI/Swagger
- **Validation**: Pydantic models

#### Infrastructure
- **Containerization**: Docker
- **Database Migrations**: Alembic
- **Testing**: pytest with comprehensive test suite
- **Version Control**: Git with structured branching

## 🔐 Authentication System

### Unified Authentication Architecture

HealthMate implements a centralized authentication system that provides secure, seamless access across all features.

#### Authentication Manager (`auth_manager.py`)

```python
class AuthManager:
    """Centralized authentication manager for HealthMate application"""
    
    def __init__(self):
        self.api_base_url = "http://localhost:8000"
        self.session_timeout_minutes = 60
        self._initialize_session_state()
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated and session is valid"""
    
    def login(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate user with email and password"""
    
    def logout(self):
        """Logout user and clear all authentication state"""
    
    def refresh_session(self) -> bool:
        """Refresh the current session if possible"""
```

#### Session State Management

The authentication manager initializes and manages comprehensive session state:

```python
auth_vars = {
    'authenticated': False,
    'token': None,
    'user_email': None,
    'user_id': None,
    'login_time': None,
    'last_login': None,
    'session_expires_at': None,
    'user_profile': {},
    'permissions': [],
    'auth_error': None,
    'auth_message': None,
    'auth_message_type': 'info'
}
```

#### Authentication Flow

1. **Registration Flow**
   ```python
   # User registration with validation
   result = auth_manager.register(email, password, full_name)
   if result["success"]:
       # User automatically logged in after registration
       redirect_to_dashboard()
   ```

2. **Login Flow**
   ```python
   # User login with credential validation
   result = auth_manager.login(email, password)
   if result["success"]:
       # Set authentication state and redirect
       set_auth_state(result["data"])
       redirect_to_dashboard()
   ```

3. **Session Management**
   ```python
   # Automatic session validation
   if not auth_manager.is_authenticated():
       redirect_to_login()
   
   # Session refresh for active users
   if session_needs_refresh():
       auth_manager.refresh_session()
   ```

### Session Management

#### Session Manager (`session_manager.py`)

```python
class SessionManager:
    """Manages user sessions with timeout and refresh capabilities"""
    
    def __init__(self, auth_manager, timeout_minutes: int = 60, warning_minutes: int = 5):
        self.auth_manager = auth_manager
        self.timeout_minutes = timeout_minutes
        self.warning_minutes = warning_minutes
    
    def check_session_status(self) -> dict:
        """Check current session status"""
    
    def handle_session_timeout(self):
        """Handle session timeout and show appropriate UI"""
    
    def setup_session_monitoring(self):
        """Setup session monitoring and automatic refresh"""
```

#### Session Middleware

```python
class SessionMiddleware:
    """Middleware for automatic session management"""
    
    def process_request(self):
        """Process each request for session management"""
    
    def display_session_ui(self):
        """Display session-related UI elements"""
```

## 🎨 Frontend Architecture

### Streamlit Application Structure

```
frontend/
├── streamlit_app.py          # Main application entry point
├── utils/
│   ├── __init__.py
│   ├── auth_manager.py       # Authentication management
│   └── session_manager.py    # Session management
├── components/
│   ├── __init__.py
│   ├── chat_interface.py     # Chat UI components
│   ├── health_metrics.py     # Metrics tracking components
│   ├── health_profile.py     # Profile management components
│   ├── reports.py           # Report generation components
│   └── settings.py          # Settings management components
├── styles/
│   ├── main.css             # Main stylesheet
│   ├── components.css       # Component-specific styles
│   └── dashboard.css        # Dashboard layout styles
└── docs/
    ├── user_guide.md        # User documentation
    ├── developer_guide.md   # Developer documentation
    └── api_documentation.md # API documentation
```

### Main Application (`streamlit_app.py`)

```python
import streamlit as st
from utils.auth_manager import auth_manager
from utils.session_manager import initialize_session_manager

# Initialize session manager
session_manager, session_middleware = initialize_session_manager(auth_manager)

def main():
    # Process session management middleware
    session_middleware.process_request()
    
    # Check authentication using auth manager
    if not auth_manager.is_authenticated():
        show_login_page()
        return
    
    # Main dashboard for authenticated users
    show_dashboard()

if __name__ == "__main__":
    main()
```

### Component Architecture

#### Modular Component Design

Each feature is implemented as a modular component with clear interfaces:

```python
def show_chat_interface():
    """Display the AI chat interface"""
    st.markdown("## 💬 AI Health Assistant")
    
    # Chat input and display logic
    user_input = st.text_input("Ask your health question:")
    if user_input:
        response = send_message(user_input)
        display_chat_response(response)

def show_health_metrics():
    """Display health metrics tracking interface"""
    st.markdown("## 📊 Health Metrics")
    
    # Metrics tracking and visualization
    metric_type = st.selectbox("Select Metric", ["Weight", "Blood Pressure", "Heart Rate"])
    display_metric_tracker(metric_type)
```

#### State Management

Components use Streamlit session state for data persistence:

```python
# Initialize component state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'health_metrics' not in st.session_state:
    st.session_state.health_metrics = {}

# Component state management
def update_chat_history(message, response):
    st.session_state.chat_history.append({
        'user': message,
        'assistant': response,
        'timestamp': datetime.now()
    })
```

## 🔌 Backend Integration

### API Integration

#### HTTP Client Configuration

```python
import requests
from typing import Dict, Any

class APIClient:
    def __init__(self, base_url: str, auth_manager):
        self.base_url = base_url
        self.auth_manager = auth_manager
    
    def _get_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        if self.auth_manager.is_authenticated():
            return {"Authorization": f"Bearer {st.session_state.token}"}
        return {}
    
    def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make authenticated POST request"""
        headers = self._get_headers()
        response = requests.post(
            f"{self.base_url}{endpoint}",
            json=data,
            headers=headers,
            timeout=30
        )
        return self._handle_response(response)
```

#### Error Handling

```python
def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
    """Handle API response with error management"""
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 401:
        # Token expired, try to refresh
        if self.auth_manager.refresh_session():
            # Retry with new token
            return self._retry_request(response.request)
        else:
            # Authentication failed
            self.auth_manager.logout()
            return {"error": "Authentication failed"}
    else:
        return {"error": f"API Error: {response.status_code}"}
```

### Data Models

#### Pydantic Models for API Communication

```python
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class UserProfile(BaseModel):
    user_id: int
    email: str
    full_name: Optional[str] = None
    age: Optional[int] = None
    created_at: datetime

class HealthMetric(BaseModel):
    metric_type: str
    value: float
    unit: str
    date: datetime
    notes: Optional[str] = None

class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[int] = None
    timestamp: datetime = datetime.now()
```

## 📚 API Documentation

### Authentication Endpoints

#### POST `/auth/register`
Register a new user account.

**Request Body:**
```json
{
    "email": "user@example.com",  # pragma: allowlist secret
    "password": "securepassword123",  # pragma: allowlist secret
    "full_name": "John Doe"
}
```

**Response:**
```json
{
    "success": true,
    "access_token": "jwt_token_here",
    "email": "user@example.com",
    "user_id": 1,
    "user_profile": {
        "full_name": "John Doe"
    },
    "permissions": ["read", "write"]
}
```

#### POST `/auth/login`
Authenticate existing user.

**Request Body:**
```json
{
    "email": "user@example.com",  # pragma: allowlist secret
    "password": "securepassword123"  # pragma: allowlist secret
}
```

**Response:**
```json
{
    "success": true,
    "access_token": "jwt_token_here",
    "email": "user@example.com",
    "user_id": 1,
    "permissions": ["read", "write", "admin"]
}
```

#### POST `/auth/forgot-password`
Request password reset.

**Request Body:**
```json
{
    "email": "user@example.com"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Password reset email sent"
}
```

#### POST `/auth/reset-password`
Reset password using token.

**Request Body:**
```json
{
    "token": "reset_token_here",  # pragma: allowlist secret
    "new_password": "newsecurepassword123"  # pragma: allowlist secret
}
```

**Response:**
```json
{
    "success": true,
    "message": "Password reset successful"
}
```

### Chat Endpoints

#### POST `/chat/message`
Send message to AI assistant.

**Request Body:**
```json
{
    "message": "What are the symptoms of diabetes?"
}
```

**Response:**
```json
{
    "response": "Diabetes symptoms include increased thirst, frequent urination, and fatigue...",
    "conversation_id": 123,
    "timestamp": "2024-01-16T10:00:00Z"
}
```

#### GET `/chat/history`
Retrieve chat conversation history.

**Response:**
```json
[
    {
        "conversation_id": 123,
        "messages": [
            {
                "role": "user",
                "content": "What are the symptoms of diabetes?",
                "timestamp": "2024-01-16T10:00:00Z"
            },
            {
                "role": "assistant",
                "content": "Diabetes symptoms include...",
                "timestamp": "2024-01-16T10:00:05Z"
            }
        ]
    }
]
```

### Health Metrics Endpoints

#### POST `/health/metrics`
Add new health metric.

**Request Body:**
```json
{
    "metric_type": "weight",
    "value": 70.5,
    "unit": "kg",
    "date": "2024-01-16",
    "notes": "Morning weight"
}
```

#### GET `/health/metrics`
Retrieve health metrics.

**Query Parameters:**
- `metric_type`: Type of metric to retrieve
- `start_date`: Start date for range
- `end_date`: End date for range

**Response:**
```json
[
    {
        "id": 1,
        "metric_type": "weight",
        "value": 70.5,
        "unit": "kg",
        "date": "2024-01-16",
        "notes": "Morning weight"
    }
]
```

## 🛠️ Development Setup

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Git
- Docker (optional)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/healthmate.git
   cd healthmate
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**
   ```bash
   alembic upgrade head
   ```

6. **Start the backend server**
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

7. **Start the frontend application**
   ```bash
   cd frontend
   streamlit run streamlit_app.py
   ```

### Development Environment

#### Environment Variables

```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost/healthmate  # pragma: allowlist secret

# Authentication
SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# API Configuration
API_BASE_URL=http://localhost:8000

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key

# Email Configuration (for password reset)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

#### Development Tools

- **Code Formatting**: Black, isort
- **Linting**: flake8, pylint
- **Type Checking**: mypy
- **Testing**: pytest
- **Documentation**: Sphinx

## 🧪 Testing Framework

### Test Structure

```
tests/
├── test_unified_auth.py           # Authentication tests
├── test_post_login_flow.py        # Post-login flow tests
├── test_end_to_end_flow.py        # End-to-end tests
├── test_dashboard_features.py     # Dashboard feature tests
├── test_navigation_ui.py          # Navigation and UI tests
├── test_integration_refactoring.py # Integration tests
└── test_comprehensive_validation.py # Comprehensive validation tests
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_unified_auth.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=frontend --cov-report=html

# Run specific test class
pytest tests/test_unified_auth.py::TestUnifiedAuth

# Run specific test method
pytest tests/test_unified_auth.py::TestUnifiedAuth::test_register_user_success
```

### Test Categories

#### Authentication Tests
- User registration and validation
- Login and logout functionality
- Password reset flow
- Session management
- Token refresh

#### Integration Tests
- API integration testing
- Database operations
- Error handling
- Performance testing

#### UI/UX Tests
- Navigation functionality
- Component rendering
- User interaction testing
- Accessibility testing

#### End-to-End Tests
- Complete user workflows
- Cross-feature integration
- Data persistence
- Error recovery

### Mock Testing

```python
from unittest.mock import patch, MagicMock

def test_api_integration():
    """Test API integration with mocked responses"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"success": True}
    
    with patch('requests.post', return_value=mock_response):
        result = api_client.send_message("test message")
        assert result["success"] == True
```

## 🚀 Deployment Guide

### Production Deployment

#### Docker Deployment

1. **Build Docker images**
   ```bash
   docker build -t healthmate-frontend ./frontend
   docker build -t healthmate-backend ./backend
   ```

2. **Run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

#### Environment Configuration

```bash
# Production environment variables
DATABASE_URL=postgresql://user:password@prod-db/healthmate  # pragma: allowlist secret
SECRET_KEY=production-secret-key
DEBUG=False
LOG_LEVEL=INFO
```

#### Database Migration

```bash
# Run database migrations
alembic upgrade head

# Create database backup
pg_dump healthmate > backup.sql
```

### Monitoring and Logging

#### Application Logging

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('healthmate.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
```

#### Health Checks

```python
@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "version": "2.0.0"
    }
```

## 🤝 Contributing Guidelines

### Development Workflow

1. **Create feature branch**
   ```bash
   git checkout -b feature/new-feature
   ```

2. **Make changes and test**
   ```bash
   # Make your changes
   pytest  # Run tests
   black .  # Format code
   flake8   # Lint code
   ```

3. **Commit changes**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

4. **Create pull request**
   - Provide clear description
   - Include tests
   - Update documentation

### Code Standards

#### Python Code Style

- Follow PEP 8 guidelines
- Use type hints
- Write docstrings for functions
- Keep functions small and focused

#### Frontend Standards

- Use consistent naming conventions
- Implement proper error handling
- Ensure accessibility compliance
- Write comprehensive tests

#### Documentation Standards

- Update user documentation for new features
- Document API changes
- Include code examples
- Maintain version history

### Review Process

1. **Code Review Checklist**
   - [ ] Code follows style guidelines
   - [ ] Tests are included and passing
   - [ ] Documentation is updated
   - [ ] Security considerations addressed
   - [ ] Performance impact assessed

2. **Testing Requirements**
   - [ ] Unit tests for new functionality
   - [ ] Integration tests for API changes
   - [ ] End-to-end tests for user flows
   - [ ] Accessibility testing for UI changes

## 🐛 Troubleshooting

### Common Issues

#### Authentication Issues

**Problem**: Users can't log in
**Debugging Steps**:
1. Check database connection
2. Verify JWT token configuration
3. Check password hashing
4. Review authentication logs

**Solution**:
```python
# Enable debug logging
logging.getLogger('auth').setLevel(logging.DEBUG)
```

#### Session Management Issues

**Problem**: Sessions expiring unexpectedly
**Debugging Steps**:
1. Check session timeout configuration
2. Verify session state management
3. Review session refresh logic
4. Check browser cookie settings

**Solution**:
```python
# Adjust session timeout
session_manager = SessionManager(auth_manager, timeout_minutes=120)
```

#### API Integration Issues

**Problem**: API calls failing
**Debugging Steps**:
1. Check API endpoint availability
2. Verify authentication headers
3. Review network connectivity
4. Check API response format

**Solution**:
```python
# Add request logging
import requests
import logging

logging.getLogger('urllib3').setLevel(logging.DEBUG)
```

### Performance Optimization

#### Frontend Optimization

```python
# Optimize Streamlit performance
st.set_page_config(
    page_title="HealthMate Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Use caching for expensive operations
@st.cache_data
def fetch_user_data(user_id):
    return api_client.get_user_data(user_id)
```

#### Database Optimization

```sql
-- Add indexes for frequently queried columns
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_health_metrics_user_date ON health_metrics(user_id, date);
CREATE INDEX idx_chat_messages_user_id ON chat_messages(user_id);
```

### Security Considerations

#### Input Validation

```python
from pydantic import BaseModel, validator

class UserInput(BaseModel):
    email: str
    password: str
    
    @validator('email')
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email format')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password too short')
        return v
```

#### SQL Injection Prevention

```python
# Use parameterized queries
def get_user_by_email(email: str):
    query = "SELECT * FROM users WHERE email = %s"
    return db.execute(query, (email,))
```

---

## 📄 Version Information

**HealthMate Developer Guide v2.0**
- **Last Updated**: January 2024
- **Compatible Version**: HealthMate Dashboard v2.0
- **Documentation Status**: Complete and Current

For the most up-to-date information, please visit our official documentation website or contact the development team.

---

*This developer guide is designed to help developers understand and contribute to the HealthMate application. For additional support, please contact the development team or refer to the project's issue tracker.* 
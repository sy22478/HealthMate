# HealthMate Testing Guide

This guide provides comprehensive information about the testing framework for the HealthMate application, including setup, usage, and best practices.

## Table of Contents

1. [Overview](#overview)
2. [Test Structure](#test-structure)
3. [Setup and Installation](#setup-and-installation)
4. [Running Tests](#running-tests)
5. [Test Types](#test-types)
6. [Writing Tests](#writing-tests)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

## Overview

The HealthMate testing framework is built on pytest and provides comprehensive testing capabilities for:
- Unit tests for individual components
- Integration tests for API workflows
- Database testing with isolated test databases
- Mocked external services
- Coverage reporting

## Test Structure

```
tests/
├── conftest.py                 # Pytest configuration and fixtures
├── test_auth_services.py       # Authentication service tests
├── test_database_models.py     # Database model tests
├── test_utility_functions.py   # Utility function tests
├── test_integration_api.py     # API integration tests
└── test_*.py                   # Other test modules
```

## Setup and Installation

### Prerequisites

- Python 3.12+
- pip
- Docker (optional, for containerized testing)

### Installation

1. **Install test dependencies:**
   ```bash
   pip install pytest pytest-cov pytest-xdist pytest-asyncio httpx coverage
   ```

2. **Setup test environment:**
   ```bash
   # Create test database
   python -c "from app.database import Base, engine; Base.metadata.create_all(bind=engine)"
   ```

3. **Verify installation:**
   ```bash
   pytest --version
   ```

## Running Tests

### Using the Test Runner Script

The easiest way to run tests is using the provided test runner script:

```bash
# Run all tests
./scripts/run_tests.sh all

# Run unit tests only
./scripts/run_tests.sh unit

# Run integration tests only
./scripts/run_tests.sh integration

# Run tests with coverage
./scripts/run_tests.sh coverage

# Run tests in Docker
./scripts/run_tests.sh docker

# Clean up test artifacts
./scripts/run_tests.sh clean
```

### Using pytest Directly

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_auth_services.py

# Run specific test class
pytest tests/test_auth_services.py::TestAuthService

# Run specific test method
pytest tests/test_auth_services.py::TestAuthService::test_password_hashing

# Run tests with markers
pytest -m "unit"
pytest -m "integration"

# Run tests with coverage
pytest --cov=app --cov-report=html:htmlcov

# Run tests in parallel
pytest -n auto
```

### Using Docker

```bash
# Run tests in Docker containers
docker-compose -f docker-compose.test.yml up --build

# Run specific test in Docker
docker-compose -f docker-compose.test.yml run test-app pytest tests/test_auth_services.py
```

## Test Types

### 1. Unit Tests

Unit tests focus on testing individual components in isolation.

**Location:** `tests/test_*.py` files
**Markers:** `@pytest.mark.unit`

**Example:**
```python
@pytest.mark.unit
def test_password_hashing(auth_service):
    """Test password hashing functionality."""
    password = "TestPassword123!"
    hashed = auth_service.get_password_hash(password)
    assert auth_service.verify_password(password, hashed) is True
```

### 2. Integration Tests

Integration tests verify that multiple components work together correctly.

**Location:** `tests/test_integration_*.py` files
**Markers:** `@pytest.mark.integration`

**Example:**
```python
@pytest.mark.integration
def test_user_registration_workflow(client):
    """Test complete user registration workflow."""
    registration_data = {
        "email": "newuser@example.com",
        "password": "StrongPassword123!",
        "full_name": "New Test User",
        "age": 25,
        "medical_conditions": "None",
        "medications": "None",
        "role": "patient"
    }
    
    response = client.post("/auth/register", json=registration_data)
    assert response.status_code == 200
```

### 3. Database Tests

Database tests verify database operations and data integrity.

**Fixtures:** `db_session`, `sample_user`, `sample_health_record`

**Example:**
```python
def test_create_user(db_session):
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
```

## Writing Tests

### Test File Structure

```python
"""
Test module description.

This module tests [specific functionality].
"""

import pytest
from unittest.mock import Mock, patch

class TestClassName:
    """Test cases for [Class/Function]."""
    
    def test_specific_functionality(self, fixture_name):
        """Test description."""
        # Arrange
        # Act
        # Assert
        pass
```

### Using Fixtures

Fixtures are defined in `conftest.py` and provide reusable test data and setup.

**Available Fixtures:**
- `client`: FastAPI test client
- `db_session`: Database session
- `auth_service`: Authentication service instance
- `sample_user`: Sample user in database
- `admin_user`: Admin user in database
- `authenticated_client`: Test client with authenticated user
- `admin_client`: Test client with authenticated admin
- `sample_health_record`: Sample health data record
- `mock_redis`: Mocked Redis client
- `mock_openai`: Mocked OpenAI client

**Example:**
```python
def test_authenticated_endpoint(authenticated_client, sample_user):
    """Test endpoint that requires authentication."""
    response = authenticated_client.get("/auth/me")
    assert response.status_code == 200
    assert response.json()["email"] == sample_user.email
```

### Mocking External Services

Use the `unittest.mock` library to mock external services:

```python
def test_external_api_call(mock_openai):
    """Test external API integration."""
    with patch('app.services.openai_agent.openai') as mock_openai:
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test response"
        mock_openai.ChatCompletion.create.return_value = mock_response
        
        # Test your code here
        pass
```

### Testing API Endpoints

Use the FastAPI test client to test API endpoints:

```python
def test_api_endpoint(client):
    """Test API endpoint."""
    # GET request
    response = client.get("/health/bmi")
    assert response.status_code == 200
    
    # POST request with JSON
    data = {"weight_kg": 70, "height_m": 1.75}
    response = client.post("/health/bmi", json=data)
    assert response.status_code == 200
    assert "bmi" in response.json()
```

## Best Practices

### 1. Test Organization

- Group related tests in classes
- Use descriptive test method names
- Follow the Arrange-Act-Assert pattern
- Keep tests independent and isolated

### 2. Test Data

- Use fixtures for reusable test data
- Create realistic test data
- Clean up test data after tests
- Use factories for complex test objects

### 3. Assertions

- Use specific assertions
- Test both positive and negative cases
- Verify error conditions
- Check response structure and content

### 4. Performance

- Keep tests fast
- Use appropriate mocking
- Avoid unnecessary database operations
- Use parallel execution when possible

### 5. Coverage

- Aim for high test coverage
- Focus on critical paths
- Test edge cases and error conditions
- Regularly review coverage reports

## Test Configuration

### pytest.ini

The `pytest.ini` file contains test configuration:

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --color=yes
    --durations=10
    --maxfail=5
    --cov=app
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-report=xml
    --cov-fail-under=80
    -n auto

markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
    auth: Authentication related tests
    health: Health data related tests
    chat: Chat/AI related tests
    security: Security related tests
    database: Database related tests
    api: API endpoint tests
    utils: Utility function tests
```

### Environment Variables

Test-specific environment variables:

```bash
TESTING=true
DATABASE_URL=sqlite:///./test.db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=test-secret-key-for-testing-only
```

## Coverage Reporting

### Running Coverage

```bash
# Generate coverage report
pytest --cov=app --cov-report=html:htmlcov --cov-report=xml

# View coverage in terminal
pytest --cov=app --cov-report=term-missing
```

### Coverage Reports

- **HTML Report:** `htmlcov/index.html`
- **XML Report:** `coverage.xml`
- **Terminal Report:** Shows missing lines

### Coverage Thresholds

- Minimum coverage: 80%
- Critical modules: 90%+
- New code: 90%+

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   ```bash
   # Recreate test database
   rm test.db
   python -c "from app.database import Base, engine; Base.metadata.create_all(bind=engine)"
   ```

2. **Import Errors**
   ```bash
   # Check Python path
   export PYTHONPATH=/path/to/healthchat-rag
   ```

3. **Fixture Errors**
   ```bash
   # Check fixture dependencies
   pytest --setup-show tests/
   ```

4. **Mock Errors**
   ```bash
   # Verify mock setup
   pytest -s tests/test_with_mocks.py
   ```

### Debug Mode

Run tests in debug mode for more information:

```bash
pytest -s -v --tb=long tests/
```

### Verbose Output

```bash
pytest -v --tb=short tests/
```

## Continuous Integration

### GitHub Actions

The testing framework is designed to work with CI/CD pipelines:

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.12
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v1
```

## Contributing

When adding new tests:

1. Follow the existing test structure
2. Use appropriate markers
3. Add comprehensive docstrings
4. Ensure tests are independent
5. Update this documentation if needed

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/14/orm/session_transaction.html#joining-a-session-into-an-external-transaction)
- [Python Mocking](https://docs.python.org/3/library/unittest.mock.html) 
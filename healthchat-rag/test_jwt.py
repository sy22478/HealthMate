#!/usr/bin/env python3

from app.utils.jwt_utils import jwt_manager
from app.config import settings

# Test token from the login response
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0QGV4YW1wbGUuY29tIiwidXNlcl9pZCI6MSwiZW1haWwiOiJ0ZXN0QGV4YW1wbGUuY29tIiwicm9sZSI6InBhdGllbnQiLCJleHAiOjE3NTM1Nzg3NjIsImlhdCI6MTc1MzU3Njk2MiwibmJmIjoxNzUzNTc2OTYyLCJ0eXBlIjoiYWNjZXNzIiwianRpIjoiOTI0MGVjZTMtZDRkYy00M2ZjLWE3Y2QtMjgzYzU4NmQ2ZWUyIiwiaXNzIjoiaGVhbHRobWF0ZSIsImF1ZCI6ImhlYWx0aG1hdGVfdXNlcnMiLCJmaW5nZXJwcmludCI6ImNjM2YyMDA5NTM0MTFkNWYifQ.iEOpgayXLdX_6awyR-akceWI1_xepha4kOQ84QEl6do"

print("Testing JWT token validation...")
print(f"Secret key: {settings.secret_key[:10]}...")
print(f"JWT manager initialized: {jwt_manager is not None}")

try:
    payload = jwt_manager.verify_token(token, "access")
    print("✅ Token is valid!")
    print(f"Payload: {payload}")
except Exception as e:
    print(f"❌ Token validation failed: {e}")
    print(f"Error type: {type(e)}") 
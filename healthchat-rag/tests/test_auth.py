import pytest
from app.services.auth import AuthService
import re

SECRET = "testsecretkey"  # pragma: allowlist secret
auth_service = AuthService(SECRET)

def test_password_hash_and_verify():
    password = "mysecurepassword"  # pragma: allowlist secret
    hashed = auth_service.get_password_hash(password)
    assert hashed != password
    assert auth_service.verify_password(password, hashed)
    assert not auth_service.verify_password("wrongpassword", hashed)

def test_create_access_token():
    data = {"sub": "user@example.com", "user_id": 1}
    token = auth_service.create_access_token(data)
    assert isinstance(token, str)
    # JWTs are three parts separated by dots
    assert len(token.split(".")) == 3 
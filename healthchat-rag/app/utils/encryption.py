from cryptography.fernet import Fernet
import base64
import os

class EncryptionManager:
    def __init__(self, key: str):
        # Key must be 32 url-safe base64-encoded bytes
        if not key:
            raise ValueError("ENCRYPTION_KEY is required")
        self.fernet = Fernet(key)

    def encrypt(self, data: str) -> str:
        if data is None:
            return None
        return self.fernet.encrypt(data.encode()).decode()

    def decrypt(self, token: str) -> str:
        if token is None:
            return None
        try:
            return self.fernet.decrypt(token.encode()).decode()
        except Exception:
            return "[decryption error]" 
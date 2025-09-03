"""
Vector Store Exceptions for HealthMate Application
"""

from .base_exceptions import HealthMateException, ErrorCode

class VectorStoreError(HealthMateException):
    """Exception raised for errors related to the vector store."""

    def __init__(self, message: str = "Vector store operation failed"):
        super().__init__(
            message=message,
            error_code=ErrorCode.VECTOR_STORE_ERROR,
            status_code=500
        )

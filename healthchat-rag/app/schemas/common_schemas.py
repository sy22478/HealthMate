"""
Common Pydantic Schemas
Shared schemas for error handling, success responses, and pagination
"""
from typing import Any, Dict, List, Optional, TypeVar, Generic
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
from enum import Enum

class ErrorCode(str, Enum):
    """Standard error codes for the API"""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    EXTERNAL_API_ERROR = "EXTERNAL_API_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"

class ErrorResponse(BaseModel):
    """Standard error response schema"""
    error: bool = Field(default=True, description="Always true for error responses")
    code: ErrorCode = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    request_id: Optional[str] = Field(default=None, description="Request ID for tracking")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "error": True,
                "code": "VALIDATION_ERROR",
                "message": "Invalid input data",
                "details": {
                    "field": "email",
                    "issue": "Invalid email format"
                },
                "timestamp": "2024-01-01T12:00:00Z",
                "request_id": "req_123456"
            }
        }
    )

class SuccessResponse(BaseModel):
    """Standard success response schema"""
    success: bool = Field(default=True, description="Always true for success responses")
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "data": {"id": 123, "status": "created"},
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }
    )

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response schema"""
    items: List[T] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Number of items per page")
    pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")

    @field_validator('pages')
    def calculate_pages(cls, v, values):
        """Calculate total pages based on total items and page size"""
        if 'total' in values and 'size' in values:
            return (values['total'] + values['size'] - 1) // values['size']
        return v

    @field_validator('has_next')
    def calculate_has_next(cls, v, values):
        """Calculate if there is a next page"""
        if 'page' in values and 'pages' in values:
            return values['page'] < values['pages']
        return v

    @field_validator('has_prev')
    def calculate_has_prev(cls, v, values):
        """Calculate if there is a previous page"""
        if 'page' in values:
            return values['page'] > 1
        return v

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 100,
                "page": 1,
                "size": 10,
                "pages": 10,
                "has_next": True,
                "has_prev": False
            }
        }
    )

class HealthStatus(BaseModel):
    """Health check response schema"""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")
    version: str = Field(..., description="API version")
    uptime: float = Field(..., description="Service uptime in seconds")
    dependencies: Dict[str, str] = Field(default_factory=dict, description="Dependency status")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2024-01-01T12:00:00Z",
                "version": "1.0.0",
                "uptime": 3600.5,
                "dependencies": {
                    "database": "healthy",
                    "redis": "healthy",
                    "external_api": "healthy"
                }
            }
        }
    )

class SearchQuery(BaseModel):
    """Generic search query schema"""
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Search filters")
    sort_by: Optional[str] = Field(default=None, description="Sort field")
    sort_order: Optional[str] = Field(default="asc", pattern="^(asc|desc)$", description="Sort order")
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=10, ge=1, le=100, description="Page size")

    @field_validator('query')
    def validate_query(cls, v):
        """Validate and sanitize search query"""
        if not v.strip():
            raise ValueError("Search query cannot be empty")
        return v.strip()

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "query": "diabetes symptoms",
                "filters": {"category": "symptoms", "severity": "moderate"},
                "sort_by": "created_at",
                "sort_order": "desc",
                "page": 1,
                "size": 10
            }
        }
    )


class BulkOperation(BaseModel):
    """Bulk operation schema"""
    operation: str = Field(..., pattern="^(create|update|delete)$", description="Operation type")
    items: List[Dict[str, Any]] = Field(..., min_length=1, max_length=100, description="Items to process")
    batch_size: Optional[int] = Field(default=10, ge=1, le=50, description="Batch size for processing")

    @field_validator('items')
    def validate_items(cls, v):
        """Validate items list"""
        if not v:
            raise ValueError("Items list cannot be empty")
        return v

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "operation": "create",
                "items": [
                    {"name": "Item 1", "description": "Description 1"},
                    {"name": "Item 2", "description": "Description 2"}
                ],
                "batch_size": 10
            }
        }
    )


class ExportRequest(BaseModel):
    """Data export request schema"""
    format: str = Field(..., pattern="^(json|csv|pdf)$", description="Export format")
    date_from: Optional[datetime] = Field(default=None, description="Start date for export")
    date_to: Optional[datetime] = Field(default=None, description="End date for export")
    fields: Optional[List[str]] = Field(default=None, description="Fields to include in export")
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Export filters")

    @field_validator('date_to')
    def validate_date_range(cls, v, values):
        """Validate date range"""
        if v and 'date_from' in values and values['date_from']:
            if v < values['date_from']:
                raise ValueError("End date must be after start date")
        return v

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "format": "csv",
                "date_from": "2024-01-01T00:00:00Z",
                "date_to": "2024-01-31T23:59:59Z",
                "fields": ["id", "name", "created_at"],
                "filters": {"status": "active"}
            }
        }
    )
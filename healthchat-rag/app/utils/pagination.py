"""
Pagination utilities for API responses.

This module provides pagination functionality for handling large datasets
in API responses efficiently.
"""

from typing import List, Dict, Any, Optional, TypeVar, Generic
from math import ceil
from fastapi import Query, HTTPException, status
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')

class PaginationParams(BaseModel):
    """Pagination parameters model."""
    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    size: int = Field(default=20, ge=1, le=100, description="Items per page (max 100)")
    offset: Optional[int] = Field(default=None, ge=0, description="Offset for cursor-based pagination")

class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response model."""
    items: List[T] = Field(description="List of items")
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number")
    size: int = Field(description="Items per page")
    pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_prev: bool = Field(description="Whether there is a previous page")
    next_page: Optional[int] = Field(default=None, description="Next page number")
    prev_page: Optional[int] = Field(default=None, description="Previous page number")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

def get_pagination_params(
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    size: int = Query(default=20, ge=1, le=100, description="Items per page (max 100)"),
    offset: Optional[int] = Query(default=None, ge=0, description="Offset for cursor-based pagination")
) -> PaginationParams:
    """
    Get pagination parameters from query parameters.
    
    Args:
        page: Page number (1-based)
        size: Items per page (max 100)
        offset: Offset for cursor-based pagination
        
    Returns:
        Pagination parameters
    """
    return PaginationParams(page=page, size=size, offset=offset)

def paginate_response(
    items: List[T],
    total: int,
    page: int,
    size: int,
    metadata: Optional[Dict[str, Any]] = None
) -> PaginatedResponse[T]:
    """
    Create a paginated response.
    
    Args:
        items: List of items for current page
        total: Total number of items
        page: Current page number
        size: Items per page
        metadata: Additional metadata
        
    Returns:
        Paginated response
    """
    pages = ceil(total / size) if total > 0 else 0
    has_next = page < pages
    has_prev = page > 1
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages,
        has_next=has_next,
        has_prev=has_prev,
        next_page=page + 1 if has_next else None,
        prev_page=page - 1 if has_prev else None,
        metadata=metadata or {}
    )

def apply_pagination(
    query,
    pagination: PaginationParams,
    order_by: Optional[str] = None,
    order_direction: str = "asc"
) -> tuple:
    """
    Apply pagination to a SQLAlchemy query.
    
    Args:
        query: SQLAlchemy query
        pagination: Pagination parameters
        order_by: Column to order by
        order_direction: Order direction (asc/desc)
        
    Returns:
        Tuple of (paginated_query, total_count)
    """
    # Get total count
    total = query.count()
    
    # Apply ordering if specified
    if order_by:
        if order_direction.lower() == "desc":
            query = query.order_by(getattr(query.column_descriptions[0]['type'], order_by).desc())
        else:
            query = query.order_by(getattr(query.column_descriptions[0]['type'], order_by).asc())
    
    # Apply pagination
    offset = (pagination.page - 1) * pagination.size
    paginated_query = query.offset(offset).limit(pagination.size)
    
    return paginated_query, total

def create_pagination_links(
    base_url: str,
    page: int,
    pages: int,
    size: int,
    **query_params
) -> Dict[str, Optional[str]]:
    """
    Create pagination links for HATEOAS.
    
    Args:
        base_url: Base URL for the API endpoint
        page: Current page number
        pages: Total number of pages
        size: Items per page
        **query_params: Additional query parameters
        
    Returns:
        Dictionary of pagination links
    """
    links = {
        "self": None,
        "first": None,
        "last": None,
        "next": None,
        "prev": None
    }
    
    # Build query parameters
    params = {**query_params, "page": page, "size": size}
    query_string = "&".join([f"{k}={v}" for k, v in params.items() if v is not None])
    
    # Self link
    links["self"] = f"{base_url}?{query_string}"
    
    # First page
    first_params = {**query_params, "page": 1, "size": size}
    first_query = "&".join([f"{k}={v}" for k, v in first_params.items() if v is not None])
    links["first"] = f"{base_url}?{first_query}"
    
    # Last page
    if pages > 0:
        last_params = {**query_params, "page": pages, "size": size}
        last_query = "&".join([f"{k}={v}" for k, v in last_params.items() if v is not None])
        links["last"] = f"{base_url}?{last_query}"
    
    # Next page
    if page < pages:
        next_params = {**query_params, "page": page + 1, "size": size}
        next_query = "&".join([f"{k}={v}" for k, v in next_params.items() if v is not None])
        links["next"] = f"{base_url}?{next_query}"
    
    # Previous page
    if page > 1:
        prev_params = {**query_params, "page": page - 1, "size": size}
        prev_query = "&".join([f"{k}={v}" for k, v in prev_params.items() if v is not None])
        links["prev"] = f"{base_url}?{prev_query}"
    
    return links

def validate_pagination_params(page: int, size: int, max_size: int = 100) -> None:
    """
    Validate pagination parameters.
    
    Args:
        page: Page number
        size: Items per page
        max_size: Maximum items per page
        
    Raises:
        HTTPException: If parameters are invalid
    """
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page number must be greater than 0"
        )
    
    if size < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page size must be greater than 0"
        )
    
    if size > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Page size cannot exceed {max_size}"
        )

class CursorPagination:
    """Cursor-based pagination for better performance with large datasets."""
    
    def __init__(self, cursor_field: str = "id", direction: str = "desc"):
        """
        Initialize cursor pagination.
        
        Args:
            cursor_field: Field to use as cursor
            direction: Sort direction (asc/desc)
        """
        self.cursor_field = cursor_field
        self.direction = direction.lower()
    
    def apply_cursor_pagination(
        self,
        query,
        cursor: Optional[str] = None,
        limit: int = 20
    ) -> tuple:
        """
        Apply cursor-based pagination to query.
        
        Args:
            query: SQLAlchemy query
            cursor: Cursor value
            limit: Number of items to return
            
        Returns:
            Tuple of (paginated_query, has_more)
        """
        if cursor:
            cursor_field = getattr(query.column_descriptions[0]['type'], self.cursor_field)
            if self.direction == "desc":
                query = query.filter(cursor_field < cursor)
            else:
                query = query.filter(cursor_field > cursor)
        
        # Apply ordering
        cursor_field = getattr(query.column_descriptions[0]['type'], self.cursor_field)
        if self.direction == "desc":
            query = query.order_by(cursor_field.desc())
        else:
            query = query.order_by(cursor_field.asc())
        
        # Apply limit
        query = query.limit(limit + 1)  # Get one extra to check if there are more
        
        return query, limit
    
    def create_cursor_response(
        self,
        items: List[T],
        limit: int,
        cursor_field: str = "id"
    ) -> Dict[str, Any]:
        """
        Create cursor-based pagination response.
        
        Args:
            items: List of items
            limit: Requested limit
            cursor_field: Field used as cursor
            
        Returns:
            Cursor pagination response
        """
        has_more = len(items) > limit
        if has_more:
            items = items[:-1]  # Remove the extra item
        
        next_cursor = None
        if items and has_more:
            next_cursor = getattr(items[-1], cursor_field)
        
        return {
            "items": items,
            "next_cursor": next_cursor,
            "has_more": has_more,
            "limit": limit
        }

def optimize_pagination_query(query, pagination: PaginationParams) -> tuple:
    """
    Optimize pagination query for better performance.
    
    Args:
        query: SQLAlchemy query
        pagination: Pagination parameters
        
    Returns:
        Tuple of (optimized_query, total_count)
    """
    # Use subquery for better performance with large datasets
    subquery = query.subquery()
    
    # Count total using subquery
    from sqlalchemy import func
    total = query.session.query(func.count(subquery.c.id)).scalar()
    
    # Apply pagination to subquery
    offset = (pagination.page - 1) * pagination.size
    optimized_query = query.session.query(subquery).offset(offset).limit(pagination.size)
    
    return optimized_query, total

def create_pagination_metadata(
    page: int,
    size: int,
    total: int,
    processing_time_ms: Optional[float] = None
) -> Dict[str, Any]:
    """
    Create pagination metadata.
    
    Args:
        page: Current page number
        size: Items per page
        total: Total number of items
        processing_time_ms: Processing time in milliseconds
        
    Returns:
        Pagination metadata
    """
    pages = ceil(total / size) if total > 0 else 0
    
    metadata = {
        "pagination": {
            "page": page,
            "size": size,
            "total": total,
            "pages": pages,
            "has_next": page < pages,
            "has_prev": page > 1
        }
    }
    
    if processing_time_ms is not None:
        metadata["processing_time_ms"] = processing_time_ms
    
    return metadata 
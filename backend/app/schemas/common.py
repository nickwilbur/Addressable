from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel, Field

T = TypeVar('T')


class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    
    @property
    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """Get limit for database queries."""
        return self.page_size


class PaginationInfo(BaseModel):
    """Pagination metadata."""
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""
    items: List[T]
    pagination: PaginationInfo
    
    @classmethod
    def create(
        cls,
        items: List[T],
        total_count: int,
        params: PaginationParams,
    ) -> "PaginatedResponse[T]":
        """Create paginated response from items and count."""
        total_pages = (total_count + params.page_size - 1) // params.page_size
        
        return cls(
            items=items,
            pagination=PaginationInfo(
                page=params.page,
                page_size=params.page_size,
                total_items=total_count,
                total_pages=total_pages,
                has_next=params.page < total_pages,
                has_previous=params.page > 1,
            ),
        )

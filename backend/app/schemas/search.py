from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field

from app.schemas.common import PaginatedResponse, PaginationParams
from app.schemas.listing import ListingSummary


class SearchCriteria(BaseModel):
    """Search criteria for property listings."""
    location: str = Field(..., description="Location to search (address, city, neighborhood, etc.)")
    min_price: Optional[int] = Field(None, ge=0, description="Minimum price")
    max_price: Optional[int] = Field(None, ge=0, description="Maximum price")
    bedrooms_min: Optional[int] = Field(None, ge=0, description="Minimum bedrooms")
    bedrooms_max: Optional[int] = Field(None, ge=0, description="Maximum bedrooms")
    bathrooms_min: Optional[float] = Field(None, ge=0, description="Minimum bathrooms")
    bathrooms_max: Optional[float] = Field(None, ge=0, description="Maximum bathrooms")
    sqft_min: Optional[int] = Field(None, ge=0, description="Minimum square feet")
    sqft_max: Optional[int] = Field(None, ge=0, description="Maximum square feet")
    property_types: Optional[List[str]] = Field(None, description="Property types to include")
    status: Optional[List[str]] = Field(None, description="Listing statuses to include")
    year_built_min: Optional[int] = Field(None, ge=1800, description="Minimum year built")
    year_built_max: Optional[int] = Field(None, ge=1800, description="Maximum year built")
    providers: Optional[List[str]] = Field(None, description="Specific providers to search (e.g., ['zillow', 'realtor', 'redfin'])")


class SearchRequest(BaseModel):
    """Search request with criteria and options."""
    criteria: SearchCriteria
    mode: str = Field(default="sync", description="Search mode: sync or async")
    pagination: Optional[PaginationParams] = Field(None, description="Pagination parameters")


class SearchSummary(BaseModel):
    """Summary of search execution."""
    search_query_id: UUID
    status: str
    total_providers: int
    completed_providers: int
    total_listings: int
    duration_ms: Optional[int] = None
    error_text: Optional[str] = None


class SearchResponse(PaginatedResponse[ListingSummary]):
    """Search response with listings and metadata."""
    search_summary: SearchSummary
    external_search_links: List[str] = Field(default_factory=list, description="External search URLs")

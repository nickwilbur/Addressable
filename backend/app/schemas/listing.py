from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ListingAddress(BaseModel):
    """Address information for a listing."""
    line1: str
    line2: Optional[str] = None
    city: str
    state: str
    postal_code: str
    country: str = "US"


class ListingLocation(BaseModel):
    """Location coordinates for a listing."""
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class ListingDetails(BaseModel):
    """Property details for a listing."""
    property_type: str
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    sqft: Optional[int] = None
    lot_sqft: Optional[int] = None
    year_built: Optional[int] = None
    description: Optional[str] = None


class ListingSource(BaseModel):
    """Source information for a listing."""
    provider_name: str
    provider_listing_id: str
    source_url: Optional[str] = None
    list_price: Optional[int] = None
    status: str
    first_seen_at: datetime
    last_seen_at: datetime


class ListingSummary(BaseModel):
    """Summary view of a listing for search results."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    canonical_key: str
    address: ListingAddress
    location: ListingLocation
    details: ListingDetails
    status: str
    list_price: Optional[int] = None
    first_seen_at: datetime
    last_seen_at: datetime
    sources: List[ListingSource] = Field(default_factory=list, description="Provider sources for this listing")


class ListingDetail(BaseModel):
    """Detailed view of a listing."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    canonical_key: str
    address: ListingAddress
    location: ListingLocation
    details: ListingDetails
    status: str
    list_price: Optional[int] = None
    first_seen_at: datetime
    last_seen_at: datetime
    images: List[str] = Field(default_factory=list, description="Image URLs")
    sources: List[ListingSource] = Field(default_factory=list, description="All provider sources for this listing")

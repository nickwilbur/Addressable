from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import structlog

from app.schemas.search import SearchCriteria
from app.core.settings import settings

logger = structlog.get_logger()


class ProviderListing(BaseModel):
    """Standard intermediate schema for provider listings."""
    provider_listing_id: str
    address: str
    city: str
    state: str
    postal_code: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    price: Optional[int] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    sqft: Optional[int] = None
    lot_sqft: Optional[int] = None
    year_built: Optional[int] = None
    property_type: str
    status: str
    url: Optional[str] = None
    description: Optional[str] = None
    images: List[str] = []
    raw: Dict[str, Any] = {}  # Original provider data


class ProviderListingDetail(BaseModel):
    """Detailed listing information from provider."""
    provider_listing_id: str
    description: Optional[str] = None
    images: List[str] = []
    features: List[str] = []
    raw: Dict[str, Any] = {}


class Provider(ABC):
    """Abstract base class for data providers."""
    
    name: str
    supports_search: bool = False
    supports_details: bool = False
    supports_images: bool = False
    
    def __init__(self):
        self.timeout_seconds = settings.provider_timeout_seconds
        self.logger = structlog.get_logger().bind(provider=self.name)
    
    @abstractmethod
    async def search(self, criteria: SearchCriteria) -> List[ProviderListing]:
        """
        Search for listings based on criteria.
        
        Args:
            criteria: Search criteria
            
        Returns:
            List of provider listings
            
        Raises:
            ProviderException: If search fails
        """
        pass
    
    async def get_details(self, provider_listing_id: str) -> Optional[ProviderListingDetail]:
        """
        Get detailed information for a specific listing.
        
        Args:
            provider_listing_id: Provider-specific listing ID
            
        Returns:
            Detailed listing information or None if not found
            
        Raises:
            ProviderException: If details retrieval fails
        """
        if not self.supports_details:
            raise NotImplementedError(f"Provider {self.name} does not support details")
        return None
    
    async def health_check(self) -> bool:
        """
        Check if provider is healthy and accessible.
        
        Returns:
            True if healthy, False otherwise
        """
        return True
    
    def get_rate_limit_per_minute(self) -> Optional[int]:
        """Get rate limit per minute for this provider."""
        return settings.provider_rate_limit_per_minute
    
    def get_timeout_seconds(self) -> int:
        """Get timeout for this provider."""
        return self.timeout_seconds

import re
from typing import Optional
import structlog

from app.providers.base import ProviderListing
from app.models.listing import Listing
from app.models.listing_source import ListingSource
from app.schemas.listing import ListingAddress, ListingLocation, ListingDetails

logger = structlog.get_logger()


class NormalizationService:
    """Service for normalizing provider listings to canonical format."""
    
    def __init__(self):
        self.logger = structlog.get_logger()
    
    def normalize_listing(self, provider_listing: ProviderListing, provider_name: str) -> Listing:
        """Normalize a provider listing to canonical Listing model."""
        try:
            # Parse address components
            address_parts = self._parse_address(provider_listing.address)
            
            # Generate canonical key
            canonical_key = self._generate_canonical_key(provider_listing)
            
            # Create canonical listing
            listing = Listing(
                canonical_key=canonical_key,
                address_line1=address_parts["line1"],
                address_line2=address_parts.get("line2"),
                city=provider_listing.city,
                state=provider_listing.state,
                postal_code=provider_listing.postal_code,
                country="US",  # Default to US
                latitude=provider_listing.latitude,
                longitude=provider_listing.longitude,
                property_type=self._normalize_property_type(provider_listing.property_type),
                bedrooms=provider_listing.bedrooms,
                bathrooms=provider_listing.bathrooms,
                sqft=provider_listing.sqft,
                lot_sqft=provider_listing.lot_sqft,
                year_built=provider_listing.year_built,
                status=self._normalize_status(provider_listing.status),
                list_price=provider_listing.price,
                description=provider_listing.description,
                images=provider_listing.images or [],
            )
            
            self.logger.debug(
                "Listing normalized",
                provider=provider_name,
                provider_listing_id=provider_listing.provider_listing_id,
                canonical_key=canonical_key,
            )
            
            return listing
            
        except Exception as e:
            self.logger.error(
                "Failed to normalize listing",
                provider=provider_name,
                provider_listing_id=provider_listing.provider_listing_id,
                error=str(e),
            )
            raise
    
    def create_listing_source(
        self,
        listing_id: str,
        provider_listing: ProviderListing,
        provider_name: str,
        raw_payload_id: Optional[str] = None,
    ) -> ListingSource:
        """Create a ListingSource from provider listing."""
        return ListingSource(
            listing_id=listing_id,
            provider_name=provider_name,
            provider_listing_id=provider_listing.provider_listing_id,
            source_url=provider_listing.url,
            list_price=provider_listing.price,
            status=self._normalize_status(provider_listing.status),
            raw_payload_id=raw_payload_id,
        )
    
    def _parse_address(self, address: str) -> dict:
        """Parse address string into components."""
        # Simple address parsing - can be enhanced with address validation services
        parts = address.split(',')
        
        result = {
            "line1": parts[0].strip() if parts else "",
            "line2": None,
        }
        
        # If there are exactly 3 parts (line1, unit/apt, city/state), the second part is line2
        # If there are exactly 4 parts (line1, unit/apt, city, state), the second part is line2
        # If there are more parts, it's probably city, state, zip - no line2
        if len(parts) == 3:
            # Check if this looks like unit/apt vs city/state
            second_part = parts[1].strip()
            third_part = parts[2].strip()
            
            # If third part looks like a state (2 letters) and second part is short, it's probably line2
            if len(third_part) == 2 and len(second_part) <= 10:
                result["line2"] = second_part
            # Otherwise, it's probably city/state/zip with no line2
        elif len(parts) == 4:
            # Format: "123 Main St, Apt 4B, Springfield, IL 62701"
            # Second part is likely line2 (unit/apt)
            result["line2"] = parts[1].strip()
        
        return result
    
    def _generate_canonical_key(self, provider_listing: ProviderListing) -> str:
        """Generate canonical key for deduplication."""
        # Normalize address
        normalized_address = self._normalize_address_text(provider_listing.address)
        
        # Round coordinates to 6 decimal places (about 0.1 meter precision)
        lat = round(provider_listing.latitude, 6) if provider_listing.latitude else None
        lng = round(provider_listing.longitude, 6) if provider_listing.longitude else None
        
        # Build canonical key
        if lat is not None and lng is not None:
            canonical_key = f"{normalized_address}|{lat}|{lng}"
        else:
            canonical_key = normalized_address
        
        return canonical_key
    
    def _normalize_address_text(self, address: str) -> str:
        """Normalize address text for canonical key generation."""
        if not address:
            return ""
        
        # Convert to lowercase and remove extra whitespace
        normalized = re.sub(r'\s+', ' ', address.lower().strip())
        
        # Remove common punctuation except for unit symbols
        normalized = re.sub(r'[.,]', '', normalized)
        
        # Standardize common abbreviations
        replacements = {
            ' street': ' st',
            ' avenue': ' ave',
            ' boulevard': ' blvd',
            ' drive': ' dr',
            ' lane': ' ln',
            ' road': ' rd',
            ' court': ' ct',
            ' way': ' wy',
            ' circle': ' cir',
            ' terrace': ' ter',
        }
        
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        
        return normalized
    
    def _normalize_property_type(self, property_type: str) -> str:
        """Normalize property type to standard values."""
        if not property_type:
            return "other"
        
        property_type = property_type.lower().strip()
        
        # Mapping of common variations to standard types
        type_mapping = {
            # Single family
            "single family": "single_family",
            "single-family": "single_family",
            "single family home": "single_family",
            "sfr": "single_family",
            "house": "single_family",
            "detached": "single_family",
            
            # Condo
            "condo": "condo",
            "condominium": "condo",
            "apartment": "condo",
            "unit": "condo",
            
            # Townhouse
            "townhouse": "townhouse",
            "town home": "townhouse",
            "town-home": "townhouse",
            "row house": "townhouse",
            
            # Multi-family
            "multi family": "multi_family",
            "multi-family": "multi_family",
            "duplex": "multi_family",
            "triplex": "multi_family",
            "fourplex": "multi_family",
            "2-4 unit": "multi_family",
            
            # Land
            "land": "land",
            "lot": "land",
            "vacant land": "land",
            
            # Commercial
            "commercial": "commercial",
            "office": "commercial",
            "retail": "commercial",
            "industrial": "commercial",
        }
        
        return type_mapping.get(property_type, "other")
    
    def _normalize_status(self, status: str) -> str:
        """Normalize listing status to standard values."""
        if not status:
            return "active"
        
        status = status.lower().strip()
        
        # Mapping of common variations to standard statuses
        status_mapping = {
            # Active
            "active": "active",
            "for sale": "active",
            "available": "active",
            "on market": "active",
            
            # Pending
            "pending": "pending",
            "pending sale": "pending",
            "under contract": "pending",
            "contingent": "pending",
            "pending - continue to show": "pending",
            
            # Sold
            "sold": "sold",
            "closed": "sold",
            "sale closed": "sold",
            
            # Off market
            "off market": "off_market",
            "withdrawn": "off_market",
            "expired": "off_market",
            "canceled": "off_market",
            "temporarily off market": "off_market",
            
            # For rent
            "for rent": "for_rent",
            "rental": "for_rent",
            "lease": "for_rent",
            
            # Rented
            "rented": "rented",
            "leased": "rented",
            "off market - rented": "rented",
        }
        
        return status_mapping.get(status, "active")

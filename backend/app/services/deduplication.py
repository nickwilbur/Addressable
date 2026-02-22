from typing import List, Dict, Set
from uuid import UUID
import structlog

from app.models.listing import Listing
from app.models.listing_source import ListingSource
from app.providers.base import ProviderListing

logger = structlog.get_logger()


class DeduplicationService:
    """Service for deduplicating listings from multiple providers."""
    
    def __init__(self):
        self.logger = structlog.get_logger()
    
    def deduplicate_listings(
        self,
        provider_listings: List[tuple[ProviderListing, str, str]],  # (listing, provider_name, raw_payload_id)
    ) -> tuple[List[Listing], List[tuple[ListingSource, str]]]:
        """
        Deduplicate provider listings into canonical listings.
        
        Args:
            provider_listings: List of tuples (provider_listing, provider_name, raw_payload_id)
            
        Returns:
            Tuple of (canonical_listings, listing_sources_with_canonical_keys)
        """
        try:
            # Group by canonical key
            canonical_groups: Dict[str, List[tuple[ProviderListing, str, str]]] = {}
            
            for provider_listing, provider_name, raw_payload_id in provider_listings:
                canonical_key = self._generate_canonical_key(provider_listing)
                
                if canonical_key not in canonical_groups:
                    canonical_groups[canonical_key] = []
                
                canonical_groups[canonical_key].append((provider_listing, provider_name, raw_payload_id))
            
            self.logger.info(
                "Grouped listings by canonical key",
                total_listings=len(provider_listings),
                unique_keys=len(canonical_groups),
            )
            
            # Create canonical listings and sources
            canonical_listings: List[Listing] = []
            listing_sources: List[tuple[ListingSource, str]] = []
            
            for canonical_key, group in canonical_groups.items():
                # Select best listing as canonical
                best_listing = self._select_best_canonical_listing(group, canonical_key)
                canonical_listings.append(best_listing)
                
                # Create sources for all listings in the group (without listing_id for now)
                for provider_listing, provider_name, raw_payload_id in group:
                    source = self._create_listing_source(
                        None,  # Will be set later after listing is saved
                        provider_listing,
                        provider_name,
                        raw_payload_id,
                    )
                    listing_sources.append((source, canonical_key))
            
            self.logger.info(
                "Deduplication completed",
                canonical_listings=len(canonical_listings),
                listing_sources=len(listing_sources),
            )
            
            return canonical_listings, listing_sources
            
        except Exception as e:
            self.logger.error("Deduplication failed", error=str(e))
            raise
    
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
        
        import re
        
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
    
    def _select_best_canonical_listing(
        self,
        group: List[tuple[ProviderListing, str, str]],
        canonical_key: str,
    ) -> Listing:
        """Select the best listing from a group to serve as canonical."""
        from app.services.normalization import NormalizationService
        
        normalization_service = NormalizationService()
        
        # Sort by quality criteria
        def listing_quality(item):
            provider_listing, provider_name, raw_payload_id = item
            score = 0
            
            # Prefer listings with more complete data
            if provider_listing.price:
                score += 10
            if provider_listing.bedrooms:
                score += 5
            if provider_listing.bathrooms:
                score += 5
            if provider_listing.sqft:
                score += 5
            if provider_listing.year_built:
                score += 3
            if provider_listing.description:
                score += 3
            if provider_listing.images:
                score += len(provider_listing.images)
            if provider_listing.latitude and provider_listing.longitude:
                score += 8
            
            # Prefer certain providers (can be configured)
            provider_preferences = {
                "mock": 1,
                "csv": 2,
                "zillow": 10,
                "redfin": 9,
                "realtor": 8,
            }
            score += provider_preferences.get(provider_name, 0)
            
            return score
        
        # Sort by quality score (descending)
        sorted_group = sorted(group, key=listing_quality, reverse=True)
        
        # Use the highest quality listing as canonical
        best_provider_listing, best_provider_name, best_raw_payload_id = sorted_group[0]
        
        # Normalize to canonical format
        canonical_listing = normalization_service.normalize_listing(
            best_provider_listing,
            best_provider_name,
        )
        
        self.logger.debug(
            "Selected canonical listing",
            canonical_key=canonical_listing.canonical_key,
            provider=best_provider_name,
            quality_score=listing_quality(sorted_group[0]),
        )
        
        return canonical_listing
    
    def _create_listing_source(
        self,
        listing_id: UUID,
        provider_listing: ProviderListing,
        provider_name: str,
        raw_payload_id: str,
    ) -> ListingSource:
        """Create a ListingSource from provider listing."""
        from app.services.normalization import NormalizationService
        
        normalization_service = NormalizationService()
        
        return normalization_service.create_listing_source(
            listing_id,
            provider_listing,
            provider_name,
            raw_payload_id,
        )
    
    def find_duplicates_for_listing(
        self,
        listing: Listing,
        existing_listings: List[Listing],
    ) -> List[Listing]:
        """Find existing listings that are duplicates of the given listing."""
        duplicates = []
        
        for existing in existing_listings:
            if existing.id == listing.id:
                continue
            
            # Check if canonical keys match
            if listing.canonical_key == existing.canonical_key:
                duplicates.append(existing)
                continue
            
            # Check for near-duplicates based on address similarity
            if self._are_addresses_similar(listing, existing):
                duplicates.append(existing)
        
        return duplicates
    
    def _are_addresses_similar(self, listing1: Listing, listing2: Listing) -> bool:
        """Check if two listings have similar addresses."""
        # Simple similarity check - can be enhanced with fuzzy matching
        address1 = f"{listing1.address_line1} {listing1.city} {listing1.state}".lower()
        address2 = f"{listing2.address_line1} {listing2.city} {listing2.state}".lower()
        
        # Check if one address contains the other
        if address1 in address2 or address2 in address1:
            return True
        
        # Check coordinate similarity if both have coordinates
        if listing1.latitude and listing1.longitude and listing2.latitude and listing2.longitude:
            lat_diff = abs(float(listing1.latitude) - float(listing2.latitude))
            lng_diff = abs(float(listing1.longitude) - float(listing2.longitude))
            
            # Within ~100 meters
            if lat_diff < 0.001 and lng_diff < 0.001:
                return True
        
        return False

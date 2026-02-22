import asyncio
import json
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, quote

from app.providers.base import Provider, ProviderListing
from app.schemas.search import SearchCriteria
from app.core.errors import ProviderException
import httpx


class ZillowProvider(Provider):
    """Provider for Zillow real estate listings."""
    
    name = "zillow"
    supports_search = True
    supports_details = True
    supports_images = True
    base_url = "https://www.zillow.com"
    
    def __init__(self):
        super().__init__()
        self.client = httpx.AsyncClient(
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
            },
            timeout=30.0
        )
    
    async def search(self, criteria: SearchCriteria) -> List[ProviderListing]:
        """Search Zillow for listings matching the criteria."""
        try:
            self.logger.info("Searching Zillow", criteria=criteria.model_dump())
            
            # Build search URL
            search_url = self._build_search_url(criteria)
            self.logger.info("Built Zillow search URL", url=search_url)
            
            # Make request
            response = await self.client.get(search_url)
            response.raise_for_status()
            
            # Parse HTML response (simplified approach)
            listings = self._parse_search_results(response.text, criteria)
            
            self.logger.info("Zillow search completed", listings_found=len(listings))
            return listings
            
        except httpx.HTTPError as e:
            self.logger.error("HTTP error from Zillow", error=str(e))
            raise ProviderException(self.name, f"HTTP error: {str(e)}")
        except Exception as e:
            self.logger.error("Zillow search failed", error=str(e))
            raise ProviderException(self.name, f"Search failed: {str(e)}")
    
    def _build_search_url(self, criteria: SearchCriteria) -> str:
        """Build Zillow search URL from criteria."""
        base_url = "https://www.zillow.com/homes/"
        
        # Location
        location_query = criteria.location.replace(' ', '-').replace(',', '').lower()
        base_url += f"{location_query}_rb/"
        
        # Build filters
        filters = []
        
        # Price range
        if criteria.min_price or criteria.max_price:
            price_range = f"{criteria.min_price or ''}-{criteria.max_price or ''}_price"
            filters.append(price_range)
        
        # Bedrooms
        if criteria.bedrooms_min or criteria.bedrooms_max:
            if criteria.bedrooms_min == criteria.bedrooms_max:
                filters.append(f"{criteria.bedrooms_min}-beds")
            elif criteria.bedrooms_min and not criteria.bedrooms_max:
                filters.append(f"{criteria.bedrooms_min}-beds")
            elif not criteria.bedrooms_min and criteria.bedrooms_max:
                filters.append(f"{criteria.bedrooms_max}-beds")
            else:
                beds_range = f"{criteria.bedrooms_min}-{criteria.bedrooms_max}-beds"
                filters.append(beds_range)
        
        # Bathrooms
        if criteria.bathrooms_min or criteria.bathrooms_max:
            if criteria.bathrooms_min == criteria.bathrooms_max:
                filters.append(f"{int(criteria.bathrooms_min)}-baths")
            else:
                baths_range = f"{criteria.bathrooms_min or ''}-{criteria.bathrooms_max or ''}-baths"
                filters.append(baths_range)
        
        # Square footage
        if criteria.sqft_min or criteria.sqft_max:
            sqft_range = f"{criteria.sqft_min or ''}-{criteria.sqft_max or ''}-sqft"
            filters.append(sqft_range)
        
        # Combine filters
        if filters:
            base_url += "/".join(filters) + "/"
        
        return base_url
    
    def _parse_search_results(self, html_content: str, criteria: SearchCriteria) -> List[ProviderListing]:
        """Parse Zillow search results from HTML content."""
        listings = []
        
        try:
            # Look for JSON data in script tags (Zillow often embeds data in JSON-LD)
            json_pattern = r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>'
            json_matches = re.findall(json_pattern, html_content, re.DOTALL)
            
            for json_text in json_matches:
                try:
                    data = json.loads(json_text)
                    if isinstance(data, list):
                        for item in data:
                            if item.get("@type") == "ListItem" and "item" in item:
                                listing_data = item["item"]
                                if listing_data.get("@type") == "SingleFamilyResidence" or listing_data.get("@type") == "Apartment":
                                    listing = self._convert_to_provider_listing(listing_data)
                                    if listing:
                                        listings.append(listing)
                except json.JSONDecodeError:
                    continue
            
            # If no JSON data found, try to extract from HTML patterns (fallback)
            if not listings:
                listings = self._parse_from_html_patterns(html_content, criteria)
            
        except Exception as e:
            self.logger.warning("Failed to parse Zillow results", error=str(e))
            # Return empty list rather than failing completely
            pass
        
        return listings
    
    def _parse_from_html_patterns(self, html_content: str, criteria: SearchCriteria) -> List[ProviderListing]:
        """Parse listings from HTML patterns as fallback."""
        listings = []
        
        # This is a simplified placeholder - in reality, you'd need to parse
        # Zillow's specific HTML structure which changes frequently
        # For now, return empty to indicate no listings found
        self.logger.info("No listings found in HTML parsing (placeholder implementation)")
        
        return listings
    
    def _convert_to_provider_listing(self, data: Dict[str, Any]) -> Optional[ProviderListing]:
        """Convert Zillow data to ProviderListing."""
        try:
            # Extract basic information
            address = data.get("name", "")
            if not address:
                return None
            
            # Parse address components
            address_parts = address.split(',')
            address_line1 = address_parts[0].strip() if address_parts else ""
            city = address_parts[1].strip() if len(address_parts) > 1 else ""
            state = ""
            postal_code = ""
            
            if len(address_parts) > 2:
                state_zip = address_parts[2].strip().split()
                if len(state_zip) >= 2:
                    state = state_zip[0]
                    postal_code = state_zip[1]
            
            # Extract other details
            price = None
            if "offers" in data and data["offers"]:
                offers = data["offers"]
                if isinstance(offers, list) and offers:
                    price = offers[0].get("price")
                elif isinstance(offers, dict):
                    price = offers.get("price")
            
            # Extract bedrooms, bathrooms, sqft
            bedrooms = None
            bathrooms = None
            sqft = None
            
            if "numberOfRooms" in data:
                bedrooms = data["numberOfRooms"]
            
            if "floorSize" in data:
                sqft = int(data["floorSize"].get("value", 0)) if isinstance(data["floorSize"], dict) else None
            
            # Extract images
            images = []
            if "image" in data:
                if isinstance(data["image"], str):
                    images = [data["image"]]
                elif isinstance(data["image"], list):
                    images = [img for img in data["image"] if isinstance(img, str)]
            
            return ProviderListing(
                provider_listing_id=str(data.get("identifier", "")),
                address_line1=address_line1,
                city=city,
                state=state,
                postal_code=postal_code,
                country="US",
                latitude=float(data.get("geo", {}).get("latitude", 0)) if data.get("geo") else None,
                longitude=float(data.get("geo", {}).get("longitude", 0)) if data.get("geo") else None,
                property_type="single_family",  # Default
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                sqft=sqft,
                list_price=int(price) if price else None,
                description=data.get("description", ""),
                images=images,
                source_url=data.get("url", ""),
                status="active",  # Default
                provider_name=self.name,
            )
            
        except Exception as e:
            self.logger.warning("Failed to convert Zillow listing", error=str(e))
            return None
    
    async def get_details(self, provider_listing_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific listing."""
        try:
            # This would fetch the detailed page for a specific listing
            # For now, return None as placeholder
            return None
        except Exception as e:
            self.logger.error("Failed to get Zillow listing details", error=str(e))
            return None
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

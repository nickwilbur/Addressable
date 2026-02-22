import asyncio
import json
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, quote

from app.providers.base import Provider, ProviderListing
from app.schemas.search import SearchCriteria
from app.core.errors import ProviderException
import httpx


class RealtorProvider(Provider):
    """Provider for Realtor.com real estate listings."""
    
    name = "realtor"
    supports_search = True
    supports_details = True
    supports_images = True
    base_url = "https://www.realtor.com"
    
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
        """Search Realtor.com for listings matching the criteria."""
        try:
            self.logger.info("Searching Realtor.com", criteria=criteria.model_dump())
            
            # Build search URL
            search_url = self._build_search_url(criteria)
            self.logger.info("Built Realtor.com search URL", url=search_url)
            
            # Make request
            response = await self.client.get(search_url)
            response.raise_for_status()
            
            # Parse HTML response
            listings = self._parse_search_results(response.text, criteria)
            
            self.logger.info("Realtor.com search completed", listings_found=len(listings))
            return listings
            
        except httpx.HTTPError as e:
            self.logger.error("HTTP error from Realtor.com", error=str(e))
            raise ProviderException(self.name, f"HTTP error: {str(e)}")
        except Exception as e:
            self.logger.error("Realtor.com search failed", error=str(e))
            raise ProviderException(self.name, f"Search failed: {str(e)}")
    
    def _build_search_url(self, criteria: SearchCriteria) -> str:
        """Build Realtor.com search URL from criteria."""
        base_url = "https://www.realtor.com/realestateandhomes-search/"
        
        # Add location
        location_encoded = quote(criteria.location)
        search_url = f"{base_url}{location_encoded}"
        
        # Build query parameters
        query_params = []
        
        if criteria.min_price:
            query_params.append(f"priceMin={criteria.min_price}")
        if criteria.max_price:
            query_params.append(f"priceMax={criteria.max_price}")
        if criteria.bedrooms_min:
            query_params.append(f"bedsMin={criteria.bedrooms_min}")
        if criteria.bedrooms_max:
            query_params.append(f"bedsMax={criteria.bedrooms_max}")
        if criteria.bathrooms_min:
            query_params.append(f"bathsMin={criteria.bathrooms_min}")
        if criteria.bathrooms_max:
            query_params.append(f"bathsMax={criteria.bathrooms_max}")
        if criteria.sqft_min:
            query_params.append(f"sqftMin={criteria.sqft_min}")
        if criteria.sqft_max:
            query_params.append(f"sqftMax={criteria.sqft_max}")
        
        if query_params:
            search_url += "?" + "&".join(query_params)
        
        return search_url
    
    def _parse_search_results(self, html_content: str, criteria: SearchCriteria) -> List[ProviderListing]:
        """Parse Realtor.com search results from HTML content."""
        listings = []
        
        try:
            # Look for JSON data in script tags
            json_pattern = r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>'
            json_matches = re.findall(json_pattern, html_content, re.DOTALL)
            
            for json_text in json_matches:
                try:
                    data = json.loads(json_text)
                    if isinstance(data, list):
                        for item in data:
                            if item.get("@type") == "ListItem" and "item" in item:
                                listing_data = item["item"]
                                if listing_data.get("@type") in ["SingleFamilyResidence", "Apartment", "Condominium"]:
                                    listing = self._convert_to_provider_listing(listing_data)
                                    if listing:
                                        listings.append(listing)
                except json.JSONDecodeError:
                    continue
            
            # If no JSON data found, try to extract from HTML patterns (fallback)
            if not listings:
                listings = self._parse_from_html_patterns(html_content, criteria)
            
        except Exception as e:
            self.logger.warning("Failed to parse Realtor.com results", error=str(e))
            pass
        
        return listings
    
    def _parse_from_html_patterns(self, html_content: str, criteria: SearchCriteria) -> List[ProviderListing]:
        """Parse listings from HTML patterns as fallback."""
        listings = []
        
        # Placeholder implementation - would need to parse Realtor.com's HTML structure
        self.logger.info("No listings found in HTML parsing (placeholder implementation)")
        
        return listings
    
    def _convert_to_provider_listing(self, data: Dict[str, Any]) -> Optional[ProviderListing]:
        """Convert Realtor.com data to ProviderListing."""
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
                property_type="single_family",
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                sqft=sqft,
                list_price=int(price) if price else None,
                description=data.get("description", ""),
                images=images,
                source_url=data.get("url", ""),
                status="active",
                provider_name=self.name,
            )
            
        except Exception as e:
            self.logger.warning("Failed to convert Realtor.com listing", error=str(e))
            return None
    
    async def get_details(self, provider_listing_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific listing."""
        try:
            return None  # Placeholder
        except Exception as e:
            self.logger.error("Failed to get Realtor.com listing details", error=str(e))
            return None
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

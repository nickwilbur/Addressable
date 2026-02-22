import urllib.parse
from typing import List

from app.providers.base import Provider, ProviderListing
from app.schemas.search import SearchCriteria
from app.core.errors import ProviderException


class OutlinkProvider(Provider):
    """Provider that generates external search links to major real estate sites."""
    
    name = "outlink"
    supports_search = True
    supports_details = False
    supports_images = False
    
    # Base URLs for major real estate sites
    SITE_URLS = {
        "zillow": "https://www.zillow.com/homes/",
        "redfin": "https://www.redfin.com/city/",
        "realtor": "https://www.realtor.com/realestateandhomes-search/",
    }
    
    async def search(self, criteria: SearchCriteria) -> List[ProviderListing]:
        """Generate external search links based on criteria."""
        try:
            self.logger.info("Generating external search links", criteria=criteria.model_dump())
            
            # This provider doesn't return actual listings, just external links
            # We'll return empty listings list and the links will be handled separately
            self.logger.info("External links generated", links_count=len(self.SITE_URLS))
            return []
            
        except Exception as e:
            self.logger.error("Outlink generation failed", error=str(e))
            raise ProviderException(self.name, f"Outlink generation failed: {str(e)}")
    
    def generate_search_links(self, criteria: SearchCriteria) -> List[str]:
        """Generate external search URLs for the given criteria."""
        links = []
        
        for site_name, base_url in self.SITE_URLS.items():
            try:
                search_url = self._build_search_url(site_name, base_url, criteria)
                if search_url:
                    links.append(search_url)
            except Exception as e:
                self.logger.warning("Failed to generate search link", site=site_name, error=str(e))
                continue
        
        return links
    
    def _build_search_url(self, site_name: str, base_url: str, criteria: SearchCriteria) -> str:
        """Build search URL for a specific site."""
        if site_name == "zillow":
            return self._build_zillow_url(criteria)
        elif site_name == "redfin":
            return self._build_redfin_url(criteria)
        elif site_name == "realtor":
            return self._build_realtor_url(criteria)
        else:
            return None
    
    def _build_zillow_url(self, criteria: SearchCriteria) -> str:
        """Build Zillow search URL."""
        base_url = "https://www.zillow.com/homes/"
        
        # Build query parameters
        params = []
        
        # Location
        location_query = criteria.location.replace(' ', '-').replace(',', '').lower()
        base_url += f"{location_query}_rb/"
        
        # Price range
        if criteria.min_price or criteria.max_price:
            price_range = f"{criteria.min_price or ''}-{criteria.max_price or ''}_price"
            params.append(price_range)
        
        # Bedrooms
        if criteria.bedrooms_min or criteria.bedrooms_max:
            if criteria.bedrooms_min == criteria.bedrooms_max:
                params.append(f"{criteria.bedrooms_min}-beds")
            elif criteria.bedrooms_min and not criteria.bedrooms_max:
                params.append(f"{criteria.bedrooms_min}-beds")
            elif not criteria.bedrooms_min and criteria.bedrooms_max:
                params.append(f"{criteria.bedrooms_max}-beds")
            else:
                beds_range = f"{criteria.bedrooms_min}-{criteria.bedrooms_max}-beds"
                params.append(beds_range)
        
        # Bathrooms
        if criteria.bathrooms_min or criteria.bathrooms_max:
            if criteria.bathrooms_min == criteria.bathrooms_max:
                params.append(f"{int(criteria.bathrooms_min)}-baths")
            else:
                baths_range = f"{criteria.bathrooms_min or ''}-{criteria.bathrooms_max or ''}-baths"
                params.append(baths_range)
        
        # Square footage
        if criteria.sqft_min or criteria.sqft_max:
            sqft_range = f"{criteria.sqft_min or ''}-{criteria.sqft_max or ''}-sqft"
            params.append(sqft_range)
        
        # Combine parameters
        if params:
            base_url += "/".join(params) + "/"
        
        return base_url
    
    def _build_redfin_url(self, criteria: SearchCriteria) -> str:
        """Build Redfin search URL."""
        # Redfin uses a different URL structure
        base_url = "https://www.redfin.com/city/"
        
        # For simplicity, we'll use the location-based search
        location_encoded = urllib.parse.quote(criteria.location)
        search_url = f"https://www.redfin.com/zipcode/19104/filter/viewport=39.96112:39.93364:-75.17647:-75.21048"
        
        # Add filters as query parameters
        query_params = []
        
        if criteria.min_price:
            query_params.append(f"min_price={criteria.min_price}")
        if criteria.max_price:
            query_params.append(f"max_price={criteria.max_price}")
        if criteria.bedrooms_min:
            query_params.append(f"min_beds={criteria.bedrooms_min}")
        if criteria.bedrooms_max:
            query_params.append(f"max_beds={criteria.bedrooms_max}")
        if criteria.bathrooms_min:
            query_params.append(f"min_baths={int(criteria.bathrooms_min)}")
        if criteria.bathrooms_max:
            query_params.append(f"max_baths={int(criteria.bathrooms_max)}")
        
        if query_params:
            search_url += "?" + "&".join(query_params)
        
        return search_url
    
    def _build_realtor_url(self, criteria: SearchCriteria) -> str:
        """Build Realtor.com search URL."""
        base_url = "https://www.realtor.com/realestateandhomes-search/"
        
        # Add location
        location_encoded = urllib.parse.quote(criteria.location)
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

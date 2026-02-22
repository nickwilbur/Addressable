import random
from typing import List
from datetime import datetime, timezone

from app.providers.base import Provider, ProviderListing, ProviderListingDetail
from app.schemas.search import SearchCriteria
from app.core.errors import ProviderException


class MockProvider(Provider):
    """Mock provider for testing and development."""
    
    name = "mock"
    supports_search = True
    supports_details = True
    supports_images = True
    
    # Mock data
    MOCK_ADDRESSES = [
        "123 Main St",
        "456 Oak Ave", 
        "789 Pine Rd",
        "321 Elm St",
        "654 Maple Dr",
        "987 Cedar Ln",
        "147 Birch Way",
        "258 Willow Ct",
        "369 Spruce St",
        "741 Ash Blvd",
    ]
    
    MOCK_CITIES = ["Springfield", "Riverside", "Franklin", "Georgetown", "Madison"]
    MOCK_STATES = ["CA", "TX", "FL", "NY", "IL"]
    
    PROPERTY_TYPES = ["single_family", "condo", "townhouse", "multi_family"]
    STATUSES = ["active", "pending", "sold", "off_market"]
    
    async def search(self, criteria: SearchCriteria) -> List[ProviderListing]:
        """Generate mock listings based on search criteria."""
        try:
            self.logger.info("Performing mock search", criteria=criteria.model_dump())
            
            # Generate 5-15 mock listings
            num_listings = random.randint(5, 15)
            listings = []
            
            for i in range(num_listings):
                listing = self._generate_mock_listing(i, criteria)
                
                # Apply filters
                if self._matches_criteria(listing, criteria):
                    listings.append(listing)
            
            self.logger.info("Mock search completed", listings_found=len(listings))
            return listings
            
        except Exception as e:
            self.logger.error("Mock search failed", error=str(e))
            raise ProviderException(self.name, f"Mock search failed: {str(e)}")
    
    async def get_details(self, provider_listing_id: str) -> ProviderListingDetail:
        """Get mock details for a listing."""
        try:
            self.logger.info("Getting mock details", provider_listing_id=provider_listing_id)
            
            # Generate mock details
            features = [
                "Hardwood floors",
                "Granite countertops", 
                "Stainless steel appliances",
                "Central air conditioning",
                "2-car garage",
                "Backyard",
                "Updated kitchen",
                "Master suite",
            ]
            
            # Randomly select 3-6 features
            selected_features = random.sample(features, random.randint(3, 6))
            
            # Generate mock images
            images = [
                f"https://picsum.photos/800/600?random={provider_listing_id}_1",
                f"https://picsum.photos/800/600?random={provider_listing_id}_2",
                f"https://picsum.photos/800/600?random={provider_listing_id}_3",
            ]
            
            return ProviderListingDetail(
                provider_listing_id=provider_listing_id,
                description=f"Beautiful property located in a great neighborhood. This home features modern amenities and is perfect for families.",
                images=images,
                features=selected_features,
                raw={"mock": True, "generated_at": datetime.now(timezone.utc).isoformat()},
            )
            
        except Exception as e:
            self.logger.error("Mock details failed", error=str(e))
            raise ProviderException(self.name, f"Mock details failed: {str(e)}")
    
    def _generate_mock_listing(self, index: int, criteria: SearchCriteria) -> ProviderListing:
        """Generate a single mock listing."""
        address = random.choice(self.MOCK_ADDRESSES)
        city = random.choice(self.MOCK_CITIES)
        state = random.choice(self.MOCK_STATES)
        postal_code = f"{random.randint(10000, 99999)}"
        
        # Generate coordinates near city center
        latitude = round(random.uniform(30.0, 45.0), 6)
        longitude = round(random.uniform(-120.0, -70.0), 6)
        
        # Generate property details
        bedrooms = random.randint(1, 6)
        bathrooms = round(random.uniform(1.0, 4.5), 1)
        sqft = random.randint(800, 5000)
        lot_sqft = random.randint(2000, 10000)
        year_built = random.randint(1980, 2023)
        property_type = random.choice(self.PROPERTY_TYPES)
        status = random.choice(self.STATUSES)
        
        # Generate price based on criteria
        if criteria.min_price and criteria.max_price:
            price = random.randint(criteria.min_price, criteria.max_price)
        elif criteria.min_price:
            price = random.randint(criteria.min_price, criteria.min_price + 200000)
        elif criteria.max_price:
            price = random.randint(max(100000, criteria.max_price - 200000), criteria.max_price)
        else:
            price = random.randint(200000, 800000)
        
        return ProviderListing(
            provider_listing_id=f"mock_{index}_{random.randint(1000, 9999)}",
            address=f"{address}, {city}, {state} {postal_code}",
            city=city,
            state=state,
            postal_code=postal_code,
            latitude=latitude,
            longitude=longitude,
            price=price,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            sqft=sqft,
            lot_sqft=lot_sqft,
            year_built=year_built,
            property_type=property_type,
            status=status,
            url=f"https://mock-provider.com/listings/mock_{index}",
            description=f"Mock property listing at {address}",
            images=[
                f"https://picsum.photos/800/600?random={index}_1",
                f"https://picsum.photos/800/600?random={index}_2",
            ],
            raw={"mock": True, "generated_at": datetime.utcnow().isoformat()},
        )
    
    def _matches_criteria(self, listing: ProviderListing, criteria: SearchCriteria) -> bool:
        """Check if listing matches search criteria."""
        # Price filters
        if criteria.min_price and listing.price and listing.price < criteria.min_price:
            return False
        if criteria.max_price and listing.price and listing.price > criteria.max_price:
            return False
        
        # Bedroom filters
        if criteria.bedrooms_min and listing.bedrooms and listing.bedrooms < criteria.bedrooms_min:
            return False
        if criteria.bedrooms_max and listing.bedrooms and listing.bedrooms > criteria.bedrooms_max:
            return False
        
        # Bathroom filters
        if criteria.bathrooms_min and listing.bathrooms and listing.bathrooms < criteria.bathrooms_min:
            return False
        if criteria.bathrooms_max and listing.bathrooms and listing.bathrooms > criteria.bathrooms_max:
            return False
        
        # Square footage filters
        if criteria.sqft_min and listing.sqft and listing.sqft < criteria.sqft_min:
            return False
        if criteria.sqft_max and listing.sqft and listing.sqft > criteria.sqft_max:
            return False
        
        # Year built filters
        if criteria.year_built_min and listing.year_built and listing.year_built < criteria.year_built_min:
            return False
        if criteria.year_built_max and listing.year_built and listing.year_built > criteria.year_built_max:
            return False
        
        # Property type filter
        if criteria.property_types and listing.property_type not in criteria.property_types:
            return False
        
        # Status filter
        if criteria.status and listing.status not in criteria.status:
            return False
        
        return True

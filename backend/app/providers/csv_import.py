import csv
import io
from typing import List, Dict, Any
from pathlib import Path

from app.providers.base import Provider, ProviderListing
from app.schemas.search import SearchCriteria
from app.core.errors import ProviderException


class CSVImportProvider(Provider):
    """CSV file import provider for bulk listing data."""
    
    name = "csv"
    supports_search = True
    supports_details = False
    supports_images = False
    
    def __init__(self):
        super().__init__()
    
    def _get_normalization_service(self):
        """Get normalization service instance to avoid circular imports."""
        from app.services.normalization import NormalizationService
        return NormalizationService()
    
    # Default CSV file path - can be overridden via environment
    CSV_FILE_PATH = "data/listings.csv"
    
    async def search(self, criteria: SearchCriteria) -> List[ProviderListing]:
        """Search listings from CSV file."""
        try:
            self.logger.info("Searching CSV file", file_path=self.CSV_FILE_PATH)
            
            # Check if CSV file exists
            csv_path = Path(self.CSV_FILE_PATH)
            if not csv_path.exists():
                self.logger.warning("CSV file not found", file_path=self.CSV_FILE_PATH)
                return []
            
            # Read CSV file
            listings = []
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row_num, row in enumerate(reader, 1):
                    try:
                        listing = self._parse_csv_row(row, row_num)
                        if self._matches_criteria(listing, criteria):
                            listings.append(listing)
                    except Exception as e:
                        self.logger.warning("Failed to parse CSV row", row=row_num, error=str(e))
                        continue
            
            self.logger.info("CSV search completed", listings_found=len(listings))
            return listings
            
        except Exception as e:
            self.logger.error("CSV search failed", error=str(e))
            raise ProviderException(self.name, f"CSV search failed: {str(e)}")
    
    def _parse_csv_row(self, row: Dict[str, str], row_num: int) -> ProviderListing:
        """Parse a single CSV row into a ProviderListing."""
        # Extract address components
        address_parts = row.get('address', '').split(',')
        address_line1 = address_parts[0].strip() if address_parts else ''
        
        # City and state from address or separate columns
        city = row.get('city', '').strip()
        state = row.get('state', '').strip()
        postal_code = row.get('postal_code', '').strip()
        
        # If city/state not in separate columns, try to extract from address
        if not city and len(address_parts) >= 2:
            # Handle format: "123 Main St, Springfield, IL 62701"
            if len(address_parts) == 2:
                city_state_zip = address_parts[1].strip()
                parts = city_state_zip.split()
                if len(parts) >= 2:
                    # City might be multiple words, state is 2nd to last, zip is last
                    state = parts[-2]
                    postal_code = parts[-1]
                    # Check if the last part looks like a zip code (5 digits)
                    if postal_code.isdigit() and len(postal_code) == 5:
                        city = ' '.join(parts[:-2])
                    else:
                        # If no zip code pattern, assume the last part is state
                        state = parts[-1]
                        postal_code = ''
                        city = ' '.join(parts[:-1])
            elif len(address_parts) == 3:
                # Handle format: "123 Main St, Springfield, IL 62701"
                # parts: [0] = street, [1] = city, [2] = state zip
                city = address_parts[1].strip()
                state_zip = address_parts[2].strip()
                state_zip_parts = state_zip.split()
                if len(state_zip_parts) >= 2:
                    state = state_zip_parts[0]
                    postal_code = state_zip_parts[1]
                else:
                    state = state_zip
                    postal_code = ''
            elif len(address_parts) > 3:
                # Handle format: "123 Main St, Springfield, IL, 62701"
                city = address_parts[1].strip()
                state = address_parts[2].strip()
                postal_code = address_parts[3].strip()
        
        # Parse numeric fields
        price = self._parse_int(row.get('price'))
        bedrooms = self._parse_int(row.get('bedrooms'))
        bathrooms = self._parse_float(row.get('bathrooms'))
        sqft = self._parse_int(row.get('sqft'))
        lot_sqft = self._parse_int(row.get('lot_sqft'))
        year_built = self._parse_int(row.get('year_built'))
        
        # Parse coordinates
        latitude = self._parse_float(row.get('latitude'))
        longitude = self._parse_float(row.get('longitude'))
        
        # Other fields
        normalization_service = self._get_normalization_service()
        property_type = normalization_service._normalize_property_type(row.get('property_type', 'single_family').strip())
        status = normalization_service._normalize_status(row.get('status', 'active').strip())
        url = row.get('url', '').strip() or None
        description = row.get('description', '').strip() or None
        
        return ProviderListing(
            provider_listing_id=f"csv_{row_num}_{row.get('id', row_num)}",
            address=address_line1,
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
            url=url,
            description=description,
            images=[],  # CSV doesn't typically include images
            raw={"csv_row": row, "row_number": row_num},
        )
    
    def _parse_int(self, value: str) -> int | None:
        """Parse integer from string, handling common formats."""
        if not value or value.strip() == '':
            return None
        
        try:
            # Remove currency symbols, commas, etc.
            clean_value = value.replace('$', '').replace(',', '').strip()
            return int(clean_value)
        except ValueError:
            return None
    
    def _parse_float(self, value: str) -> float | None:
        """Parse float from string, handling common formats."""
        if not value or value.strip() == '':
            return None
        
        try:
            # Remove currency symbols, commas, etc.
            clean_value = value.replace('$', '').replace(',', '').strip()
            return float(clean_value)
        except ValueError:
            return None
    
    def _matches_criteria(self, listing: ProviderListing, criteria: SearchCriteria) -> bool:
        """Check if listing matches search criteria."""
        # Location filter - simple text match
        if criteria.location.lower() not in listing.address.lower() and \
           criteria.location.lower() not in listing.city.lower():
            return False
        
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

import pytest
from unittest.mock import patch, Mock

from app.providers.mock import MockProvider
from app.providers.csv_import import CSVImportProvider
from app.providers.outlink import OutlinkProvider
from app.schemas.search import SearchCriteria


class TestMockProvider:
    """Test cases for the MockProvider."""

    def setup_method(self):
        """Set up test fixtures."""
        self.provider = MockProvider()

    def test_provider_attributes(self):
        """Test provider attributes."""
        assert self.provider.name == "mock"
        assert self.provider.supports_search is True
        assert self.provider.supports_details is True
        assert self.provider.supports_images is True

    @pytest.mark.asyncio
    async def test_search_returns_listings(self):
        """Test that search returns a list of listings."""
        criteria = SearchCriteria(location="Springfield, IL")
        
        listings = await self.provider.search(criteria)
        
        assert isinstance(listings, list)
        assert len(listings) > 0

    @pytest.mark.asyncio
    async def test_search_applies_filters(self):
        """Test that search applies price filters."""
        criteria = SearchCriteria(
            location="Springfield, IL",
            min_price=300000,
            max_price=400000
        )
        
        listings = await self.provider.search(criteria)
        
        # All listings should be within price range
        for listing in listings:
            assert listing.price is not None
            assert 300000 <= listing.price <= 400000

    @pytest.mark.asyncio
    async def test_search_applies_bedroom_filters(self):
        """Test that search applies bedroom filters."""
        criteria = SearchCriteria(
            location="Springfield, IL",
            bedrooms_min=3,
            bedrooms_max=4
        )
        
        listings = await self.provider.search(criteria)
        
        # All listings should have 3-4 bedrooms
        for listing in listings:
            if listing.bedrooms is not None:
                assert 3 <= listing.bedrooms <= 4

    @pytest.mark.asyncio
    async def test_get_details_returns_details(self):
        """Test that get_details returns listing details."""
        details = await self.provider.get_details("mock_123")
        
        assert details is not None
        assert details.provider_listing_id == "mock_123"
        assert isinstance(details.description, str)
        assert isinstance(details.images, list)
        assert isinstance(details.features, list)

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check."""
        is_healthy = await self.provider.health_check()
        assert is_healthy is True

    def test_generate_mock_listing_structure(self):
        """Test that generated mock listings have correct structure."""
        criteria = SearchCriteria(location="Springfield, IL")
        
        listing = self.provider._generate_mock_listing(1, criteria)
        
        assert hasattr(listing, 'provider_listing_id')
        assert hasattr(listing, 'address')
        assert hasattr(listing, 'city')
        assert hasattr(listing, 'state')
        assert hasattr(listing, 'postal_code')
        assert hasattr(listing, 'price')
        assert hasattr(listing, 'property_type')
        assert hasattr(listing, 'status')


class TestCSVImportProvider:
    """Test cases for the CSVImportProvider."""

    def setup_method(self):
        """Set up test fixtures."""
        self.provider = CSVImportProvider()

    def test_provider_attributes(self):
        """Test provider attributes."""
        assert self.provider.name == "csv"
        assert self.provider.supports_search is True
        assert self.provider.supports_details is False
        assert self.provider.supports_images is False

    def test_parse_int_valid(self):
        """Test parsing valid integers."""
        assert self.provider._parse_int("123") == 123
        assert self.provider._parse_int("$250,000") == 250000
        assert self.provider._parse_int("0") == 0

    def test_parse_int_invalid(self):
        """Test parsing invalid integers."""
        assert self.provider._parse_int("") is None
        assert self.provider._parse_int("abc") is None
        assert self.provider._parse_int(None) is None

    def test_parse_float_valid(self):
        """Test parsing valid floats."""
        assert self.provider._parse_float("2.5") == 2.5
        assert self.provider._parse_float("$1,250.50") == 1250.5
        assert self.provider._parse_float("3.0") == 3.0

    def test_parse_float_invalid(self):
        """Test parsing invalid floats."""
        assert self.provider._parse_float("") is None
        assert self.provider._parse_float("abc") is None
        assert self.provider._parse_float(None) is None

    def test_parse_csv_row_complete(self):
        """Test parsing a complete CSV row."""
        row = {
            'id': '1',
            'address': '123 Main St, Springfield, IL 62701',
            'price': '$250,000',
            'bedrooms': '3',
            'bathrooms': '2.5',
            'sqft': '1500',
            'lot_sqft': '5000',
            'year_built': '2000',
            'property_type': 'Single Family',
            'status': 'Active',
            'url': 'https://example.com/1',
            'description': 'Nice house',
        }

        listing = self.provider._parse_csv_row(row, 1)

        assert listing.provider_listing_id == "csv_1_1"
        assert listing.address == "123 Main St"
        assert listing.city == "Springfield"
        assert listing.state == "IL"
        assert listing.postal_code == "62701"
        assert listing.price == 250000
        assert listing.bedrooms == 3
        assert listing.bathrooms == 2.5
        assert listing.sqft == 1500
        assert listing.lot_sqft == 5000
        assert listing.year_built == 2000
        assert listing.property_type == "single_family"
        assert listing.status == "active"

    def test_parse_csv_row_minimal(self):
        """Test parsing a minimal CSV row."""
        row = {
            'address': '123 Main St, Springfield, IL',
            'price': '200000',
            'property_type': 'condo',
            'status': 'active',
        }

        listing = self.provider._parse_csv_row(row, 1)

        assert listing.provider_listing_id == "csv_1_1"
        assert listing.address == "123 Main St"
        assert listing.price == 200000
        assert listing.property_type == "condo"
        assert listing.status == "active"
        assert listing.bedrooms is None
        assert listing.bathrooms is None

    def test_parse_csv_row_address_extraction(self):
        """Test address extraction from CSV row."""
        # Test with separate city/state columns
        row1 = {
            'address': '123 Main St',
            'city': 'Springfield',
            'state': 'IL',
            'postal_code': '62701',
            'price': '200000',
            'property_type': 'single_family',
            'status': 'active',
        }

        listing1 = self.provider._parse_csv_row(row1, 1)
        assert listing1.city == "Springfield"
        assert listing1.state == "IL"
        assert listing1.postal_code == "62701"

        # Test with address containing city/state
        row2 = {
            'address': '123 Main St, Springfield, IL 62701',
            'price': '200000',
            'property_type': 'single_family',
            'status': 'active',
        }

        listing2 = self.provider._parse_csv_row(row2, 2)
        assert listing2.city == "Springfield"
        assert listing2.state == "IL"
        assert listing2.postal_code == "62701"

    @pytest.mark.asyncio
    async def test_search_file_not_found(self):
        """Test search when CSV file doesn't exist."""
        with patch.object(self.provider, 'CSV_FILE_PATH', 'nonexistent.csv'):
            criteria = SearchCriteria(location="Springfield, IL")
            
            listings = await self.provider.search(criteria)
            
            assert listings == []


class TestOutlinkProvider:
    """Test cases for the OutlinkProvider."""

    def setup_method(self):
        """Set up test fixtures."""
        self.provider = OutlinkProvider()

    def test_provider_attributes(self):
        """Test provider attributes."""
        assert self.provider.name == "outlink"
        assert self.provider.supports_search is True
        assert self.provider.supports_details is False
        assert self.provider.supports_images is False

    @pytest.mark.asyncio
    async def test_search_returns_empty_list(self):
        """Test that search returns empty list (outlink provider doesn't return listings)."""
        criteria = SearchCriteria(location="Springfield, IL")
        
        listings = await self.provider.search(criteria)
        
        assert listings == []

    def test_generate_search_links(self):
        """Test generation of external search links."""
        criteria = SearchCriteria(
            location="Springfield, IL",
            min_price=200000,
            max_price=300000,
            bedrooms_min=3
        )
        
        links = self.provider.generate_search_links(criteria)
        
        assert len(links) == 3  # Should have links for zillow, redfin, realtor
        
        # Check that links contain expected domains
        assert any('zillow.com' in link for link in links)
        assert any('redfin.com' in link for link in links)
        assert any('realtor.com' in link for link in links)

    def test_build_zillow_url(self):
        """Test Zillow URL building."""
        criteria = SearchCriteria(
            location="Springfield, IL",
            min_price=200000,
            max_price=300000,
            bedrooms_min=3
        )
        
        url = self.provider._build_zillow_url(criteria)
        
        assert 'zillow.com' in url
        assert 'springfield-il' in url.lower()
        assert '200000-' in url  # Price range
        assert '3-beds' in url  # Bedroom filter

    def test_build_realtor_url(self):
        """Test Realtor.com URL building."""
        criteria = SearchCriteria(
            location="Springfield, IL",
            min_price=200000,
            max_price=300000
        )
        
        url = self.provider._build_realtor_url(criteria)
        
        assert 'realtor.com' in url
        assert 'priceMin=200000' in url
        assert 'priceMax=300000' in url

    def test_build_redfin_url(self):
        """Test Redfin URL building."""
        criteria = SearchCriteria(
            location="Springfield, IL",
            min_price=200000
        )
        
        url = self.provider._build_redfin_url(criteria)
        
        assert 'redfin.com' in url
        assert 'min_price=200000' in url

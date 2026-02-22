import pytest
from unittest.mock import Mock

from app.services.normalization import NormalizationService
from app.providers.base import ProviderListing


class TestNormalizationService:
    """Test cases for the NormalizationService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.normalization_service = NormalizationService()

    def test_normalize_property_type_single_family(self):
        """Test normalization of single family property types."""
        test_cases = [
            ("single family", "single_family"),
            ("Single-Family", "single_family"),
            ("single family home", "single_family"),
            ("SFR", "single_family"),
            ("house", "single_family"),
            ("detached", "single_family"),
        ]

        for input_type, expected in test_cases:
            result = self.normalization_service._normalize_property_type(input_type)
            assert result == expected, f"Failed for input: {input_type}"

    def test_normalize_property_type_condo(self):
        """Test normalization of condo property types."""
        test_cases = [
            ("condo", "condo"),
            ("condominium", "condo"),
            ("apartment", "condo"),
            ("unit", "condo"),
        ]

        for input_type, expected in test_cases:
            result = self.normalization_service._normalize_property_type(input_type)
            assert result == expected, f"Failed for input: {input_type}"

    def test_normalize_property_type_other(self):
        """Test normalization of other property types."""
        test_cases = [
            ("townhouse", "townhouse"),
            ("multi family", "multi_family"),
            ("land", "land"),
            ("commercial", "commercial"),
            ("unknown", "other"),
            ("", "other"),
        ]

        for input_type, expected in test_cases:
            result = self.normalization_service._normalize_property_type(input_type)
            assert result == expected, f"Failed for input: {input_type}"

    def test_normalize_status_active(self):
        """Test normalization of active status."""
        test_cases = [
            ("active", "active"),
            ("for sale", "active"),
            ("available", "active"),
            ("on market", "active"),
        ]

        for input_status, expected in test_cases:
            result = self.normalization_service._normalize_status(input_status)
            assert result == expected, f"Failed for input: {input_status}"

    def test_normalize_status_pending(self):
        """Test normalization of pending status."""
        test_cases = [
            ("pending", "pending"),
            ("pending sale", "pending"),
            ("under contract", "pending"),
            ("contingent", "pending"),
        ]

        for input_status, expected in test_cases:
            result = self.normalization_service._normalize_status(input_status)
            assert result == expected, f"Failed for input: {input_status}"

    def test_normalize_status_sold(self):
        """Test normalization of sold status."""
        test_cases = [
            ("sold", "sold"),
            ("closed", "sold"),
            ("sale closed", "sold"),
        ]

        for input_status, expected in test_cases:
            result = self.normalization_service._normalize_status(input_status)
            assert result == expected, f"Failed for input: {input_status}"

    def test_normalize_address_text(self):
        """Test address text normalization."""
        test_cases = [
            ("123 Main St, Springfield, IL", "123 main st springfield il"),
            ("456 Oak Avenue", "456 oak ave"),
            ("789 Pine Road #4A", "789 pine rd #4a"),
            ("", ""),
            ("  Extra   Spaces  ", "extra spaces"),
        ]

        for input_address, expected in test_cases:
            result = self.normalization_service._normalize_address_text(input_address)
            assert result == expected, f"Failed for input: {input_address}"

    def test_generate_canonical_key_with_coordinates(self):
        """Test canonical key generation with coordinates."""
        provider_listing = ProviderListing(
            provider_listing_id="test_1",
            address="123 Main St, Springfield, IL 62701",
            city="Springfield",
            state="IL",
            postal_code="62701",
            latitude=39.781721,
            longitude=-89.650148,
            price=200000,
            property_type="single_family",
            status="active",
        )

        canonical_key = self.normalization_service._generate_canonical_key(provider_listing)
        
        expected = "123 main st springfield il 62701|39.781721|-89.650148"
        assert canonical_key == expected

    def test_generate_canonical_key_without_coordinates(self):
        """Test canonical key generation without coordinates."""
        provider_listing = ProviderListing(
            provider_listing_id="test_1",
            address="123 Main St, Springfield, IL 62701",
            city="Springfield",
            state="IL",
            postal_code="62701",
            latitude=None,
            longitude=None,
            price=200000,
            property_type="single_family",
            status="active",
        )

        canonical_key = self.normalization_service._generate_canonical_key(provider_listing)
        
        expected = "123 main st springfield il 62701"
        assert canonical_key == expected

    def test_parse_address_simple(self):
        """Test simple address parsing."""
        address = "123 Main St, Springfield, IL 62701"
        result = self.normalization_service._parse_address(address)
        
        assert result["line1"] == "123 Main St"
        assert result.get("line2") is None

    def test_parse_address_with_line2(self):
        """Test address parsing with line 2."""
        address = "123 Main St, Apt 4B, Springfield, IL 62701"
        result = self.normalization_service._parse_address(address)
        
        assert result["line1"] == "123 Main St"
        assert result["line2"] == "Apt 4B"

    def test_normalize_listing_complete(self):
        """Test complete listing normalization."""
        provider_listing = ProviderListing(
            provider_listing_id="test_1",
            address="123 Main St, Springfield, IL 62701",
            city="Springfield",
            state="IL",
            postal_code="62701",
            latitude=39.781721,
            longitude=-89.650148,
            price=200000,
            bedrooms=3,
            bathrooms=2.5,
            sqft=1500,
            lot_sqft=5000,
            year_built=2000,
            property_type="Single Family Home",
            status="For Sale",
            description="Beautiful family home",
            images=["image1.jpg", "image2.jpg"],
        )

        listing = self.normalization_service.normalize_listing(provider_listing, "mock")
        
        assert listing.address_line1 == "123 Main St"
        assert listing.city == "Springfield"
        assert listing.state == "IL"
        assert listing.postal_code == "62701"
        assert listing.property_type == "single_family"
        assert listing.status == "active"
        assert listing.list_price == 200000
        assert listing.bedrooms == 3
        assert listing.bathrooms == 2.5
        assert listing.sqft == 1500
        assert listing.lot_sqft == 5000
        assert listing.year_built == 2000
        assert listing.description == "Beautiful family home"
        assert listing.images == ["image1.jpg", "image2.jpg"]

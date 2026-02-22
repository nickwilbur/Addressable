import pytest
from unittest.mock import Mock, patch

from app.services.deduplication import DeduplicationService
from app.providers.base import ProviderListing
from app.models.listing import Listing
from app.models.listing_source import ListingSource
from uuid import uuid4


class TestDeduplicationService:
    """Test cases for the DeduplicationService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.deduplication_service = DeduplicationService()

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

        canonical_key = self.deduplication_service._generate_canonical_key(provider_listing)
        
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

        canonical_key = self.deduplication_service._generate_canonical_key(provider_listing)
        
        expected = "123 main st springfield il 62701"
        assert canonical_key == expected

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
            result = self.deduplication_service._normalize_address_text(input_address)
            assert result == expected, f"Failed for input: {input_address}"

    def test_select_best_canonical_listing_by_data_completeness(self):
        """Test selecting best canonical listing based on data completeness."""
        # Create mock listings with different data completeness
        complete_listing = ProviderListing(
            provider_listing_id="complete",
            address="123 Main St",
            city="Springfield",
            state="IL",
            postal_code="62701",
            price=200000,
            bedrooms=3,
            bathrooms=2.5,
            sqft=1500,
            year_built=2000,
            description="Complete listing",
            images=["img1.jpg", "img2.jpg"],
            latitude=39.781721,
            longitude=-89.650148,
            property_type="single_family",
            status="active",
        )

        minimal_listing = ProviderListing(
            provider_listing_id="minimal",
            address="123 Main St",
            city="Springfield",
            state="IL",
            postal_code="62701",
            price=200000,
            property_type="single_family",
            status="active",
        )

        group = [
            (minimal_listing, "mock", uuid4()),
            (complete_listing, "mock", uuid4()),
        ]

        with patch('app.services.normalization.NormalizationService') as mock_normalization:
            mock_listing = Mock()
            mock_listing.id = uuid4()
            mock_normalization.return_value.normalize_listing.return_value = mock_listing

            result = self.deduplication_service._select_best_canonical_listing(group)

            # Should select the complete listing
            mock_normalization.return_value.normalize_listing.assert_called_with(complete_listing, "mock")

    def test_select_best_canonical_listing_by_provider_preference(self):
        """Test selecting best canonical listing based on provider preference."""
        zillow_listing = ProviderListing(
            provider_listing_id="zillow_1",
            address="123 Main St",
            city="Springfield",
            state="IL",
            postal_code="62701",
            price=200000,
            property_type="single_family",
            status="active",
        )

        mock_listing = ProviderListing(
            provider_listing_id="mock_1",
            address="123 Main St",
            city="Springfield",
            state="IL",
            postal_code="62701",
            price=200000,
            property_type="single_family",
            status="active",
        )

        group = [
            (mock_listing, "mock", uuid4()),
            (zillow_listing, "zillow", uuid4()),
        ]

        with patch('app.services.normalization.NormalizationService') as mock_normalization:
            mock_result = Mock()
            mock_result.id = uuid4()
            mock_normalization.return_value.normalize_listing.return_value = mock_result

            result = self.deduplication_service._select_best_canonical_listing(group)

            # Should select the zillow listing due to provider preference
            mock_normalization.return_value.normalize_listing.assert_called_with(zillow_listing, "zillow")

    def test_deduplicate_listings_same_address_same_coordinates(self):
        """Test deduplication of listings with same address and coordinates."""
        listing1 = ProviderListing(
            provider_listing_id="provider1_1",
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

        listing2 = ProviderListing(
            provider_listing_id="provider2_1",
            address="123 Main St, Springfield, IL 62701",
            city="Springfield",
            state="IL",
            postal_code="62701",
            latitude=39.781721,
            longitude=-89.650148,
            price=210000,  # Different price
            property_type="single_family",
            status="active",
        )

        provider_listings = [
            (listing1, "provider1", uuid4()),
            (listing2, "provider2", uuid4()),
        ]

        with patch('app.services.normalization.NormalizationService') as mock_normalization:
            mock_canonical = Mock()
            mock_canonical.id = uuid4()
            mock_normalization.return_value.normalize_listing.return_value = mock_canonical
            mock_normalization.return_value.create_listing_source.return_value = Mock()

            canonical_listings, listing_sources = self.deduplication_service.deduplicate_listings(provider_listings)

            # Should result in 1 canonical listing and 2 sources
            assert len(canonical_listings) == 1
            assert len(listing_sources) == 2

    def test_deduplicate_listings_different_addresses(self):
        """Test deduplication of listings with different addresses."""
        listing1 = ProviderListing(
            provider_listing_id="provider1_1",
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

        listing2 = ProviderListing(
            provider_listing_id="provider2_1",
            address="456 Oak Ave, Springfield, IL 62701",
            city="Springfield",
            state="IL",
            postal_code="62701",
            latitude=39.782721,
            longitude=-89.651148,
            price=250000,
            property_type="single_family",
            status="active",
        )

        provider_listings = [
            (listing1, "provider1", uuid4()),
            (listing2, "provider2", uuid4()),
        ]

        with patch('app.services.normalization.NormalizationService') as mock_normalization:
            mock_canonical1 = Mock()
            mock_canonical1.id = uuid4()
            mock_canonical2 = Mock()
            mock_canonical2.id = uuid4()
            
            mock_normalization.return_value.normalize_listing.side_effect = [mock_canonical1, mock_canonical2]
            mock_normalization.return_value.create_listing_source.return_value = Mock()

            canonical_listings, listing_sources = self.deduplication_service.deduplicate_listings(provider_listings)

            # Should result in 2 canonical listings and 2 sources
            assert len(canonical_listings) == 2
            assert len(listing_sources) == 2

    def test_are_addresses_similar_text_match(self):
        """Test address similarity detection by text matching."""
        listing1 = Mock()
        listing1.address_line1 = "123 Main St"
        listing1.city = "Springfield"
        listing1.state = "IL"
        listing1.latitude = None
        listing1.longitude = None

        listing2 = Mock()
        listing2.address_line1 = "123 Main St"
        listing2.city = "Springfield"
        listing2.state = "IL"
        listing2.latitude = None
        listing2.longitude = None

        result = self.deduplication_service._are_addresses_similar(listing1, listing2)
        assert result is True

    def test_are_addresses_similar_coordinates(self):
        """Test address similarity detection by coordinates."""
        listing1 = Mock()
        listing1.address_line1 = "123 Main St"
        listing1.city = "Springfield"
        listing1.state = "IL"
        listing1.latitude = 39.781721
        listing1.longitude = -89.650148

        listing2 = Mock()
        listing2.address_line1 = "123 Main Street"
        listing2.city = "Springfield"
        listing2.state = "IL"
        listing2.latitude = 39.781722  # Very close coordinates
        listing2.longitude = -89.650149

        result = self.deduplication_service._are_addresses_similar(listing1, listing2)
        assert result is True

    def test_are_addresses_not_similar(self):
        """Test address similarity detection for non-similar addresses."""
        listing1 = Mock()
        listing1.address_line1 = "123 Main St"
        listing1.city = "Springfield"
        listing1.state = "IL"
        listing1.latitude = 39.781721
        listing1.longitude = -89.650148

        listing2 = Mock()
        listing2.address_line1 = "456 Oak Ave"
        listing2.city = "Springfield"
        listing2.state = "IL"
        listing2.latitude = 39.791721  # Different coordinates
        listing2.longitude = -89.660148

        result = self.deduplication_service._are_addresses_similar(listing1, listing2)
        assert result is False

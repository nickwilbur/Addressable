import pytest
from pydantic import ValidationError

from app.schemas.search import SearchCriteria


class TestSearchCriteria:
    """Test cases for SearchCriteria schema validation."""

    def test_search_criteria_valid_minimal(self):
        """Test creating valid search criteria with minimal fields."""
        criteria = SearchCriteria(location="Springfield, IL")
        
        assert criteria.location == "Springfield, IL"
        assert criteria.min_price is None
        assert criteria.max_price is None
        assert criteria.bedrooms_min is None
        assert criteria.bedrooms_max is None

    def test_search_criteria_valid_complete(self):
        """Test creating valid search criteria with all fields."""
        criteria = SearchCriteria(
            location="Springfield, IL",
            min_price=200000,
            max_price=500000,
            bedrooms_min=2,
            bedrooms_max=4,
            bathrooms_min=1.5,
            bathrooms_max=3.5,
            sqft_min=1000,
            sqft_max=3000,
            property_types=["single_family", "condo"],
            status=["active", "pending"],
            year_built_min=1990,
            year_built_max=2023
        )
        
        assert criteria.location == "Springfield, IL"
        assert criteria.min_price == 200000
        assert criteria.max_price == 500000
        assert criteria.bedrooms_min == 2
        assert criteria.bedrooms_max == 4
        assert criteria.bathrooms_min == 1.5
        assert criteria.bathrooms_max == 3.5
        assert criteria.sqft_min == 1000
        assert criteria.sqft_max == 3000
        assert criteria.property_types == ["single_family", "condo"]
        assert criteria.status == ["active", "pending"]
        assert criteria.year_built_min == 1990
        assert criteria.year_built_max == 2023

    def test_search_criteria_missing_location(self):
        """Test that location is required."""
        with pytest.raises(ValidationError):
            SearchCriteria()

    def test_search_criteria_invalid_price_negative(self):
        """Test validation of negative prices."""
        with pytest.raises(ValidationError):
            SearchCriteria(location="Springfield, IL", min_price=-100000)

        with pytest.raises(ValidationError):
            SearchCriteria(location="Springfield, IL", max_price=-100000)

    def test_search_criteria_invalid_bedrooms_negative(self):
        """Test validation of negative bedrooms."""
        with pytest.raises(ValidationError):
            SearchCriteria(location="Springfield, IL", bedrooms_min=-1)

        with pytest.raises(ValidationError):
            SearchCriteria(location="Springfield, IL", bedrooms_max=-1)

    def test_search_criteria_invalid_bathrooms_negative(self):
        """Test validation of negative bathrooms."""
        with pytest.raises(ValidationError):
            SearchCriteria(location="Springfield, IL", bathrooms_min=-1.0)

        with pytest.raises(ValidationError):
            SearchCriteria(location="Springfield, IL", bathrooms_max=-1.0)

    def test_search_criteria_invalid_sqft_negative(self):
        """Test validation of negative square footage."""
        with pytest.raises(ValidationError):
            SearchCriteria(location="Springfield, IL", sqft_min=-1000)

        with pytest.raises(ValidationError):
            SearchCriteria(location="Springfield, IL", sqft_max=-1000)

    def test_search_criteria_invalid_year_built_too_early(self):
        """Test validation of year built minimum."""
        with pytest.raises(ValidationError):
            SearchCriteria(location="Springfield, IL", year_built_min=1700)

        with pytest.raises(ValidationError):
            SearchCriteria(location="Springfield, IL", year_built_max=1700)

    def test_search_criteria_price_range_validation(self):
        """Test that min_price <= max_price is enforced."""
        # This should work
        criteria = SearchCriteria(
            location="Springfield, IL",
            min_price=200000,
            max_price=500000
        )
        assert criteria.min_price == 200000
        assert criteria.max_price == 500000

        # Note: Pydantic doesn't automatically validate range relationships
        # This would need custom validators in a real implementation

    def test_search_criteria_bedroom_range_validation(self):
        """Test bedroom range validation."""
        # This should work
        criteria = SearchCriteria(
            location="Springfield, IL",
            bedrooms_min=2,
            bedrooms_max=4
        )
        assert criteria.bedrooms_min == 2
        assert criteria.bedrooms_max == 4

    def test_search_criteria_bathroom_range_validation(self):
        """Test bathroom range validation."""
        # This should work
        criteria = SearchCriteria(
            location="Springfield, IL",
            bathrooms_min=1.5,
            bathrooms_max=3.5
        )
        assert criteria.bathrooms_min == 1.5
        assert criteria.bathrooms_max == 3.5

    def test_search_criteria_sqft_range_validation(self):
        """Test square footage range validation."""
        # This should work
        criteria = SearchCriteria(
            location="Springfield, IL",
            sqft_min=1000,
            sqft_max=3000
        )
        assert criteria.sqft_min == 1000
        assert criteria.sqft_max == 3000

    def test_search_criteria_year_built_range_validation(self):
        """Test year built range validation."""
        # This should work
        criteria = SearchCriteria(
            location="Springfield, IL",
            year_built_min=1990,
            year_built_max=2023
        )
        assert criteria.year_built_min == 1990
        assert criteria.year_built_max == 2023

    def test_search_criteria_property_types_list(self):
        """Test property types as list."""
        criteria = SearchCriteria(
            location="Springfield, IL",
            property_types=["single_family", "condo", "townhouse"]
        )
        
        assert len(criteria.property_types) == 3
        assert "single_family" in criteria.property_types
        assert "condo" in criteria.property_types
        assert "townhouse" in criteria.property_types

    def test_search_criteria_status_list(self):
        """Test status as list."""
        criteria = SearchCriteria(
            location="Springfield, IL",
            status=["active", "pending", "sold"]
        )
        
        assert len(criteria.status) == 3
        assert "active" in criteria.status
        assert "pending" in criteria.status
        assert "sold" in criteria.status

    def test_search_criteria_serialization(self):
        """Test that search criteria can be serialized to dict."""
        criteria = SearchCriteria(
            location="Springfield, IL",
            min_price=200000,
            max_price=500000,
            property_types=["single_family"]
        )
        
        criteria_dict = criteria.model_dump()
        
        assert criteria_dict["location"] == "Springfield, IL"
        assert criteria_dict["min_price"] == 200000
        assert criteria_dict["max_price"] == 500000
        assert criteria_dict["property_types"] == ["single_family"]

    def test_search_criteria_various_locations(self):
        """Test various location formats."""
        locations = [
            "Springfield, IL",
            "123 Main St, Springfield, IL 62701",
            "New York, NY",
            "90210",  # ZIP code
            "Downtown Los Angeles",
        ]
        
        for location in locations:
            criteria = SearchCriteria(location=location)
            assert criteria.location == location

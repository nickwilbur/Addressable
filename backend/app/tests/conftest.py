import pytest
import asyncio
from unittest.mock import Mock

from app.db.engine import engine
from app.db.session import get_db


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mock_db():
    """Mock database session for testing."""
    session = Mock()
    session.add = Mock()
    session.commit = Mock()
    session.refresh = Mock()
    session.execute = Mock()
    session.scalar = Mock()
    session.scalar_one_or_none = Mock()
    session.scalars = Mock()
    
    yield session


@pytest.fixture
def sample_provider_listing():
    """Sample provider listing for testing."""
    from app.providers.base import ProviderListing
    
    return ProviderListing(
        provider_listing_id="test_123",
        address="123 Main St, Springfield, IL 62701",
        city="Springfield",
        state="IL",
        postal_code="62701",
        latitude=39.781721,
        longitude=-89.650148,
        price=250000,
        bedrooms=3,
        bathrooms=2.5,
        sqft=1500,
        lot_sqft=5000,
        year_built=2000,
        property_type="single_family",
        status="active",
        url="https://example.com/123",
        description="Beautiful family home",
        images=["image1.jpg", "image2.jpg"],
    )


@pytest.fixture
def sample_search_criteria():
    """Sample search criteria for testing."""
    from app.schemas.search import SearchCriteria
    
    return SearchCriteria(
        location="Springfield, IL",
        min_price=200000,
        max_price=300000,
        bedrooms_min=2,
        bedrooms_max=4,
        property_types=["single_family", "condo"],
        status=["active"]
    )


@pytest.fixture
def mock_raw_payload():
    """Mock raw payload for testing."""
    from app.models.raw_payload import RawPayload
    from uuid import uuid4
    
    return RawPayload(
        id=uuid4(),
        provider_name="mock",
        request_json={"location": "Springfield, IL"},
        response_json={"listings": []},
        http_status=200,
        response_hash="abc123",
        response_size_bytes=1000,
    )

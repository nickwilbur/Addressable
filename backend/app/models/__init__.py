from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass

from .search_query import SearchQuery
from .provider_run import ProviderRun
from .raw_payload import RawPayload
from .listing import Listing
from .listing_source import ListingSource

__all__ = [
    "Base",
    "SearchQuery",
    "ProviderRun", 
    "RawPayload",
    "Listing",
    "ListingSource",
]

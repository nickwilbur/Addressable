from .base import Provider, ProviderListing, ProviderListingDetail
from .mock import MockProvider
from .csv_import import CSVImportProvider
from .outlink import OutlinkProvider
from .zillow import ZillowProvider
from .realtor import RealtorProvider
from .redfin import RedfinProvider

# Registry of available providers
PROVIDERS = {
    "mock": MockProvider,
    "csv": CSVImportProvider,
    "outlink": OutlinkProvider,
    "zillow": ZillowProvider,
    "realtor": RealtorProvider,
    "redfin": RedfinProvider,
}

# Real estate providers that return actual listings
REAL_ESTATE_PROVIDERS = {
    "zillow": ZillowProvider,
    "realtor": RealtorProvider,
    "redfin": RedfinProvider,
}

__all__ = [
    "Provider",
    "ProviderListing", 
    "ProviderListingDetail",
    "PROVIDERS",
    "REAL_ESTATE_PROVIDERS",
    "MockProvider",
    "CSVImportProvider",
    "OutlinkProvider",
    "ZillowProvider",
    "RealtorProvider",
    "RedfinProvider",
]

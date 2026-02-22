from typing import List, Optional
from pydantic import BaseModel, Field


class ProviderCapability(BaseModel):
    """Provider capabilities."""
    supports_search: bool = Field(default=False, description="Supports property search")
    supports_details: bool = Field(default=False, description="Supports listing details")
    supports_images: bool = Field(default=False, description="Supports image scraping")
    rate_limit_per_minute: Optional[int] = Field(None, description="Rate limit per minute")
    timeout_seconds: int = Field(default=10, description="Request timeout in seconds")


class ProviderInfo(BaseModel):
    """Information about a data provider."""
    name: str
    display_name: str
    description: str
    enabled: bool
    capabilities: ProviderCapability
    last_run_status: Optional[str] = None
    last_run_at: Optional[str] = None
    average_response_time_ms: Optional[int] = None

from pydantic import BaseModel
from typing import Optional


class LocationSuggestion(BaseModel):
    """Location suggestion for autocomplete."""
    city: str
    state: str
    display_name: str
    confidence: Optional[float] = None


class LocationSuggestionResponse(BaseModel):
    """Response containing location suggestions."""
    suggestions: list[LocationSuggestion]
    query: str

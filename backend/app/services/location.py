from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import structlog

from app.schemas.location import LocationSuggestion

logger = structlog.get_logger()


class LocationService:
    """Service for location-related operations."""
    
    def __init__(self):
        pass
    
    async def get_location_suggestions(
        self, 
        query: str, 
        limit: int, 
        db: AsyncSession
    ) -> List[LocationSuggestion]:
        """
        Get location suggestions based on query.
        
        For now, return a static list of common US cities.
        In a real implementation, this would query a database or external API.
        """
        # Static data for demo purposes
        cities = [
            ("New York", "NY"),
            ("Los Angeles", "CA"),
            ("Chicago", "IL"),
            ("Houston", "TX"),
            ("Phoenix", "AZ"),
            ("Philadelphia", "PA"),
            ("San Antonio", "TX"),
            ("San Diego", "CA"),
            ("Dallas", "TX"),
            ("San Jose", "CA"),
            ("Austin", "TX"),
            ("Jacksonville", "FL"),
            ("Fort Worth", "TX"),
            ("Columbus", "OH"),
            ("Charlotte", "NC"),
            ("San Francisco", "CA"),
            ("Indianapolis", "IN"),
            ("Seattle", "WA"),
            ("Denver", "CO"),
            ("Washington", "DC"),
            ("Boston", "MA"),
            ("El Paso", "TX"),
            ("Nashville", "TN"),
            ("Oklahoma City", "OK"),
            ("Las Vegas", "NV"),
            ("Detroit", "MI"),
            ("Portland", "OR"),
            ("Memphis", "TN"),
            ("Louisville", "KY"),
            ("Milwaukee", "WI"),
            ("Baltimore", "MD"),
            ("Albuquerque", "NM"),
            ("Tucson", "AZ"),
            ("Fresno", "CA"),
            ("Sacramento", "CA"),
            ("Kansas City", "MO"),
            ("Mesa", "AZ"),
            ("Atlanta", "GA"),
            ("Omaha", "NE"),
            ("Colorado Springs", "CO"),
            ("Raleigh", "NC"),
            ("Long Beach", "CA"),
            ("Virginia Beach", "VA"),
            ("Miami", "FL"),
            ("Oakland", "CA"),
            ("Minneapolis", "MN"),
            ("Tampa", "FL"),
            ("Tulsa", "OK"),
            ("Arlington", "TX"),
            ("Wichita", "KS"),
            ("New Orleans", "LA"),
        ]
        
        query_lower = query.lower()
        suggestions = []
        
        for city, state in cities:
            # Match on city name or state
            if (query_lower in city.lower() or 
                query_lower in state.lower() or
                city.lower().startswith(query_lower)):
                
                display_name = f"{city}, {state}"
                confidence = self._calculate_confidence(query, city, state)
                
                suggestions.append(LocationSuggestion(
                    city=city,
                    state=state,
                    display_name=display_name,
                    confidence=confidence
                ))
        
        # Sort by confidence and limit results
        suggestions.sort(key=lambda x: x.confidence or 0, reverse=True)
        return suggestions[:limit]
    
    def _calculate_confidence(self, query: str, city: str, state: str) -> float:
        """Calculate confidence score for a location match."""
        query_lower = query.lower()
        city_lower = city.lower()
        state_lower = state.lower()
        
        # Exact city match gets highest score
        if query_lower == city_lower:
            return 1.0
        
        # City starts with query gets high score
        if city_lower.startswith(query_lower):
            return 0.9
        
        # Query contains city name gets medium score
        if query_lower in city_lower:
            return 0.7
        
        # State match gets lower score
        if query_lower == state_lower:
            return 0.6
        
        # Partial match gets lowest score
        if query_lower in city_lower or query_lower in state_lower:
            return 0.4
        
        return 0.1

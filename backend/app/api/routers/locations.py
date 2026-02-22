from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import structlog

from app.db.session import get_db
from app.schemas.location import LocationSuggestion
from app.services.location import LocationService

router = APIRouter()
logger = structlog.get_logger()


@router.get("/locations/suggest", response_model=List[LocationSuggestion])
async def suggest_locations(
    query: str = Query(..., min_length=2, description="Search query for location"),
    limit: int = Query(10, ge=1, le=20, description="Maximum number of suggestions"),
    db: AsyncSession = Depends(get_db),
):
    """Get location suggestions based on city and state."""
    try:
        location_service = LocationService()
        suggestions = await location_service.get_location_suggestions(query, limit, db)
        return suggestions
        
    except Exception as e:
        logger.error("Failed to get location suggestions", query=query, error=str(e))
        # Return empty list instead of error to avoid breaking UI
        return []

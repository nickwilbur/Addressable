from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import structlog

from app.db.session import get_db
from app.schemas.listing import ListingDetail
from app.models.listing import Listing
from app.models.listing_source import ListingSource
from sqlalchemy import select

router = APIRouter()
logger = structlog.get_logger()


@router.get("/listings/{listing_id}", response_model=ListingDetail)
async def get_listing_detail(
    listing_id: UUID = Path(..., description="Listing ID"),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed information for a specific listing."""
    try:
        # Get listing
        result = await db.execute(
            select(Listing).where(Listing.id == listing_id)
        )
        listing = result.scalar_one_or_none()
        
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")
        
        # Get all sources for this listing
        sources_result = await db.execute(
            select(ListingSource).where(ListingSource.listing_id == listing_id)
        )
        sources = sources_result.scalars().all()
        
        # Convert to response model
        listing_detail = ListingDetail(
            id=listing.id,
            canonical_key=listing.canonical_key,
            address={
                "line1": listing.address_line1,
                "line2": listing.address_line2,
                "city": listing.city,
                "state": listing.state,
                "postal_code": listing.postal_code,
                "country": listing.country,
            },
            location={
                "latitude": float(listing.latitude) if listing.latitude else None,
                "longitude": float(listing.longitude) if listing.longitude else None,
            },
            details={
                "property_type": listing.property_type,
                "bedrooms": listing.bedrooms,
                "bathrooms": float(listing.bathrooms) if listing.bathrooms else None,
                "sqft": listing.sqft,
                "lot_sqft": listing.lot_sqft,
                "year_built": listing.year_built,
                "description": listing.description,
            },
            status=listing.status,
            list_price=listing.list_price,
            first_seen_at=listing.first_seen_at,
            last_seen_at=listing.last_seen_at,
            images=listing.images,
            sources=[
                {
                    "provider_name": source.provider_name,
                    "provider_listing_id": source.provider_listing_id,
                    "source_url": source.source_url,
                    "list_price": source.list_price,
                    "status": source.status,
                    "first_seen_at": source.first_seen_at,
                    "last_seen_at": source.last_seen_at,
                }
                for source in sources
            ],
        )
        
        return listing_detail
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get listing detail", listing_id=str(listing_id), error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import structlog

from app.db.session import get_db
from app.schemas.search import SearchRequest, SearchResponse, SearchCriteria
from app.schemas.common import PaginationParams
from app.services.search import SearchService
from app.models.search_query import SearchMode
from app.core.errors import AddressableException, http_exception_from_addressable

router = APIRouter()
logger = structlog.get_logger()


@router.post("/search", response_model=SearchResponse)
async def create_search(
    search_request: SearchRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create and execute a new property search."""
    try:
        search_service = SearchService()
        
        # Create search query
        search_query = await search_service.create_search(
            criteria=search_request.criteria,
            mode=SearchMode(search_request.mode),
            db=db,
        )
        
        # Execute search
        search_response = await search_service.execute_search(
            search_query,
            db,
        )
        
        return search_response
        
    except AddressableException as e:
        logger.error("Search failed", error=str(e))
        raise http_exception_from_addressable(e)
    except Exception as e:
        logger.error("Unexpected error in search", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/search/{search_query_id}", response_model=SearchResponse)
async def get_search_results(
    search_query_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated results for a completed search."""
    try:
        search_service = SearchService()
        
        pagination = PaginationParams(page=page, page_size=page_size)
        search_response = await search_service.get_search_results(
            search_query_id=search_query_id,
            pagination=pagination,
            db=db,
        )
        
        return search_response
        
    except ValueError as e:
        logger.error("Search not found", search_query_id=search_query_id, error=str(e))
        raise HTTPException(status_code=404, detail=str(e))
    except AddressableException as e:
        logger.error("Failed to get search results", error=str(e))
        raise http_exception_from_addressable(e)
    except Exception as e:
        logger.error("Unexpected error getting search results", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/search")
async def quick_search(
    location: str = Query(..., description="Location to search"),
    min_price: Optional[int] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[int] = Query(None, ge=0, description="Maximum price"),
    bedrooms_min: Optional[int] = Query(None, ge=0, description="Minimum bedrooms"),
    bedrooms_max: Optional[int] = Query(None, ge=0, description="Maximum bedrooms"),
    bathrooms_min: Optional[float] = Query(None, ge=0, description="Minimum bathrooms"),
    bathrooms_max: Optional[float] = Query(None, ge=0, description="Maximum bathrooms"),
    sqft_min: Optional[int] = Query(None, ge=0, description="Minimum square feet"),
    sqft_max: Optional[int] = Query(None, ge=0, description="Maximum square feet"),
    property_types: Optional[str] = Query(None, description="Property types (comma-separated)"),
    status: Optional[str] = Query(None, description="Listing statuses (comma-separated)"),
    year_built_min: Optional[int] = Query(None, ge=1800, description="Minimum year built"),
    year_built_max: Optional[int] = Query(None, ge=1800, description="Maximum year built"),
    mode: str = Query("sync", description="Search mode: sync or async"),
    db: AsyncSession = Depends(get_db),
):
    """Quick search using query parameters."""
    try:
        # Build search criteria
        criteria = SearchCriteria(
            location=location,
            min_price=min_price,
            max_price=max_price,
            bedrooms_min=bedrooms_min,
            bedrooms_max=bedrooms_max,
            bathrooms_min=bathrooms_min,
            bathrooms_max=bathrooms_max,
            sqft_min=sqft_min,
            sqft_max=sqft_max,
            property_types=property_types.split(',') if property_types else None,
            status=status.split(',') if status else None,
            year_built_min=year_built_min,
            year_built_max=year_built_max,
        )
        
        search_request = SearchRequest(criteria=criteria, mode=mode)
        
        # Execute search
        search_service = SearchService()
        search_query = await search_service.create_search(
            criteria=criteria,
            mode=SearchMode(mode),
            db=db,
        )
        
        search_response = await search_service.execute_search(
            search_query,
            db,
        )
        
        return search_response
        
    except AddressableException as e:
        logger.error("Quick search failed", error=str(e))
        raise http_exception_from_addressable(e)
    except Exception as e:
        logger.error("Unexpected error in quick search", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

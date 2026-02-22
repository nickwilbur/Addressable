import asyncio
from datetime import datetime, timezone
from typing import List, Optional, Dict
from uuid import UUID
import structlog

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func

from app.schemas.search import SearchCriteria, SearchResponse, SearchSummary
from app.schemas.common import PaginationParams, PaginatedResponse
from app.models.search_query import SearchQuery, SearchMode, SearchStatus
from app.models.provider_run import ProviderRun, ProviderRunStatus
from app.models.raw_payload import RawPayload
from app.models.listing import Listing
from app.models.listing_source import ListingSource
from app.providers.base import ProviderListing
from app.services.provider_manager import provider_manager
from app.services.normalization import NormalizationService
from app.services.deduplication import DeduplicationService
from app.core.settings import settings
from app.core.errors import ProviderException, TimeoutException

logger = structlog.get_logger()


class SearchService:
    """Service for managing property searches across multiple providers."""
    
    def __init__(self):
        self.logger = structlog.get_logger()
        self.normalization_service = NormalizationService()
        self.deduplication_service = DeduplicationService()
    
    async def create_search(
        self,
        criteria: SearchCriteria,
        mode: SearchMode = SearchMode.SYNC,
        db: AsyncSession = None,
    ) -> SearchQuery:
        """Create a new search query."""
        search_query = SearchQuery(
            criteria_json=criteria.model_dump(),
            mode=mode,
            status=SearchStatus.PENDING,
            total_providers=len(provider_manager.get_search_providers()),
        )
        
        db.add(search_query)
        await db.commit()
        await db.refresh(search_query)
        
        self.logger.info(
            "Search query created",
            search_query_id=search_query.id,
            mode=mode,
            providers=search_query.total_providers,
        )
        
        return search_query
    
    async def execute_search(
        self,
        search_query: SearchQuery,
        db: AsyncSession,
    ) -> SearchResponse:
        """Execute search across all enabled providers."""
        try:
            # Update status to running
            search_query.status = SearchStatus.RUNNING
            await db.commit()
            
            start_time = datetime.now(timezone.utc)
            
            # Get search providers
            criteria = SearchCriteria(**search_query.criteria_json)
            search_providers = provider_manager.get_search_providers(criteria.providers)
            
            self.logger.info(
                "Starting search execution",
                search_query_id=search_query.id,
                providers=len(search_providers),
            )
            
            # Execute provider searches concurrently
            provider_results = await self._execute_provider_searches(
                search_query,
                search_providers,
                criteria,
                db,
            )
            
            # Process and deduplicate results
            canonical_listings, listing_sources = await self._process_search_results(
                provider_results,
                search_query,
                db,
            )
            
            # Update search query with results
            end_time = datetime.now(timezone.utc)
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            search_query.status = SearchStatus.COMPLETED
            search_query.completed_providers = len(provider_results)
            search_query.total_listings = len(canonical_listings)
            search_query.updated_at = end_time
            
            await db.commit()
            
            # Generate external search links
            outlink_provider = provider_manager.get_provider("outlink")
            external_links = outlink_provider.generate_search_links(criteria)
            
            # Create search summary
            search_summary = SearchSummary(
                search_query_id=search_query.id,
                status=search_query.status.value,
                total_providers=search_query.total_providers,
                completed_providers=search_query.completed_providers,
                total_listings=search_query.total_listings,
                duration_ms=duration_ms,
            )
            
            self.logger.info(
                "Search execution completed",
                search_query_id=search_query.id,
                duration_ms=duration_ms,
                listings_found=len(canonical_listings),
            )
            
            # Return paginated response (first page)
            paginated_response = PaginatedResponse.create(
                items=canonical_listings,
                total_count=len(canonical_listings),
                params=PaginationParams(page=1, page_size=20),
            )
            
            return SearchResponse(
                items=paginated_response.items,
                pagination=paginated_response.pagination,
                search_summary=search_summary,
                external_search_links=external_links,
            )
            
        except Exception as e:
            # Update search query with error
            search_query.status = SearchStatus.FAILED
            search_query.error_text = str(e)
            await db.commit()
            
            self.logger.error(
                "Search execution failed",
                search_query_id=search_query.id,
                error=str(e),
            )
            raise
    
    async def get_search_results(
        self,
        search_query_id: UUID,
        pagination: PaginationParams,
        db: AsyncSession,
    ) -> SearchResponse:
        """Get paginated results for a completed search."""
        # Get search query
        result = await db.execute(
            select(SearchQuery).where(SearchQuery.id == search_query_id)
        )
        search_query = result.scalar_one_or_none()
        
        if not search_query:
            raise ValueError(f"Search query {search_query_id} not found")
        
        # Get listings for this search
        listings_query = (
            select(Listing)
            .join(ListingSource, Listing.id == ListingSource.listing_id)
            .join(ProviderRun, ListingSource.raw_payload_id == ProviderRun.raw_payload_id)
            .where(ProviderRun.search_query_id == search_query_id)
            .order_by(Listing.last_seen_at.desc())
        )
        
        # Get total count
        count_result = await db.execute(
            select(func.count(Listing.id))
            .select_from(listings_query.subquery())
        )
        total_count = count_result.scalar()
        
        # Get paginated listings
        result = await db.execute(
            listings_query.offset(pagination.offset).limit(pagination.limit)
        )
        listings = result.scalars().all()
        
        # Load sources for each listing
        for listing in listings:
            sources_result = await db.execute(
                select(ListingSource).where(ListingSource.listing_id == listing.id)
            )
            listing.sources = sources_result.scalars().all()
        
        # Create search summary
        search_summary = SearchSummary(
            search_query_id=search_query.id,
            status=search_query.status.value,
            total_providers=search_query.total_providers,
            completed_providers=search_query.completed_providers,
            total_listings=search_query.total_listings,
        )
        
        # Generate external search links
        criteria = SearchCriteria(**search_query.criteria_json)
        outlink_provider = provider_manager.get_provider("outlink")
        external_links = outlink_provider.generate_search_links(criteria)
        
        # Create paginated response
        paginated_response = PaginatedResponse.create(
            items=listings,
            total_count=total_count,
            params=pagination,
        )
        
        return SearchResponse(
            items=paginated_response.items,
            pagination=paginated_response.pagination,
            search_summary=search_summary,
            external_search_links=external_links,
        )
    
    async def _execute_provider_searches(
        self,
        search_query: SearchQuery,
        providers: List,
        criteria: SearchCriteria,
        db: AsyncSession,
    ) -> List[tuple[List[ProviderListing], str, UUID]]:
        """Execute searches across all providers concurrently."""
        tasks = []
        
        for provider in providers:
            task = self._execute_single_provider_search(
                search_query,
                provider,
                criteria,
                db,
            )
            tasks.append(task)
        
        # Wait for all provider searches to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and handle exceptions
        provider_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(
                    "Provider search failed",
                    provider=providers[i].name,
                    error=str(result),
                )
                continue
            
            provider_results.append(result)
        
        return provider_results
    
    async def _execute_single_provider_search(
        self,
        search_query: SearchQuery,
        provider,
        criteria: SearchCriteria,
        db: AsyncSession,
    ) -> tuple[List[ProviderListing], str, UUID]:
        """Execute search for a single provider."""
        provider_name = provider.name
        
        # Create provider run record
        provider_run = ProviderRun(
            search_query_id=search_query.id,
            provider_name=provider_name,
            status=ProviderRunStatus.RUNNING,
            request_json=criteria.model_dump(),
        )
        
        db.add(provider_run)
        await db.commit()
        await db.refresh(provider_run)
        
        start_time = datetime.now(timezone.utc)
        
        try:
            # Execute provider search with timeout
            listings = await asyncio.wait_for(
                provider.search(criteria),
                timeout=provider.get_timeout_seconds(),
            )
            
            end_time = datetime.now(timezone.utc)
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Store raw payload
            raw_payload = await self._store_raw_payload(
                provider_name,
                criteria.model_dump(),
                {"listings": [listing.model_dump() for listing in listings]},
                200,
                db,
            )
            
            # Update provider run
            provider_run.status = ProviderRunStatus.COMPLETED
            provider_run.finished_at = end_time
            provider_run.listings_found = len(listings)
            provider_run.duration_ms = duration_ms
            provider_run.raw_payload_id = raw_payload.id
            
            await db.commit()
            
            self.logger.info(
                "Provider search completed",
                provider=provider_name,
                listings_found=len(listings),
                duration_ms=duration_ms,
            )
            
            return listings, provider_name, raw_payload.id
            
        except asyncio.TimeoutError:
            end_time = datetime.now(timezone.utc)
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Update provider run with timeout
            provider_run.status = ProviderRunStatus.TIMEOUT
            provider_run.finished_at = end_time
            provider_run.duration_ms = duration_ms
            provider_run.error_text = f"Search timed out after {provider.get_timeout_seconds()} seconds"
            
            await db.commit()
            
            raise TimeoutException(
                f"provider_search_{provider_name}",
                provider.get_timeout_seconds(),
            )
            
        except Exception as e:
            end_time = datetime.now(timezone.utc)
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Update provider run with error
            provider_run.status = ProviderRunStatus.FAILED
            provider_run.finished_at = end_time
            provider_run.duration_ms = duration_ms
            provider_run.error_text = str(e)
            
            await db.commit()
            
            raise ProviderException(provider_name, f"Provider search failed: {str(e)}")
    
    async def _store_raw_payload(
        self,
        provider_name: str,
        request_data: dict,
        response_data: dict,
        http_status: int,
        db: AsyncSession,
    ) -> RawPayload:
        """Store raw provider response data."""
        import hashlib
        import json
        
        # Calculate response hash
        response_json = json.dumps(response_data, sort_keys=True)
        response_hash = hashlib.sha256(response_json.encode()).hexdigest()
        
        # Check for existing payload with same hash
        existing_result = await db.execute(
            select(RawPayload).where(
                and_(
                    RawPayload.provider_name == provider_name,
                    RawPayload.response_hash == response_hash,
                )
            )
        )
        existing_payload = existing_result.scalar_one_or_none()
        
        if existing_payload:
            return existing_payload
        
        # Create new raw payload
        raw_payload = RawPayload(
            provider_name=provider_name,
            request_json=request_data,
            response_json=response_data,
            http_status=http_status,
            response_hash=response_hash,
            response_size_bytes=len(response_json.encode()),
        )
        
        db.add(raw_payload)
        await db.commit()
        await db.refresh(raw_payload)
        
        return raw_payload
    
    async def _process_search_results(
        self,
        provider_results: List[tuple[List[ProviderListing], str, UUID]],
        search_query: SearchQuery,
        db: AsyncSession,
    ) -> tuple[List[Listing], List[ListingSource]]:
        """Process and deduplicate search results from all providers."""
        # Flatten all provider listings
        all_provider_listings = []
        
        for listings, provider_name, raw_payload_id in provider_results:
            for listing in listings:
                all_provider_listings.append((listing, provider_name, raw_payload_id))
        
        if not all_provider_listings:
            return [], []
        
        # Deduplicate listings
        canonical_listings, listing_sources_with_keys = self.deduplication_service.deduplicate_listings(
            all_provider_listings,
        )
        
        # Save to database
        await self._save_search_results(
            canonical_listings,
            listing_sources_with_keys,
            db,
        )
        
        return canonical_listings, [source for source, _ in listing_sources_with_keys]
    
    async def _save_search_results(
        self,
        canonical_listings: List[Listing],
        listing_sources_with_keys: List[tuple[ListingSource, str]],
        db: AsyncSession,
    ):
        """Save search results to database."""
        # Save canonical listings
        for listing in canonical_listings:
            db.add(listing)
        
        await db.flush()  # Get listing IDs
        
        # Create a mapping from canonical_key to listing_id
        key_to_listing_id = {listing.canonical_key: listing.id for listing in canonical_listings}
        
        # Save listing sources with proper listing_id
        for source, canonical_key in listing_sources_with_keys:
            if canonical_key in key_to_listing_id:
                source.listing_id = key_to_listing_id[canonical_key]
                db.add(source)
        
        await db.commit()
        
        self.logger.info(
            "Search results saved",
            listings=len(canonical_listings),
            sources=len(listing_sources_with_keys),
        )

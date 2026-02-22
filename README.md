# Addressable - Real Estate Search Engine

A modern real-estate search engine that aggregates listings from multiple data providers, normalizes data, and provides a unified API and UI for property search and analysis.

## Architecture Overview

Addressable is built with a microservices architecture that supports multiple data providers, concurrent searching, and real-time result aggregation:

- **Backend**: Python 3.12 + FastAPI (async), Pydantic v2, SQLAlchemy 2.x
- **Database**: Postgres 16 with JSONB for raw payload storage
- **Queue**: Redis + RQ for async processing
- **Frontend**: Next.js (TypeScript) with minimal UI
- **Web Scraping**: Patchwright for anti-bot evasion on major real estate sites

## Quick Start

1. **Clone and setup**:
   ```bash
   git clone <repository>
   cd addressable
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Start all services**:
   ```bash
   make up
   ```

3. **Run migrations**:
   ```bash
   make migrate
   ```

4. **Access the application**:
   - Frontend: http://localhost:3000
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Development

### Backend Development
```bash
# Install dependencies
cd backend
pip install -e .

# Run tests
make backend-test

# Lint and format
make backend-lint

# Run migrations
make migrate
make downgrade  # rollback last migration
```

### Adding New Providers

1. Create a new provider in `backend/app/providers/`:
   ```python
   from .base import Provider, ProviderListing
   
   class MyProvider(Provider):
       name = "myprovider"
       supports_search = True
       
       async def search(self, criteria: SearchCriteria) -> List[ProviderListing]:
           # Implement search logic
           pass
   ```

2. Register the provider in `backend/app/providers/__init__.py`

3. Add provider configuration to `.env`

### Testing

```bash
# Backend tests
make backend-test

# Frontend tests (optional)
cd frontend && npm test

# Integration tests
docker compose -f docker-compose.test.yml up --abort-on-container-exit
```

## API Endpoints

- `POST /api/search` - Submit search criteria
- `GET /api/search/{search_query_id}` - Get search results
- `GET /api/listings/{listing_id}` - Get listing details
- `GET /api/providers` - List enabled providers
- `GET /healthz` - Health check

## Data Model

### Core Entities
- **SearchQuery**: User search requests with criteria and status
- **ProviderRun**: Individual provider execution tracking
- **RawPayload**: Original provider responses stored as JSONB
- **Listing**: Canonical deduplicated property listings
- **ListingSource**: Mapping from canonical listings to provider sources

### Deduplication
Canonical listings are created using a deterministic key:
```
canonical_key = normalized_address + "|" + rounded_lat + "|" + rounded_lng
```

## Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/addressable

# Redis
REDIS_URL=redis://localhost:6379

# API
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=["http://localhost:3000"]

# Providers
ENABLED_PROVIDERS=mock,outlink,csv
PROVIDER_TIMEOUT_SECONDS=10

# Scraping
USE_HEADED_BROWSER=true
BROWSER_HEADLESS=false
```

## Provider Support

### Currently Implemented
- **MockProvider**: Returns sample data for testing
- **CSVImportProvider**: Imports from CSV files
- **OutlinkProvider**: Generates external search links

### Planned (Phase 2)
- **ZillowProvider**: Web scraping with Patchwright
- **RedfinProvider**: Web scraping with Patchwright  
- **RealtorProvider**: Web scraping with Patchwright

## Performance & Reliability

- Concurrent provider execution with configurable timeouts
- Rate limiting and request throttling
- Automatic retry with exponential backoff
- Payload size limits and validation
- Health checks and monitoring

## Security

- No secrets committed to repository
- CORS configured for local development
- Input validation on all endpoints
- JSONB payload size limits
- SQL injection prevention via SQLAlchemy

## Docker Services

- **postgres**: Postgres 16 database
- **redis**: Redis cache and queue
- **backend**: FastAPI application
- **worker**: RQ background job processor
- **frontend**: Next.js application

## Project Structure

```
/
├── README.md
├── docker-compose.yml
├── .env.example
├── Makefile
├── backend/
│   ├── pyproject.toml
│   └── app/
│       ├── main.py
│       ├── core/
│       ├── db/
│       ├── models/
│       ├── schemas/
│       ├── providers/
│       ├── services/
│       ├── api/
│       ├── workers/
│       └── tests/
└── frontend/
    ├── package.json
    └── app/
        ├── components/
        ├── lib/
        └── tests/
```

## License

MIT License - see LICENSE file for details.
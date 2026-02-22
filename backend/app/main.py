from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from app.core.settings import settings
from app.core.logging import setup_logging
from app.api.routers import search, listings, providers, health, locations
from app.db.engine import engine
from app.db.session import get_db
from app.models import Base

# Setup logging
setup_logging()
logger = structlog.get_logger()

# Create FastAPI app
app = FastAPI(
    title="Addressable API",
    description="Real estate search engine API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/healthz", tags=["health"])
app.include_router(search.router, prefix="/api", tags=["search"])
app.include_router(listings.router, prefix="/api", tags=["listings"])
app.include_router(providers.router, prefix="/api", tags=["providers"])
app.include_router(locations.router, prefix="/api", tags=["locations"])


@app.on_event("startup")
async def startup_event():
    logger.info("Starting Addressable API", version="0.1.0")
    
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Application startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Addressable API")
    
    # Close database connections
    await engine.dispose()
    
    logger.info("Application shutdown complete")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error("Unhandled exception", exc_info=exc, path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
    )

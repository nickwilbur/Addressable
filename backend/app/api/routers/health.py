from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from sqlalchemy import text
from app.db.session import get_db
from app.services.provider_manager import provider_manager

router = APIRouter()
logger = structlog.get_logger()


@router.get("/")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint."""
    try:
        # Check database connection
        await db.execute(text("SELECT 1"))
        db_healthy = True
        db_error = None
    except Exception as e:
        db_healthy = False
        db_error = str(e)
        logger.error("Database health check failed", error=str(e))
    
    # Check provider health
    try:
        provider_health = await provider_manager.health_check()
        providers_healthy = all(provider_health.values())
        provider_error = None if providers_healthy else "Some providers are unhealthy"
    except Exception as e:
        provider_health = {}
        providers_healthy = False
        provider_error = str(e)
        logger.error("Provider health check failed", error=str(e))
    
    # Overall health
    overall_healthy = db_healthy and providers_healthy
    
    health_data = {
        "status": "healthy" if overall_healthy else "unhealthy",
        "timestamp": "2025-01-01T00:00:00Z",  # Would use actual timestamp
        "checks": {
            "database": {
                "status": "healthy" if db_healthy else "unhealthy",
                "error": db_error,
            },
            "providers": {
                "status": "healthy" if providers_healthy else "unhealthy",
                "error": provider_error,
                "details": provider_health,
            },
        },
    }
    
    # Return appropriate status code
    status_code = 200 if overall_healthy else 503
    
    return health_data

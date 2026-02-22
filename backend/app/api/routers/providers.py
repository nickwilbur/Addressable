from fastapi import APIRouter, Depends
import structlog

from app.services.provider_manager import provider_manager
from app.schemas.provider import ProviderInfo

router = APIRouter()
logger = structlog.get_logger()


@router.get("/providers", response_model=list[ProviderInfo])
async def get_providers():
    """Get information about all available providers."""
    try:
        provider_info = provider_manager.get_provider_info()
        
        # Convert to response models
        providers = [
            ProviderInfo(
                name=info["name"],
                display_name=info["display_name"],
                description=info["description"],
                enabled=info["enabled"],
                capabilities=info["capabilities"],
            )
            for info in provider_info
        ]
        
        return providers
        
    except Exception as e:
        logger.error("Failed to get provider information", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/providers/health")
async def get_provider_health():
    """Get health status of all providers."""
    try:
        health_status = await provider_manager.health_check()
        return health_status
        
    except Exception as e:
        logger.error("Failed to get provider health", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

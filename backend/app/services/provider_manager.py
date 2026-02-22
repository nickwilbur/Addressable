from typing import List, Dict, Type
import structlog

from app.providers.base import Provider
from app.providers import PROVIDERS, REAL_ESTATE_PROVIDERS
from app.core.settings import settings
from app.core.errors import ProviderException

logger = structlog.get_logger()


class ProviderManager:
    """Manages provider instances and operations."""
    
    def __init__(self):
        self.logger = structlog.get_logger()
        self._providers: Dict[str, Provider] = {}
        self._enabled_providers: List[str] = []
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize enabled provider instances."""
        enabled_names = settings.enabled_providers_list
        
        for provider_name in enabled_names:
            if provider_name not in PROVIDERS:
                self.logger.warning("Unknown provider", provider=provider_name)
                continue
            
            try:
                provider_class = PROVIDERS[provider_name]
                provider_instance = provider_class()
                self._providers[provider_name] = provider_instance
                self._enabled_providers.append(provider_name)
                self.logger.info("Provider initialized", provider=provider_name)
                
            except Exception as e:
                self.logger.error("Failed to initialize provider", provider=provider_name, error=str(e))
                continue
        
        self.logger.info("Provider manager initialized", providers=len(self._enabled_providers))
    
    def get_provider(self, name: str) -> Provider:
        """Get a specific provider by name."""
        if name not in self._providers:
            raise ProviderException("system", f"Provider '{name}' not found or not enabled")
        return self._providers[name]
    
    def get_enabled_providers(self) -> List[str]:
        """Get list of enabled provider names."""
        return self._enabled_providers.copy()
    
    def get_search_providers(self, provider_names: List[str] = None) -> List[Provider]:
        """Get providers that support search.
        
        Args:
            provider_names: Optional list of specific provider names to use.
                           If None, returns all enabled search providers except mock.
        """
        if provider_names:
            # Return specific providers requested
            providers = []
            for name in provider_names:
                if name in self._providers and self._providers[name].supports_search:
                    providers.append(self._providers[name])
                else:
                    self.logger.warning("Requested provider not found or doesn't support search", provider=name)
            return providers
        else:
            # Return all enabled search providers except mock
            return [
                provider for name, provider in self._providers.items()
                if provider.supports_search and name != "mock"
            ]
    
    def get_real_estate_providers(self) -> List[str]:
        """Get list of real estate provider names."""
        return list(REAL_ESTATE_PROVIDERS.keys())
    
    def get_provider_info(self) -> List[Dict]:
        """Get information about all providers."""
        info = []
        
        for name, provider in self._providers.items():
            provider_info = {
                "name": provider.name,
                "display_name": name.title(),
                "description": f"{name.title()} data provider",
                "enabled": name in self._enabled_providers,
                "capabilities": {
                    "supports_search": provider.supports_search,
                    "supports_details": provider.supports_details,
                    "supports_images": provider.supports_images,
                    "rate_limit_per_minute": provider.get_rate_limit_per_minute(),
                    "timeout_seconds": provider.get_timeout_seconds(),
                },
            }
            info.append(provider_info)
        
        return info
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all providers."""
        results = {}
        
        for name, provider in self._providers.items():
            try:
                is_healthy = await provider.health_check()
                results[name] = is_healthy
                self.logger.info("Provider health check", provider=name, healthy=is_healthy)
                
            except Exception as e:
                results[name] = False
                self.logger.error("Provider health check failed", provider=name, error=str(e))
        
        return results


# Global provider manager instance
provider_manager = ProviderManager()

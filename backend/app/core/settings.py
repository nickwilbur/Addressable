from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # Database
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/addressable"
    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "addressable"
    database_user: str = "postgres"
    database_password: str = "password"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    redis_host: str = "localhost"
    redis_port: int = 6379
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    cors_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"]
    
    # Providers
    enabled_providers: str = "zillow,realtor,redfin,outlink"  # Exclude mock by default
    provider_timeout_seconds: int = 10
    provider_rate_limit_per_minute: int = 60
    
    # Scraping
    use_headed_browser: bool = True
    browser_headless: bool = False
    browser_slowmo: int = 100
    browser_timeout: int = 30000
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # Background Jobs
    redis_queue: str = "high"
    worker_concurrency: int = 4
    
    # Payload Limits
    max_payload_size_mb: int = 10
    max_response_size_mb: int = 5
    
    @property
    def enabled_providers_list(self) -> List[str]:
        """Get enabled providers as a list."""
        return [p.strip() for p in self.enabled_providers.split(",") if p.strip()]
    
    @property
    def max_payload_size_bytes(self) -> int:
        """Get max payload size in bytes."""
        return self.max_payload_size_mb * 1024 * 1024
    
    @property
    def max_response_size_bytes(self) -> int:
        """Get max response size in bytes."""
        return self.max_response_size_mb * 1024 * 1024


# Global settings instance
settings = Settings()

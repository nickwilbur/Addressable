from fastapi import HTTPException
from typing import Any, Dict, Optional


class AddressableException(Exception):
    """Base exception for Addressable application."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ProviderException(AddressableException):
    """Exception raised when provider operations fail."""
    
    def __init__(
        self,
        provider_name: str,
        message: str,
        status_code: int = 502,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.provider_name = provider_name
        super().__init__(message, status_code, details)


class ValidationException(AddressableException):
    """Exception raised for validation errors."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, 400, details)


class TimeoutException(AddressableException):
    """Exception raised when operations timeout."""
    
    def __init__(
        self,
        operation: str,
        timeout_seconds: int,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.operation = operation
        self.timeout_seconds = timeout_seconds
        message = f"Operation '{operation}' timed out after {timeout_seconds} seconds"
        super().__init__(message, 408, details)


class RateLimitException(AddressableException):
    """Exception raised when rate limits are exceeded."""
    
    def __init__(
        self,
        provider_name: str,
        retry_after_seconds: int,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.provider_name = provider_name
        self.retry_after_seconds = retry_after_seconds
        message = f"Rate limit exceeded for {provider_name}. Retry after {retry_after_seconds} seconds."
        super().__init__(message, 429, details)


class PayloadSizeException(AddressableException):
    """Exception raised when payload size exceeds limits."""
    
    def __init__(
        self,
        actual_size: int,
        max_size: int,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.actual_size = actual_size
        self.max_size = max_size
        message = f"Payload size {actual_size} bytes exceeds maximum {max_size} bytes"
        super().__init__(message, 413, details)


def http_exception_from_addressable(exc: AddressableException) -> HTTPException:
    """Convert AddressableException to HTTPException."""
    return HTTPException(
        status_code=exc.status_code,
        detail={
            "message": exc.message,
            "details": exc.details,
        },
    )

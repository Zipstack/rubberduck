from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import json
import hashlib
from fastapi import Request, Response
import httpx

class BaseProvider(ABC):
    """
    Abstract base class for LLM provider implementations.
    Each provider must implement methods to normalize requests and forward them to the actual LLM API.
    """
    
    def __init__(self, name: str, base_url: str):
        self.name = name
        self.base_url = base_url
    
    @abstractmethod
    def normalize_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize the incoming request data to a standard format.
        This ensures consistent cache key generation across different request formats.
        
        Args:
            request_data: Raw request data from the client
            
        Returns:
            Normalized request data with sorted keys
        """
        pass
    
    @abstractmethod
    async def forward_request(
        self, 
        request_data: Dict[str, Any], 
        headers: Dict[str, str],
        endpoint: str
    ) -> Dict[str, Any]:
        """
        Forward the request to the actual LLM provider API.
        
        Args:
            request_data: Normalized request data
            headers: HTTP headers including authorization
            endpoint: The specific API endpoint to call
            
        Returns:
            Response data from the LLM provider
        """
        pass
    
    def generate_cache_key(self, normalized_request: Dict[str, Any]) -> str:
        """
        Generate a cache key from normalized request data.
        
        Args:
            normalized_request: Request data that has been normalized
            
        Returns:
            SHA-256 hash of the request as cache key
        """
        # Sort the request data to ensure consistent hashing
        sorted_request = json.dumps(normalized_request, sort_keys=True)
        return hashlib.sha256(sorted_request.encode()).hexdigest()
    
    @abstractmethod
    def get_supported_endpoints(self) -> list[str]:
        """
        Get list of supported API endpoints for this provider.
        
        Returns:
            List of endpoint paths this provider supports
        """
        pass
    
    @abstractmethod
    def transform_error_response(self, error_response: Dict[str, Any], status_code: int) -> Dict[str, Any]:
        """
        Transform error responses to match the provider's expected format.
        
        Args:
            error_response: Generic error response
            status_code: HTTP status code
            
        Returns:
            Provider-specific error response format
        """
        pass
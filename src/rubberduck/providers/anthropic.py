from typing import Dict, Any, Optional
import httpx
from .base import BaseProvider

class AnthropicProvider(BaseProvider):
    """
    Anthropic API provider implementation.
    Handles Claude chat completions and other Anthropic endpoints.
    """
    
    def __init__(self):
        super().__init__(name="anthropic", base_url="https://api.anthropic.com/v1")
    
    def normalize_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize Anthropic request data for consistent caching.
        """
        normalized = {}
        
        # Core parameters that affect the response
        core_params = [
            "model", "messages", "max_tokens", "temperature", "top_p", "top_k",
            "stop_sequences", "stream", "system", "metadata", "tools", "tool_choice"
        ]
        
        # Only include parameters that are present in the request
        for param in core_params:
            if param in request_data:
                normalized[param] = request_data[param]
        
        # Special handling for messages to ensure consistent ordering
        if "messages" in normalized:
            messages = []
            for msg in normalized["messages"]:
                normalized_msg = {
                    "role": msg.get("role"),
                    "content": msg.get("content")
                }
                messages.append(normalized_msg)
            normalized["messages"] = messages
        
        return normalized
    
    async def forward_request(
        self, 
        request_data: Dict[str, Any], 
        headers: Dict[str, str],
        endpoint: str
    ) -> Dict[str, Any]:
        """
        Forward request to Anthropic API.
        """
        # Prepare headers for Anthropic API
        api_headers = {
            "Content-Type": "application/json",
            "User-Agent": "Rubberduck-Proxy/0.1.0",
            "anthropic-version": "2023-06-01"  # Required by Anthropic API
        }
        
        # Pass through authorization header
        if "authorization" in headers:
            api_headers["Authorization"] = headers["authorization"]
        elif "Authorization" in headers:
            api_headers["Authorization"] = headers["Authorization"]
        elif "x-api-key" in headers:
            api_headers["x-api-key"] = headers["x-api-key"]
        elif "X-API-Key" in headers:
            api_headers["X-API-Key"] = headers["X-API-Key"]
        
        # Construct full URL
        url = f"{self.base_url}{endpoint}"
        
        # Make request to Anthropic API
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url,
                    json=request_data,
                    headers=api_headers,
                    timeout=300.0  # 5 minute timeout
                )
                
                # Handle different response codes
                if response.status_code == 200:
                    return {
                        "status_code": response.status_code,
                        "data": response.json(),
                        "headers": dict(response.headers)
                    }
                else:
                    # Return error response in Anthropic format
                    error_data = response.json() if response.content else {"error": {"message": "Unknown error"}}
                    return {
                        "status_code": response.status_code,
                        "data": error_data,
                        "headers": dict(response.headers)
                    }
                    
            except httpx.TimeoutException:
                return self.transform_error_response(
                    {"error": {"message": "Request timeout", "type": "timeout"}}, 
                    408
                )
            except httpx.RequestError as e:
                return self.transform_error_response(
                    {"error": {"message": f"Request failed: {str(e)}", "type": "connection_error"}}, 
                    503
                )
    
    def get_supported_endpoints(self) -> list[str]:
        """
        Get list of supported Anthropic API endpoints.
        """
        return [
            "/messages",
            "/complete",
            "/models"
        ]
    
    def transform_error_response(self, error_response: Dict[str, Any], status_code: int) -> Dict[str, Any]:
        """
        Transform error responses to match Anthropic's expected format.
        """
        # Anthropic error format
        anthropic_error = {
            "status_code": status_code,
            "data": {
                "error": {
                    "type": error_response.get("error", {}).get("type", "api_error"),
                    "message": error_response.get("error", {}).get("message", "Unknown error")
                }
            },
            "headers": {
                "Content-Type": "application/json"
            }
        }
        
        return anthropic_error
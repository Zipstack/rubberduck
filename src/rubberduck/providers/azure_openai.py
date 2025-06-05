from typing import Dict, Any, Optional
import httpx
from .base import BaseProvider
import re

class AzureOpenAIProvider(BaseProvider):
    """
    Azure OpenAI API provider implementation.
    Handles Azure OpenAI endpoints with resource-specific URLs.
    """
    
    def __init__(self):
        super().__init__(name="azure_openai", base_url="https://{resource}.openai.azure.com")
    
    def normalize_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize Azure OpenAI request data for consistent caching.
        """
        normalized = {}
        
        # Core parameters that affect the response (similar to OpenAI)
        core_params = [
            "messages", "temperature", "max_tokens", "top_p", 
            "frequency_penalty", "presence_penalty", "stop", "stream",
            "tools", "tool_choice", "user", "response_format"
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
                if "name" in msg:
                    normalized_msg["name"] = msg["name"]
                if "tool_calls" in msg:
                    normalized_msg["tool_calls"] = msg["tool_calls"]
                if "tool_call_id" in msg:
                    normalized_msg["tool_call_id"] = msg["tool_call_id"]
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
        Forward request to Azure OpenAI API.
        """
        # Prepare headers for Azure OpenAI API
        api_headers = {
            "Content-Type": "application/json",
            "User-Agent": "Rubberduck-Proxy/0.1.0"
        }
        
        # Pass through authorization header (Azure uses api-key)
        if "api-key" in headers:
            api_headers["api-key"] = headers["api-key"]
        elif "Api-Key" in headers:
            api_headers["api-key"] = headers["Api-Key"]
        elif "authorization" in headers:
            api_headers["Authorization"] = headers["authorization"]
        elif "Authorization" in headers:
            api_headers["Authorization"] = headers["Authorization"]
        
        # Extract Azure resource name and deployment from request
        # Expected format: /openai/deployments/{deployment-id}/chat/completions?api-version={version}
        # or extract from headers or use default placeholder
        resource_name = headers.get("azure-resource", "your-resource")
        
        # Build Azure OpenAI URL
        if "{resource}" in self.base_url:
            base_url = self.base_url.format(resource=resource_name)
        else:
            base_url = self.base_url
            
        url = f"{base_url}{endpoint}"
        
        # Add api-version parameter if not present
        if "api-version=" not in url:
            separator = "&" if "?" in url else "?"
            url += f"{separator}api-version=2024-02-01"
        
        # Make request to Azure OpenAI API
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
                    # Return error response in Azure OpenAI format
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
        Get list of supported Azure OpenAI API endpoints.
        """
        return [
            "/openai/deployments/{deployment_id}/chat/completions",
            "/openai/deployments/{deployment_id}/completions",
            "/openai/deployments/{deployment_id}/embeddings",
            "/openai/deployments/{deployment_id}/images/generations",
            "/openai/deployments/{deployment_id}/audio/transcriptions",
            "/openai/deployments/{deployment_id}/audio/translations",
            "/openai/models"
        ]
    
    def transform_error_response(self, error_response: Dict[str, Any], status_code: int) -> Dict[str, Any]:
        """
        Transform error responses to match Azure OpenAI's expected format.
        """
        # Azure OpenAI error format (similar to OpenAI)
        azure_error = {
            "status_code": status_code,
            "data": {
                "error": {
                    "message": error_response.get("error", {}).get("message", "Unknown error"),
                    "type": error_response.get("error", {}).get("type", "api_error"),
                    "code": error_response.get("error", {}).get("code", None)
                }
            },
            "headers": {
                "Content-Type": "application/json"
            }
        }
        
        return azure_error
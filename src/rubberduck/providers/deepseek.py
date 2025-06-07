from typing import Dict, Any, Optional
import httpx
from .base import BaseProvider

class DeepSeekProvider(BaseProvider):
    """
    DeepSeek API provider implementation.
    Handles chat completions using OpenAI-compatible format.
    """
    
    def __init__(self):
        super().__init__(name="deepseek", base_url="https://api.deepseek.com")
    
    def normalize_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize DeepSeek request data for consistent caching.
        Uses similar normalization to OpenAI since DeepSeek is OpenAI-compatible.
        """
        normalized = {}
        
        # Core parameters that affect the response
        core_params = [
            "model", "messages", "temperature", "max_tokens", "top_p", 
            "frequency_penalty", "presence_penalty", "stop", "stream",
            "tools", "tool_choice", "user", "response_format"
        ]
        
        # Only include parameters that are present in the request
        for param in core_params:
            if param in request_data:
                normalized[param] = request_data[param]
        
        # Special handling for messages to ensure consistent ordering
        if "messages" in normalized:
            # Ensure messages maintain order but normalize any inconsistencies
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
        Forward request to DeepSeek API.
        """
        # Prepare headers for DeepSeek API
        api_headers = {
            "Content-Type": "application/json",
            "User-Agent": "Rubberduck-Proxy/0.1.0"
        }
        
        # Pass through authorization header (DeepSeek uses Bearer token)
        if "authorization" in headers:
            api_headers["Authorization"] = headers["authorization"]
        elif "Authorization" in headers:
            api_headers["Authorization"] = headers["Authorization"]
        
        # Normalize endpoint to ensure v1 prefix for compatibility
        normalized_endpoint = endpoint
        if not normalized_endpoint.startswith("/v1/") and not normalized_endpoint.startswith("/"):
            normalized_endpoint = f"/v1/{normalized_endpoint}"
        elif not normalized_endpoint.startswith("/v1/") and normalized_endpoint.startswith("/"):
            normalized_endpoint = f"/v1{normalized_endpoint}"
        
        # Construct full URL
        url = f"{self.base_url}{normalized_endpoint}"
        
        # Make request to DeepSeek API
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
                    # Return error response in OpenAI format (DeepSeek follows OpenAI format)
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
        Get list of supported DeepSeek API endpoints.
        DeepSeek is OpenAI-compatible, so it supports similar endpoints.
        """
        return [
            "/chat/completions",
            "/v1/chat/completions",
            "/models",
            "/v1/models"
        ]
    
    def transform_error_response(self, error_response: Dict[str, Any], status_code: int) -> Dict[str, Any]:
        """
        Transform error responses to match OpenAI's expected format.
        DeepSeek follows OpenAI error format, so this is consistent.
        """
        # OpenAI-compatible error format
        openai_error = {
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
        
        return openai_error
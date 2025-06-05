from typing import Dict, Any, Optional
import httpx
from .base import BaseProvider

class OpenAIProvider(BaseProvider):
    """
    OpenAI API provider implementation.
    Handles chat completions, embeddings, and other OpenAI endpoints.
    """
    
    def __init__(self):
        super().__init__(name="openai", base_url="https://api.openai.com/v1")
    
    def normalize_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize OpenAI request data for consistent caching.
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
        Forward request to OpenAI API.
        """
        # Prepare headers for OpenAI API
        api_headers = {
            "Content-Type": "application/json",
            "User-Agent": "Rubberduck-Proxy/0.1.0"
        }
        
        # Pass through authorization header
        if "authorization" in headers:
            api_headers["Authorization"] = headers["authorization"]
        elif "Authorization" in headers:
            api_headers["Authorization"] = headers["Authorization"]
        
        # Construct full URL - base_url already includes /v1
        if endpoint.startswith("/v1"):
            url = f"{self.base_url}{endpoint[3:]}"  # Remove /v1 prefix since base_url includes it
        else:
            url = f"{self.base_url}{endpoint}"
        
        # Make request to OpenAI API
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
                    # Return error response in OpenAI format
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
        Get list of supported OpenAI API endpoints.
        """
        return [
            "/v1/chat/completions",
            "/v1/completions", 
            "/v1/embeddings",
            "/v1/models",
            "/v1/images/generations",
            "/v1/images/edits",
            "/v1/images/variations",
            "/v1/audio/transcriptions",
            "/v1/audio/translations",
            "/v1/files",
            "/v1/fine_tuning/jobs",
            "/v1/moderations"
        ]
    
    def transform_error_response(self, error_response: Dict[str, Any], status_code: int) -> Dict[str, Any]:
        """
        Transform error responses to match OpenAI's expected format.
        """
        # OpenAI error format
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
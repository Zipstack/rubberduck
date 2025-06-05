from typing import Dict, Any, Optional
import httpx
import json
from .base import BaseProvider

class BedrockProvider(BaseProvider):
    """
    AWS Bedrock API provider implementation.
    Handles various model endpoints including Claude, Llama, and other models on Bedrock.
    """
    
    def __init__(self):
        super().__init__(name="bedrock", base_url="https://bedrock-runtime.{region}.amazonaws.com")
    
    def normalize_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize Bedrock request data for consistent caching.
        """
        normalized = {}
        
        # Core parameters that affect the response
        # Note: Bedrock uses different parameter names depending on the model
        core_params = [
            "prompt", "messages", "max_tokens", "max_tokens_to_sample", 
            "temperature", "top_p", "top_k", "stop_sequences", "stop",
            "anthropic_version", "model", "system"
        ]
        
        # Only include parameters that are present in the request
        for param in core_params:
            if param in request_data:
                normalized[param] = request_data[param]
        
        # Special handling for messages if present
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
        Forward request to AWS Bedrock API.
        """
        # Prepare headers for Bedrock API
        api_headers = {
            "Content-Type": "application/json",
            "User-Agent": "Rubberduck-Proxy/0.1.0",
            "Accept": "application/json"
        }
        
        # AWS authentication headers
        aws_headers = [
            "authorization", "Authorization",
            "x-amz-date", "X-Amz-Date", 
            "x-amz-security-token", "X-Amz-Security-Token",
            "x-amz-target", "X-Amz-Target"
        ]
        
        for header in aws_headers:
            if header in headers:
                api_headers[header] = headers[header]
        
        # Extract AWS region from headers or use default
        region = headers.get("aws-region", headers.get("AWS-Region", "us-east-1"))
        
        # Build Bedrock URL
        if "{region}" in self.base_url:
            base_url = self.base_url.format(region=region)
        else:
            base_url = self.base_url
            
        url = f"{base_url}{endpoint}"
        
        # Make request to AWS Bedrock API
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
                    # Return error response in Bedrock format
                    try:
                        error_data = response.json()
                    except:
                        error_data = {"message": response.text or "Unknown error"}
                    
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
        Get list of supported AWS Bedrock API endpoints.
        """
        return [
            "/model/{model_id}/invoke",
            "/model/{model_id}/invoke-with-response-stream",
            "/foundation-models",
            "/custom-models"
        ]
    
    def transform_error_response(self, error_response: Dict[str, Any], status_code: int) -> Dict[str, Any]:
        """
        Transform error responses to match AWS Bedrock's expected format.
        """
        # AWS Bedrock error format
        bedrock_error = {
            "status_code": status_code,
            "data": {
                "__type": error_response.get("error", {}).get("type", "ServiceException"),
                "message": error_response.get("error", {}).get("message", "Unknown error")
            },
            "headers": {
                "Content-Type": "application/x-amz-json-1.1"
            }
        }
        
        return bedrock_error
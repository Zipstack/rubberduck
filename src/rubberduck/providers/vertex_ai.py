from typing import Dict, Any, Optional
import httpx
from .base import BaseProvider

class VertexAIProvider(BaseProvider):
    """
    Google Vertex AI API provider implementation.
    Handles Vertex AI endpoints including PaLM, Gemini, and other Google models.
    """
    
    def __init__(self):
        super().__init__(name="vertex_ai", base_url="https://{location}-aiplatform.googleapis.com/v1")
    
    def normalize_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize Vertex AI request data for consistent caching.
        """
        normalized = {}
        
        # Core parameters that affect the response
        core_params = [
            "instances", "parameters", "contents", "generationConfig", 
            "safetySettings", "tools", "toolConfig", "systemInstruction"
        ]
        
        # Only include parameters that are present in the request
        for param in core_params:
            if param in request_data:
                normalized[param] = request_data[param]
        
        # Special handling for contents (Gemini format)
        if "contents" in normalized:
            contents = []
            for content in normalized["contents"]:
                normalized_content = {}
                if "role" in content:
                    normalized_content["role"] = content["role"]
                if "parts" in content:
                    normalized_content["parts"] = content["parts"]
                contents.append(normalized_content)
            normalized["contents"] = contents
        
        # Special handling for instances (PaLM format)
        if "instances" in normalized:
            instances = []
            for instance in normalized["instances"]:
                normalized_instance = {}
                for key, value in instance.items():
                    normalized_instance[key] = value
                instances.append(normalized_instance)
            normalized["instances"] = instances
        
        return normalized
    
    async def forward_request(
        self, 
        request_data: Dict[str, Any], 
        headers: Dict[str, str],
        endpoint: str
    ) -> Dict[str, Any]:
        """
        Forward request to Google Vertex AI API.
        """
        # Prepare headers for Vertex AI API
        api_headers = {
            "Content-Type": "application/json",
            "User-Agent": "Rubberduck-Proxy/0.1.0"
        }
        
        # Pass through authorization header (Google uses Bearer tokens)
        if "authorization" in headers:
            api_headers["Authorization"] = headers["authorization"]
        elif "Authorization" in headers:
            api_headers["Authorization"] = headers["Authorization"]
        
        # Extract Google Cloud project and location from headers or use defaults
        project_id = headers.get("google-cloud-project", headers.get("Google-Cloud-Project", "your-project"))
        location = headers.get("google-cloud-location", headers.get("Google-Cloud-Location", "us-central1"))
        
        # Build Vertex AI URL
        if "{location}" in self.base_url:
            base_url = self.base_url.format(location=location)
        else:
            base_url = self.base_url
        
        # Replace project placeholder in endpoint if present
        if "{project}" in endpoint:
            endpoint = endpoint.replace("{project}", project_id)
        if "{location}" in endpoint:
            endpoint = endpoint.replace("{location}", location)
            
        url = f"{base_url}{endpoint}"
        
        # Make request to Vertex AI API
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
                    # Return error response in Vertex AI format
                    try:
                        error_data = response.json()
                    except:
                        error_data = {"error": {"message": response.text or "Unknown error"}}
                    
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
        Get list of supported Vertex AI API endpoints.
        """
        return [
            "/projects/{project}/locations/{location}/publishers/google/models/{model}:predict",
            "/projects/{project}/locations/{location}/publishers/google/models/{model}:generateContent",
            "/projects/{project}/locations/{location}/publishers/google/models/{model}:streamGenerateContent",
            "/projects/{project}/locations/{location}/models",
            "/projects/{project}/locations/{location}/endpoints",
            "/projects/{project}/locations/{location}/publishers/anthropic/models/{model}:rawPredict",
            "/projects/{project}/locations/{location}/publishers/meta/models/{model}:predict"
        ]
    
    def transform_error_response(self, error_response: Dict[str, Any], status_code: int) -> Dict[str, Any]:
        """
        Transform error responses to match Vertex AI's expected format.
        """
        # Google Cloud error format
        vertex_error = {
            "status_code": status_code,
            "data": {
                "error": {
                    "code": status_code,
                    "message": error_response.get("error", {}).get("message", "Unknown error"),
                    "status": self._get_status_text(status_code)
                }
            },
            "headers": {
                "Content-Type": "application/json"
            }
        }
        
        return vertex_error
    
    def _get_status_text(self, status_code: int) -> str:
        """Get status text for Google Cloud error codes."""
        status_map = {
            400: "INVALID_ARGUMENT",
            401: "UNAUTHENTICATED", 
            403: "PERMISSION_DENIED",
            404: "NOT_FOUND",
            408: "DEADLINE_EXCEEDED",
            409: "ALREADY_EXISTS",
            429: "RESOURCE_EXHAUSTED",
            500: "INTERNAL",
            501: "NOT_IMPLEMENTED",
            503: "UNAVAILABLE"
        }
        return status_map.get(status_code, "UNKNOWN")
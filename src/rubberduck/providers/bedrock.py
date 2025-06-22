from typing import Dict, Any, Optional
import httpx
import json
import os
import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.credentials import Credentials
from .base import BaseProvider

class BedrockProvider(BaseProvider):
    """
    AWS Bedrock API provider implementation.
    
    Supports dual-mode authentication:
    1. Custom Headers Mode (Recommended): 
       - Client sends X-AWS-Access-Key/X-AWS-Secret-Key headers
       - Proxy re-signs requests with client credentials
       - Full caching, error injection, and logging support
    
    2. Endpoint Override Mode (Limited):
       - Client uses boto3 with endpoint_url='http://localhost:8009'
       - boto3 signs for proxy endpoint (causes signature mismatch with AWS)
       - Results in InvalidSignatureException from AWS
    
    Architecture Note:
    This is an API reverse proxy, not an HTTP CONNECT proxy. FastAPI does not
    support the HTTP CONNECT method required for traditional proxy tunneling.
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
            "anthropic_version", "model", "system", "inferenceConfig"
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
        
        # Special handling for inferenceConfig (Nova models)
        if "inferenceConfig" in normalized:
            inference_config = normalized["inferenceConfig"]
            normalized_config = {}
            # Normalize inference config parameters
            config_params = ["temperature", "maxTokens", "topP", "topK", "stopSequences"]
            for param in config_params:
                if param in inference_config:
                    normalized_config[param] = inference_config[param]
            normalized["inferenceConfig"] = normalized_config
        
        return normalized
    
    async def forward_request(
        self, 
        request_data: Dict[str, Any], 
        headers: Dict[str, str],
        endpoint: str
    ) -> Dict[str, Any]:
        """
        Forward request to AWS Bedrock API with re-signing.
        """
        # Debug: Log incoming headers
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Incoming headers: {headers}")
        
        # Extract AWS region from headers or use default
        region = headers.get("aws-region", headers.get("AWS-Region", "us-east-1"))
        
        # Build Bedrock URL
        if "{region}" in self.base_url:
            base_url = self.base_url.format(region=region)
        else:
            base_url = self.base_url
            
        url = f"{base_url}{endpoint}"
        
        # Dual-mode authentication detection:
        # Mode 1: Client sent pre-signed request (endpoint override)
        # Mode 2: Client sent unsigned request with custom headers (recommended)
        
        auth_header = headers.get("authorization") or headers.get("Authorization", "")
        
        # Mode 1: Client sent a signed request - forward it (limited functionality)
        if auth_header and auth_header.startswith("AWS4-HMAC-SHA256"):
            logger.info("Forwarding signed request from client")
            return await self._forward_signed_request(request_data, headers, endpoint, region, url)
        
        # Mode 2: Client sent unsigned request - re-sign with custom headers (recommended)
        logger.info("Handling unsigned request - will re-sign")
        
        # Try to get credentials from custom headers first
        client_access_key = headers.get("x-aws-access-key") or headers.get("X-AWS-Access-Key")
        client_secret_key = headers.get("x-aws-secret-key") or headers.get("X-AWS-Secret-Key")
        client_session_token = headers.get("x-aws-session-token") or headers.get("X-AWS-Session-Token")
        
        if client_access_key and client_secret_key:
            # Use client-provided credentials
            credentials = Credentials(
                access_key=client_access_key,
                secret_key=client_secret_key,
                token=client_session_token
            )
            logger.info("Using client-provided AWS credentials from custom headers")
        else:
            # Fall back to proxy's own credentials
            session = boto3.Session()
            credentials = session.get_credentials()
            
            if not credentials:
                return self.transform_error_response(
                    {"error": {"message": "No AWS credentials found. For unsigned requests, provide credentials via X-AWS-Access-Key/X-AWS-Secret-Key headers or configure proxy with AWS credentials.", "type": "authentication_error"}}, 
                    401
                )
            logger.info("Using proxy's AWS credentials")
        
        # Create request for signing
        request_body = json.dumps(request_data)
        
        # Prepare headers for Bedrock API
        api_headers = {
            "Content-Type": "application/json",
            "User-Agent": "Rubberduck-Proxy/0.1.0",
            "Accept": "application/json",
            "Host": f"bedrock-runtime.{region}.amazonaws.com"
        }
        
        # Create AWS request for signing
        aws_request = AWSRequest(
            method='POST',
            url=url,
            data=request_body,
            headers=api_headers
        )
        
        # Sign the request with proxy's AWS credentials
        signer = SigV4Auth(credentials, 'bedrock', region)
        signer.add_auth(aws_request)
        
        # Get the signed headers
        signed_headers = dict(aws_request.headers)
        
        # Make request to AWS Bedrock API
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url,
                    content=request_body,  # Use content instead of json since we already serialized
                    headers=signed_headers,
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
    
    async def _forward_signed_request(
        self,
        request_data: Dict[str, Any],
        headers: Dict[str, str],
        endpoint: str,
        region: str,
        url: str
    ) -> Dict[str, Any]:
        """
        Forward a signed request from the client directly to AWS Bedrock.
        The client has already signed the request properly for AWS.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"Forwarding to URL: {url}")
        logger.info(f"Request endpoint: {endpoint}")
        
        # Prepare headers for AWS Bedrock - use client's signed headers
        api_headers = {}
        
        # Copy all headers from client request except Host (which we'll set correctly)
        for key, value in headers.items():
            if key.lower() != "host":
                api_headers[key] = value
        
        # Set the correct Host header for AWS Bedrock endpoint
        api_headers["Host"] = f"bedrock-runtime.{region}.amazonaws.com"
        
        # Ensure proper content type
        api_headers["Content-Type"] = "application/json"
        
        # Prepare request body
        request_body = json.dumps(request_data)
        
        # Make request to AWS Bedrock API with client's signature
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url,
                    content=request_body,
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
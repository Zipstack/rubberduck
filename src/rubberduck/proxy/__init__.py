import socket
import threading
import uuid
import time
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import uvicorn

from ..database import get_db, SessionLocal
from ..models import Proxy
from ..providers import get_provider, list_providers
from ..cache import cache_manager
from ..failure import FailureConfig, failure_simulator
from ..logging import log_proxy_request


class ProxyManager:
    """
    Manages the lifecycle of proxy instances.
    Each proxy runs on its own port and forwards requests to LLM providers.
    """
    
    def __init__(self):
        self.active_proxies: Dict[int, dict] = {}  # proxy_id -> {"app": FastAPI, "thread": Thread, "port": int}
        self.port_assignments: Dict[int, int] = {}  # port -> proxy_id
        self._lock = threading.Lock()
    
    def find_available_port(self, preferred_port: Optional[int] = None, strict_port: bool = False, current_proxy_id: Optional[int] = None) -> int:
        """
        Find an available port for a new proxy.
        
        Args:
            preferred_port: Try this port first if provided
            strict_port: If True, only try the preferred port (for existing proxies)
            current_proxy_id: ID of the proxy being started (to exclude from port conflict check)
            
        Returns:
            Available port number
            
        Raises:
            RuntimeError: If no available port found, or if strict_port=True and preferred_port unavailable
        """
        # Check database for existing port assignments, excluding current proxy
        from ..database import SessionLocal
        from ..models import Proxy
        
        db = SessionLocal()
        try:
            query = db.query(Proxy).filter(Proxy.port.isnot(None))
            if current_proxy_id:
                query = query.filter(Proxy.id != current_proxy_id)
            existing_ports = {proxy.port for proxy in query.all()}
        finally:
            db.close()
        
        if strict_port and preferred_port:
            # For existing proxies, only try the assigned port
            if (self._is_port_available(preferred_port) and 
                preferred_port not in self.port_assignments and 
                preferred_port not in existing_ports):
                return preferred_port
            else:
                # Provide more detailed error message
                conflicts = []
                if not self._is_port_available(preferred_port):
                    conflicts.append("port is in use by another process")
                if preferred_port in self.port_assignments:
                    conflicts.append(f"port is assigned to active proxy {self.port_assignments[preferred_port]}")
                if preferred_port in existing_ports:
                    conflicts.append("port is assigned to another proxy in database")
                
                error_msg = f"Cannot start proxy on assigned port {preferred_port}: {', '.join(conflicts)}"
                raise RuntimeError(error_msg)
        
        ports_to_try = []
        
        if preferred_port:
            ports_to_try.append(preferred_port)
        
        # Try ports in range 8001-9000 (only for new proxies)
        ports_to_try.extend(range(8001, 9001))
        
        for port in ports_to_try:
            if (self._is_port_available(port) and 
                port not in self.port_assignments and 
                port not in existing_ports):
                return port
        
        raise RuntimeError("No available ports found")
    
    def _is_port_available(self, port: int) -> bool:
        """Check if a port is available."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(('127.0.0.1', port))
                return True
        except OSError:
            return False
    
    def create_proxy_app(self, proxy_id: int, provider_name: str) -> FastAPI:
        """
        Create a FastAPI app for a specific proxy instance.
        
        Args:
            proxy_id: Database ID of the proxy
            provider_name: Name of the LLM provider
            
        Returns:
            FastAPI application configured for this proxy
        """
        app = FastAPI(title=f"Rubberduck Proxy {proxy_id}", version="0.1.0")
        
        # Get the provider instance
        try:
            provider = get_provider(provider_name)
        except KeyError:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        # Get failure configuration from database
        db = SessionLocal()
        try:
            proxy_record = db.query(Proxy).filter(Proxy.id == proxy_id).first()
            failure_config = FailureConfig.from_json(proxy_record.failure_config if proxy_record else None)
        finally:
            db.close()
        
        # Create dynamic endpoints for all supported provider endpoints
        for endpoint in provider.get_supported_endpoints():
            self._create_proxy_endpoint(app, endpoint, provider, proxy_id, failure_config)
        
        return app
    
    def _create_proxy_endpoint(self, app: FastAPI, endpoint: str, provider, proxy_id: int, failure_config: FailureConfig):
        """
        Create a proxy endpoint that forwards requests to the LLM provider.
        """
        @app.post(endpoint)
        @app.get(endpoint)
        @app.put(endpoint)
        @app.delete(endpoint)
        @app.patch(endpoint)
        async def proxy_endpoint(request: Request):
            start_time = time.time()
            cache_hit = False
            failure_type = None
            request_data = None
            response = None
            
            try:
                # Apply failure simulation first
                failure_error = await failure_simulator.process_request(
                    config=failure_config,
                    proxy_id=proxy_id,
                    request=request
                )
                
                if failure_error:
                    # Determine failure type
                    if failure_error.status_code == 403 and "blocked" in failure_error.detail.lower():
                        failure_type = "ip_blocked"
                    elif failure_error.status_code == 429 and "rate limit" in failure_error.detail.lower():
                        failure_type = "rate_limited"
                    elif "timeout" in failure_error.detail.lower():
                        failure_type = "timeout"
                    else:
                        failure_type = "error_injection"
                    
                    # Create failure response
                    response = JSONResponse(
                        content={"error": {"message": failure_error.detail, "type": "simulated_failure"}},
                        status_code=failure_error.status_code
                    )
                    
                    # Log the failure
                    await log_proxy_request(
                        proxy_id=proxy_id,
                        request=request,
                        response=response,
                        start_time=start_time,
                        cache_hit=False,
                        failure_type=failure_type,
                        request_data=request_data
                    )
                    
                    return response
                
                # Get request data
                if request.method in ["POST", "PUT", "PATCH"]:
                    request_data = await request.json()
                else:
                    request_data = {}
                
                # Get headers and pass through authorization
                headers = dict(request.headers)
                
                # Check cache first (only for cacheable methods and endpoints)
                cached_response = None
                cache_key = None
                normalized_request = None
                
                if request.method in ["POST", "GET"] and request_data:
                    # Normalize request for cache key generation
                    normalized_request = provider.normalize_request(request_data)
                    cache_key = cache_manager.generate_cache_key(proxy_id, normalized_request)
                    cached_response = cache_manager.get_cached_response(proxy_id, cache_key)
                
                if cached_response:
                    # Create cache hit response
                    cache_hit = True
                    
                    # Filter out problematic headers from cached response too
                    cached_headers = cached_response.get("headers", {})
                    headers_to_filter = {
                        'content-encoding', 'content-length', 'transfer-encoding',
                        'connection', 'server', 'date', 'set-cookie', 'vary',
                        'cache-control', 'etag', 'last-modified', 'expires',
                        'alt-svc', 'cf-ray', 'cf-cache-status', 'x-cache',
                        'strict-transport-security', 'x-content-type-options',
                        'x-envoy-upstream-service-time'
                    }
                    
                    clean_headers = {}
                    for key, value in cached_headers.items():
                        if key.lower() not in headers_to_filter:
                            clean_headers[key] = value
                    
                    # Add cache-specific headers
                    clean_headers["X-Cache"] = "HIT"
                    clean_headers["X-Cache-Timestamp"] = cached_response.get("cache_timestamp", "")
                    
                    response = JSONResponse(
                        content=cached_response.get("data", {}),
                        status_code=cached_response.get("status_code", 200),
                        headers=clean_headers
                    )
                    
                    # Log the cache hit
                    await log_proxy_request(
                        proxy_id=proxy_id,
                        request=request,
                        response=response,
                        start_time=start_time,
                        cache_hit=cache_hit,
                        failure_type=None,
                        request_data=request_data
                    )
                    
                    return response
                
                # Extract path parameters and construct actual endpoint
                path_params = dict(request.path_params)
                actual_endpoint = endpoint
                for param_name, param_value in path_params.items():
                    actual_endpoint = actual_endpoint.replace(f"{{{param_name}}}", param_value)
                
                # Forward request to provider
                response_data = await provider.forward_request(
                    request_data=request_data,
                    headers=headers,
                    endpoint=actual_endpoint
                )
                
                # Cache successful responses
                if (cache_key and normalized_request and 
                    200 <= response_data.get("status_code", 500) < 300):
                    cache_manager.store_response(
                        proxy_id=proxy_id,
                        cache_key=cache_key,
                        normalized_request=normalized_request,
                        response_data=response_data.get("data", {}),
                        response_headers=response_data.get("headers", {}),
                        status_code=response_data.get("status_code", 500)
                    )
                
                # Return response with appropriate status code
                upstream_headers = response_data.get("headers", {})
                
                # Filter out headers that should not be forwarded from upstream
                # These headers are either handled by FastAPI or cause conflicts
                headers_to_filter = {
                    'content-encoding', 'content-length', 'transfer-encoding',
                    'connection', 'server', 'date', 'set-cookie', 'vary',
                    'cache-control', 'etag', 'last-modified', 'expires',
                    'alt-svc', 'cf-ray', 'cf-cache-status', 'x-cache',
                    'strict-transport-security', 'x-content-type-options',
                    'x-envoy-upstream-service-time'
                }
                
                # Build clean response headers
                response_headers = {}
                for key, value in upstream_headers.items():
                    if key.lower() not in headers_to_filter:
                        response_headers[key] = value
                
                # Add our own cache status
                if cache_key:
                    response_headers["X-Cache"] = "MISS"
                
                response = JSONResponse(
                    content=response_data.get("data", {}),
                    status_code=response_data.get("status_code", 200),
                    headers=response_headers
                )
                
                # Log the successful request (cache miss or non-cacheable)
                await log_proxy_request(
                    proxy_id=proxy_id,
                    request=request,
                    response=response,
                    start_time=start_time,
                    cache_hit=False,
                    failure_type=None,
                    request_data=request_data
                )
                
                return response
                
            except Exception as e:
                # Transform error using provider's error format
                error_response = provider.transform_error_response(
                    {"error": {"message": str(e), "type": "proxy_error"}},
                    500
                )
                
                response = JSONResponse(
                    content=error_response["data"],
                    status_code=error_response["status_code"]
                )
                
                # Log the error
                await log_proxy_request(
                    proxy_id=proxy_id,
                    request=request,
                    response=response,
                    start_time=start_time,
                    cache_hit=False,
                    failure_type="proxy_error",
                    request_data=request_data
                )
                
                return response
    
    def start_proxy(self, proxy_id: int, provider_name: str, port: Optional[int] = None) -> int:
        """
        Start a proxy instance.
        
        Args:
            proxy_id: Database ID of the proxy
            provider_name: Name of the LLM provider
            port: Preferred port (will find available if not provided)
            
        Returns:
            Port number the proxy is running on
            
        Raises:
            RuntimeError: If proxy is already running or port conflicts
        """
        with self._lock:
            if proxy_id in self.active_proxies:
                raise RuntimeError(f"Proxy {proxy_id} is already running")
            
            # Find available port
            # If port is provided (existing proxy), use strict checking
            # If port is None (new proxy), allow flexible port assignment
            strict_mode = port is not None
            assigned_port = self.find_available_port(port, strict_port=strict_mode, current_proxy_id=proxy_id)
            
            if assigned_port in self.port_assignments:
                raise RuntimeError(f"Port {assigned_port} is already in use")
            
            # Create the FastAPI app for this proxy
            app = self.create_proxy_app(proxy_id, provider_name)
            
            # Create server config for proper shutdown control
            config = uvicorn.Config(app, host="127.0.0.1", port=assigned_port, log_level="warning")
            server = uvicorn.Server(config)
            
            # Create shutdown event for clean termination
            shutdown_event = threading.Event()
            
            # Start the proxy in a separate thread
            def run_proxy():
                import asyncio
                asyncio.run(server.serve())
            
            proxy_thread = threading.Thread(target=run_proxy, daemon=False)
            proxy_thread.start()
            
            # Store proxy info including server instance for shutdown
            self.active_proxies[proxy_id] = {
                "app": app,
                "thread": proxy_thread,
                "server": server,
                "shutdown_event": shutdown_event,
                "port": assigned_port,
                "provider": provider_name
            }
            self.port_assignments[assigned_port] = proxy_id
            
            return assigned_port
    
    def stop_proxy(self, proxy_id: int):
        """
        Stop a proxy instance.
        
        Args:
            proxy_id: Database ID of the proxy
        """
        with self._lock:
            if proxy_id not in self.active_proxies:
                raise RuntimeError(f"Proxy {proxy_id} is not running")
            
            proxy_info = self.active_proxies[proxy_id]
            port = proxy_info["port"]
            server = proxy_info["server"]
            thread = proxy_info["thread"]
            
            # Trigger server shutdown
            server.should_exit = True
            
            # Remove from tracking
            del self.active_proxies[proxy_id]
            del self.port_assignments[port]
            
            # Wait for thread to finish (with timeout)
            thread.join(timeout=5.0)
            
            if thread.is_alive():
                logger.warning(f"Proxy {proxy_id} thread did not shut down cleanly within timeout")
    
    def get_proxy_status(self, proxy_id: int) -> dict:
        """
        Get status information for a proxy.
        
        Args:
            proxy_id: Database ID of the proxy
            
        Returns:
            Status information dictionary
        """
        if proxy_id in self.active_proxies:
            proxy_info = self.active_proxies[proxy_id]
            return {
                "status": "running",
                "port": proxy_info["port"],
                "provider": proxy_info["provider"],
                "url": f"http://127.0.0.1:{proxy_info['port']}"
            }
        else:
            return {"status": "stopped"}
    
    def list_active_proxies(self) -> list[dict]:
        """
        List all active proxy instances.
        
        Returns:
            List of proxy status dictionaries
        """
        return [
            {
                "proxy_id": proxy_id,
                **self.get_proxy_status(proxy_id)
            }
            for proxy_id in self.active_proxies.keys()
        ]


# Global proxy manager instance
proxy_manager = ProxyManager()


def update_proxy_port_in_db(proxy_id: int, port: int):
    """
    Update the port assignment in the database.
    
    Args:
        proxy_id: Database ID of the proxy
        port: Port number assigned to the proxy
    """
    db = SessionLocal()
    try:
        proxy = db.query(Proxy).filter(Proxy.id == proxy_id).first()
        if proxy:
            proxy.port = port
            db.commit()
    finally:
        db.close()


def start_proxy_for_id(proxy_id: int) -> dict:
    """
    Start a proxy instance for a given proxy ID.
    
    Args:
        proxy_id: Database ID of the proxy
        
    Returns:
        Status information for the started proxy
        
    Raises:
        HTTPException: If proxy not found or start fails
    """
    import logging
    logger = logging.getLogger(__name__)
    
    db = SessionLocal()
    try:
        proxy = db.query(Proxy).filter(Proxy.id == proxy_id).first()
        if not proxy:
            raise HTTPException(status_code=404, detail="Proxy not found")
        
        logger.info(f"Starting proxy {proxy_id} ({proxy.name}) on port {proxy.port or 'auto-assign'}")
        
        # Start the proxy (try to use existing port if available)
        try:
            port = proxy_manager.start_proxy(
                proxy_id=proxy.id,
                provider_name=proxy.provider,
                port=proxy.port  # Try to reuse the previously assigned port
            )
            
            # Update database with assigned port (should be same as existing port for restarts)
            proxy.port = port
            proxy.status = "running"
            db.commit()
            
            logger.info(f"Successfully started proxy {proxy_id} on port {port}")
            return proxy_manager.get_proxy_status(proxy_id)
            
        except RuntimeError as e:
            # Port conflict or other proxy start error
            error_msg = str(e)
            logger.error(f"Failed to start proxy {proxy_id}: {error_msg}")
            
            # Don't change the proxy status if it fails to start
            raise HTTPException(status_code=409, detail=error_msg)
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error starting proxy {proxy_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        db.close()


def stop_proxy_for_id(proxy_id: int) -> dict:
    """
    Stop a proxy instance for a given proxy ID.
    
    Args:
        proxy_id: Database ID of the proxy
        
    Returns:
        Status information for the stopped proxy
    """
    db = SessionLocal()
    try:
        proxy = db.query(Proxy).filter(Proxy.id == proxy_id).first()
        if not proxy:
            raise HTTPException(status_code=404, detail="Proxy not found")
        
        # Stop the proxy
        proxy_manager.stop_proxy(proxy_id)
        
        # Update database
        proxy.status = "stopped"
        db.commit()
        
        return proxy_manager.get_proxy_status(proxy_id)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
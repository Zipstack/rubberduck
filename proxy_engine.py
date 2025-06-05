import socket
import threading
import uuid
import time
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import uvicorn

from database import get_db, SessionLocal
from models import Proxy
from providers import get_provider, list_providers
from cache_system import cache_manager
from failure_simulation import FailureConfig, failure_simulator
from logging_middleware import log_proxy_request


class ProxyManager:
    """
    Manages the lifecycle of proxy instances.
    Each proxy runs on its own port and forwards requests to LLM providers.
    """
    
    def __init__(self):
        self.active_proxies: Dict[int, dict] = {}  # proxy_id -> {"app": FastAPI, "thread": Thread, "port": int}
        self.port_assignments: Dict[int, int] = {}  # port -> proxy_id
        self._lock = threading.Lock()
    
    def find_available_port(self, preferred_port: Optional[int] = None) -> int:
        """
        Find an available port for a new proxy.
        
        Args:
            preferred_port: Try this port first if provided
            
        Returns:
            Available port number
            
        Raises:
            RuntimeError: If no available port found
        """
        # Check database for existing port assignments
        from database import SessionLocal
        from models import Proxy
        
        db = SessionLocal()
        try:
            existing_ports = {proxy.port for proxy in db.query(Proxy).filter(Proxy.port.isnot(None)).all()}
        finally:
            db.close()
        
        ports_to_try = []
        
        if preferred_port:
            ports_to_try.append(preferred_port)
        
        # Try ports in range 8001-9000
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
                    response = JSONResponse(
                        content=cached_response.get("data", {}),
                        status_code=cached_response.get("status_code", 200),
                        headers={
                            **cached_response.get("headers", {}),
                            "X-Cache": "HIT",
                            "X-Cache-Timestamp": cached_response.get("cache_timestamp", "")
                        }
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
                
                # Forward request to provider
                response_data = await provider.forward_request(
                    request_data=request_data,
                    headers=headers,
                    endpoint=endpoint
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
                response_headers = response_data.get("headers", {})
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
            assigned_port = self.find_available_port(port)
            
            if assigned_port in self.port_assignments:
                raise RuntimeError(f"Port {assigned_port} is already in use")
            
            # Create the FastAPI app for this proxy
            app = self.create_proxy_app(proxy_id, provider_name)
            
            # Start the proxy in a separate thread
            def run_proxy():
                uvicorn.run(app, host="127.0.0.1", port=assigned_port, log_level="warning")
            
            proxy_thread = threading.Thread(target=run_proxy, daemon=True)
            proxy_thread.start()
            
            # Store proxy info
            self.active_proxies[proxy_id] = {
                "app": app,
                "thread": proxy_thread,
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
            
            # Remove from tracking
            del self.active_proxies[proxy_id]
            del self.port_assignments[port]
            
            # Note: uvicorn doesn't have a clean shutdown mechanism when run in thread
            # In production, we'd use a more sophisticated process management approach
    
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
    db = SessionLocal()
    try:
        proxy = db.query(Proxy).filter(Proxy.id == proxy_id).first()
        if not proxy:
            raise HTTPException(status_code=404, detail="Proxy not found")
        
        # Start the proxy (don't pass the existing port to avoid conflicts)
        port = proxy_manager.start_proxy(
            proxy_id=proxy.id,
            provider_name=proxy.provider,
            port=None  # Let the manager find an available port
        )
        
        # Update database with assigned port
        proxy.port = port
        proxy.status = "running"
        db.commit()
        
        return proxy_manager.get_proxy_status(proxy_id)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
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
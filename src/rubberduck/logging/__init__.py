import time
import hashlib
import json
from typing import Optional
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime

from ..database import SessionLocal
from ..models import LogEntry


class LoggingMiddleware:
    """Middleware to capture request metadata for audit logging."""
    
    def __init__(self):
        pass
    
    async def log_request(
        self,
        proxy_id: int,
        request: Request,
        response: Response,
        start_time: float,
        cache_hit: bool = False,
        failure_type: Optional[str] = None
    ):
        """
        Log request metadata to the database.
        
        Args:
            proxy_id: ID of the proxy handling the request
            request: FastAPI request object
            response: FastAPI response object
            start_time: Time when request processing started
            cache_hit: Whether this was a cache hit
            failure_type: Type of simulated failure (if any)
        """
        # Calculate latency
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        
        # Get client IP
        client_ip = request.client.host if request.client else "127.0.0.1"
        
        # Get request body for hash generation
        prompt_hash = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                # We need to get the request body, but it might already be consumed
                # This is a limitation - in real implementation we'd capture it earlier
                body = await request.body() if hasattr(request, '_body') else b""
                if body:
                    prompt_hash = hashlib.sha256(body).hexdigest()[:16]  # Short hash for privacy
            except Exception:
                prompt_hash = None
        
        # Extract status code
        status_code = getattr(response, 'status_code', 200)
        
        # Create log entry
        db = SessionLocal()
        try:
            log_entry = LogEntry(
                proxy_id=proxy_id,
                ip_address=client_ip,
                status_code=status_code,
                latency=latency_ms,
                cache_hit=cache_hit,
                prompt_hash=prompt_hash,
                failure_type=failure_type,
                timestamp=datetime.utcnow()
            )
            
            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)
            
            # Send WebSocket notification for real-time log updates
            try:
                # Import here to avoid circular imports
                from ..main import manager
                
                # Get the user who owns this proxy to send targeted notification
                from ..models import Proxy, User
                proxy = db.query(Proxy).filter(Proxy.id == proxy_id).first()
                if proxy:
                    user = db.query(User).filter(User.id == proxy.user_id).first()
                    if user:
                        # Use a simplified user ID for WebSocket (in production, use proper JWT decoding)
                        user_id = str(user.id)[:8]  # Use first 8 chars of user ID
                        
                        # Send log event asynchronously (fire and forget)
                        import asyncio
                        try:
                            # Try to get the running event loop
                            loop = asyncio.get_running_loop()
                            # Schedule the coroutine
                            loop.create_task(manager.send_log_event(log_entry, user_id))
                        except RuntimeError:
                            # No running event loop, skip WebSocket notification
                            pass
            except Exception as e:
                # Don't fail the request if WebSocket notification fails
                print(f"Warning: Failed to send WebSocket log notification: {e}")
            
        except Exception as e:
            db.rollback()
            print(f"Error logging request: {e}")
        finally:
            db.close()
    
    def generate_prompt_hash(self, request_data: dict) -> str:
        """
        Generate a hash of the request data for privacy-preserving logging.
        
        Args:
            request_data: Normalized request data
            
        Returns:
            Short hash string
        """
        if not request_data:
            return ""
        
        # Convert to JSON and hash
        json_str = json.dumps(request_data, sort_keys=True)
        hash_obj = hashlib.sha256(json_str.encode())
        return hash_obj.hexdigest()[:16]  # First 16 characters for brevity


# Global logging middleware instance
logging_middleware = LoggingMiddleware()


async def log_proxy_request(
    proxy_id: int,
    request: Request,
    response: Response,
    start_time: float,
    cache_hit: bool = False,
    failure_type: Optional[str] = None,
    request_data: Optional[dict] = None
):
    """
    Convenience function to log proxy requests.
    
    Args:
        proxy_id: ID of the proxy handling the request
        request: FastAPI request object
        response: FastAPI response object
        start_time: Time when request processing started
        cache_hit: Whether this was a cache hit
        failure_type: Type of simulated failure (if any)
        request_data: Request data for hash generation
    """
    # Calculate latency
    end_time = time.time()
    latency_ms = (end_time - start_time) * 1000
    
    # Get client IP
    client_ip = request.client.host if request.client else "127.0.0.1"
    
    # Generate prompt hash
    prompt_hash = None
    if request_data:
        prompt_hash = logging_middleware.generate_prompt_hash(request_data)
    
    # Extract status code
    status_code = getattr(response, 'status_code', 200)
    if isinstance(response, JSONResponse):
        status_code = response.status_code
    
    # Create log entry
    db = SessionLocal()
    try:
        log_entry = LogEntry(
            proxy_id=proxy_id,
            ip_address=client_ip,
            status_code=status_code,
            latency=latency_ms,
            cache_hit=cache_hit,
            prompt_hash=prompt_hash,
            failure_type=failure_type,
            timestamp=datetime.utcnow()
        )
        
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        
        # Send WebSocket notification for real-time log updates
        try:
            # Import here to avoid circular imports
            from ..main import manager
            
            # Get the user who owns this proxy to send targeted notification
            from ..models import Proxy, User
            proxy = db.query(Proxy).filter(Proxy.id == proxy_id).first()
            if proxy:
                user = db.query(User).filter(User.id == proxy.user_id).first()
                if user:
                    # Use a simplified user ID for WebSocket (in production, use proper JWT decoding)
                    user_id = str(user.id)[:8]  # Use first 8 chars of user ID
                    
                    # Send log event asynchronously (fire and forget)
                    import asyncio
                    try:
                        # Try to get the running event loop
                        loop = asyncio.get_running_loop()
                        # Schedule the coroutine
                        loop.create_task(manager.send_log_event(log_entry, user_id))
                    except RuntimeError:
                        # No running event loop, skip WebSocket notification
                        pass
        except Exception as e:
            # Don't fail the request if WebSocket notification fails
            print(f"Warning: Failed to send WebSocket log notification: {e}")
        
    except Exception as e:
        db.rollback()
        print(f"Error logging request: {e}")
    finally:
        db.close()
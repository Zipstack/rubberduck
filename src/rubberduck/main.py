import csv
import io
import json
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Set
from fastapi import FastAPI, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from .auth import auth_backend, fastapi_users, current_active_user
from .models import User, Proxy, LogEntry
from .models.schemas import UserRead, UserCreate
from .database import get_db
from .proxy import start_proxy_for_id, stop_proxy_for_id, proxy_manager
from .providers import list_providers
from .cache import cache_manager
from .failure import FailureConfig, create_default_failure_config
from .database import SessionLocal
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
import logging

app = FastAPI(title="Rubberduck", version="0.1.0")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        
    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                
    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            message_str = json.dumps(message)
            # Send to all connections for this user
            disconnected = set()
            for connection in self.active_connections[user_id].copy():
                try:
                    await connection.send_text(message_str)
                except:
                    disconnected.add(connection)
            
            # Clean up disconnected connections
            for connection in disconnected:
                self.active_connections[user_id].discard(connection)
    
    async def broadcast_to_all_users(self, message: dict):
        """Broadcast a message to all connected users"""
        for user_id in list(self.active_connections.keys()):
            await self.send_personal_message(message, user_id)
    
    async def send_log_event(self, log_entry: LogEntry, user_id: str):
        """Send a new log entry event to a specific user"""
        # Get proxy info for the log
        db = SessionLocal()
        try:
            proxy = db.query(Proxy).filter(Proxy.id == log_entry.proxy_id).first()
            proxy_name = proxy.name if proxy else f"Proxy {log_entry.proxy_id}"
            
            # Determine event type and status
            if log_entry.failure_type:
                event = f"Failure: {log_entry.failure_type}"
                status = "error"
            elif log_entry.cache_hit:
                event = "Cache hit"
                status = "success"
            elif log_entry.status_code >= 400:
                event = f"Error {log_entry.status_code}"
                status = "error"
            elif log_entry.status_code >= 200:
                event = "Request completed"
                status = "success"
            else:
                event = "Request processed"
                status = "info"
            
            # Calculate time ago
            time_diff = datetime.utcnow() - log_entry.timestamp
            if time_diff.total_seconds() < 60:
                time_ago = "Just now"
            elif time_diff.total_seconds() < 3600:
                minutes = int(time_diff.total_seconds() / 60)
                time_ago = f"{minutes} min ago"
            elif time_diff.total_seconds() < 86400:
                hours = int(time_diff.total_seconds() / 3600)
                time_ago = f"{hours} hour{'s' if hours != 1 else ''} ago"
            else:
                days = int(time_diff.total_seconds() / 86400)
                time_ago = f"{days} day{'s' if days != 1 else ''} ago"
            
            await self.send_personal_message({
                "type": "new_log_entry",
                "data": {
                    "id": log_entry.id,
                    "timestamp": log_entry.timestamp.isoformat() if log_entry.timestamp else None,
                    "proxy_id": log_entry.proxy_id,
                    "proxy_name": proxy_name,
                    "ip_address": log_entry.ip_address,
                    "status_code": log_entry.status_code,
                    "latency": round(log_entry.latency, 2) if log_entry.latency is not None else None,
                    "cache_hit": log_entry.cache_hit,
                    "prompt_hash": log_entry.prompt_hash,
                    "failure_type": log_entry.failure_type,
                    "token_usage": log_entry.token_usage,
                    "cost": log_entry.cost,
                    # Formatted data for dashboard
                    "time": time_ago,
                    "event": event,
                    "proxy": proxy_name,
                    "status": status,
                    "details": {
                        "status_code": log_entry.status_code,
                        "latency": round(log_entry.latency, 2) if log_entry.latency is not None else None,
                        "cache_hit": log_entry.cache_hit
                    }
                }
            }, user_id)
        finally:
            db.close()
    
    async def send_dashboard_update(self, user_id: str):
        """Send updated dashboard metrics to a specific user"""
        # Calculate fresh metrics
        db = SessionLocal()
        try:
            # For simplicity, get the first user and send their data
            # In a production app, you'd properly map user_id to actual users
            user = db.query(User).first()
            if not user:
                logger.warning(f"No users found in database")
                return
                
            # Get user's proxies
            user_proxies = db.query(Proxy).filter(Proxy.user_id == user.id).all()
            logger.info(f"Dashboard update for user {user_id}: found {len(user_proxies)} proxies")
            
            # Calculate basic proxy stats
            total_proxies = len(user_proxies)
            running_proxies = len([p for p in user_proxies if p.status == "running"])
            stopped_proxies = total_proxies - running_proxies
            
            # Get proxy IDs for filtering logs
            proxy_ids = [p.id for p in user_proxies]
            
            # Calculate time ranges
            now = datetime.utcnow()
            last_24h = now - timedelta(hours=24)
            last_hour = now - timedelta(hours=1)
            last_minute = now - timedelta(minutes=1)  # For true RPM calculation
            
            # Query recent logs for metrics
            recent_logs_query = db.query(LogEntry).filter(
                LogEntry.proxy_id.in_(proxy_ids),
                LogEntry.timestamp >= last_24h
            )
            recent_logs = recent_logs_query.all()
            
            # Calculate cache hit rate
            if recent_logs:
                cache_hits = len([log for log in recent_logs if log.cache_hit])
                cache_hit_rate = (cache_hits / len(recent_logs)) * 100
            else:
                cache_hit_rate = 0.0
            
            # Calculate error rate
            if recent_logs:
                errors = len([log for log in recent_logs if log.status_code >= 400])
                error_rate = (errors / len(recent_logs)) * 100
            else:
                error_rate = 0.0
            
            # Calculate RPM (requests per minute based on last 1 minute)
            recent_1min_logs = [log for log in recent_logs if log.timestamp >= last_minute]
            total_rpm = len(recent_1min_logs)  # Count of requests in the last minute = RPM
            
            # Calculate total cost (sum of cost field where available)
            total_cost = sum([log.cost for log in recent_logs if log.cost is not None])
            
            # Get in-flight requests from proxy manager
            active_proxies = proxy_manager.list_active_proxies()
            in_flight_requests = len(active_proxies)  # Simplified metric
            
            # Calculate per-proxy metrics
            proxy_metrics = []
            for proxy in user_proxies:
                # Get logs for this specific proxy in the last 1 minute
                proxy_1min_logs = [log for log in recent_1min_logs if log.proxy_id == proxy.id]
                proxy_rpm = len(proxy_1min_logs)  # Count of requests in the last minute = RPM
                
                proxy_metrics.append({
                    "id": proxy.id,  # Frontend expects "id" not "proxy_id"
                    "name": proxy.name,
                    "provider": proxy.provider,
                    "status": proxy.status,
                    "port": proxy.port,
                    "rpm": round(proxy_rpm, 1)  # Round to 1 decimal place
                })
            
            metrics_data = {
                "total_proxies": total_proxies,
                "running_proxies": running_proxies,
                "stopped_proxies": stopped_proxies,
                "cache_hit_rate": round(cache_hit_rate, 1),
                "error_rate": round(error_rate, 1),
                "total_rpm": round(total_rpm, 1),
                "total_cost": round(total_cost, 2),
                "in_flight_requests": in_flight_requests,
                "proxy_metrics": proxy_metrics,
                "last_updated": now.isoformat()
            }
            
            logger.info(f"Sending dashboard update with {len(proxy_metrics)} proxy metrics to user {user_id}")
            
            await self.send_personal_message({
                "type": "dashboard_update",
                "data": metrics_data
            }, user_id)
            
        except Exception as e:
            logger.error(f"Error calculating dashboard metrics for WebSocket: {str(e)}")
        finally:
            db.close()

manager = ConnectionManager()

@app.on_event("startup")
async def startup_event():
    """
    Startup event handler that creates default user and restarts any proxies 
    that were left in running state. This ensures proxy continuity across 
    application restarts.
    """
    logger.info("Starting up Rubberduck application...")
    
    db = SessionLocal()
    try:
        # Check if any users exist, if not create default user
        user_count = db.query(User).count()
        if user_count == 0:
            logger.info("No users found in database, creating default user")
            try:
                from .auth import user_manager
                from .models.schemas import UserCreate
                
                # Create default user
                default_user_data = UserCreate(
                    email="admin@rubberduck.local",
                    password="admin"
                )
                
                # Use the user manager to create the user properly
                default_user = await user_manager.create(default_user_data, safe=False)
                logger.info(f"Created default user: {default_user.email}")
                
            except Exception as e:
                logger.error(f"Failed to create default user: {str(e)}")
        else:
            logger.info(f"Found {user_count} existing users in database")
        
        # Query database for proxies that were left in running state
        running_proxies = db.query(Proxy).filter(Proxy.status == "running").all()
        
        if running_proxies:
            logger.info(f"Found {len(running_proxies)} proxies that were left in running state")
            
            for proxy in running_proxies:
                try:
                    logger.info(f"Restarting proxy {proxy.id} ({proxy.name}) for provider {proxy.provider}")
                    
                    # Start the proxy using the existing function
                    # Note: This will automatically update the database status and port
                    status = start_proxy_for_id(proxy.id)
                    logger.info(f"Successfully restarted proxy {proxy.id} on port {status.get('port')}")
                    
                except Exception as e:
                    logger.error(f"Failed to restart proxy {proxy.id} ({proxy.name}): {str(e)}")
                    # Mark proxy as stopped if restart failed
                    try:
                        proxy.status = "stopped"
                        db.commit()
                    except Exception as db_error:
                        logger.error(f"Failed to update proxy {proxy.id} status to stopped: {str(db_error)}")
                        db.rollback()
        else:
            logger.info("No proxies found in running state - no restart needed")
            
    except Exception as e:
        logger.error(f"Error during application startup: {str(e)}")
    finally:
        db.close()
    
    logger.info("Rubberduck application startup complete")

@app.on_event("shutdown")
async def shutdown_event():
    """
    Shutdown event handler to gracefully stop all running proxy processes.
    Database status remains 'running' so proxies can be restarted on app startup.
    """
    logger.info("Shutting down Rubberduck application...")
    
    # Get all active proxies from the proxy manager
    active_proxies = proxy_manager.list_active_proxies()
    
    if active_proxies:
        logger.info(f"Gracefully stopping {len(active_proxies)} active proxies")
        
        for proxy_info in active_proxies:
            proxy_id = proxy_info["proxy_id"]
            try:
                logger.info(f"Stopping proxy {proxy_id}")
                proxy_manager.stop_proxy(proxy_id)
                logger.info(f"Stopped proxy {proxy_id} (status remains 'running' in database for restart)")
                
            except Exception as e:
                logger.error(f"Error stopping proxy {proxy_id}: {str(e)}")
    else:
        logger.info("No active proxies to stop")
    
    logger.info("Rubberduck application shutdown complete")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Frontend development server
        "http://127.0.0.1:5173",
        "http://localhost:5175",  # Frontend development server (alternative port)
        "http://127.0.0.1:5175",
        "http://localhost:3000",  # Alternative frontend port
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"]
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserCreate),
    prefix="/users",
    tags=["users"],
)

# Social login stubs - to be implemented when social providers are configured
@app.get("/auth/google")
async def google_login():
    return {"message": "Google OAuth not yet configured"}

@app.get("/auth/github")
async def github_login():
    return {"message": "GitHub OAuth not yet configured"}

@app.get("/dashboard/metrics")
async def get_dashboard_metrics(
    user: User = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    """Get real-time dashboard metrics for the current user."""
    try:
        # Get user's proxies
        user_proxies = db.query(Proxy).filter(Proxy.user_id == user.id).all()
        
        # Calculate basic proxy stats
        total_proxies = len(user_proxies)
        running_proxies = len([p for p in user_proxies if p.status == "running"])
        stopped_proxies = total_proxies - running_proxies
        
        # Get proxy IDs for filtering logs
        proxy_ids = [p.id for p in user_proxies]
        
        # Calculate time ranges
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        last_hour = now - timedelta(hours=1)
        last_minute = now - timedelta(minutes=1)  # For true RPM calculation
        
        # Query recent logs for metrics
        recent_logs_query = db.query(LogEntry).filter(
            LogEntry.proxy_id.in_(proxy_ids),
            LogEntry.timestamp >= last_24h
        )
        recent_logs = recent_logs_query.all()
        
        # Calculate cache hit rate
        if recent_logs:
            cache_hits = len([log for log in recent_logs if log.cache_hit])
            cache_hit_rate = (cache_hits / len(recent_logs)) * 100
        else:
            cache_hit_rate = 0.0
        
        # Calculate error rate
        if recent_logs:
            errors = len([log for log in recent_logs if log.status_code >= 400])
            error_rate = (errors / len(recent_logs)) * 100
        else:
            error_rate = 0.0
        
        # Calculate RPM (requests per minute based on last 1 minute)
        recent_1min_logs = [log for log in recent_logs if log.timestamp >= last_minute]
        total_rpm = len(recent_1min_logs)  # Count of requests in the last minute = RPM
        
        # Calculate total cost (sum of cost field where available)
        total_cost = sum([log.cost for log in recent_logs if log.cost is not None])
        
        # Get in-flight requests from proxy manager
        active_proxies = proxy_manager.list_active_proxies()
        in_flight_requests = len(active_proxies)  # Simplified metric
        
        # Calculate per-proxy metrics
        proxy_metrics = []
        for proxy in user_proxies:
            # Get logs for this specific proxy in the last 1 minute
            proxy_1min_logs = [log for log in recent_1min_logs if log.proxy_id == proxy.id]
            proxy_rpm = len(proxy_1min_logs)  # Count of requests in the last minute = RPM
            
            proxy_metrics.append({
                "id": proxy.id,  # Frontend expects "id" not "proxy_id"
                "name": proxy.name,
                "provider": proxy.provider,
                "status": proxy.status,
                "port": proxy.port,
                "rpm": round(proxy_rpm, 1)  # Round to 1 decimal place
            })
        
        return {
            "total_proxies": total_proxies,
            "running_proxies": running_proxies,
            "stopped_proxies": stopped_proxies,
            "cache_hit_rate": round(cache_hit_rate, 1),
            "error_rate": round(error_rate, 1),
            "total_rpm": round(total_rpm, 1),
            "total_cost": round(total_cost, 2),
            "in_flight_requests": in_flight_requests,
            "proxy_metrics": proxy_metrics,
            "last_updated": now.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error calculating dashboard metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to calculate metrics")

@app.get("/dashboard/recent-activity")
async def get_recent_activity(
    user: User = Depends(current_active_user),
    db: Session = Depends(get_db),
    limit: int = Query(10, description="Number of recent log entries to return")
):
    """Get recent activity logs for dashboard."""
    try:
        # Get user's proxy IDs
        user_proxy_ids = [proxy.id for proxy in db.query(Proxy).filter(Proxy.user_id == user.id).all()]
        
        if not user_proxy_ids:
            return {"logs": []}
        
        # Query recent logs
        recent_logs = db.query(LogEntry).filter(
            LogEntry.proxy_id.in_(user_proxy_ids)
        ).order_by(desc(LogEntry.timestamp)).limit(limit).all()
        
        # Format logs for dashboard
        formatted_logs = []
        for log in recent_logs:
            # Get proxy name
            proxy = db.query(Proxy).filter(Proxy.id == log.proxy_id).first()
            proxy_name = proxy.name if proxy else f"Proxy {log.proxy_id}"
            
            # Determine event type
            if log.failure_type:
                event = f"Failure: {log.failure_type}"
                status = "error"
            elif log.cache_hit:
                event = "Cache hit"
                status = "success"
            elif log.status_code >= 400:
                event = f"Error {log.status_code}"
                status = "error"
            elif log.status_code >= 200:
                event = "Request completed"
                status = "success"
            else:
                event = "Request processed"
                status = "info"
            
            # Calculate time ago
            time_diff = datetime.utcnow() - log.timestamp
            if time_diff.total_seconds() < 60:
                time_ago = "Just now"
            elif time_diff.total_seconds() < 3600:
                minutes = int(time_diff.total_seconds() / 60)
                time_ago = f"{minutes} min ago"
            elif time_diff.total_seconds() < 86400:
                hours = int(time_diff.total_seconds() / 3600)
                time_ago = f"{hours} hour{'s' if hours != 1 else ''} ago"
            else:
                days = int(time_diff.total_seconds() / 86400)
                time_ago = f"{days} day{'s' if days != 1 else ''} ago"
            
            formatted_logs.append({
                "time": time_ago,
                "event": event,
                "proxy": proxy_name,
                "status": status,
                "details": {
                    "status_code": log.status_code,
                    "latency": round(log.latency, 2) if log.latency is not None else None,
                    "cache_hit": log.cache_hit
                }
            })
        
        return {"logs": formatted_logs}
        
    except Exception as e:
        logger.error(f"Error getting recent activity: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get recent activity")

@app.get("/healthz")
async def health_check():
    return {
        "status": "ok",
        "version": "0.1.0"
    }

@app.get("/protected-route")
async def protected_route(user: User = Depends(current_active_user)):
    return f"Hello {user.email}"

# WebSocket endpoint temporarily disabled due to connection issues
# TODO: Fix WebSocket implementation and re-enable
# @app.websocket("/ws/proxies")
# async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
#     # WebSocket implementation commented out

# Proxy management endpoints
@app.post("/proxies")
async def create_proxy(
    proxy_data: dict,
    user: User = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new proxy instance."""
    # Validate provider
    if proxy_data.get("provider") not in list_providers():
        raise HTTPException(status_code=400, detail="Invalid provider")
    
    # Validate port if provided
    requested_port = proxy_data.get("port")
    if requested_port is not None:
        # Validate port range
        if not isinstance(requested_port, int) or requested_port < 1024 or requested_port > 65535:
            raise HTTPException(status_code=400, detail="Port must be an integer between 1024 and 65535")
        
        # Check if port is already in use by another proxy
        existing_proxy = db.query(Proxy).filter(Proxy.port == requested_port).first()
        if existing_proxy:
            raise HTTPException(status_code=400, detail=f"Port {requested_port} is already assigned to proxy '{existing_proxy.name}'")
    
    # Create proxy in database
    proxy = Proxy(
        name=proxy_data["name"],
        provider=proxy_data["provider"],
        description=proxy_data.get("description", ""),
        port=requested_port,  # Set the user-provided port
        user_id=user.id,
        status="stopped"
    )
    
    db.add(proxy)
    db.commit()
    db.refresh(proxy)
    
    # Send WebSocket notification about new proxy
    for user_id in manager.active_connections.keys():
        await manager.send_personal_message({
            "type": "proxy_created",
            "proxy_id": proxy.id,
            "data": {
                "id": proxy.id,
                "name": proxy.name,
                "provider": proxy.provider,
                "status": proxy.status,
                "port": proxy.port
            }
        }, user_id)
    
    return {
        "id": proxy.id,
        "name": proxy.name,
        "provider": proxy.provider,
        "status": proxy.status,
        "port": proxy.port
    }

@app.get("/proxies")
async def list_proxies(
    user: User = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    """List all proxies for the current user."""
    proxies = db.query(Proxy).filter(Proxy.user_id == user.id).all()
    
    proxy_list = []
    for proxy in proxies:
        proxy_info = {
            "id": proxy.id,
            "name": proxy.name,
            "provider": proxy.provider,
            "status": proxy.status,
            "port": proxy.port,
            "description": proxy.description
        }
        
        # Get live status from proxy manager
        live_status = proxy_manager.get_proxy_status(proxy.id)
        proxy_info.update(live_status)
        
        proxy_list.append(proxy_info)
    
    return {"proxies": proxy_list}

@app.post("/proxies/{proxy_id}/start")
async def start_proxy(
    proxy_id: int,
    user: User = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    """Start a proxy instance."""
    # Verify proxy belongs to user
    proxy = db.query(Proxy).filter(
        Proxy.id == proxy_id, 
        Proxy.user_id == user.id
    ).first()
    
    if not proxy:
        raise HTTPException(status_code=404, detail="Proxy not found")
    
    # Start the proxy
    status = start_proxy_for_id(proxy_id)
    
    # WebSocket notifications temporarily disabled
    # TODO: Re-enable when WebSocket implementation is fixed
    
    return status

@app.post("/proxies/{proxy_id}/stop")
async def stop_proxy(
    proxy_id: int,
    user: User = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    """Stop a proxy instance."""
    # Verify proxy belongs to user
    proxy = db.query(Proxy).filter(
        Proxy.id == proxy_id, 
        Proxy.user_id == user.id
    ).first()
    
    if not proxy:
        raise HTTPException(status_code=404, detail="Proxy not found")
    
    # Stop the proxy
    status = stop_proxy_for_id(proxy_id)
    
    # WebSocket notifications temporarily disabled
    # TODO: Re-enable when WebSocket implementation is fixed
    
    return status

@app.delete("/proxies/{proxy_id}")
async def delete_proxy(
    proxy_id: int,
    user: User = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a proxy instance."""
    # Verify proxy belongs to user
    proxy = db.query(Proxy).filter(
        Proxy.id == proxy_id, 
        Proxy.user_id == user.id
    ).first()
    
    if not proxy:
        raise HTTPException(status_code=404, detail="Proxy not found")
    
    # Stop the proxy if it's running
    try:
        stop_proxy_for_id(proxy_id)
    except:
        pass  # Ignore errors if proxy is already stopped
    
    # Delete from database
    db.delete(proxy)
    db.commit()
    
    return {"message": f"Proxy {proxy_id} deleted successfully"}

@app.get("/providers")
async def get_providers():
    """Get list of available LLM providers."""
    return {"providers": list_providers()}

@app.delete("/cache/{proxy_id}")
async def invalidate_cache(
    proxy_id: int,
    user: User = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    """Invalidate cache for a specific proxy."""
    # Verify proxy belongs to user
    proxy = db.query(Proxy).filter(
        Proxy.id == proxy_id,
        Proxy.user_id == user.id
    ).first()
    
    if not proxy:
        raise HTTPException(status_code=404, detail="Proxy not found")
    
    # Invalidate cache
    deleted_count = cache_manager.invalidate_proxy_cache(proxy_id)
    
    return {
        "message": f"Cache invalidated for proxy {proxy_id}",
        "entries_removed": deleted_count
    }

@app.delete("/cache")
async def clear_all_cache(
    user: User = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    """Clear all cache entries for the current user's proxies."""
    logger.info(f"Clear cache request received for user {user.id}")
    
    try:
        # Get user's proxy IDs
        user_proxy_ids = [proxy.id for proxy in db.query(Proxy).filter(Proxy.user_id == user.id).all()]
        logger.info(f"Found {len(user_proxy_ids)} proxies for user {user.id}")
        
        if not user_proxy_ids:
            return {
                "message": "No proxies found for user",
                "entries_removed": 0
            }
        
        # Clear cache for all user's proxies
        total_deleted = 0
        for proxy_id in user_proxy_ids:
            deleted_count = cache_manager.invalidate_proxy_cache(proxy_id)
            total_deleted += deleted_count
            logger.info(f"Cleared {deleted_count} cache entries for proxy {proxy_id}")
        
        logger.info(f"Total cache entries cleared: {total_deleted}")
        return {
            "message": f"Cache cleared for all {len(user_proxy_ids)} proxies",
            "entries_removed": total_deleted
        }
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")

@app.get("/cache/{proxy_id}/stats")
async def get_cache_stats(
    proxy_id: int,
    user: User = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    """Get cache statistics for a proxy."""
    # Verify proxy belongs to user
    proxy = db.query(Proxy).filter(
        Proxy.id == proxy_id,
        Proxy.user_id == user.id
    ).first()
    
    if not proxy:
        raise HTTPException(status_code=404, detail="Proxy not found")
    
    # Get cache stats
    stats = cache_manager.get_cache_stats(proxy_id)
    
    return {
        "proxy_id": proxy_id,
        "cache_stats": stats
    }

@app.get("/proxies/{proxy_id}/failure-config")
async def get_failure_config(
    proxy_id: int,
    user: User = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    """Get failure configuration for a proxy."""
    # Verify proxy belongs to user
    proxy = db.query(Proxy).filter(
        Proxy.id == proxy_id,
        Proxy.user_id == user.id
    ).first()
    
    if not proxy:
        raise HTTPException(status_code=404, detail="Proxy not found")
    
    # Get failure configuration
    failure_config = FailureConfig.from_json(proxy.failure_config)
    
    return {
        "proxy_id": proxy_id,
        "failure_config": {
            "timeout_enabled": failure_config.timeout_enabled,
            "timeout_seconds": failure_config.timeout_seconds,
            "timeout_rate": failure_config.timeout_rate,
            "error_injection_enabled": failure_config.error_injection_enabled,
            "error_rates": failure_config.error_rates,
            "ip_filtering_enabled": failure_config.ip_filtering_enabled,
            "ip_allowlist": failure_config.ip_allowlist,
            "ip_blocklist": failure_config.ip_blocklist,
            "rate_limiting_enabled": failure_config.rate_limiting_enabled,
            "requests_per_minute": failure_config.requests_per_minute
        }
    }

@app.put("/proxies/{proxy_id}/failure-config")
async def update_failure_config(
    proxy_id: int,
    config_data: dict,
    user: User = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    """Update failure configuration for a proxy."""
    # Verify proxy belongs to user
    proxy = db.query(Proxy).filter(
        Proxy.id == proxy_id,
        Proxy.user_id == user.id
    ).first()
    
    if not proxy:
        raise HTTPException(status_code=404, detail="Proxy not found")
    
    # Create failure config from provided data
    try:
        failure_config = FailureConfig(**config_data)
        proxy.failure_config = failure_config.to_json()
        db.commit()
        
        return {
            "message": f"Failure configuration updated for proxy {proxy_id}",
            "proxy_id": proxy_id,
            "failure_config": config_data
        }
    except (TypeError, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid configuration: {str(e)}")

@app.post("/proxies/{proxy_id}/failure-config/reset")
async def reset_failure_config(
    proxy_id: int,
    user: User = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    """Reset failure configuration to defaults for a proxy."""
    # Verify proxy belongs to user
    proxy = db.query(Proxy).filter(
        Proxy.id == proxy_id,
        Proxy.user_id == user.id
    ).first()
    
    if not proxy:
        raise HTTPException(status_code=404, detail="Proxy not found")
    
    # Reset to default configuration
    default_config = create_default_failure_config()
    proxy.failure_config = default_config.to_json()
    db.commit()
    
    return {
        "message": f"Failure configuration reset to defaults for proxy {proxy_id}",
        "proxy_id": proxy_id
    }

@app.get("/logs")
async def get_logs(
    user: User = Depends(current_active_user),
    db: Session = Depends(get_db),
    proxy_id: Optional[int] = Query(None, description="Filter by proxy ID"),
    status_code: Optional[int] = Query(None, description="Filter by status code"),
    failure_type: Optional[str] = Query(None, description="Filter by failure type"),
    cache_hit: Optional[bool] = Query(None, description="Filter by cache hit status"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(100, description="Number of logs to return"),
    offset: int = Query(0, description="Number of logs to skip"),
    export: Optional[str] = Query(None, description="Export format: csv or json")
):
    """Get logs with optional filtering and export functionality."""
    
    # Build query
    query = db.query(LogEntry).join(Proxy).filter(Proxy.user_id == user.id)
    
    # Apply filters
    if proxy_id:
        query = query.filter(LogEntry.proxy_id == proxy_id)
    
    if status_code:
        query = query.filter(LogEntry.status_code == status_code)
    
    if failure_type:
        query = query.filter(LogEntry.failure_type == failure_type)
    
    if cache_hit is not None:
        query = query.filter(LogEntry.cache_hit == cache_hit)
    
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(LogEntry.timestamp >= start_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD")
    
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            query = query.filter(LogEntry.timestamp < end_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD")
    
    # Order by timestamp (newest first)
    query = query.order_by(desc(LogEntry.timestamp))
    
    # Handle export formats
    if export == "csv":
        return _export_logs_csv(query.all())
    elif export == "json":
        return _export_logs_json(query.all())
    
    # Regular pagination for API response
    logs = query.offset(offset).limit(limit).all()
    total_count = query.count()
    
    log_data = []
    for log in logs:
        log_data.append({
            "id": log.id,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            "proxy_id": log.proxy_id,
            "ip_address": log.ip_address,
            "status_code": log.status_code,
            "latency": round(log.latency, 2) if log.latency is not None else None,
            "cache_hit": log.cache_hit,
            "prompt_hash": log.prompt_hash,
            "failure_type": log.failure_type,
            "token_usage": log.token_usage,
            "cost": log.cost
        })
    
    return {
        "logs": log_data,
        "total_count": total_count,
        "limit": limit,
        "offset": offset
    }

def _export_logs_csv(logs: List[LogEntry]) -> StreamingResponse:
    """Export logs as CSV file."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "timestamp", "proxy_id", "ip_address", "status_code", "latency_ms",
        "cache_hit", "prompt_hash", "failure_type", "token_usage", "cost"
    ])
    
    # Write data
    for log in logs:
        writer.writerow([
            log.timestamp.isoformat() if log.timestamp else "",
            log.proxy_id,
            log.ip_address,
            log.status_code,
            round(log.latency, 2) if log.latency is not None else "",
            log.cache_hit,
            log.prompt_hash or "",
            log.failure_type or "",
            log.token_usage or "",
            log.cost or ""
        ])
    
    output.seek(0)
    
    # Create streaming response
    def iter_csv():
        yield output.getvalue()
    
    return StreamingResponse(
        iter_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=rubberduck_logs.csv"}
    )

def _export_logs_json(logs: List[LogEntry]) -> Response:
    """Export logs as JSON file."""
    import json
    
    log_data = []
    for log in logs:
        log_data.append({
            "id": log.id,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            "proxy_id": log.proxy_id,
            "ip_address": log.ip_address,
            "status_code": log.status_code,
            "latency": round(log.latency, 2) if log.latency is not None else None,
            "cache_hit": log.cache_hit,
            "prompt_hash": log.prompt_hash,
            "failure_type": log.failure_type,
            "token_usage": log.token_usage,
            "cost": log.cost
        })
    
    json_str = json.dumps({"logs": log_data}, indent=2)
    
    return Response(
        content=json_str,
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=rubberduck_logs.json"}
    )

@app.get("/logs/stats")
async def get_log_stats(
    user: User = Depends(current_active_user),
    db: Session = Depends(get_db),
    proxy_id: Optional[int] = Query(None, description="Filter by proxy ID"),
    days: int = Query(7, description="Number of days to analyze")
):
    """Get logging statistics and metrics."""
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Build base query
    query = db.query(LogEntry).join(Proxy).filter(
        Proxy.user_id == user.id,
        LogEntry.timestamp >= start_date,
        LogEntry.timestamp <= end_date
    )
    
    if proxy_id:
        query = query.filter(LogEntry.proxy_id == proxy_id)
    
    logs = query.all()
    
    if not logs:
        return {
            "total_requests": 0,
            "cache_hit_rate": 0.0,
            "error_rate": 0.0,
            "average_latency": 0.0,
            "status_code_distribution": {},
            "failure_type_distribution": {},
            "requests_by_day": {}
        }
    
    # Calculate metrics
    total_requests = len(logs)
    cache_hits = sum(1 for log in logs if log.cache_hit)
    errors = sum(1 for log in logs if log.status_code >= 400)
    latencies = [log.latency for log in logs if log.latency]
    
    cache_hit_rate = (cache_hits / total_requests) * 100 if total_requests > 0 else 0
    error_rate = (errors / total_requests) * 100 if total_requests > 0 else 0
    average_latency = sum(latencies) / len(latencies) if latencies else 0
    
    # Status code distribution
    status_code_dist = {}
    for log in logs:
        status = str(log.status_code)
        status_code_dist[status] = status_code_dist.get(status, 0) + 1
    
    # Failure type distribution
    failure_type_dist = {}
    for log in logs:
        if log.failure_type:
            failure_type_dist[log.failure_type] = failure_type_dist.get(log.failure_type, 0) + 1
    
    # Requests by day
    requests_by_day = {}
    for log in logs:
        if log.timestamp:
            day_key = log.timestamp.strftime("%Y-%m-%d")
            requests_by_day[day_key] = requests_by_day.get(day_key, 0) + 1
    
    return {
        "total_requests": total_requests,
        "cache_hit_rate": round(cache_hit_rate, 2),
        "error_rate": round(error_rate, 2),
        "average_latency": round(average_latency, 2),
        "status_code_distribution": status_code_dist,
        "failure_type_distribution": failure_type_dist,
        "requests_by_day": requests_by_day,
        "date_range": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "days": days
        }
    }

@app.delete("/logs")
async def purge_logs(
    user: User = Depends(current_active_user),
    db: Session = Depends(get_db),
    proxy_id: Optional[int] = Query(None, description="Purge logs for specific proxy"),
    days: Optional[int] = Query(None, description="Purge logs older than N days"),
    confirm: bool = Query(False, description="Confirmation required for purge")
):
    """Purge log entries with optional filtering."""
    
    if not confirm:
        raise HTTPException(
            status_code=400, 
            detail="Purge operation requires confirmation. Add ?confirm=true to the request."
        )
    
    # First get user's proxy IDs for filtering
    user_proxy_ids = [proxy.id for proxy in db.query(Proxy).filter(Proxy.user_id == user.id).all()]
    
    if not user_proxy_ids:
        return {"message": "No proxies found for user", "deleted_count": 0}
    
    # Build query for logs to delete (without join to avoid SQLAlchemy delete limitation)
    query = db.query(LogEntry).filter(LogEntry.proxy_id.in_(user_proxy_ids))
    
    if proxy_id:
        if proxy_id not in user_proxy_ids:
            raise HTTPException(status_code=404, detail="Proxy not found")
        query = query.filter(LogEntry.proxy_id == proxy_id)
    
    if days:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(LogEntry.timestamp < cutoff_date)
    
    # Count logs to be deleted
    count = query.count()
    
    if count == 0:
        return {"message": "No logs found matching the criteria", "deleted_count": 0}
    
    # Delete logs
    query.delete(synchronize_session=False)
    db.commit()
    
    return {
        "message": f"Successfully purged {count} log entries",
        "deleted_count": count
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
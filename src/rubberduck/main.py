import csv
import io
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException, Query
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
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

app = FastAPI(title="Rubberduck", version="0.1.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Frontend development server
        "http://127.0.0.1:5173",
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

@app.get("/healthz")
async def health_check():
    return {
        "status": "ok",
        "version": "0.1.0"
    }

@app.get("/protected-route")
async def protected_route(user: User = Depends(current_active_user)):
    return f"Hello {user.email}"

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
    
    # Create proxy in database
    proxy = Proxy(
        name=proxy_data["name"],
        provider=proxy_data["provider"],
        description=proxy_data.get("description", ""),
        user_id=user.id,
        status="stopped"
    )
    
    db.add(proxy)
    db.commit()
    db.refresh(proxy)
    
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
            "latency": log.latency,
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
            log.latency,
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
            "latency": log.latency,
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
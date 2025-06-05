import json
import hashlib
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from database import SessionLocal
from models import CacheEntry, Proxy
from providers import get_provider


class CacheManager:
    """
    Manages response caching for LLM proxy instances.
    Only successful (2xx) responses are cached.
    """
    
    def __init__(self):
        pass
    
    def generate_cache_key(self, proxy_id: int, normalized_request: Dict[str, Any]) -> str:
        """
        Generate a cache key for a request.
        
        Args:
            proxy_id: The proxy instance ID
            normalized_request: Normalized request data
            
        Returns:
            SHA-256 hash as cache key
        """
        # Include proxy_id in cache key to scope cache per proxy
        cache_data = {
            "proxy_id": proxy_id,
            "request": normalized_request
        }
        
        # Sort keys for consistent hashing
        sorted_data = json.dumps(cache_data, sort_keys=True)
        return hashlib.sha256(sorted_data.encode()).hexdigest()
    
    def get_cached_response(self, proxy_id: int, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached response if available.
        
        Args:
            proxy_id: The proxy instance ID
            cache_key: Cache key to lookup
            
        Returns:
            Cached response data or None if not found
        """
        db = SessionLocal()
        try:
            cache_entry = db.query(CacheEntry).filter(
                CacheEntry.proxy_id == proxy_id,
                CacheEntry.cache_key == cache_key
            ).first()
            
            if cache_entry:
                response_data = json.loads(cache_entry.response_data)
                response_headers = json.loads(cache_entry.response_headers) if cache_entry.response_headers else {}
                
                return {
                    "status_code": 200,  # Cached responses are always successful
                    "data": response_data,
                    "headers": response_headers,
                    "cached": True,
                    "cache_timestamp": cache_entry.created_at.isoformat()
                }
            
            return None
            
        finally:
            db.close()
    
    def store_response(
        self, 
        proxy_id: int, 
        cache_key: str, 
        normalized_request: Dict[str, Any],
        response_data: Dict[str, Any],
        response_headers: Dict[str, str],
        status_code: int
    ) -> bool:
        """
        Store a response in cache if it's successful (2xx).
        
        Args:
            proxy_id: The proxy instance ID
            cache_key: Cache key for the request
            normalized_request: Normalized request data
            response_data: Response data to cache
            response_headers: Response headers
            status_code: HTTP status code
            
        Returns:
            True if response was cached, False otherwise
        """
        # Only cache successful responses (2xx status codes)
        if not (200 <= status_code < 300):
            return False
        
        db = SessionLocal()
        try:
            # Check if cache entry already exists (avoid duplicates)
            existing_entry = db.query(CacheEntry).filter(
                CacheEntry.proxy_id == proxy_id,
                CacheEntry.cache_key == cache_key
            ).first()
            
            if existing_entry:
                # Update existing entry
                existing_entry.request_data = json.dumps(normalized_request)
                existing_entry.response_data = json.dumps(response_data)
                existing_entry.response_headers = json.dumps(response_headers)
                existing_entry.created_at = datetime.utcnow()
            else:
                # Create new cache entry
                cache_entry = CacheEntry(
                    proxy_id=proxy_id,
                    cache_key=cache_key,
                    request_data=json.dumps(normalized_request),
                    response_data=json.dumps(response_data),
                    response_headers=json.dumps(response_headers)
                )
                db.add(cache_entry)
            
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            print(f"Error storing cache entry: {e}")
            return False
        finally:
            db.close()
    
    def invalidate_proxy_cache(self, proxy_id: int) -> int:
        """
        Invalidate all cache entries for a specific proxy.
        
        Args:
            proxy_id: The proxy instance ID
            
        Returns:
            Number of cache entries removed
        """
        db = SessionLocal()
        try:
            deleted_count = db.query(CacheEntry).filter(
                CacheEntry.proxy_id == proxy_id
            ).delete()
            
            db.commit()
            return deleted_count
            
        except Exception as e:
            db.rollback()
            print(f"Error invalidating cache: {e}")
            return 0
        finally:
            db.close()
    
    def get_cache_stats(self, proxy_id: int) -> Dict[str, Any]:
        """
        Get cache statistics for a proxy.
        
        Args:
            proxy_id: The proxy instance ID
            
        Returns:
            Dictionary with cache statistics
        """
        db = SessionLocal()
        try:
            total_entries = db.query(CacheEntry).filter(
                CacheEntry.proxy_id == proxy_id
            ).count()
            
            if total_entries > 0:
                oldest_entry = db.query(CacheEntry).filter(
                    CacheEntry.proxy_id == proxy_id
                ).order_by(CacheEntry.created_at.asc()).first()
                
                newest_entry = db.query(CacheEntry).filter(
                    CacheEntry.proxy_id == proxy_id
                ).order_by(CacheEntry.created_at.desc()).first()
                
                return {
                    "total_entries": total_entries,
                    "oldest_entry": oldest_entry.created_at.isoformat() if oldest_entry else None,
                    "newest_entry": newest_entry.created_at.isoformat() if newest_entry else None
                }
            else:
                return {
                    "total_entries": 0,
                    "oldest_entry": None,
                    "newest_entry": None
                }
                
        finally:
            db.close()


# Global cache manager instance
cache_manager = CacheManager()


def process_request_with_cache(
    proxy_id: int,
    provider_name: str,
    request_data: Dict[str, Any],
    headers: Dict[str, str],
    endpoint: str
) -> Tuple[Dict[str, Any], bool]:
    """
    Process a request with caching support.
    
    Args:
        proxy_id: The proxy instance ID
        provider_name: Name of the LLM provider
        request_data: Request data
        headers: HTTP headers
        endpoint: API endpoint
        
    Returns:
        Tuple of (response_data, was_cached)
    """
    # Get the provider to normalize the request
    provider = get_provider(provider_name)
    normalized_request = provider.normalize_request(request_data)
    
    # Generate cache key
    cache_key = cache_manager.generate_cache_key(proxy_id, normalized_request)
    
    # Try to get cached response
    cached_response = cache_manager.get_cached_response(proxy_id, cache_key)
    if cached_response:
        return cached_response, True
    
    # Make actual request to provider (this would be async in the real implementation)
    # For now, we'll return a placeholder
    return {
        "status_code": 200,
        "data": {"message": "This would be the actual provider response"},
        "headers": {"content-type": "application/json"},
        "cached": False
    }, False
"""
Simple cache implementation for FastAPI
"""
import time
import hashlib
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("uvicorn.error")


class SimpleCache:
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _generate_key(self, endpoint: str, **params) -> str:
        """Generate cache key from endpoint and parameters"""
        # Create a consistent string representation
        param_str = json.dumps(params, sort_keys=True, default=str)
        cache_input = f"{endpoint}:{param_str}"
        return hashlib.md5(cache_input.encode()).hexdigest()

    def get(self, endpoint: str, **params) -> Optional[Any]:
        """Get cached response if valid"""
        key = self._generate_key(endpoint, **params)
        
        if key not in self._cache:
            logger.info(f"Cache miss for {endpoint} - key: {key[:8]}...")
            return None
            
        cache_entry = self._cache[key]
        current_time = time.time()
        
        # Check if cache has expired
        if current_time > cache_entry["expires_at"]:
            del self._cache[key]
            logger.info(f"Cache expired for {endpoint} - key: {key[:8]}...")
            return None
            
        logger.info(f"Cache hit for {endpoint} - key: {key[:8]}...")
        return cache_entry["data"]

    def set(self, endpoint: str, data: Any, ttl: int, **params) -> None:
        """Cache response with TTL"""
        key = self._generate_key(endpoint, **params)
        expires_at = time.time() + ttl
        
        self._cache[key] = {
            "data": data,
            "expires_at": expires_at,
            "created_at": time.time(),
            "endpoint": endpoint
        }
        
        logger.info(f"Cached response for {endpoint} - key: {key[:8]}... (TTL: {ttl}s)")

    def clear(self) -> int:
        """Clear all cached entries"""
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"Cleared {count} cache entries")
        return count

    def clear_expired(self) -> int:
        """Clear only expired entries"""
        current_time = time.time()
        expired_keys = []
        
        for key, entry in self._cache.items():
            if current_time > entry["expires_at"]:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]
            
        logger.info(f"Cleared {len(expired_keys)} expired cache entries")
        return len(expired_keys)

    def get_stats(self) -> Dict:
        """Get cache statistics"""
        current_time = time.time()
        active_entries = 0
        expired_entries = 0
        endpoint_stats = {}
        
        for entry in self._cache.values():
            endpoint = entry.get("endpoint", "unknown")
            if endpoint not in endpoint_stats:
                endpoint_stats[endpoint] = {"active": 0, "expired": 0}
            
            if current_time <= entry["expires_at"]:
                active_entries += 1
                endpoint_stats[endpoint]["active"] += 1
            else:
                expired_entries += 1
                endpoint_stats[endpoint]["expired"] += 1
        
        return {
            "total_entries": len(self._cache),
            "active_entries": active_entries,
            "expired_entries": expired_entries,
            "endpoint_breakdown": endpoint_stats,
            "cache_size_mb": self._get_cache_size_mb()
        }

    def _get_cache_size_mb(self) -> float:
        """Estimate cache size in MB"""
        try:
            cache_str = json.dumps(self._cache, default=str)
            size_bytes = len(cache_str.encode('utf-8'))
            return round(size_bytes / (1024 * 1024), 2)
        except:
            return 0.0


# Global cache instance
simple_cache = SimpleCache()
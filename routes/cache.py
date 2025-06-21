"""
Cache management endpoints
"""

from fastapi import APIRouter
from utils.simple_cache import simple_cache

router = APIRouter(prefix="/cache", tags=["cache"])


@router.delete("/")
async def clear_all_cache():
    """Clear all cached responses"""
    cleared_count = simple_cache.clear()
    return {"message": f"Cleared {cleared_count} cached entries"}


@router.delete("/expired")
async def clear_expired_cache():
    """Clear only expired cached responses"""
    cleared_count = simple_cache.clear_expired()
    return {"message": f"Cleared {cleared_count} expired cache entries"}


@router.get("/stats")
async def get_cache_stats():
    """Get comprehensive cache statistics"""
    stats = simple_cache.get_stats()
    return {"cache_stats": stats, "default_ttl_seconds": 300}

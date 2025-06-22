from fastapi import APIRouter, HTTPException
from .scraper import YouTubeScraper
from .models import ChannelHealthResponse
from utils.simple_cache import simple_cache


router = APIRouter(prefix="/youtube", tags=["youtube"])
scraper = YouTubeScraper()


@router.get("/channel/health", response_model=ChannelHealthResponse)
async def get_channel_health(url: str):
    """Get comprehensive channel health analysis and content insights"""
    endpoint = "youtube.channel.health"

    # Check cache first
    cached_result = simple_cache.get(endpoint, url=url)
    if cached_result:
        return cached_result

    try:
        result = await scraper.get_channel_health(url)

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        # Cache successful result for 5 minutes
        simple_cache.set(endpoint, result, ttl=300, url=url)
        return result

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error analyzing channel: {str(e)}"
        )

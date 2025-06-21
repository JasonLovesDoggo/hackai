from fastapi import APIRouter, HTTPException
from .scraper import YouTubeScraper


router = APIRouter(prefix="/youtube", tags=["youtube"])
scraper = YouTubeScraper()


@router.get("/channel/health")
async def get_channel_health(url: str):
    """Get channel health analysis and content type"""
    try:
        result = await scraper.get_channel_health(url)

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error analyzing channel: {str(e)}"
        )

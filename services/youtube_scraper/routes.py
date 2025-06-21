from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from .models import ScrapeRequest, ChannelInfo
from .scraper import YouTubeScraper
import asyncio


router = APIRouter(prefix="/youtube", tags=["youtube"])
scraper = YouTubeScraper()


@router.post("/channel", response_model=ChannelInfo)
async def scrape_channel(request: ScrapeRequest):
    try:
        channel_info = await scraper.get_channel_info(
            request.channel_id, 
            request.max_videos
        )
        
        if not channel_info:
            raise HTTPException(
                status_code=404, 
                detail=f"Channel {request.channel_id} not found or could not be scraped"
            )
        
        return channel_info
    
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error scraping channel: {str(e)}"
        )


@router.get("/channel/{channel_input}")
async def get_channel_info(channel_input: str, max_videos: int = 20):
    try:
        channel_info = await scraper.get_channel_info(channel_input, max_videos)
        
        if not channel_info:
            raise HTTPException(
                status_code=404, 
                detail=f"Channel {channel_input} not found"
            )
        
        return channel_info
    
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error fetching channel info: {str(e)}"
        )


@router.get("/video/{video_id}")
async def get_video_info(video_id: str):
    try:
        video_info = await scraper.get_video_details(video_id)
        
        if not video_info:
            raise HTTPException(
                status_code=404, 
                detail=f"Video {video_id} not found"
            )
        
        return video_info
    
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error fetching video info: {str(e)}"
        )
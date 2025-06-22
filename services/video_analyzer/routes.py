from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from .analyzer import analyze_youtube_video


router = APIRouter(prefix="/video-analysis", tags=["video-analysis"])


class VideoRequest(BaseModel):
    video_url: str


@router.post("/analyze")
async def analyze_video(data: VideoRequest):
    try:
        result = analyze_youtube_video(data.video_url)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

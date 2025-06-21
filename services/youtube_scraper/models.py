from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class VideoInfo(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    tags: List[str] = []
    view_count: int = 0
    like_count: Optional[int] = None
    comment_count: Optional[int] = None
    duration: Optional[int] = None
    upload_date: Optional[datetime] = None
    thumbnail_url: Optional[str] = None


class ChannelInfo(BaseModel):
    id: str
    name: str
    handle: Optional[str] = None
    description: Optional[str] = None
    subscriber_count: Optional[int] = None
    video_count: Optional[int] = None
    view_count: Optional[int] = None
    profile_picture_url: Optional[str] = None
    banner_url: Optional[str] = None
    keywords: List[str] = []
    videos: List[VideoInfo] = []


class ScrapeRequest(BaseModel):
    channel_id: str
    max_videos: int = 50
    include_video_details: bool = True

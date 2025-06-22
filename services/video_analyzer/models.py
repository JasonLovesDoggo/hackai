from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class VideoAnalysisRequest(BaseModel):
    """Request model for video analysis"""
    features: List[str] = ["conversation", "visual", "text_in_video", "action", "concept"]


class VideoAnalysisResult(BaseModel):
    """Response model for video analysis results"""
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime 
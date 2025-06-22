from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class VideoAnalysisRequest(BaseModel):
    """Request model for video analysis"""
    features: List[str] = ["visual", "audio"]


class TranscriptSegment(BaseModel):
    """Individual transcript segment with timing"""
    start: float
    end: float
    text: str
    confidence: Optional[float] = None


class VisualObject(BaseModel):
    """Detected visual object or scene"""
    label: str
    confidence: float
    start: float
    end: float
    description: Optional[str] = None


class SceneAnalysis(BaseModel):
    """Scene/chapter analysis"""
    start: float
    end: float
    description: str
    key_elements: List[str] = []
    confidence: Optional[float] = None


class VideoContext(BaseModel):
    """Context and analysis of the video content"""
    content_summary: str
    main_topics: List[str] = []
    content_type: str
    duration: Optional[float] = None
    language: Optional[str] = None


class VideoAnalysisResult(BaseModel):
    """Comprehensive video analysis response"""
    task_id: str
    status: str
    video_metadata: Dict[str, Any] = {}
    transcript: List[TranscriptSegment] = []
    visual_analysis: List[VisualObject] = []
    scenes: List[SceneAnalysis] = []
    context: Optional[VideoContext] = None
    raw_data: Optional[Dict[str, Any]] = None  # Keep original API response
    error_message: Optional[str] = None
    created_at: datetime 
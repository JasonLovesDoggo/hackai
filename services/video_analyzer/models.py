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


class FrameAnalysis(BaseModel):
    """Frame-by-frame analysis for a specific time interval"""
    start_time: float
    end_time: float
    visual_objects: List[VisualObject] = []
    scene_description: Optional[str] = None
    dominant_colors: List[str] = []
    text_detected: List[str] = []
    audio_analysis: Optional[Dict[str, Any]] = None


class TimeBasedAnalysis(BaseModel):
    """Time-based analysis with frame breakdowns"""
    interval_seconds: int = 5
    total_frames: int
    frames: List[FrameAnalysis] = []
    summary: Optional[str] = None


class VideoContext(BaseModel):
    """Context and analysis of the video content"""
    content_summary: Optional[str] = ""
    main_topics: List[str] = []
    content_type: Optional[str] = "unknown"
    duration: Optional[float] = None
    language: Optional[str] = None
    title: Optional[str] = None
    hashtags: List[str] = []
    target_audience: Optional[str] = None
    sentiment: Optional[str] = None
    key_insights: List[str] = []


class VideoAnalysisResult(BaseModel):
    """Comprehensive video analysis response"""
    task_id: str
    status: str
    video_metadata: Dict[str, Any] = {}
    transcript: List[TranscriptSegment] = []
    visual_analysis: List[VisualObject] = []
    scenes: List[SceneAnalysis] = []
    context: Optional[VideoContext] = None
    time_based_analysis: Optional[TimeBasedAnalysis] = None
    raw_data: Optional[Dict[str, Any]] = None  # Keep original API response
    error_message: Optional[str] = None
    created_at: datetime 
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


class AudioAnalysis(BaseModel):
    """Audio analysis results"""
    speech_detected: bool
    music_detected: Optional[bool] = None
    background_noise: Optional[str] = None
    audio_quality: Optional[str] = None


class SceneAnalysis(BaseModel):
    """Scene/chapter analysis"""
    start: float
    end: float
    description: str
    key_elements: List[str] = []
    confidence: Optional[float] = None


class VideoInsights(BaseModel):
    """Actionable insights from video analysis"""
    content_type: str  # e.g., "tutorial", "entertainment", "news", "interview"
    target_audience: Optional[str] = None
    key_topics: List[str] = []
    sentiment: Optional[str] = None  # positive, negative, neutral
    engagement_hooks: List[str] = []  # moments that could engage viewers
    improvement_suggestions: List[str] = []


class VideoAnalysisResult(BaseModel):
    """Comprehensive video analysis response"""
    task_id: str
    status: str
    video_metadata: Dict[str, Any] = {}
    transcript: List[TranscriptSegment] = []
    visual_analysis: List[VisualObject] = []
    audio_analysis: Optional[AudioAnalysis] = None
    scenes: List[SceneAnalysis] = []
    insights: Optional[VideoInsights] = None
    raw_data: Optional[Dict[str, Any]] = None  # Keep original API response
    error_message: Optional[str] = None
    created_at: datetime 
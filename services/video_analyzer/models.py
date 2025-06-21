

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class VideoAnalysisRequest(BaseModel):
    video_url: Optional[str] = None
    video_file_path: Optional[str] = None
    features: List[str] = ["conversation", "visual", "text_in_video", "action", "concept"]
    language: str = "en"


class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str
    confidence: Optional[float] = None


class VisualObject(BaseModel):
    label: str
    confidence: float
    start: float
    end: float


class Scene(BaseModel):
    start: float
    end: float
    description: str
    confidence: Optional[float] = None


class Concept(BaseModel):
    name: str
    confidence: float
    start: float
    end: float


class VideoAnalysisResult(BaseModel):
    video_id: str
    status: str
    transcript: List[TranscriptSegment] = []
    tags: List[str] = []
    visual_objects: List[VisualObject] = []
    scenes: List[Scene] = []
    concepts: List[Concept] = []
    analysis_duration: Optional[float] = None
    created_at: datetime
    error_message: Optional[str] = None


class AnalysisStatus(BaseModel):
    video_id: str
    status: str  # "pending", "processing", "completed", "failed"
    progress: Optional[float] = None
    estimated_completion: Optional[datetime] = None
    error_message: Optional[str] = None

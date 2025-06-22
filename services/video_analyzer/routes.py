from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List, Optional
import os
import tempfile

from .models import VideoAnalysisRequest, VideoAnalysisResult
from .analyzer import VideoAnalyzer

router = APIRouter(prefix="/video-analysis", tags=["video-analysis"])

# Lazy initialization
_analyzer = None

def get_analyzer():
    global _analyzer
    if _analyzer is None:
        _analyzer = VideoAnalyzer()
    return _analyzer

@router.post("/analyze-file", response_model=VideoAnalysisResult)
def analyze_video_file(
    file: UploadFile = File(...),
    features: Optional[str] = Form("visual,audio")
):
    """
    Upload and analyze a video file using Twelve Labs API
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('video/'):
            raise HTTPException(
                status_code=400,
                detail="Uploaded file must be a video"
            )
        
        # Save uploaded file to temporary location
        temp_fd, temp_path = tempfile.mkstemp(suffix='.mp4')
        os.close(temp_fd)
        
        try:
            # Write uploaded file to temp location
            with open(temp_path, 'wb') as f:
                content = file.file.read()
                f.write(content)
            
            # Parse features
            feature_list = [f.strip() for f in features.split(",") if f.strip()]
            
            # Create request
            request = VideoAnalysisRequest(features=feature_list)
            
            # Analyze video
            analyzer = get_analyzer()
            result = analyzer.analyze_video(temp_path, request)
            
            if result.status == "failed":
                raise HTTPException(
                    status_code=400,
                    detail=result.error_message or "Video analysis failed"
                )
            
            return result
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error analyzing video file: {str(e)}"
        )

@router.get("/supported-features")
def get_supported_features():
    """Get list of supported analysis features"""
    return {
        "features": [
            "visual",
            "audio"
        ],
        "description": "Available features for video analysis using Twelve Labs marengo2.7 model"
    }

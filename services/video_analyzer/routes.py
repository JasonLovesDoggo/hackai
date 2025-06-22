import os
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from typing import List
from .models import VideoAnalysisRequest, VideoAnalysisResult
from .analyzer import VideoAnalyzer

router = APIRouter(prefix="/video-analysis", tags=["Video Analysis"])

@router.post("/analyze", response_model=VideoAnalysisResult)
async def analyze_video(
    file: UploadFile = File(...),
    features: str = Form("visual,audio")  # Default features
):
    """
    Analyze a video file and return comprehensive results including:
    - Transcript with timing
    - Visual object detection
    - Audio analysis
    - Scene analysis
    - Actionable insights
    """
    # Validate file type
    if not file.content_type or not file.content_type.startswith('video/'):
        raise HTTPException(status_code=400, detail="File must be a video")
    
    # Parse features
    feature_list = [f.strip() for f in features.split(',')]
    request = VideoAnalysisRequest(features=feature_list)
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as temp_file:
        try:
            # Write uploaded file to temporary file
            content = await file.read()
            temp_file.write(content)
            temp_file.flush()
            
            # Analyze the video
            analyzer = VideoAnalyzer()
            result = analyzer.analyze_video(temp_file.name, request)
            
            return result
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file.name)
            except:
                pass

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "video-analysis"}

@router.get("/features")
async def get_available_features():
    """Get available analysis features"""
    return {
        "available_features": [
            "visual",      # Visual object detection
            "audio"        # Audio analysis and transcript
        ],
        "description": "These features are supported by the Twelve Labs API"
    }

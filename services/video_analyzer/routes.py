from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
import tempfile

from .models import VideoAnalysisRequest, VideoAnalysisResult, AnalysisStatus
from .analyzer import VideoAnalyzer
from .resolver import VideoInputResolver


router = APIRouter(prefix="/video-analysis", tags=["video-analysis"])
analyzer = VideoAnalyzer()
resolver = VideoInputResolver()


@router.post("/analyze", response_model=VideoAnalysisResult)
def analyze_video(request: VideoAnalysisRequest):
    """
    Analyze a video using Twelve Labs API
    
    Accepts either a video URL or file path and returns comprehensive analysis
    including transcript, tags, visual objects, scenes, and concepts.
    """
    try:
        result = analyzer.analyze_video(request)
        
        if result.status == "failed":
            raise HTTPException(
                status_code=400,
                detail=result.error_message or "Video analysis failed"
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error analyzing video: {str(e)}"
        )


@router.post("/analyze-url")
def analyze_video_url(
    video_url: str = Form(...),
    features: Optional[str] = Form("conversation,visual,text_in_video,action,concept"),
    language: str = Form("en")
):
    """
    Analyze a video from URL
    
    Convenience endpoint for analyzing videos from URLs with form data
    """
    try:
        # Parse features string to list
        feature_list = [f.strip() for f in features.split(",") if f.strip()]
        
        request = VideoAnalysisRequest(
            video_url=video_url,
            features=feature_list,
            language=language
        )
        
        result = analyzer.analyze_video(request)
        
        if result.status == "failed":
            raise HTTPException(
                status_code=400,
                detail=result.error_message or "Video analysis failed"
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error analyzing video URL: {str(e)}"
        )


@router.post("/analyze-file")
def analyze_video_file(
    file: UploadFile = File(...),
    features: Optional[str] = Form("conversation,visual,text_in_video,action,concept"),
    language: str = Form("en")
):
    """
    Analyze an uploaded video file
    
    Accepts video file upload and returns analysis results
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
            
            # Parse features string to list
            feature_list = [f.strip() for f in features.split(",") if f.strip()]
            
            request = VideoAnalysisRequest(
                video_file_path=temp_path,
                features=feature_list,
                language=language
            )
            
            result = analyzer.analyze_video(request)
            
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


@router.get("/validate-input/{input_str}")
def validate_video_input(input_str: str):
    """
    Validate video input (URL or file path) without performing analysis
    
    Useful for checking if a video URL or file path is valid before analysis
    """
    try:
        input_info = resolver.get_video_info(input_str)
        return {
            "input": input_str,
            "is_valid": input_info['is_valid'],
            "input_type": input_info['input_type'],
            "details": input_info
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error validating input: {str(e)}"
        )


@router.get("/status/{video_id}", response_model=AnalysisStatus)
def get_analysis_status(video_id: str):
    """
    Get the status of a video analysis
    
    Note: This is a placeholder implementation. In a real system,
    you would store analysis status in a database or cache.
    """
    return AnalysisStatus(
        video_id=video_id,
        status="unknown",
        error_message="Status tracking not implemented"
    )


@router.get("/supported-features")
def get_supported_features():
    """
    Get list of supported analysis features
    """
    return {
        "features": [
            "conversation",
            "visual", 
            "text_in_video",
            "action",
            "concept"
        ],
        "description": "Available features for video analysis using Twelve Labs API"
    }


@router.get("/supported-formats")
def get_supported_formats():
    """
    Get list of supported video formats
    """
    return {
        "formats": list(resolver.supported_video_extensions),
        "max_file_size": "100MB",
        "description": "Supported video formats for file upload analysis"
    }




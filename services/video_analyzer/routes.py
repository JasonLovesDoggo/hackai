import os
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from .models import VideoAnalysisRequest, VideoAnalysisResult
from .analyzer import VideoAnalyzer

router = APIRouter(prefix="/video-analysis", tags=["Video Analysis"])


@router.post("/analyze", response_model=VideoAnalysisResult)
async def analyze_video(
    file: UploadFile = File(...),
    features: str = Form("gist,summary,analysis"),  # Default features
):
    """
    Analyze a video file using Twelve Labs API and return comprehensive results including:
    - Titles, topics, and hashtags (gist)
    - Video summaries
    - Chapter breakdowns
    - Highlights and key moments
    - Open-ended analysis with insights
    - Target audience and content type
    - Sentiment analysis
    """
    # Validate file type
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="File must be a video")

    # Parse features
    feature_list = [f.strip() for f in features.split(",")]
    request = VideoAnalysisRequest(features=feature_list)

    # Create temporary file
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=f".{file.filename.split('.')[-1]}"
    ) as temp_file:
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


@router.get("/features")
async def get_available_features():
    """Get available analysis features based on Twelve Labs SDK"""
    return {
        "available_features": {
            "gist": {
                "description": "Generate titles, topics, and hashtags",
                "types": ["title", "topic", "hashtag"],
            },
            "summary": {
                "description": "Generate comprehensive video summaries",
                "type": "summary",
            },
            "chapters": {
                "description": "Break down video into logical chapters with titles and summaries",
                "type": "chapter",
            },
            "highlights": {
                "description": "Identify key moments and highlights in the video",
                "type": "highlight",
            },
            "analysis": {
                "description": "Open-ended analysis with custom prompts for comprehensive insights",
                "type": "analysis",
            },
            "frames": {
                "description": "Frame-by-frame analysis with customizable time intervals (1-60 seconds)",
                "type": "frame_analysis",
                "endpoint": "/api/video-analysis/analyze-frames",
            },
            "visual": {
                "description": "Visual object detection and scene analysis",
                "type": "visual_analysis",
            },
        },
        "usage": "Specify features as comma-separated values (e.g., 'gist,summary,analysis')",
        "default": "gist,summary,analysis",
        "frame_analysis": {
            "description": "For detailed frame-by-frame analysis, use the /analyze-frames endpoint",
            "parameters": {
                "interval_seconds": "Time interval in seconds (1-60) for frame breakdown"
            },
            "example": "POST /api/video-analysis/analyze-frames with interval_seconds=5",
        },
    }


@router.get("/supported-formats")
async def get_supported_formats():
    """Get supported video formats and requirements"""
    return {
        "supported_formats": ["MP4", "AVI", "MOV", "WMV", "FLV", "WebM", "MKV"],
        "requirements": {
            "resolution": "Between 360x360 and 3840x2160",
            "duration": "Between 10 seconds and 2 hours (7200 seconds)",
            "aspect_ratio": "Between 1:1 and 16:9",
            "file_size": "Less than 4GB (varies by plan)",
        },
        "error_codes": {
            "video_resolution_too_low": "Resolution below 360x360",
            "video_resolution_too_high": "Resolution above 3840x2160",
            "video_duration_too_short": "Duration less than 10 seconds",
            "video_duration_too_long": "Duration more than 2 hours",
            "video_file_broken": "Invalid or corrupted video file",
            "usage_limit_exceeded": "API quota exceeded",
        },
    }





# cool stuff below !!

@router.post("/upload")
async def upload_video_only(file: UploadFile = File(...)):
    """
    Upload a video file to Twelve Labs without analysis.
    Returns video_id for later analysis.
    """
    # Validate file type
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="File must be a video")

    # Create temporary file
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=f".{file.filename.split('.')[-1]}"
    ) as temp_file:
        try:
            # Write uploaded file to temporary file
            content = await file.read()
            temp_file.write(content)
            temp_file.flush()

            # Upload the video
            from .api_client import TwelveLabsAPIClient

            client = TwelveLabsAPIClient()
            result = client.upload_video(temp_file.name)

            return {
                "message": "Video uploaded successfully",
                "video_id": result["video_id"],
                "task_id": result["task_id"],
                "status": result["status"],
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file.name)
            except:
                pass


@router.post("/analyze/{video_id}")
async def analyze_existing_video(
    video_id: str, features: str = Form("gist,summary,analysis")
):
    """
    Analyze an already uploaded video by video_id
    """
    try:
        # Parse features
        feature_list = [f.strip() for f in features.split(",")]

        # Analyze the video
        from .api_client import TwelveLabsAPIClient

        client = TwelveLabsAPIClient()
        result = client.analyze_video(video_id, feature_list)

        return {"video_id": video_id, "analysis": result, "status": "completed"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

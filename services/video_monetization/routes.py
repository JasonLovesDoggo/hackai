import os
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import Optional
from .models import VideoMonetizationResult
from .analyzer import video_monetization_analyzer

router = APIRouter(prefix="/video-monetization", tags=["Video Monetization"])


@router.post("/analyze", response_model=VideoMonetizationResult)
async def start_video_monetization_analysis(
    file: UploadFile = File(...),
    youtube_channel_url: Optional[str] = Form(None),
    amazon_affiliate_code: Optional[str] = Form(None),
):
    """
    Start comprehensive video monetization analysis workflow.

    Flow:
    1. Upload and analyze video content
    2. Extract product keywords from analysis
    3. Generate affiliate links for products
    4. Fetch YouTube channel context (if URL provided)
    5. Generate AI-powered monetization strategies

    Returns task ID for status tracking.
    """
    # Validate file type
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="File must be a video")

    # Create temporary file (don't delete immediately)
    temp_file = tempfile.NamedTemporaryFile(
        delete=False, suffix=f".{file.filename.split('.')[-1]}"
    )
    try:
        # Write uploaded file to temporary file
        content = await file.read()
        temp_file.write(content)
        temp_file.flush()
        temp_file.close()  # Close file handle but keep file

        # Start analysis workflow (background task will handle cleanup)
        task_id = await video_monetization_analyzer.start_analysis(
            temp_file.name, youtube_channel_url, amazon_affiliate_code
        )

        # Get the task status immediately
        task_status = video_monetization_analyzer.get_task_status(task_id)
        return task_status

    except Exception as e:
        # Clean up on error
        try:
            os.unlink(temp_file.name)
        except:
            pass
        raise HTTPException(
            status_code=500, detail=f"Analysis startup failed: {str(e)}"
        )


@router.get("/status/{task_id}", response_model=VideoMonetizationResult)
async def get_analysis_status(task_id: str):
    """
    Get current status and results of video monetization analysis.

    Status values:
    - "pending": Analysis queued but not started
    - "processing": Analysis in progress
    - "completed": Analysis finished successfully
    - "failed": Analysis encountered an error

    Example completed response:
    {
        "task_id": "abc123-def456",
        "status": "completed",
        "video_analysis": {
            "task_id": "abc123",
            "context": {
                "content_summary": "Video shows tech gadgets including Logitech mouse, Celsius drink...",
                "target_audience": "tech enthusiasts"
            }
        },
        "products": [
            {
                "product_name": "Logitech MX Master 3s Mouse",
                "product_url": "https://www.amazon.com/dp/B0CX23PHFD",
                "affiliate_url": "https://www.amazon.com/dp/B0CX23PHFD?tag=yourcode-20",
                "platform": "amazon",
                "price": "$99.99",
                "timestamp": "0s-5s"
            },
            {
                "product_name": "Celsius Energy Drink",
                "product_url": "https://www.amazon.com/dp/B0D2R5DR1M",
                "affiliate_url": "https://www.amazon.com/dp/B0D2R5DR1M?tag=yourcode-20",
                "platform": "amazon",
                "price": "$24.99",
                "timestamp": "5s-13s"
            }
        ],
        "product_keywords": ["Logitech MX Master 3s mouse", "Celsius energy drink"],
        "monetization_strategies": [
            {
                "strategy_type": "course",
                "title": "Complete Tech Setup Guide",
                "description": "Create a course teaching optimal workspace setup",
                "implementation_steps": ["Plan curriculum", "Record videos", "Launch on platform"],
                "estimated_effort": "high",
                "estimated_timeline": "2-3 months",
                "potential_revenue": "high"
            }
        ],
        "channel_context": {
            "channel": {"subscribers": 245000, "name": "TechReviewer"}
        },
        "created_at": "2025-06-22T10:30:00",
        "completed_at": "2025-06-22T10:35:00",
        "timestamps": {
            "started": "2025-06-22T10:30:00",
            "video_analysis_completed": "2025-06-22T10:32:00",
            "affiliate_links_generated": "2025-06-22T10:34:00",
            "strategies_generated": "2025-06-22T10:35:00"
        }
    }
    """
    result = video_monetization_analyzer.get_task_status(task_id)

    if not result:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    return result


@router.get("/tasks")
async def list_all_tasks():
    """
    List all tasks (for debugging/admin purposes).
    In production, this should be protected or removed.
    """
    tasks = video_monetization_analyzer.list_tasks()

    # Return summary of tasks
    task_summaries = {}
    for task_id, task in tasks.items():
        task_summaries[task_id] = {
            "task_id": task.task_id,
            "status": task.status,
            "created_at": task.created_at,
            "completed_at": task.completed_at,
            "has_video_analysis": bool(task.video_analysis),
            "product_count": len(task.products),
            "strategy_count": len(task.monetization_strategies),
            "has_channel_context": bool(task.channel_context),
            "error_message": task.error_message,
        }

    return {"total_tasks": len(tasks), "tasks": task_summaries}


@router.get("/workflow-info")
async def get_workflow_info():
    """
    Get information about the video monetization analysis workflow.
    """
    return {
        "workflow_steps": [
            {
                "step": 1,
                "name": "Video Analysis",
                "description": "Analyze video content using Twelve Labs API for visual objects, transcription, and insights",
                "outputs": [
                    "video_metadata",
                    "transcript",
                    "visual_analysis",
                    "context",
                ],
            },
            {
                "step": 2,
                "name": "Product Extraction",
                "description": "Extract product keywords from video analysis using regex pattern matching",
                "outputs": ["product_keywords"],
            },
            {
                "step": 3,
                "name": "Affiliate Link Generation",
                "description": "Generate affiliate links for extracted products using real web scraping",
                "outputs": ["products", "affiliate_links"],
            },
            {
                "step": 4,
                "name": "Channel Context (Optional)",
                "description": "Fetch YouTube channel health data if channel URL provided",
                "outputs": ["channel_context", "subscriber_count", "content_type"],
            },
            {
                "step": 5,
                "name": "Monetization Strategy Generation",
                "description": "Generate AI-powered monetization strategies using GROQ based on content analysis",
                "outputs": [
                    "monetization_strategies",
                    "implementation_steps",
                    "revenue_estimates",
                ],
            },
        ],
        "supported_file_formats": ["MP4", "AVI", "MOV", "WMV", "FLV", "WebM", "MKV"],
        "example_strategies": [
            "Course creation based on video content",
            "Sponsorship opportunities matching content type",
            "Affiliate marketing for featured products",
            "Merchandise creation",
            "Coaching/consulting services",
            "YouTube memberships and Patreon",
            "Live events and workshops",
        ],
        "affiliate_platforms": [
            "Amazon",
            "eBay",
            "Walmart",
            "Target",
            "ShareASale",
            "CJ Affiliate",
            "ClickBank",
        ],
    }

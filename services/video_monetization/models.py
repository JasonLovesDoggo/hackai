from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class VideoMonetizationRequest(BaseModel):
    """Request model for video monetization analysis workflow"""

    youtube_channel_url: Optional[str] = (
        None  # Optional YouTube channel URL for additional context
    )
    amazon_affiliate_code: Optional[str] = (
        None  # Amazon affiliate code for product links
    )


class ProductLink(BaseModel):
    """Product link with affiliate information"""

    product_name: str
    product_url: str
    affiliate_url: str
    platform: str
    price: Optional[str] = None
    rating: Optional[float] = None
    image_url: Optional[str] = None
    availability: Optional[str] = None
    timestamp: Optional[str] = (
        None  # Video timestamp when product appears (e.g., "0s-5s")
    )


class MonetizationStrategy(BaseModel):
    """AI-generated monetization strategy"""

    strategy_type: str  # e.g., "course", "sponsorship", "affiliate", "merchandise"
    title: str
    description: str
    why_this_works: (
        str  # Detailed explanation of why this strategy is perfect for this creator
    )
    implementation_steps: List[str]
    estimated_effort: str  # e.g., "low", "medium", "high"
    estimated_timeline: str  # e.g., "1-2 weeks", "1-3 months"
    potential_revenue: str  # e.g., "low", "medium", "high"


class VideoMonetizationResult(BaseModel):
    """Complete video monetization analysis result"""

    task_id: str
    status: str  # "pending", "processing", "completed", "failed"

    # Video analysis data
    video_analysis: Optional[Dict[str, Any]] = None

    # Product recommendations
    products: List[ProductLink] = []
    product_keywords: List[str] = []

    # Monetization strategies
    monetization_strategies: List[MonetizationStrategy] = []

    # YouTube channel context (if provided)
    channel_context: Optional[Dict[str, Any]] = None

    # Metadata
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    # Processing timestamps for tracking
    timestamps: Dict[str, datetime] = {}

    def dict(self, **kwargs):
        """Custom dict method to filter out internal analysis from end user response"""
        data = super().dict(**kwargs)

        # Remove internal analysis from video_analysis if present
        if data.get("video_analysis") and isinstance(data["video_analysis"], dict):
            video_analysis = data["video_analysis"].copy()
            # Remove internal analysis field - users don't need to see this
            if "_internal_analysis" in video_analysis:
                del video_analysis["_internal_analysis"]
            data["video_analysis"] = video_analysis

        return data

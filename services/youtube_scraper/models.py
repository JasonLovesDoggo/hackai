from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class VideoInfo(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    tags: List[str] = []
    view_count: int = 0
    like_count: Optional[int] = None
    comment_count: Optional[int] = None
    duration: Optional[int] = None
    upload_date: Optional[datetime] = None
    thumbnail_url: Optional[str] = None


class ChannelInfo(BaseModel):
    id: str
    name: str
    handle: Optional[str] = None
    description: Optional[str] = None
    subscriber_count: Optional[int] = None
    video_count: Optional[int] = None
    view_count: Optional[int] = None
    profile_picture_url: Optional[str] = None
    banner_url: Optional[str] = None
    keywords: List[str] = []
    videos: List[VideoInfo] = []


class VideoMetrics(BaseModel):
    views: int
    likes: int
    comments: int
    duration: str
    engagement_rate: float


class VideoPerformance(BaseModel):
    view_tier: str
    has_good_engagement: bool
    comment_ratio: float


class TitleAnalysis(BaseModel):
    length: int
    word_count: int
    has_numbers: bool
    has_caps: bool
    has_question: bool
    has_exclamation: bool
    clickbait_indicators: List[str]
    seo_score: int


class MonetizationSpots(BaseModel):
    product_placement: List[str]
    affiliate_potential: List[str]
    sponsorship_segments: List[str]
    course_material: bool


class VideoAnalysisDetailed(BaseModel):
    rank: str
    title: str
    video_id: str
    upload_date: str
    metrics: VideoMetrics
    performance: VideoPerformance
    title_analysis: TitleAnalysis
    tags: List[str]
    monetization_spots: MonetizationSpots


class VideoInsights(BaseModel):
    performance_trend: Optional[Dict[str, Any]] = None
    title_optimization: Optional[Dict[str, Any]] = None
    content_consistency: Optional[Dict[str, Any]] = None


class VideoAnalysis(BaseModel):
    recent_top_5: List[VideoAnalysisDetailed]
    most_popular_5: List[VideoAnalysisDetailed]
    insights: VideoInsights


class PerformanceMetrics(BaseModel):
    tier: str
    avg_views: int
    max_views: int
    min_views: int
    engagement_rate: float
    avg_duration: str
    total_videos_analyzed: int


class RecentContent(BaseModel):
    video_titles: List[str]
    upload_dates: List[str]
    title_themes: List[str]
    common_tags: List[str]


class CreatorInsights(BaseModel):
    uses_tags_effectively: bool
    title_consistency: bool
    description_quality: str
    content_focus: str
    upload_consistency: bool
    audience_engagement: str


class MonetizationIndicators(BaseModel):
    subscriber_milestone: str
    content_suitable_for_ads: bool
    brand_partnership_ready: bool
    merch_potential: bool
    course_creation_potential: bool


class MonetizationAdvantage(BaseModel):
    niche_value: str
    cpm_potential: str
    affiliate_potential: str
    course_potential: str
    specificity_bonus: str
    audience_targeting: str


class NicheAnalysis(BaseModel):
    specificity_score: float
    niche_type: str
    focus_level: str
    category_diversity: float
    total_categories: int
    cross_niche_patterns: List[str]
    monetization_advantage: MonetizationAdvantage


class ContentAnalysis(BaseModel):
    content_type: str
    secondary_categories: List[str]
    content_categories: Dict[str, int]
    niche_analysis: NicheAnalysis
    upload_style: str
    video_style: str
    performance_metrics: PerformanceMetrics
    recent_content: RecentContent
    creator_insights: CreatorInsights
    monetization_indicators: MonetizationIndicators


class HealthAnalysis(BaseModel):
    health_score: int
    health_rating: str
    monetization_ready: bool


class ChannelBasicInfo(BaseModel):
    id: str
    name: str
    handle: Optional[str]
    description: Optional[str]
    subscribers: Optional[int]
    total_videos: Optional[int]
    view_count: Optional[int]


class ChannelHealthResponse(BaseModel):
    channel: ChannelBasicInfo
    content_analysis: ContentAnalysis
    health_analysis: HealthAnalysis
    video_analysis: VideoAnalysis


class ScrapeRequest(BaseModel):
    channel_id: str
    max_videos: int = 50
    include_video_details: bool = True

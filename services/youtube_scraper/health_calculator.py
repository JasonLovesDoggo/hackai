"""
Health Calculator Module - Specialized for channel health scoring and assessment
"""
import logging
from typing import Dict
from .models import ChannelInfo

logger = logging.getLogger('uvicorn.error')


class HealthCalculator:
    def __init__(self):
        pass

    def calculate_health_score(self, channel: ChannelInfo) -> Dict:
        """Calculate comprehensive channel health score"""
        health_score = 0
        
        # Subscriber health (40 points max)
        sub_score = self._analyze_subscriber_health(channel.subscriber_count or 0)
        health_score += sub_score
        
        # Video count and consistency (30 points max)
        consistency_score = self._analyze_content_consistency(channel.videos)
        health_score += consistency_score
        
        # Engagement health (30 points max)
        engagement_score = self._analyze_engagement_health(channel.videos)
        health_score += engagement_score
        
        # Overall health rating
        health_rating = self._get_health_rating(health_score)
        
        # Monetization readiness
        monetization_ready = self._assess_basic_monetization_readiness(
            channel.subscriber_count or 0, 
            len(channel.videos)
        )
        
        return {
            "health_score": health_score,
            "health_rating": health_rating,
            "monetization_ready": monetization_ready
        }

    def _analyze_subscriber_health(self, sub_count: int) -> int:
        """Analyze subscriber count health (0-40 points)"""
        if sub_count >= 1000000:
            return 40  # Mega creator
        elif sub_count >= 100000:
            return 35  # Established creator
        elif sub_count >= 10000:
            return 30  # Growing creator
        elif sub_count >= 1000:
            return 25  # Monetization eligible
        elif sub_count >= 100:
            return 15  # Emerging creator
        else:
            return 5   # Starting out

    def _analyze_content_consistency(self, videos: list) -> int:
        """Analyze content consistency and volume (0-30 points)"""
        video_count = len(videos)
        
        if video_count >= 100:
            return 30  # Excellent content volume
        elif video_count >= 50:
            return 25  # Good content volume
        elif video_count >= 20:
            return 20  # Decent content volume
        elif video_count >= 10:
            return 15  # Basic content volume
        elif video_count >= 5:
            return 10  # Limited content
        else:
            return 5   # Very limited content

    def _analyze_engagement_health(self, videos: list) -> int:
        """Analyze engagement health (0-30 points)"""
        if not videos:
            return 0
        
        # Calculate average engagement rate
        total_views = sum(v.view_count for v in videos if v.view_count)
        total_likes = sum(v.like_count for v in videos if v.like_count)
        
        if total_views == 0:
            return 0
        
        engagement_rate = (total_likes / total_views) * 100
        
        if engagement_rate >= 5:
            return 30  # Excellent engagement
        elif engagement_rate >= 3:
            return 25  # Very good engagement
        elif engagement_rate >= 2:
            return 20  # Good engagement
        elif engagement_rate >= 1:
            return 15  # Fair engagement
        else:
            return 5   # Poor engagement

    def _get_health_rating(self, health_score: int) -> str:
        """Convert health score to rating"""
        if health_score >= 85:
            return "Excellent"
        elif health_score >= 70:
            return "Very Good"
        elif health_score >= 55:
            return "Good"
        elif health_score >= 40:
            return "Fair"
        elif health_score >= 25:
            return "Poor"
        else:
            return "Critical"

    def _assess_basic_monetization_readiness(self, sub_count: int, video_count: int) -> bool:
        """Basic monetization readiness assessment"""
        return sub_count >= 1000 and video_count >= 10
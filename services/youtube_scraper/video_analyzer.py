"""
Video Analysis Module - Specialized for individual video analysis and monetization opportunities
"""

import logging
from typing import Dict, List, Optional
from .models import VideoInfo

logger = logging.getLogger("uvicorn.error")


class VideoAnalyzer:
    def __init__(self):
        pass

    def analyze_top_videos(self, videos: List[VideoInfo]) -> Dict:
        """Analyze top 5 recent videos and top 5 most popular videos"""
        if not videos:
            return {"recent_top_5": [], "most_popular_5": [], "insights": {}}

        # Sort videos
        recent_videos = sorted(
            [v for v in videos if v.upload_date],
            key=lambda x: x.upload_date,
            reverse=True,
        )[:5]
        popular_videos = sorted(
            [v for v in videos if v.view_count],
            key=lambda x: x.view_count,
            reverse=True,
        )[:5]

        # Analyze each video set
        recent_analysis = [
            self._analyze_single_video(video, f"Recent #{i}")
            for i, video in enumerate(recent_videos, 1)
        ]
        popular_analysis = [
            self._analyze_single_video(video, f"Popular #{i}")
            for i, video in enumerate(popular_videos, 1)
        ]

        # Generate comparative insights
        insights = self._generate_video_insights(recent_videos, popular_videos)

        return {
            "recent_top_5": recent_analysis,
            "most_popular_5": popular_analysis,
            "insights": insights,
        }

    def _analyze_single_video(self, video: VideoInfo, rank: str) -> Dict:
        """Perform detailed analysis of a single video"""
        # Calculate engagement metrics
        engagement_rate = 0
        if video.view_count and video.view_count > 0 and video.like_count:
            engagement_rate = (video.like_count / video.view_count) * 100

        # Format duration
        duration_formatted = self._format_duration(video.duration)

        # Analyze title characteristics
        title_analysis = self._analyze_title_characteristics(video.title)

        # Performance classification
        view_performance = self._classify_view_performance(video.view_count)

        return {
            "rank": rank,
            "title": video.title,
            "video_id": video.id,
            "upload_date": video.upload_date.strftime("%Y-%m-%d")
            if video.upload_date
            else "unknown",
            "metrics": {
                "views": video.view_count or 0,
                "likes": video.like_count or 0,
                "comments": video.comment_count or 0,
                "duration": duration_formatted,
                "engagement_rate": round(engagement_rate, 2),
            },
            "performance": {
                "view_tier": view_performance,
                "has_good_engagement": engagement_rate > 2,
                "comment_ratio": round(
                    (video.comment_count or 0) / max(video.view_count or 1, 1) * 1000, 2
                ),
            },
            "title_analysis": title_analysis,
            "tags": video.tags[:8] if video.tags else [],
            "monetization_spots": self._identify_monetization_opportunities(video),
        }

    def _format_duration(self, duration: Optional[int]) -> str:
        """Format video duration"""
        if not duration:
            return "unknown"

        mins = duration // 60
        secs = duration % 60
        return f"{mins}m {secs}s"

    def _classify_view_performance(self, view_count: Optional[int]) -> str:
        """Classify video performance based on view count"""
        if not view_count:
            return "low"

        if view_count >= 1000000:
            return "viral"
        elif view_count >= 100000:
            return "high"
        elif view_count >= 10000:
            return "medium"
        else:
            return "low"

    def _analyze_title_characteristics(self, title: str) -> Dict:
        """Analyze title for SEO and engagement characteristics"""
        if not title:
            return {}

        return {
            "length": len(title),
            "word_count": len(title.split()),
            "has_numbers": any(c.isdigit() for c in title),
            "has_caps": any(c.isupper() for c in title),
            "has_question": "?" in title,
            "has_exclamation": "!" in title,
            "clickbait_indicators": self._detect_clickbait_elements(title),
            "seo_score": self._calculate_title_seo_score(title),
        }

    def _detect_clickbait_elements(self, title: str) -> List[str]:
        """Detect potential clickbait elements in title"""
        clickbait_words = [
            "amazing",
            "shocking",
            "unbelievable",
            "incredible",
            "insane",
            "crazy",
            "secret",
            "hidden",
            "exposed",
            "revealed",
            "truth",
            "you won't believe",
            "must see",
            "gone wrong",
            "epic fail",
        ]

        title_lower = title.lower()
        found_elements = []

        for word in clickbait_words:
            if word in title_lower:
                found_elements.append(word)

        # Check for excessive punctuation
        if title.count("!") > 1:
            found_elements.append("excessive_exclamation")
        if title.count("?") > 1:
            found_elements.append("excessive_questions")

        return found_elements

    def _calculate_title_seo_score(self, title: str) -> int:
        """Calculate SEO score for video title (0-100)"""
        score = 50  # Base score

        # Length optimization (40-60 chars is ideal)
        if 40 <= len(title) <= 60:
            score += 20
        elif 30 <= len(title) <= 70:
            score += 10
        else:
            score -= 10

        # Word count (5-10 words is good)
        word_count = len(title.split())
        if 5 <= word_count <= 10:
            score += 15
        elif 3 <= word_count <= 12:
            score += 5

        # Has numbers (good for tutorials/lists)
        if any(c.isdigit() for c in title):
            score += 10

        # Capitalization (title case is good)
        if title.istitle():
            score += 5

        return min(100, max(0, score))

    def _identify_monetization_opportunities(self, video: VideoInfo) -> Dict:
        """Identify monetization opportunities in video content"""
        opportunities = {
            "product_placement": [],
            "affiliate_potential": [],
            "sponsorship_segments": [],
            "course_material": False,
        }

        title_lower = video.title.lower()
        description_lower = (video.description or "").lower()
        all_text = f"{title_lower} {description_lower}"

        # Product placement opportunities
        product_keywords = [
            "review",
            "unboxing",
            "setup",
            "tutorial",
            "guide",
            "comparison",
            "vs",
        ]
        for keyword in product_keywords:
            if keyword in all_text:
                opportunities["product_placement"].append(keyword)

        # Affiliate marketing potential
        affiliate_keywords = [
            "best",
            "top",
            "recommend",
            "gear",
            "equipment",
            "tools",
            "software",
            "app",
        ]
        for keyword in affiliate_keywords:
            if keyword in all_text:
                opportunities["affiliate_potential"].append(keyword)

        # Sponsorship segments
        sponsor_keywords = ["intro", "tutorial", "educational", "how-to", "explanation"]
        for keyword in sponsor_keywords:
            if keyword in all_text:
                opportunities["sponsorship_segments"].append(keyword)

        # Course creation potential
        course_keywords = [
            "tutorial",
            "learn",
            "course",
            "lesson",
            "training",
            "guide",
            "step by step",
        ]
        opportunities["course_material"] = any(
            keyword in all_text for keyword in course_keywords
        )

        return opportunities

    def _generate_video_insights(
        self, recent_videos: List[VideoInfo], popular_videos: List[VideoInfo]
    ) -> Dict:
        """Generate insights comparing recent vs popular videos"""
        if not recent_videos and not popular_videos:
            return {}

        insights = {}

        # Performance comparison
        if recent_videos and popular_videos:
            recent_avg_views = sum(v.view_count or 0 for v in recent_videos) / len(
                recent_videos
            )
            popular_avg_views = sum(v.view_count or 0 for v in popular_videos) / len(
                popular_videos
            )

            insights["performance_trend"] = {
                "recent_avg_views": int(recent_avg_views),
                "popular_avg_views": int(popular_avg_views),
                "trend": "improving"
                if recent_avg_views > popular_avg_views * 0.7
                else "declining",
            }

        # Title optimization analysis
        if recent_videos:
            recent_title_lengths = [len(v.title) for v in recent_videos]
            insights["title_optimization"] = {
                "avg_title_length": sum(recent_title_lengths)
                / len(recent_title_lengths),
                "optimal_range": all(
                    40 <= length <= 60 for length in recent_title_lengths
                ),
            }

        # Content consistency analysis
        all_videos = recent_videos + popular_videos
        if all_videos:
            durations = [v.duration for v in all_videos if v.duration]
            if durations:
                avg_duration = sum(durations) / len(durations)
                insights["content_consistency"] = {
                    "avg_video_length": f"{int(avg_duration // 60)}m {int(avg_duration % 60)}s",
                    "consistent_length": max(durations) - min(durations)
                    < 300,  # Within 5 minutes
                }

        return insights

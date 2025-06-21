from typing import Optional
import logging
from .models import ChannelInfo
from .resolver import YouTubeURLResolver
from .youtube_api import YouTubeAPIClient

logger = logging.getLogger('uvicorn.error')


class YouTubeScraper:
    def __init__(self):
        self.resolver = YouTubeURLResolver()
        self.api_client = YouTubeAPIClient()

    async def get_channel_health(self, channel_input: str) -> dict:
        """Get channel health analysis and content type"""
        # Only use YouTube Data API - fast and reliable
        if not self.api_client.api_key:
            logger.error("YouTube API key not found")
            return {
                "error": "YouTube API key required. Set YOUTUBE_API_KEY environment variable."
            }

        try:
            logger.info(f"Analyzing channel: {channel_input}")
            
            # Resolve channel input to channel ID
            if channel_input.startswith("https://www.youtube.com/@"):
                # Strip URL to just handle
                handle = channel_input.replace("https://www.youtube.com/", "")
                logger.info(f"Extracted handle from URL: {handle}")
                async with self.api_client as api:
                    channel_id = await api.get_channel_by_handle(handle)
            elif channel_input.startswith("@"):
                logger.info(f"Using handle directly: {channel_input}")
                async with self.api_client as api:
                    channel_id = await api.get_channel_by_handle(channel_input)
            elif channel_input.startswith("UC") and len(channel_input) == 24:
                logger.info(f"Using direct channel ID: {channel_input}")
                channel_id = channel_input
            else:
                logger.info(f"Using resolver for: {channel_input}")
                channel_id = self.resolver.resolve_to_channel_id(channel_input)

            logger.info(f"Resolved channel ID: {channel_id}")
            
            if not channel_id:
                logger.error(f"Could not resolve channel: {channel_input}")
                return {"error": f"Could not resolve channel: {channel_input}"}

            # Get channel data via API
            async with self.api_client as api:
                channel_info = await api.get_channel_info(channel_id, 20)

            if not channel_info:
                logger.error(f"Channel data not found: {channel_id}")
                return {"error": f"Channel data not found: {channel_id}"}

            logger.info(f"Successfully got channel data for: {channel_info.name}")

            # Simple health analysis
            health_analysis = self._analyze_basic_health(channel_info)
            
            return {
                "channel": {
                    "id": channel_info.id,
                    "name": channel_info.name,
                    "handle": channel_info.handle,
                    "subscribers": channel_info.subscriber_count,
                    "total_videos": channel_info.video_count
                },
                "health_analysis": health_analysis
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze channel: {str(e)}")
            return {"error": f"Failed to analyze channel: {str(e)}"}

    def _analyze_basic_health(self, channel: ChannelInfo) -> dict:
        """Basic health analysis without complex analyzer"""
        subs = channel.subscriber_count or 0
        video_count = len(channel.videos)
        
        # Simple health score
        health_score = 0
        if subs >= 1000:
            health_score += 40
        elif subs >= 100:
            health_score += 20
        
        if video_count >= 10:
            health_score += 30
        elif video_count >= 5:
            health_score += 20
        
        if channel.videos:
            avg_views = sum(v.view_count for v in channel.videos if v.view_count) // len(channel.videos)
            if avg_views >= 1000:
                health_score += 30
            elif avg_views >= 100:
                health_score += 20
        
        # Health rating
        if health_score >= 80:
            rating = "Excellent"
        elif health_score >= 60:
            rating = "Good"
        elif health_score >= 40:
            rating = "Fair"
        else:
            rating = "Poor"
        
        return {
            "health_score": health_score,
            "health_rating": rating,
            "subscriber_count": subs,
            "video_count": video_count,
            "monetization_ready": subs >= 1000 and video_count > 0
        }
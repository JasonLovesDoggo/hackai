import logging
from typing import Dict
from .resolver import YouTubeURLResolver
from .youtube_api import YouTubeAPIClient
from .content_analyzer import ContentAnalyzer
from .video_analyzer import VideoAnalyzer
from .health_calculator import HealthCalculator

logger = logging.getLogger("uvicorn.error")


class YouTubeScraper:
    def __init__(self):
        self.resolver = YouTubeURLResolver()
        self.api_client = YouTubeAPIClient()
        self.content_analyzer = ContentAnalyzer()
        self.video_analyzer = VideoAnalyzer()
        self.health_calculator = HealthCalculator()

    async def get_channel_health(self, channel_input: str) -> Dict:
        """Get comprehensive channel health analysis and content insights"""
        # Validate API key
        if not self.api_client.api_key:
            logger.error("YouTube API key not found")
            return {
                "error": "YouTube API key required. Set YOUTUBE_API_KEY environment variable."
            }

        try:
            logger.info(f"Analyzing channel: {channel_input}")

            # Resolve channel input to channel ID
            channel_id = await self._resolve_channel_input(channel_input)
            if not channel_id:
                logger.error(f"Could not resolve channel: {channel_input}")
                return {"error": f"Could not resolve channel: {channel_input}"}

            logger.info(f"Resolved channel ID: {channel_id}")

            # Get channel data via API
            channel_info = await self.api_client.get_channel_info(channel_id, 20)
            if not channel_info:
                logger.error(f"Channel data not found: {channel_id}")
                return {"error": f"Channel data not found: {channel_id}"}

            logger.info(f"Successfully got channel data for: {channel_info.name}")

            # Perform specialized analysis using dedicated modules
            content_analysis = self.content_analyzer.analyze_content_style(channel_info)
            health_analysis = self.health_calculator.calculate_health_score(
                channel_info
            )
            video_analysis = self.video_analyzer.analyze_top_videos(channel_info.videos)

            # Build comprehensive response
            return {
                "channel": {
                    "id": channel_info.id,
                    "name": channel_info.name,
                    "handle": channel_info.handle,
                    "description": channel_info.description,
                    "subscribers": channel_info.subscriber_count,
                    "total_videos": channel_info.video_count,
                    "view_count": channel_info.view_count,
                },
                "content_analysis": content_analysis,
                "health_analysis": health_analysis,
                "video_analysis": video_analysis,
            }

        except Exception as e:
            logger.error(f"Failed to analyze channel: {str(e)}")
            return {"error": f"Failed to analyze channel: {str(e)}"}

    async def _resolve_channel_input(self, channel_input: str) -> str:
        """Resolve various channel input formats to channel ID"""
        if channel_input.startswith("https://www.youtube.com/@"):
            # Strip URL to just handle
            handle = channel_input.replace("https://www.youtube.com/", "")
            logger.info(f"Extracted handle from URL: {handle}")
            return await self.api_client.get_channel_by_handle(handle)

        elif channel_input.startswith("@"):
            logger.info(f"Using handle directly: {channel_input}")
            return await self.api_client.get_channel_by_handle(channel_input)

        elif channel_input.startswith("UC") and len(channel_input) == 24:
            logger.info(f"Using direct channel ID: {channel_input}")
            return channel_input

        else:
            logger.info(f"Using resolver for: {channel_input}")
            return self.resolver.resolve_to_channel_id(channel_input)

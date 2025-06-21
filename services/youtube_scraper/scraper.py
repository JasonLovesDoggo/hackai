import logging
from .models import ChannelInfo
from .resolver import YouTubeURLResolver
from .youtube_api import YouTubeAPIClient

logger = logging.getLogger("uvicorn.error")


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
                channel_id = await self.api_client.get_channel_by_handle(handle)
            elif channel_input.startswith("@"):
                logger.info(f"Using handle directly: {channel_input}")
                channel_id = await self.api_client.get_channel_by_handle(channel_input)
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
            channel_info = await self.api_client.get_channel_info(channel_id, 20)

            if not channel_info:
                logger.error(f"Channel data not found: {channel_id}")
                return {"error": f"Channel data not found: {channel_id}"}

            logger.info(f"Successfully got channel data for: {channel_info.name}")

            # Analyze channel content and style
            content_analysis = self._analyze_content_style(channel_info)
            health_analysis = self._analyze_basic_health(channel_info)

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
            avg_views = sum(
                v.view_count for v in channel.videos if v.view_count
            ) // len(channel.videos)
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
            "monetization_ready": subs >= 1000 and video_count > 0,
        }

    def _analyze_content_style(self, channel: ChannelInfo) -> dict:
        """Analyze content style, topics, and creator focus"""
        if not channel.videos:
            return {
                "content_type": "unknown",
                "style": "unknown", 
                "topics": [],
                "video_titles": [],
                "common_tags": []
            }

        # Get all video titles and tags
        titles = [v.title for v in channel.videos]
        all_tags = []
        for video in channel.videos:
            if video.tags:
                all_tags.extend(video.tags)

        # Count most common tags
        tag_counts = {}
        for tag in all_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # Get top 10 most common tags
        common_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        common_tags = [tag for tag, count in common_tags]

        # Analyze content type based on titles and tags
        content_categories = {
            'cybersecurity': ['security', 'hacking', 'cyber', 'penetration', 'vulnerability', 'malware', 'privacy', 'encryption'],
            'tech': ['programming', 'coding', 'software', 'tech', 'development', 'javascript', 'python', 'tutorial'],
            'gaming': ['gaming', 'gameplay', 'game', 'stream', 'minecraft', 'fortnite'],
            'lifestyle': ['vlog', 'daily', 'life', 'routine', 'travel', 'food'],
            'education': ['tutorial', 'learn', 'course', 'explained', 'how to', 'guide'],
            'entertainment': ['funny', 'comedy', 'react', 'reaction', 'meme', 'music'],
            'business': ['business', 'entrepreneur', 'startup', 'marketing', 'finance']
        }

        # Analyze all text content
        all_text = ' '.join(titles + all_tags + [channel.description or '']).lower()
        
        category_scores = {}
        for category, keywords in content_categories.items():
            score = sum(all_text.count(keyword) for keyword in keywords)
            if score > 0:
                category_scores[category] = score

        # Determine primary content type
        if category_scores:
            primary_category = max(category_scores, key=category_scores.get)
        else:
            primary_category = "general"

        # Analyze upload style/frequency
        recent_videos = [v for v in channel.videos if v.upload_date]
        if len(recent_videos) >= 2:
            # Calculate average days between uploads
            dates = sorted([v.upload_date for v in recent_videos], reverse=True)
            intervals = []
            for i in range(1, min(len(dates), 6)):  # Look at last 5 intervals
                interval = (dates[i-1] - dates[i]).days
                intervals.append(interval)
            
            if intervals:
                avg_interval = sum(intervals) / len(intervals)
                if avg_interval <= 2:
                    upload_style = "daily"
                elif avg_interval <= 7:
                    upload_style = "weekly"
                elif avg_interval <= 14:
                    upload_style = "bi-weekly"
                else:
                    upload_style = "monthly"
            else:
                upload_style = "irregular"
        else:
            upload_style = "insufficient_data"

        # Analyze video performance
        if channel.videos:
            avg_views = sum(v.view_count for v in channel.videos if v.view_count) // len(channel.videos)
            avg_likes = sum(v.like_count for v in channel.videos if v.like_count) // len([v for v in channel.videos if v.like_count])
            
            performance_tier = "low"
            if avg_views >= 100000:
                performance_tier = "viral"
            elif avg_views >= 10000:
                performance_tier = "high"
            elif avg_views >= 1000:
                performance_tier = "medium"
        else:
            performance_tier = "unknown"

        return {
            "content_type": primary_category,
            "content_categories": category_scores,
            "upload_style": upload_style,
            "performance_tier": performance_tier,
            "video_titles": titles[:5],  # Show first 5 titles
            "common_tags": common_tags,
            "total_unique_tags": len(set(all_tags)),
            "style_indicators": {
                "uses_tags": len(all_tags) > 0,
                "consistent_naming": self._check_title_consistency(titles),
                "description_length": len(channel.description or ""),
            }
        }

    def _check_title_consistency(self, titles: list) -> bool:
        """Check if video titles follow a consistent pattern"""
        if len(titles) < 3:
            return False
        
        # Check for common patterns like series numbering, consistent format
        patterns = []
        for title in titles:
            # Look for common patterns
            if any(char.isdigit() for char in title):
                patterns.append("numbered")
            if ":" in title:
                patterns.append("colon_format")
            if title.isupper():
                patterns.append("all_caps")
            if "|" in title:
                patterns.append("pipe_separator")
        
        # If more than 60% follow same pattern, consider it consistent
        if patterns:
            most_common = max(set(patterns), key=patterns.count)
            consistency = patterns.count(most_common) / len(titles)
            return consistency > 0.6
        
        return False

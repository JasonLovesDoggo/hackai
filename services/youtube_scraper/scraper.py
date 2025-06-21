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

        # Analyze video performance and engagement
        if channel.videos:
            views_list = [v.view_count for v in channel.videos if v.view_count]
            likes_list = [v.like_count for v in channel.videos if v.like_count]
            
            avg_views = sum(views_list) // len(views_list) if views_list else 0
            max_views = max(views_list) if views_list else 0
            min_views = min(views_list) if views_list else 0
            
            # Calculate engagement rate (likes/views)
            total_views = sum(views_list)
            total_likes = sum(likes_list)
            engagement_rate = (total_likes / total_views * 100) if total_views > 0 else 0
            
            performance_tier = "low"
            if avg_views >= 100000:
                performance_tier = "viral"
            elif avg_views >= 10000:
                performance_tier = "high"
            elif avg_views >= 1000:
                performance_tier = "medium"
        else:
            performance_tier = "unknown"
            avg_views = max_views = min_views = engagement_rate = 0

        # Analyze content themes from titles
        title_keywords = self._extract_title_themes(titles)
        
        # Analyze video durations if available
        durations = [v.duration for v in channel.videos if v.duration]
        avg_duration = sum(durations) // len(durations) if durations else 0
        
        # Format duration nicely
        if avg_duration > 0:
            duration_formatted = f"{avg_duration // 60}m {avg_duration % 60}s"
            if avg_duration < 60:
                video_style = "shorts"
            elif avg_duration < 600:  # 10 min
                video_style = "short_form"
            elif avg_duration < 1800:  # 30 min
                video_style = "medium_form"
            else:
                video_style = "long_form"
        else:
            duration_formatted = "unknown"
            video_style = "unknown"

        # Get recent upload dates
        upload_dates = [v.upload_date.strftime("%Y-%m-%d") for v in channel.videos if v.upload_date]
        
        # Analyze top performing videos
        top_videos_analysis = self._analyze_top_videos(channel.videos)
        
        return {
            "content_type": primary_category,
            "content_categories": category_scores,
            "upload_style": upload_style,
            "video_style": video_style,
            "performance_metrics": {
                "tier": performance_tier,
                "avg_views": avg_views,
                "max_views": max_views,
                "min_views": min_views,
                "engagement_rate": round(engagement_rate, 2),
                "avg_duration": duration_formatted,
                "total_videos_analyzed": len(channel.videos)
            },
            "recent_content": {
                "video_titles": titles[:8],  # Show more titles
                "upload_dates": upload_dates[:5],
                "title_themes": title_keywords[:10],
                "common_tags": common_tags[:15]  # More tags
            },
            "creator_insights": {
                "uses_tags_effectively": len(all_tags) > len(channel.videos) * 3,  # 3+ tags per video
                "title_consistency": self._check_title_consistency(titles),
                "description_quality": "detailed" if len(channel.description or "") > 200 else "basic" if len(channel.description or "") > 50 else "minimal",
                "content_focus": "specialized" if len(category_scores) <= 2 else "diverse",
                "upload_consistency": upload_style in ["daily", "weekly", "bi-weekly"],
                "audience_engagement": "high" if engagement_rate > 3 else "medium" if engagement_rate > 1 else "low"
            },
            "monetization_indicators": {
                "subscriber_milestone": self._get_subscriber_milestone(channel.subscriber_count or 0),
                "content_suitable_for_ads": primary_category not in ["controversial", "adult"],
                "brand_partnership_ready": (channel.subscriber_count or 0) >= 10000 and engagement_rate > 2,
                "merch_potential": (channel.subscriber_count or 0) >= 5000 and performance_tier in ["high", "viral"],
                "course_creation_potential": primary_category in ["education", "tech", "business"] and performance_tier != "low"
            },
            "video_analysis": top_videos_analysis
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

    def _extract_title_themes(self, titles: list) -> list:
        """Extract common themes/keywords from video titles"""
        if not titles:
            return []
        
        # Common words to ignore
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'its', 'our', 'their'}
        
        # Extract all words from titles
        all_words = []
        for title in titles:
            # Remove special characters and split into words
            import re
            words = re.findall(r'\b[a-zA-Z]{3,}\b', title.lower())
            all_words.extend([w for w in words if w not in stop_words])
        
        # Count word frequency
        word_counts = {}
        for word in all_words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        # Return most common themes (words that appear more than once)
        themes = sorted([(word, count) for word, count in word_counts.items() if count > 1], 
                       key=lambda x: x[1], reverse=True)
        
        return [word for word, count in themes]

    def _get_subscriber_milestone(self, sub_count: int) -> str:
        """Get the subscriber milestone status"""
        if sub_count >= 10000000:
            return "10M+ (mega influencer)"
        elif sub_count >= 1000000:
            return "1M+ (major influencer)"
        elif sub_count >= 100000:
            return "100K+ (established creator)"
        elif sub_count >= 10000:
            return "10K+ (growing creator)"
        elif sub_count >= 1000:
            return "1K+ (monetization eligible)"
        elif sub_count >= 100:
            return "100+ (emerging creator)"
        else:
            return "Under 100 (starting out)"

    def _analyze_top_videos(self, videos: list) -> dict:
        """Analyze top 5 recent videos and top 5 most popular videos"""
        if not videos:
            return {
                "recent_top_5": [],
                "most_popular_5": [],
                "insights": {}
            }

        # Sort by upload date for recent videos (most recent first)
        recent_videos = sorted([v for v in videos if v.upload_date], 
                             key=lambda x: x.upload_date, reverse=True)[:5]
        
        # Sort by view count for most popular videos
        popular_videos = sorted([v for v in videos if v.view_count], 
                               key=lambda x: x.view_count, reverse=True)[:5]

        # Analyze recent videos
        recent_analysis = []
        for i, video in enumerate(recent_videos, 1):
            analysis = self._analyze_single_video(video, f"Recent #{i}")
            recent_analysis.append(analysis)

        # Analyze popular videos  
        popular_analysis = []
        for i, video in enumerate(popular_videos, 1):
            analysis = self._analyze_single_video(video, f"Popular #{i}")
            popular_analysis.append(analysis)

        # Generate insights from top videos
        insights = self._generate_video_insights(recent_videos, popular_videos)

        return {
            "recent_top_5": recent_analysis,
            "most_popular_5": popular_analysis,
            "insights": insights
        }

    def _analyze_single_video(self, video, rank: str) -> dict:
        """Analyze a single video for detailed metrics"""
        # Calculate engagement metrics
        engagement_rate = 0
        if video.view_count and video.view_count > 0 and video.like_count:
            engagement_rate = (video.like_count / video.view_count) * 100

        # Format duration
        duration_formatted = "unknown"
        if video.duration:
            mins = video.duration // 60
            secs = video.duration % 60
            duration_formatted = f"{mins}m {secs}s"

        # Analyze title characteristics
        title_analysis = self._analyze_title_characteristics(video.title)
        
        # Performance classification
        view_performance = "low"
        if video.view_count:
            if video.view_count >= 1000000:
                view_performance = "viral"
            elif video.view_count >= 100000:
                view_performance = "high"
            elif video.view_count >= 10000:
                view_performance = "medium"

        return {
            "rank": rank,
            "title": video.title,
            "video_id": video.id,
            "upload_date": video.upload_date.strftime("%Y-%m-%d") if video.upload_date else "unknown",
            "metrics": {
                "views": video.view_count or 0,
                "likes": video.like_count or 0,
                "comments": video.comment_count or 0,
                "duration": duration_formatted,
                "engagement_rate": round(engagement_rate, 2)
            },
            "performance": {
                "view_tier": view_performance,
                "has_good_engagement": engagement_rate > 2,
                "comment_ratio": round((video.comment_count or 0) / max(video.view_count or 1, 1) * 1000, 2)  # Comments per 1k views
            },
            "title_analysis": title_analysis,
            "tags": video.tags[:8] if video.tags else [],  # Show first 8 tags
            "monetization_spots": self._identify_monetization_opportunities(video)
        }

    def _analyze_title_characteristics(self, title: str) -> dict:
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
            "seo_score": self._calculate_title_seo_score(title)
        }

    def _detect_clickbait_elements(self, title: str) -> list:
        """Detect potential clickbait elements in title"""
        clickbait_words = [
            "amazing", "shocking", "unbelievable", "incredible", "insane", 
            "crazy", "secret", "hidden", "exposed", "revealed", "truth",
            "you won't believe", "must see", "gone wrong", "epic fail"
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

    def _identify_monetization_opportunities(self, video) -> dict:
        """Identify monetization opportunities in video content"""
        opportunities = {
            "product_placement": [],
            "affiliate_potential": [],
            "sponsorship_segments": [],
            "course_material": False
        }
        
        title_lower = video.title.lower()
        description_lower = (video.description or "").lower()
        all_text = f"{title_lower} {description_lower}"
        
        # Product placement opportunities
        product_keywords = ["review", "unboxing", "setup", "tutorial", "guide", "comparison", "vs"]
        for keyword in product_keywords:
            if keyword in all_text:
                opportunities["product_placement"].append(keyword)
        
        # Affiliate marketing potential
        affiliate_keywords = ["best", "top", "recommend", "gear", "equipment", "tools", "software", "app"]
        for keyword in affiliate_keywords:
            if keyword in all_text:
                opportunities["affiliate_potential"].append(keyword)
        
        # Sponsorship segments
        sponsor_keywords = ["intro", "tutorial", "educational", "how-to", "explanation"]
        for keyword in sponsor_keywords:
            if keyword in all_text:
                opportunities["sponsorship_segments"].append(keyword)
        
        # Course creation potential
        course_keywords = ["tutorial", "learn", "course", "lesson", "training", "guide", "step by step"]
        opportunities["course_material"] = any(keyword in all_text for keyword in course_keywords)
        
        return opportunities

    def _generate_video_insights(self, recent_videos: list, popular_videos: list) -> dict:
        """Generate insights comparing recent vs popular videos"""
        if not recent_videos and not popular_videos:
            return {}
        
        insights = {}
        
        # Performance comparison
        if recent_videos and popular_videos:
            recent_avg_views = sum(v.view_count or 0 for v in recent_videos) / len(recent_videos)
            popular_avg_views = sum(v.view_count or 0 for v in popular_videos) / len(popular_videos)
            
            insights["performance_trend"] = {
                "recent_avg_views": int(recent_avg_views),
                "popular_avg_views": int(popular_avg_views),
                "trend": "improving" if recent_avg_views > popular_avg_views * 0.7 else "declining"
            }
        
        # Title length analysis
        if recent_videos:
            recent_title_lengths = [len(v.title) for v in recent_videos]
            insights["title_optimization"] = {
                "avg_title_length": sum(recent_title_lengths) / len(recent_title_lengths),
                "optimal_range": all(40 <= length <= 60 for length in recent_title_lengths)
            }
        
        # Content consistency
        all_videos = recent_videos + popular_videos
        if all_videos:
            durations = [v.duration for v in all_videos if v.duration]
            if durations:
                avg_duration = sum(durations) / len(durations)
                insights["content_consistency"] = {
                    "avg_video_length": f"{int(avg_duration // 60)}m {int(avg_duration % 60)}s",
                    "consistent_length": max(durations) - min(durations) < 300  # Within 5 minutes
                }
        
        return insights

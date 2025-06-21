"""
Content Analysis Module - Specialized for analyzing video content and categories
"""

import logging
from typing import Dict, List, Optional
from .models import ChannelInfo, VideoInfo

logger = logging.getLogger("uvicorn.error")


class ContentAnalyzer:
    def __init__(self):
        self.content_categories = {
            "cybersecurity": [
                "security",
                "hacking",
                "cyber",
                "penetration",
                "vulnerability",
                "malware",
                "privacy",
                "encryption",
                "breach",
                "phishing",
                "ransomware",
                "firewall",
                "vpn",
                "forensics",
                "osint",
            ],
            "tech_programming": [
                "programming",
                "coding",
                "software",
                "development",
                "javascript",
                "python",
                "react",
                "node",
                "api",
                "database",
                "algorithm",
                "framework",
                "frontend",
                "backend",
                "fullstack",
            ],
            "tech_hardware": [
                "hardware",
                "pc build",
                "gpu",
                "cpu",
                "motherboard",
                "ram",
                "ssd",
                "cooling",
                "overclocking",
                "benchmark",
                "tech review",
                "unboxing",
                "setup",
            ],
            "gaming_competitive": [
                "esports",
                "tournament",
                "competitive",
                "ranking",
                "pro",
                "league",
                "valorant",
                "csgo",
                "dota",
                "overwatch",
                "apex",
                "fortnite",
            ],
            "gaming_casual": [
                "gaming",
                "gameplay",
                "playthrough",
                "lets play",
                "indie",
                "minecraft",
                "simulation",
                "sandbox",
                "adventure",
                "puzzle",
            ],
            "gaming_review": [
                "game review",
                "first impressions",
                "gaming news",
                "upcoming games",
                "trailer reaction",
                "early access",
            ],
            "lifestyle_vlog": [
                "vlog",
                "daily",
                "life",
                "routine",
                "day in my life",
                "behind the scenes",
                "personal",
                "family",
            ],
            "lifestyle_travel": [
                "travel",
                "vacation",
                "exploring",
                "adventure",
                "culture",
                "food tour",
                "destination",
                "backpacking",
            ],
            "lifestyle_fitness": [
                "workout",
                "fitness",
                "gym",
                "health",
                "nutrition",
                "diet",
                "exercise",
                "bodybuilding",
                "cardio",
                "yoga",
            ],
            "education_academic": [
                "physics",
                "chemistry",
                "math",
                "science",
                "history",
                "biology",
                "research",
                "university",
                "study",
            ],
            "education_tutorial": [
                "tutorial",
                "how to",
                "guide",
                "learn",
                "course",
                "lesson",
                "training",
                "tips",
                "explained",
                "beginner",
            ],
            "entertainment_comedy": [
                "funny",
                "comedy",
                "humor",
                "sketch",
                "parody",
                "meme",
                "jokes",
                "stand up",
                "roast",
            ],
            "entertainment_reaction": [
                "react",
                "reaction",
                "first time",
                "watching",
                "review",
                "commentary",
                "response",
            ],
            "entertainment_music": [
                "music",
                "song",
                "cover",
                "original",
                "instrumental",
                "remix",
                "beat",
                "producer",
                "studio",
            ],
            "business_entrepreneur": [
                "business",
                "entrepreneur",
                "startup",
                "founder",
                "ceo",
                "company",
                "growth",
                "scaling",
            ],
            "business_finance": [
                "finance",
                "investing",
                "stocks",
                "crypto",
                "trading",
                "money",
                "wealth",
                "passive income",
                "budget",
            ],
            "business_marketing": [
                "marketing",
                "social media",
                "advertising",
                "brand",
                "strategy",
                "content",
                "seo",
                "growth hacking",
            ],
            "art_creative": [
                "art",
                "drawing",
                "painting",
                "design",
                "creative",
                "illustration",
                "digital art",
                "photoshop",
                "blender",
            ],
            "food_cooking": [
                "cooking",
                "recipe",
                "food",
                "kitchen",
                "chef",
                "baking",
                "meal prep",
                "restaurant",
                "cuisine",
            ],
            "automotive": [
                "car",
                "auto",
                "vehicle",
                "driving",
                "mechanic",
                "repair",
                "modification",
                "racing",
                "review",
            ],
            "fashion_beauty": [
                "fashion",
                "style",
                "outfit",
                "beauty",
                "makeup",
                "skincare",
                "haul",
                "trends",
            ],
            "sports": [
                "sports",
                "football",
                "basketball",
                "soccer",
                "baseball",
                "athlete",
                "training",
                "highlights",
            ],
            "podcast_interview": [
                "podcast",
                "interview",
                "conversation",
                "discussion",
                "talk",
                "guest",
                "story",
            ],
            "news_commentary": [
                "news",
                "politics",
                "current events",
                "commentary",
                "analysis",
                "opinion",
                "debate",
            ],
            "kids_family": [
                "kids",
                "children",
                "family",
                "toys",
                "educational",
                "nursery",
                "cartoon",
                "animation",
            ],
            "science_tech": [
                "science",
                "experiment",
                "discovery",
                "technology",
                "innovation",
                "research",
                "invention",
            ],
            "home_diy": [
                "diy",
                "home improvement",
                "renovation",
                "crafts",
                "building",
                "repair",
                "decor",
                "garden",
            ],
            "spiritual_wellness": [
                "meditation",
                "spirituality",
                "mindfulness",
                "wellness",
                "self help",
                "motivation",
                "personal growth",
            ],
        }

    def analyze_content_style(self, channel: ChannelInfo) -> Dict:
        """Analyze content style, topics, and creator focus"""
        if not channel.videos:
            return self._get_empty_analysis()

        # Extract content data
        titles = [v.title for v in channel.videos]
        all_tags = self._extract_all_tags(channel.videos)

        # Perform weighted analysis
        category_scores = self._calculate_weighted_scores(
            titles, all_tags, channel.description
        )
        primary_category, secondary_categories = self._determine_categories(
            category_scores
        )

        # Advanced analysis
        niche_specificity = self._calculate_niche_specificity(
            category_scores, primary_category
        )
        upload_analysis = self._analyze_upload_patterns(channel.videos)
        performance_analysis = self._analyze_performance(channel.videos)
        content_themes = self._extract_title_themes(titles)

        return {
            "content_type": primary_category,
            "secondary_categories": secondary_categories,
            "content_categories": category_scores,
            "niche_analysis": niche_specificity,
            "upload_style": upload_analysis["style"],
            "video_style": performance_analysis["video_style"],
            "performance_metrics": performance_analysis["metrics"],
            "recent_content": {
                "video_titles": titles[:8],
                "upload_dates": upload_analysis["recent_dates"],
                "title_themes": content_themes[:10],
                "common_tags": self._get_common_tags(all_tags, 15),
            },
            "creator_insights": self._generate_creator_insights(
                channel, upload_analysis, performance_analysis
            ),
            "monetization_indicators": self._assess_monetization_readiness(
                channel, primary_category, performance_analysis["engagement_rate"]
            ),
        }

    def _get_empty_analysis(self) -> Dict:
        """Return empty analysis structure"""
        return {
            "content_type": "unknown",
            "secondary_categories": [],
            "content_categories": {},
            "niche_analysis": {"specificity_score": 0, "niche_type": "undefined"},
            "upload_style": "unknown",
            "video_style": "unknown",
            "performance_metrics": {},
            "recent_content": {
                "video_titles": [],
                "upload_dates": [],
                "title_themes": [],
                "common_tags": [],
            },
            "creator_insights": {},
            "monetization_indicators": {},
        }

    def _extract_all_tags(self, videos: List[VideoInfo]) -> List[str]:
        """Extract all tags from videos"""
        all_tags = []
        for video in videos:
            if video.tags:
                all_tags.extend(video.tags)
        return all_tags

    def _calculate_weighted_scores(
        self, titles: List[str], all_tags: List[str], description: Optional[str]
    ) -> Dict[str, int]:
        """Calculate weighted category scores"""
        category_scores = {}
        title_weight, tag_weight, desc_weight = 3, 2, 1

        for category, keywords in self.content_categories.items():
            score = 0

            # Analyze titles (higher weight)
            title_text = " ".join(titles).lower()
            score += sum(
                title_text.count(keyword) * title_weight for keyword in keywords
            )

            # Analyze tags (medium weight)
            tag_text = " ".join(all_tags).lower()
            score += sum(tag_text.count(keyword) * tag_weight for keyword in keywords)

            # Analyze description (lower weight)
            desc_text = (description or "").lower()
            score += sum(desc_text.count(keyword) * desc_weight for keyword in keywords)

            if score > 0:
                category_scores[category] = score

        return category_scores

    def _determine_categories(self, category_scores: Dict[str, int]) -> tuple:
        """Determine primary and secondary categories"""
        if not category_scores:
            return "general", []

        sorted_categories = sorted(
            category_scores.items(), key=lambda x: x[1], reverse=True
        )
        primary_category = sorted_categories[0][0]

        # Get secondary categories (with at least 20% of primary score)
        primary_score = sorted_categories[0][1]
        secondary_categories = [
            cat for cat, score in sorted_categories[1:4] if score >= primary_score * 0.2
        ]

        return primary_category, secondary_categories

    def _analyze_upload_patterns(self, videos: List[VideoInfo]) -> Dict:
        """Analyze upload frequency and patterns"""
        recent_videos = [v for v in videos if v.upload_date]

        if len(recent_videos) < 2:
            return {"style": "insufficient_data", "recent_dates": []}

        # Calculate upload intervals
        dates = sorted([v.upload_date for v in recent_videos], reverse=True)
        intervals = [
            (dates[i - 1] - dates[i]).days for i in range(1, min(len(dates), 6))
        ]

        if intervals:
            avg_interval = sum(intervals) / len(intervals)
            if avg_interval <= 2:
                style = "daily"
            elif avg_interval <= 7:
                style = "weekly"
            elif avg_interval <= 14:
                style = "bi-weekly"
            else:
                style = "monthly"
        else:
            style = "irregular"

        recent_dates = [v.upload_date.strftime("%Y-%m-%d") for v in recent_videos[:5]]

        return {"style": style, "recent_dates": recent_dates}

    def _analyze_performance(self, videos: List[VideoInfo]) -> Dict:
        """Analyze video performance metrics"""
        if not videos:
            return {"video_style": "unknown", "metrics": {}, "engagement_rate": 0}

        # Analyze durations
        durations = [v.duration for v in videos if v.duration]
        avg_duration = sum(durations) // len(durations) if durations else 0

        # Determine video style
        if avg_duration > 0:
            duration_formatted = f"{avg_duration // 60}m {avg_duration % 60}s"
            if avg_duration < 60:
                video_style = "shorts"
            elif avg_duration < 600:
                video_style = "short_form"
            elif avg_duration < 1800:
                video_style = "medium_form"
            else:
                video_style = "long_form"
        else:
            duration_formatted = "unknown"
            video_style = "unknown"

        # Calculate performance metrics
        views_list = [v.view_count for v in videos if v.view_count]
        likes_list = [v.like_count for v in videos if v.like_count]

        avg_views = sum(views_list) // len(views_list) if views_list else 0
        max_views = max(views_list) if views_list else 0
        min_views = min(views_list) if views_list else 0

        # Calculate engagement rate
        total_views = sum(views_list)
        total_likes = sum(likes_list)
        engagement_rate = (total_likes / total_views * 100) if total_views > 0 else 0

        # Determine performance tier
        if avg_views >= 100000:
            tier = "viral"
        elif avg_views >= 10000:
            tier = "high"
        elif avg_views >= 1000:
            tier = "medium"
        else:
            tier = "low"

        return {
            "video_style": video_style,
            "engagement_rate": engagement_rate,
            "metrics": {
                "tier": tier,
                "avg_views": avg_views,
                "max_views": max_views,
                "min_views": min_views,
                "engagement_rate": round(engagement_rate, 2),
                "avg_duration": duration_formatted,
                "total_videos_analyzed": len(videos),
            },
        }

    def _extract_title_themes(self, titles: List[str]) -> List[str]:
        """Extract common themes from video titles"""
        if not titles:
            return []

        stop_words = {
            "the",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "a",
            "an",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "can",
            "this",
            "that",
            "these",
            "those",
            "i",
            "you",
            "he",
            "she",
            "it",
            "we",
            "they",
            "me",
            "him",
            "her",
            "us",
            "them",
            "my",
            "your",
            "his",
            "its",
            "our",
            "their",
        }

        all_words = []
        for title in titles:
            import re

            words = re.findall(r"\b[a-zA-Z]{3,}\b", title.lower())
            all_words.extend([w for w in words if w not in stop_words])

        word_counts = {}
        for word in all_words:
            word_counts[word] = word_counts.get(word, 0) + 1

        themes = sorted(
            [(word, count) for word, count in word_counts.items() if count > 1],
            key=lambda x: x[1],
            reverse=True,
        )

        return [word for word, count in themes]

    def _get_common_tags(self, all_tags: List[str], limit: int) -> List[str]:
        """Get most common tags"""
        tag_counts = {}
        for tag in all_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

        common_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[
            :limit
        ]
        return [tag for tag, count in common_tags]

    def _generate_creator_insights(
        self, channel: ChannelInfo, upload_analysis: Dict, performance_analysis: Dict
    ) -> Dict:
        """Generate insights about the creator"""
        videos = channel.videos
        engagement_rate = performance_analysis.get("engagement_rate", 0)

        return {
            "uses_tags_effectively": len(self._extract_all_tags(videos))
            > len(videos) * 3,
            "title_consistency": self._check_title_consistency(
                [v.title for v in videos]
            ),
            "description_quality": "detailed"
            if len(channel.description or "") > 200
            else "basic"
            if len(channel.description or "") > 50
            else "minimal",
            "content_focus": "specialized",  # Will be determined by niche analysis
            "upload_consistency": upload_analysis["style"]
            in ["daily", "weekly", "bi-weekly"],
            "audience_engagement": "high"
            if engagement_rate > 3
            else "medium"
            if engagement_rate > 1
            else "low",
        }

    def _check_title_consistency(self, titles: List[str]) -> bool:
        """Check if video titles follow consistent patterns"""
        if len(titles) < 3:
            return False

        patterns = []
        for title in titles:
            if any(char.isdigit() for char in title):
                patterns.append("numbered")
            if ":" in title:
                patterns.append("colon_format")
            if title.isupper():
                patterns.append("all_caps")
            if "|" in title:
                patterns.append("pipe_separator")

        if patterns:
            most_common = max(set(patterns), key=patterns.count)
            consistency = patterns.count(most_common) / len(titles)
            return consistency > 0.6

        return False

    def _assess_monetization_readiness(
        self, channel: ChannelInfo, primary_category: str, engagement_rate: float
    ) -> Dict:
        """Assess monetization readiness"""
        subs = channel.subscriber_count or 0

        return {
            "subscriber_milestone": self._get_subscriber_milestone(subs),
            "content_suitable_for_ads": primary_category
            not in ["controversial", "adult"],
            "brand_partnership_ready": subs >= 10000 and engagement_rate > 2,
            "merch_potential": subs >= 5000,
            "course_creation_potential": primary_category
            in ["education_tutorial", "tech_programming", "business_finance"],
        }

    def _get_subscriber_milestone(self, sub_count: int) -> str:
        """Get subscriber milestone status"""
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

    def _calculate_niche_specificity(
        self, category_scores: Dict[str, int], primary_category: str
    ) -> Dict:
        """Calculate niche specificity and monetization potential"""
        if not category_scores:
            return {
                "specificity_score": 0,
                "niche_type": "undefined",
                "focus_level": "unknown",
                "category_diversity": 0,
                "total_categories": 0,
                "cross_niche_patterns": [],
                "monetization_advantage": {},
            }

        total_score = sum(category_scores.values())
        primary_score = category_scores.get(primary_category, 0)
        primary_dominance = (
            (primary_score / total_score) * 100 if total_score > 0 else 0
        )

        # Determine niche type
        if primary_dominance >= 70:
            niche_type, focus_level = "highly_specialized", "laser_focused"
        elif primary_dominance >= 50:
            niche_type, focus_level = "specialized", "focused"
        elif primary_dominance >= 30:
            niche_type, focus_level = "somewhat_diverse", "mixed_content"
        else:
            niche_type, focus_level = "very_diverse", "broad_content"

        num_categories = len(category_scores)
        category_diversity = min(num_categories / 10 * 100, 100)

        return {
            "specificity_score": round(primary_dominance, 1),
            "niche_type": niche_type,
            "focus_level": focus_level,
            "category_diversity": round(category_diversity, 1),
            "total_categories": num_categories,
            "cross_niche_patterns": self._detect_cross_niche_patterns(category_scores),
            "monetization_advantage": self._assess_niche_monetization_potential(
                primary_category, primary_dominance
            ),
        }

    def _detect_cross_niche_patterns(
        self, category_scores: Dict[str, int]
    ) -> List[str]:
        """Detect cross-niche content patterns"""
        patterns = []

        # Tech combinations
        if (
            "tech_programming" in category_scores
            and "education_tutorial" in category_scores
        ):
            patterns.append("tech_educator")
        if (
            "cybersecurity" in category_scores
            and "education_tutorial" in category_scores
        ):
            patterns.append("security_educator")
        if (
            any("gaming" in cat for cat in category_scores)
            and "tech_hardware" in category_scores
        ):
            patterns.append("gaming_tech_reviewer")

        # Business combinations
        if (
            "business_finance" in category_scores
            and "education_tutorial" in category_scores
        ):
            patterns.append("finance_educator")
        if (
            "business_entrepreneur" in category_scores
            and "lifestyle_vlog" in category_scores
        ):
            patterns.append("entrepreneur_lifestyle")

        return patterns

    def _assess_niche_monetization_potential(
        self, primary_category: str, specificity: float
    ) -> Dict:
        """Assess monetization potential based on niche"""
        high_value_niches = {
            "business_finance": {
                "cpm": "high",
                "affiliate": "excellent",
                "courses": "excellent",
            },
            "business_entrepreneur": {
                "cmp": "high",
                "affiliate": "excellent",
                "courses": "excellent",
            },
            "tech_programming": {
                "cpm": "medium-high",
                "affiliate": "good",
                "courses": "excellent",
            },
            "cybersecurity": {
                "cpm": "high",
                "affiliate": "good",
                "courses": "excellent",
            },
        }

        niche_data = high_value_niches.get(
            primary_category,
            {"cpm": "medium", "affiliate": "medium", "courses": "medium"},
        )

        specificity_bonus = (
            "high" if specificity >= 60 else "medium" if specificity >= 40 else "low"
        )

        return {
            "niche_value": "high"
            if primary_category in high_value_niches
            else "standard",
            "cpm_potential": niche_data.get("cpm", "medium"),
            "affiliate_potential": niche_data.get("affiliate", "medium"),
            "course_potential": niche_data.get("courses", "medium"),
            "specificity_bonus": specificity_bonus,
            "audience_targeting": "precise"
            if specificity >= 60
            else "moderate"
            if specificity >= 40
            else "broad",
        }

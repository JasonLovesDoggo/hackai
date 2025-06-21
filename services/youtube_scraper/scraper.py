import yt_dlp
from typing import Optional, List, Dict, Any
from datetime import datetime
import httpx
import asyncio
from .models import ChannelInfo, VideoInfo
from .resolver import YouTubeURLResolver


class YouTubeScraper:
    def __init__(self):
        self.ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "writesubtitles": False,
            "writeautomaticsub": False,
        }
        self.resolver = YouTubeURLResolver()

    async def get_channel_info(
        self, channel_input: str, max_videos: int = 50
    ) -> Optional[ChannelInfo]:
        try:
            # Resolve channel input to actual channel ID
            channel_id = self.resolver.resolve_to_channel_id(channel_input)
            if not channel_id:
                print(f"Could not resolve channel input: {channel_input}")
                return None

            channel_url = f"https://www.youtube.com/channel/{channel_id}/videos"

            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                channel_data = ydl.extract_info(channel_url, download=False)

                if not channel_data:
                    return None

                videos = []
                entries = channel_data.get("entries", [])[:max_videos]

                for entry in entries:
                    video_info = self._extract_video_info(entry)
                    if video_info:
                        videos.append(video_info)

                channel_info = ChannelInfo(
                    id=channel_id,
                    name=channel_data.get("uploader", ""),
                    handle=channel_data.get("uploader_id", ""),
                    description=channel_data.get("description", ""),
                    subscriber_count=self._safe_int(
                        channel_data.get("subscriber_count")
                    ),
                    video_count=self._safe_int(channel_data.get("video_count")),
                    view_count=self._safe_int(channel_data.get("view_count")),
                    profile_picture_url=self._get_best_thumbnail(
                        channel_data.get("thumbnails", [])
                    ),
                    keywords=channel_data.get("tags", []) or [],
                    videos=videos,
                )

                return channel_info

        except Exception as e:
            print(f"Error scraping channel {channel_id}: {str(e)}")
            return None

    async def get_video_details(self, video_id: str) -> Optional[VideoInfo]:
        try:
            video_url = f"https://www.youtube.com/watch?v={video_id}"

            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                video_data = ydl.extract_info(video_url, download=False)

                if not video_data:
                    return None

                return self._extract_video_info(video_data)

        except Exception as e:
            print(f"Error scraping video {video_id}: {str(e)}")
            return None

    def _extract_video_info(self, video_data: Dict[str, Any]) -> Optional[VideoInfo]:
        try:
            upload_date = None
            if video_data.get("upload_date"):
                upload_date = datetime.strptime(video_data["upload_date"], "%Y%m%d")

            return VideoInfo(
                id=video_data.get("id", ""),
                title=video_data.get("title", ""),
                description=video_data.get("description", ""),
                tags=video_data.get("tags", []) or [],
                view_count=self._safe_int(video_data.get("view_count")) or 0,
                like_count=self._safe_int(video_data.get("like_count")),
                comment_count=self._safe_int(video_data.get("comment_count")),
                duration=self._safe_int(video_data.get("duration")),
                upload_date=upload_date,
                thumbnail_url=self._get_best_thumbnail(
                    video_data.get("thumbnails", [])
                ),
            )
        except Exception as e:
            print(f"Error extracting video info: {str(e)}")
            return None

    def _safe_int(self, value: Any) -> Optional[int]:
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    def _get_best_thumbnail(self, thumbnails: List[Dict[str, Any]]) -> Optional[str]:
        if not thumbnails:
            return None

        # Sort by resolution and get the best one
        sorted_thumbs = sorted(
            thumbnails,
            key=lambda x: (x.get("width", 0) * x.get("height", 0)),
            reverse=True,
        )

        return sorted_thumbs[0].get("url") if sorted_thumbs else None

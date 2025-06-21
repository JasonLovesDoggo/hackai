import httpx
import asyncio
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import os
from .models import ChannelInfo, VideoInfo

logger = logging.getLogger("uvicorn.error")


class YouTubeAPIClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("YOUTUBE_API_KEY")
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=httpx.Timeout(5.0, connect=2.0))
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    def _parse_duration(self, duration_str: str) -> Optional[int]:
        """Parse ISO 8601 duration format (PT4M13S) to seconds"""
        if not duration_str:
            return None

        try:
            import re

            pattern = r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?"
            match = re.match(pattern, duration_str)
            if not match:
                return None

            hours = int(match.group(1) or 0)
            minutes = int(match.group(2) or 0)
            seconds = int(match.group(3) or 0)

            return hours * 3600 + minutes * 60 + seconds
        except Exception:
            return None

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse ISO 8601 date format"""
        if not date_str:
            return None

        try:
            # Remove timezone info and parse
            date_str = date_str.replace("Z", "+00:00")
            return datetime.fromisoformat(date_str.replace("+00:00", ""))
        except Exception:
            return None

    async def get_channel_by_handle(self, handle: str) -> Optional[str]:
        """Get channel ID from handle (@username)"""
        if not self.api_key:
            return None

        # Remove @ if present
        if handle.startswith("@"):
            handle = handle[1:]

        try:
            url = f"{self.base_url}/channels"
            params = {"part": "id", "forHandle": handle, "key": self.api_key}

            logger.debug(f"API request: GET {url} with params: {params}")
            response = await self.client.get(url, params=params)
            logger.debug(f"Response status: {response.status_code}")
            response.raise_for_status()

            data = response.json()
            logger.debug(f"Handle lookup response: {data}")

            if data.get("items"):
                channel_id = data["items"][0]["id"]
                logger.info(f"Found channel ID: {channel_id}")
                return channel_id
            else:
                logger.warning(f"No items found for handle: {handle}")

        except Exception as e:
            logger.error(f"Error getting channel by handle {handle}: {str(e)}")

        return None

    async def get_channel_by_username(self, username: str) -> Optional[str]:
        """Get channel ID from legacy username"""
        if not self.api_key:
            return None

        try:
            url = f"{self.base_url}/channels"
            params = {"part": "id", "forUsername": username, "key": self.api_key}

            response = await self.client.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            if data.get("items"):
                return data["items"][0]["id"]

        except Exception as e:
            logger.error(f"Error getting channel by username {username}: {str(e)}")

        return None

    async def get_channel_info(
        self, channel_id: str, max_videos: int = 50
    ) -> Optional[ChannelInfo]:
        """Get channel information and recent videos using YouTube Data API"""
        if not self.api_key:
            return None

        try:
            # Get channel details
            channel_url = f"{self.base_url}/channels"
            channel_params = {
                "part": "snippet,statistics,brandingSettings",
                "id": channel_id,
                "key": self.api_key,
            }

            # Get channel videos
            videos_url = f"{self.base_url}/search"
            videos_params = {
                "part": "snippet",
                "channelId": channel_id,
                "order": "date",
                "type": "video",
                "maxResults": min(max_videos, 50),
                "key": self.api_key,
            }

            logger.debug(
                f"Getting channel info - URL: {channel_url}, params: {channel_params}"
            )
            logger.debug(f"Getting videos - URL: {videos_url}, params: {videos_params}")

            # Make both requests concurrently
            channel_response, videos_response = await asyncio.gather(
                self.client.get(channel_url, params=channel_params),
                self.client.get(videos_url, params=videos_params),
                return_exceptions=True,
            )

            logger.debug(f"Channel response type: {type(channel_response)}")
            logger.debug(f"Videos response type: {type(videos_response)}")

            if isinstance(channel_response, Exception):
                logger.error(f"Channel API exception: {channel_response}")
                return None

            if isinstance(videos_response, Exception):
                logger.error(f"Videos API exception: {videos_response}")
                return None

            logger.debug(f"Channel response status: {channel_response.status_code}")
            logger.debug(f"Videos response status: {videos_response.status_code}")

            channel_response.raise_for_status()
            videos_response.raise_for_status()

            channel_data = channel_response.json()
            videos_data = videos_response.json()

            logger.debug(f"Channel API response for {channel_id}:")
            logger.debug(f"Channel data items: {len(channel_data.get('items', []))}")
            logger.debug(f"Channel response: {channel_data}")
            logger.debug(f"Videos data items: {len(videos_data.get('items', []))}")

            if not channel_data.get("items"):
                logger.error(f"No channel items found for {channel_id}")
                return None

            channel_item = channel_data["items"][0]
            snippet = channel_item["snippet"]
            statistics = channel_item.get("statistics", {})

            # Get video details for the found videos
            video_ids = [item["id"]["videoId"] for item in videos_data.get("items", [])]
            videos = await self._get_video_details_batch(video_ids) if video_ids else []

            # Get profile picture URL
            thumbnails = snippet.get("thumbnails", {})
            profile_pic = None
            for size in ["high", "medium", "default"]:
                if size in thumbnails:
                    profile_pic = thumbnails[size]["url"]
                    break

            return ChannelInfo(
                id=channel_id,
                name=snippet.get("title", ""),
                handle=snippet.get("customUrl", ""),
                description=snippet.get("description", ""),
                subscriber_count=int(statistics.get("subscriberCount", 0))
                if statistics.get("subscriberCount")
                else None,
                video_count=int(statistics.get("videoCount", 0))
                if statistics.get("videoCount")
                else None,
                view_count=int(statistics.get("viewCount", 0))
                if statistics.get("viewCount")
                else None,
                profile_picture_url=profile_pic,
                keywords=snippet.get("tags", []) or [],
                videos=videos,
            )

        except Exception as e:
            logger.error(f"Error getting channel info for {channel_id}: {str(e)}")
            return None

    async def _get_video_details_batch(self, video_ids: List[str]) -> List[VideoInfo]:
        """Get detailed information for multiple videos"""
        if not video_ids or not self.api_key:
            return []

        try:
            # YouTube API allows up to 50 video IDs per request
            video_details = []

            for i in range(0, len(video_ids), 50):
                batch_ids = video_ids[i : i + 50]

                url = f"{self.base_url}/videos"
                params = {
                    "part": "snippet,statistics,contentDetails",
                    "id": ",".join(batch_ids),
                    "key": self.api_key,
                }

                response = await self.client.get(url, params=params)
                response.raise_for_status()

                data = response.json()

                for item in data.get("items", []):
                    video_info = self._parse_video_item(item)
                    if video_info:
                        video_details.append(video_info)

            return video_details

        except Exception as e:
            print(f"Error getting video details: {str(e)}")
            return []

    def _parse_video_item(self, item: Dict[str, Any]) -> Optional[VideoInfo]:
        """Parse a video item from YouTube API response"""
        try:
            snippet = item.get("snippet", {})
            statistics = item.get("statistics", {})
            content_details = item.get("contentDetails", {})

            # Get best thumbnail
            thumbnails = snippet.get("thumbnails", {})
            thumbnail_url = None
            for size in ["maxres", "high", "medium", "default"]:
                if size in thumbnails:
                    thumbnail_url = thumbnails[size]["url"]
                    break

            return VideoInfo(
                id=item.get("id", ""),
                title=snippet.get("title", ""),
                description=snippet.get("description", ""),
                tags=snippet.get("tags", []) or [],
                view_count=int(statistics.get("viewCount", 0))
                if statistics.get("viewCount")
                else 0,
                like_count=int(statistics.get("likeCount", 0))
                if statistics.get("likeCount")
                else None,
                comment_count=int(statistics.get("commentCount", 0))
                if statistics.get("commentCount")
                else None,
                duration=self._parse_duration(content_details.get("duration")),
                upload_date=self._parse_date(snippet.get("publishedAt")),
                thumbnail_url=thumbnail_url,
            )

        except Exception as e:
            print(f"Error parsing video item: {str(e)}")
            return None

    async def get_video_info(self, video_id: str) -> Optional[VideoInfo]:
        """Get detailed information for a single video"""
        if not self.api_key:
            return None

        try:
            url = f"{self.base_url}/videos"
            params = {
                "part": "snippet,statistics,contentDetails",
                "id": video_id,
                "key": self.api_key,
            }

            response = await self.client.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            if not data.get("items"):
                return None

            return self._parse_video_item(data["items"][0])

        except Exception as e:
            print(f"Error getting video info for {video_id}: {str(e)}")
            return None

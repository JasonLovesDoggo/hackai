import re
import yt_dlp
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import json
import os
from urllib.parse import urlparse, parse_qs


class YouTubeURLResolver:
    def __init__(self, cache_dir: str = ".cache"):
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(cache_dir, "youtube_resolver_cache.json")
        self.cache_ttl = 24 * 60 * 60  # 24 hours in seconds
        self._ensure_cache_dir()
        self._load_cache()

    def _ensure_cache_dir(self):
        """Ensure cache directory exists"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def _load_cache(self):
        """Load cache from file"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, "r") as f:
                    self.cache = json.load(f)
            else:
                self.cache = {}
        except Exception:
            self.cache = {}

    def _save_cache(self):
        """Save cache to file"""
        try:
            with open(self.cache_file, "w") as f:
                json.dump(self.cache, f, indent=2)
        except Exception:
            pass

    def _is_cache_valid(self, timestamp: str) -> bool:
        """Check if cache entry is still valid"""
        try:
            cached_time = datetime.fromisoformat(timestamp)
            return (datetime.now() - cached_time).total_seconds() < self.cache_ttl
        except Exception:
            return False

    def _extract_channel_id_from_url(self, url: str) -> Optional[str]:
        """Extract channel ID from various YouTube URL formats"""
        # Handle @username format
        if "@" in url:
            handle_match = re.search(r"@([^/?#&]+)", url)
            if handle_match:
                return self._resolve_handle_to_channel_id(handle_match.group(1))

        # Handle /c/ format
        c_match = re.search(r"/c/([^/?#&]+)", url)
        if c_match:
            return self._resolve_custom_url_to_channel_id(c_match.group(1))

        # Handle /user/ format
        user_match = re.search(r"/user/([^/?#&]+)", url)
        if user_match:
            return self._resolve_username_to_channel_id(user_match.group(1))

        # Handle /channel/ format (already has channel ID)
        channel_match = re.search(r"/channel/([^/?#&]+)", url)
        if channel_match:
            return channel_match.group(1)

        return None

    def _resolve_handle_to_channel_id(self, handle: str) -> Optional[str]:
        """Resolve @handle to channel ID using yt-dlp"""
        cache_key = f"handle:{handle}"

        # Check cache first
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if self._is_cache_valid(cache_entry["timestamp"]):
                return cache_entry["channel_id"]

        try:
            # Use yt-dlp to resolve the handle
            url = f"https://www.youtube.com/@{handle}"

            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "extract_flat": True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                if info and "channel_id" in info:
                    channel_id = info["channel_id"]

                    # Cache the result
                    self.cache[cache_key] = {
                        "channel_id": channel_id,
                        "timestamp": datetime.now().isoformat(),
                    }
                    self._save_cache()

                    return channel_id

        except Exception as e:
            print(f"Error resolving handle @{handle}: {str(e)}")

        return None

    def _resolve_custom_url_to_channel_id(self, custom_name: str) -> Optional[str]:
        """Resolve /c/customname to channel ID"""
        cache_key = f"custom:{custom_name}"

        # Check cache first
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if self._is_cache_valid(cache_entry["timestamp"]):
                return cache_entry["channel_id"]

        try:
            url = f"https://www.youtube.com/c/{custom_name}"

            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "extract_flat": True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                if info and "channel_id" in info:
                    channel_id = info["channel_id"]

                    # Cache the result
                    self.cache[cache_key] = {
                        "channel_id": channel_id,
                        "timestamp": datetime.now().isoformat(),
                    }
                    self._save_cache()

                    return channel_id

        except Exception as e:
            print(f"Error resolving custom URL /c/{custom_name}: {str(e)}")

        return None

    def _resolve_username_to_channel_id(self, username: str) -> Optional[str]:
        """Resolve /user/username to channel ID"""
        cache_key = f"user:{username}"

        # Check cache first
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if self._is_cache_valid(cache_entry["timestamp"]):
                return cache_entry["channel_id"]

        try:
            url = f"https://www.youtube.com/user/{username}"

            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "extract_flat": True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                if info and "channel_id" in info:
                    channel_id = info["channel_id"]

                    # Cache the result
                    self.cache[cache_key] = {
                        "channel_id": channel_id,
                        "timestamp": datetime.now().isoformat(),
                    }
                    self._save_cache()

                    return channel_id

        except Exception as e:
            print(f"Error resolving username /user/{username}: {str(e)}")

        return None

    def resolve_to_channel_id(self, input_str: str) -> Optional[str]:
        """
        Resolve various YouTube URL formats or handles to channel ID

        Supports:
        - https://www.youtube.com/@ThePrimeTimeagen
        - https://www.youtube.com/c/ThePrimeTimeagen
        - https://www.youtube.com/user/ThePrimeTimeagen
        - https://www.youtube.com/channel/UCUyeluBRhGPCW4rPe_UvBZQ
        - @ThePrimeTimeagen
        - Raw channel IDs
        """
        # If it's already a channel ID (starts with UC and is 24 chars long)
        if input_str.startswith("UC") and len(input_str) == 24:
            return input_str

        # If it's just a handle without @, add it
        if not input_str.startswith(("http", "@", "UC")) and "/" not in input_str:
            input_str = f"@{input_str}"

        # If it's a handle starting with @, resolve it
        if input_str.startswith("@"):
            handle = input_str[1:]  # Remove @
            return self._resolve_handle_to_channel_id(handle)

        # If it's a URL, extract channel ID
        if input_str.startswith("http"):
            return self._extract_channel_id_from_url(input_str)

        return None

    def clear_cache(self):
        """Clear the resolver cache"""
        self.cache = {}
        try:
            if os.path.exists(self.cache_file):
                os.remove(self.cache_file)
        except Exception:
            pass

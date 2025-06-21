import re
import os
from typing import Optional, Tuple
from urllib.parse import urlparse


class VideoInputResolver:
    """Resolves different types of video inputs (URLs, file paths)"""
    
    def __init__(self):
        self.supported_video_extensions = {
            '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'
        }
        
        self.youtube_patterns = [
            r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
            r'(?:https?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]{11})',
            r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})',
        ]

    def resolve_input(self, input_str: str) -> Tuple[str, str]:
        """
        Resolve video input to determine type and extract relevant information
        
        Returns:
            Tuple of (input_type, identifier)
            input_type: 'youtube_url', 'file_path', 'other_url', 'invalid'
            identifier: video_id, file_path, or URL
        """
        if not input_str:
            return 'invalid', ''
        
        # Check if it's a YouTube URL
        youtube_id = self.extract_youtube_id(input_str)
        if youtube_id:
            return 'youtube_url', youtube_id
        
        # Check if it's a file path
        if self.is_valid_file_path(input_str):
            return 'file_path', input_str
        
        # Check if it's a valid URL
        if self.is_valid_url(input_str):
            return 'other_url', input_str
        
        return 'invalid', input_str

    def extract_youtube_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from various YouTube URL formats"""
        for pattern in self.youtube_patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def is_valid_file_path(self, path: str) -> bool:
        """Check if the path is a valid video file path"""
        if not path or not os.path.exists(path):
            return False
        
        # Check if it's a file (not directory)
        if not os.path.isfile(path):
            return False
        
        # Check file extension
        _, ext = os.path.splitext(path.lower())
        return ext in self.supported_video_extensions

    def is_valid_url(self, url: str) -> bool:
        """Check if the string is a valid URL"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False

    def validate_video_file(self, file_path: str) -> Tuple[bool, str]:
        """
        Validate a video file for analysis
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not os.path.exists(file_path):
            return False, "File does not exist"
        
        if not os.path.isfile(file_path):
            return False, "Path is not a file"
        
        # Check file size (max 100MB for API)
        file_size = os.path.getsize(file_path)
        max_size = 100 * 1024 * 1024  # 100MB
        if file_size > max_size:
            return False, f"File size ({file_size / 1024 / 1024:.1f}MB) exceeds maximum allowed size (100MB)"
        
        # Check file extension
        _, ext = os.path.splitext(file_path.lower())
        if ext not in self.supported_video_extensions:
            return False, f"Unsupported file format: {ext}. Supported formats: {', '.join(self.supported_video_extensions)}"
        
        return True, ""

    def get_video_info(self, input_str: str) -> dict:
        """
        Get information about the video input
        
        Returns:
            Dictionary with video information
        """
        input_type, identifier = self.resolve_input(input_str)
        
        info = {
            'input_type': input_type,
            'identifier': identifier,
            'is_valid': input_type != 'invalid'
        }
        
        if input_type == 'file_path':
            is_valid, error = self.validate_video_file(identifier)
            info['file_valid'] = is_valid
            info['file_error'] = error if not is_valid else None
            
            if is_valid:
                info['file_size'] = os.path.getsize(identifier)
                info['file_extension'] = os.path.splitext(identifier)[1].lower()
        
        elif input_type == 'youtube_url':
            info['video_id'] = identifier
            info['youtube_url'] = f"https://www.youtube.com/watch?v={identifier}"
        
        elif input_type == 'other_url':
            info['url'] = identifier
        
        return info 
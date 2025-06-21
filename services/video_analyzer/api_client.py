import os
from typing import List, Optional, Dict, Any
from twelvelabs import TwelveLabs
import time

class TwelveLabsAPIClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("TWELVE_LABS_API_KEY")
        if not self.api_key:
            raise ValueError("Twelve Labs API key is required. Set TWELVE_LABS_API_KEY environment variable.")
        self.client = TwelveLabs(api_key=self.api_key)

    def analyze_video_url(self, video_url: str, features: List[str]) -> str:
        """Submit a video URL for analysis and return the index ID."""
        index = self.client.index.create(
            video_url=video_url,
            features=features
        )
        return index.id

    def analyze_video_file(self, file_path: str, features: List[str]) -> str:
        """Upload a video file for analysis and return the index ID."""
        index = self.client.index.create(
            video_file=file_path,
            features=features
        )
        return index.id

    def wait_for_completion(self, index_id: str, timeout: int = 300) -> bool:
        """Wait for the analysis to complete."""
        start = time.time()
        while time.time() - start < timeout:
            index = self.client.index.retrieve(index_id)
            if index.status == "ready":
                return True
            elif index.status == "failed":
                return False
            time.sleep(5)
        return False

    def get_analysis_result(self, index_id: str) -> Dict[str, Any]:
        """Get the analysis result for the given index ID."""
        # The SDK may provide a method for this; if not, use .retrieve
        index = self.client.index.retrieve(index_id)
        return index.to_dict() 
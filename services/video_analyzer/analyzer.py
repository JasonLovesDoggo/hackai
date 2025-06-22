import uuid
from datetime import datetime
from .models import VideoAnalysisRequest, VideoAnalysisResult
from .api_client import TwelveLabsAPIClient

class VideoAnalyzer:
    def __init__(self):
        self.api_client = TwelveLabsAPIClient()

    def analyze_video(self, file_path: str, request: VideoAnalysisRequest) -> VideoAnalysisResult:
        """Analyze a video file and return results"""
        task_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        try:
            # Use the API client to analyze the video
            result = self.api_client.analyze_video_file(file_path, request.features)
            
            return VideoAnalysisResult(
                task_id=result["task_id"],
                status=result["status"],
                result=result["result"],
                created_at=start_time
            )
            
        except Exception as e:
            return VideoAnalysisResult(
                task_id=task_id,
                status="failed",
                error_message=str(e),
                created_at=start_time
            )
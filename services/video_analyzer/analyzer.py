import uuid
from datetime import datetime
from typing import List
from .models import VideoAnalysisRequest, VideoAnalysisResult
from .api_client import TwelveLabsAPIClient
from .resolver import VideoInputResolver

class VideoAnalyzer:
    def __init__(self):
        self.api_client = TwelveLabsAPIClient()
        self.resolver = VideoInputResolver()

    def analyze_video(self, request: VideoAnalysisRequest) -> VideoAnalysisResult:
        video_id = str(uuid.uuid4())
        start_time = datetime.now()
        try:
            features = request.features or ["conversation", "visual", "text_in_video", "action", "concept"]
            if request.video_url:
                input_info = self.resolver.get_video_info(request.video_url)
                if not input_info['is_valid']:
                    return VideoAnalysisResult(
                        video_id=video_id,
                        status="failed",
                        created_at=start_time,
                        error_message=f"Invalid video URL: {request.video_url}"
                    )
                index_id = self.api_client.analyze_video_url(request.video_url, features)
            elif request.video_file_path:
                input_info = self.resolver.get_video_info(request.video_file_path)
                if not input_info['is_valid'] or not input_info.get('file_valid', False):
                    return VideoAnalysisResult(
                        video_id=video_id,
                        status="failed",
                        created_at=start_time,
                        error_message=input_info.get('file_error', 'Invalid file path')
                    )
                index_id = self.api_client.analyze_video_file(request.video_file_path, features)
            else:
                return VideoAnalysisResult(
                    video_id=video_id,
                    status="failed",
                    created_at=start_time,
                    error_message="Either video_url or video_file_path must be provided"
                )
            # Wait for completion
            success = self.api_client.wait_for_completion(index_id)
            if not success:
                return VideoAnalysisResult(
                    video_id=video_id,
                    status="failed",
                    created_at=start_time,
                    error_message="Video analysis timed out or failed"
                )
            # Get results
            analysis_data = self.api_client.get_analysis_result(index_id)
            # Just return the raw data for now for simplicity
            return VideoAnalysisResult(
                video_id=video_id,
                status="completed",
                transcript=analysis_data.get("transcript", []),
                tags=analysis_data.get("tags", []),
                visual_objects=analysis_data.get("visual", []),
                scenes=analysis_data.get("scenes", []),
                concepts=analysis_data.get("concepts", []),
                analysis_duration=(datetime.now() - start_time).total_seconds(),
                created_at=start_time
            )
        except Exception as e:
            return VideoAnalysisResult(
                video_id=video_id,
                status="failed",
                created_at=start_time,
                error_message=f"Analysis failed: {str(e)}"
            )

if __name__ == "__main__":
    # Example usage:
    sample_video = VideoAnalysisRequest(video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    analyzer = VideoAnalyzer()
    result = analyzer.analyze_video(sample_video)
    print("Analysis result:", result)

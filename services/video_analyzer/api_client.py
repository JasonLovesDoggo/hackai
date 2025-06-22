import os
import time
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from twelvelabs import TwelveLabs
from datetime import datetime

load_dotenv()

class TwelveLabsAPIClient:
    def __init__(self):
        api_key = os.getenv("TWELVE_LABS_API_KEY")
        if not api_key:
            raise ValueError("TWELVE_LABS_API_KEY environment variable is required")
        self.client = TwelveLabs(api_key=api_key)
        self._index_id = None

    def _get_or_create_index(self) -> str:
        """Get existing index or create a new one for video analysis"""
        if self._index_id:
            return self._index_id
        
        # Create an index with marengo2.7 model for visual and audio analysis
        # The generate methods (gist, summarize, analyze) work directly on video IDs
        print("Creating index for video analysis...")
        index = self.client.index.create(
            name=f"Video Analysis Index - {datetime.now().isoformat()}",
            models=[
                {"name": "marengo2.7", "options": ["visual", "audio"]}
            ]
        )
        self._index_id = index.id
        print(f"Index created: {self._index_id}")
        return self._index_id

    def upload_video(self, file_path: str) -> Dict[str, Any]:
        """
        Upload a video file using the official SDK pattern
        Returns task information with video_id
        """
        try:
            index_id = self._get_or_create_index()
            
            print(f"Uploading video: {file_path}")
            # Create a video indexing task using the official pattern
            task = self.client.task.create(
                index_id=index_id,
                file=file_path
            )
            print(f"Task created: {task.id}")

            # Wait for the task to complete using the built-in method
            print("Waiting for video upload and indexing to complete...")
            
            def on_task_update(task):
                print(f"  Status: {task.status}")
                if hasattr(task, 'process') and task.process:
                    print(f"  Progress: {task.process.percentage}%")
            
            task.wait_for_done(sleep_interval=5, callback=on_task_update)

            if task.status != "ready":
                raise Exception(f"Video upload failed. Status: {task.status}")

            print(f"Video uploaded successfully! Video ID: {task.video_id}")
            
            return {
                "task_id": task.id,
                "video_id": task.video_id,
                "status": task.status,
                "created_at": datetime.now()
            }

        except Exception as e:
            print(f"Error uploading video: {str(e)}")
            raise

    def analyze_video(self, video_id: str, analysis_types: List[str] = None) -> Dict[str, Any]:
        """
        Analyze a video using various Twelve Labs analysis methods
        Returns comprehensive analysis results
        """
        if analysis_types is None:
            analysis_types = ["gist", "summary", "analysis"]
        
        results = {}
        
        try:
            # 1. Generate titles, topics, and hashtags
            if "gist" in analysis_types:
                print("Generating titles, topics, and hashtags...")
                gist_result = self.client.gist(
                    video_id=video_id,
                    types=["title", "topic", "hashtag"]
                )
                results["gist"] = {
                    "title": gist_result.title,
                    "topics": gist_result.topics,
                    "hashtags": gist_result.hashtags,
                    "usage": gist_result.usage
                }

            # 2. Generate summary
            if "summary" in analysis_types:
                print("Generating video summary...")
                summary_result = self.client.summarize(
                    video_id=video_id,
                    type="summary",
                    prompt="Provide a comprehensive summary of this video content, including main topics, key points, and important details.",
                    temperature=0.7
                )
                results["summary"] = {
                    "summary": summary_result.summary,
                    "usage": summary_result.usage
                }

            # 3. Generate chapters
            if "chapters" in analysis_types:
                print("Generating video chapters...")
                chapters_result = self.client.summarize(
                    video_id=video_id,
                    type="chapter",
                    prompt="Break down this video into logical chapters with clear titles and summaries for each section.",
                    temperature=0.7
                )
                results["chapters"] = {
                    "chapters": chapters_result.chapters,
                    "usage": chapters_result.usage
                }

            # 4. Generate highlights
            if "highlights" in analysis_types:
                print("Generating video highlights...")
                highlights_result = self.client.summarize(
                    video_id=video_id,
                    type="highlight",
                    prompt="Identify the most important and engaging moments in this video.",
                    temperature=0.7
                )
                results["highlights"] = {
                    "highlights": highlights_result.highlights,
                    "usage": highlights_result.usage
                }

            # 5. Open-ended analysis
            if "analysis" in analysis_types:
                print("Performing open-ended analysis...")
                analysis_result = self.client.analyze(
                    video_id=video_id,
                    prompt="Analyze this video comprehensively. Include: 1) Main content and themes, 2) Visual elements and objects detected, 3) Audio characteristics, 4) Target audience, 5) Content quality assessment, 6) Engagement potential, 7) Key insights and takeaways.",
                    temperature=0.7
                )
                results["analysis"] = {
                    "analysis": analysis_result.data,
                    "usage": analysis_result.usage
                }

            return results

        except Exception as e:
            print(f"Error analyzing video: {str(e)}")
            raise

    def analyze_video_file(self, file_path: str, features: List[str] = None) -> Dict[str, Any]:
        """
        Complete workflow: Upload video and analyze it
        Returns comprehensive analysis results
        """
        try:
            # Step 1: Upload the video
            upload_result = self.upload_video(file_path)
            video_id = upload_result["video_id"]
            
            # Step 2: Analyze the video
            analysis_results = self.analyze_video(video_id, features)
            
            # Combine results
            return {
                "upload": upload_result,
                "analysis": analysis_results,
                "video_id": video_id,
                "status": "completed",
                "created_at": datetime.now()
            }

        except Exception as e:
            print(f"Error in complete video analysis workflow: {str(e)}")
            raise

    def get_video_info(self, video_id: str) -> Dict[str, Any]:
        """Get information about a specific video"""
        try:
            # You can use the video API to get video information
            # This would require additional SDK methods if available
            return {
                "video_id": video_id,
                "status": "info_retrieved"
            }
        except Exception as e:
            print(f"Error getting video info: {str(e)}")
            raise

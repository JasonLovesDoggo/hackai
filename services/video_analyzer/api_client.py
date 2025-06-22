import os
import time
from typing import Dict, Any
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

    def analyze_video_file(self, file_path: str, features: list) -> Dict[str, Any]:
        """
        Analyze a video file using Twelve Labs API
        Returns the analysis results
        """
        try:
            # Filter features to only use valid options: visual, audio
            valid_features = [f for f in features if f in ['visual', 'audio']]
            if not valid_features:
                valid_features = ['visual', 'audio']  # Default to both if none specified
            
            # Create an index with the correct models format
            print("Creating index...")
            index = self.client.index.create(
                name=f"Video Analysis - {datetime.now().isoformat()}",
                models=[{"name": "marengo2.7", "options": valid_features}]
            )
            print(f"Index created: {index.id}")

            # Create a task to analyze the video
            print("Creating analysis task...")
            with open(file_path, 'rb') as video_file:
                task = self.client.task.create(
                    index_id=index.id,
                    file=video_file
                )
            print(f"Task created: {task.id}")

            # Wait for the task to complete using the built-in method
            print("Waiting for analysis to complete...")
            task.wait_for_done()

            if task.status != "ready":
                raise Exception(f"Video analysis failed. Status: {task.status}")

            print("Analysis completed!")
            
            # Get the raw task data
            task_data = task.__dict__
            
            return {
                "task_id": task.id,
                "status": "completed",
                "result": task_data,
                "created_at": datetime.now()
            }

        except Exception as e:
            print(f"Error in video analysis: {str(e)}")
            raise

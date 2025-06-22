import os
from typing import Dict, Any, List
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

        # Create an index with pegasus1.2 model for visual and audio analysis
        # The generate methods (gist, summarize, analyze) work directly on video IDs
        print("Creating index for video analysis...")
        index = self.client.index.create(
            name=f"Video Analysis Index - {datetime.now().isoformat()}",
            models=[{"name": "pegasus1.2", "options": ["visual", "audio"]}],
        )
        self._index_id = index.id
        print(f"Index created: {self._index_id}")
        return self._index_id

    def upload_video_async(self, file_path: str) -> Dict[str, Any]:
        """
        Start video upload without waiting for completion
        Returns task information immediately
        """
        try:
            index_id = self._get_or_create_index()

            print(f"Uploading video: {file_path}")
            # Create a video indexing task using the official pattern
            task = self.client.task.create(index_id=index_id, file=file_path)
            print(f"Task created: {task.id}")

            return {
                "task_id": task.id,
                "video_id": getattr(task, 'video_id', None),
                "status": task.status,
                "created_at": datetime.now(),
            }

        except Exception as e:
            print(f"Error uploading video: {str(e)}")
            raise

    async def wait_for_upload_completion(self, task_id: str) -> Dict[str, Any]:
        """
        Async polling for video upload completion
        """
        import asyncio
        
        while True:
            # Get task status
            task = self.client.task.retrieve(task_id)
            print(f"  Status: {task.status}")
            
            if task.status == "ready":
                return {
                    "task_id": task.id,
                    "video_id": task.video_id,
                    "status": task.status,
                    "created_at": datetime.now(),
                }
            elif task.status in ["failed", "error"]:
                raise Exception(f"Video upload failed. Status: {task.status}")
            
            # Wait 5 seconds before polling again
            await asyncio.sleep(5)

    def upload_video(self, file_path: str) -> Dict[str, Any]:
        """
        Upload a video file using the official SDK pattern
        Returns task information with video_id
        """
        try:
            index_id = self._get_or_create_index()

            print(f"Uploading video: {file_path}")
            # Create a video indexing task using the official pattern
            task = self.client.task.create(index_id=index_id, file=file_path)
            print(f"Task created: {task.id}")

            # Wait for the task to complete using the built-in method
            print("Waiting for video upload and indexing to complete...")

            def on_task_update(task):
                print(f"  Status: {task.status}")
                if hasattr(task, "process") and task.process:
                    print(f"  Progress: {task.process.percentage}%")

            task.wait_for_done(sleep_interval=5, callback=on_task_update)

            if task.status != "ready":
                raise Exception(f"Video upload failed. Status: {task.status}")

            print(f"Video uploaded successfully! Video ID: {task.video_id}")

            return {
                "task_id": task.id,
                "video_id": task.video_id,
                "status": task.status,
                "created_at": datetime.now(),
            }

        except Exception as e:
            print(f"Error uploading video: {str(e)}")
            raise

    async def analyze_video(
        self, video_id: str, analysis_types: List[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a video using various Twelve Labs analysis methods
        Returns comprehensive analysis results
        """
        if analysis_types is None:
            analysis_types = ["gist", "summary", "analysis"]

        results = {}

        try:
            # 1. Generate titles, topics, and hashtags
            # if "gist" in analysis_types:
            #     print("Generating titles, topics, and hashtags...")
            #     gist_result = self.client.gist(
            #         video_id=video_id,
            #         types=["title", "topic", "hashtag"]
            #     )
            #     results["gist"] = {
            #         "title": gist_result.title,
            #         "topics": gist_result.topics,
            #         "hashtags": gist_result.hashtags,
            #         "usage": gist_result.usage
            #     }

            # 2. Generate summary
            if "summary" in analysis_types:
                print("Generating video summary...")
                summary_result = self.client.summarize(
                    video_id=video_id,
                    type="summary",
                    prompt="Provide a comprehensive summary of this video content, including main topics, key points, and important details.",
                    temperature=0.7,
                )
                results["summary"] = {
                    "summary": summary_result.summary,
                    "usage": summary_result.usage,
                }

            # 3. Generate chapters
            if "chapters" in analysis_types:
                print("Generating video chapters...")
                chapters_result = self.client.summarize(
                    video_id=video_id,
                    type="chapter",
                    prompt="Break down this video into logical chapters with clear titles and summaries for each section. Also give them suggestions on how they can monetize the content using some of the content montization ideas which regards to the features that are available in the stan store",
                    temperature=0.7,
                )
                results["chapters"] = {
                    "chapters": chapters_result.chapters,
                    "usage": chapters_result.usage,
                }

            # 4. Generate highlights
            if "highlights" in analysis_types:
                print("Generating video highlights...")
                highlights_result = self.client.summarize(
                    video_id=video_id,
                    type="highlight",
                    prompt="Identify the most important and engaging moments in this video.",
                    temperature=0.7,
                )
                results["highlights"] = {
                    "highlights": highlights_result.highlights,
                    "usage": highlights_result.usage,
                }

            # 5. Open-ended analysis
            if "analysis" in analysis_types:
                print("Performing open-ended analysis...")
                analysis_result = self.client.analyze(
                    video_id=video_id,
                    prompt="Analyze this video comprehensively. Include: 1) Main content and themes, 2) Visual elements and objects detected, 3) Audio characteristics, 4) Target audience, 5) Content quality assessment, 6) Engagement potential, 7) Key insights and takeaways. 8) Any Products/things that the viewer can buy that has been shown it should be a very particular named or shown item and a list of items consumer items that were shown with time stamps. 9) Also give them suggestions on how they can monetize the content using some of the content monetization ideas which regards to the features that are available in the stanstore",
                    temperature=0.7,
                )
                results["analysis"] = {
                    "analysis": analysis_result.data,
                    "usage": analysis_result.usage,
                }

            return results

        except Exception as e:
            print(f"Error analyzing video: {str(e)}")
            raise

    def analyze_video_file(
        self, file_path: str, features: List[str] = None
    ) -> Dict[str, Any]:
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
                "created_at": datetime.now(),
            }

        except Exception as e:
            print(f"Error in complete video analysis workflow: {str(e)}")
            raise

    def get_frame_by_frame_analysis(
        self, video_id: str, interval_seconds: int = 5
    ) -> Dict[str, Any]:
        """
        Get frame-by-frame analysis of a video using time-based search
        Returns analysis for each time interval
        """
        try:
            print(
                f"Getting frame-by-frame analysis with {interval_seconds}s intervals..."
            )

            # First, get video information to determine duration
            videos = self.client.index.video.list(self._index_id)
            video_info = None
            for video in videos:
                if video.id == video_id:
                    video_info = video
                    break

            if not video_info:
                raise Exception(f"Video {video_id} not found in index")

            # Get actual video duration - try different attributes
            duration = None
            for attr in ["duration", "length", "video_duration"]:
                if hasattr(video_info, attr):
                    duration = getattr(video_info, attr)
                    break

            if duration is None:
                # If we can't get duration, try to estimate from search results
                print("Could not get video duration, attempting to estimate...")
                try:
                    # Try a broad search to see if we get any results
                    test_search = self.client.search(
                        index_id=self._index_id, query="*", search_options=["visual"]
                    )
                    if hasattr(test_search, "data") and test_search.data:
                        # Find the latest timestamp
                        max_time = 0
                        for result in test_search.data:
                            if hasattr(result, "end_time"):
                                max_time = max(max_time, result.end_time)
                            elif hasattr(result, "start_time"):
                                max_time = max(max_time, result.start_time)
                        duration = max_time if max_time > 0 else None
                        if duration:
                            print(
                                f"Estimated duration from search results: {duration}s"
                            )
                        else:
                            print("Could not estimate duration from search results")
                    else:
                        print("No search results available for duration estimation")
                except Exception as e:
                    print(f"Could not estimate duration: {str(e)}")

                # If we still don't have duration, we need to handle this case
                if duration is None:
                    print(
                        "Warning: Could not determine video duration. Analysis may be incomplete."
                    )
                    # For frame analysis, we'll need to handle this case differently
                    # For now, let's try to get a reasonable estimate
                    duration = 300  # Assume 5 minutes as a reasonable default
                    print(f"Using estimated duration: {duration}s")

            print(f"Video duration: {duration} seconds")

            # Test if search API is working
            search_api_working = False
            try:
                test_search = self.client.search(
                    index_id=self._index_id, query="*", search_options=["visual"]
                )
                search_api_working = hasattr(test_search, "data")
                print(f"Search API working: {search_api_working}")
            except Exception as e:
                print(f"Search API test failed: {str(e)}")
                search_api_working = False

            # If search API is not working, use fallback
            if not search_api_working:
                print("Search API not working, using fallback analysis...")
                return self.get_frame_by_frame_analysis_fallback(
                    video_id, interval_seconds
                )

            frames = []
            total_frames = 0

            # Analyze video in intervals - use the FULL duration
            for start_time in range(0, int(duration), interval_seconds):
                end_time = min(start_time + interval_seconds, duration)
                print(f"Analyzing {start_time}s to {end_time}s...")

                # Search for visual content in this time interval
                try:
                    # Try different search approaches
                    visual_objects = []
                    text_detected = []

                    # Approach 1: Search for any visual content
                    try:
                        visual_search = self.client.search(
                            index_id=self._index_id,
                            query="*",  # Search for any visual content
                            search_options=["visual"],
                            start_time=start_time,
                            end_time=end_time,
                        )

                        if hasattr(visual_search, "data") and visual_search.data:
                            for result in visual_search.data:
                                if hasattr(result, "start_time") and hasattr(
                                    result, "end_time"
                                ):
                                    visual_objects.append(
                                        {
                                            "label": getattr(
                                                result, "label", "unknown"
                                            ),
                                            "confidence": getattr(
                                                result, "confidence", 0.5
                                            ),
                                            "start": result.start_time,
                                            "end": result.end_time,
                                            "description": getattr(
                                                result, "description", ""
                                            ),
                                        }
                                    )
                    except Exception as e:
                        print(f"  Visual search failed: {str(e)}")

                    # Approach 2: Search for specific common objects
                    if not visual_objects:
                        common_objects = [
                            "person",
                            "car",
                            "building",
                            "text",
                            "screen",
                            "object",
                        ]
                        for obj in common_objects:
                            try:
                                obj_search = self.client.search(
                                    index_id=self._index_id,
                                    query=obj,
                                    search_options=["visual"],
                                    start_time=start_time,
                                    end_time=end_time,
                                )

                                if hasattr(obj_search, "data") and obj_search.data:
                                    for result in obj_search.data:
                                        if hasattr(result, "start_time") and hasattr(
                                            result, "end_time"
                                        ):
                                            visual_objects.append(
                                                {
                                                    "label": obj,
                                                    "confidence": getattr(
                                                        result, "confidence", 0.5
                                                    ),
                                                    "start": result.start_time,
                                                    "end": result.end_time,
                                                    "description": f"Detected {obj}",
                                                }
                                            )
                                    break  # Found something, stop searching
                            except Exception:
                                continue  # Try next object

                    # Approach 3: Search for text specifically
                    try:
                        text_search = self.client.search(
                            index_id=self._index_id,
                            query="text",
                            search_options=["visual"],
                            start_time=start_time,
                            end_time=end_time,
                        )

                        if hasattr(text_search, "data") and text_search.data:
                            for result in text_search.data:
                                if hasattr(result, "text"):
                                    text_detected.append(result.text)
                    except Exception as e:
                        print(f"  Text search failed: {str(e)}")

                    # Create frame analysis
                    frame = {
                        "start_time": start_time,
                        "end_time": end_time,
                        "visual_objects": visual_objects,
                        "text_detected": text_detected,
                        "scene_description": self._generate_scene_description(
                            visual_objects, text_detected
                        ),
                        "dominant_colors": [],  # Could be enhanced with color analysis
                        "audio_analysis": None,  # Could be enhanced with audio analysis
                    }

                    frames.append(frame)
                    total_frames += 1

                except Exception as e:
                    print(
                        f"Warning: Could not analyze interval {start_time}s-{end_time}s: {str(e)}"
                    )
                    # Add empty frame with error description
                    frames.append(
                        {
                            "start_time": start_time,
                            "end_time": end_time,
                            "visual_objects": [],
                            "text_detected": [],
                            "scene_description": f"Analysis failed: {str(e)}",
                            "dominant_colors": [],
                            "audio_analysis": None,
                        }
                    )
                    total_frames += 1

            return {
                "interval_seconds": interval_seconds,
                "total_frames": total_frames,
                "frames": frames,
                "summary": self._generate_frame_analysis_summary(frames),
                "video_duration": duration,
                "analysis_mode": "search_api",
            }

        except Exception as e:
            print(f"Error in frame-by-frame analysis: {str(e)}")
            # Try fallback if main method fails
            try:
                print("Trying fallback analysis...")
                return self.get_frame_by_frame_analysis_fallback(
                    video_id, interval_seconds
                )
            except Exception as fallback_error:
                print(f"Fallback also failed: {str(fallback_error)}")
                raise

    def _generate_scene_description(
        self, visual_objects: List[Dict], text_detected: List[str]
    ) -> str:
        """Generate a description of the scene based on visual objects and text"""
        if not visual_objects and not text_detected:
            return "No visual content detected"

        description_parts = []

        # Add visual objects
        if visual_objects:
            object_counts = {}
            for obj in visual_objects:
                label = obj.get("label", "unknown")
                object_counts[label] = object_counts.get(label, 0) + 1

            object_descriptions = []
            for label, count in object_counts.items():
                if count == 1:
                    object_descriptions.append(f"a {label}")
                else:
                    object_descriptions.append(f"{count} {label}s")

            if object_descriptions:
                description_parts.append(f"Shows {', '.join(object_descriptions)}")

        # Add text content
        if text_detected:
            text_summary = (
                text_detected[0][:50] + "..."
                if len(text_detected[0]) > 50
                else text_detected[0]
            )
            description_parts.append(f"Contains text: '{text_summary}'")

        return (
            ". ".join(description_parts)
            if description_parts
            else "Scene content detected"
        )

    def _generate_frame_analysis_summary(self, frames: List[Dict]) -> str:
        """Generate a summary of the frame-by-frame analysis"""
        if not frames:
            return "No frames analyzed"

        total_objects = sum(len(frame.get("visual_objects", [])) for frame in frames)
        total_text = sum(len(frame.get("text_detected", [])) for frame in frames)

        # Find most common objects
        object_counts = {}
        for frame in frames:
            for obj in frame.get("visual_objects", []):
                label = obj.get("label", "unknown")
                object_counts[label] = object_counts.get(label, 0) + 1

        most_common_objects = sorted(
            object_counts.items(), key=lambda x: x[1], reverse=True
        )[:3]

        summary_parts = [
            f"Analyzed {len(frames)} time intervals",
            f"Detected {total_objects} visual objects",
            f"Found {total_text} text elements",
        ]

        if most_common_objects:
            common_objects_str = ", ".join(
                [f"{label} ({count})" for label, count in most_common_objects]
            )
            summary_parts.append(f"Most common objects: {common_objects_str}")

        return ". ".join(summary_parts)

    def get_frame_by_frame_analysis_fallback(
        self, video_id: str, interval_seconds: int = 5
    ) -> Dict[str, Any]:
        """
        Fallback frame-by-frame analysis using video metadata and basic analysis
        This method doesn't rely on the search API
        """
        try:
            print(
                f"Using fallback frame-by-frame analysis with {interval_seconds}s intervals..."
            )

            # Get video information
            videos = self.client.index.video.list(self._index_id)
            video_info = None
            for video in videos:
                if video.id == video_id:
                    video_info = video
                    break

            if not video_info:
                raise Exception(f"Video {video_id} not found in index")

            # Try to get duration from video info
            duration = None
            for attr in ["duration", "length", "video_duration"]:
                if hasattr(video_info, attr):
                    duration = getattr(video_info, attr)
                    break

            if duration is None:
                print("Warning: Could not determine video duration in fallback mode.")
                print("Using estimated duration for analysis.")
                duration = 300  # Assume 5 minutes as a reasonable default
                print(f"Using estimated duration: {duration}s")

            print(f"Video duration: {duration} seconds")

            frames = []
            total_frames = 0

            # Create basic frame analysis without search API
            for start_time in range(0, int(duration), interval_seconds):
                end_time = min(start_time + interval_seconds, duration)

                # Create a basic frame with placeholder data
                frame = {
                    "start_time": start_time,
                    "end_time": end_time,
                    "visual_objects": [],
                    "text_detected": [],
                    "scene_description": f"Time segment {start_time}s-{end_time}s (basic analysis)",
                    "dominant_colors": [],
                    "audio_analysis": None,
                }

                # Try to get some basic info from video metadata
                if hasattr(video_info, "metadata"):
                    metadata = video_info.metadata
                    if metadata:
                        frame["scene_description"] = (
                            f"Video segment {start_time}s-{end_time}s"
                        )

                frames.append(frame)
                total_frames += 1

            return {
                "interval_seconds": interval_seconds,
                "total_frames": total_frames,
                "frames": frames,
                "summary": f"Basic analysis of {total_frames} time intervals (fallback mode)",
                "video_duration": duration,
                "analysis_mode": "fallback",
            }

        except Exception as e:
            print(f"Error in fallback frame-by-frame analysis: {str(e)}")
            raise

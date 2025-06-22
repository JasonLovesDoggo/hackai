import uuid
from datetime import datetime
from typing import Dict, Any, List
from .models import (
    VideoAnalysisRequest,
    VideoAnalysisResult,
    TranscriptSegment,
    VisualObject,
    SceneAnalysis,
    VideoContext,
    FrameAnalysis,
    TimeBasedAnalysis,
)
from .api_client import TwelveLabsAPIClient


class VideoAnalyzer:
    def __init__(self):
        self.api_client = TwelveLabsAPIClient()

    def analyze_video(
        self, file_path: str, request: VideoAnalysisRequest
    ) -> VideoAnalysisResult:
        """Analyze a video file and return comprehensive results"""
        task_id = str(uuid.uuid4())
        start_time = datetime.now()

        try:
            # Map features to analysis types
            analysis_types = self._map_features_to_analysis_types(request.features)

            # Use the API client to analyze the video
            result = self.api_client.analyze_video_file(file_path, analysis_types)

            # Parse the analysis data into structured format
            parsed_data = self._parse_analysis_data(result["analysis"])

            # Get frame-by-frame analysis if requested
            time_based_analysis = None
            if "frames" in request.features or "visual" in request.features:
                try:
                    frame_analysis_data = self.api_client.get_frame_by_frame_analysis(
                        result["video_id"], interval_seconds=5
                    )
                    time_based_analysis = self._parse_frame_analysis_data(
                        frame_analysis_data
                    )
                except Exception as e:
                    print(f"Warning: Frame-by-frame analysis failed: {str(e)}")

            return VideoAnalysisResult(
                task_id=result["upload"]["task_id"],
                status=result["status"],
                video_metadata=self._extract_metadata(result),
                transcript=parsed_data.get("transcript", []),
                visual_analysis=parsed_data.get("visual_analysis", []),
                scenes=parsed_data.get("scenes", []),
                context=parsed_data.get("context"),
                time_based_analysis=time_based_analysis,
                raw_data=result,
                created_at=start_time,
            )

        except Exception as e:
            return VideoAnalysisResult(
                task_id=task_id,
                status="failed",
                error_message=str(e),
                created_at=start_time,
            )

    def _map_features_to_analysis_types(self, features: List[str]) -> List[str]:
        """Map feature requests to Twelve Labs analysis types"""
        analysis_types = []

        # Map common features to analysis types
        feature_mapping = {
            "transcript": ["gist", "summary"],
            "visual": ["gist", "analysis"],
            "audio": ["gist", "summary"],
            "scenes": ["chapters", "highlights"],
            "summary": ["summary"],
            "chapters": ["chapters"],
            "highlights": ["highlights"],
            "topics": ["gist"],
            "hashtags": ["gist"],
            "analysis": ["analysis"],
        }

        for feature in features:
            if feature in feature_mapping:
                analysis_types.extend(feature_mapping[feature])

        # Remove duplicates and ensure we have at least some analysis
        analysis_types = list(set(analysis_types))
        if not analysis_types:
            analysis_types = ["gist", "summary", "analysis"]

        return analysis_types

    def _extract_metadata(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from the analysis result"""
        metadata = {
            "video_id": result.get("video_id"),
            "task_id": result.get("upload", {}).get("task_id"),
            "upload_status": result.get("upload", {}).get("status"),
            "created_at": result.get("created_at"),
        }

        # Add usage information if available
        usage_info = {}
        for analysis_type, data in result.get("analysis", {}).items():
            if "usage" in data:
                usage_info[analysis_type] = data["usage"]

        if usage_info:
            metadata["usage"] = usage_info

        return metadata

    def _parse_analysis_data(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Twelve Labs analysis results into structured data"""
        parsed = {
            "transcript": [],
            "visual_analysis": [],
            "scenes": [],
            "context": None,
        }

        try:
            # Parse summary data
            if "summary" in analysis_data:
                summary_data = analysis_data["summary"]
                if parsed["context"] is None:
                    try:
                        parsed["context"] = VideoContext()
                    except Exception as e:
                        print(f"Warning: Could not create VideoContext: {str(e)}")
                        parsed["context"] = None
                if parsed["context"]:
                    parsed["context"].content_summary = summary_data.get("summary", "")

            # Parse chapters data
            if "chapters" in analysis_data:
                chapters_data = analysis_data["chapters"]
                parsed["scenes"] = self._parse_chapters_to_scenes(
                    chapters_data.get("chapters", [])
                )

            # Parse highlights data
            if "highlights" in analysis_data:
                highlights_data = analysis_data["highlights"]
                # Add highlights to context
                if parsed["context"] is None:
                    try:
                        parsed["context"] = VideoContext()
                    except Exception as e:
                        print(f"Warning: Could not create VideoContext: {str(e)}")
                        parsed["context"] = None
                if parsed["context"]:
                    parsed["context"].key_insights = self._extract_highlights(
                        highlights_data.get("highlights", [])
                    )

            # Parse open-ended analysis
            if "analysis" in analysis_data:
                analysis_text = analysis_data["analysis"].get("analysis", "")
                if parsed["context"] is None:
                    try:
                        parsed["context"] = VideoContext()
                    except Exception as e:
                        print(f"Warning: Could not create VideoContext: {str(e)}")
                        parsed["context"] = None
                if parsed["context"]:
                    parsed["context"] = self._enhance_context_with_analysis(
                        parsed["context"], analysis_text
                    )

        except Exception as e:
            print(f"Error parsing analysis data: {str(e)}")
            import traceback

            traceback.print_exc()

        return parsed

    def _parse_chapters_to_scenes(
        self, chapters: List[Dict[str, Any]]
    ) -> List[SceneAnalysis]:
        """Convert chapters data to scene analysis"""
        scenes = []
        for chapter in chapters:
            if isinstance(chapter, dict):
                scenes.append(
                    SceneAnalysis(
                        start=chapter.get("start", 0),
                        end=chapter.get("end", 0),
                        description=chapter.get("chapter_title", "")
                        + ": "
                        + chapter.get("chapter_summary", ""),
                        key_elements=[chapter.get("chapter_title", "")],
                        confidence=0.9,  # Default confidence for chapters
                    )
                )
        return scenes

    def _extract_highlights(self, highlights: List[Dict[str, Any]]) -> List[str]:
        """Extract key insights from highlights"""
        insights = []
        for highlight in highlights:
            if isinstance(highlight, dict):
                insights.append(highlight.get("highlight", ""))
        return insights

    def _enhance_context_with_analysis(
        self, context: VideoContext, analysis_text: str
    ) -> VideoContext:
        """Enhance context with open-ended analysis results"""
        try:
            if not context:
                context = VideoContext()

            # Extract additional insights from analysis text
            context.content_summary = (
                analysis_text[:500] + "" if len(analysis_text) > 500 else analysis_text
            )

            # Try to extract target audience from analysis
            if "audience" in analysis_text.lower():
                context.target_audience = self._extract_target_audience(analysis_text)

            # Try to extract sentiment
            context.sentiment = self._analyze_sentiment(analysis_text)

            return context
        except Exception as e:
            print(f"Warning: Could not enhance context with analysis: {str(e)}")
            return context

    def _extract_target_audience(self, analysis_text: str) -> str:
        """Extract target audience from analysis text"""
        text_lower = analysis_text.lower()

        if any(word in text_lower for word in ["beginner", "newcomer", "starter"]):
            return "beginners"
        elif any(word in text_lower for word in ["advanced", "expert", "professional"]):
            return "advanced users"
        elif any(word in text_lower for word in ["student", "learner", "education"]):
            return "students"
        else:
            return "general audience"

    def _analyze_sentiment(self, text: str) -> str:
        """Simple sentiment analysis"""
        text_lower = text.lower()

        positive_words = [
            "good",
            "great",
            "excellent",
            "amazing",
            "wonderful",
            "positive",
        ]
        negative_words = [
            "bad",
            "poor",
            "terrible",
            "awful",
            "negative",
            "disappointing",
        ]

        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)

        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"

    def _parse_transcript(self, transcript_data: Any) -> List[TranscriptSegment]:
        """Parse transcript data into structured segments"""
        segments = []
        try:
            if isinstance(transcript_data, list):
                for segment in transcript_data:
                    if isinstance(segment, dict):
                        segments.append(
                            TranscriptSegment(
                                start=segment.get("start", 0),
                                end=segment.get("end", 0),
                                text=segment.get("text", ""),
                                confidence=segment.get("confidence"),
                            )
                        )
        except Exception as e:
            print(f"Error parsing transcript: {str(e)}")
        return segments

    def _parse_visual_analysis(self, visual_data: Any) -> List[VisualObject]:
        """Parse visual analysis data"""
        objects = []
        try:
            if isinstance(visual_data, list):
                for obj in visual_data:
                    if isinstance(obj, dict):
                        objects.append(
                            VisualObject(
                                label=obj.get("label", ""),
                                confidence=obj.get("confidence", 0),
                                start=obj.get("start", 0),
                                end=obj.get("end", 0),
                                description=obj.get("description"),
                            )
                        )
        except Exception as e:
            print(f"Error parsing visual analysis: {str(e)}")
        return objects

    def _parse_scenes(self, scenes_data: Any) -> List[SceneAnalysis]:
        """Parse scene/chapter data"""
        scenes = []
        try:
            if isinstance(scenes_data, list):
                for scene in scenes_data:
                    if isinstance(scene, dict):
                        scenes.append(
                            SceneAnalysis(
                                start=scene.get("start", 0),
                                end=scene.get("end", 0),
                                description=scene.get("description", ""),
                                key_elements=scene.get("key_elements", []),
                                confidence=scene.get("confidence"),
                            )
                        )
        except Exception as e:
            print(f"Error parsing scenes: {str(e)}")
        return scenes

    def _generate_context(
        self,
        transcript: List[TranscriptSegment],
        visual_objects: List[VisualObject],
        scenes: List[SceneAnalysis],
        raw_data: Any,
    ) -> VideoContext:
        """Generate context from the analysis data"""
        try:
            # Get full transcript text
            full_text = " ".join([seg.text for seg in transcript])

            # Extract main topics from transcript
            main_topics = self._extract_main_topics(full_text)

            # Determine content type
            content_type = self._determine_content_type(full_text, visual_objects)

            # Get duration from scenes or transcript
            duration = None
            if scenes:
                duration = max([scene.end for scene in scenes])
            elif transcript:
                duration = max([seg.end for seg in transcript])

            # Create content summary
            content_summary = self._create_content_summary(
                full_text, visual_objects, scenes
            )

            return VideoContext(
                content_summary=content_summary,
                main_topics=main_topics,
                content_type=content_type,
                duration=duration,
                language=None,  # Could be detected from transcript
            )

        except Exception as e:
            print(f"Error generating context: {str(e)}")
            return VideoContext(
                content_summary="Analysis data available",
                main_topics=[],
                content_type="unknown",
            )

    def _extract_main_topics(self, text: str) -> List[str]:
        """Extract main topics from text"""
        # Simple keyword extraction
        words = text.lower().split()
        word_freq = {}
        common_words = {
            "the",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "can",
            "this",
            "that",
            "these",
            "those",
            "a",
            "an",
        }

        for word in words:
            if word not in common_words and len(word) > 3:
                word_freq[word] = word_freq.get(word, 0) + 1

        # Return top 5 most frequent words
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for (word,) in sorted_words[:5]]

    def _determine_content_type(
        self, text: str, visual_objects: List[VisualObject]
    ) -> str:
        """Determine content type from text and visual objects"""
        text_lower = text.lower()

        if any(
            word in text_lower
            for word in ["tutorial", "how to", "step by step", "guide"]
        ):
            return "tutorial"
        elif any(
            word in text_lower for word in ["news", "breaking", "update", "report"]
        ):
            return "news"
        elif any(word in text_lower for word in ["interview", "question", "answer"]):
            return "interview"
        elif any(
            word in text_lower for word in ["funny", "joke", "entertainment", "comedy"]
        ):
            return "entertainment"
        else:
            return "general"

    def _create_content_summary(
        self, text: str, visual_objects: List[VisualObject], scenes: List[SceneAnalysis]
    ) -> str:
        """Create a summary of the video content"""
        summary_parts = []

        # Add transcript summary if available
        if text:
            words = text.split()
            if len(words) > 50:
                summary_parts.append(f"Contains {len(words)} words of spoken content")
            else:
                summary_parts.append(f"Contains spoken content: {text[:200]}...")

        # Add visual content summary
        if visual_objects:
            unique_objects = list(set([obj.label for obj in visual_objects]))
            summary_parts.append(f"Visual elements: {', '.join(unique_objects[:5])}")

        # Add scene summary
        if scenes:
            summary_parts.append(f"Contains {len(scenes)} scenes/chapters")

        return ". ".join(summary_parts) if summary_parts else "Video analysis completed"

    def _parse_frame_analysis_data(
        self, frame_analysis_data: Dict[str, Any]
    ) -> TimeBasedAnalysis:
        """Parse frame-by-frame analysis data into TimeBasedAnalysis model"""
        try:
            frames = []

            for frame_data in frame_analysis_data.get("frames", []):
                # Parse visual objects
                visual_objects = []
                for obj_data in frame_data.get("visual_objects", []):
                    visual_objects.append(
                        VisualObject(
                            label=obj_data.get("label", ""),
                            confidence=obj_data.get("confidence", 0.0),
                            start=obj_data.get("start", 0.0),
                            end=obj_data.get("end", 0.0),
                            description=obj_data.get("description", ""),
                        )
                    )

                # Create frame analysis
                frame = FrameAnalysis(
                    start_time=frame_data.get("start_time", 0.0),
                    end_time=frame_data.get("end_time", 0.0),
                    visual_objects=visual_objects,
                    scene_description=frame_data.get("scene_description", ""),
                    dominant_colors=frame_data.get("dominant_colors", []),
                    text_detected=frame_data.get("text_detected", []),
                    audio_analysis=frame_data.get("audio_analysis"),
                )
                frames.append(frame)

            return TimeBasedAnalysis(
                interval_seconds=frame_analysis_data.get("interval_seconds", 5),
                total_frames=frame_analysis_data.get("total_frames", len(frames)),
                frames=frames,
                summary=frame_analysis_data.get("summary", ""),
            )

        except Exception as e:
            print(f"Error parsing frame analysis data: {str(e)}")
            return TimeBasedAnalysis(
                interval_seconds=5,
                total_frames=0,
                frames=[],
                summary="Frame analysis parsing failed",
            )

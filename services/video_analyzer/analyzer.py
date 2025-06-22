import uuid
import json
from datetime import datetime
from typing import Dict, Any, List
from .models import (
    VideoAnalysisRequest, 
    VideoAnalysisResult, 
    TranscriptSegment, 
    VisualObject, 
    AudioAnalysis, 
    SceneAnalysis, 
    VideoInsights
)
from .api_client import TwelveLabsAPIClient

class VideoAnalyzer:
    def __init__(self):
        self.api_client = TwelveLabsAPIClient()

    def analyze_video(self, file_path: str, request: VideoAnalysisRequest) -> VideoAnalysisResult:
        """Analyze a video file and return comprehensive results"""
        task_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        try:
            # Use the API client to analyze the video
            result = self.api_client.analyze_video_file(file_path, request.features)
            
            # Parse the raw data into structured format
            parsed_data = self._parse_analysis_data(result["result"])
            
            return VideoAnalysisResult(
                task_id=result["task_id"],
                status=result["status"],
                video_metadata=parsed_data.get("metadata", {}),
                transcript=parsed_data.get("transcript", []),
                visual_analysis=parsed_data.get("visual_analysis", []),
                audio_analysis=parsed_data.get("audio_analysis"),
                scenes=parsed_data.get("scenes", []),
                insights=parsed_data.get("insights"),
                raw_data=result["result"],
                created_at=start_time
            )
            
        except Exception as e:
            return VideoAnalysisResult(
                task_id=task_id,
                status="failed",
                error_message=str(e),
                created_at=start_time
            )

    def _parse_analysis_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse raw Twelve Labs API response into structured data"""
        parsed = {
            "metadata": {},
            "transcript": [],
            "visual_analysis": [],
            "audio_analysis": None,
            "scenes": [],
            "insights": None
        }
        
        try:
            # Extract basic metadata
            if hasattr(raw_data, 'id'):
                parsed["metadata"]["task_id"] = raw_data.id
            if hasattr(raw_data, 'created_at'):
                parsed["metadata"]["created_at"] = raw_data.created_at
            
            # Extract transcript if available
            if hasattr(raw_data, 'transcript') and raw_data.transcript:
                parsed["transcript"] = self._parse_transcript(raw_data.transcript)
            
            # Extract visual analysis if available
            if hasattr(raw_data, 'visual') and raw_data.visual:
                parsed["visual_analysis"] = self._parse_visual_analysis(raw_data.visual)
            
            # Extract audio analysis
            parsed["audio_analysis"] = self._extract_audio_analysis(raw_data)
            
            # Extract scenes/chapters
            if hasattr(raw_data, 'scenes') and raw_data.scenes:
                parsed["scenes"] = self._parse_scenes(raw_data.scenes)
            
            # Generate insights
            parsed["insights"] = self._generate_insights(
                parsed["transcript"], 
                parsed["visual_analysis"], 
                parsed["audio_analysis"]
            )
            
        except Exception as e:
            print(f"Error parsing analysis data: {str(e)}")
        
        return parsed

    def _parse_transcript(self, transcript_data: Any) -> List[TranscriptSegment]:
        """Parse transcript data into structured segments"""
        segments = []
        try:
            if isinstance(transcript_data, list):
                for segment in transcript_data:
                    if isinstance(segment, dict):
                        segments.append(TranscriptSegment(
                            start=segment.get('start', 0),
                            end=segment.get('end', 0),
                            text=segment.get('text', ''),
                            confidence=segment.get('confidence')
                        ))
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
                        objects.append(VisualObject(
                            label=obj.get('label', ''),
                            confidence=obj.get('confidence', 0),
                            start=obj.get('start', 0),
                            end=obj.get('end', 0),
                            description=obj.get('description')
                        ))
        except Exception as e:
            print(f"Error parsing visual analysis: {str(e)}")
        return objects

    def _extract_audio_analysis(self, raw_data: Any) -> AudioAnalysis:
        """Extract audio analysis from raw data"""
        try:
            # Check if there's speech in the transcript
            has_speech = False
            if hasattr(raw_data, 'transcript') and raw_data.transcript:
                has_speech = len(raw_data.transcript) > 0
            
            return AudioAnalysis(
                speech_detected=has_speech,
                music_detected=None,  # Would need additional audio analysis
                background_noise=None,
                audio_quality=None
            )
        except Exception as e:
            print(f"Error extracting audio analysis: {str(e)}")
            return AudioAnalysis(speech_detected=False)

    def _parse_scenes(self, scenes_data: Any) -> List[SceneAnalysis]:
        """Parse scene/chapter data"""
        scenes = []
        try:
            if isinstance(scenes_data, list):
                for scene in scenes_data:
                    if isinstance(scene, dict):
                        scenes.append(SceneAnalysis(
                            start=scene.get('start', 0),
                            end=scene.get('end', 0),
                            description=scene.get('description', ''),
                            key_elements=scene.get('key_elements', []),
                            confidence=scene.get('confidence')
                        ))
        except Exception as e:
            print(f"Error parsing scenes: {str(e)}")
        return scenes

    def _generate_insights(self, transcript: List[TranscriptSegment], 
                          visual_objects: List[VisualObject], 
                          audio_analysis: AudioAnalysis) -> VideoInsights:
        """Generate actionable insights from the analysis"""
        try:
            # Analyze content type based on transcript and visual content
            content_type = self._determine_content_type(transcript, visual_objects)
            
            # Extract key topics from transcript
            key_topics = self._extract_key_topics(transcript)
            
            # Determine target audience
            target_audience = self._determine_target_audience(transcript, visual_objects)
            
            # Analyze sentiment
            sentiment = self._analyze_sentiment(transcript)
            
            # Find engagement hooks
            engagement_hooks = self._find_engagement_hooks(transcript, visual_objects)
            
            # Generate improvement suggestions
            improvement_suggestions = self._generate_improvement_suggestions(
                transcript, visual_objects, audio_analysis
            )
            
            return VideoInsights(
                content_type=content_type,
                target_audience=target_audience,
                key_topics=key_topics,
                sentiment=sentiment,
                engagement_hooks=engagement_hooks,
                improvement_suggestions=improvement_suggestions
            )
            
        except Exception as e:
            print(f"Error generating insights: {str(e)}")
            return VideoInsights(content_type="unknown", key_topics=[])

    def _determine_content_type(self, transcript: List[TranscriptSegment], 
                               visual_objects: List[VisualObject]) -> str:
        """Determine the type of content based on analysis"""
        # Simple heuristics - can be enhanced with ML
        text = " ".join([seg.text.lower() for seg in transcript])
        
        if any(word in text for word in ["tutorial", "how to", "step by step", "guide"]):
            return "tutorial"
        elif any(word in text for word in ["news", "breaking", "update", "report"]):
            return "news"
        elif any(word in text for word in ["interview", "question", "answer"]):
            return "interview"
        elif any(word in text for word in ["funny", "joke", "entertainment", "comedy"]):
            return "entertainment"
        else:
            return "general"

    def _extract_key_topics(self, transcript: List[TranscriptSegment]) -> List[str]:
        """Extract key topics from transcript"""
        # Simple keyword extraction - can be enhanced with NLP
        text = " ".join([seg.text.lower() for seg in transcript])
        common_words = ["the", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"]
        
        words = text.split()
        word_freq = {}
        for word in words:
            if word not in common_words and len(word) > 3:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Return top 5 most frequent words as topics
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:5]]

    def _determine_target_audience(self, transcript: List[TranscriptSegment], 
                                  visual_objects: List[VisualObject]) -> str:
        """Determine target audience"""
        # Simple heuristics
        text = " ".join([seg.text.lower() for seg in transcript])
        
        if any(word in text for word in ["kids", "children", "family"]):
            return "family"
        elif any(word in text for word in ["professional", "business", "corporate"]):
            return "professional"
        elif any(word in text for word in ["student", "education", "learning"]):
            return "students"
        else:
            return "general"

    def _analyze_sentiment(self, transcript: List[TranscriptSegment]) -> str:
        """Analyze sentiment of the content"""
        # Simple sentiment analysis - can be enhanced with proper NLP
        text = " ".join([seg.text.lower() for seg in transcript])
        
        positive_words = ["good", "great", "excellent", "amazing", "wonderful", "love", "like"]
        negative_words = ["bad", "terrible", "awful", "hate", "dislike", "problem", "issue"]
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"

    def _find_engagement_hooks(self, transcript: List[TranscriptSegment], 
                              visual_objects: List[VisualObject]) -> List[str]:
        """Find potential engagement hooks in the content"""
        hooks = []
        
        # Look for questions in transcript
        for segment in transcript:
            if "?" in segment.text:
                hooks.append(f"Question at {segment.start}s: {segment.text}")
        
        # Look for visual highlights
        for obj in visual_objects:
            if obj.confidence > 0.8:  # High confidence objects
                hooks.append(f"Visual highlight at {obj.start}s: {obj.label}")
        
        return hooks[:5]  # Return top 5 hooks

    def _generate_improvement_suggestions(self, transcript: List[TranscriptSegment], 
                                        visual_objects: List[VisualObject], 
                                        audio_analysis: AudioAnalysis) -> List[str]:
        """Generate improvement suggestions"""
        suggestions = []
        
        # Check transcript length
        if len(transcript) < 5:
            suggestions.append("Consider adding more spoken content for better engagement")
        
        # Check visual content
        if len(visual_objects) < 3:
            suggestions.append("Add more visual elements to keep viewers engaged")
        
        # Check audio quality
        if not audio_analysis.speech_detected:
            suggestions.append("Consider adding voice-over or narration")
        
        return suggestions
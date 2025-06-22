#!/usr/bin/env python3
"""
Test script for comprehensive video analysis
"""

import asyncio
import aiofiles
import json
from pathlib import Path
from services.video_analyzer.analyzer import VideoAnalyzer
from services.video_analyzer.models import VideoAnalysisRequest

async def test_comprehensive_analysis():
    """Test the comprehensive video analysis"""
    
    # Check if we have a test video file
    test_video_path = "test_video.mp4"  # You can replace this with your test video
    
    if not Path(test_video_path).exists():
        print(f"❌ Test video file '{test_video_path}' not found!")
        print("Please upload a video file to test the analysis.")
        print("\nYou can:")
        print("1. Use the FastAPI docs at http://localhost:8000/docs")
        print("2. Use curl to upload a video:")
        print(f"   curl -X POST 'http://localhost:8000/video-analysis/analyze' \\")
        print(f"        -H 'accept: application/json' \\")
        print(f"        -H 'Content-Type: multipart/form-data' \\")
        print(f"        -F 'file=@your_video.mp4' \\")
        print(f"        -F 'features=visual,audio'")
        return
    
    print("🎬 Testing Comprehensive Video Analysis")
    print("=" * 50)
    
    try:
        # Create analyzer
        analyzer = VideoAnalyzer()
        
        # Create request with both visual and audio features
        request = VideoAnalysisRequest(features=["visual", "audio"])
        
        print(f"📹 Analyzing video: {test_video_path}")
        print(f"🔧 Features: {request.features}")
        print("\n⏳ Processing... (this may take a few minutes)")
        
        # Analyze the video
        result = analyzer.analyze_video(test_video_path, request)
        
        print(f"\n✅ Analysis completed!")
        print(f"📊 Status: {result.status}")
        print(f"🆔 Task ID: {result.task_id}")
        
        if result.error_message:
            print(f"❌ Error: {result.error_message}")
            return
        
        # Display results
        print("\n" + "=" * 50)
        print("📋 ANALYSIS RESULTS")
        print("=" * 50)
        
        # Transcript
        if result.transcript:
            print(f"\n🗣️  TRANSCRIPT ({len(result.transcript)} segments):")
            print("-" * 30)
            for i, segment in enumerate(result.transcript[:5]):  # Show first 5 segments
                print(f"{i+1}. [{segment.start:.1f}s - {segment.end:.1f}s] {segment.text}")
            if len(result.transcript) > 5:
                print(f"... and {len(result.transcript) - 5} more segments")
        
        # Visual Analysis
        if result.visual_analysis:
            print(f"\n👁️  VISUAL OBJECTS ({len(result.visual_analysis)} detected):")
            print("-" * 30)
            for i, obj in enumerate(result.visual_analysis[:10]):  # Show first 10 objects
                print(f"{i+1}. {obj.label} (confidence: {obj.confidence:.2f}) at {obj.start:.1f}s")
            if len(result.visual_analysis) > 10:
                print(f"... and {len(result.visual_analysis) - 10} more objects")
        
        # Audio Analysis
        if result.audio_analysis:
            print(f"\n🔊 AUDIO ANALYSIS:")
            print("-" * 30)
            print(f"Speech detected: {result.audio_analysis.speech_detected}")
            if result.audio_analysis.music_detected is not None:
                print(f"Music detected: {result.audio_analysis.music_detected}")
        
        # Scenes
        if result.scenes:
            print(f"\n🎬 SCENES ({len(result.scenes)} detected):")
            print("-" * 30)
            for i, scene in enumerate(result.scenes):
                print(f"{i+1}. [{scene.start:.1f}s - {scene.end:.1f}s] {scene.description}")
        
        # Insights
        if result.insights:
            print(f"\n💡 ACTIONABLE INSIGHTS:")
            print("-" * 30)
            print(f"Content Type: {result.insights.content_type}")
            if result.insights.target_audience:
                print(f"Target Audience: {result.insights.target_audience}")
            if result.insights.sentiment:
                print(f"Sentiment: {result.insights.sentiment}")
            
            if result.insights.key_topics:
                print(f"Key Topics: {', '.join(result.insights.key_topics)}")
            
            if result.insights.engagement_hooks:
                print(f"\n🎯 Engagement Hooks:")
                for hook in result.insights.engagement_hooks[:3]:
                    print(f"  • {hook}")
            
            if result.insights.improvement_suggestions:
                print(f"\n💡 Improvement Suggestions:")
                for suggestion in result.insights.improvement_suggestions:
                    print(f"  • {suggestion}")
        
        # Save detailed results to file
        output_file = "analysis_results.json"
        with open(output_file, 'w') as f:
            json.dump(result.dict(), f, indent=2, default=str)
        
        print(f"\n💾 Detailed results saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_comprehensive_analysis()) 
# Video Analysis Service

A comprehensive video analysis service using the Twelve Labs API that provides detailed insights from video content including transcripts, visual analysis, and actionable recommendations.

## Features

### 🎯 Core Analysis Capabilities

- **Transcript Generation**: Accurate speech-to-text with timing information
- **Visual Object Detection**: Identify objects, scenes, and visual elements
- **Audio Analysis**: Speech detection and audio quality assessment
- **Scene Analysis**: Automatic scene/chapter detection and description
- **Content Insights**: AI-powered analysis of content type, audience, and sentiment

### 💡 Actionable Insights

- **Content Classification**: Automatically categorize videos (tutorial, news, entertainment, etc.)
- **Target Audience**: Identify the intended audience for the content
- **Key Topics**: Extract main themes and subjects discussed
- **Sentiment Analysis**: Determine the emotional tone of the content
- **Engagement Hooks**: Identify moments that could engage viewers
- **Improvement Suggestions**: Get recommendations for better content

## API Endpoints

### POST `/video-analysis/analyze`

Upload and analyze a video file.

**Parameters:**
- `file`: Video file (MP4, MOV, AVI, etc.)
- `features`: Comma-separated list of features (default: "visual,audio")

**Response:**
```json
{
  "task_id": "uuid",
  "status": "completed",
  "video_metadata": {},
  "transcript": [
    {
      "start": 0.0,
      "end": 2.5,
      "text": "Hello, welcome to this tutorial...",
      "confidence": 0.95
    }
  ],
  "visual_analysis": [
    {
      "label": "person",
      "confidence": 0.92,
      "start": 0.0,
      "end": 5.0,
      "description": "A person speaking to camera"
    }
  ],
  "audio_analysis": {
    "speech_detected": true,
    "music_detected": false,
    "background_noise": null,
    "audio_quality": null
  },
  "scenes": [
    {
      "start": 0.0,
      "end": 30.0,
      "description": "Introduction scene",
      "key_elements": ["person", "camera"],
      "confidence": 0.88
    }
  ],
  "insights": {
    "content_type": "tutorial",
    "target_audience": "general",
    "key_topics": ["tutorial", "guide", "learning"],
    "sentiment": "positive",
    "engagement_hooks": [
      "Question at 15.2s: What do you think about this approach?"
    ],
    "improvement_suggestions": [
      "Consider adding more visual elements to keep viewers engaged"
    ]
  },
  "created_at": "2024-01-01T12:00:00"
}
```

### GET `/video-analysis/features`

Get available analysis features.

**Response:**
```json
{
  "available_features": ["visual", "audio"],
  "description": "These features are supported by the Twelve Labs API"
}
```

### GET `/video-analysis/health`

Health check endpoint.

## Usage Examples

### Using FastAPI Docs

1. Start the server: `uvicorn main:app --reload`
2. Open http://localhost:8000/docs
3. Navigate to the `/video-analysis/analyze` endpoint
4. Upload a video file and click "Execute"

### Using cURL

```bash
curl -X POST 'http://localhost:8000/video-analysis/analyze' \
     -H 'accept: application/json' \
     -H 'Content-Type: multipart/form-data' \
     -F 'file=@your_video.mp4' \
     -F 'features=visual,audio'
```

### Using Python

```python
import requests

url = "http://localhost:8000/video-analysis/analyze"
files = {"file": open("your_video.mp4", "rb")}
data = {"features": "visual,audio"}

response = requests.post(url, files=files, data=data)
result = response.json()

# Access transcript
for segment in result["transcript"]:
    print(f"[{segment['start']:.1f}s] {segment['text']}")

# Access insights
insights = result["insights"]
print(f"Content Type: {insights['content_type']}")
print(f"Key Topics: {', '.join(insights['key_topics'])}")
```

## Testing

### Run the Test Script

```bash
python test_comprehensive_analysis.py
```

This will:
1. Check for a test video file (`test_video.mp4`)
2. Run comprehensive analysis
3. Display formatted results
4. Save detailed results to `analysis_results.json`

### Manual Testing

1. Place a video file in the project root
2. Update the `test_video_path` in `test_comprehensive_analysis.py`
3. Run the test script

## Configuration

### Environment Variables

Set your Twelve Labs API key:

```bash
export TWELVE_LABS_API_KEY="your_api_key_here"
```

Or create a `.env` file:

```
TWELVE_LABS_API_KEY=your_api_key_here
```

## Supported Video Formats

- MP4
- MOV
- AVI
- WebM
- And other common video formats

## Analysis Features

### Visual Analysis (`visual`)
- Object detection and recognition
- Scene understanding
- Visual element identification
- Confidence scoring for detections

### Audio Analysis (`audio`)
- Speech-to-text transcription
- Audio quality assessment
- Speech detection
- Timing information for all audio elements

## Content Insights

The service automatically generates insights including:

### Content Classification
- **Tutorial**: How-to guides, educational content
- **News**: News reports, updates, breaking news
- **Interview**: Q&A sessions, conversations
- **Entertainment**: Comedy, fun content
- **General**: Other content types

### Target Audience
- **Family**: Content suitable for all ages
- **Professional**: Business, corporate content
- **Students**: Educational, learning content
- **General**: Broad audience content

### Sentiment Analysis
- **Positive**: Upbeat, encouraging content
- **Negative**: Critical, concerning content
- **Neutral**: Balanced, factual content

## Error Handling

The service provides detailed error messages for:
- Invalid file formats
- API authentication issues
- Processing failures
- Network connectivity problems

## Performance Notes

- Analysis time depends on video length and complexity
- Longer videos may take several minutes to process
- The service uses async processing for better performance
- Results are cached to avoid re-processing

## Dependencies

- FastAPI
- Twelve Labs SDK
- Python 3.8+
- Required packages listed in `pyproject.toml` 
# HackAI - Creator Monetization Backend

A comprehensive AI-powered backend system that helps YouTube creators analyze their channels and discover monetization opportunities.

## Features

- **Channel Health Analysis** - Deep analytics on subscriber growth, engagement, and content performance
- **Video Intelligence** - AI-powered analysis of your top performing content
- **Monetization Opportunities** - Discover affiliate marketing and sponsorship potential
- **Revenue Playbooks** - Personalized 30-day monetization strategies
- **AI Coach** - Contextual AI assistant that knows your channel inside and out

## Quick Start

1. **Clone the repository**
```bash
git clone https://github.com/JasonLovesDoggo/hackai-boi/
cd hackai-boi
```

2. **Install dependencies**
```bash
uv sync
```

3. **Set up environment variables**
```bash
cp .env.example .env
# Add your API keys to .env
```

4. **Run the server**
```bash
uv run uvicorn main:app --reload
```

5. **Visit the API docs**
Open http://localhost:8000/docs in your browser

## API Endpoints

### YouTube Analysis
- `GET /api/youtube/channel/health?url=@username` - Complete channel analysis

### Video Analysis
- `POST /api/video-analyzer/analyze` - Upload and analyze video content
- `GET /api/video-analyzer/status/{task_id}` - Check analysis status
- `POST /api/video-analyzer/summary` - Generate video summaries

### Monetization
- `POST /api/video-monetization/analyze` - Full monetization workflow analysis
- `GET /api/video-monetization/status/{task_id}` - Check monetization status
- `GET /api/revenue-playbook/generate?channel_url=@username` - Personalized revenue strategies

### Affiliate Discovery
- `GET /api/affiliate-discovery/search?keywords=product` - Find affiliate opportunities
- `GET /api/affiliate-discovery/overrides` - Get affiliate overrides
- `POST /api/affiliate-discovery/overrides` - Add affiliate overrides

### AI Assistant
- `POST /api/groq/chat` - Full GROQ chat completions API
- `POST /api/groq/simple` - Quick AI responses
- `POST /api/groq/contextual` - AI coach with your channel data

### Cache Management
- `GET /api/cache/stats` - View cache statistics
- `DELETE /api/cache/clear` - Clear all cache entries

## Required API Keys

Add these to your `.env` file:

```bash
YOUTUBE_API_KEY=your_youtube_api_key
GROQ_API_KEY=your_groq_api_key
TWELVELABS_API_KEY=your_twelvelabs_api_key
```

## Tech Stack

Built with FastAPI, GROQ AI, TwelveLabs video analysis, and YouTube Data API for lightning-fast performance and intelligent insights.

## Example Usage

```bash
# Analyze a YouTube channel
curl "http://localhost:8000/api/youtube/channel/health?url=@Seytonic"

# Get personalized revenue strategies
curl "http://localhost:8000/api/revenue-playbook/generate?channel_url=@Seytonic"

# Chat with your AI coach
curl -X POST "http://localhost:8000/api/groq/contextual" \
  -H "Content-Type: application/json" \
  -d '{"msg": "How can I improve my monetization?", "channel_url": "@Seytonic"}'
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details
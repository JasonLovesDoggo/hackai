from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from services.affiliate_discovery.groq_client import GroqClient
from services.youtube_scraper.scraper import YouTubeScraper
from utils.simple_cache import simple_cache
from typing import Dict, List
import logging

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/groq", tags=["GROQ Passthrough"])

groq_client = GroqClient()
youtube_scraper = YouTubeScraper()


def _format_video_list(videos):
    """Format video list for context"""
    if not videos:
        return "No videos available"
    
    formatted = []
    for i, video in enumerate(videos, 1):
        formatted.append(f"  {i}. '{video.get('title', 'Unknown')}' - {video.get('views', 0):,} views, {video.get('likes', 0):,} likes, {video.get('engagement_rate', 0):.1f}% engagement")
    
    return "\n".join(formatted)


class GroqRequest(BaseModel):
    messages: List[Dict[str, str]]
    model: str = "llama-3.3-70b-versatile"
    temperature: float = 0.7
    max_tokens: int = 1000


class SimpleGroqRequest(BaseModel):
    msg: str


class ContextualGroqRequest(BaseModel):
    msg: str
    channel_url: str


@router.post("/chat")
async def groq_chat(request: GroqRequest):
    """
    Direct passthrough to GROQ chat completions API
    """
    try:
        import httpx

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{groq_client.base_url}/chat/completions",
                headers=groq_client.headers,
                json={
                    "model": request.model,
                    "messages": request.messages,
                    "temperature": request.temperature,
                    "max_tokens": request.max_tokens,
                },
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"GROQ API error: {response.status_code}")
                raise HTTPException(
                    status_code=response.status_code, detail="GROQ API error"
                )

    except Exception as e:
        logger.error(f"Error calling GROQ: {e}")
        raise HTTPException(status_code=500, detail="Failed to call GROQ API")


@router.post("/simple")
async def groq_simple(request: SimpleGroqRequest):
    """
    Simple GROQ call - just send a message and get response using 8B model
    """
    try:
        import httpx

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{groq_client.base_url}/chat/completions",
                headers=groq_client.headers,
                json={
                    "model": "llama-3.1-8b-instant",
                    "messages": [{"role": "user", "content": request.msg}],
                    "temperature": 0.7,
                    "max_tokens": 1000,
                },
            )

            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                return {"response": content}
            else:
                logger.error(f"GROQ API error: {response.status_code}")
                raise HTTPException(
                    status_code=response.status_code, detail="GROQ API error"
                )

    except Exception as e:
        logger.error(f"Error calling GROQ: {e}")
        raise HTTPException(status_code=500, detail="Failed to call GROQ API")


@router.post("/contextual")
async def groq_contextual(request: ContextualGroqRequest):
    """
    Contextual GROQ call with YouTube channel health data
    """
    try:
        # Get cached channel health data first
        cached_health = simple_cache.get("groq_health", channel_url=request.channel_url)
        
        if cached_health:
            logger.info("Using cached channel health data")
            channel_data = cached_health
        else:
            logger.info("Fetching fresh channel health data")
            channel_data = await youtube_scraper.get_channel_health(request.channel_url)
            # Cache for 1 hour
            simple_cache.set("groq_health", channel_data, 3600, channel_url=request.channel_url)
        
        # Build context from channel data
        channel_info = channel_data.get("channel", {})
        content_analysis = channel_data.get("content_analysis", {})
        health_analysis = channel_data.get("health_analysis", {})
        video_analysis = channel_data.get("video_analysis", {})
        
        # Get top videos data
        recent_videos = video_analysis.get("recent_top_5", [])
        popular_videos = video_analysis.get("most_popular_5", [])
        
        # Build detailed context
        context = f"""
CHANNEL OVERVIEW:
- Channel Name: {channel_info.get('name', 'Unknown')}
- Channel Handle: {channel_info.get('handle', 'N/A')}
- Subscribers: {channel_info.get('subscribers', 0):,}
- Total Videos: {channel_info.get('total_videos', 0)}
- Channel Age: {channel_info.get('channel_age_days', 0)} days
- Description: {channel_info.get('description', 'No description')[:200]}...

CONTENT ANALYSIS:
- Content Type: {content_analysis.get('content_type', 'general')}
- Upload Style: {content_analysis.get('upload_style', 'irregular')}
- Upload Frequency: {content_analysis.get('upload_frequency', 'unknown')}
- Performance Tier: {content_analysis.get('performance_tier', 'unknown')}
- Video Style: {content_analysis.get('video_style', 'unknown')}
- Content Focus: {content_analysis.get('content_focus', 'unknown')}

HEALTH METRICS:
- Overall Health Score: {health_analysis.get('health_score', 50)}/100
- Health Rating: {health_analysis.get('health_rating', 'Unknown')}
- Monetization Ready: {health_analysis.get('monetization_ready', False)}
- Subscriber Milestone: {health_analysis.get('subscriber_milestone', 'Unknown')}
- Revenue Streams Ready: {', '.join(health_analysis.get('revenue_streams_ready', []))}
- Growth Trend: {health_analysis.get('growth_trend', 'unknown')}

RECENT TOP 5 VIDEOS:
{_format_video_list(recent_videos)}

MOST POPULAR 5 VIDEOS:
{_format_video_list(popular_videos)}

VIDEO INSIGHTS:
- Average Views (Recent): {video_analysis.get('insights', {}).get('avg_views_recent', 0):,}
- Average Views (Popular): {video_analysis.get('insights', {}).get('avg_views_popular', 0):,}
- Performance Comparison: {video_analysis.get('insights', {}).get('performance_comparison', 'unknown')}
- Engagement Trend: {video_analysis.get('insights', {}).get('engagement_trend', 'unknown')}
"""
        
        import httpx
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{groq_client.base_url}/chat/completions",
                headers=groq_client.headers,
                json={
                    "model": "llama-3.1-8b-instant",
                    "messages": [
                        {
                            "role": "system",
                            "content": f"You are {channel_info.get('name', 'this creator')}'s personal YouTube monetization coach! You know everything about their channel and you genuinely want them to succeed and be happy. You're excited about their {content_analysis.get('content_type', 'amazing')} content and you believe in their potential. Be encouraging, enthusiastic, and personal - like you're talking to a close friend who you're rooting for.\n\nYou have complete insight into {channel_info.get('name', 'their')}'s channel performance and you use this data to give them the most helpful, tailored advice possible. Always reference their specific situation and celebrate their wins while helping them overcome challenges.\n\nYour creator's current stats: {context}\n\nRemember: You know this creator personally, you believe in them completely, and you want to see them thrive both financially and creatively. Be their biggest supporter while giving them actionable, data-driven advice!"
                        },
                        {
                            "role": "user",
                            "content": request.msg
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1500
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                return {"response": content, "context_used": True}
            else:
                logger.error(f"GROQ API error: {response.status_code}")
                raise HTTPException(status_code=response.status_code, detail="GROQ API error")
                
    except Exception as e:
        logger.error(f"Error calling GROQ contextual: {e}")
        raise HTTPException(status_code=500, detail="Failed to call GROQ API")
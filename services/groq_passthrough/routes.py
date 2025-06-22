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
        
        context = f"""
Channel Context:
- Name: {channel_info.get('name', 'Unknown')}
- Subscribers: {channel_info.get('subscribers', 0):,}
- Content Type: {content_analysis.get('content_type', 'general')}
- Upload Style: {content_analysis.get('upload_style', 'irregular')}
- Health Score: {health_analysis.get('health_score', 50)}/100
- Monetization Ready: {health_analysis.get('monetization_ready', False)}
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
                            "content": f"You are an AI chatbot designed to help creative content creators monetize their YouTube channels and learn how to grow their audience. You have access to detailed channel analytics data that includes subscriber count, content type classification, upload patterns, channel health scores, and monetization readiness indicators. Use this data to provide personalized, actionable advice for revenue generation, audience growth, and content strategy optimization.\n\nChannel Analytics Data: {context}\n\nThis data represents the current state of the creator's channel including their subscriber base, content categorization, posting frequency, overall channel health (0-100 score), and whether they meet basic monetization requirements. Use these insights to tailor your responses specifically to their channel's current situation and growth potential."
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
        
        context = f"""
Channel Context:
- Name: {channel_info.get('name', 'Unknown')}
- Subscribers: {channel_info.get('subscribers', 0):,}
- Content Type: {content_analysis.get('content_type', 'general')}
- Upload Style: {content_analysis.get('upload_style', 'irregular')}
- Health Score: {health_analysis.get('health_score', 50)}/100
- Monetization Ready: {health_analysis.get('monetization_ready', False)}
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
                            "content": f"You are an AI chatbot designed to help creative content creators monetize their YouTube channels and learn how to grow their audience. You have access to detailed channel analytics data that includes subscriber count, content type classification, upload patterns, channel health scores, and monetization readiness indicators. Use this data to provide personalized, actionable advice for revenue generation, audience growth, and content strategy optimization.\n\nChannel Analytics Data: {context}\n\nThis data represents the current state of the creator's channel including their subscriber base, content categorization, posting frequency, overall channel health (0-100 score), and whether they meet basic monetization requirements. Use these insights to tailor your responses specifically to their channel's current situation and growth potential."
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

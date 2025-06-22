from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.affiliate_discovery.groq_client import GroqClient
from typing import Dict, Any, List
import logging

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/groq", tags=["GROQ Passthrough"])

groq_client = GroqClient()


class GroqRequest(BaseModel):
    messages: List[Dict[str, str]]
    model: str = "llama-3.3-70b-versatile"
    temperature: float = 0.7
    max_tokens: int = 1000


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
                    "max_tokens": request.max_tokens
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"GROQ API error: {response.status_code}")
                raise HTTPException(status_code=response.status_code, detail="GROQ API error")
                
    except Exception as e:
        logger.error(f"Error calling GROQ: {e}")
        raise HTTPException(status_code=500, detail="Failed to call GROQ API")
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.affiliate_discovery.groq_client import GroqClient
from typing import Dict, List
import logging

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/groq", tags=["GROQ Passthrough"])

groq_client = GroqClient()


class GroqRequest(BaseModel):
    messages: List[Dict[str, str]]
    model: str = "llama-3.3-70b-versatile"
    temperature: float = 0.7
    max_tokens: int = 1000


class SimpleGroqRequest(BaseModel):
    msg: str


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

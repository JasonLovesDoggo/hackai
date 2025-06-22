from fastapi import APIRouter, HTTPException, Query
from .generator import RevenuePlaybookGenerator
from .models import RevenuePlaybook
import logging

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/api/revenue-playbook", tags=["Revenue Playbook"])

# Global generator instance
revenue_playbook_generator = RevenuePlaybookGenerator()


@router.get("/generate", response_model=RevenuePlaybook)
async def generate_revenue_playbook(
    channel_url: str = Query(..., description="YouTube channel URL, handle, or ID"),
):
    """
    Generate a personalized 30-day revenue playbook for a YouTube channel.

    Takes a YouTube channel URL/handle/ID and returns a comprehensive monetization strategy
    tailored to the channel's size, content type, and current performance.

    Examples:
    - @Seytonic
    - https://www.youtube.com/@Seytonic
    - UCW6xlqxSY3gGur4PkGPEUeA
    """
    try:
        logger.info(f"Generating revenue playbook for: {channel_url}")

        playbook = await revenue_playbook_generator.generate_playbook(channel_url)

        logger.info(
            f"Successfully generated playbook: '{playbook.title}' for {playbook.channel_name}"
        )

        return playbook

    except ValueError as e:
        logger.error(f"Invalid input for revenue playbook: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating revenue playbook: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to generate revenue playbook"
        )

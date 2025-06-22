from fastapi import APIRouter, HTTPException, Query
from typing import List
import logging
from .models import (
    SearchRequest,
    ProductSearchResult,
    OverrideEntry,
    LinkGenerationRequest,
    LinkGenerationResult,
)
from .discovery_engine import discovery_engine
from .overrides import override_manager
from .link_generator import link_generator

router = APIRouter(prefix="/affiliate", tags=["Affiliate Discovery"])
logger = logging.getLogger("uvicorn.error")


@router.post("/programs", response_model=ProductSearchResult)
async def discover_affiliate_programs(request: SearchRequest):
    """
    Discover affiliate programs for given product keywords.

    This endpoint uses AI to search for relevant affiliate programs and returns
    structured data with direct links, commission rates, and program details.
    """
    try:
        result = await discovery_engine.discover_affiliate_programs(request)
        return result
    except Exception as e:
        logger.error(f"Error in affiliate discovery endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Discovery failed: {str(e)}")


@router.get("/programs", response_model=ProductSearchResult)
async def discover_affiliate_programs_get(
    keywords: List[str] = Query(..., description="Product keywords to search for"),
    max_results: int = Query(
        default=20, ge=1, le=50, description="Maximum number of results"
    ),
    include_marketplaces: bool = Query(
        default=True, description="Include marketplace programs (Amazon, eBay)"
    ),
    include_direct_programs: bool = Query(
        default=True, description="Include direct company programs"
    ),
    include_networks: bool = Query(
        default=True, description="Include affiliate networks"
    ),
):
    """
    Discover affiliate programs using GET request with query parameters.

    Example: /api/affiliate/programs?keywords=gaming+mouse&keywords=wireless&max_results=15
    """
    request = SearchRequest(
        keywords=keywords,
        max_results=max_results,
        include_marketplaces=include_marketplaces,
        include_direct_programs=include_direct_programs,
        include_networks=include_networks,
    )

    try:
        result = await discovery_engine.discover_affiliate_programs(request)
        return result
    except Exception as e:
        logger.error(f"Error in affiliate discovery GET endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Discovery failed: {str(e)}")


@router.post("/links", response_model=LinkGenerationResult)
async def generate_affiliate_links(request: LinkGenerationRequest):
    """
    Generate actual affiliate product links with your affiliate codes.

    This endpoint searches for specific products and returns direct affiliate links
    with your affiliate codes embedded for immediate use.
    """
    try:
        result = await link_generator.generate_affiliate_links(request)
        return result
    except Exception as e:
        logger.error(f"Error generating affiliate links: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Link generation failed: {str(e)}")


@router.post("/overrides/{key}")
async def add_override(key: str, override: OverrideEntry):
    """
    Add or update a manual override for specific keywords.

    Overrides allow you to manually specify affiliate programs for certain keywords
    to ensure accuracy or add programs that might not be found automatically.
    """
    try:
        override_manager.add_override(key, override)
        return {
            "message": f"Override added successfully for key: {key}",
            "keywords": override.keywords,
            "programs_count": len(override.forced_programs),
            "replace_all": override.replace_all,
        }
    except Exception as e:
        logger.error(f"Error adding override: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add override: {str(e)}")


@router.delete("/overrides/{key}")
async def remove_override(key: str):
    """Remove a manual override"""
    success = override_manager.remove_override(key)
    if success:
        return {"message": f"Override removed successfully for key: {key}"}
    else:
        raise HTTPException(
            status_code=404, detail=f"Override not found for key: {key}"
        )


@router.get("/overrides")
async def list_overrides():
    """List all available overrides"""
    overrides = override_manager.list_overrides()
    return {"total_overrides": len(overrides), "overrides": overrides}


@router.get("/health")
async def health_check():
    """Check the health of the affiliate discovery system"""
    try:
        health_status = await discovery_engine.health_check()
        return health_status
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {"status": "unhealthy", "error": str(e)}


@router.delete("/cache")
async def clear_cache():
    """Clear all cached affiliate discovery results"""
    try:
        cleared_count = discovery_engine.clear_cache()
        return {
            "message": "Cache cleared successfully",
            "entries_cleared": cleared_count,
        }
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


@router.get("/examples")
async def get_examples():
    """Get example requests for testing the API"""
    return {
        "examples": [
            {
                "description": "Gaming peripherals",
                "request": {
                    "keywords": ["gaming mouse", "wireless", "rgb"],
                    "max_results": 15,
                    "include_marketplaces": True,
                    "include_direct_programs": True,
                    "include_networks": True,
                },
            },
            {
                "description": "Fitness supplements",
                "request": {
                    "keywords": ["protein powder", "whey", "vanilla"],
                    "max_results": 10,
                    "include_marketplaces": True,
                    "include_direct_programs": True,
                    "include_networks": False,
                },
            },
            {
                "description": "Tech gadgets",
                "request": {
                    "keywords": ["smartphone", "android", "unlocked"],
                    "max_results": 20,
                    "include_marketplaces": True,
                    "include_direct_programs": True,
                    "include_networks": True,
                },
            },
        ],
        "curl_examples": [
            'curl -X POST "http://localhost:8000/api/affiliate/programs" -H "Content-Type: application/json" -d \'{"keywords": ["gaming mouse"], "max_results": 10}\'',
            'curl "http://localhost:8000/api/affiliate/programs?keywords=protein+powder&max_results=15"',
            'curl -X POST "http://localhost:8000/api/affiliate/links" -H "Content-Type: application/json" -d \'{"keywords": ["uniqlo", "red", "tshirt"], "affiliate_codes": {"amazon": "your-amazon-tag", "ebay": "your-ebay-campid"}}\'',
            'curl "http://localhost:8000/api/affiliate/health"',
        ],
    }

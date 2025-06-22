from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class AffiliateProgram(BaseModel):
    name: str
    website: str
    affiliate_link: Optional[str] = None
    commission_rate: Optional[str] = None
    program_type: str  # "direct", "network", "marketplace"
    signup_link: Optional[str] = None
    requirements: Optional[str] = None
    confidence_score: float = Field(..., ge=0.0, le=1.0)


class ProductSearchResult(BaseModel):
    keywords: List[str]
    product_name: str
    category: Optional[str] = None
    affiliate_programs: List[AffiliateProgram]
    total_programs_found: int
    search_timestamp: str


class SearchRequest(BaseModel):
    keywords: List[str] = Field(..., min_items=1, max_items=10)
    max_results: int = Field(default=20, ge=1, le=50)
    include_marketplaces: bool = True
    include_direct_programs: bool = True
    include_networks: bool = True


class OverrideEntry(BaseModel):
    keywords: List[str]
    forced_programs: List[AffiliateProgram]
    replace_all: bool = False  # If True, replaces all results; if False, adds to results


class AffiliateCodes(BaseModel):
    amazon: Optional[str] = None
    ebay: Optional[str] = None
    walmart: Optional[str] = None
    target: Optional[str] = None
    shareasale: Optional[str] = None
    cj_affiliate: Optional[str] = None
    clickbank: Optional[str] = None


class ProductLink(BaseModel):
    product_name: str
    product_url: str
    affiliate_url: str
    platform: str  # "amazon", "ebay", etc.
    price: Optional[str] = None
    rating: Optional[float] = None
    image_url: Optional[str] = None
    availability: Optional[str] = None


class LinkGenerationRequest(BaseModel):
    keywords: List[str] = Field(..., min_items=1, max_items=10)
    affiliate_codes: AffiliateCodes
    max_results: int = Field(default=10, ge=1, le=50)


class LinkGenerationResult(BaseModel):
    keywords: List[str]
    product_links: List[ProductLink]
    total_links_found: int
    search_timestamp: str
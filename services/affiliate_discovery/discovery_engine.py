import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from .models import AffiliateProgram, ProductSearchResult, SearchRequest
from .groq_client import GroqClient
from .overrides import override_manager
from utils.simple_cache import simple_cache

logger = logging.getLogger("uvicorn.error")


class AffiliateDiscoveryEngine:
    def __init__(self):
        self.groq_client = GroqClient()
        self.cache_ttl = 3600  # 1 hour cache for search results
    
    async def discover_affiliate_programs(self, request: SearchRequest) -> ProductSearchResult:
        """Main discovery method that orchestrates the entire process"""
        logger.info(f"Starting affiliate program discovery for keywords: {request.keywords}")
        
        # Check cache first
        cached_result = simple_cache.get("affiliate_discovery", keywords=request.keywords)
        if cached_result:
            logger.info("Returning cached affiliate discovery result")
            return ProductSearchResult(**cached_result)
        
        try:
            # Step 1: Search for affiliate programs using GROQ
            search_result = await self.groq_client.search_affiliate_programs(request.keywords)
            
            programs = []
            
            if search_result["success"]:
                if "programs" in search_result:
                    # Direct JSON response
                    programs = self._parse_programs({"programs": search_result["programs"]}, request)
                else:
                    # Text response - try extraction
                    extraction_result = await self.groq_client.extract_program_details(
                        search_result["content"], request.keywords
                    )
                    if extraction_result["success"]:
                        programs = self._parse_programs(extraction_result["data"], request)
            
            # Add fallback programs if we got nothing
            if not programs:
                logger.warning("No programs found via GROQ, adding fallback programs")
                programs = self._get_fallback_programs(request.keywords)
            
            # Step 2: Apply manual overrides
            programs = override_manager.apply_overrides(request.keywords, programs)
            
            # Step 3: Filter and limit results
            programs = self._filter_and_limit_programs(programs, request)
            
            # Step 4: Create result
            result = ProductSearchResult(
                keywords=request.keywords,
                product_name=" ".join(request.keywords).title(),
                category=self._guess_category(request.keywords),
                affiliate_programs=programs,
                total_programs_found=len(programs),
                search_timestamp=datetime.now().isoformat()
            )
            
            # Cache the result
            simple_cache.set(
                "affiliate_discovery", 
                result.model_dump(), 
                self.cache_ttl, 
                keywords=request.keywords
            )
            
            logger.info(f"Successfully discovered {len(programs)} affiliate programs")
            return result
            
        except Exception as e:
            logger.error(f"Error in affiliate discovery: {str(e)}")
            return self._create_empty_result(request.keywords, f"Discovery error: {str(e)}")
    
    def _parse_programs(self, extracted_data: Dict[str, Any], request: SearchRequest) -> List[AffiliateProgram]:
        """Parse extracted program data into AffiliateProgram objects"""
        programs = []
        
        for program_data in extracted_data.get("programs", []):
            try:
                # Validate and create AffiliateProgram
                program = AffiliateProgram(
                    name=program_data.get("name", "Unknown"),
                    website=program_data.get("website", ""),
                    affiliate_link=program_data.get("affiliate_link"),
                    commission_rate=program_data.get("commission_rate"),
                    program_type=program_data.get("program_type", "unknown"),
                    signup_link=program_data.get("signup_link"),
                    requirements=program_data.get("requirements"),
                    confidence_score=float(program_data.get("confidence_score", 0.5))
                )
                programs.append(program)
                
            except Exception as e:
                logger.warning(f"Failed to parse program data: {program_data}, error: {e}")
                continue
        
        return programs
    
    def _filter_and_limit_programs(self, programs: List[AffiliateProgram], request: SearchRequest) -> List[AffiliateProgram]:
        """Filter programs based on request criteria and limit results"""
        filtered_programs = []
        
        for program in programs:
            # Filter by program type
            if (
                (program.program_type == "marketplace" and not request.include_marketplaces) or
                (program.program_type == "direct" and not request.include_direct_programs) or
                (program.program_type == "network" and not request.include_networks)
            ):
                continue
            
            # Filter by confidence score (minimum 0.3)
            if program.confidence_score < 0.3:
                continue
            
            filtered_programs.append(program)
        
        # Sort by confidence score (highest first)
        filtered_programs.sort(key=lambda x: x.confidence_score, reverse=True)
        
        # Limit results
        return filtered_programs[:request.max_results]
    
    def _get_fallback_programs(self, keywords: List[str]) -> List[AffiliateProgram]:
        """Get fallback affiliate programs when GROQ fails"""
        fallback_programs = [
            AffiliateProgram(
                name="Amazon Associates",
                website="https://amazon.com",
                affiliate_link="https://affiliate-program.amazon.com/",
                commission_rate="1-10%",
                program_type="marketplace",
                signup_link="https://affiliate-program.amazon.com/",
                requirements="Valid website or app, comply with policies",
                confidence_score=0.9
            ),
            AffiliateProgram(
                name="eBay Partner Network",
                website="https://ebay.com",
                affiliate_link="https://partnernetwork.ebay.com/",
                commission_rate="1-6%",
                program_type="marketplace",
                signup_link="https://partnernetwork.ebay.com/",
                requirements="Active website, compliance with terms",
                confidence_score=0.8
            ),
            AffiliateProgram(
                name="ShareASale",
                website="https://shareasale.com",
                affiliate_link="https://www.shareasale.com/info/",
                commission_rate="Varies by merchant",
                program_type="network",
                signup_link="https://www.shareasale.com/info/",
                requirements="Website approval required",
                confidence_score=0.75
            )
        ]
        
        # Add category-specific programs
        keywords_lower = [k.lower() for k in keywords]
        
        if any(word in keywords_lower for word in ["clothing", "fashion", "shirt", "dress", "uniqlo", "nike", "adidas"]):
            fallback_programs.extend([
                AffiliateProgram(
                    name="Uniqlo Affiliate",
                    website="https://uniqlo.com",
                    affiliate_link="https://www.uniqlo.com/us/en/affiliate/",
                    commission_rate="2-5%",
                    program_type="direct",
                    signup_link="https://www.uniqlo.com/us/en/affiliate/",
                    requirements="Fashion/lifestyle content preferred",
                    confidence_score=0.85
                ),
                AffiliateProgram(
                    name="Nordstrom Affiliate",
                    website="https://nordstrom.com",
                    affiliate_link="https://www.nordstrom.com/browse/affiliate-program",
                    commission_rate="2-11%",
                    program_type="direct",
                    signup_link="https://www.nordstrom.com/browse/affiliate-program",
                    requirements="Fashion content, active promotion",
                    confidence_score=0.8
                )
            ])
        
        return fallback_programs
    
    def _guess_category(self, keywords: List[str]) -> str:
        """Guess product category from keywords"""
        keywords_lower = [k.lower() for k in keywords]
        
        if any(word in keywords_lower for word in ["clothing", "shirt", "dress", "pants", "fashion", "uniqlo"]):
            return "Fashion & Clothing"
        elif any(word in keywords_lower for word in ["tech", "electronics", "gadget", "phone", "computer"]):
            return "Technology"
        elif any(word in keywords_lower for word in ["fitness", "protein", "supplement", "gym"]):
            return "Health & Fitness"
        elif any(word in keywords_lower for word in ["gaming", "mouse", "keyboard", "headset"]):
            return "Gaming"
        else:
            return "General"
    
    def _create_empty_result(self, keywords: List[str], reason: str) -> ProductSearchResult:
        """Create an empty result when search fails"""
        logger.warning(f"Creating empty result for {keywords}: {reason}")
        return ProductSearchResult(
            keywords=keywords,
            product_name=" ".join(keywords),
            category=None,
            affiliate_programs=[],
            total_programs_found=0,
            search_timestamp=datetime.now().isoformat()
        )
    
    async def get_cached_results(self, keywords: List[str]) -> Optional[ProductSearchResult]:
        """Get cached results for specific keywords"""
        cached_result = simple_cache.get("affiliate_discovery", keywords=keywords)
        if cached_result:
            return ProductSearchResult(**cached_result)
        return None
    
    def clear_cache(self) -> int:
        """Clear all cached affiliate discovery results"""
        return simple_cache.clear()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check system health"""
        try:
            # Test GROQ connection with a simple query
            test_result = await self.groq_client.search_affiliate_programs(["test"])
            
            return {
                "status": "healthy" if test_result["success"] else "degraded",
                "groq_api": test_result["success"],
                "cache_stats": simple_cache.get_stats(),
                "override_count": len(override_manager.list_overrides()),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# Global discovery engine instance
discovery_engine = AffiliateDiscoveryEngine()
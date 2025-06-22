import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from .models import LinkGenerationRequest, LinkGenerationResult, ProductLink, AffiliateCodes
from .groq_client import GroqClient
from utils.simple_cache import simple_cache

logger = logging.getLogger("uvicorn.error")


class LinkGenerator:
    def __init__(self):
        self.groq_client = GroqClient()
        self.cache_ttl = 1800  # 30 minutes cache for product links
    
    async def generate_affiliate_links(self, request: LinkGenerationRequest) -> LinkGenerationResult:
        """Generate actual affiliate product links with user's affiliate codes"""
        logger.info(f"Generating affiliate links for keywords: {request.keywords}")
        
        # Auto-detect platforms from provided affiliate codes
        platforms = self._get_active_platforms(request.affiliate_codes)
        logger.info(f"Auto-detected platforms: {platforms}")
        
        # Check cache first
        cache_key = f"{'-'.join(request.keywords)}-{'-'.join(platforms)}"
        cached_result = simple_cache.get("affiliate_links", cache_key=cache_key)
        if cached_result:
            # Apply fresh affiliate codes to cached results
            cached_result = self._apply_affiliate_codes(cached_result, request.affiliate_codes)
            return LinkGenerationResult(**cached_result)
        
        try:
            # Use GROQ to find actual products and generate links
            product_links = await self._search_and_generate_links(request, platforms)
            
            result = LinkGenerationResult(
                keywords=request.keywords,
                product_links=product_links,
                total_links_found=len(product_links),
                search_timestamp=datetime.now().isoformat()
            )
            
            # Cache without affiliate codes (we'll apply them fresh each time)
            cache_data = result.model_dump()
            cache_data["product_links"] = [
                {**link, "affiliate_url": link["product_url"]} 
                for link in cache_data["product_links"]
            ]
            simple_cache.set("affiliate_links", cache_data, self.cache_ttl, cache_key=cache_key)
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating affiliate links: {str(e)}")
            return self._create_empty_result(request.keywords)
    
    def _get_active_platforms(self, codes: AffiliateCodes) -> List[str]:
        """Get list of platforms that have affiliate codes provided"""
        platforms = []
        if codes.amazon:
            platforms.append("amazon")
        if codes.ebay:
            platforms.append("ebay")
        if codes.walmart:
            platforms.append("walmart")
        if codes.target:
            platforms.append("target")
        if codes.shareasale:
            platforms.append("shareasale")
        if codes.cj_affiliate:
            platforms.append("cj_affiliate")
        if codes.clickbank:
            platforms.append("clickbank")
        
        # If no codes provided, default to major platforms
        if not platforms:
            platforms = ["amazon", "ebay", "walmart"]
            logger.warning("No affiliate codes provided, using default platforms")
        
        return platforms
    
    async def _search_and_generate_links(self, request: LinkGenerationRequest, platforms: List[str]) -> List[ProductLink]:
        """Search for products and generate affiliate links"""
        
        search_prompt = f"""
Find specific products for: {', '.join(request.keywords)}

Return ONLY a JSON array with actual products from these platforms: {', '.join(platforms)}

Format:
[
  {{
    "product_name": "Uniqlo Men's Red T-Shirt Cotton Crew Neck",
    "product_url": "https://www.uniqlo.com/us/en/products/E12345-000",
    "platform": "uniqlo",
    "price": "$12.90",
    "rating": 4.5,
    "image_url": "https://uniqlo.com/images/product.jpg",
    "availability": "In Stock"
  }}
]

Include real products from:
- Amazon: specific product ASINs/URLs
- eBay: actual listing URLs  
- Walmart: real product pages
- Target: specific product URLs
- Uniqlo: direct product links

Return ONLY the JSON array, no other text.
        """

        try:
            search_result = await self.groq_client._search_products(search_prompt)
            
            if search_result["success"] and "products" in search_result:
                products = search_result["products"]
            else:
                # Fallback to basic product search
                products = self._get_fallback_products_data(request, platforms)
            
            # Generate affiliate links
            product_links = []
            for product in products[:request.max_results]:
                affiliate_url = self._generate_affiliate_url(
                    product.get("product_url", ""),
                    product.get("platform", ""),
                    request.affiliate_codes
                )
                
                product_links.append(ProductLink(
                    product_name=product.get("product_name", f"{' '.join(request.keywords)} Product"),
                    product_url=product.get("product_url", ""),
                    affiliate_url=affiliate_url,
                    platform=product.get("platform", "unknown"),
                    price=product.get("price"),
                    rating=product.get("rating"),
                    image_url=product.get("image_url"),
                    availability=product.get("availability", "Check website")
                ))
            
            return product_links
            
        except Exception as e:
            logger.error(f"Error in product search: {str(e)}")
            return self._get_fallback_products_as_links(request, platforms)
    
    def _generate_affiliate_url(self, product_url: str, platform: str, codes: AffiliateCodes) -> str:
        """Generate affiliate URL with user's affiliate code"""
        if not product_url:
            return ""
        
        platform_lower = platform.lower()
        
        if platform_lower == "amazon" and codes.amazon:
            # Amazon affiliate link format
            if "amazon.com" in product_url:
                if "?" in product_url:
                    return f"{product_url}&tag={codes.amazon}"
                else:
                    return f"{product_url}?tag={codes.amazon}"
        
        elif platform_lower == "ebay" and codes.ebay:
            # eBay Partner Network format
            if "?" in product_url:
                return f"{product_url}&campid={codes.ebay}"
            else:
                return f"{product_url}?campid={codes.ebay}"
        
        elif platform_lower == "walmart" and codes.walmart:
            # Walmart affiliate format
            if "?" in product_url:
                return f"{product_url}&wmlspartner={codes.walmart}"
            else:
                return f"{product_url}?wmlspartner={codes.walmart}"
        
        elif platform_lower == "target" and codes.target:
            # Target affiliate format (via ShareASale)
            if "?" in product_url:
                return f"{product_url}&u1={codes.target}"
            else:
                return f"{product_url}?u1={codes.target}"
        
        # Return original URL if no affiliate code available
        return product_url
    
    def _get_fallback_products_data(self, request: LinkGenerationRequest, platforms: List[str]) -> List[Dict]:
        """Generate fallback product data when AI search fails"""
        keywords_str = "+".join(request.keywords)
        fallback_data = []
        
        if "amazon" in platforms:
            fallback_data.append({
                "product_name": f"{' '.join(request.keywords).title()} - Amazon Search",
                "product_url": f"https://amazon.com/s?k={keywords_str}",
                "platform": "amazon",
                "availability": "Search Results"
            })
        
        if "ebay" in platforms:
            fallback_data.append({
                "product_name": f"{' '.join(request.keywords).title()} - eBay Search", 
                "product_url": f"https://ebay.com/sch/i.html?_nkw={keywords_str}",
                "platform": "ebay",
                "availability": "Search Results"
            })
        
        if "walmart" in platforms:
            fallback_data.append({
                "product_name": f"{' '.join(request.keywords).title()} - Walmart Search",
                "product_url": f"https://walmart.com/search?q={keywords_str}",
                "platform": "walmart", 
                "availability": "Search Results"
            })
        
        return fallback_data
    
    def _get_fallback_products_as_links(self, request: LinkGenerationRequest, platforms: List[str]) -> List[ProductLink]:
        """Generate fallback product links when AI search fails"""
        keywords_str = "+".join(request.keywords)
        fallback_products = []
        
        if "amazon" in platforms:
            fallback_products.append(ProductLink(
                product_name=f"{' '.join(request.keywords).title()} - Amazon Search",
                product_url=f"https://amazon.com/s?k={keywords_str}",
                affiliate_url=self._generate_affiliate_url(
                    f"https://amazon.com/s?k={keywords_str}", 
                    "amazon", 
                    request.affiliate_codes
                ),
                platform="amazon",
                availability="Search Results"
            ))
        
        if "ebay" in platforms:
            fallback_products.append(ProductLink(
                product_name=f"{' '.join(request.keywords).title()} - eBay Search",
                product_url=f"https://ebay.com/sch/i.html?_nkw={keywords_str}",
                affiliate_url=self._generate_affiliate_url(
                    f"https://ebay.com/sch/i.html?_nkw={keywords_str}",
                    "ebay",
                    request.affiliate_codes
                ),
                platform="ebay",
                availability="Search Results"
            ))
        
        if "walmart" in platforms:
            fallback_products.append(ProductLink(
                product_name=f"{' '.join(request.keywords).title()} - Walmart Search",
                product_url=f"https://walmart.com/search?q={keywords_str}",
                affiliate_url=self._generate_affiliate_url(
                    f"https://walmart.com/search?q={keywords_str}",
                    "walmart",
                    request.affiliate_codes
                ),
                platform="walmart",
                availability="Search Results"
            ))
        
        return fallback_products
    
    def _apply_affiliate_codes(self, cached_data: Dict, codes: AffiliateCodes) -> Dict:
        """Apply fresh affiliate codes to cached product data"""
        for product in cached_data.get("product_links", []):
            product["affiliate_url"] = self._generate_affiliate_url(
                product["product_url"],
                product["platform"],
                codes
            )
        return cached_data
    
    def _create_empty_result(self, keywords: List[str]) -> LinkGenerationResult:
        """Create empty result when generation fails"""
        return LinkGenerationResult(
            keywords=keywords,
            product_links=[],
            total_links_found=0,
            search_timestamp=datetime.now().isoformat()
        )


# Add product search method to GroqClient
async def _search_products(self, prompt: str) -> Dict[str, Any]:
    """Search for specific products using GROQ"""
    try:
        async with __import__('httpx').AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a product search expert. Return only valid JSON arrays with real products."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.1,
                    "max_tokens": 2000
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"].strip()
                
                try:
                    import json
                    products = json.loads(content)
                    return {
                        "success": True,
                        "products": products,
                        "usage": result.get("usage", {}),
                        "timestamp": datetime.now().isoformat()
                    }
                except json.JSONDecodeError:
                    return {
                        "success": False,
                        "error": "JSON parsing failed",
                        "raw_content": content
                    }
            else:
                return {
                    "success": False,
                    "error": f"API error: {response.status_code}"
                }
                
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# Monkey patch the method onto GroqClient
GroqClient._search_products = _search_products

# Global link generator instance
link_generator = LinkGenerator()
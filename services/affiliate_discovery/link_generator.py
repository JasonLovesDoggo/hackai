import logging
from datetime import datetime
from typing import List, Dict
from urllib.parse import quote_plus
import re

import httpx
from bs4 import BeautifulSoup

from .models import (
    LinkGenerationRequest,
    LinkGenerationResult,
    ProductLink,
    AffiliateCodes,
)
from .groq_client import GroqClient
from utils.simple_cache import simple_cache

logger = logging.getLogger("uvicorn.error")


class LinkGenerator:
    def __init__(self, groq_client: GroqClient = None):
        self.groq_client = groq_client if groq_client else GroqClient()
        self.cache_ttl = 1800  # 30 minutes cache for product links

    async def generate_affiliate_links(
        self, request: LinkGenerationRequest
    ) -> LinkGenerationResult:
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
            cached_result = self._apply_affiliate_codes(
                cached_result, request.affiliate_codes
            )
            return LinkGenerationResult(**cached_result)

        try:
            # Use GROQ to find actual products and generate links
            product_links = await self._search_and_generate_links(request, platforms)

            result = LinkGenerationResult(
                keywords=request.keywords,
                product_links=product_links,
                total_links_found=len(product_links),
                search_timestamp=datetime.now().isoformat(),
            )

            # Cache without affiliate codes (we'll apply them fresh each time)
            cache_data = result.model_dump()
            cache_data["product_links"] = [
                {**link, "affiliate_url": link["product_url"]}
                for link in cache_data["product_links"]
            ]
            simple_cache.set(
                "affiliate_links", cache_data, self.cache_ttl, cache_key=cache_key
            )

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

    async def _search_and_generate_links(
        self, request: LinkGenerationRequest, platforms: List[str]
    ) -> List[ProductLink]:
        """Search for products and generate affiliate links"""
        
        try:
            # Try GROQ tool calling first
            search_result = await self.groq_client.search_products_with_tools(
                request.keywords
            )

            if not search_result.get("success") or not search_result.get("products"):
                # Fallback to web scraping
                products = await self._search_products_via_web(
                    request.keywords, platforms
                )
                search_result = {"success": True, "products": products}

            if search_result["success"] and "products" in search_result:
                products = search_result["products"]
            else:
                # Fallback to basic product search
                products = self._get_fallback_products_data(request, platforms)

            # Generate affiliate links
            product_links = []
            for product in products[: request.max_results]:
                affiliate_url = self._generate_affiliate_url(
                    product.get("product_url", ""),
                    product.get("platform", ""),
                    request.affiliate_codes,
                )

                product_links.append(
                    ProductLink(
                        product_name=product.get(
                            "product_name", f"{' '.join(request.keywords)} Product"
                        ),
                        product_url=product.get("product_url", ""),
                        affiliate_url=affiliate_url,
                        platform=product.get("platform", "unknown"),
                        price=product.get("price"),
                        rating=product.get("rating"),
                        image_url=product.get("image_url"),
                        availability=product.get("availability", "Check website"),
                    )
                )

            return product_links

        except Exception as e:
            logger.error(f"Error in product search: {str(e)}")
            return self._get_fallback_products_as_links(request, platforms)

    def _generate_affiliate_url(
        self, product_url: str, platform: str, codes: AffiliateCodes
    ) -> str:
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

    def _get_fallback_products_data(
        self, request: LinkGenerationRequest, platforms: List[str]
    ) -> List[Dict]:
        """Generate fallback product data when AI search fails"""
        keywords_str = "+".join(request.keywords)
        fallback_data = []

        if "amazon" in platforms:
            fallback_data.append(
                {
                    "product_name": f"{' '.join(request.keywords).title()} - Amazon Search",
                    "product_url": f"https://amazon.com/s?k={keywords_str}",
                    "platform": "amazon",
                    "availability": "Search Results",
                }
            )

        if "ebay" in platforms:
            fallback_data.append(
                {
                    "product_name": f"{' '.join(request.keywords).title()} - eBay Search",
                    "product_url": f"https://ebay.com/sch/i.html?_nkw={keywords_str}",
                    "platform": "ebay",
                    "availability": "Search Results",
                }
            )

        if "walmart" in platforms:
            fallback_data.append(
                {
                    "product_name": f"{' '.join(request.keywords).title()} - Walmart Search",
                    "product_url": f"https://walmart.com/search?q={keywords_str}",
                    "platform": "walmart",
                    "availability": "Search Results",
                }
            )

        return fallback_data

    def _get_fallback_products_as_links(
        self, request: LinkGenerationRequest, platforms: List[str]
    ) -> List[ProductLink]:
        """Generate fallback product links when AI search fails"""
        keywords_str = "+".join(request.keywords)
        fallback_products = []

        if "amazon" in platforms:
            fallback_products.append(
                ProductLink(
                    product_name=f"{' '.join(request.keywords).title()} - Amazon Search",
                    product_url=f"https://amazon.com/s?k={keywords_str}",
                    affiliate_url=self._generate_affiliate_url(
                        f"https://amazon.com/s?k={keywords_str}",
                        "amazon",
                        request.affiliate_codes,
                    ),
                    platform="amazon",
                    availability="Search Results",
                )
            )

        if "ebay" in platforms:
            fallback_products.append(
                ProductLink(
                    product_name=f"{' '.join(request.keywords).title()} - eBay Search",
                    product_url=f"https://ebay.com/sch/i.html?_nkw={keywords_str}",
                    affiliate_url=self._generate_affiliate_url(
                        f"https://ebay.com/sch/i.html?_nkw={keywords_str}",
                        "ebay",
                        request.affiliate_codes,
                    ),
                    platform="ebay",
                    availability="Search Results",
                )
            )

        if "walmart" in platforms:
            fallback_products.append(
                ProductLink(
                    product_name=f"{' '.join(request.keywords).title()} - Walmart Search",
                    product_url=f"https://walmart.com/search?q={keywords_str}",
                    affiliate_url=self._generate_affiliate_url(
                        f"https://walmart.com/search?q={keywords_str}",
                        "walmart",
                        request.affiliate_codes,
                    ),
                    platform="walmart",
                    availability="Search Results",
                )
            )

        return fallback_products

    def _apply_affiliate_codes(self, cached_data: Dict, codes: AffiliateCodes) -> Dict:
        """Apply fresh affiliate codes to cached product data"""
        for product in cached_data.get("product_links", []):
            product["affiliate_url"] = self._generate_affiliate_url(
                product["product_url"], product["platform"], codes
            )
        return cached_data

    def _create_empty_result(self, keywords: List[str]) -> LinkGenerationResult:
        """Create empty result when generation fails"""
        return LinkGenerationResult(
            keywords=keywords,
            product_links=[],
            total_links_found=0,
            search_timestamp=datetime.now().isoformat(),
        )

    async def _search_products_via_web(
        self, keywords: List[str], platforms: List[str]
    ) -> List[Dict]:
        """Search for real products using web search"""
        import httpx

        all_products = []
        search_query = " ".join(keywords)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                for platform in platforms[:3]:  # Limit to first 3 platforms
                    try:
                        if platform == "amazon":
                            products = await self._search_amazon(client, search_query)
                            all_products.extend(products)
                        elif platform == "ebay":
                            products = await self._search_ebay(client, search_query)
                            all_products.extend(products)
                        elif platform == "walmart":
                            products = await self._search_walmart(client, search_query)
                            all_products.extend(products)
                    except Exception as e:
                        logger.warning(f"Failed to search {platform}: {e}")
                        continue

            return all_products
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return []

    async def _search_amazon(self, client: httpx.AsyncClient, query: str) -> List[Dict]:
        """Search Amazon for real products using actual web scraping"""
        try:
            search_url = f"https://www.amazon.com/s?k={quote_plus(query)}&ref=sr_pg_1"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }

            response = await client.get(
                search_url, headers=headers, follow_redirects=True, timeout=30.0
            )
            if response.status_code != 200:
                logger.error(f"Amazon returned {response.status_code}")
                return []

            # Parse HTML to extract real product links
            soup = BeautifulSoup(response.text, "html.parser")
            products = []

            # Find product containers
            product_containers = soup.find_all(
                "div", {"data-component-type": "s-search-result"}
            )

            for container in product_containers[:5]:  # Get first 5 products
                try:
                    # Find product title and link
                    title_elem = container.find("h2")
                    if not title_elem:
                        continue

                    link_elem = title_elem.find("a")
                    if not link_elem or not link_elem.get("href"):
                        continue

                    title = title_elem.get_text(strip=True)
                    product_url = f"https://www.amazon.com{link_elem['href']}"

                    # Clean up the URL to remove tracking parameters
                    if "/dp/" in product_url:
                        match = re.search(r"/dp/([A-Z0-9]{10})", product_url)
                        if match:
                            asin = match.group(1)
                            product_url = f"https://www.amazon.com/dp/{asin}"

                    # Try to find price
                    price = "Check website"
                    price_elem = container.find("span", class_="a-price-whole")
                    if price_elem:
                        price_fraction = container.find(
                            "span", class_="a-price-fraction"
                        )
                        if price_fraction:
                            price = f"${price_elem.get_text(strip=True)}.{price_fraction.get_text(strip=True)}"
                        else:
                            price = f"${price_elem.get_text(strip=True)}"

                    # Try to find rating
                    rating = None
                    rating_elem = container.find("span", class_="a-icon-alt")
                    if rating_elem:
                        rating_text = rating_elem.get_text()
                        if "out of 5 stars" in rating_text:
                            try:
                                rating = float(rating_text.split()[0])
                            except (ValueError, IndexError):
                                pass

                    products.append(
                        {
                            "product_name": title,
                            "product_url": product_url,
                            "platform": "amazon",
                            "price": price,
                            "rating": rating,
                            "image_url": None,
                            "availability": "Check availability",
                        }
                    )

                except Exception as e:
                    logger.debug(f"Failed to parse product container: {e}")
                    continue

            return products

        except Exception as e:
            logger.error(f"Amazon search failed: {e}")
            return []

    async def _search_ebay(self, client: httpx.AsyncClient, query: str) -> List[Dict]:
        """Search eBay for real products using actual web scraping"""
        try:
            search_url = (
                f"https://www.ebay.com/sch/i.html?_nkw={quote_plus(query)}&_sacat=0"
            )
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            }

            response = await client.get(search_url, headers=headers, timeout=30.0)
            if response.status_code != 200:
                logger.error(f"eBay returned {response.status_code}")
                return []

            # Parse HTML to extract real product links
            soup = BeautifulSoup(response.text, "html.parser")
            products = []

            # Find product containers
            product_containers = soup.find_all("div", class_="s-item")

            for container in product_containers[:5]:  # Get first 5 products
                try:
                    # Find product title and link
                    title_elem = container.find("h3", class_="s-item__title")
                    if not title_elem:
                        continue

                    link_elem = container.find("a", class_="s-item__link")
                    if not link_elem or not link_elem.get("href"):
                        continue

                    title = title_elem.get_text(strip=True)
                    product_url = link_elem["href"]

                    # Try to find price
                    price = "Check website"
                    price_elem = container.find("span", class_="s-item__price")
                    if price_elem:
                        price = price_elem.get_text(strip=True)

                    products.append(
                        {
                            "product_name": title,
                            "product_url": product_url,
                            "platform": "ebay",
                            "price": price,
                            "rating": None,
                            "image_url": None,
                            "availability": "Check availability",
                        }
                    )

                except Exception as e:
                    logger.debug(f"Failed to parse eBay product container: {e}")
                    continue

            return products

        except Exception as e:
            logger.error(f"eBay search failed: {e}")
            return []

    async def _search_walmart(
        self, client: httpx.AsyncClient, query: str
    ) -> List[Dict]:
        """Search Walmart for real products using actual web scraping"""
        try:
            search_url = f"https://www.walmart.com/search?q={quote_plus(query)}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            }

            response = await client.get(search_url, headers=headers, timeout=30.0)
            if response.status_code != 200:
                logger.error(f"Walmart returned {response.status_code}")
                return []

            # Parse HTML to extract real product links
            soup = BeautifulSoup(response.text, "html.parser")
            products = []

            # Find product containers
            product_containers = soup.find_all("div", {"data-testid": "item-stack"})

            for container in product_containers[:5]:  # Get first 5 products
                try:
                    # Find product link
                    link_elem = container.find("a")
                    if not link_elem or not link_elem.get("href"):
                        continue

                    # Find product title
                    title_elem = container.find(
                        "span", {"data-automation-id": "product-title"}
                    )
                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)
                    product_url = f"https://www.walmart.com{link_elem['href']}"

                    # Try to find price
                    price = "Check website"
                    price_elem = container.find("span", {"itemprop": "price"})
                    if price_elem:
                        price = price_elem.get_text(strip=True)

                    products.append(
                        {
                            "product_name": title,
                            "product_url": product_url,
                            "platform": "walmart",
                            "price": price,
                            "rating": None,
                            "image_url": None,
                            "availability": "Check availability",
                        }
                    )

                except Exception as e:
                    logger.debug(f"Failed to parse Walmart product container: {e}")
                    continue

            return products

        except Exception as e:
            logger.error(f"Walmart search failed: {e}")
            return []


# Global link generator instance
link_generator = LinkGenerator()

import os
import httpx
import json
import logging
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger("uvicorn.error")


class GroqClient:
    def __init__(self):
        self.api_key = os.getenv("GROQ_KEY_FOOL")
        if not self.api_key:
            raise ValueError("GROQ_KEY_FOOL environment variable is required")

        self.base_url = "https://api.groq.com/openai/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def search_products_with_tools(self, keywords: List[str]) -> Dict[str, Any]:
        """Use GROQ with tool calling to search for real products"""
        try:
            # Actually search the internet for real products
            products = await self._search_real_products(keywords)

            return {
                "success": True,
                "products": products,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def _search_real_products(self, keywords: List[str]) -> List[Dict]:
        """Search for real products and verify URLs work"""
        try:
            # Search Amazon directly - most reliable method
            products = await self._search_amazon_directly("".join(keywords))

            if not products:
                # Fallback to Bing if Amazon fails
                products = await self._search_bing("".join(keywords))

            # Verify URLs actually work (no 404s)
            verified_products = await self._verify_product_urls(products)

            logger.info(f"Found {len(verified_products)} verified working products")
            return verified_products

        except Exception as e:
            logger.error(f"Product search failed: {e}")
            return []

    async def _verify_product_urls(self, products: List[Dict]) -> List[Dict]:
        """Verify product URLs actually work (no 404s)"""
        try:
            import asyncio

            verified_products = []

            async with httpx.AsyncClient(timeout=10.0) as client:
                # Check URLs in parallel
                tasks = []
                for product in products:
                    task = self._check_url_exists(client, product)
                    tasks.append(task)

                results = await asyncio.gather(*tasks, return_exceptions=True)

                for result in results:
                    if isinstance(result, dict):  # Not an exception
                        verified_products.append(result)

            return verified_products

        except Exception as e:
            logger.error(f"URL verification failed: {e}")
            return products  # Return unverified if verification fails

    async def _check_url_exists(self, client: httpx.AsyncClient, product: Dict) -> Dict:
        """Check if a single product URL exists"""
        try:
            url = product["product_url"]

            # HEAD request to check if URL exists
            response = await client.head(url, follow_redirects=True)

            if response.status_code == 200:
                return product
            else:
                logger.debug(f"Product URL {url} returned {response.status_code}")
                return None

        except Exception as e:
            logger.debug(f"Failed to verify URL {product.get('product_url')}: {e}")
            return None

    async def _search_bing(self, query: str) -> List[Dict]:
        """Search Bing for Amazon products"""
        try:
            from urllib.parse import quote_plus

            search_url = f"https://www.bing.com/search?q={quote_plus(query + ' site:amazon.com')}"

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(search_url, headers=headers)

                if response.status_code == 200:
                    import re

                    amazon_pattern = (
                        r'https://www\.amazon\.com/[^"\'>\s]*?/dp/([A-Z0-9]{10})'
                    )
                    matches = re.findall(amazon_pattern, response.text)

                    unique_asins = list(set(matches))[:5]

                    products = []
                    for asin in unique_asins:
                        products.append(
                            {
                                "product_name": f"{query.title()} - Amazon Product (ASIN: {asin})",
                                "product_url": f"https://www.amazon.com/dp/{asin}",
                                "platform": "amazon",
                                "price": "Check website",
                                "rating": None,
                                "image_url": None,
                                "availability": "Check availability",
                            }
                        )

                    return products

        except Exception as e:
            logger.error(f"Bing search failed: {e}")
            return []

    async def _search_amazon_directly(self, query: str) -> List[Dict]:
        """Search Amazon directly"""
        try:
            from urllib.parse import quote_plus
            from bs4 import BeautifulSoup

            search_url = (
                f"https://www.amazon.com/s?k={quote_plus(query)}&ref=nb_sb_noss"
            )

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(search_url, headers=headers)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")

                    products = []

                    # Find product containers
                    product_containers = soup.find_all(
                        "div", {"data-component-type": "s-search-result"}
                    )

                    for container in product_containers[:5]:
                        try:
                            # Find product link
                            link_elem = container.find("a", href=True)
                            if not link_elem:
                                continue

                            href = link_elem["href"]
                            if "/dp/" in href:
                                import re

                                match = re.search(r"/dp/([A-Z0-9]{10})", href)
                                if match:
                                    asin = match.group(1)

                                    # Try to get title
                                    title_elem = container.find("h2")
                                    title = query.title() + " Product"
                                    if title_elem:
                                        title = title_elem.get_text(strip=True)

                                    products.append(
                                        {
                                            "product_name": title,
                                            "product_url": f"https://www.amazon.com/dp/{asin}",
                                            "platform": "amazon",
                                            "price": "Check website",
                                            "rating": None,
                                            "image_url": None,
                                            "availability": "Check availability",
                                        }
                                    )

                        except Exception:
                            continue

                    return products

        except Exception as e:
            logger.error(f"Direct Amazon search failed: {e}")
            return []

    async def search_affiliate_programs(self, keywords: List[str]) -> Dict[str, Any]:
        """Use GROQ to intelligently search for affiliate programs"""

        search_prompt = f"""
Find affiliate programs for: {", ".join(keywords)}

Return ONLY a JSON array with this exact format:
[
  {{
    "name": "Amazon Associates",
    "website": "https://amazon.com",
    "affiliate_link": "https://affiliate-program.amazon.com/",
    "commission_rate": "1-10%",
    "program_type": "marketplace",
    "signup_link": "https://affiliate-program.amazon.com/",
    "requirements": "Valid website or app",
    "confidence_score": 0.95
  }}
]

Include these types:
- marketplaces: Amazon, eBay, Walmart, Target
- direct: Brand websites that sell the product
- networks: ShareASale, CJ Affiliate, ClickBank

Return ONLY the JSON array, no other text.
        """

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are an expert in affiliate marketing and e-commerce. Provide accurate, up-to-date information about affiliate programs.",
                            },
                            {"role": "user", "content": search_prompt},
                        ],
                        "temperature": 0.1,
                        "max_tokens": 1500,
                    },
                )

                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"].strip()

                    # Try to parse directly as JSON
                    try:
                        parsed_programs = json.loads(content)
                        return {
                            "success": True,
                            "programs": parsed_programs,
                            "usage": result.get("usage", {}),
                            "timestamp": datetime.now().isoformat(),
                        }
                    except json.JSONDecodeError:
                        # Fallback to text content
                        return {
                            "success": True,
                            "content": content,
                            "usage": result.get("usage", {}),
                            "timestamp": datetime.now().isoformat(),
                        }
                else:
                    logger.error(
                        f"GROQ API error: {response.status_code} - {response.text}"
                    )
                    return {
                        "success": False,
                        "error": f"API error: {response.status_code}",
                        "timestamp": datetime.now().isoformat(),
                    }

        except Exception as e:
            logger.error(f"Error calling GROQ API: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def extract_program_details(
        self, raw_content: str, keywords: List[str]
    ) -> Dict[str, Any]:
        """Use GROQ to extract structured data from the raw search results"""

        extraction_prompt = f"""
        Parse the following affiliate program information and extract it into a structured format.
        
        Original keywords: {", ".join(keywords)}
        
        Raw content:
        {raw_content}
        
        Please extract and format this information as a JSON structure with the following format:
        {{
            "programs": [
                {{
                    "name": "Company Name",
                    "website": "https://website.com",
                    "affiliate_link": "https://affiliate-signup-link.com",
                    "commission_rate": "5-10%",
                    "program_type": "direct|network|marketplace",
                    "signup_link": "https://signup.com",
                    "requirements": "Brief description of requirements",
                    "confidence_score": 0.8
                }}
            ],
            "product_name": "Inferred product name",
            "category": "Product category"
        }}
        
        Make sure:
        - All URLs are valid and complete
        - Commission rates are realistic
        - Confidence scores reflect how well the program matches the keywords
        - Program types are accurately classified
        - Only include legitimate, known programs
        
        Return only the JSON structure, no additional text.
        """

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a data extraction expert. Return only valid JSON structures as requested.",
                            },
                            {"role": "user", "content": extraction_prompt},
                        ],
                        "temperature": 0.1,
                        "max_tokens": 1500,
                    },
                )

                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]

                    # Try to parse the JSON response
                    try:
                        parsed_data = json.loads(content)
                        return {
                            "success": True,
                            "data": parsed_data,
                            "usage": result.get("usage", {}),
                            "timestamp": datetime.now().isoformat(),
                        }
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse GROQ JSON response: {e}")
                        return {
                            "success": False,
                            "error": f"JSON parsing error: {e}",
                            "raw_content": content,
                            "timestamp": datetime.now().isoformat(),
                        }

                else:
                    logger.error(
                        f"GROQ API error: {response.status_code} - {response.text}"
                    )
                    return {
                        "success": False,
                        "error": f"API error: {response.status_code}",
                        "timestamp": datetime.now().isoformat(),
                    }

        except Exception as e:
            logger.error(f"Error calling GROQ API for extraction: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

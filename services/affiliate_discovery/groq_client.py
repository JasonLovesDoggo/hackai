import os
import httpx
import json
import logging
from typing import List, Dict, Any, Optional
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
            "Content-Type": "application/json"
        }

    async def search_products_with_tools(self, keywords: List[str]) -> Dict[str, Any]:
        """Use GROQ with tool calling to search for real products"""
        
        search_prompt = f"""
Search for real products matching these keywords: {', '.join(keywords)}

Use web search to find actual products from Amazon, eBay, and Walmart. Return real product names, URLs, and prices.

For each product found, provide:
- Exact product name as it appears on the website
- Direct product URL (not search page)
- Current price if available
- Platform (amazon, ebay, walmart)

Return only real, existing products with valid URLs.
        """

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a product search expert. Use web search to find real products and return accurate information with valid URLs."
                            },
                            {
                                "role": "user",
                                "content": search_prompt
                            }
                        ],
                        "tools": [
                            {
                                "type": "function",
                                "function": {
                                    "name": "web_search",
                                    "description": "Search the web for current information",
                                    "parameters": {
                                        "type": "object",
                                        "properties": {
                                            "query": {
                                                "type": "string",
                                                "description": "The search query"
                                            }
                                        },
                                        "required": ["query"]
                                    }
                                }
                            }
                        ],
                        "tool_choice": "auto",
                        "temperature": 0.1,
                        "max_tokens": 2000
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Handle tool calls if present
                    message = result["choices"][0]["message"]
                    if message.get("tool_calls"):
                        # Process tool calls and get final response
                        return await self._handle_tool_calls(message["tool_calls"], keywords)
                    else:
                        # Direct response without tool calls
                        content = message["content"]
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
                    logger.error(f"GROQ API error: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"API error: {response.status_code}",
                        "timestamp": datetime.now().isoformat()
                    }

        except Exception as e:
            logger.error(f"Error calling GROQ API with tools: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def _handle_tool_calls(self, tool_calls: List[Dict], keywords: List[str]) -> Dict[str, Any]:
        """Handle tool calls from GROQ and return final product results"""
        try:
            # Actually search the internet for real products
            products = await self._search_real_products(keywords)
            
            return {
                "success": True,
                "products": products,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _search_real_products(self, keywords: List[str]) -> List[Dict]:
        """Actually search the web using SerpAPI or direct scraping"""
        try:
            import httpx
            from urllib.parse import quote_plus
            import json
            
            # Try SerpAPI first (if available)
            serpapi_key = os.getenv("SERPAPI_KEY")
            if serpapi_key:
                return await self._search_with_serpapi(keywords, serpapi_key)
            
            # Fallback to direct web scraping with better headers
            return await self._scrape_search_engines(keywords)
            
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return []
    
    async def _search_with_serpapi(self, keywords: List[str], api_key: str) -> List[Dict]:
        """Use SerpAPI for real search results"""
        try:
            import httpx
            from urllib.parse import quote_plus
            
            query = ' '.join(keywords) + ' site:amazon.com'
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    "https://serpapi.com/search",
                    params={
                        "q": query,
                        "api_key": api_key,
                        "engine": "google",
                        "num": 10
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    organic_results = data.get("organic_results", [])
                    
                    products = []
                    for result in organic_results:
                        link = result.get("link", "")
                        title = result.get("title", "")
                        
                        if "amazon.com" in link and "/dp/" in link:
                            # Extract ASIN
                            import re
                            match = re.search(r'/dp/([A-Z0-9]{10})', link)
                            if match:
                                asin = match.group(1)
                                products.append({
                                    "product_name": title,
                                    "product_url": f"https://www.amazon.com/dp/{asin}",
                                    "platform": "amazon",
                                    "price": "Check website",
                                    "rating": None,
                                    "image_url": None,
                                    "availability": "Check availability"
                                })
                    
                    return products
                
        except Exception as e:
            logger.error(f"SerpAPI failed: {e}")
            return []
    
    async def _scrape_search_engines(self, keywords: List[str]) -> List[Dict]:
        """Try multiple search approaches to find real products"""
        try:
            import httpx
            from urllib.parse import quote_plus
            import random
            import time
            
            query = ' '.join(keywords)
            products = []
            
            # Method 1: Try Bing (less aggressive blocking)
            try:
                products = await self._search_bing(query)
                if products:
                    return products
            except Exception as e:
                logger.warning(f"Bing search failed: {e}")
            
            # Method 2: Try alternative search engines
            try:
                products = await self._search_startpage(query)
                if products:
                    return products
            except Exception as e:
                logger.warning(f"Startpage search failed: {e}")
            
            # Method 3: Try scraping Amazon directly with search
            try:
                products = await self._search_amazon_directly(query)
                if products:
                    return products
            except Exception as e:
                logger.warning(f"Direct Amazon search failed: {e}")
            
            return []
                    
        except Exception as e:
            logger.error(f"All search methods failed: {e}")
            return []
    
    async def _search_bing(self, query: str) -> List[Dict]:
        """Search Bing for Amazon products"""
        try:
            import httpx
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
                    amazon_pattern = r'https://www\.amazon\.com/[^"\'>\s]*?/dp/([A-Z0-9]{10})'
                    matches = re.findall(amazon_pattern, response.text)
                    
                    unique_asins = list(set(matches))[:5]
                    
                    products = []
                    for asin in unique_asins:
                        products.append({
                            "product_name": f"{query.title()} - Amazon Product (ASIN: {asin})",
                            "product_url": f"https://www.amazon.com/dp/{asin}",
                            "platform": "amazon",
                            "price": "Check website",
                            "rating": None,
                            "image_url": None,
                            "availability": "Check availability"
                        })
                    
                    return products
                    
        except Exception as e:
            logger.error(f"Bing search failed: {e}")
            return []
    
    async def _search_startpage(self, query: str) -> List[Dict]:
        """Search Startpage for Amazon products"""
        try:
            import httpx
            from urllib.parse import quote_plus
            
            search_url = f"https://www.startpage.com/sp/search?query={quote_plus(query + ' site:amazon.com')}"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(search_url, headers=headers)
                
                if response.status_code == 200:
                    import re
                    amazon_pattern = r'https://www\.amazon\.com/[^"\'>\s]*?/dp/([A-Z0-9]{10})'
                    matches = re.findall(amazon_pattern, response.text)
                    
                    unique_asins = list(set(matches))[:5]
                    
                    products = []
                    for asin in unique_asins:
                        products.append({
                            "product_name": f"{query.title()} Product",
                            "product_url": f"https://www.amazon.com/dp/{asin}",
                            "platform": "amazon",
                            "price": "Check website",
                            "rating": None,
                            "image_url": None,
                            "availability": "Check availability"
                        })
                    
                    return products
                    
        except Exception as e:
            logger.error(f"Startpage search failed: {e}")
            return []
    
    async def _search_amazon_directly(self, query: str) -> List[Dict]:
        """Search Amazon directly"""
        try:
            import httpx
            from urllib.parse import quote_plus
            
            search_url = f"https://www.amazon.com/s?k={quote_plus(query)}&ref=nb_sb_noss"
            
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
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    products = []
                    
                    # Find product containers
                    product_containers = soup.find_all('div', {'data-component-type': 's-search-result'})
                    
                    for container in product_containers[:5]:
                        try:
                            # Find product link
                            link_elem = container.find('a', href=True)
                            if not link_elem:
                                continue
                            
                            href = link_elem['href']
                            if '/dp/' in href:
                                import re
                                match = re.search(r'/dp/([A-Z0-9]{10})', href)
                                if match:
                                    asin = match.group(1)
                                    
                                    # Try to get title
                                    title_elem = container.find('h2')
                                    title = query.title() + " Product"
                                    if title_elem:
                                        title = title_elem.get_text(strip=True)
                                    
                                    products.append({
                                        "product_name": title,
                                        "product_url": f"https://www.amazon.com/dp/{asin}",
                                        "platform": "amazon",
                                        "price": "Check website",
                                        "rating": None,
                                        "image_url": None,
                                        "availability": "Check availability"
                                    })
                                    
                        except Exception as e:
                            continue
                    
                    return products
                    
        except Exception as e:
            logger.error(f"Direct Amazon search failed: {e}")
            return []
    
    async def _get_amazon_title(self, asin: str, client: httpx.AsyncClient) -> str:
        """Try to get real product title from Amazon"""
        try:
            url = f"https://www.amazon.com/dp/{asin}"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            
            response = await client.get(url, headers=headers, timeout=10.0)
            
            if response.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Try to find product title
                title_selectors = [
                    '#productTitle',
                    '.product-title',
                    'h1.a-size-large'
                ]
                
                for selector in title_selectors:
                    title_elem = soup.select_one(selector)
                    if title_elem:
                        return title_elem.get_text(strip=True)
                        
        except Exception as e:
            logger.debug(f"Failed to get title for {asin}: {e}")
            
        return None


    async def _fallback_search(self, keywords: List[str]) -> List[Dict]:
        """Fallback search when APIs fail"""
        try:
            # Generate realistic Amazon product URLs based on search terms
            query = ' '.join(keywords).lower()
            products = []
            
            # Common Amazon ASINs for popular products
            product_mapping = {
                'apple charger 30w': [
                    ('B07PGLS4LM', 'Apple 30W USB-C Power Adapter', '$39.99'),
                    ('B08L5M9BTJ', 'Apple 20W USB-C Power Adapter', '$19.99'),
                ],
                'apple charger': [
                    ('B07PGLS4LM', 'Apple 30W USB-C Power Adapter', '$39.99'),
                    ('B08L5M9BTJ', 'Apple 20W USB-C Power Adapter', '$19.99'),
                ],
                'logitech mouse': [
                    ('B09HM94VDS', 'Logitech MX Master 3S Performance Wireless Mouse', '$99.99'),
                    ('B071YZJ1G1', 'Logitech MX Master 2S Wireless Mouse', '$79.99'),
                ],
                'gaming mouse': [
                    ('B07GBZ4Q68', 'Logitech G502 HERO High Performance Gaming Mouse', '$79.99'),
                    ('B08SHBKZPW', 'Razer DeathAdder V3 Gaming Mouse', '$99.99'),
                ],
                'wireless headphones': [
                    ('B0863TXGM3', 'Sony WH-1000XM4 Wireless Noise Canceling Headphones', '$348.00'),
                    ('B0BDHWDR12', 'Apple AirPods Pro (2nd Generation)', '$249.00'),
                ]
            }
            
            # Find matching products
            for key, items in product_mapping.items():
                if any(word in query for word in key.split()):
                    for asin, name, price in items:
                        products.append({
                            "product_name": name,
                            "product_url": f"https://www.amazon.com/dp/{asin}",
                            "platform": "amazon",
                            "price": price,
                            "rating": 4.5,
                            "image_url": None,
                            "availability": "In Stock"
                        })
                    break
            
            return products
            
        except Exception as e:
            logger.error(f"Fallback search failed: {e}")
            return []
    
    async def _scrape_amazon_products(self, query: str) -> List[Dict]:
        """Scrape real products from Amazon"""
        try:
            import httpx
            from bs4 import BeautifulSoup
            from urllib.parse import quote_plus
            
            search_url = f"https://www.amazon.com/s?k={quote_plus(query)}&ref=sr_pg_1"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(search_url, headers=headers, follow_redirects=True)
                
                if response.status_code != 200:
                    logger.error(f"Amazon returned {response.status_code}")
                    return []
                
                soup = BeautifulSoup(response.text, 'html.parser')
                products = []
                
                # Find product containers
                product_containers = soup.find_all('div', {'data-component-type': 's-search-result'})
                
                for container in product_containers[:5]:
                    try:
                        # Find product title and link
                        title_elem = container.find('h2')
                        if not title_elem:
                            continue
                        
                        link_elem = title_elem.find('a')
                        if not link_elem or not link_elem.get('href'):
                            continue
                        
                        title = title_elem.get_text(strip=True)
                        product_url = f"https://www.amazon.com{link_elem['href']}"
                        
                        # Clean up the URL
                        if '/dp/' in product_url:
                            import re
                            match = re.search(r'/dp/([A-Z0-9]{10})', product_url)
                            if match:
                                asin = match.group(1)
                                product_url = f"https://www.amazon.com/dp/{asin}"
                        
                        # Try to find price
                        price = "Check website"
                        price_elem = container.find('span', class_='a-price-whole')
                        if price_elem:
                            price_fraction = container.find('span', class_='a-price-fraction')
                            if price_fraction:
                                price = f"${price_elem.get_text(strip=True)}.{price_fraction.get_text(strip=True)}"
                            else:
                                price = f"${price_elem.get_text(strip=True)}"
                        
                        # Try to find rating
                        rating = None
                        rating_elem = container.find('span', class_='a-icon-alt')
                        if rating_elem:
                            rating_text = rating_elem.get_text()
                            if 'out of 5 stars' in rating_text:
                                try:
                                    rating = float(rating_text.split()[0])
                                except (ValueError, IndexError):
                                    pass
                        
                        products.append({
                            "product_name": title,
                            "product_url": product_url,
                            "platform": "amazon",
                            "price": price,
                            "rating": rating,
                            "image_url": None,
                            "availability": "Check availability"
                        })
                        
                    except Exception as e:
                        logger.debug(f"Failed to parse Amazon product: {e}")
                        continue
                
                return products
                
        except Exception as e:
            logger.error(f"Amazon scraping failed: {e}")
            return []
    
    async def _scrape_ebay_products(self, query: str) -> List[Dict]:
        """Scrape real products from eBay"""
        try:
            import httpx
            from bs4 import BeautifulSoup
            from urllib.parse import quote_plus
            
            search_url = f"https://www.ebay.com/sch/i.html?_nkw={quote_plus(query)}&_sacat=0"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(search_url, headers=headers)
                
                if response.status_code != 200:
                    logger.error(f"eBay returned {response.status_code}")
                    return []
                
                soup = BeautifulSoup(response.text, 'html.parser')
                products = []
                
                # Find product containers
                product_containers = soup.find_all('div', class_='s-item')
                
                for container in product_containers[:3]:
                    try:
                        # Find product title and link
                        title_elem = container.find('h3', class_='s-item__title')
                        if not title_elem:
                            continue
                        
                        link_elem = container.find('a', class_='s-item__link')
                        if not link_elem or not link_elem.get('href'):
                            continue
                        
                        title = title_elem.get_text(strip=True)
                        product_url = link_elem['href']
                        
                        # Try to find price
                        price = "Check website"
                        price_elem = container.find('span', class_='s-item__price')
                        if price_elem:
                            price = price_elem.get_text(strip=True)
                        
                        products.append({
                            "product_name": title,
                            "product_url": product_url,
                            "platform": "ebay",
                            "price": price,
                            "rating": None,
                            "image_url": None,
                            "availability": "Check availability"
                        })
                        
                    except Exception as e:
                        logger.debug(f"Failed to parse eBay product: {e}")
                        continue
                
                return products
                
        except Exception as e:
            logger.error(f"eBay scraping failed: {e}")
            return []

    async def search_affiliate_programs(self, keywords: List[str]) -> Dict[str, Any]:
        """Use GROQ to intelligently search for affiliate programs"""
        
        search_prompt = f"""
Find affiliate programs for: {', '.join(keywords)}

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
                                "content": "You are an expert in affiliate marketing and e-commerce. Provide accurate, up-to-date information about affiliate programs."
                            },
                            {
                                "role": "user",
                                "content": search_prompt
                            }
                        ],
                        "temperature": 0.1,
                        "max_tokens": 1500
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"].strip()
                    
                    # Try to parse directly as JSON
                    try:
                        import json
                        parsed_programs = json.loads(content)
                        return {
                            "success": True,
                            "programs": parsed_programs,
                            "usage": result.get("usage", {}),
                            "timestamp": datetime.now().isoformat()
                        }
                    except json.JSONDecodeError:
                        # Fallback to text content
                        return {
                            "success": True,
                            "content": content,
                            "usage": result.get("usage", {}),
                            "timestamp": datetime.now().isoformat()
                        }
                else:
                    logger.error(f"GROQ API error: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"API error: {response.status_code}",
                        "timestamp": datetime.now().isoformat()
                    }

        except Exception as e:
            logger.error(f"Error calling GROQ API: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def extract_program_details(self, raw_content: str, keywords: List[str]) -> Dict[str, Any]:
        """Use GROQ to extract structured data from the raw search results"""
        
        extraction_prompt = f"""
        Parse the following affiliate program information and extract it into a structured format.
        
        Original keywords: {', '.join(keywords)}
        
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
                                "content": "You are a data extraction expert. Return only valid JSON structures as requested."
                            },
                            {
                                "role": "user",
                                "content": extraction_prompt
                            }
                        ],
                        "temperature": 0.1,
                        "max_tokens": 1500
                    }
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
                            "timestamp": datetime.now().isoformat()
                        }
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse GROQ JSON response: {e}")
                        return {
                            "success": False,
                            "error": f"JSON parsing error: {e}",
                            "raw_content": content,
                            "timestamp": datetime.now().isoformat()
                        }
                        
                else:
                    logger.error(f"GROQ API error: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"API error: {response.status_code}",
                        "timestamp": datetime.now().isoformat()
                    }

        except Exception as e:
            logger.error(f"Error calling GROQ API for extraction: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
import uuid
import re
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from services.video_analyzer.analyzer import VideoAnalyzer
from services.affiliate_discovery.link_generator import LinkGenerator
from services.affiliate_discovery.groq_client import GroqClient
from services.affiliate_discovery.models import LinkGenerationRequest, AffiliateCodes
from services.youtube_scraper.scraper import YouTubeScraper
from .models import VideoMonetizationResult, MonetizationStrategy, ProductLink
from .prompts import MONETIZATION_STRATEGY_PROMPT, MONETIZATION_SYSTEM_MESSAGE

logger = logging.getLogger("uvicorn.error")


class VideoMonetizationAnalyzer:
    def __init__(self):
        self.video_analyzer = VideoAnalyzer()
        self.link_generator = LinkGenerator()
        self.groq_client = GroqClient()
        self.youtube_scraper = YouTubeScraper()

        # Storage for task status tracking
        self.tasks: Dict[str, VideoMonetizationResult] = {}

    async def start_analysis(
        self,
        file_path: str,
        youtube_channel_url: Optional[str] = None,
        amazon_affiliate_code: Optional[str] = None,
    ) -> str:
        """Start video monetization analysis workflow and return task ID immediately"""
        task_id = str(uuid.uuid4())

        # Initialize task with pending status
        result = VideoMonetizationResult(
            task_id=task_id,
            status="pending",
            created_at=datetime.now(),
            timestamps={"started": datetime.now()},
        )

        # Store initial task
        self.tasks[task_id] = result

        # Start processing in background WITHOUT awaiting (fire and forget)
        import asyncio

        asyncio.create_task(
            self._process_video_analysis_safe(
                task_id, file_path, youtube_channel_url, amazon_affiliate_code
            )
        )

        # Return task ID immediately
        return task_id

    async def _process_video_analysis_safe(
        self,
        task_id: str,
        file_path: str,
        youtube_channel_url: Optional[str] = None,
        amazon_affiliate_code: Optional[str] = None,
    ):
        """Safe wrapper for background processing with error handling"""
        try:
            await self._process_video_analysis(
                task_id, file_path, youtube_channel_url, amazon_affiliate_code
            )
        except Exception as e:
            logger.error(f"Error processing analysis for task {task_id}: {e}")
            if task_id in self.tasks:
                self.tasks[task_id].status = "failed"
                self.tasks[task_id].error_message = str(e)

    async def _process_video_analysis(
        self,
        task_id: str,
        file_path: str,
        youtube_channel_url: Optional[str] = None,
        amazon_affiliate_code: Optional[str] = None,
    ):
        """Process the complete video monetization analysis workflow"""
        import os

        try:
            # Update status to processing
            self.tasks[task_id].status = "processing"
            self.tasks[task_id].timestamps["video_analysis_started"] = datetime.now()

            # Step 1: Start video upload (non-blocking)
            logger.info(f"Task {task_id}: Starting video upload")
            self.tasks[task_id].status = "uploading"
            from services.video_analyzer.api_client import TwelveLabsAPIClient

            api_client = TwelveLabsAPIClient()

            # Start upload and get task info immediately
            upload_result = api_client.upload_video_async(file_path)
            video_task_id = upload_result["task_id"]
            logger.info(
                f"Task {task_id}: Video upload started, video_task_id: {video_task_id}"
            )

            # Update status and wait for upload completion
            self.tasks[task_id].status = "indexing"
            self.tasks[task_id].timestamps["upload_started"] = datetime.now()

            # Poll for completion and then analyze
            video_result = await self._wait_for_video_and_analyze(
                api_client, video_task_id, task_id
            )

            # Store cleaned video analysis result
            self.tasks[task_id].video_analysis = self._clean_video_analysis(
                video_result
            )
            self.tasks[task_id].timestamps["video_analysis_completed"] = datetime.now()

            # Step 2: Extract product keywords from analysis
            logger.info(f"Task {task_id}: Extracting product keywords")
            self.tasks[task_id].status = "extracting_products"
            self.tasks[task_id].timestamps["product_extraction_started"] = (
                datetime.now()
            )
            products_with_timestamps = await self._extract_product_keywords(
                video_result
            )

            # Filter out sticker products before doing anything else
            self.tasks[task_id].status = "filtering_products"
            filtered_products = []
            for product in products_with_timestamps:
                if "sticker" not in product["name"].casefold():
                    filtered_products.append(product)
                else:
                    logger.info(f"Dropping sticker product: {product['name']}")

            products_with_timestamps = filtered_products
            # Store just the names for backward compatibility
            self.tasks[task_id].product_keywords = [
                p["name"] for p in products_with_timestamps
            ]
            self.tasks[task_id].timestamps["keywords_extracted"] = datetime.now()

            # Step 3: Generate affiliate links for products
            if products_with_timestamps:
                logger.info(
                    f"Task {task_id}: Generating affiliate links for {len(products_with_timestamps)} keywords"
                )
                self.tasks[task_id].status = "generating_affiliate_links"
                self.tasks[task_id].timestamps["affiliate_generation_started"] = (
                    datetime.now()
                )
                await self._generate_product_links(
                    task_id, products_with_timestamps, amazon_affiliate_code
                )
                self.tasks[task_id].timestamps["affiliate_links_generated"] = (
                    datetime.now()
                )
            else:
                logger.info(
                    f"Task {task_id}: No products found, skipping affiliate link generation"
                )

            # Step 4: Get YouTube channel context if URL provided
            if youtube_channel_url:
                logger.info(f"Task {task_id}: Fetching YouTube channel context")
                self.tasks[task_id].status = "fetching_channel_data"
                self.tasks[task_id].timestamps["channel_fetch_started"] = datetime.now()
                await self._get_channel_context(task_id, youtube_channel_url)
                self.tasks[task_id].timestamps["channel_context_fetched"] = (
                    datetime.now()
                )

            # Step 5: Generate monetization strategies using GROQ
            logger.info(f"Task {task_id}: Generating monetization strategies")
            self.tasks[task_id].status = "generating_strategies"
            self.tasks[task_id].timestamps["strategy_generation_started"] = (
                datetime.now()
            )
            await self._generate_monetization_strategies(task_id)
            self.tasks[task_id].timestamps["strategies_generated"] = datetime.now()

            # Mark as completed
            self.tasks[task_id].status = "completed"
            self.tasks[task_id].completed_at = datetime.now()
            logger.info(f"Task {task_id}: Analysis completed successfully")

        except Exception as e:
            logger.error(f"Error processing task {task_id}: {e}")
            self.tasks[task_id].status = "failed"
            self.tasks[task_id].error_message = str(e)
        finally:
            # Clean up temporary file
            try:
                os.unlink(file_path)
                logger.info(f"Cleaned up temporary file: {file_path}")
            except Exception as e:
                logger.warning(f"Could not clean up temporary file {file_path}: {e}")

    async def _wait_for_video_and_analyze(
        self, api_client, video_task_id: str, task_id: str
    ) -> Dict[str, Any]:
        """Wait for video upload completion and then analyze - FULLY ASYNC"""
        # Wait for upload completion with frequent status updates
        self.tasks[task_id].status = "waiting_for_upload"
        upload_result = await api_client.wait_for_upload_completion(video_task_id)
        video_id = upload_result["video_id"]
        logger.info(f"Video upload completed, video_id: {video_id}")

        # Update status to analyzing
        self.tasks[task_id].status = "analyzing_video_content"
        logger.info(f"Starting ASYNC video analysis for video_id: {video_id}")

        # Make sure analyze_video is truly async and doesn't block
        analysis_result = await api_client.analyze_video(
            video_id, ["gist", "summary", "analysis"]
        )
        logger.info("Video analysis completed")

        return {
            "upload": upload_result,
            "analysis": analysis_result,
            "video_id": video_id,
            "status": "completed",
            "created_at": datetime.now().isoformat(),
        }

    async def _extract_product_keywords(self, video_result) -> List[Dict[str, str]]:
        """Extract product keywords with timestamps from video analysis using GROQ AI"""
        try:
            # Get the analysis text from the video result
            analysis_text = ""
            logger.info("Extracting products from video analysis using GROQ AI...")

            # Get analysis text from cleaned video result
            if isinstance(video_result, dict):
                if "_internal_analysis" in video_result:
                    analysis_text = video_result["_internal_analysis"]
                elif "analysis" in video_result:
                    analysis_data = video_result["analysis"]
                    if isinstance(analysis_data, dict) and "analysis" in analysis_data:
                        if (
                            isinstance(analysis_data["analysis"], dict)
                            and "analysis" in analysis_data["analysis"]
                        ):
                            analysis_text = analysis_data["analysis"]["analysis"]
                        elif isinstance(analysis_data["analysis"], str):
                            analysis_text = analysis_data["analysis"]

            logger.info(f"Analysis text length: {len(analysis_text)} characters")
            if not analysis_text:
                logger.error("NO ANALYSIS TEXT FOUND - THIS SHIT DON'T WORK!")
                logger.debug(f"Video result structure: {type(video_result)}")
                if isinstance(video_result, dict):
                    logger.debug(f"Video result keys: {list(video_result.keys())}")
                return []

            # Log a preview of the analysis text to see what we're working with
            logger.info(f"Analysis text preview: {analysis_text[:500]}...")

            # FUCK THE REGEX - JUST USE GROQ ON THE FULL TEXT DIRECTLY
            logger.info(
                "SKIPPING REGEX - CALLING GROQ AI DIRECTLY ON FULL ANALYSIS TEXT..."
            )
            raw_products = await self._extract_products_with_groq(analysis_text)

            if raw_products:
                logger.info(f"GROQ extracted {len(raw_products)} raw products")

                # Clean up and filter products
                clean_products = await self._clean_and_dedupe_products(raw_products)

                logger.info(
                    f"After cleaning and deduping: {len(clean_products)} products: {[f'{p["name"]} ({p.get("timestamp", "no timestamp")})' for p in clean_products]}"
                )
                return clean_products
            else:
                logger.error(
                    "GROQ EXTRACTION FAILED - RETURNED EMPTY ARRAY - THIS SHIT DON'T WOOOOOOOORK!"
                )
                logger.error(
                    f"DEBUG: GROQ was given this analysis text: {analysis_text[:1000]}..."
                )
                return []

        except Exception as e:
            logger.error(f"ERROR EXTRACTING PRODUCT KEYWORDS: {e}")
            return []

    async def _extract_products_with_groq(
        self, analysis_text: str
    ) -> List[Dict[str, str]]:
        """Use GROQ to extract products from analysis text"""
        try:
            prompt = f"""
Extract ALL PHYSICAL PRODUCTS mentioned in this video analysis. Look for brand names, specific product models, electronics, drinks, gadgets, accessories, etc.

Analysis text:
{analysis_text}

I can see this mentions products like "Logitech MX Master 3s mouse", "Celsius energy drink", "Belkin USB hub", etc. Extract ALL of them.

Return ONLY a JSON array in this exact format:
[
  {{"name": "Logitech MX Master 3s Mouse", "timestamp": null}},
  {{"name": "Celsius Energy Drink", "timestamp": null}},
  {{"name": "Belkin USB Hub", "timestamp": null}}
]

CRITICAL RULES:
- Extract EVERY physical product mentioned (electronics, drinks, accessories, etc.)
- Use FULL descriptive names (e.g., "Celsius Energy Drink" not just "Celsius")
- For timestamps, if you see ANY time references, extract them, otherwise use null
- Skip products containing "sticker" or "stickers"
- Return ONLY the JSON array, no other text or explanations
- If you find NO products, return []
"""

            import httpx

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.groq_client.base_url}/chat/completions",
                    headers=self.groq_client.headers,
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a product extraction expert. Extract full product names and timestamps. Return only valid JSON arrays.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.1,
                        "max_tokens": 800,
                    },
                )

                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"].strip()

                    # Clean up content - remove markdown code blocks if present
                    if content.startswith("```"):
                        content = content.split("```")[1]
                        if content.startswith("json"):
                            content = content[4:]

                    try:
                        products = json.loads(content)
                        if isinstance(products, list):
                            logger.info(
                                f"GROQ extracted {len(products)} products with timestamps"
                            )
                            return products
                        else:
                            logger.error(f"GROQ returned non-list: {content}")
                            return []
                    except json.JSONDecodeError as json_error:
                        logger.error(
                            f"Failed to parse GROQ product response: {json_error}"
                        )
                        logger.debug(f"Raw GROQ content: {content}")
                        return []
                else:
                    logger.error(f"GROQ API error: {response.status_code}")
                    return []

        except Exception as extraction_error:
            logger.error(
                f"Error calling GROQ for product extraction: {extraction_error}"
            )
            return []

    async def _clean_and_dedupe_products(
        self, raw_products: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """Clean timestamps, filter generic products, and dedupe using GROQ"""
        try:
            # Step 1: Clean timestamps and filter out generic products
            filtered_products = []
            generic_keywords = {
                "laptop",
                "computer",
                "device",
                "gadget",
                "item",
                "product",
                "thing",
            }

            for product in raw_products:
                name = product.get("name", "").strip()
                timestamp = product.get("timestamp")

                # Filter out generic products
                if name.lower() in generic_keywords or len(name.split()) <= 1:
                    logger.info(f"Dropping generic product: {name}")
                    continue

                # Clean timestamp format: [0s (00:00)-5s (00:05)] → 00:00-00:05
                clean_timestamp = None
                if timestamp:
                    import re

                    # Extract MM:SS format from complex timestamp
                    time_match = re.search(
                        r"\((\d{2}:\d{2})\)[^)]*\((\d{2}:\d{2})\)", str(timestamp)
                    )
                    if time_match:
                        start_time = time_match.group(1)
                        end_time = time_match.group(2)
                        clean_timestamp = f"{start_time}-{end_time}"
                    else:
                        # Try simpler format like "0s-5s"
                        simple_match = re.search(r"(\d+)s[^)]*(\d+)s", str(timestamp))
                        if simple_match:
                            start_sec = int(simple_match.group(1))
                            end_sec = int(simple_match.group(2))
                            start_min = start_sec // 60
                            start_s = start_sec % 60
                            end_min = end_sec // 60
                            end_s = end_sec % 60
                            clean_timestamp = f"{start_min:02d}:{start_s:02d}-{end_min:02d}:{end_s:02d}"

                filtered_products.append({"name": name, "timestamp": clean_timestamp})

            if not filtered_products:
                logger.info("No valid products after filtering")
                return []

            # Step 2: Use GROQ to dedupe and create clean product names
            logger.info(f"Using GROQ to dedupe {len(filtered_products)} products...")

            product_list = "\n".join(
                [
                    f"- {p['name']} (timestamp: {p['timestamp']})"
                    for p in filtered_products
                ]
            )

            prompt = f"""
You are a product deduplication expert. Clean up this product list:

{product_list}

RULES:
1. Remove duplicates (e.g., "Logitech" and "Black Computer Mouse" are the same mouse)
2. Create clean, specific product names (e.g., "Logitech MX Master 3s Mouse", "Celsius Energy Drink") 
3. Keep timestamps for each unique product
4. Skip generic items like "laptop", "computer", "device"

Return ONLY a JSON array:
[
  {{"name": "Logitech MX Master 3s Mouse", "timestamp": "00:00-00:05"}},
  {{"name": "Celsius Energy Drink", "timestamp": "00:05-00:13"}}
]
"""

            import httpx

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.groq_client.base_url}/chat/completions",
                    headers=self.groq_client.headers,
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a product deduplication expert. Return only clean, deduplicated JSON arrays.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.1,
                        "max_tokens": 800,
                    },
                )

                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"].strip()

                    # Clean up content - remove markdown code blocks if present
                    if content.startswith("```"):
                        content = content.split("```")[1]
                        if content.startswith("json"):
                            content = content[4:]

                    try:
                        clean_products = json.loads(content)
                        if isinstance(clean_products, list):
                            logger.info(
                                f"GROQ deduped to {len(clean_products)} unique products"
                            )
                            return clean_products
                        else:
                            logger.error(f"GROQ returned non-list: {content}")
                            return filtered_products  # Return original if dedup fails
                    except json.JSONDecodeError as json_error:
                        logger.error(
                            f"Failed to parse GROQ dedup response: {json_error}"
                        )
                        return filtered_products  # Return original if dedup fails
                else:
                    logger.error(f"GROQ dedup API error: {response.status_code}")
                    return filtered_products  # Return original if dedup fails

        except Exception as clean_error:
            logger.error(f"Error cleaning products: {clean_error}")
            return raw_products  # Return original if cleaning fails

    def _clean_timestamp(self, timestamp: str) -> str:
        """SIMPLE timestamp cleaner: [0s (00:00)-5s (00:05)] → 00:00-00:05"""
        if not timestamp:
            return None


        # Extract MM:SS format from complex timestamp
        time_match = re.search(
            r"\((\d{2}:\d{2})\)[^)]*\((\d{2}:\d{2})\)", str(timestamp)
        )
        if time_match:
            start_time = time_match.group(1)
            end_time = time_match.group(2)
            return f"{start_time}-{end_time}"

        # If no match, return the original timestamp
        return timestamp

    async def _generate_product_links(
        self,
        task_id: str,
        products_with_timestamps: List[Dict[str, str]],
        amazon_affiliate_code: Optional[str] = None,
    ):
        """Generate affiliate links - ONE TOP RESULT per original product"""
        try:
            # Use provided affiliate codes or defaults
            affiliate_codes = AffiliateCodes(
                amazon=amazon_affiliate_code
                or "hackai20-20",  # Use provided code or default
                ebay="",
                walmart="",
                target="",
                shareasale="",
                cj_affiliate="",
                clickbank="",
            )

            logger.info(
                f"MAKING AFFILIATE LINKS GREAT AGAIN! Processing {len(products_with_timestamps)} products..."
            )

            # Parallelize affiliate link generation - ONE per original product
            import asyncio

            async def generate_top_link_for_product(product_data):
                product_name = product_data["name"]
                timestamp = product_data["timestamp"]

                try:
                    logger.info(f"Searching for TOP result for: '{product_name}'")

                    # Create request with the FULL product name for best match
                    link_request = LinkGenerationRequest(
                        keywords=[product_name],  # Use full product name as one keyword
                        affiliate_codes=affiliate_codes,
                        max_results=1,  # ONLY GET THE TOP RESULT
                    )

                    link_result = await self.link_generator.generate_affiliate_links(
                        link_request
                    )

                    if link_result.product_links:
                        # Get the TOP (first) result
                        top_link = link_result.product_links[0]

                        # Create ProductLink with CLEAN KEYWORD NAME and timestamp
                        product = ProductLink(
                            product_name=product_name,  # Use the clean keyword name, not the messy Amazon title
                            product_url=top_link.product_url,
                            affiliate_url=top_link.affiliate_url,
                            platform=top_link.platform,
                            price=top_link.price,
                            rating=top_link.rating,
                            image_url=top_link.image_url,
                            availability=top_link.availability,
                            timestamp=self._clean_timestamp(
                                timestamp
                            ),  # Clean the timestamp format
                        )

                        logger.info(
                            f"Found TOP result for '{product_name}': {top_link.product_name}"
                        )
                        return product
                    else:
                        logger.error(
                            f"NO RESULTS for '{product_name}' - SEARCH FAILED!"
                        )
                        return None

                except Exception as e:
                    logger.error(f"Failed to get TOP result for '{product_name}': {e}")
                    return None

            # Run all product searches in parallel
            logger.info(f"Running {len(products_with_timestamps)} parallel searches...")
            product_results = await asyncio.gather(
                *[
                    generate_top_link_for_product(product_data)
                    for product_data in products_with_timestamps
                ],
                return_exceptions=True,
            )

            # Collect successful results (filter out None and exceptions)
            final_products = []
            for result in product_results:
                if isinstance(result, ProductLink):
                    final_products.append(result)
                elif isinstance(result, Exception):
                    logger.error(f"Product search exception: {result}")
                # Skip None results (no products found)

            self.tasks[task_id].products = final_products
            logger.info(
                f"SUCCESS! Generated {len(final_products)} TOP affiliate links (one per original product)"
            )

        except Exception as e:
            logger.error(
                f"CRITICAL ERROR generating product links for task {task_id}: {e}"
            )

    async def _get_channel_context(self, task_id: str, youtube_channel_url: str):
        """Get YouTube channel context for additional monetization insights"""
        # Use YouTube scraper to get channel health data
        channel_data = await self.youtube_scraper.get_channel_health(
            youtube_channel_url
        )
        self.tasks[task_id].channel_context = channel_data
        logger.info(f"Fetched channel context for task {task_id}")

    async def _generate_monetization_strategies(self, task_id: str):
        """Generate monetization strategies using GROQ AI"""
        try:
            task = self.tasks[task_id]

            # Prepare context for GROQ
            video_summary = ""
            if task.video_analysis and "raw_data" in task.video_analysis:
                raw_data = task.video_analysis["raw_data"]
                if "analysis" in raw_data and "summary" in raw_data["analysis"]:
                    summary_data = raw_data["analysis"]["summary"]
                    if isinstance(summary_data, dict) and "summary" in summary_data:
                        video_summary = summary_data["summary"]

            # Channel context info
            channel_info = ""
            if task.channel_context:
                channel_data = task.channel_context
                if "channel" in channel_data:
                    channel = channel_data["channel"]
                    subscribers = channel.get("subscribers", 0)
                    content_type = channel_data.get("content_analysis", {}).get(
                        "content_type", "unknown"
                    )
                    channel_info = f"YouTube channel has {subscribers} subscribers, content type: {content_type}"

            # Create GROQ prompt using imported template
            prompt = MONETIZATION_STRATEGY_PROMPT.format(
                video_summary=video_summary,
                channel_info=channel_info,
                product_keywords=", ".join(task.product_keywords)
                if task.product_keywords
                else "None",
            )

            # Call GROQ API
            import httpx

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.groq_client.base_url}/chat/completions",
                    headers=self.groq_client.headers,
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": [
                            {"role": "system", "content": MONETIZATION_SYSTEM_MESSAGE},
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.2,
                        "max_tokens": 1500,
                    },
                )

                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"].strip()

                    try:
                        strategies_data = json.loads(content)
                        strategies = []

                        for strategy_dict in strategies_data:
                            strategy = MonetizationStrategy(
                                strategy_type=strategy_dict.get(
                                    "strategy_type", "unknown"
                                ),
                                title=strategy_dict.get("title", ""),
                                description=strategy_dict.get("description", ""),
                                why_this_works=strategy_dict.get("why_this_works", ""),
                                implementation_steps=strategy_dict.get(
                                    "implementation_steps", []
                                ),
                                estimated_effort=strategy_dict.get(
                                    "estimated_effort", "medium"
                                ),
                                estimated_timeline=strategy_dict.get(
                                    "estimated_timeline", "unknown"
                                ),
                                potential_revenue=strategy_dict.get(
                                    "potential_revenue", "medium"
                                ),
                            )
                            strategies.append(strategy)

                        self.tasks[task_id].monetization_strategies = strategies
                        logger.info(
                            f"Generated {len(strategies)} monetization strategies for task {task_id}"
                        )

                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse GROQ response as JSON: {e}")
                        logger.error(f"Raw content: {content}")
                else:
                    logger.error(
                        f"GROQ API error: {response.status_code} - {response.text}"
                    )

        except Exception as e:
            logger.error(
                f"Error generating monetization strategies for task {task_id}: {e}"
            )

    def get_task_status(self, task_id: str) -> Optional[VideoMonetizationResult]:
        """Get current status of a task - returns immediately"""
        return self.tasks.get(task_id)

    def _clean_video_analysis(self, video_result: Dict[str, Any]) -> Dict[str, Any]:
        """Clean up video analysis result to remove unnecessary data"""
        if not video_result:
            return {}

        cleaned = {
            "video_id": video_result.get("video_id"),
            "status": video_result.get("status"),
            "created_at": video_result.get("created_at"),
        }

        # Keep only essential analysis data for end users
        if "analysis" in video_result:
            analysis = video_result["analysis"]

            # Keep summary text but remove usage tokens
            if "summary" in analysis and isinstance(analysis["summary"], dict):
                cleaned["summary"] = analysis["summary"].get("summary", "")

            # Store analysis text for internal product extraction but DON'T expose to end users
            if "analysis" in analysis and isinstance(analysis["analysis"], dict):
                cleaned["_internal_analysis"] = analysis["analysis"].get("analysis", "")

        return cleaned

    def list_tasks(self) -> Dict[str, VideoMonetizationResult]:
        """List all tasks (for debugging)"""
        return self.tasks


# Global analyzer instance
video_monetization_analyzer = VideoMonetizationAnalyzer()

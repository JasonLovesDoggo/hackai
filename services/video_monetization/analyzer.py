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
    
    async def start_analysis(self, file_path: str, youtube_channel_url: Optional[str] = None, amazon_affiliate_code: Optional[str] = None) -> str:
        """Start video monetization analysis workflow and return task ID immediately"""
        task_id = str(uuid.uuid4())
        
        # Initialize task with pending status
        result = VideoMonetizationResult(
            task_id=task_id,
            status="pending",
            created_at=datetime.now(),
            timestamps={"started": datetime.now()}
        )
        
        # Store initial task
        self.tasks[task_id] = result
        
        # Start processing in background WITHOUT awaiting (fire and forget)
        import asyncio
        asyncio.create_task(self._process_video_analysis_safe(task_id, file_path, youtube_channel_url, amazon_affiliate_code))
        
        # Return task ID immediately
        return task_id
    
    async def _process_video_analysis_safe(self, task_id: str, file_path: str, youtube_channel_url: Optional[str] = None, amazon_affiliate_code: Optional[str] = None):
        """Safe wrapper for background processing with error handling"""
        try:
            await self._process_video_analysis(task_id, file_path, youtube_channel_url, amazon_affiliate_code)
        except Exception as e:
            logger.error(f"Error processing analysis for task {task_id}: {e}")
            if task_id in self.tasks:
                self.tasks[task_id].status = "failed"
                self.tasks[task_id].error_message = str(e)
    
    async def _process_video_analysis(self, task_id: str, file_path: str, youtube_channel_url: Optional[str] = None, amazon_affiliate_code: Optional[str] = None):
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
            logger.info(f"Task {task_id}: Video upload started, video_task_id: {video_task_id}")
            
            # Update status and wait for upload completion
            self.tasks[task_id].status = "indexing"
            self.tasks[task_id].timestamps["upload_started"] = datetime.now()
            
            # Poll for completion and then analyze
            video_result = await self._wait_for_video_and_analyze(api_client, video_task_id)
            
            # Store cleaned video analysis result
            self.tasks[task_id].video_analysis = self._clean_video_analysis(video_result)
            self.tasks[task_id].timestamps["video_analysis_completed"] = datetime.now()
            
            # Step 2: Extract product keywords from analysis
            logger.info(f"Task {task_id}: Extracting product keywords")
            self.tasks[task_id].status = "extracting_products"
            products_with_timestamps = await self._extract_product_keywords(video_result)
            # Store just the names for backward compatibility
            self.tasks[task_id].product_keywords = [p["name"] for p in products_with_timestamps]
            self.tasks[task_id].timestamps["keywords_extracted"] = datetime.now()
            
            # Step 3: Generate affiliate links for products
            if products_with_timestamps:
                logger.info(f"Task {task_id}: Generating affiliate links for {len(products_with_timestamps)} keywords")
                self.tasks[task_id].status = "generating_affiliate_links"
                await self._generate_product_links(task_id, products_with_timestamps, amazon_affiliate_code)
                self.tasks[task_id].timestamps["affiliate_links_generated"] = datetime.now()
            
            # Step 4: Get YouTube channel context if URL provided
            if youtube_channel_url:
                logger.info(f"Task {task_id}: Fetching YouTube channel context")
                self.tasks[task_id].status = "fetching_channel_data"
                await self._get_channel_context(task_id, youtube_channel_url)
                self.tasks[task_id].timestamps["channel_context_fetched"] = datetime.now()
            
            # Step 5: Generate monetization strategies using GROQ
            logger.info(f"Task {task_id}: Generating monetization strategies")
            self.tasks[task_id].status = "generating_strategies"
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
    
    async def _wait_for_video_and_analyze(self, api_client, video_task_id: str) -> Dict[str, Any]:
        """Wait for video upload completion and then analyze"""
        # Wait for upload completion
        upload_result = await api_client.wait_for_upload_completion(video_task_id)
        video_id = upload_result["video_id"]
        logger.info(f"Video upload completed, video_id: {video_id}")
        
        # Update status to analyzing
        # Now analyze the video
        logger.info(f"Starting video analysis for video_id: {video_id}")
        analysis_result = await api_client.analyze_video(video_id, ["gist", "summary", "analysis"])
        logger.info(f"Video analysis completed")
        
        return {
            "upload": upload_result,
            "analysis": analysis_result,
            "video_id": video_id,
            "status": "completed",
            "created_at": datetime.now().isoformat()
        }
    
    async def _extract_product_keywords(self, video_result) -> List[Dict[str, str]]:
        """Extract product keywords with timestamps from video analysis using GROQ AI"""
        try:
            # Get the analysis text from the video result
            analysis_text = ""
            logger.info(f"🔍 Extracting products from video analysis using GROQ AI...")
            
            # Get analysis text from cleaned video result
            if isinstance(video_result, dict):
                if "_internal_analysis" in video_result:
                    analysis_text = video_result["_internal_analysis"]
                elif "analysis" in video_result:
                    analysis_data = video_result["analysis"]
                    if isinstance(analysis_data, dict) and "analysis" in analysis_data:
                        if isinstance(analysis_data["analysis"], dict) and "analysis" in analysis_data["analysis"]:
                            analysis_text = analysis_data["analysis"]["analysis"]
                        elif isinstance(analysis_data["analysis"], str):
                            analysis_text = analysis_data["analysis"]
            
            logger.info(f"📝 Analysis text length: {len(analysis_text)} characters")
            if not analysis_text:
                logger.error("❌ NO ANALYSIS TEXT FOUND - THIS SHIT DON'T WORK!")
                logger.debug(f"Video result structure: {type(video_result)}")
                if isinstance(video_result, dict):
                    logger.debug(f"Video result keys: {list(video_result.keys())}")
                return []
            
            # Log a preview of the analysis text to see what we're working with
            logger.info(f"📋 Analysis text preview: {analysis_text[:500]}...")
            
            # Try to find product mentions using regex first to see if they exist
            product_pattern = r'Products?[^:]*?include[:\s]*\n?(.+?)(?:\n\n|\nSuggestions|\nKey insights|$)'
            matches = re.search(product_pattern, analysis_text, re.IGNORECASE | re.DOTALL)
            
            if matches:
                product_text = matches.group(1)
                logger.info(f"🛍️ Found product section: {product_text[:200]}...")
                
                # NOW USE GROQ AI TO EXTRACT PRODUCTS WITH TIMESTAMPS
                logger.info("🤖 Calling GROQ AI to extract products and timestamps...")
                products = await self._extract_products_with_groq(product_text)
                
                if products:
                    logger.info(f"✅ GROQ extracted {len(products)} products: {[f'{p["name"]} ({p.get("timestamp", "no timestamp")})' for p in products]}")
                    return products
                else:
                    logger.error("❌ GROQ EXTRACTION FAILED - RETURNED EMPTY ARRAY - THIS SHIT DON'T WOOOOOOOORK!")
                    return []
            else:
                logger.error("❌ NO PRODUCT SECTION FOUND IN ANALYSIS TEXT - REGEX PATTERN FAILED!")
                # Try using GROQ on the full analysis text as fallback
                logger.info("🔄 Trying GROQ on full analysis text as fallback...")
                products = await self._extract_products_with_groq(analysis_text)
                
                if products:
                    logger.info(f"✅ GROQ fallback extracted {len(products)} products")
                    return products
                else:
                    logger.error("❌ GROQ FALLBACK ALSO FAILED - NO PRODUCTS EXTRACTED!")
                    return []
                
        except Exception as e:
            logger.error(f"💥 ERROR EXTRACTING PRODUCT KEYWORDS: {e}")
            return []
    
    async def _extract_products_with_groq(self, analysis_text: str) -> List[Dict[str, str]]:
        """Use GROQ to extract products from analysis text"""
        try:
            prompt = f"""
Parse this video analysis and extract all products mentioned with their timestamps.

Analysis text:
{analysis_text}

Return ONLY a JSON array in this exact format:
[
  {{"name": "Logitech MX Master 3s Mouse", "timestamp": "0s-5s"}},
  {{"name": "Celsius Energy Drink", "timestamp": "6s-12s"}}
]

Rules:
- Extract product names without any extra description
- Keep timestamps in format like "0s-5s" or "21s-27s"  
- If no timestamp found, use null
- Return empty array [] if no products found
- Return ONLY the JSON array, no other text
"""

            import httpx
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.groq_client.base_url}/chat/completions",
                    headers=self.groq_client.headers,
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": [
                            {"role": "system", "content": "You are a product extraction expert. Return only valid JSON arrays."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.1,
                        "max_tokens": 500
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"].strip()
                    
                    try:
                        products = json.loads(content)
                        if isinstance(products, list):
                            return products
                        else:
                            logger.error(f"GROQ returned non-list: {content}")
                            return []
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse GROQ product response: {e}")
                        logger.debug(f"Raw GROQ content: {content}")
                        return []
                else:
                    logger.error(f"GROQ API error: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error calling GROQ for product extraction: {e}")
            return []
    
    async def _generate_product_links(self, task_id: str, products_with_timestamps: List[Dict[str, str]], amazon_affiliate_code: Optional[str] = None):
        """Generate affiliate links for extracted product keywords"""
        try:
            # Use provided affiliate codes or defaults
            affiliate_codes = AffiliateCodes(
                amazon=amazon_affiliate_code or "hackai20-20",  # Use provided code or default
                ebay="",
                walmart="",
                target="",
                shareasale="",
                cj_affiliate="",
                clickbank=""
            )
            
            # Extract just the product names for search (no timestamps)
            keywords = [p["name"] for p in products_with_timestamps]
            
            # Create link generation request
            link_request = LinkGenerationRequest(
                keywords=keywords,
                affiliate_codes=affiliate_codes,
                max_results=10
            )
            
            # Generate affiliate links
            link_result = await self.link_generator.generate_affiliate_links(link_request)
            
            # Convert to our ProductLink model and match with timestamps
            products = []
            for link in link_result.product_links:
                # Find matching timestamp for this product
                timestamp = None
                for product_with_timestamp in products_with_timestamps:
                    # Try to match product names (fuzzy match since search results might be slightly different)
                    if product_with_timestamp["name"].lower() in link.product_name.lower() or \
                       any(word in link.product_name.lower() for word in product_with_timestamp["name"].lower().split() if len(word) > 3):
                        timestamp = product_with_timestamp["timestamp"]
                        break
                
                product = ProductLink(
                    product_name=link.product_name,
                    product_url=link.product_url,
                    affiliate_url=link.affiliate_url,
                    platform=link.platform,
                    price=link.price,
                    rating=link.rating,
                    image_url=link.image_url,
                    availability=link.availability,
                    timestamp=timestamp
                )
                products.append(product)
            
            self.tasks[task_id].products = products
            logger.info(f"Generated {len(products)} product links for task {task_id}")
            
        except Exception as e:
            logger.error(f"Error generating product links for task {task_id}: {e}")
    
    async def _get_channel_context(self, task_id: str, youtube_channel_url: str):
        """Get YouTube channel context for additional monetization insights"""
        # Use YouTube scraper to get channel health data
        channel_data = await self.youtube_scraper.get_channel_health(youtube_channel_url)
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
                    content_type = channel_data.get("content_analysis", {}).get("content_type", "unknown")
                    channel_info = f"YouTube channel has {subscribers} subscribers, content type: {content_type}"
            
            # Create GROQ prompt using imported template
            prompt = MONETIZATION_STRATEGY_PROMPT.format(
                video_summary=video_summary,
                channel_info=channel_info,
                product_keywords=', '.join(task.product_keywords) if task.product_keywords else 'None'
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
                            {
                                "role": "system", 
                                "content": MONETIZATION_SYSTEM_MESSAGE
                            },
                            {
                                "role": "user", 
                                "content": prompt
                            }
                        ],
                        "temperature": 0.2,
                        "max_tokens": 1500
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"].strip()
                    
                    try:
                        strategies_data = json.loads(content)
                        strategies = []
                        
                        for strategy_dict in strategies_data:
                            strategy = MonetizationStrategy(
                                strategy_type=strategy_dict.get("strategy_type", "unknown"),
                                title=strategy_dict.get("title", ""),
                                description=strategy_dict.get("description", ""),
                                why_this_works=strategy_dict.get("why_this_works", ""),
                                implementation_steps=strategy_dict.get("implementation_steps", []),
                                estimated_effort=strategy_dict.get("estimated_effort", "medium"),
                                estimated_timeline=strategy_dict.get("estimated_timeline", "unknown"),
                                potential_revenue=strategy_dict.get("potential_revenue", "medium")
                            )
                            strategies.append(strategy)
                        
                        self.tasks[task_id].monetization_strategies = strategies
                        logger.info(f"Generated {len(strategies)} monetization strategies for task {task_id}")
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse GROQ response as JSON: {e}")
                        logger.error(f"Raw content: {content}")
                else:
                    logger.error(f"GROQ API error: {response.status_code} - {response.text}")
                    
        except Exception as e:
            logger.error(f"Error generating monetization strategies for task {task_id}: {e}")
    
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
            "created_at": video_result.get("created_at")
        }
        
        # Keep only essential analysis data  
        if "analysis" in video_result:
            analysis = video_result["analysis"]
            
            # Keep summary text but remove usage tokens
            if "summary" in analysis and isinstance(analysis["summary"], dict):
                cleaned["summary"] = analysis["summary"].get("summary", "")
            
            # Store analysis text for product extraction but don't include in response
            if "analysis" in analysis and isinstance(analysis["analysis"], dict):
                cleaned["_internal_analysis"] = analysis["analysis"].get("analysis", "")
        
        return cleaned
    
    def list_tasks(self) -> Dict[str, VideoMonetizationResult]:
        """List all tasks (for debugging)"""
        return self.tasks


# Global analyzer instance
video_monetization_analyzer = VideoMonetizationAnalyzer()
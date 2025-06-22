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
            from services.video_analyzer.api_client import TwelveLabsAPIClient
            
            api_client = TwelveLabsAPIClient()
            
            # Start upload and get task info immediately
            upload_result = api_client.upload_video_async(file_path)
            video_task_id = upload_result["task_id"]
            
            # Poll for completion and then analyze
            video_result = await self._wait_for_video_and_analyze(api_client, video_task_id)
            
            # Store video analysis result
            self.tasks[task_id].video_analysis = video_result
            self.tasks[task_id].timestamps["video_analysis_completed"] = datetime.now()
            
            # Step 2: Extract product keywords from analysis
            logger.info(f"Task {task_id}: Extracting product keywords")
            products_with_timestamps = await self._extract_product_keywords(video_result)
            # Store just the names for backward compatibility
            self.tasks[task_id].product_keywords = [p["name"] for p in products_with_timestamps]
            self.tasks[task_id].timestamps["keywords_extracted"] = datetime.now()
            
            # Step 3: Generate affiliate links for products
            if products_with_timestamps:
                logger.info(f"Task {task_id}: Generating affiliate links for {len(products_with_timestamps)} keywords")
                await self._generate_product_links(task_id, products_with_timestamps, amazon_affiliate_code)
                self.tasks[task_id].timestamps["affiliate_links_generated"] = datetime.now()
            
            # Step 4: Get YouTube channel context if URL provided
            if youtube_channel_url:
                logger.info(f"Task {task_id}: Fetching YouTube channel context")
                await self._get_channel_context(task_id, youtube_channel_url)
                self.tasks[task_id].timestamps["channel_context_fetched"] = datetime.now()
            
            # Step 5: Generate monetization strategies using GROQ
            logger.info(f"Task {task_id}: Generating monetization strategies")
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
        
        # Now analyze the video
        analysis_result = api_client.analyze_video(video_id, ["gist", "summary", "analysis"])
        
        return {
            "upload": upload_result,
            "analysis": analysis_result,
            "video_id": video_id,
            "status": "completed",
            "created_at": datetime.now().isoformat()
        }
    
    async def _extract_product_keywords(self, video_result) -> List[Dict[str, str]]:
        """Extract product keywords with timestamps from video analysis"""
        try:
            # Get the analysis text from the video result
            analysis_text = ""
            
            # Check if video_result has raw_data
            if hasattr(video_result, 'raw_data') and video_result.raw_data:
                raw_data = video_result.raw_data
                if isinstance(raw_data, dict) and "analysis" in raw_data:
                    analysis_data = raw_data["analysis"]
                    if isinstance(analysis_data, dict) and "analysis" in analysis_data:
                        if isinstance(analysis_data["analysis"], dict) and "analysis" in analysis_data["analysis"]:
                            analysis_text = analysis_data["analysis"]["analysis"]
                        elif isinstance(analysis_data["analysis"], str):
                            analysis_text = analysis_data["analysis"]
            
            if not analysis_text:
                logger.warning("No analysis text found in video result")
                return []
            
            # Use regex to find product mentions
            product_pattern = r'Products?[/\s]things?.+?buy.+?shown.+?video[:\s]*\n?(.+?)(?:\n\n|\nSuggestions|\nKey insights|$)'
            matches = re.search(product_pattern, analysis_text, re.IGNORECASE | re.DOTALL)
            
            if matches:
                product_text = matches.group(1)
                
                # Extract individual products with timestamps
                products = []
                for line in product_text.split('\n'):
                    line = line.strip()
                    if line.startswith('-') or line.startswith('•') or line.startswith('*'):
                        # Clean up the product line
                        product_line = line.lstrip('-•* ').strip()
                        
                        # Extract timestamp if present
                        timestamp_match = re.search(r'\((\d+s-\d+s)\)', product_line)
                        timestamp = timestamp_match.group(1) if timestamp_match else None
                        
                        # Extract product name (remove timestamps in parentheses for search)
                        product_name = re.sub(r'\s*\(\d+s-\d+s\)', '', product_line).strip()
                        
                        if product_name:
                            products.append({
                                "name": product_name,
                                "timestamp": timestamp
                            })
                
                logger.info(f"Extracted {len(products)} products with timestamps: {[f'{p["name"]} ({p["timestamp"]})' for p in products]}")
                return products
            else:
                logger.warning("No product section found in analysis text")
                return []
                
        except Exception as e:
            logger.error(f"Error extracting product keywords: {e}")
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
    
    def list_tasks(self) -> Dict[str, VideoMonetizationResult]:
        """List all tasks (for debugging)"""
        return self.tasks


# Global analyzer instance
video_monetization_analyzer = VideoMonetizationAnalyzer()
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
        """Start video monetization analysis workflow and return task ID"""
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
        
        # Start processing in background (in real app, use background tasks)
        try:
            await self._process_video_analysis(task_id, file_path, youtube_channel_url, amazon_affiliate_code)
        except Exception as e:
            logger.error(f"Error starting analysis for task {task_id}: {e}")
            self.tasks[task_id].status = "failed"
            self.tasks[task_id].error_message = str(e)
        
        return task_id
    
    async def _process_video_analysis(self, task_id: str, file_path: str, youtube_channel_url: Optional[str] = None, amazon_affiliate_code: Optional[str] = None):
        """Process the complete video monetization analysis workflow"""
        try:
            # Update status to processing
            self.tasks[task_id].status = "processing"
            self.tasks[task_id].timestamps["video_analysis_started"] = datetime.now()
            
            # Step 1: Analyze video using video analyzer
            logger.info(f"Task {task_id}: Starting video analysis")
            from services.video_analyzer.models import VideoAnalysisRequest
            
            video_request = VideoAnalysisRequest(features=["gist", "summary", "analysis"])
            video_result = self.video_analyzer.analyze_video(file_path, video_request)
            
            # Store video analysis result
            self.tasks[task_id].video_analysis = video_result.model_dump() if hasattr(video_result, 'model_dump') else video_result.__dict__
            self.tasks[task_id].timestamps["video_analysis_completed"] = datetime.now()
            
            # Step 2: Extract product keywords from analysis
            logger.info(f"Task {task_id}: Extracting product keywords")
            product_keywords = await self._extract_product_keywords(video_result)
            self.tasks[task_id].product_keywords = product_keywords
            self.tasks[task_id].timestamps["keywords_extracted"] = datetime.now()
            
            # Step 3: Generate affiliate links for products
            if product_keywords:
                logger.info(f"Task {task_id}: Generating affiliate links for {len(product_keywords)} keywords")
                await self._generate_product_links(task_id, product_keywords, amazon_affiliate_code)
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
    
    async def _extract_product_keywords(self, video_result) -> List[str]:
        """Extract product keywords from video analysis"""
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
                
                # Extract individual products using bullet points or dashes
                products = []
                for line in product_text.split('\n'):
                    line = line.strip()
                    if line.startswith('-') or line.startswith('•') or line.startswith('*'):
                        # Clean up the product name
                        product = line.lstrip('-•* ').strip()
                        # Extract product name (remove timestamps in parentheses)
                        product = re.sub(r'\s*\(\d+s-\d+s\)', '', product)
                        if product:
                            products.append(product)
                
                logger.info(f"Extracted {len(products)} product keywords: {products}")
                return products
            else:
                logger.warning("No product section found in analysis text")
                return []
                
        except Exception as e:
            logger.error(f"Error extracting product keywords: {e}")
            return []
    
    async def _generate_product_links(self, task_id: str, keywords: List[str], amazon_affiliate_code: Optional[str] = None):
        """Generate affiliate links for extracted product keywords"""
        try:
            # Default affiliate codes (in real app, these would come from user settings)
            affiliate_codes = AffiliateCodes(
                amazon="hackai20-20",  # Example Amazon Associates tag
                ebay="",
                walmart="",
                target="",
                shareasale="",
                cj_affiliate="",
                clickbank=""
            )
            
            # Create link generation request
            link_request = LinkGenerationRequest(
                keywords=keywords,
                affiliate_codes=affiliate_codes,
                max_results=10
            )
            
            # Generate affiliate links
            link_result = await self.link_generator.generate_affiliate_links(link_request)
            
            # Convert to our ProductLink model
            products = []
            for link in link_result.product_links:
                product = ProductLink(
                    product_name=link.product_name,
                    product_url=link.product_url,
                    affiliate_url=link.affiliate_url,
                    platform=link.platform,
                    price=link.price,
                    rating=link.rating,
                    image_url=link.image_url,
                    availability=link.availability
                )
                products.append(product)
            
            self.tasks[task_id].products = products
            logger.info(f"Generated {len(products)} product links for task {task_id}")
            
        except Exception as e:
            logger.error(f"Error generating product links for task {task_id}: {e}")
    
    async def _get_channel_context(self, task_id: str, youtube_channel_url: str):
        """Get YouTube channel context for additional monetization insights"""
        try:
            # Use YouTube scraper to get channel health data
            channel_data = await self.youtube_scraper.get_channel_health(youtube_channel_url)
            self.tasks[task_id].channel_context = channel_data
            logger.info(f"Fetched channel context for task {task_id}")
            
        except Exception as e:
            logger.error(f"Error fetching channel context for task {task_id}: {e}")
    
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
            
            # Create GROQ prompt
            prompt = f"""
Based on the following video content analysis, generate specific monetization strategies for this content creator:

Video Summary:
{video_summary}

Channel Context:
{channel_info}

Products mentioned in video:
{', '.join(task.product_keywords) if task.product_keywords else 'None'}

Generate monetization strategies that are:
1. Specific and actionable
2. Based on the actual content shown
3. Realistic for the creator's current situation

Return ONLY a JSON array with this exact format:
[
  {{
    "strategy_type": "course",
    "title": "How to Get a Job at Meta",
    "description": "Create a comprehensive course teaching viewers how to prepare for and land a job at Meta, based on your insider experience",
    "implementation_steps": ["Step 1", "Step 2", "Step 3"],
    "estimated_effort": "high",
    "estimated_timeline": "2-3 months",
    "potential_revenue": "high"
  }}
]

Strategy types can be: course, sponsorship, affiliate, merchandise, coaching, consulting, patreon, youtube_memberships, live_events
Effort levels: low, medium, high
Timeline examples: "1-2 weeks", "1 month", "2-3 months", "3-6 months"
Revenue potential: low, medium, high
            """
            
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
                                "content": "You are an expert in content creator monetization strategies. Return only valid JSON as requested."
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
        """Get current status of a task"""
        return self.tasks.get(task_id)
    
    def list_tasks(self) -> Dict[str, VideoMonetizationResult]:
        """List all tasks (for debugging)"""
        return self.tasks


# Global analyzer instance
video_monetization_analyzer = VideoMonetizationAnalyzer()
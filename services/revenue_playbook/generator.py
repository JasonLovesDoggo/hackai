import logging
from typing import Dict, Any, Optional
from services.youtube_scraper.scraper import YouTubeScraper
from services.affiliate_discovery.groq_client import GroqClient
from .models import RevenuePlaybook, PlaybookSection
import json

logger = logging.getLogger("uvicorn.error")


class RevenuePlaybookGenerator:
    def __init__(self):
        self.youtube_scraper = YouTubeScraper()
        self.groq_client = GroqClient()

    async def generate_playbook(self, channel_url: str) -> RevenuePlaybook:
        """Generate a comprehensive revenue playbook for a YouTube channel"""
        try:
            logger.info(f"Generating revenue playbook for channel: {channel_url}")
            
            # Get channel health data
            channel_data = await self.youtube_scraper.get_channel_health(channel_url)
            
            if not channel_data or "channel" not in channel_data:
                raise ValueError("Could not fetch channel data")
            
            channel_info = channel_data["channel"]
            content_analysis = channel_data.get("content_analysis", {})
            health_analysis = channel_data.get("health_analysis", {})
            
            logger.info(f"Channel: {channel_info.get('name')} ({channel_info.get('subscribers')} subscribers)")
            
            # Generate playbook using GROQ
            playbook_data = await self._generate_playbook_with_groq(
                channel_info, content_analysis, health_analysis
            )
            
            return RevenuePlaybook(
                title=playbook_data["title"],
                sections=playbook_data["sections"],
                channel_id=channel_info.get("id"),
                channel_name=channel_info.get("name"),
                generated_for_subscriber_count=channel_info.get("subscribers")
            )
            
        except Exception as e:
            logger.error(f"Error generating revenue playbook: {e}")
            raise

    async def _generate_playbook_with_groq(
        self, 
        channel_info: Dict[str, Any], 
        content_analysis: Dict[str, Any], 
        health_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use GROQ to generate a personalized revenue playbook"""
        
        subscribers = channel_info.get("subscribers", 0)
        content_type = content_analysis.get("content_type", "general")
        upload_style = content_analysis.get("upload_style", "irregular")
        health_score = health_analysis.get("health_score", 50)
        monetization_ready = health_analysis.get("monetization_ready", False)
        
        # Determine subscriber tier for tailored advice
        if subscribers < 1000:
            tier = "starting"
        elif subscribers < 10000:
            tier = "growing"
        elif subscribers < 100000:
            tier = "established"
        else:
            tier = "large"
        
        prompt = f"""
Create a personalized revenue playbook for a YouTube channel with the following details:

Channel Stats:
- Subscribers: {subscribers:,}
- Content Type: {content_type}
- Upload Style: {upload_style}
- Health Score: {health_score}/100
- Monetization Ready: {monetization_ready}
- Tier: {tier}

Create a comprehensive 30-day revenue playbook with 4-5 sections focusing on immediate, short-term, and long-term monetization strategies.

Return ONLY a JSON object in this exact format:
{{
  "title": "Your 30-Day Revenue Playbook",
  "sections": [
    {{
      "id": "low-hanging",
      "heading": "Low-Hanging Fruit (Do This Week)",
      "body_md": "Focus on **immediate revenue opportunities** that require minimal effort but can generate quick returns. Based on your {subscribers:,} subscribers and {content_type} content, these are your highest-impact actions:\\n\\n- **Affiliate marketing** is perfect for your audience size\\n- **Direct monetization** through existing content\\n- **Audience engagement** improvements for better reach",
      "actions": [
        "Add affiliate links to your top 5 performing videos",
        "Pin call-to-action comments on recent videos",
        "Create a basic landing page for affiliate products"
      ]
    }},
    {{
      "id": "short-term",
      "heading": "30-Day Growth Accelerators",
      "body_md": "Strategic moves to **increase revenue potential** over the next month. These tactics will help you build momentum:\\n\\n- **Content optimization** for better discovery\\n- **Audience building** strategies\\n- **Revenue stream diversification**",
      "actions": [
        "Launch a weekly series around your {content_type} niche",
        "Create product review videos with affiliate partnerships",
        "Set up email capture for your audience"
      ]
    }},
    {{
      "id": "medium-term",
      "heading": "Revenue Multiplication (Month 2-3)",
      "body_md": "**Scale your income streams** with these proven strategies. Focus on systems that can generate recurring revenue:\\n\\n- **Multiple revenue channels** working together\\n- **Community building** for long-term value\\n- **Premium offerings** for dedicated fans",
      "actions": [
        "Launch a Patreon or channel membership program",
        "Create digital products related to your content",
        "Establish brand partnership relationships"
      ]
    }},
    {{
      "id": "advanced",
      "heading": "Long-Term Wealth Building",
      "body_md": "**Advanced monetization strategies** for sustained growth. These require more effort but offer the highest returns:\\n\\n- **Business development** opportunities\\n- **Passive income** generation\\n- **Brand building** for premium partnerships",
      "actions": [
        "Develop signature courses or coaching programs",
        "Create a personal brand beyond YouTube",
        "Build email list for direct marketing"
      ]
    }}
  ]
}}

CRITICAL REQUIREMENTS:
- Tailor ALL advice specifically to {tier} channels with {subscribers:,} subscribers
- Include specific {content_type} content strategies
- Make actions concrete and measurable
- Use markdown formatting in body_md (bold, lists, etc.)
- Focus on revenue generation, not just growth
- Return ONLY the JSON object, no other text
"""

        try:
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
                                "content": "You are a YouTube monetization expert. Create detailed, actionable revenue playbooks. Return only valid JSON."
                            },
                            {
                                "role": "user", 
                                "content": prompt
                            }
                        ],
                        "temperature": 0.3,
                        "max_tokens": 2000
                    }
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
                        playbook_data = json.loads(content)
                        
                        # Convert to our models
                        sections = []
                        for section_data in playbook_data["sections"]:
                            section = PlaybookSection(
                                id=section_data["id"],
                                heading=section_data["heading"],
                                body_md=section_data["body_md"],
                                actions=section_data["actions"]
                            )
                            sections.append(section)
                        
                        return {
                            "title": playbook_data["title"],
                            "sections": sections
                        }
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse GROQ playbook response: {e}")
                        logger.debug(f"Raw GROQ content: {content}")
                        raise ValueError("Failed to generate valid playbook")
                else:
                    logger.error(f"GROQ API error: {response.status_code}")
                    raise ValueError("Failed to generate playbook")
                    
        except Exception as e:
            logger.error(f"Error calling GROQ for playbook generation: {e}")
            raise
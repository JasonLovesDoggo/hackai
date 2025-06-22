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
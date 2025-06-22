"""
GROQ prompts for video monetization analysis
"""

MONETIZATION_STRATEGY_PROMPT = """
Based on the following video content analysis, generate 3 HIGHLY SPECIFIC monetization strategies for this content creator:

Video Summary:
{video_summary}

Channel Context:
{channel_info}

Products mentioned in video:
{product_keywords}

Requirements:
- Generate EXACTLY 3 strategies
- Make each strategy HIGHLY specific to the actual content shown
- Include detailed WHY this strategy works for this creator
- Provide 5-7 specific implementation steps
- Reference actual content from the video

Return ONLY a JSON array with this exact format:
[
  {{
    "strategy_type": "course",
    "title": "Complete Tech Workspace Setup Guide",
    "description": "Create a premium course teaching the exact setup shown in your video - from the Logitech MX Master 3s configuration to optimal desk organization. This works because you demonstrated real expertise with specific products and your audience clearly values tech recommendations.",
    "why_this_works": "Your video shows genuine product knowledge and your 838k subscribers trust your tech opinions. The specific products you use (Logitech mouse, Framework laptop) prove you know quality gear.",
    "implementation_steps": [
      "Record 10 detailed modules covering each piece of equipment shown",
      "Include downloadable setup checklists for each product", 
      "Create bonus content on productivity workflows",
      "Add Q&A sessions for course members",
      "Partner with featured brands for exclusive discounts",
      "Launch at $197 with early bird pricing at $147",
      "Promote to your 838k programming audience"
    ],
    "estimated_effort": "high",
    "estimated_timeline": "6-8 weeks",
    "potential_revenue": "high"
  }}
]

Strategy types: course, sponsorship, affiliate, merchandise, coaching, consulting
Effort: low, medium, high  
Timeline: "2-4 weeks", "1-2 months", "6-8 weeks", "3-4 months"
Revenue: medium, high, very high
"""

MONETIZATION_SYSTEM_MESSAGE = "You are an expert in content creator monetization strategies. Return only valid JSON as requested."
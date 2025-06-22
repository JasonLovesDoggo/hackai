"""
GROQ prompts for video monetization analysis
"""

MONETIZATION_STRATEGY_PROMPT = """
Based on the following video content analysis, generate specific monetization strategies for this content creator:

Video Summary:
{video_summary}

Channel Context:
{channel_info}

Products mentioned in video:
{product_keywords}

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

MONETIZATION_SYSTEM_MESSAGE = "You are an expert in content creator monetization strategies. Return only valid JSON as requested."
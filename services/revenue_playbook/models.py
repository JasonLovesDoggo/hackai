from pydantic import BaseModel
from typing import List, Optional


class PlaybookAction(BaseModel):
    """Individual action item in a playbook section"""

    action: str
    description: Optional[str] = None
    priority: Optional[str] = "medium"  # low, medium, high


class PlaybookSection(BaseModel):
    """A section of the revenue playbook"""

    id: str
    heading: str
    body_md: str
    actions: List[str]


class RevenuePlaybook(BaseModel):
    """Complete revenue playbook for a YouTube channel"""

    title: str
    sections: List[PlaybookSection]

    # Metadata
    channel_id: Optional[str] = None
    channel_name: Optional[str] = None
    generated_for_subscriber_count: Optional[int] = None

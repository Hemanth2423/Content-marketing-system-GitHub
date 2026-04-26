from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional
from datetime import datetime
import uuid


class ContentType(str, Enum):
    tutorial = "tutorial"
    announcement = "announcement"
    thought_leadership = "thought_leadership"
    case_study = "case_study"


class BriefStatus(str, Enum):
    draft = "DRAFT"
    confirmed = "CONFIRMED"


class BriefEnrichment(BaseModel):
    suggested_keywords: list[str] = []
    audience_framing: str = ""
    content_angle: str = ""
    similar_past_content_ids: list[str] = []


class BriefCreate(BaseModel):
    title: str = Field(..., min_length=10, max_length=200)
    content_type: ContentType
    target_audience: str = Field(..., min_length=5)
    goal: str = Field(..., min_length=10)
    requested_publish_date: datetime
    keywords: list[str] = []


class Brief(BaseModel):
    brief_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    requester_id: str = "requester"
    title: str
    content_type: ContentType
    target_audience: str
    goal: str
    requested_publish_date: datetime
    keywords: list[str] = []
    enrichment: Optional[BriefEnrichment] = None
    confirmed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: BriefStatus = BriefStatus.draft

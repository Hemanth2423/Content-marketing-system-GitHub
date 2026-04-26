from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional
from datetime import datetime


class EvaluationResult(str, Enum):
    pass_ = "PASS"
    fail = "FAIL"
    inconclusive = "EVALUATION_INCONCLUSIVE"


class EvaluationIssue(BaseModel):
    field: str
    problem: str
    location: str
    expected: str


class Evaluation(BaseModel):
    result: EvaluationResult
    issues: list[EvaluationIssue] = []
    confidence: float = 1.0


class ResearchSource(BaseModel):
    file: str
    chunk: str
    relevance_score: float


class ResearchBrief(BaseModel):
    brief_id: str
    sources: list[ResearchSource] = []
    key_points: list[str] = []
    suggested_angles: list[str] = []
    gaps: list[str] = []
    low_context: bool = False
    retrieved_chunk_count: int = 0
    evaluation: Optional[Evaluation] = None


class LinkedInFormat(BaseModel):
    post: str
    character_count: int


class TwitterFormat(BaseModel):
    thread: list[str]
    total_characters: int


class EmailFormat(BaseModel):
    subject: str
    body: str


class ChannelFormats(BaseModel):
    linkedin: Optional[LinkedInFormat] = None
    twitter: Optional[TwitterFormat] = None
    email: Optional[EmailFormat] = None
    constraint_failures: list[str] = []


class DraftMetadata(BaseModel):
    tone: str = ""
    target_audience: str = ""
    keywords_used: list[str] = []


class Draft(BaseModel):
    brief_id: str
    revision: int = 0
    content_type: str
    primary_draft: str
    word_count: int = 0
    metadata: DraftMetadata = Field(default_factory=DraftMetadata)
    formats: Optional[ChannelFormats] = None
    evaluation: Optional[Evaluation] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

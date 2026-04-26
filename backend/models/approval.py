from pydantic import BaseModel
from enum import Enum
from typing import Optional
from datetime import datetime


class ApprovalStage(str, Enum):
    strategist = "strategist"
    reviewer = "reviewer"
    publisher = "publisher"


class ApprovalDecision(str, Enum):
    approved = "APPROVED"
    rejected = "REJECTED"
    skipped = "SKIPPED"


class ApprovalEntry(BaseModel):
    stage: ApprovalStage
    actor_id: str
    decision: ApprovalDecision
    feedback: Optional[str] = None
    skip_reason: Optional[str] = None
    timestamp: datetime = None

    def __init__(self, **data):
        if "timestamp" not in data or data["timestamp"] is None:
            data["timestamp"] = datetime.utcnow()
        super().__init__(**data)


class ApprovalLog(BaseModel):
    brief_id: str
    stages: list[ApprovalEntry] = []

    def get_stage(self, stage: ApprovalStage) -> Optional[ApprovalEntry]:
        for entry in self.stages:
            if entry.stage == stage:
                return entry
        return None

    def is_stage_complete(self, stage: ApprovalStage) -> bool:
        entry = self.get_stage(stage)
        return entry is not None and entry.decision in (
            ApprovalDecision.approved, ApprovalDecision.skipped
        )

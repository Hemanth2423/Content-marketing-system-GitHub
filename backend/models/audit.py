from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime
import uuid


class AuditEntry(BaseModel):
    entry_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    content_id: str
    actor: str = "system"
    actor_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    payload: dict[str, Any] = {}
    prev_entry_hash: str = ""
    entry_hash: str = ""

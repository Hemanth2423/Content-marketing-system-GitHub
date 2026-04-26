from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional
from datetime import datetime
import uuid


class AlertType(str, Enum):
    sla_warning = "SLA_WARNING"
    sla_urgent = "SLA_URGENT"
    sla_breach = "SLA_BREACH"
    publish_window = "PUBLISH_WINDOW"
    compliance_failure = "COMPLIANCE_FAILURE"
    agent_failure = "AGENT_FAILURE"
    publish_failure = "PUBLISH_FAILURE"


class AlertSeverity(str, Enum):
    yellow = "YELLOW"
    red = "RED"


class Alert(BaseModel):
    alert_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content_id: str
    type: AlertType
    severity: AlertSeverity
    message: str
    triggered_at: datetime = Field(default_factory=datetime.utcnow)
    response_deadline: Optional[datetime] = None
    assigned_to: str = "strategist"
    dismissed_at: Optional[datetime] = None
    escalation_level: int = 0

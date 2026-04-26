import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Any

from config import settings
from audit_log.audit_logger import log_event
from orchestrator.state_machine import PipelineState, can_transition
from models.brief import Brief
from models.draft import Draft, ResearchBrief
from models.approval import ApprovalLog, ApprovalEntry, ApprovalStage, ApprovalDecision

_orchestrator: Optional["Orchestrator"] = None


class PipelineStateRecord:
    def __init__(self, content_id: str, data: dict):
        self.content_id = content_id
        self._data = data

    @property
    def state(self) -> PipelineState:
        return PipelineState(self._data["state"])

    @property
    def revision_count(self) -> int:
        return self._data.get("revision_count", 0)

    @property
    def brief_id(self) -> str:
        return self._data.get("brief_id", self.content_id)

    @property
    def scheduled_datetime(self) -> Optional[datetime]:
        val = self._data.get("scheduled_datetime")
        if val:
            return datetime.fromisoformat(val)
        return None

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value: Any):
        self._data[key] = value

    def to_dict(self) -> dict:
        return dict(self._data)


class Orchestrator:
    def __init__(self):
        self._state_dir = settings.storage_dir / "pipeline_states"
        self._state_dir.mkdir(parents=True, exist_ok=True)

    # ── State file helpers ──────────────────────────────────────────────

    def _state_path(self, content_id: str) -> Path:
        return self._state_dir / f"{content_id}.json"

    def load_state(self, content_id: str) -> Optional[PipelineStateRecord]:
        path = self._state_path(content_id)
        if not path.exists():
            return None
        data = json.loads(path.read_text())
        return PipelineStateRecord(content_id, data)

    def _save_state(self, record: PipelineStateRecord):
        path = self._state_path(record.content_id)
        path.write_text(json.dumps(record.to_dict(), default=str))

    # ── State transition ─────────────────────────────────────────────────

    def transition(
        self,
        content_id: str,
        target: PipelineState,
        payload: dict = None,
        actor: str = "system",
        actor_id: Optional[str] = None,
    ) -> PipelineStateRecord:
        """Log first, then transition. Raises ValueError on invalid transition."""
        record = self.load_state(content_id)
        if record is None:
            raise ValueError(f"No pipeline state found for {content_id}")

        current = record.state
        if not can_transition(current, target):
            raise ValueError(
                f"Invalid transition: {current.value} → {target.value}"
            )

        # Log before writing new state
        log_event(
            event_type=f"STATE_TRANSITION_{target.value}",
            content_id=content_id,
            payload={"from": current.value, "to": target.value, **(payload or {})},
            actor=actor,
            actor_id=actor_id,
        )

        record.set("state", target.value)
        record.set("updated_at", datetime.utcnow().isoformat())
        if payload:
            for k, v in payload.items():
                record.set(k, v)
        self._save_state(record)
        return record

    # ── Content piece creation ───────────────────────────────────────────

    def create_pipeline(self, brief: Brief) -> PipelineStateRecord:
        content_id = brief.brief_id
        data = {
            "content_id": content_id,
            "brief_id": brief.brief_id,
            "state": PipelineState.BRIEF_DRAFT.value,
            "revision_count": 0,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "scheduled_datetime": None,
            "sla_strategist_started_at": None,
            "sla_reviewer_started_at": None,
            "sla_publisher_started_at": None,
        }
        record = PipelineStateRecord(content_id, data)
        self._save_state(record)
        log_event("PIPELINE_CREATED", content_id, {"brief_id": brief.brief_id})
        return record

    # ── Brief helpers ────────────────────────────────────────────────────

    def save_brief(self, brief: Brief):
        path = settings.storage_dir / "briefs" / f"{brief.brief_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(brief.model_dump_json(indent=2))

    def load_brief(self, brief_id: str) -> Optional[Brief]:
        path = settings.storage_dir / "briefs" / f"{brief_id}.json"
        if not path.exists():
            return None
        return Brief.model_validate_json(path.read_text())

    # ── Research brief helpers ───────────────────────────────────────────

    def save_research_brief(self, research: ResearchBrief):
        path = settings.storage_dir / "drafts" / f"{research.brief_id}_research.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(research.model_dump_json(indent=2))

    def load_research_brief(self, brief_id: str) -> Optional[ResearchBrief]:
        path = settings.storage_dir / "drafts" / f"{brief_id}_research.json"
        if not path.exists():
            return None
        return ResearchBrief.model_validate_json(path.read_text())

    # ── Draft helpers ────────────────────────────────────────────────────

    def save_draft(self, draft: Draft):
        path = settings.storage_dir / "drafts" / f"{draft.brief_id}_draft_r{draft.revision}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(draft.model_dump_json(indent=2))

    def load_latest_draft(self, brief_id: str) -> Optional[Draft]:
        draft_dir = settings.storage_dir / "drafts"
        drafts = sorted(draft_dir.glob(f"{brief_id}_draft_r*.json"))
        if not drafts:
            return None
        return Draft.model_validate_json(drafts[-1].read_text())

    # ── Approval helpers ─────────────────────────────────────────────────

    def _approval_path(self, brief_id: str) -> Path:
        path = settings.storage_dir / "briefs" / f"{brief_id}_approvals.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def load_approval_log(self, brief_id: str) -> ApprovalLog:
        path = self._approval_path(brief_id)
        if not path.exists():
            return ApprovalLog(brief_id=brief_id)
        return ApprovalLog.model_validate_json(path.read_text())

    def record_approval(
        self,
        brief_id: str,
        stage: ApprovalStage,
        decision: ApprovalDecision,
        actor_id: str,
        feedback: Optional[str] = None,
        skip_reason: Optional[str] = None,
    ) -> ApprovalLog:
        approval_log = self.load_approval_log(brief_id)
        entry = ApprovalEntry(
            stage=stage,
            actor_id=actor_id,
            decision=decision,
            feedback=feedback,
            skip_reason=skip_reason,
        )
        approval_log.stages.append(entry)
        path = self._approval_path(brief_id)
        path.write_text(approval_log.model_dump_json(indent=2))

        log_event(
            event_type=f"{stage.value.upper()}_{decision.value}",
            content_id=brief_id,
            payload={
                "stage": stage.value,
                "decision": decision.value,
                "feedback": feedback,
                "skip_reason": skip_reason,
            },
            actor=stage.value,
            actor_id=actor_id,
        )
        return approval_log

    # ── Prerequisite verification (publish gate) ─────────────────────────

    def verify_publish_prerequisites(self, brief_id: str) -> tuple[bool, list[str]]:
        """Check all 5 conditions must be true before publish job can lock."""
        from audit_log.audit_logger import get_audit_log
        entries = get_audit_log(brief_id)
        event_types = {e["event_type"] for e in entries}

        missing = []
        if "STRATEGIST_APPROVED" not in event_types:
            missing.append("STRATEGIST_APPROVED not in audit log")
        reviewer_ok = (
            "REVIEWER_APPROVED" in event_types
            or "STATE_TRANSITION_REVIEWER_SKIPPED" in event_types
        )
        if not reviewer_ok:
            missing.append("REVIEWER_APPROVED or REVIEWER_SKIPPED not in audit log")
        if "STATE_TRANSITION_COMPLIANCE_PASSED" not in event_types:
            missing.append("COMPLIANCE_PASSED not in audit log")
        if "PUBLISHER_CONFIRMED" not in event_types:
            missing.append("PUBLISHER_CONFIRMED not in audit log")

        record = self.load_state(brief_id)
        if record and record.scheduled_datetime:
            if record.scheduled_datetime <= datetime.utcnow():
                missing.append("scheduled_datetime is not in the future")
        else:
            missing.append("No scheduled_datetime set")

        return len(missing) == 0, missing

    def list_all_pipelines(self) -> list[dict]:
        result = []
        for path in self._state_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text())
                result.append(data)
            except Exception:
                continue
        return sorted(result, key=lambda x: x.get("created_at", ""), reverse=True)


def get_orchestrator() -> Orchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator

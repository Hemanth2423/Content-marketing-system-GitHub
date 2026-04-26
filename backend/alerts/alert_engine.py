import json
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from config import settings
from models.alert import Alert, AlertType, AlertSeverity
from audit_log.audit_logger import log_event

_engine: Optional["AlertEngine"] = None
_lock = threading.Lock()


class AlertEngine:
    def __init__(self):
        self._alerts_path = settings.storage_dir / "alerts.json"
        self._alerts_path.parent.mkdir(parents=True, exist_ok=True)

    # ── Alert store ──────────────────────────────────────────────────────

    def _load_alerts(self) -> list[dict]:
        if not self._alerts_path.exists():
            return []
        try:
            return json.loads(self._alerts_path.read_text())
        except Exception:
            return []

    def _save_alerts(self, alerts: list[dict]):
        self._alerts_path.write_text(json.dumps(alerts, default=str, indent=2))

    def _add_alert(self, alert: Alert):
        with _lock:
            alerts = self._load_alerts()
            alerts.append(alert.model_dump(mode="json"))
            self._save_alerts(alerts)
        log_event(
            event_type=f"ALERT_FIRED_{alert.type.value}",
            content_id=alert.content_id,
            payload=alert.model_dump(mode="json"),
        )

    def get_active_alerts(self, content_id: Optional[str] = None) -> list[dict]:
        alerts = self._load_alerts()
        active = [a for a in alerts if not a.get("dismissed_at")]
        if content_id:
            active = [a for a in active if a["content_id"] == content_id]
        return active

    def dismiss_alert(self, alert_id: str) -> bool:
        with _lock:
            alerts = self._load_alerts()
            for a in alerts:
                if a["alert_id"] == alert_id and not a.get("dismissed_at"):
                    a["dismissed_at"] = datetime.utcnow().isoformat()
                    self._save_alerts(alerts)
                    return True
        return False

    # ── SLA monitoring ───────────────────────────────────────────────────

    def check_sla(self):
        """Called on a background schedule. Check all in-flight pipelines."""
        from orchestrator import get_orchestrator
        from orchestrator.state_machine import PipelineState

        orch = get_orchestrator()
        pipelines = orch.list_all_pipelines()

        sla_map = {
            PipelineState.PENDING_STRATEGIST_REVIEW.value: settings.sla_strategist_seconds,
            PipelineState.PENDING_REVIEWER_REVIEW.value: settings.sla_reviewer_seconds,
            PipelineState.PENDING_PUBLISHER_REVIEW.value: settings.sla_publisher_seconds,
        }

        for pipeline in pipelines:
            state = pipeline.get("state")
            content_id = pipeline.get("content_id")
            if state not in sla_map:
                continue

            sla_seconds = sla_map[state]
            updated_at_str = pipeline.get("updated_at")
            if not updated_at_str:
                continue

            updated_at = datetime.fromisoformat(updated_at_str)
            elapsed = (datetime.utcnow() - updated_at).total_seconds()
            pct = elapsed / sla_seconds

            existing = self.get_active_alerts(content_id)
            existing_types = {a["type"] for a in existing}

            if pct >= 1.0 and AlertType.sla_breach.value not in existing_types:
                self._fire_sla(content_id, AlertType.sla_breach, AlertSeverity.red, sla_seconds, state)
                # Mark pipeline as stalled
                try:
                    orch.transition(content_id, PipelineState.STALLED)
                except Exception:
                    pass
            elif pct >= settings.sla_urgent_pct and AlertType.sla_urgent.value not in existing_types:
                self._fire_sla(content_id, AlertType.sla_urgent, AlertSeverity.red, sla_seconds, state)
            elif pct >= settings.sla_warning_pct and AlertType.sla_warning.value not in existing_types:
                self._fire_sla(content_id, AlertType.sla_warning, AlertSeverity.yellow, sla_seconds, state)

            # Publish window check
            scheduled = pipeline.get("scheduled_datetime")
            if scheduled:
                publish_at = datetime.fromisoformat(scheduled)
                time_to_publish = (publish_at - datetime.utcnow()).total_seconds()
                if (
                    0 < time_to_publish < settings.publish_window_warning_seconds
                    and state not in ("PUBLISHED", "CANCELLED", "SCHEDULED", "PUBLISH_JOB_LOCKED")
                    and AlertType.publish_window.value not in existing_types
                ):
                    self.fire_publish_window(content_id, publish_at)

    def _fire_sla(
        self,
        content_id: str,
        alert_type: AlertType,
        severity: AlertSeverity,
        sla_seconds: int,
        stage: str,
    ):
        messages = {
            AlertType.sla_warning: f"Stage {stage} has been waiting for 50% of its SLA window ({sla_seconds}s)",
            AlertType.sla_urgent: f"Stage {stage} is at 80% of its SLA window — action required",
            AlertType.sla_breach: f"Stage {stage} SLA breached — pipeline marked STALLED",
        }
        alert = Alert(
            content_id=content_id,
            type=alert_type,
            severity=severity,
            message=messages.get(alert_type, "SLA alert"),
            response_deadline=datetime.utcnow() + timedelta(seconds=sla_seconds // 5),
            assigned_to="strategist",
        )
        self._add_alert(alert)

    def fire_publish_window(self, content_id: str, publish_at: datetime):
        alert = Alert(
            content_id=content_id,
            type=AlertType.publish_window,
            severity=AlertSeverity.red,
            message=f"Scheduled publish at {publish_at.isoformat()} is approaching but pipeline is not complete",
            response_deadline=publish_at,
            assigned_to="all",
        )
        self._add_alert(alert)

    def fire_agent_failure(self, content_id: str, failure_type: str, detail: str):
        alert = Alert(
            content_id=content_id,
            type=AlertType.agent_failure,
            severity=AlertSeverity.yellow,
            message=f"{failure_type}: {detail}",
            assigned_to="strategist",
        )
        self._add_alert(alert)

    def fire_compliance_failure(self, content_id: str, violation_count: int):
        alert = Alert(
            content_id=content_id,
            type=AlertType.compliance_failure,
            severity=AlertSeverity.red,
            message=f"Compliance check found {violation_count} violation(s) — content blocked from Publisher",
            assigned_to="strategist",
        )
        self._add_alert(alert)

    def fire_publish_failure(self, content_id: str, results: dict):
        failed = [ch for ch, r in results.items() if r.get("status") != "SUCCESS"]
        alert = Alert(
            content_id=content_id,
            type=AlertType.publish_failure,
            severity=AlertSeverity.red,
            message=f"Publish failed for channels: {', '.join(failed)}",
            assigned_to="publisher",
        )
        self._add_alert(alert)


def get_alert_engine() -> AlertEngine:
    global _engine
    if _engine is None:
        _engine = AlertEngine()
    return _engine

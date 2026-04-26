import json
from datetime import datetime
from typing import Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from config import settings
from audit_log.audit_logger import log_event

_scheduler_instance: Optional["PublishScheduler"] = None


class PublishScheduler:
    def __init__(self):
        self._scheduler = BackgroundScheduler(timezone="UTC")
        self._scheduler.start()

    def schedule_publish(self, brief_id: str, publish_at: datetime) -> bool:
        """
        Lock and schedule a publish job after verifying all 5 conditions.
        Returns True if scheduled, False if conditions not met.
        """
        from orchestrator import get_orchestrator
        from orchestrator.state_machine import PipelineState

        orch = get_orchestrator()
        ok, missing = orch.verify_publish_prerequisites(brief_id)
        if not ok:
            log_event(
                event_type="PUBLISH_JOB_LOCK_FAILED",
                content_id=brief_id,
                payload={"missing_conditions": missing},
            )
            return False

        log_event(
            event_type="PUBLISH_JOB_LOCKED",
            content_id=brief_id,
            payload={
                "scheduled_datetime": publish_at.isoformat(),
                "conditions_verified": True,
            },
        )
        orch.transition(brief_id, PipelineState.PUBLISH_JOB_LOCKED)
        orch.transition(brief_id, PipelineState.SCHEDULED)

        self._scheduler.add_job(
            func=self._execute_publish,
            trigger=DateTrigger(run_date=publish_at),
            id=f"publish_{brief_id}",
            args=[brief_id],
            replace_existing=True,
            misfire_grace_time=300,
        )
        return True

    def cancel_publish(self, brief_id: str):
        try:
            self._scheduler.remove_job(f"publish_{brief_id}")
            log_event(
                event_type="PUBLISH_JOB_CANCELLED",
                content_id=brief_id,
                payload={"reason": "manually_cancelled"},
            )
        except Exception:
            pass

    def _execute_publish(self, brief_id: str):
        from orchestrator import get_orchestrator
        from orchestrator.state_machine import PipelineState
        from automation.publisher import publish_all_channels

        orch = get_orchestrator()
        brief = orch.load_brief(brief_id)
        draft = orch.load_latest_draft(brief_id)
        if not brief or not draft:
            log_event("PUBLISH_TRIGGER_FAILED", brief_id, {"reason": "brief or draft not found"})
            return

        log_event("PUBLISH_TRIGGER_FIRED", brief_id, {"triggered_at": datetime.utcnow().isoformat()})
        orch.transition(brief_id, PipelineState.PUBLISHING_IN_PROGRESS)

        results = publish_all_channels(brief, draft, draft.formats)
        all_ok = all(r.get("status") == "SUCCESS" for r in results.values())

        target_state = PipelineState.PUBLISHED if all_ok else PipelineState.PUBLISH_FAILED
        orch.transition(brief_id, target_state, payload={"channel_results": results})

        if not all_ok:
            from alerts import AlertEngine
            AlertEngine().fire_publish_failure(brief_id, results)

    def shutdown(self):
        self._scheduler.shutdown(wait=False)


def get_scheduler() -> PublishScheduler:
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = PublishScheduler()
    return _scheduler_instance

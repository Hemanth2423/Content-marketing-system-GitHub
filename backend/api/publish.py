from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from orchestrator import get_orchestrator
from orchestrator.state_machine import PipelineState
from models.approval import ApprovalStage, ApprovalDecision
from audit_log.audit_logger import log_event

router = APIRouter(prefix="/publish", tags=["publish"])


class ConfirmRequest(BaseModel):
    scheduled_datetime: datetime
    actor_id: str = "publisher"


@router.post("/{content_id}/confirm")
async def confirm_publish(content_id: str, body: ConfirmRequest):
    """F-05 Step 5.1: Publisher confirms schedule."""
    orch = get_orchestrator()
    record = orch.load_state(content_id)
    if not record:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    if record.state != PipelineState.PENDING_PUBLISHER_REVIEW:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot confirm from state {record.state.value}. Must be PENDING_PUBLISHER_REVIEW",
        )

    if body.scheduled_datetime <= datetime.utcnow():
        raise HTTPException(status_code=422, detail="scheduled_datetime must be in the future")

    # Record publisher confirmation
    orch.record_approval(
        brief_id=content_id,
        stage=ApprovalStage.publisher,
        decision=ApprovalDecision.approved,
        actor_id=body.actor_id,
    )
    log_event("PUBLISHER_CONFIRMED", content_id, {
        "scheduled_datetime": body.scheduled_datetime.isoformat(),
    }, actor="publisher", actor_id=body.actor_id)

    record.set("scheduled_datetime", body.scheduled_datetime.isoformat())
    orch.transition(content_id, PipelineState.PUBLISHER_CONFIRMED)

    # Lock publish job (5-condition gate)
    from scheduler import get_scheduler
    scheduler = get_scheduler()
    scheduled = scheduler.schedule_publish(content_id, body.scheduled_datetime)

    if not scheduled:
        ok, missing = orch.verify_publish_prerequisites(content_id)
        raise HTTPException(
            status_code=422,
            detail={"error": "Publish job could not be locked", "missing": missing},
        )

    final = orch.load_state(content_id)
    return {
        "content_id": content_id,
        "state": final.state.value,
        "scheduled_datetime": body.scheduled_datetime.isoformat(),
    }


@router.post("/{content_id}/retry")
async def retry_publish(content_id: str):
    """Publisher-initiated retry after PUBLISH_FAILED."""
    orch = get_orchestrator()
    record = orch.load_state(content_id)
    if not record or record.state != PipelineState.PUBLISH_FAILED:
        raise HTTPException(status_code=400, detail="Pipeline is not in PUBLISH_FAILED state")

    brief = orch.load_brief(content_id)
    draft = orch.load_latest_draft(content_id)
    if not brief or not draft:
        raise HTTPException(status_code=404, detail="Brief or draft not found")

    orch.transition(content_id, PipelineState.PUBLISHING_IN_PROGRESS)
    log_event("PUBLISH_RETRY_INITIATED", content_id, {}, actor="publisher")

    from automation.publisher import publish_all_channels
    results = publish_all_channels(brief, draft, draft.formats)
    all_ok = all(r.get("status") == "SUCCESS" for r in results.values())

    target = PipelineState.PUBLISHED if all_ok else PipelineState.PUBLISH_FAILED
    orch.transition(content_id, target, payload={"channel_results": results})

    return {
        "content_id": content_id,
        "state": target.value,
        "channel_results": results,
    }


@router.get("/{content_id}/status")
async def get_publish_status(content_id: str):
    orch = get_orchestrator()
    record = orch.load_state(content_id)
    if not record:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return {
        "content_id": content_id,
        "state": record.state.value,
        "scheduled_datetime": record.get("scheduled_datetime"),
        "channel_results": record.get("channel_results"),
    }

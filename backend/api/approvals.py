from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from orchestrator import get_orchestrator
from orchestrator.state_machine import PipelineState
from models.approval import ApprovalStage, ApprovalDecision
from audit_log.audit_logger import log_event
from automation.legal_trigger import check_legal_triggers

router = APIRouter(prefix="/approvals", tags=["approvals"])


class ApprovalRequest(BaseModel):
    stage: ApprovalStage
    decision: str  # "approve" or "reject"
    actor_id: str = "unknown"
    feedback: Optional[str] = None


@router.post("/{content_id}")
async def submit_approval(content_id: str, body: ApprovalRequest):
    orch = get_orchestrator()
    record = orch.load_state(content_id)
    if not record:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    decision = ApprovalDecision.approved if body.decision == "approve" else ApprovalDecision.rejected

    if decision == ApprovalDecision.rejected and (not body.feedback or len(body.feedback.strip()) < 20):
        raise HTTPException(
            status_code=422,
            detail="Rejection requires feedback of at least 20 characters",
        )

    orch.record_approval(
        brief_id=content_id,
        stage=body.stage,
        decision=decision,
        actor_id=body.actor_id,
        feedback=body.feedback,
    )

    if body.stage == ApprovalStage.strategist:
        if decision == ApprovalDecision.approved:
            log_event("STRATEGIST_APPROVED", content_id, {}, actor="strategist", actor_id=body.actor_id)
            orch.transition(content_id, PipelineState.STRATEGIST_APPROVED)
            # Immediately run legal trigger check
            await _run_legal_check(content_id)
        else:
            orch.transition(content_id, PipelineState.DRAFT_IN_PROGRESS,
                            payload={"strategist_feedback": body.feedback})

    elif body.stage == ApprovalStage.reviewer:
        if decision == ApprovalDecision.approved:
            log_event("REVIEWER_APPROVED", content_id, {}, actor="reviewer", actor_id=body.actor_id)
            orch.transition(content_id, PipelineState.REVIEWER_APPROVED)
            await _run_compliance(content_id)
        else:
            orch.transition(content_id, PipelineState.DRAFT_IN_PROGRESS,
                            payload={"reviewer_feedback": body.feedback})

    elif body.stage == ApprovalStage.publisher:
        if decision == ApprovalDecision.approved:
            raise HTTPException(status_code=400, detail="Use /publish/confirm for publisher confirmation")
        else:
            raise HTTPException(status_code=400, detail="Publisher cannot reject — can only delay or escalate")

    final_record = orch.load_state(content_id)
    return {"content_id": content_id, "state": final_record.state.value}


async def _run_legal_check(content_id: str):
    orch = get_orchestrator()
    orch.transition(content_id, PipelineState.LEGAL_CHECK_IN_PROGRESS)

    draft = orch.load_latest_draft(content_id)
    if not draft:
        orch.transition(content_id, PipelineState.REVIEWER_SKIPPED)
        log_event("REVIEWER_STAGE_SKIPPED", content_id, {"reason": "no draft found"})
        return

    triggered, matches = check_legal_triggers(draft.primary_draft)
    log_event("LEGAL_TRIGGER_CHECK_COMPLETE", content_id, {
        "result": "TRIGGER" if triggered else "NO_TRIGGER",
        "matches": matches,
    })

    if triggered:
        orch.transition(content_id, PipelineState.PENDING_REVIEWER_REVIEW)
        from datetime import datetime
        record = orch.load_state(content_id)
        record.set("sla_reviewer_started_at", datetime.utcnow().isoformat())
    else:
        orch.record_approval(
            brief_id=content_id,
            stage=ApprovalStage.reviewer,
            decision=ApprovalDecision.skipped,
            actor_id="system",
            skip_reason="no legal triggers detected",
        )
        log_event("REVIEWER_STAGE_SKIPPED", content_id,
                  {"reason": "no legal triggers detected"})
        orch.transition(content_id, PipelineState.REVIEWER_SKIPPED)
        await _run_compliance(content_id)


async def _run_compliance(content_id: str):
    from automation.rules_engine import run_rules_engine, apply_auto_fixes
    from agents.evaluator import EvaluatorAgent

    orch = get_orchestrator()
    brief = orch.load_brief(content_id)
    draft = orch.load_latest_draft(content_id)
    if not brief or not draft:
        return

    orch.transition(content_id, PipelineState.COMPLIANCE_RULES_CHECK_IN_PROGRESS)
    log_event("COMPLIANCE_RULES_CHECK_STARTED", content_id)

    violations = run_rules_engine(draft, draft.formats)

    # Auto-fix deterministic violations
    auto_fixed = []
    for v in violations:
        if v.auto_fixable:
            draft.primary_draft = apply_auto_fixes(draft.primary_draft)
            auto_fixed.append(v.rule)

    remaining = [v for v in violations if not v.auto_fixable]

    if remaining:
        log_event("COMPLIANCE_RULES_FAILED", content_id, {
            "violation_count": len(remaining),
            "violations": [
                {"rule": v.rule, "location": v.location, "offending_text": v.offending_text}
                for v in remaining
            ],
        })
        orch.transition(content_id, PipelineState.COMPLIANCE_RULES_FAILED)
        orch.transition(content_id, PipelineState.STRATEGIST_RESOLVING)

        from alerts import get_alert_engine
        get_alert_engine().fire_compliance_failure(content_id, len(remaining))
        return

    log_event("COMPLIANCE_RULES_PASSED", content_id, {"auto_fixed": auto_fixed})

    # Judgment pass
    orch.transition(content_id, PipelineState.COMPLIANCE_JUDGMENT_CHECK_IN_PROGRESS)
    evaluator = EvaluatorAgent()
    judgment = evaluator.evaluate_compliance_judgment(brief, draft)
    log_event("COMPLIANCE_JUDGMENT_CHECK_STARTED", content_id)

    if judgment.result.value == "PASS":
        log_event("COMPLIANCE_JUDGMENT_PASSED", content_id)
        log_event("STATE_TRANSITION_COMPLIANCE_PASSED", content_id)
        orch.transition(content_id, PipelineState.COMPLIANCE_PASSED)
        orch.transition(content_id, PipelineState.PENDING_PUBLISHER_REVIEW)
        from datetime import datetime
        record = orch.load_state(content_id)
        record.set("sla_publisher_started_at", datetime.utcnow().isoformat())
    else:
        log_event("COMPLIANCE_JUDGMENT_FAILED", content_id, {
            "issues": [i.model_dump() for i in judgment.issues]
        })
        orch.transition(content_id, PipelineState.COMPLIANCE_RULES_FAILED)
        orch.transition(content_id, PipelineState.STRATEGIST_RESOLVING)
        from alerts import get_alert_engine
        get_alert_engine().fire_compliance_failure(content_id, len(judgment.issues))


@router.post("/{content_id}/resolve-compliance")
async def resolve_compliance(content_id: str, body: dict):
    """Strategist resolves compliance violations and re-runs the check."""
    orch = get_orchestrator()
    record = orch.load_state(content_id)
    if not record or record.state != PipelineState.STRATEGIST_RESOLVING:
        raise HTTPException(status_code=400, detail="Not in compliance resolution state")

    draft = orch.load_latest_draft(content_id)
    if body.get("manual_edit") and draft:
        draft.primary_draft = body["manual_edit"]
        orch.save_draft(draft)

    log_event("COMPLIANCE_VIOLATION_RESOLVED", content_id, {
        "resolution_type": body.get("resolution_type", "manual"),
        "actor_id": body.get("actor_id", "strategist"),
    }, actor="strategist")

    orch.transition(content_id, PipelineState.COMPLIANCE_RULES_CHECK_IN_PROGRESS)
    await _run_compliance(content_id)
    final = orch.load_state(content_id)
    return {"content_id": content_id, "state": final.state.value}

import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from orchestrator import get_orchestrator
from orchestrator.state_machine import PipelineState
from audit_log.audit_logger import log_event, get_audit_log

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.get("/{content_id}")
async def get_pipeline_status(content_id: str):
    orch = get_orchestrator()
    record = orch.load_state(content_id)
    if not record:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    brief = orch.load_brief(content_id)
    draft = orch.load_latest_draft(content_id)
    research = orch.load_research_brief(content_id)
    approval_log = orch.load_approval_log(content_id)
    alerts = []
    try:
        from alerts import get_alert_engine
        alerts = get_alert_engine().get_active_alerts(content_id)
    except Exception:
        pass

    return {
        "content_id": content_id,
        "state": record.state.value,
        "brief": brief.model_dump(mode="json") if brief else None,
        "research": research.model_dump(mode="json") if research else None,
        "draft": draft.model_dump(mode="json") if draft else None,
        "approval_log": approval_log.model_dump(mode="json"),
        "active_alerts": alerts,
        "revision_count": record.revision_count,
        "scheduled_datetime": record.get("scheduled_datetime"),
        "updated_at": record.get("updated_at"),
    }


@router.post("/{content_id}/research")
async def run_research(content_id: str):
    """F-02 Step 2.1-2.2: Run research agent and evaluate."""
    from agents.researcher import ResearcherAgent
    from agents.evaluator import EvaluatorAgent

    orch = get_orchestrator()
    brief = orch.load_brief(content_id)
    if not brief:
        raise HTTPException(status_code=404, detail="Brief not found")

    orch.transition(content_id, PipelineState.RESEARCH_IN_PROGRESS)
    log_event("RESEARCH_STARTED", content_id)

    researcher = ResearcherAgent()
    research = researcher.run(brief)
    orch.save_research_brief(research)

    evaluator = EvaluatorAgent()
    eval_result = evaluator.evaluate_research(brief, research)
    research.evaluation = eval_result
    orch.save_research_brief(research)

    if research.low_context:
        orch.transition(content_id, PipelineState.RESEARCH_LOW_CONTEXT)
        log_event("RESEARCH_LOW_CONTEXT", content_id, {"chunk_count": research.retrieved_chunk_count})
        from alerts import get_alert_engine
        get_alert_engine().fire_agent_failure(
            content_id, "RESEARCH_LOW_CONTEXT",
            f"Only {research.retrieved_chunk_count} chunks retrieved above threshold"
        )
    else:
        orch.transition(content_id, PipelineState.RESEARCH_COMPLETE)
        log_event("RESEARCH_COMPLETE", content_id, {
            "chunk_count": research.retrieved_chunk_count,
            "evaluation": eval_result.result.value,
        })
        result_event = "RESEARCH_EVALUATED_PASS" if eval_result.result.value == "PASS" else "RESEARCH_EVALUATED_FAIL"
        log_event(result_event, content_id, {"issues": [i.model_dump() for i in eval_result.issues]})

    return {
        "content_id": content_id,
        "state": orch.load_state(content_id).state.value,
        "research": research.model_dump(mode="json"),
        "evaluation": eval_result.model_dump(mode="json"),
    }


@router.post("/{content_id}/draft")
async def run_draft(content_id: str, body: dict = None):
    """F-02 Step 2.3-2.6: Write draft, evaluate, handle revisions."""
    body = body or {}
    from agents.writer import WriterAgent
    from agents.evaluator import EvaluatorAgent
    from agents.formatter import FormatterAgent

    orch = get_orchestrator()
    brief = orch.load_brief(content_id)
    research = orch.load_research_brief(content_id)
    if not brief or not research:
        raise HTTPException(status_code=404, detail="Brief or research not found")

    record = orch.load_state(content_id)
    revision = record.revision_count
    evaluator_critique = body.get("evaluator_critique", "")
    strategist_feedback = body.get("strategist_feedback", "")

    state = PipelineState.DRAFT_REVISION_IN_PROGRESS if revision > 0 else PipelineState.DRAFT_IN_PROGRESS
    orch.transition(content_id, state)
    log_event("DRAFT_STARTED", content_id, {"revision": revision})

    writer = WriterAgent()
    draft = writer.run(brief, research, revision, evaluator_critique, strategist_feedback)

    orch.transition(content_id, PipelineState.DRAFT_UNDER_EVALUATION)
    evaluator = EvaluatorAgent()
    eval_result = evaluator.evaluate_draft(brief, draft)
    draft.evaluation = eval_result
    orch.save_draft(draft)

    log_event("DRAFT_COMPLETE", content_id, {"revision": revision, "word_count": draft.word_count})
    event = "DRAFT_EVALUATED_PASS" if eval_result.result.value == "PASS" else "DRAFT_EVALUATED_FAIL"
    log_event(event, content_id, {
        "revision": revision,
        "result": eval_result.result.value,
        "issues": [i.model_dump() for i in eval_result.issues],
    })

    new_revision = revision + 1
    record.set("revision_count", new_revision)

    if eval_result.result.value == "PASS":
        orch.transition(content_id, PipelineState.DRAFT_EVALUATION_PASSED)

        # Run formatter
        orch.transition(content_id, PipelineState.FORMAT_IN_PROGRESS)
        log_event("FORMAT_STARTED", content_id)
        formatter = FormatterAgent()
        formats = formatter.run(brief, draft)
        format_eval = evaluator.evaluate_format(brief, draft, formats)
        draft.formats = formats
        orch.save_draft(draft)

        if format_eval.result.value == "PASS":
            orch.transition(content_id, PipelineState.FORMAT_COMPLETE)
            log_event("FORMAT_COMPLETE", content_id)
            log_event("FORMAT_EVALUATED_PASS", content_id)
            orch.transition(content_id, PipelineState.PENDING_STRATEGIST_REVIEW)
            record = orch.load_state(content_id)
            record.set("sla_strategist_started_at", __import__("datetime").datetime.utcnow().isoformat())
            from orchestrator.orchestrator import Orchestrator
        else:
            log_event("FORMAT_EVALUATED_FAIL", content_id, {"issues": [i.model_dump() for i in format_eval.issues]})
            if formats.constraint_failures:
                from alerts import get_alert_engine
                get_alert_engine().fire_agent_failure(
                    content_id, "FORMAT_CONSTRAINT_FAILURE",
                    ", ".join(formats.constraint_failures)
                )

    elif new_revision > settings.max_draft_revisions:
        orch.transition(content_id, PipelineState.DRAFT_ESCALATED)
        log_event("DRAFT_ESCALATED", content_id, {"revision": revision})
        from alerts import get_alert_engine
        get_alert_engine().fire_agent_failure(
            content_id, "DRAFT_ESCALATED",
            f"Draft failed evaluation after {settings.max_draft_revisions} revisions"
        )
    else:
        orch.transition(content_id, PipelineState.DRAFT_REVISION_IN_PROGRESS)

    final_record = orch.load_state(content_id)
    return {
        "content_id": content_id,
        "state": final_record.state.value,
        "draft": draft.model_dump(mode="json"),
        "evaluation": eval_result.model_dump(mode="json"),
        "revision": revision,
    }


@router.get("/{content_id}/stream-draft")
async def stream_draft(content_id: str):
    """Stream the draft generation in real time via SSE."""
    from agents.writer import WriterAgent
    orch = get_orchestrator()
    brief = orch.load_brief(content_id)
    research = orch.load_research_brief(content_id)
    if not brief or not research:
        raise HTTPException(status_code=404, detail="Brief or research not found")

    record = orch.load_state(content_id)

    async def generate():
        writer = WriterAgent()
        for chunk in writer.stream(brief, research, record.revision_count):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/{content_id}/accept-low-context")
async def accept_low_context(content_id: str):
    """Allow pipeline to proceed despite low context."""
    orch = get_orchestrator()
    record = orch.load_state(content_id)
    if not record or record.state != PipelineState.RESEARCH_LOW_CONTEXT:
        raise HTTPException(status_code=400, detail="Pipeline is not in RESEARCH_LOW_CONTEXT state")
    orch.transition(content_id, PipelineState.RESEARCH_COMPLETE)
    log_event("LOW_CONTEXT_ACCEPTED", content_id, {}, actor="requester")
    return {"content_id": content_id, "state": PipelineState.RESEARCH_COMPLETE.value}

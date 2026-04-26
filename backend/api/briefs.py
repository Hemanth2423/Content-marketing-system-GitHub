from fastapi import APIRouter, HTTPException
from models.brief import Brief, BriefCreate, BriefStatus
from orchestrator import get_orchestrator
from orchestrator.state_machine import PipelineState
from automation.validator import validate_brief, check_duplicate
from audit_log.audit_logger import log_event

router = APIRouter(prefix="/briefs", tags=["briefs"])


@router.post("")
async def create_brief(data: BriefCreate):
    """F-01 Step 1-3: Validate, check duplicates, create brief."""
    errors = validate_brief(data)
    if errors:
        log_event("BRIEF_VALIDATION_FAILED", "unknown", {"errors": errors})
        raise HTTPException(status_code=422, detail={"errors": errors})

    is_dup, dup_id = check_duplicate(data.title, data.content_type.value)
    if is_dup:
        log_event("DUPLICATE_DETECTED", "unknown", {"matching_brief_id": dup_id, "title": data.title})
        raise HTTPException(
            status_code=409,
            detail={"error": "Duplicate brief", "matching_brief_id": dup_id},
        )

    brief = Brief(**data.model_dump())
    orch = get_orchestrator()
    orch.save_brief(brief)
    record = orch.create_pipeline(brief)

    log_event("BRIEF_FORM_SUBMITTED", brief.brief_id, {"title": brief.title, "content_type": brief.content_type.value})
    record = orch.transition(brief.brief_id, PipelineState.BRIEF_SUBMITTED)
    log_event("DUPLICATE_CHECK_COMPLETE", brief.brief_id, {"result": "DUPLICATE_CLEAR"})

    return {"brief_id": brief.brief_id, "state": record.state.value}


@router.post("/{brief_id}/enrich")
async def enrich_brief(brief_id: str):
    """F-01 Step 4-5: Run enrichment and evaluate."""
    from agents.researcher import ResearcherAgent
    from agents.evaluator import EvaluatorAgent

    orch = get_orchestrator()
    brief = orch.load_brief(brief_id)
    if not brief:
        raise HTTPException(status_code=404, detail="Brief not found")

    orch.transition(brief_id, PipelineState.ENRICHMENT_IN_PROGRESS)
    log_event("BRIEF_ENRICHMENT_STARTED", brief_id)

    researcher = ResearcherAgent()
    research = researcher.run(brief)

    evaluator = EvaluatorAgent()
    eval_result = evaluator.evaluate_research(brief, research)

    enrichment_data = {
        "suggested_keywords": [kw for kw in brief.keywords] + (research.key_points[:3] if research.key_points else []),
        "audience_framing": research.suggested_angles[0] if research.suggested_angles else "",
        "content_angle": research.suggested_angles[1] if len(research.suggested_angles) > 1 else "",
        "similar_past_content_ids": [],
    }

    orch.transition(brief_id, PipelineState.ENRICHMENT_COMPLETE)
    log_event("BRIEF_ENRICHMENT_COMPLETE", brief_id, {
        "evaluation_result": eval_result.result.value,
        "low_context": research.low_context,
    })
    log_event("ENRICHMENT_EVALUATED_PASS" if eval_result.result.value == "PASS" else "ENRICHMENT_EVALUATED_FAIL",
              brief_id, {"issues": [i.model_dump() for i in eval_result.issues]})

    return {
        "brief_id": brief_id,
        "enrichment": enrichment_data,
        "research_summary": {
            "key_points": research.key_points[:5],
            "suggested_angles": research.suggested_angles,
            "low_context": research.low_context,
            "source_count": research.retrieved_chunk_count,
        },
        "evaluation": eval_result.result.value,
    }


@router.post("/{brief_id}/confirm")
async def confirm_brief(brief_id: str, body: dict):
    """F-01 Step 6: Requester confirms brief."""
    from datetime import datetime
    orch = get_orchestrator()
    brief = orch.load_brief(brief_id)
    if not brief:
        raise HTTPException(status_code=404, detail="Brief not found")

    # Apply any edits from Requester
    for field in ["title", "target_audience", "goal", "keywords"]:
        if field in body:
            setattr(brief, field, body[field])

    brief.status = BriefStatus.confirmed
    brief.confirmed_at = datetime.utcnow()
    orch.save_brief(brief)

    orch.transition(brief_id, PipelineState.BRIEF_CONFIRMED)
    log_event("BRIEF_CONFIRMED", brief_id, {
        "requester_id": body.get("requester_id", "requester"),
        "title": brief.title,
    }, actor="requester", actor_id=body.get("requester_id", "requester"))

    return {"brief_id": brief_id, "state": PipelineState.BRIEF_CONFIRMED.value}


@router.get("/{brief_id}")
async def get_brief(brief_id: str):
    orch = get_orchestrator()
    brief = orch.load_brief(brief_id)
    if not brief:
        raise HTTPException(status_code=404, detail="Brief not found")
    return brief


@router.get("")
async def list_briefs():
    return get_orchestrator().list_all_pipelines()

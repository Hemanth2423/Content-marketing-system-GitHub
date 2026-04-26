from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from audit_log.audit_logger import get_audit_log, verify_chain, export_audit_csv

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/{content_id}")
async def get_audit(content_id: str, stage: str = None):
    entries = get_audit_log(content_id, stage_filter=stage)
    return {"content_id": content_id, "entries": entries, "count": len(entries)}


@router.get("/{content_id}/export")
async def export_audit(content_id: str):
    is_valid, broken_at = verify_chain(content_id)
    csv_data = export_audit_csv(content_id)
    headers = {
        "Content-Disposition": f"attachment; filename=audit_{content_id}.csv",
        "X-Chain-Valid": str(is_valid),
        "X-Chain-Broken-At": broken_at or "",
    }
    return PlainTextResponse(content=csv_data, media_type="text/csv", headers=headers)


@router.get("/{content_id}/verify")
async def verify_audit_chain(content_id: str):
    is_valid, broken_at = verify_chain(content_id)
    return {
        "content_id": content_id,
        "chain_valid": is_valid,
        "broken_at_entry_id": broken_at,
    }

from fastapi import APIRouter, HTTPException
from alerts import get_alert_engine

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("")
async def list_alerts(content_id: str = None):
    engine = get_alert_engine()
    return {"alerts": engine.get_active_alerts(content_id)}


@router.post("/{alert_id}/dismiss")
async def dismiss_alert(alert_id: str):
    engine = get_alert_engine()
    dismissed = engine.dismiss_alert(alert_id)
    if not dismissed:
        raise HTTPException(status_code=404, detail="Alert not found or already dismissed")
    return {"dismissed": True, "alert_id": alert_id}

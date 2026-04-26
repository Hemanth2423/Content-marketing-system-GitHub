import json
from datetime import datetime
from pathlib import Path
from config import settings
from models.brief import BriefCreate


def validate_brief(data: BriefCreate) -> list[str]:
    """Returns list of validation error messages. Empty = valid."""
    errors = []
    if len(data.title) < 10:
        errors.append("title must be at least 10 characters")
    if len(data.title) > 200:
        errors.append("title must be at most 200 characters")
    now = datetime.now(data.requested_publish_date.tzinfo) if data.requested_publish_date.tzinfo else datetime.utcnow()
    if data.requested_publish_date <= now:
        errors.append("requested_publish_date must be in the future")
    if not data.target_audience or len(data.target_audience.strip()) < 5:
        errors.append("target_audience is required (minimum 5 characters)")
    if not data.goal or len(data.goal.strip()) < 10:
        errors.append("goal is required (minimum 10 characters)")
    return errors


def check_duplicate(title: str, content_type: str) -> tuple[bool, str | None]:
    """Returns (is_duplicate, matching_brief_id)."""
    briefs_dir = settings.storage_dir / "briefs"
    if not briefs_dir.exists():
        return False, None
    for path in briefs_dir.glob("*.json"):
        if "_approvals" in path.name:
            continue
        try:
            data = json.loads(path.read_text())
            if (
                data.get("title", "").strip().lower() == title.strip().lower()
                and data.get("content_type") == content_type
            ):
                return True, data.get("brief_id")
        except Exception:
            continue
    return False, None

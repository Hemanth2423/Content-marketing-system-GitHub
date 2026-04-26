import hashlib
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from config import settings
from models.audit import AuditEntry

_lock = threading.Lock()


def _audit_path(content_id: str) -> Path:
    path = settings.storage_dir / "audit_logs" / f"{content_id}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _compute_hash(payload: dict, prev_hash: str) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str) + prev_hash
    return hashlib.sha256(raw.encode()).hexdigest()


def _last_hash(content_id: str) -> str:
    path = _audit_path(content_id)
    if not path.exists():
        return ""
    last_line = ""
    with open(path, "r") as f:
        for line in f:
            stripped = line.strip()
            if stripped:
                last_line = stripped
    if not last_line:
        return ""
    try:
        return json.loads(last_line).get("entry_hash", "")
    except Exception:
        return ""


def log_event(
    event_type: str,
    content_id: str,
    payload: dict[str, Any] = None,
    actor: str = "system",
    actor_id: Optional[str] = None,
) -> AuditEntry:
    """Write an audit entry. Must be called BEFORE the action it records."""
    payload = payload or {}
    with _lock:
        prev_hash = _last_hash(content_id)
        entry = AuditEntry(
            event_type=event_type,
            content_id=content_id,
            actor=actor,
            actor_id=actor_id,
            payload=payload,
            prev_entry_hash=prev_hash,
        )
        entry_dict = entry.model_dump(mode="json")
        entry.entry_hash = _compute_hash(entry_dict, prev_hash)
        entry_dict["entry_hash"] = entry.entry_hash

        path = _audit_path(content_id)
        with open(path, "a") as f:
            f.write(json.dumps(entry_dict, default=str) + "\n")

    return entry


def get_audit_log(content_id: str, stage_filter: Optional[str] = None) -> list[dict]:
    path = _audit_path(content_id)
    if not path.exists():
        return []
    entries = []
    with open(path, "r") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                entry = json.loads(stripped)
                if stage_filter and stage_filter.lower() not in entry.get("event_type", "").lower():
                    continue
                entries.append(entry)
            except Exception:
                continue
    return entries


def verify_chain(content_id: str) -> tuple[bool, Optional[str]]:
    """Returns (is_valid, broken_at_entry_id). Used on export."""
    entries = get_audit_log(content_id)
    prev_hash = ""
    for entry in entries:
        payload_for_hash = {k: v for k, v in entry.items() if k != "entry_hash"}
        expected = _compute_hash(payload_for_hash, prev_hash)
        if expected != entry.get("entry_hash", ""):
            return False, entry.get("entry_id")
        prev_hash = entry["entry_hash"]
    return True, None


def export_audit_csv(content_id: str) -> str:
    entries = get_audit_log(content_id)
    if not entries:
        return "entry_id,event_type,actor,timestamp,payload\n"
    lines = ["entry_id,event_type,actor,timestamp,payload"]
    for e in entries:
        payload_str = json.dumps(e.get("payload", {}), default=str).replace('"', '""')
        lines.append(
            f"{e.get('entry_id','')},{e.get('event_type','')},{e.get('actor','')},"
            f"{e.get('timestamp','')},\"{payload_str}\""
        )
    return "\n".join(lines)

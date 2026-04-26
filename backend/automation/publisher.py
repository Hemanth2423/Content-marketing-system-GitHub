import json
import uuid
import requests
from datetime import datetime
from pathlib import Path
from config import settings
from models.draft import Draft, ChannelFormats
from models.brief import Brief


def publish_all_channels(brief: Brief, draft: Draft, formats: ChannelFormats) -> dict:
    """
    Execute channel publishing. Returns per-channel results.
    Each channel reports success (with post_id) or failure (with error).
    """
    from audit_log.audit_logger import log_event
    channel_specs_path = settings.data_dir / "channel_specs.json"
    channel_specs = json.loads(channel_specs_path.read_text()) if channel_specs_path.exists() else {}
    expected = channel_specs.get("channel_by_content_type", {}).get(brief.content_type.value, [])

    results = {}

    for channel in expected:
        log_event(
            event_type="CHANNEL_PUBLISH_INITIATED",
            content_id=brief.brief_id,
            payload={"channel": channel},
        )
        if channel == "blog":
            results["blog"] = _publish_blog(brief, draft)
        elif channel == "linkedin":
            results["linkedin"] = _publish_linkedin(brief, formats)
        elif channel == "twitter":
            results["twitter"] = _publish_twitter(brief, formats)
        elif channel == "email":
            results["email"] = _publish_email(brief, formats)

        event_type = (
            "CHANNEL_PUBLISH_SUCCESS" if results[channel]["status"] == "SUCCESS"
            else "CHANNEL_PUBLISH_FAILED"
        )
        log_event(
            event_type=event_type,
            content_id=brief.brief_id,
            payload={"channel": channel, **results[channel]},
        )

    return results


def _publish_blog(brief: Brief, draft: Draft) -> dict:
    try:
        pub_dir = settings.storage_dir / "published" / "blog"
        pub_dir.mkdir(parents=True, exist_ok=True)
        slug = brief.title.lower().replace(" ", "-")[:60]
        slug = "".join(c if c.isalnum() or c == "-" else "" for c in slug)
        filename = f"{datetime.utcnow().strftime('%Y-%m-%d')}-{slug}.md"
        filepath = pub_dir / filename

        content = f"""---
title: {brief.title}
content_type: {brief.content_type.value}
published_at: {datetime.utcnow().isoformat()}
brief_id: {brief.brief_id}
---

{draft.primary_draft}
"""
        filepath.write_text(content)
        return {
            "status": "SUCCESS",
            "post_id": filename,
            "published_at": datetime.utcnow().isoformat(),
            "path": str(filepath),
        }
    except Exception as e:
        return {"status": "FAILED", "error": str(e)}


_zernio_accounts: dict = {}


def _get_zernio_account_id(platform: str) -> str | None:
    global _zernio_accounts
    if not _zernio_accounts and settings.zernio_api_key:
        try:
            resp = requests.get(
                "https://zernio.com/api/v1/accounts",
                headers={"Authorization": f"Bearer {settings.zernio_api_key}"},
                timeout=10,
            )
            resp.raise_for_status()
            for acct in resp.json().get("accounts", []):
                _zernio_accounts[acct.get("platform", "").lower()] = acct.get("_id") or acct.get("accountId")
        except Exception:
            pass
    return _zernio_accounts.get(platform)


def _zernio_post(platform: str, content: str) -> dict:
    if not settings.zernio_api_key:
        return {"status": "MOCK", "post_id": f"{platform[:2]}_{uuid.uuid4().hex[:12]}"}
    account_id = _get_zernio_account_id(platform)
    payload: dict = {"content": content, "publishNow": True, "platforms": [{"platform": platform}]}
    if account_id:
        payload["platforms"][0]["accountId"] = account_id
    resp = requests.post(
        "https://zernio.com/api/v1/posts",
        headers={"Authorization": f"Bearer {settings.zernio_api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=15,
    )
    resp.raise_for_status()
    post = resp.json().get("post", {})
    platform_data = (post.get("platforms") or [{}])[0]
    return {
        "status": "SUCCESS",
        "post_id": platform_data.get("platformPostId") or post.get("_id", ""),
        "url": platform_data.get("platformPostUrl", ""),
        "published_at": post.get("publishedAt", datetime.utcnow().isoformat()),
    }


def _publish_linkedin(brief: Brief, formats: ChannelFormats) -> dict:
    if not formats.linkedin:
        return {"status": "FAILED", "error": "No LinkedIn format available"}
    content = formats.linkedin.body[:3000]
    try:
        result = _zernio_post("linkedin", content)
        return result
    except Exception as e:
        return {"status": "FAILED", "error": str(e)}


def _publish_twitter(brief: Brief, formats: ChannelFormats) -> dict:
    if not formats.twitter:
        return {"status": "FAILED", "error": "No Twitter format available"}
    content = formats.twitter.thread[0] if formats.twitter.thread else ""
    if not content:
        return {"status": "FAILED", "error": "Empty Twitter thread"}
    try:
        result = _zernio_post("twitter", content[:280])
        result["thread_count"] = len(formats.twitter.thread)
        return result
    except Exception as e:
        return {"status": "FAILED", "error": str(e)}


def _publish_email(brief: Brief, formats: ChannelFormats) -> dict:
    if not formats.email:
        return {"status": "FAILED", "error": "No email format available"}
    if settings.mailgun_api_key == "dummy" or "dummy" in settings.mailgun_api_key:
        mock_id = f"mg_{uuid.uuid4().hex[:12]}"
        return {
            "status": "SUCCESS",
            "post_id": mock_id,
            "subject": formats.email.subject,
            "published_at": datetime.utcnow().isoformat(),
            "note": "Mock — Mailgun key is a placeholder",
        }
    try:
        resp = requests.post(
            f"https://api.mailgun.net/v3/{settings.mailgun_domain}/messages",
            auth=("api", settings.mailgun_api_key),
            data={
                "from": settings.mailgun_from,
                "to": [settings.mailgun_to],
                "subject": formats.email.subject,
                "text": formats.email.body,
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "status": "SUCCESS",
            "post_id": data.get("id", ""),
            "subject": formats.email.subject,
            "published_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {"status": "FAILED", "error": str(e)}

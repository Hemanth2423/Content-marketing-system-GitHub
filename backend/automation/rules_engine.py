import json
import re
from dataclasses import dataclass
from config import settings
from models.draft import Draft, ChannelFormats


@dataclass
class ComplianceViolation:
    rule: str
    location: str
    offending_text: str
    suggested_fix: str
    auto_fixable: bool = False


PRODUCT_NAME_CORRECTIONS = {
    r"\bgithub\b": "GitHub",
    r"\bGITHUB\b": "GitHub",
    r"\bgit hub\b": "GitHub",
    r"\bgithub actions\b": "GitHub Actions",
    r"\bgithub copilot\b": "GitHub Copilot",
    r"\bgithub codespaces\b": "GitHub Codespaces",
}

PROHIBITED_PHRASES = [
    "game-changing",
    "revolutionary",
    "world-class",
    "best-in-class",
    "cutting-edge",
    "state-of-the-art",
    "seamlessly integrates",
    "end-to-end solution",
    "robust platform",
    "at the end of the day",
    "circle back",
    "synergize",
]


def run_rules_engine(draft: Draft, formats: ChannelFormats | None = None) -> list[ComplianceViolation]:
    """
    Deterministic rules check. Same input → same violations every time.
    Returns list of violations. Empty = passed.
    """
    violations = []
    all_texts = {"primary_draft": draft.primary_draft}
    if formats:
        if formats.linkedin:
            all_texts["linkedin_post"] = formats.linkedin.post
        if formats.twitter:
            all_texts["twitter_thread"] = " ".join(formats.twitter.thread)
        if formats.email:
            all_texts["email_subject"] = formats.email.subject
            all_texts["email_body"] = formats.email.body

    for location, text in all_texts.items():
        # Check product name formatting
        for pattern, correct in PRODUCT_NAME_CORRECTIONS.items():
            for m in re.finditer(pattern, text, re.IGNORECASE):
                found = text[m.start():m.end()]
                if found != correct:
                    violations.append(ComplianceViolation(
                        rule="product_name_formatting",
                        location=location,
                        offending_text=found,
                        suggested_fix=f'Replace "{found}" with "{correct}"',
                        auto_fixable=True,
                    ))

        # Check prohibited phrases
        for phrase in PROHIBITED_PHRASES:
            if phrase.lower() in text.lower():
                violations.append(ComplianceViolation(
                    rule="prohibited_phrase",
                    location=location,
                    offending_text=phrase,
                    suggested_fix=f'Remove or rewrite the phrase "{phrase}" — see brand guidelines for alternatives',
                    auto_fixable=False,
                ))

    # Channel-specific character limit checks
    if formats:
        channel_specs = _load_channel_specs()
        if formats.linkedin:
            max_chars = channel_specs.get("linkedin", {}).get("max_characters", 3000)
            if formats.linkedin.character_count > max_chars:
                violations.append(ComplianceViolation(
                    rule="linkedin_character_limit",
                    location="linkedin_post",
                    offending_text=f"{formats.linkedin.character_count} characters",
                    suggested_fix=f"Reduce LinkedIn post to under {max_chars} characters",
                    auto_fixable=False,
                ))
        if formats.email:
            if len(formats.email.subject) > 60:
                violations.append(ComplianceViolation(
                    rule="email_subject_length",
                    location="email_subject",
                    offending_text=formats.email.subject,
                    suggested_fix="Shorten email subject to 60 characters or fewer",
                    auto_fixable=False,
                ))

    return violations


def apply_auto_fixes(text: str) -> str:
    """Apply only deterministic auto-fixes (product name corrections)."""
    for pattern, correct in PRODUCT_NAME_CORRECTIONS.items():
        text = re.sub(pattern, correct, text, flags=re.IGNORECASE)
    return text


def _load_channel_specs() -> dict:
    path = settings.data_dir / "channel_specs.json"
    return json.loads(path.read_text()) if path.exists() else {}

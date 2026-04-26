import re
from config import settings


def _load_flags() -> list[str]:
    path = settings.data_dir / "legal_flags.txt"
    if not path.exists():
        return []
    flags = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            flags.append(line)
    return flags


def check_legal_triggers(text: str) -> tuple[bool, list[dict]]:
    """
    Returns (triggered, matches).
    matches is a list of {keyword, location} dicts.
    Deterministic keyword match — same input, same output, always.
    """
    flags = _load_flags()
    matches = []
    text_lower = text.lower()

    for flag in flags:
        pattern = re.escape(flag.lower())
        for m in re.finditer(pattern, text_lower):
            start = max(0, m.start() - 40)
            end = min(len(text), m.end() + 40)
            matches.append({
                "keyword": flag,
                "location": f"position {m.start()}",
                "context": text[start:end].strip(),
            })

    return len(matches) > 0, matches

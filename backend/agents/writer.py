import json
import anthropic
from config import settings
from models.brief import Brief, ContentType
from models.draft import Draft, ResearchBrief, DraftMetadata

_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

CONTENT_TYPE_STRUCTURES = {
    ContentType.tutorial: """Structure: hook that establishes the problem → prerequisites → numbered step-by-step body
(each step: what to do, the command/code with inline comments, expected output) → verification step → next steps.
Use H2 for major sections, H3 for steps. Code blocks for all commands.""",

    ContentType.announcement: """Structure: lead with what changed and why it matters → concrete use case or example → call to action.
No throat-clearing. No superlatives. Direct and specific. 500-800 words.""",

    ContentType.thought_leadership: """Structure: specific opinionated opening statement (not "many developers...") → the problem or trend →
evidence and GitHub's position → implications for developers → forward-looking close that commits to a view.
800-1200 words. Take a clear position. Do not hedge.""",

    ContentType.case_study: """Structure: customer context (company, scale, challenge) → what they built with GitHub and how →
measurable outcome with specific numbers if available → why this matters for similar companies.
1200-2000 words. Lead with the customer's challenge, not GitHub's product.""",
}


class WriterAgent:
    def run(
        self,
        brief: Brief,
        research: ResearchBrief,
        revision: int = 0,
        evaluator_critique: str = "",
        strategist_feedback: str = "",
    ) -> Draft:
        brand = self._load_brand_guidelines()
        past_examples = self._load_past_examples(brief.content_type)
        structure = CONTENT_TYPE_STRUCTURES.get(brief.content_type, "")

        critique_section = ""
        if evaluator_critique:
            critique_section = f"\nEVALUATOR CRITIQUE (address every point):\n{evaluator_critique}\n"
        if strategist_feedback:
            critique_section += f"\nSTRATEGIST FEEDBACK (explicit instruction):\n{strategist_feedback}\n"

        revision_instruction = ""
        if revision > 0:
            revision_instruction = f"\nThis is revision {revision}. Produce a FRESH draft that fully addresses the critique above — do not patch the previous version."

        sources_text = "\n".join(
            f"- [{s.file}]: {s.chunk[:300]}"
            for s in research.sources[:6]
        )
        key_points_text = "\n".join(f"- {p}" for p in research.key_points[:8])
        angles_text = "\n".join(f"- {a}" for a in research.suggested_angles[:3])

        prompt = f"""You are the Writer Agent for GitHub's content marketing system.
Write a complete {brief.content_type.value} for GitHub.

CONTENT BRIEF:
- Title: {brief.title}
- Type: {brief.content_type.value}
- Target audience: {brief.target_audience}
- Goal: {brief.goal}
- Required keywords (use naturally): {', '.join(brief.keywords) if brief.keywords else 'none specified'}

STRUCTURE REQUIREMENTS:
{structure}

RESEARCH MATERIAL (write from these sources, do not invent facts):
Key points:
{key_points_text}

Suggested angles (choose one):
{angles_text}

Sources (for reference):
{sources_text}

BRAND VOICE (read and apply):
{brand[:600]}

PAST SUCCESSFUL EXAMPLES (for tone reference):
{past_examples[:400]}{critique_section}{revision_instruction}

OUTPUT:
Write the complete draft in markdown. After the draft, add a metadata block:
---METADATA---
tone: <one word>
target_audience: <brief description>
keywords_used: <comma-separated list of required keywords you used>
word_count: <approximate>
---END---"""

        full_text = ""
        with _client.messages.stream(
            model=settings.model_sonnet,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            for text in stream.text_stream:
                full_text += text

        primary_draft, metadata = self._parse_output(full_text)
        return Draft(
            brief_id=brief.brief_id,
            revision=revision,
            content_type=brief.content_type.value,
            primary_draft=primary_draft,
            word_count=len(primary_draft.split()),
            metadata=DraftMetadata(
                tone=metadata.get("tone", ""),
                target_audience=metadata.get("target_audience", brief.target_audience),
                keywords_used=[k.strip() for k in metadata.get("keywords_used", "").split(",") if k.strip()],
            ),
        )

    def stream(
        self,
        brief: Brief,
        research: ResearchBrief,
        revision: int = 0,
        evaluator_critique: str = "",
        strategist_feedback: str = "",
    ):
        """Yield text chunks for SSE streaming."""
        brand = self._load_brand_guidelines()
        structure = CONTENT_TYPE_STRUCTURES.get(brief.content_type, "")
        key_points_text = "\n".join(f"- {p}" for p in research.key_points[:8])

        critique_section = ""
        if evaluator_critique:
            critique_section = f"\nEVALUATOR CRITIQUE:\n{evaluator_critique}\n"
        if strategist_feedback:
            critique_section += f"\nSTRATEGIST FEEDBACK:\n{strategist_feedback}\n"

        prompt = f"""You are the Writer Agent for GitHub's content marketing system.
Write a complete {brief.content_type.value} for GitHub.

Title: {brief.title}
Audience: {brief.target_audience}
Goal: {brief.goal}
Keywords: {', '.join(brief.keywords) if brief.keywords else 'none'}

Structure: {structure}

Key research points:
{key_points_text}

Brand: developer-first, direct, no jargon, no superlatives.
{critique_section}

Write the complete draft in markdown now:"""

        with _client.messages.stream(
            model=settings.model_sonnet,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            for text in stream.text_stream:
                yield text

    def _parse_output(self, full_text: str) -> tuple[str, dict]:
        if "---METADATA---" in full_text:
            parts = full_text.split("---METADATA---")
            draft = parts[0].strip()
            meta_block = parts[1].split("---END---")[0].strip()
            metadata = {}
            for line in meta_block.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    metadata[k.strip()] = v.strip()
            return draft, metadata
        return full_text.strip(), {}

    def _load_brand_guidelines(self) -> str:
        path = settings.data_dir / "brand_guidelines.txt"
        return path.read_text() if path.exists() else ""

    def _load_past_examples(self, content_type: ContentType) -> str:
        path = settings.data_dir / "past_campaigns.json"
        if not path.exists():
            return ""
        campaigns = json.loads(path.read_text())
        examples = [c for c in campaigns if c.get("content_type") == content_type.value]
        if not examples:
            return ""
        ex = examples[0]
        return f"Example past {content_type.value}: '{ex['title']}' — angle: {ex.get('angle','')}"

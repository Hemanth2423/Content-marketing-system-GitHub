import json
import requests
import anthropic
from config import settings
from models.brief import Brief
from models.draft import ResearchBrief, ResearchSource

_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)


class ResearcherAgent:
    def run(self, brief: Brief, force_web_search: bool = False) -> ResearchBrief:
        from vector_store import get_store

        query = f"{brief.title} {brief.goal} {' '.join(brief.keywords)}"
        store = get_store()
        raw_results = store.search(query, top_k=settings.retrieval_top_k)

        # Filter to relevance threshold
        sources = [
            ResearchSource(**r)
            for r in raw_results
            if r["relevance_score"] >= settings.retrieval_min_score
        ]

        low_context = len(sources) < settings.low_context_threshold

        # Web search fallback
        if low_context or force_web_search:
            web_sources = self._web_search(brief)
            sources.extend(web_sources)
            low_context = len(sources) < settings.low_context_threshold

        if not sources:
            return ResearchBrief(
                brief_id=brief.brief_id,
                low_context=True,
                retrieved_chunk_count=0,
            )

        # Summarise into structured research brief using Haiku
        structured = self._structure(brief, sources)
        structured.low_context = low_context
        return structured

    def _web_search(self, brief: Brief) -> list[ResearchSource]:
        if not settings.firecrawl_api_key:
            return []
        query = f"GitHub {brief.title} {brief.content_type.value} developer"
        try:
            resp = requests.post(
                "https://api.firecrawl.dev/v1/search",
                headers={
                    "Authorization": f"Bearer {settings.firecrawl_api_key}",
                    "Content-Type": "application/json",
                },
                json={"query": query, "limit": settings.firecrawl_max_results},
                timeout=15,
            )
            resp.raise_for_status()
            results = resp.json().get("data", [])
            sources = []
            for item in results:
                content = item.get("markdown") or item.get("description") or ""
                if content:
                    sources.append(ResearchSource(
                        file=f"web:{item.get('url','')[:80]}",
                        chunk=content[:500],
                        relevance_score=0.65,
                    ))
            return sources
        except Exception:
            return []

    def _structure(self, brief: Brief, sources: list[ResearchSource]) -> ResearchBrief:
        sources_text = "\n".join(
            f"[{s.file}] (score={s.relevance_score}): {s.chunk[:400]}"
            for s in sources[:8]
        )
        past_campaigns = self._load_past_campaigns()
        similar_ids = self._find_similar_campaigns(brief, past_campaigns)

        prompt = f"""You are the Research Agent for GitHub's content marketing system.

Content brief:
- Title: {brief.title}
- Type: {brief.content_type.value}
- Audience: {brief.target_audience}
- Goal: {brief.goal}
- Keywords: {', '.join(brief.keywords) if brief.keywords else 'none specified'}

Retrieved source material:
{sources_text}

Task: Structure this material into a research brief. Return ONLY valid JSON with this exact schema:
{{
  "key_points": ["<factual claim from sources, max 8>"],
  "suggested_angles": ["<possible content framing, max 3>"],
  "gaps": ["<topic in brief not covered by sources, if any>"]
}}

Rules:
- key_points must be drawn from the source material. No invented facts.
- suggested_angles are options for the writer, not decisions.
- gaps identify areas where source coverage is thin.
- Return only the JSON object, no other text."""

        response = _client.messages.create(
            model=settings.model_haiku,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()

        try:
            # Strip markdown code fences if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            parsed = json.loads(raw)
        except Exception:
            parsed = {"key_points": [], "suggested_angles": [], "gaps": ["Could not parse structured output"]}

        return ResearchBrief(
            brief_id=brief.brief_id,
            sources=sources,
            key_points=parsed.get("key_points", []),
            suggested_angles=parsed.get("suggested_angles", []),
            gaps=parsed.get("gaps", []),
            retrieved_chunk_count=len(sources),
        )

    def _load_past_campaigns(self) -> list[dict]:
        path = settings.data_dir / "past_campaigns.json"
        if path.exists():
            return json.loads(path.read_text())
        return []

    def _find_similar_campaigns(self, brief: Brief, campaigns: list[dict]) -> list[str]:
        return [
            c["id"] for c in campaigns
            if c.get("content_type") == brief.content_type.value
        ][:2]

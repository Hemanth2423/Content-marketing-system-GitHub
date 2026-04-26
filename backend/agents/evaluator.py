import json
import anthropic
from config import settings
from models.draft import (
    ResearchBrief, Draft, ChannelFormats, Evaluation, EvaluationResult, EvaluationIssue
)
from models.brief import Brief

_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)


class EvaluatorAgent:
    def evaluate_research(self, brief: Brief, research: ResearchBrief) -> Evaluation:
        brand = self._load_brand_guidelines()
        prompt = f"""You are the Central Evaluator for GitHub's content marketing system.
Evaluate this research brief against the content brief.

Content brief:
- Title: {brief.title}
- Type: {brief.content_type.value}
- Audience: {brief.target_audience}
- Goal: {brief.goal}
- Keywords required: {', '.join(brief.keywords) if brief.keywords else 'none'}

Research brief:
- Key points: {json.dumps(research.key_points)}
- Suggested angles: {json.dumps(research.suggested_angles)}
- Gaps: {json.dumps(research.gaps)}
- Sources retrieved: {research.retrieved_chunk_count}
- Low context: {research.low_context}

Evaluate on:
1. Are the key points relevant to the brief goal?
2. Do the suggested angles serve the stated audience?
3. Are gaps appropriately identified?
4. Is there enough material for a quality draft?

Return ONLY valid JSON:
{{
  "result": "PASS" or "FAIL" or "EVALUATION_INCONCLUSIVE",
  "confidence": 0.0-1.0,
  "issues": [
    {{"field": "key_points", "problem": "...", "location": "...", "expected": "..."}}
  ]
}}
issues array should be empty if PASS. Return only the JSON."""

        return self._call(prompt, settings.model_haiku)

    def evaluate_draft(self, brief: Brief, draft: Draft) -> Evaluation:
        brand = self._load_brand_guidelines()
        legal_flags = self._load_legal_flags()

        prompt = f"""You are the Central Evaluator for GitHub's content marketing system.
Evaluate this draft against the content brief and brand guidelines.

Content brief:
- Title: {brief.title}
- Type: {brief.content_type.value}
- Audience: {brief.target_audience}
- Goal: {brief.goal}
- Keywords required: {', '.join(brief.keywords) if brief.keywords else 'none'}

Draft (first 3000 chars):
{draft.primary_draft[:3000]}

Brand guidelines summary:
{brand[:800]}

Legal flag keywords (any match = flag):
{', '.join(legal_flags[:20])}

Evaluate on:
1. Does the draft address the brief goal?
2. Is tone appropriate for the audience? (developer-first, not marketing-heavy)
3. Are required keywords present?
4. Is structure appropriate for content type {brief.content_type.value}?
5. Does any text match legal flag keywords? If so, flag as issue.
6. No invented statistics without attribution?

Use Sonnet-level judgment for tone and argument quality.

Return ONLY valid JSON:
{{
  "result": "PASS" or "FAIL" or "EVALUATION_INCONCLUSIVE",
  "confidence": 0.0-1.0,
  "issues": [
    {{"field": "tone", "problem": "...", "location": "paragraph 2", "expected": "developer-credible, direct"}}
  ]
}}
Return only the JSON."""

        return self._call(prompt, settings.model_sonnet)

    def evaluate_format(self, brief: Brief, draft: Draft, formats: ChannelFormats) -> Evaluation:
        channel_specs = self._load_channel_specs()
        content_type = brief.content_type.value
        expected_channels = channel_specs.get("channel_by_content_type", {}).get(content_type, [])

        issues = []
        # Deterministic character limit checks
        if formats.linkedin and "linkedin" in expected_channels:
            if formats.linkedin.character_count > channel_specs.get("linkedin", {}).get("max_characters", 3000):
                issues.append(EvaluationIssue(
                    field="linkedin.post",
                    problem=f"Exceeds max characters ({formats.linkedin.character_count} > 3000)",
                    location="linkedin post",
                    expected="Maximum 3000 characters",
                ))
        if formats.twitter and "twitter" in expected_channels:
            for i, tweet in enumerate(formats.twitter.thread):
                if len(tweet) > 280:
                    issues.append(EvaluationIssue(
                        field=f"twitter.thread[{i}]",
                        problem=f"Tweet {i+1} exceeds 280 characters ({len(tweet)})",
                        location=f"tweet {i+1}",
                        expected="Maximum 280 characters per tweet",
                    ))
        if formats.email:
            if len(formats.email.subject) > 60:
                issues.append(EvaluationIssue(
                    field="email.subject",
                    problem=f"Subject exceeds 60 characters ({len(formats.email.subject)})",
                    location="email subject",
                    expected="Maximum 60 characters",
                ))

        if issues:
            return Evaluation(result=EvaluationResult.fail, issues=issues, confidence=1.0)

        # Agent judgment for message consistency
        format_text = ""
        if formats.linkedin:
            format_text += f"\nLinkedIn post:\n{formats.linkedin.post[:500]}"
        if formats.twitter:
            format_text += f"\nTwitter thread:\n{chr(10).join(formats.twitter.thread[:3])}"

        if not format_text:
            return Evaluation(result=EvaluationResult.pass_, confidence=1.0)

        prompt = f"""You are the Central Evaluator.

Primary draft core message (first 500 chars):
{draft.primary_draft[:500]}

Channel formats:{format_text}

Check:
1. Does each format preserve the core message without adding or removing claims?
2. Is tone appropriate per channel?

Return ONLY valid JSON:
{{
  "result": "PASS" or "FAIL",
  "confidence": 0.0-1.0,
  "issues": []
}}"""

        return self._call(prompt, settings.model_haiku)

    def evaluate_compliance_judgment(self, brief: Brief, draft: Draft) -> Evaluation:
        brand = self._load_brand_guidelines()
        prompt = f"""You are the Central Evaluator running a compliance judgment pass.

Draft (first 2000 chars):
{draft.primary_draft[:2000]}

Brand guidelines:
{brand[:600]}

Check:
1. Is the tone consistent with GitHub's brand voice (developer-first, direct, no marketing jargon)?
2. Are there any prohibited phrases from the guidelines?
3. Is readability appropriate for the target audience?

Return ONLY valid JSON:
{{
  "result": "PASS" or "FAIL",
  "confidence": 0.0-1.0,
  "issues": [
    {{"field": "tone", "problem": "...", "location": "...", "expected": "..."}}
  ]
}}"""

        return self._call(prompt, settings.model_sonnet)

    # ── Helpers ─────────────────────────────────────────────────────────

    def _call(self, prompt: str, model: str) -> Evaluation:
        try:
            response = _client.messages.create(
                model=model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            parsed = json.loads(raw)
            result_str = parsed.get("result", "EVALUATION_INCONCLUSIVE")
            result_map = {
                "PASS": EvaluationResult.pass_,
                "FAIL": EvaluationResult.fail,
                "EVALUATION_INCONCLUSIVE": EvaluationResult.inconclusive,
            }
            result = result_map.get(result_str, EvaluationResult.inconclusive)
            issues = [EvaluationIssue(**i) for i in parsed.get("issues", [])]
            confidence = float(parsed.get("confidence", 0.8))
            return Evaluation(result=result, issues=issues, confidence=confidence)
        except Exception as e:
            return Evaluation(
                result=EvaluationResult.inconclusive,
                issues=[EvaluationIssue(
                    field="evaluation",
                    problem=f"Evaluator error: {str(e)}",
                    location="N/A",
                    expected="Clean evaluation output",
                )],
                confidence=0.0,
            )

    def _load_brand_guidelines(self) -> str:
        path = settings.data_dir / "brand_guidelines.txt"
        return path.read_text() if path.exists() else ""

    def _load_legal_flags(self) -> list[str]:
        path = settings.data_dir / "legal_flags.txt"
        if not path.exists():
            return []
        flags = []
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                flags.append(line)
        return flags

    def _load_channel_specs(self) -> dict:
        path = settings.data_dir / "channel_specs.json"
        return json.loads(path.read_text()) if path.exists() else {}

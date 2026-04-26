import json
import anthropic
from config import settings
from models.brief import Brief, ContentType
from models.draft import Draft, ChannelFormats, LinkedInFormat, TwitterFormat, EmailFormat

_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)


class FormatterAgent:
    def run(self, brief: Brief, draft: Draft) -> ChannelFormats:
        channel_specs = self._load_channel_specs()
        content_type = brief.content_type
        expected = channel_specs.get("channel_by_content_type", {}).get(content_type.value, [])

        formats = ChannelFormats()
        failures = []

        if "linkedin" in expected:
            result = self._format_linkedin(brief, draft, channel_specs)
            if isinstance(result, str):
                failures.append(f"linkedin: {result}")
            else:
                formats.linkedin = result

        if "twitter" in expected:
            result = self._format_twitter(brief, draft, channel_specs)
            if isinstance(result, str):
                failures.append(f"twitter: {result}")
            else:
                formats.twitter = result

        if "email" in expected:
            result = self._format_email(brief, draft, channel_specs)
            if isinstance(result, str):
                failures.append(f"email: {result}")
            else:
                formats.email = result

        formats.constraint_failures = failures
        return formats

    def _format_linkedin(self, brief: Brief, draft: Draft, specs: dict) -> LinkedInFormat | str:
        spec = specs.get("linkedin", {})
        max_chars = spec.get("max_characters", 3000)

        prompt = f"""You are the Formatter Agent for GitHub's content marketing system.

Adapt this {brief.content_type.value} into a LinkedIn post.

Primary draft (first 1500 chars):
{draft.primary_draft[:1500]}

LinkedIn rules:
- Max {max_chars} characters (STRICT — count carefully)
- Open with the most compelling fact or implication, not a preamble
- Short paragraphs (2-3 lines max)
- One clear call to action at the end
- Maximum 3 relevant hashtags at the end
- Tone: professional but developer-credible, not corporate
- No em-dash lists, no all-caps, no clickbait

Return ONLY the LinkedIn post text, nothing else. Count to ensure it is under {max_chars} chars."""

        response = _client.messages.create(
            model=settings.model_haiku,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        post = response.content[0].text.strip()
        if len(post) > max_chars:
            return f"FORMAT_CONSTRAINT_FAILURE: LinkedIn post is {len(post)} chars, exceeds {max_chars}"
        return LinkedInFormat(post=post, character_count=len(post))

    def _format_twitter(self, brief: Brief, draft: Draft, specs: dict) -> TwitterFormat | str:
        prompt = f"""You are the Formatter Agent for GitHub's content marketing system.

Adapt this content into a Twitter/X thread.

Primary draft (first 1500 chars):
{draft.primary_draft[:1500]}

Thread rules:
- 2-8 tweets total
- Each tweet MUST be under 280 characters (count carefully)
- Tweet 1: standalone hook — must make sense and be shareable without the rest
- Tweets 2 to N: develop the argument in order
- Final tweet: summary or call to action
- Number each tweet: "1/N" format at the start
- Each tweet should be understandable if seen in isolation

Return ONLY a JSON array of tweet strings:
["tweet 1 text", "tweet 2 text", ...]

No other text."""

        response = _client.messages.create(
            model=settings.model_haiku,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        try:
            tweets = json.loads(raw)
        except Exception:
            return "FORMAT_CONSTRAINT_FAILURE: Could not parse Twitter thread JSON"

        oversized = [f"tweet {i+1} ({len(t)} chars)" for i, t in enumerate(tweets) if len(t) > 280]
        if oversized:
            return f"FORMAT_CONSTRAINT_FAILURE: Tweets exceed 280 chars: {', '.join(oversized)}"

        return TwitterFormat(thread=tweets, total_characters=sum(len(t) for t in tweets))

    def _format_email(self, brief: Brief, draft: Draft, specs: dict) -> EmailFormat | str:
        spec = specs.get("email", {})
        max_subject = spec.get("subject_max_characters", 60)

        prompt = f"""You are the Formatter Agent for GitHub's content marketing system.

Adapt this content into an email newsletter section.

Primary draft (first 1000 chars):
{draft.primary_draft[:1000]}

Email rules:
- Subject: max {max_subject} characters, clear value statement, no clickbait
- Body: plain prose, NO markdown formatting (email clients don't render it)
- Short paragraphs, one idea per paragraph
- One call to action

Return ONLY valid JSON:
{{
  "subject": "<subject line under {max_subject} chars>",
  "body": "<plain prose email body>"
}}"""

        response = _client.messages.create(
            model=settings.model_haiku,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        try:
            parsed = json.loads(raw)
        except Exception:
            return "FORMAT_CONSTRAINT_FAILURE: Could not parse email JSON"

        subject = parsed.get("subject", "")
        if len(subject) > max_subject:
            return f"FORMAT_CONSTRAINT_FAILURE: Subject is {len(subject)} chars, exceeds {max_subject}"

        return EmailFormat(subject=subject, body=parsed.get("body", ""))

    def _load_channel_specs(self) -> dict:
        path = settings.data_dir / "channel_specs.json"
        return json.loads(path.read_text()) if path.exists() else {}

# GitHub Enterprise Content Marketing System
## Full Product & Technical Spec
**Version:** 4.0 | **Status:** Final Draft | **Repo:** [Hemanth2423/Content-marketing-system-GitHub](https://github.com/Hemanth2423/Content-marketing-system-GitHub)

---

## Vision

GitHub's content reaches millions of developers worldwide — but producing it is slow, inconsistent, and manually intensive. This system automates the journey from content idea to published post, while keeping humans in control of every decision that matters.

The goal is simple: a developer marketer at GitHub should be able to initiate a content brief, watch AI research and draft the content, move it through an approval chain with real feedback, and publish to the right channel — all from a single dashboard, without switching tools or chasing approvals over email.

This is built to run locally as a demo, but designed with the discipline of an enterprise system. Agents handle the work that doesn't require human judgment. Humans handle the work that does. The boundary between the two is explicit, enforced, and never blurry.

---

## Problem Space

### Who is this for?

GitHub's content marketing team is small relative to the volume and technical depth of content it needs to produce. Content spans developer education, product launches, open source thought leadership, and enterprise sales enablement. Each content type has a different audience, tone, and channel — and each requires a different kind of expertise to produce well.

The four personas using this system are:

**Requester** (typically a PM or marketer) is the person who identifies the need for a piece of content. They know what they want to say and why, but they shouldn't have to do the research, write the draft, or chase the approvals themselves. Their job ends when the brief is submitted and resumes when they need to clarify something during revision.

**Strategist** is the editorial gatekeeper. They review whether the content serves GitHub's current priorities, whether the angle is right, and whether the draft quality is good enough to move forward. They approve or reject with feedback — they don't rewrite.

**Reviewer** is the legal and compliance gate. They only enter the workflow when content triggers a compliance concern — competitor mentions, legal claims, regulated language. Their role is narrow and conditional. When they're not needed, they're not bothered.

**Publisher** owns the final step. They confirm the publish schedule, verify the right content is going to the right channel, and hit confirm. They don't edit content — that window has closed by the time it reaches them.

### What content does this system support?

GitHub prioritizes four content types, each mapped to the channel where it performs best:

- **Technical tutorials** are step-by-step how-to guides aimed at developers learning GitHub features or adjacent tools. These are detailed, code-heavy, and published as blog posts. They are GitHub's highest-volume content type and the primary driver of organic search traffic.

- **Product announcements** cover feature launches and changelog highlights. The audience is existing GitHub users — developers and engineering leads — and the tone is clear and direct. These publish to LinkedIn, where GitHub's enterprise and decision-maker audience is most active.

- **Developer thought leadership** covers GitHub's perspective on trends in AI, open source, DevOps, and the future of software development. These are opinionated, concise, and written for Twitter/X where developer conversation happens in real time.

- **Case studies** tell the story of how enterprise customers use GitHub to ship better software. These are longer, structured narratives aimed at enterprise buyers and published as blog posts alongside technical tutorials.

### What problem does this solve?

Without this system, content production at GitHub involves too many handoffs, too much manual coordination, and too little consistency. A brief gets written in a Google Doc, research happens in separate tabs, drafts go back and forth over Slack, approvals happen over email, and publishing requires manually logging into three platforms. Nothing is tracked. Nothing is auditable. Quality is inconsistent.

This system makes the entire pipeline visible, structured, and partially automated — without removing human judgment from the decisions that require it.

---

## Design Principles

**1. Collect before you reason.**
Research and retrieval always complete before any agent interprets or generates content. Agents receive pre-computed inputs. They never search while writing — those are two different jobs that belong in two different steps.

**2. No agent judges its own output.**
Every agent output passes through the central evaluator before moving forward. The agent that writes the draft does not decide whether the draft is good. The agent that formats a tweet does not decide whether the tweet is on-brand. Evaluation is always independent.

**3. Deterministic gates are non-negotiable.**
Compliance checks, approval logging, and publish triggers run on explicit rules, not agent judgment. These steps must produce the same result every time given the same input. Agents advise and generate — they never trigger irreversible actions.

**4. Every agent has a contract.**
Each agent in this system has a crisp definition of what it does, what it explicitly does not do, what it receives as input, what it returns as output, what tools it can access, and what happens when it fails. There are no vague "helper" agents. If an agent's role can't be described in two sentences, it shouldn't exist.

**5. Start minimal, add agents only when justified.**
The system uses the simplest architecture that produces good output. A single agent with tools before multi-agent. A deterministic function before an agent. Complexity is added only when a distinct capability genuinely requires a distinct role — not because multi-agent sounds more impressive.

**6. Log before you act.**
No action fires before its audit entry exists. If writing the log entry fails, the action does not proceed. The audit trail is not an afterthought — it is a prerequisite.

---

## Enterprise Context

### Scale and volume

This system is designed for a content marketing team of 8–15 people producing 50–100 content pieces per month. At any given time, 10–20 pieces are in-flight across different pipeline stages. During peak periods — major product launches like GitHub Universe, GitHub Copilot feature drops, or annual developer surveys — concurrent in-flight volume may spike to 30 pieces.

Each piece carries an estimated 6–12 hours of human time under the current manual process. The system's goal is to reduce that to 2–3 hours per piece by automating research, drafting, and format adaptation, while preserving the human time that actually requires judgment.

### Stakeholders

- **Content marketers (Requesters):** The primary users. 4–6 people who initiate briefs and monitor pipeline progress. They are the customer of the system.
- **Editorial lead (Strategist):** 1 person. The editorial gatekeeper for every piece. High-trust, high-judgment role. The most frequent approval bottleneck.
- **Legal counsel (Reviewer):** 1–2 people from the legal team who review on a part-time, as-needed basis. They are pulled in only when legal triggers fire. Minimizing their involvement through good compliance guardrails is a design goal.
- **Distribution lead (Publisher):** 1 person. Owns publishing schedules and channel relationships. Final confirmation authority.
- **Engineering / IT (operators):** Maintain the system, manage API credentials, monitor system health. They are not workflow actors.

### Compliance constraints

This system operates under three compliance frameworks:

**FTC endorsement and disclosure rules:** Any content that involves a partnership, sponsorship, or paid relationship must include a clear disclosure. The system's legal_flags.txt includes disclosure keywords. If a brief or draft references a partner without a disclosure marker, it triggers Reviewer review.

**Platform Terms of Service:** LinkedIn and Twitter/X both prohibit specific content categories (spam, misleading claims, prohibited industries). Character limits are enforced deterministically by the rules engine. Content that violates platform ToS is blocked from reaching the Publisher stage.

**GitHub internal brand standards:** Product names must be formatted correctly (GitHub, not Github or GITHUB). Tone guardrails apply across all content types. Prohibited phrases (competitive disparagement, unverified performance claims) are listed in legal_flags.txt and brand_guidelines.txt.

**Copyright requirements:** Third-party quotes and statistics must be attributed. The system's research brief flags any sourced data points for attribution, and the evaluator checks for attribution in the draft before it advances.

### Approval hierarchy

Every content piece moves through approvals in this exact sequence: Requester → Strategist → Reviewer (conditional) → Publisher. There are no parallel approval paths. The Reviewer stage is the only gate that can be skipped, and only when the legal trigger check returns no matches and that result is explicitly logged.

---

## System Architecture

### Pattern: Central Orchestrator + Central Evaluator

The system uses one orchestrator that manages all pipeline state and routes work to specialized agents, and one evaluator that reviews every agent output before it advances. Nothing else can transition pipeline state or approve agent output.

This was chosen over a hierarchical agent tree for three reasons. First, it is simpler to reason about — one place controls state, one place controls quality. Second, it is easier to debug — when something goes wrong, you check the orchestrator log and the evaluator log, not a tree of nested calls. Third, it maps cleanly to the principle that no agent evaluates its own work.

```
┌──────────────────────────────────────────────────────────────┐
│                    CENTRAL ORCHESTRATOR                      │
│  Owns pipeline state. Routes tasks. Enforces transitions.    │
└───────────────────────────┬──────────────────────────────────┘
                            │
           ┌────────────────┼──────────────────┐
           ▼                ▼                  ▼
   [Research Agent]   [Draft Agent]    [Format Agent]
           │                │                  │
           └────────────────┼──────────────────┘
                            ▼
                 ┌─────────────────────┐
                 │   CENTRAL EVALUATOR  │
                 │  Reviews all output  │
                 │  before it advances  │
                 └─────────────────────┘
                            │
               Pass ────────┴──────── Fail → feedback → retry
```

Every agent returns its output to the orchestrator. The orchestrator sends it to the evaluator. The evaluator returns pass or fail. The orchestrator logs the result, then either advances state or routes the output back for revision. Agents never communicate directly with each other, never write pipeline state, and never trigger downstream actions on their own.

### State machine

The orchestrator manages pipeline state as a formal finite state machine. Every transition is logged before it takes effect. No component can jump to a state that isn't reachable from the current state.

```
BRIEF_DRAFT
  → BRIEF_SUBMITTED
  → ENRICHMENT_IN_PROGRESS
  → ENRICHMENT_COMPLETE
  → BRIEF_CONFIRMED
  → RESEARCH_IN_PROGRESS
  → RESEARCH_COMPLETE
     (or → RESEARCH_LOW_CONTEXT → human decision required)
  → DRAFT_IN_PROGRESS
  → DRAFT_UNDER_EVALUATION
  → DRAFT_REVISION_IN_PROGRESS    (max 2 loops before escalation)
  → DRAFT_EVALUATION_PASSED
     (or → DRAFT_ESCALATED → Strategist decides)
  → FORMAT_IN_PROGRESS
  → FORMAT_COMPLETE
  → PENDING_STRATEGIST_REVIEW
  → STRATEGIST_REJECTED → DRAFT_IN_PROGRESS  (with feedback appended)
  → STRATEGIST_APPROVED
  → LEGAL_CHECK_IN_PROGRESS
  → REVIEWER_SKIPPED              (legal triggers: none → logged)
  → PENDING_REVIEWER_REVIEW
  → REVIEWER_REJECTED → DRAFT_IN_PROGRESS  (with feedback appended)
  → REVIEWER_APPROVED
  → COMPLIANCE_RULES_CHECK_IN_PROGRESS
  → COMPLIANCE_RULES_FAILED → STRATEGIST_RESOLVING
  → COMPLIANCE_JUDGMENT_CHECK_IN_PROGRESS
  → COMPLIANCE_PASSED
  → PENDING_PUBLISHER_REVIEW
  → PUBLISHER_CONFIRMED
  → PUBLISH_JOB_LOCKED
  → SCHEDULED
  → PUBLISHING_IN_PROGRESS
  → PUBLISHED
     (or → PUBLISH_FAILED → Publisher retry)
  → STALLED                       (SLA breach with no human action)
  → CANCELLED
```

The compliance check (F-04) runs after Reviewer approval and before Publisher review. The Publisher only ever sees content that has already cleared compliance. This ordering matters: it ensures the Publisher's confirmation is the final human act on a fully verified piece, with no open questions remaining.

### Central storage

Each content piece has a `pipeline_state.json` file. It contains the current state, revision counters, timestamps, actor assignments, and a pointer to the latest version of each artifact. Only the orchestrator writes to this file. All other components read from it.

---

## Agent Profiles

There are four AI agents in this system. Each has a single, clearly defined role. None of them overlap, none of them evaluate their own work, and none of them can trigger the next step in the pipeline themselves — that is always the orchestrator's job.

A brief note on the **Central Orchestrator**: it is not an AI agent. It is deterministic software that manages pipeline state, routes work to agents and automation, enforces state machine transitions, and writes to the audit log. It does not use language models. It is covered in the Control Flow Architecture section. The four agents described here are the AI components that do the generative and evaluative work.

---

### Agent 1: The Researcher

**Core Responsibility:** Find and structure everything the Draft Agent needs to write from, so the Draft Agent never has to search for anything itself. The Researcher is a retrieval and synthesis role — it gathers evidence, organizes it, and identifies gaps. It does not form opinions, write prose, or decide what angle the content should take. Its job is to give the writer the best possible raw material before any writing begins.

**Inputs:**
- The confirmed content brief — defines the topic, content type, audience, goal, and required keywords
- ChromaDB vector index over `company_data/` — a local knowledge base containing past campaigns, product documentation, developer persona profiles, GitHub feature notes, and case study raw material. This is the primary source.
- `past_campaigns.json` — a structured record of previously published content with topics, angles, and brief performance notes. Used to check whether similar content already exists and to calibrate what approaches have worked before.
- Tavily web search API (optional fallback) — used only when the local knowledge base returns fewer than 3 relevant chunks for the brief. External search is not the default; it is the contingency when internal knowledge is insufficient.

**Outputs:**

A structured research brief containing:
- **Sources:** A list of retrieved chunks with file name, excerpt, and relevance score. These are the raw materials the Draft Agent will write from. Every claim in the final draft should be traceable to a source here.
- **Key points:** Bulleted factual claims drawn directly from the retrieved sources. No editorializing. No synthesis beyond grouping related facts. The Draft Agent decides how to argue from these points — the Researcher just surfaces them.
- **Suggested angles:** 2–3 possible framings for the content, derived from what the source material most strongly supports. These are options, not decisions. The Draft Agent chooses how to approach the content; the Researcher maps what's possible given the evidence.
- **Gaps:** Areas the brief mentions where the knowledge base returned little or no useful material. Flagged explicitly so the Draft Agent knows where it's working with thin coverage and should hedge or acknowledge limitations.
- **low_context flag:** Set to `true` if fewer than 3 chunks scored ≥ 0.6 relevance. When this flag is set, the orchestrator pauses the pipeline and prompts the Requester to add more context or explicitly accept that the draft will be produced with limited source material.

```json
{
  "brief_id": "string",
  "sources": [{ "file": "string", "chunk": "string", "relevance_score": 0.0 }],
  "key_points": ["string"],
  "suggested_angles": ["string"],
  "gaps": ["string"],
  "low_context": false,
  "retrieved_chunk_count": 0
}
```

**Tools:**
- ChromaDB (local vector database) — primary retrieval tool
- Tavily API (optional fallback) — used only when local retrieval is insufficient

**Pipeline state transitions (via orchestrator):** RESEARCH_IN_PROGRESS → RESEARCH_COMPLETE or RESEARCH_LOW_CONTEXT

**Explicitly Not Responsible For:**
- Deciding what angle the content should take — it surfaces options based on what the source material supports; the Draft Agent decides
- Writing any prose that will appear in the final content
- Evaluating whether its own research is sufficient — the Central Evaluator makes that call independently
- Running web searches as a first resort — the local knowledge base is always searched first; external search is only used as a fallback
- Judging whether sourced facts are still accurate or current — it retrieves what's in the knowledge base; content owners are responsible for keeping that base up to date

**Typical Failure Modes:**
- Returning high relevance scores for chunks that are technically adjacent but not actually useful for the specific brief — appearing thorough while missing the point. A chunk about GitHub Actions might score well for a Copilot brief because both involve automation, but the content isn't relevant.
- Not flagging `low_context` when it should — retrieving 3 marginally relevant chunks and reporting clean context when the Draft Agent will actually be writing with thin coverage. This sets the Draft Agent up to produce confident-sounding content with weak support.
- Surfacing outdated information from old campaigns as if it were current — there is no date filtering by default, so a 2021 blog post about a deprecated feature can score highly against a 2025 brief.
- Missing key angles because they exist in formats the vector index doesn't represent well — PDFs, code-heavy documentation, or embedded tables may not chunk cleanly.
- During the brief enrichment pass (F-01), suggesting keywords that are either too broad ("developer tools") or too narrow ("GitHub Actions YAML workflow_dispatch syntax") to be strategically useful.

---

### Agent 2: The Writer

**Core Responsibility:** Take the research brief and the content brief and write the complete primary content piece. The Writer makes all narrative decisions — structure, framing, argument construction, example selection, tone — within the constraints set by the brief. This is the most creatively demanding role in the pipeline.

**Inputs:**
- The confirmed content brief (via the Orchestrator) — defines type, audience, goal, required keywords, and publish date. This is the contract the Writer works within.
- The evaluator-approved research brief — provides the factual foundation. The Writer writes from this material. It should not introduce claims, statistics, or context that don't appear in the research brief or the reference documents below.
- `brand_guidelines.txt` — GitHub's tone standards (developer-first, technically credible, direct, no marketing jargon), vocabulary preferences, and content-type-specific writing patterns. The Writer reads this on every run — it is not cached in the agent's context.
- `past_campaigns.json` — examples of previously published pieces for tone and structure calibration. The Writer reads these to understand what "on-brand" looks and feels like in practice, not just in abstract rules.

**Outputs:**

A complete draft including:
- Headline (and optional subheadline for longer pieces)
- Full body content in markdown with proper heading hierarchy (H1 for title, H2 for major sections, H3 for subsections)
- **For technical tutorials:** hook that establishes the problem → prerequisites (what the reader needs before starting) → numbered step-by-step body where each step includes the command or code block, an explanation of what it does and why, and the expected output → verification step (how to confirm it worked) → next steps or related resources. Code examples include inline comments.
- **For product announcements:** what changed → why it matters for the developer → a concrete use case or example showing it in action → call to action. Direct, no padding, no throat-clearing.
- **For developer thought leadership:** a specific, opinionated opening statement (not "many developers wonder...") → the problem or trend being addressed → evidence and GitHub's position on it → implications for how developers should think or act → a forward-looking close that commits to a view, not a hedge.
- **For case studies:** customer context (company, scale, engineering setup) → the specific challenge they faced → what they built with GitHub and how → measurable outcome → why this matters to other enterprises in similar situations.
- Metadata block appended to the output: target keywords used and where, word count, heading structure list, content type, target audience level.

When the evaluator returns FAIL with structured critique, the Writer receives the original brief plus the evaluator's critique explicitly appended as instruction — not as background context. It produces a fresh draft that addresses the critique from the beginning, not a patched version of the previous draft. Patching is the failure mode; this constraint prevents it.

```json
{
  "brief_id": "string",
  "revision": 0,
  "content_type": "string",
  "primary_draft": "string",
  "word_count": 0,
  "metadata": {
    "tone": "string",
    "target_audience": "string",
    "keywords_used": ["string"]
  }
}
```

**Tools:**
- Read access to `brand_guidelines.txt`
- Read access to `past_campaigns.json`

**Pipeline state transitions (via orchestrator):** DRAFT_IN_PROGRESS → DRAFT_UNDER_EVALUATION. On revision: DRAFT_REVISION_IN_PROGRESS → DRAFT_UNDER_EVALUATION. After two failed revisions: DRAFT_ESCALATED (Strategist intervenes).

**Explicitly Not Responsible For:**
- Researching its own inputs — it writes from the research brief it receives; it does not run searches
- Adapting the draft for secondary channels — that is the Format Agent's job; the Writer produces the primary piece only
- Evaluating whether its own output meets the rubric — it produces a draft and hands it to the orchestrator
- Deciding which content angle to use — the brief defines the goal, the research brief provides suggested angles; the Writer works within those
- Verifying that code examples execute correctly in a live environment — the evaluator checks for structural correctness and inline comment quality; actual execution testing is out of scope for this system

**Typical Failure Modes:**
- Technically plausible but factually wrong content, especially in tutorials — the Writer may produce a code example that looks right but doesn't work, particularly for newer GitHub features underrepresented in training data. Code examples should always come from the research brief's sources, not from the model's general knowledge.
- Drifting from the brief's stated audience level — writing at a senior engineer level when the brief specifies "developers new to GitHub Actions," or oversimplifying for an enterprise buyer audience.
- Tone mismatch — reverting to marketing-heavy or overly formal language instead of GitHub's developer-credible voice. This is especially common in product announcement content where the instinct is to "sell" rather than "show."
- Padding to reach word count — producing thin coverage of the brief's key points and filling space with loosely related background. Thinner, tighter content usually performs better than padded content.
- For thought leadership: stating a provocative thesis and then failing to defend it — hedging every claim, ending with "it depends," or listing considerations rather than taking a position.
- On revision: patching the specific sentences the evaluator flagged rather than reconsidering the structure underneath them. If the evaluator says "the argument doesn't hold together in section 2," fixing section 2's word choices while leaving the structure intact is not a meaningful revision.

---

### Agent 3: The Formatter

**Core Responsibility:** Take the approved primary draft and adapt it into the channel-specific formats required by the content type. The Formatter shortens, restructures, and reformats — it does not add claims, change meaning, or make editorial decisions about what the content says. Its job is faithful adaptation under constraints, not creative reinterpretation.

**Inputs:**
- The evaluator-approved primary draft — the source of truth for all content claims. Every statement in the formatted versions must trace back to this draft.
- `channel_specs.json` — per-channel rules including character limits, structural conventions, tone variations by channel, and prohibited formats. The Formatter reads this on every run.

Channel mapping by content type (what formats are produced):
- Technical tutorials → Blog post only. No secondary format is required or produced.
- Product announcements → LinkedIn post (the primary social channel for GitHub's enterprise and decision-maker audience).
- Developer thought leadership → Twitter/X thread (where developer conversation happens in real time).
- Case studies → Blog post only. No secondary format is required or produced.

**Outputs:**

Per applicable channel:
- **LinkedIn post:** A single post (max 3,000 characters) that captures the core announcement or argument, opens with the most compelling fact or implication rather than a preamble, uses short paragraphs optimized for mobile reading, adds one clear call to action at the end, and uses at most 3 relevant hashtags. No em-dash lists (LinkedIn renders them poorly on mobile). Tone is professional but not corporate.
- **Twitter/X thread:** A thread of 2–8 tweets. Tweet 1 is the hook — max 280 characters, must make sense and be shareable on its own without the rest of the thread. Tweets 2 through N develop the argument, evidence, or steps in logical order. Each tweet is self-contained enough to be understood by someone who sees a retweet of it in isolation. Final tweet is a summary or call to action. Each tweet is numbered (1/N format).
- **Email newsletter section:** Subject line (max 60 characters, no clickbait, clear value statement), preview text (max 90 characters, expands on subject rather than repeating it), body in plain prose — no markdown formatting because most email clients don't render it, short paragraphs, one link per section.
- **constraint_failures:** A list of channels where the core message could not be adapted within format constraints without distorting its meaning. Each entry includes the channel name and a plain-language explanation of why faithful adaptation wasn't possible (e.g., "The benchmark claim requires context that cannot be preserved in 280 characters without misrepresentation").

```json
{
  "brief_id": "string",
  "primary_draft_id": "string",
  "formats": {
    "linkedin": { "post": "string", "character_count": 0 },
    "twitter": { "thread": ["string"], "total_characters": 0 },
    "email": { "subject": "string", "body": "string" }
  },
  "constraint_failures": []
}
```

**Tools:**
- Read access to `channel_specs.json`

**Pipeline state transitions (via orchestrator):** FORMAT_IN_PROGRESS → FORMAT_COMPLETE or FORMAT_CONSTRAINT_FAILURE

**Explicitly Not Responsible For:**
- Changing the core claim or argument — if the primary draft says "GitHub Copilot reduced review time by 35% in internal testing," the LinkedIn post cannot soften this to "Copilot can help reduce review time" to save characters. The claim must be preserved accurately or flagged as a constraint failure.
- Adding new claims, statistics, or context not in the primary draft — the Formatter cannot introduce information that wasn't in its input
- Evaluating brand or compliance alignment — the Central Evaluator handles this after formatting is complete
- Producing formats for content types that don't require them — tutorials and case studies go to blog only; the Formatter does not produce a LinkedIn post for these even if prompted
- Deciding whether to skip a channel when constraints can't be met — that decision goes to the Strategist via the orchestrator

**Typical Failure Modes:**
- Truncating a qualified claim to fit a character limit in a way that removes the qualification — "35% faster in controlled testing" becomes "35% faster," which is no longer accurate and is a potential legal flag.
- Twitter/X threads where individual tweets require the previous tweets for context — if tweet 4 only makes sense after reading tweets 1–3, anyone who sees a retweet of tweet 4 gets a misleading fragment.
- LinkedIn posts that drift toward either too casual (sounds like a tweet) or too corporate (sounds like a press release) — LinkedIn has a narrower acceptable tonal range than either of those, and the Formatter is prone to overshooting in both directions.
- Email subject lines that are either too cryptic (saves characters but loses the reader before they open it) or too explicit (gets cut off in inbox preview, leaving the sentence incomplete).
- Returning FORMAT_CONSTRAINT_FAILURE when a genuinely faithful adaptation was possible with better restructuring — the failure mode of giving up on adaptation rather than working through it.

---

### Agent 4: The Evaluator

**Core Responsibility:** Review every agent output against the rubric for that output type and return a clear, structured verdict before anything advances. The Evaluator is the independent quality gate on all agent work. It never produces content. It never approves publication. It gives the orchestrator the specific information it needs to decide what happens next — and its critique gives the producing agent exactly what it needs to improve.

The Evaluator is the only agent in the system that sees the output of other agents and judges it. This separation is non-negotiable: the agent that produces a draft cannot assess whether its draft is good enough. The Evaluator exists precisely to enforce that boundary.

**Inputs:**
- The agent output being evaluated (research brief, primary draft, or channel formats)
- The rubric for that output type:
  - **Research rubric:** Are the retrieved sources relevant to the brief's goal and content type? Does the research cover the brief's key required angles, or are there gaps? Are the key points accurately drawn from the sources (no hallucinated claims)? Are gaps appropriately flagged rather than papered over?
  - **Draft rubric:** Does the draft address the brief's stated goal? Is the tone appropriate for the stated audience? Are the brief's required keywords present and naturally incorporated? Is the structure appropriate for the content type? Is attribution present for sourced data points? Are there any matches against `legal_flags.txt`? Does the argument hold together, or does it make a claim it doesn't support?
  - **Format rubric:** Is each channel format within its character or length constraints? Does each format preserve the core claims from the primary draft without adding or removing information? Are structural conventions followed (thread numbering, subject line length, paragraph length)? Does the tone match what's appropriate for each channel?
- `brand_guidelines.txt` — tone rules and vocabulary standards used to evaluate draft and format alignment
- `legal_flags.txt` — keyword and phrase list for legal triggers. The Evaluator flags any match in the draft, regardless of the context in which it appears. The Reviewer makes the final judgment; the Evaluator's job is to ensure the flag is surfaced.
- `channel_specs.json` — per-channel constraints used to verify format compliance

**Outputs:**

- **PASS** — the output meets the rubric. The orchestrator advances pipeline state. No further information is required.
- **FAIL** — the output does not meet the rubric. Includes a structured list of issues, each specifying: which field or section failed, what the specific problem is, where in the output it appears, and what a passing version would look like — described in terms of what it achieves, not the specific words to use. The producing agent receives this critique and revises.
- **EVALUATION_INCONCLUSIVE** — the Evaluator cannot produce a confident verdict (confidence below 0.6). This occurs when the output is genuinely ambiguous, the input is malformed, or the rubric criteria are difficult to apply to this specific piece. The orchestrator routes to the Strategist rather than defaulting to pass or fail. INCONCLUSIVE is never treated as an implicit pass.

For draft evaluation, the Evaluator uses `claude-haiku-4-5` for deterministic rubric checks (keyword presence, character counts, structural requirements) and escalates to `claude-sonnet-4-6` for judgment-based critique (tone coherence, argument quality, audience fit). This keeps evaluation costs low for clear-cut cases and reserves the stronger model for nuanced assessment.

```json
{
  "brief_id": "string",
  "evaluation_target": "research | draft | format",
  "revision_number": 0,
  "result": "PASS | FAIL | EVALUATION_INCONCLUSIVE",
  "issues": [
    {
      "field": "string",
      "problem": "string",
      "location": "string",
      "expected": "string"
    }
  ],
  "confidence": 0.0
}
```

**Tools:**
- Read access to `brand_guidelines.txt`
- Read access to `legal_flags.txt`
- Read access to `channel_specs.json`

**Pipeline state transitions (via orchestrator):** DRAFT_UNDER_EVALUATION → DRAFT_EVALUATION_PASSED or DRAFT_REVISION_IN_PROGRESS (up to 2 loops) or DRAFT_ESCALATED (after 2 failed loops).

**Explicitly Not Responsible For:**
- Rewriting or suggesting specific fixes — it identifies problems and describes what a passing version would achieve; producing the solution is the responsible agent's job
- Making publication decisions — PASS means "meets the rubric," not "should be published." Human approvers make that call.
- Running the legal trigger check at Step 3.3 — that is a separate deterministic function. The Evaluator's `legal_flags.txt` check during draft evaluation is an independent safety layer, not the authoritative trigger gate.
- Assessing whether the content strategy or brief is correct — the Evaluator checks the draft against the brief as given. If the brief itself is wrong, that's a problem for the Strategist to catch at approval, not the Evaluator.
- Evaluating its own outputs or prior evaluations

**Typical Failure Modes:**
- Returning EVALUATION_INCONCLUSIVE when a confident verdict was actually reachable — this forces unnecessary human intervention and slows the pipeline. It tends to happen when the Haiku model encounters a borderline case that should have been escalated to Sonnet.
- Applying the wrong rubric to the content type — evaluating a thought leadership piece with tutorial structural requirements and flagging the absence of "numbered steps" or "prerequisites." The evaluation target and content type must be matched correctly on every call.
- Rubric drift across revision loops — being progressively more lenient on the second evaluation than the first, effectively creating an implicit preference for passing revised work even when it doesn't actually meet the standard. The rubric does not change between revisions.
- `legal_flags.txt` false positives — flagging a word that appears on the list but is used in a clearly incidental context (e.g., the word "benchmark" in a sentence about developer productivity metrics rather than a competitive claim). The Evaluator should flag any match but should note in its output whether the match appears incidental, so the Reviewer has context when they review.
- Missing structural failures in formatted content — approving a Twitter thread where the tweets only make sense in sequence but won't survive out-of-context sharing, because the character count check passed and the sequence wasn't evaluated holistically.

---

## Model Routing

Task complexity determines model selection. Haiku handles structured, low-ambiguity work. Sonnet handles tasks that require reasoning, synthesis, or nuanced judgment.

| Task | Model |
|------|-------|
| Research summarization and structuring | claude-haiku-4-5 |
| Draft generation (blog, announcement, thought leadership, case study) | claude-sonnet-4-6 |
| Format adaptation (LinkedIn, Twitter/X, email) | claude-haiku-4-5 |
| Evaluation: deterministic rubric checks | claude-haiku-4-5 |
| Evaluation: judgment-based critique | claude-sonnet-4-6 |

---

## Full Process Map

Every step is specified completely. No step is implicit. Steps are organized into phases that map to the pipeline features below.

Each step specifies: **Actor** · **Input** · **Output** · **Verification** · **Approval** · **Logging**

---

### Phase 1 — Content Initiation

**Step 1.1 — Requester fills brief form**
- Actor: Human (Requester)
- Input: Structured form fields: title, content type, target audience, goal, requested publish date, keywords (optional)
- Output: Raw brief payload submitted to API
- Verification: Client-side presence checks on required fields before submission
- Approval: None
- Logging: `BRIEF_FORM_SUBMITTED` with raw payload and Requester ID

**Step 1.2 — Field validation**
- Actor: Deterministic automation (orchestrator validation layer)
- Input: Raw brief payload
- Output: Validated brief or structured error response listing each invalid field
- Verification: Schema check — all required fields present, content type is one of four valid enums, publish date is a future datetime, title length between 10 and 200 characters
- Approval: None
- Logging: `BRIEF_VALIDATED` or `BRIEF_VALIDATION_FAILED` with field-level errors

**Step 1.3 — Duplicate detection**
- Actor: Deterministic automation
- Input: Validated brief + index of existing briefs in `briefs/`
- Output: `DUPLICATE_CLEAR` or `DUPLICATE_DETECTED` with matching brief ID and title
- Verification: Exact match on title + content type. If detected, pipeline halts and returns error to Requester with the matching brief ID.
- Approval: None
- Logging: `DUPLICATE_CHECK_COMPLETE` with result and matched ID if applicable

**Step 1.4 — Brief enrichment**
- Actor: Research Agent (lightweight pass)
- Input: Validated brief + `company_data/` + `past_campaigns.json`
- Output: Enriched fields: suggested keywords (up to 5), audience framing, recommended content angle, similar past content IDs if any
- Verification: Central Evaluator reviews enrichment quality before it is shown to Requester
- Approval: None
- Logging: `BRIEF_ENRICHMENT_STARTED`, `BRIEF_ENRICHMENT_COMPLETE`

**Step 1.5 — Evaluator reviews enrichment**
- Actor: Central Evaluator
- Input: Enriched brief fields + validated original brief
- Output: PASS (enrichment shown to Requester) or FAIL (enrichment discarded, Requester sees original fields only)
- Verification: Enriched keywords must be relevant to the brief goal and content type; angle must not contradict stated audience
- Approval: None
- Logging: `ENRICHMENT_EVALUATED_PASS` or `ENRICHMENT_EVALUATED_FAIL` with reason

**Step 1.6 — Requester reviews and confirms brief**
- Actor: Human (Requester)
- Input: Original brief fields + AI-enriched suggestions (clearly marked as AI-suggested, fully editable)
- Output: Confirmed brief — Requester edits any fields and clicks Confirm
- Verification: Requester must explicitly click Confirm; the button is not auto-triggered. Any field edited by the Requester overwrites the AI suggestion and the final value is what was confirmed.
- Approval: Requester confirmation (named actor, timestamp logged)
- Logging: `BRIEF_CONFIRMED` with final field values and Requester ID. State → BRIEF_CONFIRMED.

---

### Phase 2 — Research & Drafting

**Step 2.1 — Research Agent runs vector search**
- Actor: Research Agent
- Input: Confirmed brief
- Output: Research brief — top retrieved chunks with relevance scores, structured key points, suggested angles, identified gaps, `low_context` flag
- Verification: Minimum 3 relevant chunks (relevance score ≥ 0.6) required to proceed without `low_context` flag. If fewer than 3, flag is set and orchestrator pauses for human decision.
- Approval: None (human decision only triggered on LOW_CONTEXT)
- Logging: `RESEARCH_STARTED`, `RESEARCH_COMPLETE` or `RESEARCH_LOW_CONTEXT` with chunk count and top scores

**Step 2.2 — Evaluator reviews research**
- Actor: Central Evaluator
- Input: Research brief + confirmed brief
- Output: PASS or FAIL with specific issues (irrelevant sources, missing key angles, incomplete coverage)
- Verification: Sources must be relevant to the brief goal and content type; key points must not contradict the brief's stated audience or goal
- Approval: None
- Logging: `RESEARCH_EVALUATED_PASS` or `RESEARCH_EVALUATED_FAIL` with issues list

**Step 2.3 — Draft Agent writes primary draft**
- Actor: Draft Agent
- Input: Research brief (evaluator-approved) + confirmed brief + `brand_guidelines.txt` + `past_campaigns.json`
- Output: Primary draft with metadata (word count, tone, keywords used)
- Verification: None at this step — evaluation happens in Step 2.4
- Approval: None
- Logging: `DRAFT_STARTED` with revision number, `DRAFT_COMPLETE` with word count

**Step 2.4 — Evaluator reviews draft**
- Actor: Central Evaluator (Haiku for rubric checks, Sonnet for judgment critique)
- Input: Primary draft + confirmed brief + `brand_guidelines.txt` + `legal_flags.txt`
- Output: PASS, FAIL with structured critique (issue, location, expected), or EVALUATION_INCONCLUSIVE
- Verification rubric: Does the draft match the stated goal? Is the tone appropriate for the target audience? Are the brief's required keywords present? Does anything trigger legal_flags.txt? Is attribution present for sourced data?
- Approval: None
- Logging: `DRAFT_EVALUATED_PASS`, `DRAFT_EVALUATED_FAIL` with structured critique, or `DRAFT_EVALUATED_INCONCLUSIVE`

**Step 2.5 — Draft revision (conditional, max 2 loops)**
- Actor: Draft Agent
- Input: Rejected draft + evaluator's structured critique, explicitly appended to the prompt. The agent is told exactly what failed and where — it does not re-infer from the original output.
- Output: Revised draft (incremented revision number)
- Verification: Returns to Step 2.4 for re-evaluation
- Approval: None
- Logging: `DRAFT_REVISION_STARTED` with revision number and critique summary, `DRAFT_REVISION_COMPLETE`

**Step 2.6 — Draft escalation (conditional, after 2 failed loops)**
- Actor: Deterministic automation (orchestrator) → then Human (Strategist)
- Input: Two consecutive DRAFT_EVALUATED_FAIL results for the same brief
- Output: DRAFT_ESCALATED alert sent to Strategist with both sets of evaluator critique
- Verification: Orchestrator confirms exactly 2 revision loop entries in audit log before escalating
- Approval: Strategist must decide: (a) inject explicit guidance for a third attempt, (b) assign to human writer, or (c) cancel
- Logging: `DRAFT_ESCALATED` with revision history and evaluator critique for both attempts

**Step 2.7 — Format Agent adapts content**
- Actor: Format Agent
- Input: Evaluator-approved primary draft + channel specifications from `channel_specs.json`
- Output: Channel-specific formats (LinkedIn post, Twitter/X thread, or email newsletter depending on content type)
- Verification: Character limits, structural requirements per channel (thread structure for Twitter/X, subject line for email)
- Approval: None
- Logging: `FORMAT_STARTED`, `FORMAT_COMPLETE`, or `FORMAT_CONSTRAINT_FAILURE` with explanation

**Step 2.8 — Evaluator reviews format**
- Actor: Central Evaluator
- Input: Formatted content + primary draft + channel specs
- Output: PASS or FAIL (character limit breach, message inconsistency with primary, tone mismatch)
- Verification: Does each formatted piece stay within channel constraints? Does it preserve the core message from the primary draft without adding or removing claims?
- Approval: None
- Logging: `FORMAT_EVALUATED_PASS` or `FORMAT_EVALUATED_FAIL` with specific issues

---

### Phase 3 — Approval Workflow

**Step 3.1 — Strategist review**
- Actor: Human (Strategist)
- Input: Primary draft + channel-adapted formats + research brief + confirmed brief. All visible in a side-by-side panel.
- Output: STRATEGIST_APPROVED or STRATEGIST_REJECTED with plain-text feedback
- Verification: Strategist must explicitly select Approve or Reject — no auto-advance. If Reject, a feedback input is required before submission can proceed. Feedback must be at least 20 characters.
- Approval: Named Strategist required. This stage cannot be skipped under any condition.
- Logging: `STRATEGIST_REVIEW_STARTED` with SLA deadline, `STRATEGIST_APPROVED` or `STRATEGIST_REJECTED` with feedback text verbatim, actor ID, and timestamp

**Step 3.2 — Revision with Strategist feedback (conditional)**
- Actor: Draft Agent (→ returns to Step 2.4 for evaluation)
- Input: Rejected draft + Strategist feedback text explicitly appended as instruction, not as context
- Output: Revised draft
- Verification: Revised draft is re-evaluated by the Central Evaluator (Step 2.4) before returning to Strategist
- Approval: None for the revision itself — Strategist re-reviews in Step 3.1 after evaluation passes
- Logging: `STRATEGIST_REVISION_REQUESTED` with feedback text, `REVISION_SUBMITTED`

**Step 3.3 — Legal trigger check**
- Actor: Deterministic automation (rules engine)
- Input: Strategist-approved draft + `legal_flags.txt`
- Output: TRIGGER or NO_TRIGGER with a list of matched phrases and their locations in the draft
- Verification: Exact keyword and phrase match against legal_flags.txt. This is a deterministic function — same input produces same output, always. No agent judgment.
- Approval: None
- Logging: `LEGAL_TRIGGER_CHECK_COMPLETE` with result, matched terms and locations, or NO_TRIGGER confirmation

**Step 3.4a — Reviewer review (conditional, only if TRIGGER)**
- Actor: Human (Reviewer)
- Input: Draft with triggered phrases highlighted + trigger list + legal_flags.txt context
- Output: REVIEWER_APPROVED or REVIEWER_REJECTED with compliance-specific feedback
- Verification: Reviewer must interact — approve or reject. If reject, feedback input is required. Reviewer's scope is limited to legal and compliance concerns only; content quality is not in scope at this stage.
- Approval: Named Reviewer required. Cannot be substituted by Strategist.
- Logging: `REVIEWER_REVIEW_STARTED` with SLA deadline, `REVIEWER_APPROVED` or `REVIEWER_REJECTED` with feedback verbatim, actor ID, timestamp

**Step 3.4b — Reviewer stage skipped (conditional, only if NO_TRIGGER)**
- Actor: Deterministic automation (orchestrator)
- Input: NO_TRIGGER result from Step 3.3
- Output: State → REVIEWER_SKIPPED
- Verification: NO_TRIGGER must be explicitly logged before skip can be recorded. An absence of a trigger check is not the same as a passed trigger check.
- Approval: None (skip is automatic, not a human decision)
- Logging: `REVIEWER_STAGE_SKIPPED` with reason ("no legal triggers detected") and pointer to the trigger check log entry. This event must exist in the audit log — skipped stages are never simply absent.

---

### Phase 4 — Brand & Compliance Guardrails

**Step 4.1 — Rules engine check**
- Actor: Deterministic automation (rules engine)
- Input: All approved content (primary draft + channel formats) + `brand_guidelines.txt` + `legal_flags.txt` + `channel_specs.json`
- Output: PASS or structured violation list — each violation includes the specific text that triggered it, the rule it violated, the location in the content, and a suggested deterministic fix
- Verification: Checks run in this order: product name formatting, prohibited phrases, character limits per channel, FTC disclosure markers if partner content, copyright attribution markers for sourced data
- Approval: None at this step — Strategist reviews violations in Step 4.3
- Logging: `COMPLIANCE_RULES_CHECK_STARTED`, `COMPLIANCE_RULES_PASSED` or `COMPLIANCE_RULES_FAILED` with full violation list

**Step 4.2 — Evaluator judgment pass (only if Step 4.1 passes)**
- Actor: Central Evaluator (Sonnet for judgment critique)
- Input: Approved content + `brand_guidelines.txt` + `channel_specs.json`
- Output: PASS or flagged issues (tone inconsistency, cross-channel message drift, readability concerns)
- Verification: Does the primary draft tone match the brand guidelines for the content type? Does the Twitter/X thread convey the same message as the blog post, just shorter? Is the LinkedIn post appropriate for an enterprise audience?
- Approval: None
- Logging: `COMPLIANCE_JUDGMENT_CHECK_STARTED`, `COMPLIANCE_JUDGMENT_PASSED` or `COMPLIANCE_JUDGMENT_FAILED` with issues

**Step 4.3 — Strategist resolves violations (conditional, only if Step 4.1 or 4.2 fails)**
- Actor: Human (Strategist)
- Input: Violation list with highlighted text, rule reference, and suggested fix for each item
- Output: Per violation: Auto-fix applied (deterministic violations only), manual edit (Strategist types the correction), or escalation to Reviewer (if a legal concern slipped through)
- Verification: All violations must be resolved before state can advance to COMPLIANCE_PASSED. "Resolved" means one of the three above outcomes is logged for each violation.
- Approval: Strategist confirmation required for each non-auto-fix. Auto-fixes are applied without interaction but logged.
- Logging: `COMPLIANCE_VIOLATION_RESOLVED` per violation with resolution type and actor ID, `COMPLIANCE_CLEARED` when all violations are resolved, state → COMPLIANCE_PASSED

---

### Phase 5 — Publishing & Distribution

**Step 5.1 — Publisher reviews final content**
- Actor: Human (Publisher)
- Input: Compliance-cleared final content across all channels in a preview panel + approval log summary (who approved, when) + scheduled publish date
- Output: PUBLISHER_CONFIRMED with scheduled datetime, or feedback sent back to Strategist
- Verification: Publisher must see all channel previews before Confirm is enabled. The Confirm button is disabled unless state = COMPLIANCE_PASSED and all prior approvals are logged.
- Approval: Named Publisher required. This is the final human gate. No further edits are possible after this confirmation.
- Logging: `PUBLISHER_REVIEW_STARTED` with SLA deadline, `PUBLISHER_CONFIRMED` with scheduled datetime and Publisher ID

**Step 5.2 — Publish job locked**
- Actor: Deterministic automation (orchestrator)
- Input: Publisher confirmation + prerequisite check against audit log
- Output: Locked publish job registered with APScheduler
- Verification: All five conditions must be true before the job is registered:
  1. `STRATEGIST_APPROVED` is in the audit log
  2. `REVIEWER_APPROVED` or `REVIEWER_STAGE_SKIPPED` (with reason) is in the audit log
  3. `COMPLIANCE_PASSED` is in the audit log
  4. `PUBLISHER_CONFIRMED` is in the audit log
  5. Scheduled datetime is in the future
  If any condition is false, the job is not created and an alert fires.
- Approval: None (all approvals already captured in prior steps)
- Logging: `PUBLISH_JOB_LOCKED` with channel list, scheduled datetime, and confirmation that all five conditions were met

**Step 5.3 — Scheduled trigger fires**
- Actor: APScheduler (automation)
- Input: Locked publish job at the scheduled datetime
- Output: Publish sequence initiated per channel
- Verification: Scheduled datetime has passed, job is not cancelled, job is in LOCKED state (not already PUBLISHED or CANCELLED)
- Approval: None
- Logging: `PUBLISH_TRIGGER_FIRED` with job ID and actual fire time

**Step 5.4 — Content published per channel**
- Actor: Deterministic automation (per-channel publish function)
- Input: Final content per channel from the locked publish job
- Output: Per channel: success with API response ID, or failure with error message
- Verification: API response confirms the post was created. No assumed success.
- Approval: None
- Logging: `CHANNEL_PUBLISH_SUCCESS` with platform, post ID, and API response timestamp; or `CHANNEL_PUBLISH_FAILED` with platform, error message, and error code. On failure: alert fired, Publisher notified, retry option shown. No auto-retry.

---

### Phase 6 — Audit Logging (Cross-Cutting)

Every step above calls `log_event()`. This is not optional — it is a prerequisite for state transitions. No component writes to the audit log directly. Only the logging module can.

Each log entry is append-only and structured as:
```json
{
  "entry_id": "uuid",
  "event_type": "string",
  "content_id": "string",
  "actor": "system | requester | strategist | reviewer | publisher",
  "actor_id": "string | null",
  "timestamp": "ISO 8601",
  "payload": {},
  "prev_entry_hash": "sha256",
  "entry_hash": "sha256(payload + prev_entry_hash)"
}
```

The hash chain makes tampering detectable on export. Any entry modified after writing breaks the chain from that point forward. The chain is verified whenever the log is exported.

---

### Phase 7 — Alert Engine (Cross-Cutting)

The alert engine runs as a background monitor alongside the pipeline. It is fully deterministic — thresholds are fixed rules, not agent assessments.

**Alert types:**

An SLA warning fires when a stage has been idle for 50% of its allowed window with no human action. Severity: YELLOW. Shows on dashboard alert panel.

An SLA urgent fires when the same stage reaches 80% of its window with no action. Severity: RED. Dashboard + Mailgun email to the assigned actor.

An SLA breach fires at 100% of the window. State → STALLED. All stakeholders notified. Pipeline paused until manually resumed.

A publish window alert fires when scheduled publish is within 2 hours and not all stages are complete. Severity: RED, immediate. All actors notified.

A compliance failure alert fires when the rules engine or evaluator fails at Phase 4. Content is blocked from advancing to Publisher.

An agent failure alert fires on DRAFT_ESCALATED, RESEARCH_LOW_CONTEXT, or FORMAT_CONSTRAINT_FAILURE. Strategist is notified with a clear explanation and the relevant artifacts.

A publish failure alert fires when a channel API call fails at Step 5.4. Publisher is notified with error details and a retry button.

**Alert record:**
```json
{
  "alert_id": "uuid",
  "content_id": "string",
  "type": "SLA_WARNING | SLA_URGENT | SLA_BREACH | PUBLISH_WINDOW | COMPLIANCE_FAILURE | AGENT_FAILURE | PUBLISH_FAILURE",
  "severity": "YELLOW | RED",
  "triggered_at": "ISO 8601",
  "response_deadline": "ISO 8601",
  "assigned_to": "string",
  "dismissed_at": "ISO 8601 | null",
  "escalation_level": 0
}
```

---

## Agent vs Automation Boundaries

For each step in the process map, this section classifies whether the work is done by an agent, deterministic automation, or a human — and explains why that assignment is correct.

### Classification framework

**Agent-driven** means the step requires language understanding, synthesis, creative generation, or judgment that cannot be expressed as a rule. The key question is: "Can this step produce correct output from a lookup table or a rule?" If no, it's an agent step.

**Deterministic automation** means the step always produces the same output from the same input. It runs on explicit rules, schema checks, regex matches, or API calls. There is no ambiguity. The key question is: "Would a senior engineer be comfortable replacing this with a simple function?" If yes, it should be automation.

**Human-only** means the step requires named accountability, legal authority, or irreversible action. The key question is: "Does this decision require a person to own it?" If yes, it stays human.

---

### Step-by-step classifications

**Step 1.1 (Requester fills brief):** Human-only. Content intent originates with a person. No automation can decide what content GitHub should produce.

**Step 1.2 (Field validation):** Deterministic automation. Schema checks are rules. If an agent handled this, it might interpret an invalid date charitably instead of flagging it — introducing silent errors at intake. If humans reviewed field validation, they'd be doing the work of a form.

**Step 1.3 (Duplicate detection):** Deterministic automation. Exact match on title + content type. An agent might rate two similar-but-not-identical briefs as duplicates based on semantic proximity — a false positive that kills valid content. This must be a rule, not a judgment.

**Step 1.4 (Brief enrichment):** Agent-driven. Suggesting relevant keywords, audience framing, and content angles requires understanding the content goal and existing knowledge base — not rule matching. A deterministic function cannot suggest "angle: position this as a developer productivity story rather than a feature announcement."

**Step 1.5 (Evaluator reviews enrichment):** Agent-driven. Assessing whether a suggested keyword is genuinely relevant to the brief's goal requires reading both — not a rule match. However, if the evaluator returned INCONCLUSIVE, a human skip (showing original fields only) is the safer fallback than auto-approving.

**Step 1.6 (Requester confirms brief):** Human-only. The brief is a contract. The person who initiates content must own the terms of that contract. No automation can substitute for the Requester's intent.

**Step 2.1 (Research retrieval):** Agent-driven. Structuring retrieved chunks into key points and suggested angles requires synthesis. Retrieving chunks from ChromaDB is deterministic; the structuring step that follows is not.

**Step 2.2 (Evaluator reviews research):** Agent-driven. Assessing relevance requires reading both the brief and the research brief together. However, the scoring threshold (relevance ≥ 0.6) is deterministic — the evaluator's judgment is applied on top of a deterministic filter, not instead of it.

**Step 2.3 (Draft writing):** Agent-driven. Writing long-form content with the right tone, structure, and argument requires language synthesis. This is the core value proposition of the Draft Agent. A deterministic system cannot write a blog post.

**Step 2.4 (Draft evaluation):** Agent-driven. Assessing tone, audience fit, and argument quality requires reading and judging language — not rule matching. But: any legal_flags.txt check inside this evaluation is deterministic. The evaluator runs both layers and reports them separately.

**Step 2.5 (Draft revision):** Agent-driven. Revising prose based on specific critique requires language generation. The critique is deterministic (logged verbatim from the evaluator); acting on it is not.

**Step 2.6 (Draft escalation):** Deterministic automation triggers the escalation, human decides what to do next. The counter check (exactly 2 revision loops) is a rule. The decision about what to do next (guide the agent, assign a human writer, cancel) belongs to the Strategist. Letting an agent decide what happens after it has failed twice would be circular.

**Step 2.7 (Format adaptation):** Agent-driven. Condensing a 1,500-word blog post into a 280-character tweet that preserves the core message requires language understanding. Character limits are enforced deterministically afterward; the condensation itself is not.

**Step 2.8 (Format evaluation):** Agent-driven. Checking message consistency between primary and formatted content requires reading both. Character limit checks within this step are deterministic.

**Step 3.1 (Strategist review):** Human-only. The Strategist's approval is an editorial judgment about whether the content serves GitHub's priorities. No agent can substitute for this because the decision requires contextual knowledge — current company focus, recent competitive moves, upcoming announcements — that is not in the system's knowledge base. This decision also carries accountability: if bad content ships, the Strategist is responsible.

**Step 3.2 (Revision with Strategist feedback):** Agent-driven. The Draft Agent receives explicit instruction and produces revised prose. The Strategist's feedback is the deterministic input; the revision is the agent output.

**Step 3.3 (Legal trigger check):** Deterministic automation. Matching phrases against legal_flags.txt is a rule. If an agent handled this, it might miss a literal match because it assessed the phrase as "contextually acceptable" — which is exactly the kind of judgment that creates legal exposure. Literal keyword matching must be a function, not an assessment.

**Step 3.4a (Reviewer review):** Human-only. Legal review requires a qualified, named individual. Legal judgments carry professional accountability. An agent that decided whether a competitor mention was legally acceptable would expose GitHub to liability — the Reviewer exists precisely to apply human legal judgment.

**Step 3.4b (Reviewer skip):** Deterministic automation. The skip is mechanical — if no triggers, skip. It must be logged, not just silently applied. An agent deciding whether the Reviewer should be skipped ("this mention seems benign") would reintroduce the probabilistic risk that Step 3.3 was designed to eliminate.

**Step 4.1 (Rules engine check):** Deterministic automation. Product name formatting, prohibited phrases, character limits, FTC markers — all of these are rules. An agent handling compliance rules introduces variance: it might decide a prohibited phrase is "used ironically" or "clearly satirical." Rules must behave identically every time.

**Step 4.2 (Evaluator judgment pass):** Agent-driven. Tone consistency and cross-channel message drift require reading multiple pieces of content in relation to each other. This is the only compliance step that benefits from language understanding over rule matching.

**Step 4.3 (Strategist resolves violations):** Human-only for non-deterministic fixes. Auto-fixes (correcting a product name format) can run without human interaction. But any fix that changes the meaning or angle of content — even slightly — requires Strategist confirmation. The line is: if the fix can be applied by substituting one string for another, it's auto-fix. If it requires a judgment about what the content should say instead, it's human.

**Step 5.1 (Publisher review):** Human-only. Publishing is irreversible. The Publisher is the last check on channel, schedule, and final content. The Publisher also carries organizational accountability for what GitHub says publicly and when. No agent can hold this accountability.

**Step 5.2 (Publish job lock):** Deterministic automation. The five-condition check is a rule. All five must be true. This step must be a function because any variance in how the conditions are evaluated would create a risk that content publishes without all approvals in place.

**Step 5.3 (Scheduler trigger):** Deterministic automation. APScheduler fires at the specified datetime. This is a clock check. An agent deciding "now seems like a good time" is not acceptable.

**Step 5.4 (Channel publish):** Deterministic automation. API calls to LinkedIn, Twitter/X, and Mailgun are deterministic — the system sends the content, the platform responds with success or failure. An agent narrating what to post instead of calling the API would introduce unnecessary indirection and failure modes.

**Phases 6 & 7 (Logging, Alerts):** Deterministic automation. Log entry construction, hash chaining, and threshold-based alerting are all functions. Agents must not be involved in either — both are reliability systems that depend on identical behavior every time.

---

## Approval, Verification, and Guardrails

### Approval stage specifications

**Strategist (always required)**
- Scope: Goal alignment, editorial angle, audience fit, draft quality
- SLA (production): 24 hours from stage entry
- SLA (demo): 30 seconds
- Can be skipped: Never
- Rejection requires: Feedback text, minimum 20 characters
- What happens on no action: Yellow at 50% SLA → Red + email at 80% → STALLED at 100%

**Reviewer (conditional)**
- Scope: Legal and compliance concerns only — not content quality
- Trigger condition: At least one match in the draft against `legal_flags.txt`
- SLA (production): 48 hours from stage entry
- SLA (demo): 45 seconds
- Can be skipped: Yes, but only when NO_TRIGGER is explicitly logged. A skip without a logged trigger check is a pipeline error.
- Rejection requires: Feedback text describing the specific legal concern
- What happens on no action: Same escalation as Strategist, but final STALLED notification goes to both Strategist and Requester

**Publisher (always required)**
- Scope: Channel selection, publish schedule, final content confirmation
- SLA (production): 4 hours from stage entry
- SLA (demo): 15 seconds
- Can be skipped: Never
- Approval requires: Explicit Confirm click with a scheduled datetime selected
- What happens on no action: Yellow at 50% SLA → Red + email at 80% → STALLED at 100%. If the scheduled publish window closes before confirmation, the scheduled publish is automatically cancelled and Requester is notified.

### Documentation prerequisites before any approval is recorded

Before the system writes an approval event to the audit log, the orchestrator verifies that the following log entries exist:

- Before STRATEGIST_APPROVED can be written: `BRIEF_CONFIRMED` + `RESEARCH_EVALUATED_PASS` + `DRAFT_EVALUATED_PASS` + `FORMAT_EVALUATED_PASS` must all exist in the log for this content ID.
- Before REVIEWER_APPROVED can be written: `STRATEGIST_APPROVED` + `LEGAL_TRIGGER_CHECK_COMPLETE` (with result = TRIGGER) must exist.
- Before PUBLISHER_CONFIRMED can be written: `STRATEGIST_APPROVED` + (`REVIEWER_APPROVED` or `REVIEWER_STAGE_SKIPPED`) + `COMPLIANCE_PASSED` must all exist.

If any prerequisite is missing, the approval endpoint returns an error and the UI shows a warning. Approvals cannot be granted out of sequence.

### Alert thresholds and escalation paths

| Alert | Trigger | Severity | Notification | Response window |
|-------|---------|----------|--------------|----------------|
| SLA Warning | 50% of stage SLA elapsed, no action | YELLOW | Dashboard panel | Until 80% |
| SLA Urgent | 80% of stage SLA elapsed, no action | RED | Dashboard + email | Until 100% |
| SLA Breach | 100% of stage SLA elapsed, no action | RED | Dashboard + email to all stakeholders | Manual resume required |
| Publish Window | <2h to scheduled publish, stages incomplete | RED | Dashboard + email to all actors | Immediate |
| Compliance Failure | Rules engine or evaluator fails at F-04 | RED | Dashboard to Strategist | Until resolved |
| Agent Failure | DRAFT_ESCALATED, LOW_CONTEXT, FORMAT_CONSTRAINT_FAILURE | YELLOW/RED | Dashboard to Strategist | Until resolved |
| Publish Failure | Channel API call returns error at Step 5.4 | RED | Dashboard to Publisher | Manual retry |

**No-action escalation sequence:**
1. Stage entered → SLA clock starts → logged as `SLA_CLOCK_STARTED`
2. 50% elapsed → yellow alert fires → `SLA_WARNING_FIRED` logged
3. 80% elapsed → red alert fires → email sent via Mailgun → `SLA_URGENT_FIRED` logged
4. 100% elapsed → state → STALLED → all stakeholders notified → `SLA_BREACH_FIRED` logged
5. STALLED content must be manually resumed by Strategist or Requester. No auto-resume, no auto-cancel (except for publish window expiry, which auto-cancels the scheduled job).

---

## Risk Mitigation Strategy

### Risk 1 — Agent bypasses an approval gate

**Why this matters:** If an agent could advance pipeline state without a logged human approval, the entire approval structure becomes decorative. Content could reach the Publisher or even publish without Strategist or Reviewer sign-off.

**Detection:** The orchestrator checks prerequisite audit log entries before writing any state transition. If a prerequisite event is missing, the transition is rejected and an alert fires. This check runs on every transition, not just approval-adjacent ones.

**Mitigation:** Approvals are written by the human-facing API endpoint — not by the agent layer. The agent layer has no write access to `approval_log.json` or `pipeline_state.json`. Only the orchestrator (called by authenticated human-facing endpoints) can write these files.

**Escalation:** Any detected state inconsistency (state says STRATEGIST_APPROVED but no such log entry exists) locks the content and fires a RED alert to the Strategist and system operator.

**Human override condition:** The Strategist can manually unlock and reset state via a protected admin panel. All admin panel actions are logged with the same hash-chained audit format as standard events.

---

### Risk 2 — Legal trigger missed (false negative)

**Why this matters:** If a draft contains a competitor mention or unverified benchmark claim that the trigger check misses, it bypasses Reviewer review and moves toward publication unchecked. This is the highest-consequence failure in the compliance chain.

**Detection:** The legal trigger check (Step 3.3) and the compliance rules engine (Step 4.1) both scan for legal_flags.txt matches independently. A phrase that was missed at Step 3.3 will be caught at Step 4.1. A late trigger detection at Step 4.1 generates a `COMPLIANCE_LATE_TRIGGER` alert — a distinct event type that signals the trigger check at Step 3.3 may need its keyword list updated.

**Mitigation:** Two independent checks of the same keyword list. The checks are run by different components (the pipeline trigger check vs. the compliance rules engine) so a failure in one does not propagate to the other.

**Escalation:** Late trigger detected at Step 4.1 → Reviewer is pulled back in → state reverts to PENDING_REVIEWER_REVIEW → Publisher cannot confirm until Reviewer re-approves.

**Human override condition:** The Reviewer can explicitly waive a late trigger with a logged justification. This creates a clear record that the decision was made intentionally.

---

### Risk 3 — Scheduling deadline conflict

**Why this matters:** If a publish window closes before all approvals are complete, content either publishes without full approval (wrong) or silently misses its window (also wrong, but better). The system must detect this before it happens, not after.

**Detection:** The publish window alert fires when the scheduled publish datetime is within 2 hours and the content is not in PUBLISHER_CONFIRMED state. This alert is RED and immediate — no yellow phase.

**Mitigation:** The orchestrator enforces strict sequencing. Publish job locking requires all five conditions to be true. If the scheduled datetime passes before the job is locked, the job is automatically cancelled and the Requester is notified with the reason.

**Escalation:** Publish window alert → RED, immediate, all actors notified. If still blocked at publish time, job is cancelled with `PUBLISH_JOB_CANCELLED` logged and `reason: publish_window_expired`.

**Human override condition:** The Requester can reschedule. No agent can reschedule. If the Requester reschedules, the full publish job lock process repeats with the new datetime.

---

### Risk 4 — Agent misclassifies content as low-risk

**Why this matters:** If the Central Evaluator incorrectly passes a draft that contains a legal flag or brand violation, the content advances with the appearance of having been reviewed but with an actual compliance gap.

**Detection:** The evaluator's `confidence` field is checked by the orchestrator. Confidence below 0.6 triggers `EVALUATION_INCONCLUSIVE`. Inconclusive is never treated as a pass. Additionally, the compliance rules engine at Step 4.1 runs deterministic checks independently of the evaluator — it is the safety net for evaluator errors.

**Mitigation:** Two-layer compliance design: deterministic rules engine catches rule violations regardless of evaluator output; the evaluator handles judgment-based concerns that rules can't capture. The layers are independent and run sequentially, not in parallel.

**Escalation:** EVALUATION_INCONCLUSIVE → routed to Strategist for manual review before advancing.

**Human override condition:** The Strategist reviews all EVALUATION_INCONCLUSIVE outputs and decides whether to pass, request revision, or escalate.

---

### Risk 5 — Escalation loop

**Why this matters:** Without a hard cap, the Draft Agent could cycle through revisions indefinitely — producing drafts that never meet the evaluator's standard. This wastes time, consumes API budget, and stalls the pipeline.

**Detection:** The orchestrator tracks the revision counter for each content piece in `pipeline_state.json`. The counter is not stored in agent context (which could be lost between calls) — it is in the orchestrator's centrally managed state.

**Mitigation:** Hard cap at 2 revision loops. After 2 consecutive DRAFT_EVALUATED_FAIL results, state → DRAFT_ESCALATED. The agent does not attempt a third revision without explicit human direction.

**Escalation:** DRAFT_ESCALATED → alert to Strategist with both revision drafts and both sets of evaluator critique. Strategist decides: inject explicit guidance for a third attempt, assign to a human writer, or cancel.

**Human override condition:** Strategist can unlock and reset the revision counter if they choose to give the agent a third attempt with new direction. All such overrides are logged.

---

### Risk 6 — Brand voice inconsistency across channels

**Why this matters:** If the Twitter/X thread contradicts or materially misrepresents the blog post — even subtly — GitHub's message becomes incoherent across platforms. This erodes audience trust and creates confusion about what GitHub actually announced.

**Detection:** The Central Evaluator checks cross-channel message consistency at Step 2.8 (format evaluation). The compliance judgment pass at Step 4.2 runs a second independent check. Both checks compare each channel format against the primary draft for claim consistency.

**Mitigation:** Format Agent reads `channel_specs.json` on every run, which includes per-channel tone rules, not just character limits. The evaluator's consistency check is part of its standard rubric for format evaluation.

**Escalation:** Inconsistency at Step 2.8 → Format Agent revises (one loop only). If still flagged, Strategist resolves manually before advancing to approval.

---

## Control Flow Architecture

### The orchestrator owns all state

The Central Orchestrator is the only component authorized to write state transitions. Every other component — agents, the evaluator, the rules engine, the scheduler — returns output to the orchestrator. The orchestrator validates the output, logs the event, checks prerequisites, and then writes the new state. Components do not chain themselves.

```
Component returns result to orchestrator
  → Orchestrator verifies result is complete and well-formed
  → Orchestrator calls log_event() — writes audit entry
  → Orchestrator verifies prerequisite audit entries exist
  → Orchestrator writes new state to pipeline_state.json
  → Orchestrator routes to next component
```

If any step in this sequence fails — the log write fails, the prerequisite check fails, the state write fails — the orchestrator halts, fires an alert, and does not advance the pipeline. It does not retry automatically.

### State is stored centrally, not distributed

Each content piece has one `pipeline_state.json`. It is the single authoritative record of where the piece is in the pipeline and how it got there. There is no pipeline state inside agent context, inside the evaluator, or inside the scheduler. If a component crashes and restarts, it reads `pipeline_state.json` and continues from the last known good state.

### Agents cannot trigger downstream actions

Agents return structured output. They do not call the next step. They do not write state. They do not send alerts. The orchestrator reads their output and decides what happens next. This constraint is architectural — the agent API returns a payload; it does not have access to the orchestrator's routing functions.

### Five-condition publish gate

The publish job locking step (Step 5.2) checks all five conditions simultaneously against the audit log before creating the scheduled job:

```python
PUBLISH_CONDITIONS = [
    audit_log.contains(content_id, "STRATEGIST_APPROVED"),
    audit_log.contains(content_id, "REVIEWER_APPROVED") or
        audit_log.contains(content_id, "REVIEWER_STAGE_SKIPPED"),
    audit_log.contains(content_id, "COMPLIANCE_PASSED"),
    audit_log.contains(content_id, "PUBLISHER_CONFIRMED"),
    pipeline_state.scheduled_datetime > datetime.utcnow()
]
assert all(PUBLISH_CONDITIONS), "Publish job cannot be locked"
```

All five must be true. If any is false, the publish job is not created. This is not a soft check — it is a hard assertion.

### Log before act

The invariant throughout the system is: write the audit log entry first, then perform the action. Not the reverse.

```python
# Correct
log_event("CHANNEL_PUBLISH_INITIATED", {...})
result = publish_to_linkedin(content)
log_event("CHANNEL_PUBLISH_SUCCESS", {post_id: result.id})

# Wrong — never done
result = publish_to_linkedin(content)
log_event("CHANNEL_PUBLISH_SUCCESS", {...})  # What if this fails?
```

If the pre-action log write fails, the action does not proceed and an alert fires. This ensures the audit trail is always complete — there is no scenario where an action happened but no log entry exists.

### Hash-chained audit integrity

Every audit log entry includes a SHA-256 hash of its own payload concatenated with the hash of the previous entry. This creates a chain: if any past entry is modified, its hash changes, and all subsequent entries reference the wrong previous hash. The chain breaks detectably.

On export, the chain is verified from entry 1 to the current entry. A broken chain is reported with the entry ID where the break was detected. This is not cryptographic signing — it is tamper detection.

---

## What Must Never Be Left to an Agent

This section is a hard list. These decisions remain deterministic, human, or logged-before-execution under all circumstances — including future system enhancements.

### Decisions that must remain deterministic (never agent judgment)

- Legal trigger detection (Step 3.3): keyword matching against legal_flags.txt. An agent's "contextual interpretation" of whether a phrase is legally sensitive creates liability.
- Duplicate brief detection (Step 1.3): exact title + content type match. An agent's semantic similarity judgment could suppress valid content.
- Approval gate enforcement: whether a stage prerequisite has been satisfied. If an agent decided whether an approval counts, approvals lose meaning.
- SLA threshold calculations: whether 50%, 80%, or 100% of a window has elapsed is arithmetic, not judgment.
- Compliance rules engine checks (Step 4.1): product name formatting, prohibited phrases, character limits, FTC markers. These must behave identically every run.
- Publish job locking (Step 5.2): the five-condition check is a rule. Variance here is how content publishes without authorization.
- Publish execution (Step 5.4): API calls are deterministic. An agent narrating what to post is not acceptable.

### Approvals that must require a named human

- Strategist approval or rejection: every piece, no exceptions, no delegation to automation.
- Reviewer approval or rejection: when triggered, no exceptions, cannot be substituted by the Strategist.
- Publisher confirmation: every piece, no exceptions. The Confirm button cannot fire without a human click.
- Compliance violation resolution that is not a deterministic auto-fix: if the resolution requires judgment about what the content should say, a named Strategist owns the decision.
- Decision to assign a DRAFT_ESCALATED piece to a human writer: this is a resource and quality decision that belongs to the Strategist.

### Actions that must be logged before execution

- Every state transition
- Every approval decision — including the feedback text verbatim, not summarized
- Every agent output sent for evaluation
- Every evaluation result — pass, fail, or inconclusive — with full critique
- Every alert fired — type, severity, assigned actor, response deadline
- Every stage skip — with the specific reason logged, not just the skip event
- Every compliance check result — rules engine and evaluator, separately
- Every publish attempt — initiated before the API call, result after

### Irreversible actions that require full prerequisite verification before execution

- Publishing to any channel (blog file write, email send, social post): requires all five publish conditions verified against the audit log.
- Locking a publish job: same five-condition check.
- Cancelling a scheduled publish job: must be logged with reason before cancellation fires.
- Marking a content piece as PUBLISHED or CANCELLED: these states cannot be reversed. The audit entry must exist before the state is written.

No agent can trigger any of these actions. No agent can be granted the ability to trigger them in a future version without revisiting this specification.

---

## Full Pipeline (Feature by Feature)

---

### F-01: Content Initiation & Brief Generation

The pipeline begins when a Requester submits a content brief. The brief is the contract for everything that follows — if it's vague, every downstream step suffers. This feature enforces structure at intake and uses AI to enrich the brief before any human reviews it.

**What the Requester does:** Fills a structured form with the content title, type (tutorial, announcement, thought leadership, case study), target audience, goal, and requested publish date. Submits. Watches the AI enrichment populate in the right panel. Reviews and edits any suggested field. Confirms to proceed.

**What the system does:** Validates the form fields deterministically — required fields, valid content type, future publish date, no duplicate title+type. Then the Research Agent runs a lightweight enrichment pass: suggested keywords, audience framing, content angle, and whether similar content exists in `past_campaigns.json`. The Central Evaluator checks enrichment quality before it's shown to the Requester. Enriched fields are clearly marked as AI-suggested and fully editable.

**Why enrichment happens here:** The brief drives everything. Getting the keywords, audience, and angle right at intake means the Research Agent in F-02 gets a better signal. Catching problems at the brief stage is cheaper than fixing a bad draft.

**Deterministic steps:** Field validation, duplicate detection, schema enforcement.

**Agent steps:** Brief enrichment (Research Agent, lightweight pass) → evaluated by Central Evaluator before display.

**Output:** Confirmed brief JSON locked after Requester confirmation, passed to F-02.

---

### F-02: Research & Drafting

This is the core generative step. The system does the research and writes the draft. The Strategist reviews the result — they don't produce it.

**What the Strategist sees:** A research panel on the left showing sources, key points, and suggested angles. A draft panel on the right showing the full primary content piece. Below it, the channel-adapted formats. A "Regenerate with notes" button if anything needs to change.

**What the system does, in order:**

First, the Research Agent searches `company_data/` using ChromaDB vector search, structures the top relevant chunks into a research brief, and returns it to the orchestrator. The Central Evaluator checks the research brief for relevance and completeness before the Draft Agent sees it.

Second, the Draft Agent receives the confirmed brief and the evaluator-approved research brief. It writes the full primary draft. The Central Evaluator reviews against a rubric: goal alignment, audience fit, tone, keyword coverage, attribution. If it fails, the evaluator returns structured critique and the Draft Agent revises — told exactly what failed, not left to re-infer. Maximum two revision loops.

Third, the Format Agent takes the approved draft and adapts it for the appropriate channel. The Central Evaluator checks format compliance and message consistency with the primary piece.

**The regeneration flow:** If the Strategist clicks "Regenerate with notes," their feedback is appended to the Draft Agent's prompt as explicit instruction. The agent is told what to fix, not left to guess.

**Output:** Draft JSON containing primary draft and channel-adapted formats, passed to F-03.

---

### F-03: Multi-Stage Approval Workflow

Approvals are the human checkpoints in the pipeline. Each stage has a defined scope — approvers review what they're qualified to review and nothing more.

**The approval stages:**

- **Strategist** reviews every piece. They check goal alignment, editorial angle, audience fit, and draft quality. They are not proofreading for typos — they are asking whether this content should exist in its current form.

- **Reviewer** enters only when `legal_flags.txt` triggers. Scope: legal and compliance concerns only. If nothing triggers, this stage is auto-skipped and logged as `REVIEWER_STAGE_SKIPPED`.

- **Publisher** is the final confirmation before scheduling. They confirm the content, the channel, and the publish window. They do not edit — that window is closed.

**The rejection and feedback flow:** When an approver rejects, a chat-like input appears inline below the content preview. They type feedback in plain text. This feedback threads to the relevant agent as explicit instruction. The approver sees the revised draft in the same thread. It feels like a conversation, not a form. This matters because vague feedback produces bad revisions — the chat format encourages specificity.

**Output:** Approval log JSON with all stage decisions, timestamps, and actor roles, passed to F-04.

---

### F-04: Brand & Compliance Guardrails

This step runs automatically after Reviewer approval (or skip) and before Publisher review. No user triggers it. Strategist sees the result and resolves any issues before the content reaches the Publisher.

**Two-layer design:**

The first layer is the rules engine — deterministic, fast, auditable. Product name formatting, competitor mentions, character limits, FTC markers, prohibited phrases. Same input, same output, every time.

The second layer is the Central Evaluator running a judgment pass. Tone consistency, cross-channel message coherence, readability. This only runs if the rules layer is clean.

**Auto-fix is narrow.** The system only auto-fixes deterministic violations — a product name formatted incorrectly is corrected automatically. Agent suggestions for tone or messaging are shown as options. The Strategist confirms or edits. Agents never silently rewrite approved content.

**Output:** Compliance-cleared final content JSON, passed to F-05 (Publisher review).

---

### F-05: Scheduled Publishing & Distribution

Publishing is the most consequential and irreversible step. No agent is involved. No action fires without explicit human confirmation.

**What the Publisher does:** Reviews the final content for each channel in a preview panel. Sets the publish date and time. Clicks "Confirm Schedule." Watches each channel's status update in real time after the scheduled time passes.

**What the system does:** The orchestrator runs the five-condition check against the audit log. APScheduler waits for the scheduled datetime. When it fires, the publish sequence runs: blog post written to `published/blog/`, email sent via Mailgun, social post sent via LinkedIn or Twitter/X API. Each channel reports success or failure.

**Channels by content type:**
- Technical tutorials → Blog post
- Product announcements → LinkedIn post
- Developer thought leadership → Twitter/X thread
- Case studies → Blog post

**On failure:** Dashboard shows the error with a retry option. Publisher decides whether to retry or investigate. No auto-retry.

**Output:** Published content record with channel statuses, publish timestamps, and API response IDs, written to F-06.

---

### F-06: Audit Trail & Logging

The audit trail is a cross-cutting system, not a reporting feature. It runs from the moment a brief is submitted to the moment content is published. Every action, decision, skip, and failure is logged.

**What the user sees:** A collapsible audit panel at the bottom of the dashboard, always visible. Timestamped list of every event for the current content piece. Filterable by stage. Exportable as CSV.

**What gets logged:** Every state transition, every approval decision (with feedback text verbatim), every agent output sent for evaluation and its result, every skipped stage, every compliance check result, every publish attempt and outcome, every alert fired.

**How it works:** Every system action calls `log_event()`. No component writes to the audit log directly — only the logging module can. Entries are append-only. Each entry includes a SHA-256 hash of itself concatenated with the previous entry's hash, creating a tamper-detectable chain.

---

### F-07: Escalation & Alert Engine

Alerts exist because pipelines stall. The alert engine catches situations before they become problems.

**What the user sees:** An alert panel in the top-right of the dashboard. Active alerts show the content ID, the trigger, the required action, and the severity. Dismiss, reassign, or escalate from the panel. Urgent alerts trigger a Mailgun email so the responsible person is notified even if they're not on the dashboard.

**Alert types:**

SLA warning fires at 50% of the stage window with no action — yellow, dashboard only. Escalates to red + email at 80%. Escalates to STALLED at 100%.

Publish window alert fires when fewer than 2 hours remain before scheduled publish and not all stages are complete — immediate red, all actors notified.

Compliance failure alert fires when the rules engine or evaluator flags a violation — content blocked from Publisher until resolved.

Agent failure alerts fire on DRAFT_ESCALATED, RESEARCH_LOW_CONTEXT, and FORMAT_CONSTRAINT_FAILURE — routed to Strategist with explanation.

Publish failure alert fires when a channel API call fails — Publisher notified with error details and retry option.

**What's deterministic:** All alert thresholds and routing logic are fixed rules. An agent does not decide whether something is urgent. The rules decide.

---

## User Acceptance Criteria

### Brief Generation (F-01)
- Submitting the intake form with all required fields completes without error, and the AI enrichment panel populates within 10 seconds.
- Every AI-suggested enrichment field is editable before the brief is confirmed.
- Submitting a brief with the same title and content type as an existing brief shows an error with the matching brief ID.
- The audit log shows both `BRIEF_SUBMITTED` and `BRIEF_CONFIRMED` events after the step completes.

### Research & Drafting (F-02)
- The blog or case study draft streams to the panel in real time — the user sees it being written, not a loading spinner followed by a wall of text.
- The channel-adapted format (LinkedIn, Twitter/X, or email) appears alongside the primary draft.
- Clicking "Regenerate with notes" and typing a specific instruction produces a revised draft that visibly addresses the feedback.
- Research sources are listed and each one is traceable to a file in `company_data/`.
- Any section of the draft can be edited inline by the user before approval.

### Approval Workflow (F-03)
- The progress bar shows all applicable approval stages with the current stage clearly highlighted.
- The role switcher in the top-right changes which stakeholder role is shown on the approval action.
- Rejecting at any stage opens a chat-like input where the approver types feedback. That feedback is visible in the thread and the revised draft references it.
- When no legal keywords are detected, the Reviewer stage is auto-skipped and a `REVIEWER_STAGE_SKIPPED` entry appears in the audit log.
- Every approval and rejection is logged with the actor role and timestamp.

### Brand & Compliance (F-04)
- The compliance check runs automatically after Reviewer approval or skip — no user needs to trigger it.
- Each violation is shown with the specific text that triggered it, the rule it broke, and a suggested fix.
- "Auto-Fix" resolves only deterministic violations. Agent suggestions require Strategist confirmation.
- The panel shows a clear PASSED status before the Strategist can forward content to the Publisher.

### Publishing (F-05)
- The publish schedule cannot be confirmed until all approval stages are complete and compliance has passed. The Confirm button is disabled otherwise.
- All channel previews are visible before the user confirms the schedule.
- After the scheduled time, each channel shows a real-time success or failure status.
- A successfully published blog post appears as a file in `published/blog/`.
- A successful email send shows a Mailgun message ID on the dashboard.
- A successful social post shows the post ID returned by the LinkedIn or Twitter/X API.
- A failed channel publish shows an error alert with a retry option — it does not auto-retry.

### Audit Trail (F-06)
- The audit log is visible and collapsible at all times without navigating away from the dashboard.
- Every stage transition produces a new log entry within 2 seconds.
- Skipped stages appear in the log as `REVIEWER_STAGE_SKIPPED` with a reason — they are never simply absent.
- The log is filterable by stage and exportable as CSV.

### Alerts (F-07)
- An SLA warning appears on the dashboard after the demo-compressed idle window for each stage.
- An email notification is sent (and visible in inbox) when the urgent threshold is reached.
- A publish window alert appears when fewer than 2 hours remain before a scheduled publish and the content hasn't cleared all stages.
- A channel failure at publish time shows an error alert with retry option.
- Every alert event appears in the audit log.

---

## Data Contracts

### brief.json
```json
{
  "brief_id": "uuid",
  "requester_id": "string",
  "title": "string",
  "content_type": "tutorial | announcement | thought_leadership | case_study",
  "target_audience": "string",
  "goal": "string",
  "requested_publish_date": "ISO 8601",
  "keywords": ["string"],
  "enrichment": {
    "suggested_keywords": ["string"],
    "audience_framing": "string",
    "content_angle": "string",
    "similar_past_content_ids": ["string"]
  },
  "confirmed_at": "ISO 8601",
  "status": "DRAFT | CONFIRMED"
}
```

### research_brief.json
```json
{
  "brief_id": "string",
  "sources": [
    { "file": "string", "chunk": "string", "relevance_score": 0.0 }
  ],
  "key_points": ["string"],
  "suggested_angles": ["string"],
  "gaps": ["string"],
  "low_context": false,
  "retrieved_chunk_count": 0,
  "evaluation_result": "PASS | FAIL | EVALUATION_INCONCLUSIVE"
}
```

### draft.json
```json
{
  "brief_id": "string",
  "revision": 0,
  "content_type": "string",
  "primary_draft": "string",
  "word_count": 0,
  "metadata": {
    "tone": "string",
    "target_audience": "string",
    "keywords_used": ["string"]
  },
  "formats": {
    "linkedin": { "post": "string", "character_count": 0 },
    "twitter": { "thread": ["string"], "total_characters": 0 },
    "email": { "subject": "string", "body": "string" }
  },
  "evaluation_result": "PASS | FAIL | EVALUATION_INCONCLUSIVE",
  "evaluator_critique": []
}
```

### approval_log.json
```json
{
  "brief_id": "string",
  "stages": [
    {
      "stage": "strategist | reviewer | publisher",
      "actor_id": "string",
      "decision": "APPROVED | REJECTED | SKIPPED",
      "feedback": "string | null",
      "skip_reason": "string | null",
      "timestamp": "ISO 8601"
    }
  ]
}
```

### publish_job.json
```json
{
  "job_id": "uuid",
  "brief_id": "string",
  "channels": ["blog | linkedin | twitter | email"],
  "scheduled_datetime": "ISO 8601",
  "publisher_confirmed_at": "ISO 8601",
  "locked_at": "ISO 8601",
  "status": "LOCKED | PUBLISHING | PUBLISHED | FAILED | CANCELLED",
  "channel_results": [
    {
      "channel": "string",
      "status": "SUCCESS | FAILED",
      "post_id": "string | null",
      "error": "string | null",
      "published_at": "ISO 8601 | null"
    }
  ]
}
```

### audit_entry.json
```json
{
  "entry_id": "uuid",
  "event_type": "string",
  "content_id": "string",
  "actor": "system | requester | strategist | reviewer | publisher",
  "actor_id": "string | null",
  "timestamp": "ISO 8601",
  "payload": {},
  "prev_entry_hash": "sha256",
  "entry_hash": "sha256"
}
```

---

## Knowledge Base & RAG Pipeline

The Research Agent does not generate content from its own training data. It retrieves evidence from two sources — a local knowledge base and optional web search — and structures that evidence into a research brief for the Writer. This section describes how that retrieval pipeline works.

### Local knowledge base

The local knowledge base is a folder (`backend/data/company_data/`) containing markdown files that represent GitHub's institutional knowledge: product documentation, developer persona profiles, content strategy notes, and feature summaries. These files are chunked and indexed into a ChromaDB vector database when the backend starts up.

The files in `company_data/` are the primary source. The Research Agent always searches here first. These files represent what GitHub already knows — past positioning, established audience framing, product context — that should inform any new content piece.

**How indexing works:**
1. On backend startup, the vector store module reads every markdown file in `company_data/`
2. Each file is split into overlapping chunks (~500 tokens, 50-token overlap) to preserve context across chunk boundaries
3. Each chunk is embedded and stored in ChromaDB with metadata: source file name, chunk index, content type tag
4. If the ChromaDB collection already exists and the source files haven't changed, indexing is skipped (no re-indexing on every restart)

**How retrieval works:**
1. The Research Agent embeds the content brief's goal and keywords as a query
2. ChromaDB returns the top-k chunks by cosine similarity (default k=10, filtered to those with relevance ≥ 0.6)
3. If fewer than 3 chunks score above the threshold, the `low_context` flag is set and the pipeline pauses for human input

### Web search fallback

When local retrieval returns fewer than 3 relevant chunks, the Research Agent calls the Serper web search API as a fallback. This is used to find publicly available information — GitHub blog posts, developer surveys, industry reports, open source statistics — that supplements the local knowledge base.

Web search is a fallback, not a default. Relying on web search as the primary source would introduce citation uncertainty and make research outputs harder to trace. Local retrieval is always attempted first.

**What web search is used for:**
- Current GitHub feature documentation not yet in the local knowledge base
- Industry statistics and developer survey data (Stack Overflow survey, GitHub Octoverse)
- Public GitHub blog posts and changelogs relevant to the brief topic
- Publicly available case study details for enterprise content

**What web search is not used for:**
- Internal GitHub data, positioning strategy, or confidential product roadmaps — these must come from the local knowledge base
- Generating facts that can't be sourced — if web search doesn't return something useful, the gap is flagged, not fabricated

### Brand guidelines as local reference

`brand_guidelines.txt` is not indexed into ChromaDB. It is loaded as a direct string reference by the Writer and Evaluator agents on every run. It is not retrieved by similarity — it is always fully included. This is intentional: brand rules apply to every piece unconditionally. Similarity-based retrieval would risk partial or missed brand context.

### Adding content to the knowledge base

To add new content to the Research Agent's local knowledge, place a markdown file in `backend/data/company_data/` and restart the backend. The indexing step runs on startup and will pick up new files automatically. Existing files that haven't changed are not re-indexed.

---

## Local Implementation Stack

The system runs entirely on a local machine. No cloud infrastructure is required for the demo.

- **UI:** React, single-page application, Tailwind CSS
- **Backend:** FastAPI (Python)
- **Agent API:** Anthropic Claude API (claude-haiku-4-5 + claude-sonnet-4-6)
- **Vector search:** ChromaDB (local, no external server)
- **Scheduler:** APScheduler (Python, in-process)
- **Email:** Mailgun free tier
- **Social:** LinkedIn API or Twitter/X API (free tier)
- **Brief and draft storage:** Local JSON files
- **Pipeline state:** `pipeline_state.json` per content piece
- **Audit log:** Append-only JSON array with SHA-256 hash chaining
- **Alert store:** `alerts.json`, polled by frontend every 5 seconds

---

## Decision Log

- **D-01** — Company is GitHub. Content system reflects GitHub's developer-first audience and content priorities.
- **D-02** — Central Orchestrator + Central Evaluator. Chosen over hierarchical agent tree for simplicity, debuggability, and clean separation between production and evaluation.
- **D-03** — No agent evaluates its own output. All agent outputs pass through the Central Evaluator before advancing.
- **D-04** — Haiku for structured, low-ambiguity tasks. Sonnet for drafting, synthesis, and judgment-based evaluation. No Opus.
- **D-05** — Content types and channels: tutorials → Blog, announcements → LinkedIn, thought leadership → Twitter/X, case studies → Blog.
- **D-06** — Publishing is fully deterministic. No agent involvement at publish time.
- **D-07** — Rejection flow is chat-like. Approver types plain text feedback inline. It threads to the relevant agent as explicit context.
- **D-08** — Auto-fix applies only to deterministic rule violations. Agent suggestions always require human confirmation.
- **D-09** — Agents cannot write to the audit log. Only the logging module can. Log is append-only with SHA-256 hash chaining.
- **D-10** — Alert SLAs are compressed for demo (seconds, not days). Logic is identical to production.
- **D-11** — Legal Reviewer stage is conditionally triggered. Auto-skipped with explicit log entry when legal_flags.txt returns no matches.
- **D-12** — No content tiers or VP approval stage. The system has exactly 4 personas and 3 approval stages: Strategist (always), Reviewer (conditional), Publisher (always).
- **D-13** — Compliance (F-04) runs after Reviewer approval and before Publisher review. Publisher only sees compliance-cleared content.
- **D-14** — Formal state machine with ~25 explicit states. No implicit transitions. Every state change is logged before it takes effect.
- **D-15** — Log-before-act invariant. The audit entry is written before the action executes. If the log write fails, the action does not proceed.
- **D-16** — Compliance scope: FTC endorsement disclosure rules, LinkedIn and Twitter/X platform ToS, GitHub internal brand standards. No GDPR or SOX — out of scope for this system.
- **D-17** — Five-condition publish gate. All five conditions must be verified against the audit log before the publish job is created. A single false condition blocks the job entirely.

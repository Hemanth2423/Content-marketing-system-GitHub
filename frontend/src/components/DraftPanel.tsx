import { useState, useRef, useEffect } from "react";
import { runDraft } from "../api/client";
import type { PipelineStatus } from "../types";

interface Props {
  pipeline: PipelineStatus;
  onRefresh: () => void;
}

const DRAFT_STATES = new Set([
  "RESEARCH_COMPLETE",
  "DRAFT_IN_PROGRESS",
  "DRAFT_UNDER_EVALUATION",
  "DRAFT_EVALUATION_PASSED",
  "DRAFT_REVISION_IN_PROGRESS",
  "DRAFT_ESCALATED",
  "FORMAT_IN_PROGRESS",
  "FORMAT_COMPLETE",
  "PENDING_STRATEGIST_REVIEW",
  "PENDING_REVIEWER_REVIEW",
  "REVIEWER_SKIPPED",
  "PENDING_COMPLIANCE",
  "COMPLIANCE_PASSED",
  "COMPLIANCE_FAILED",
  "PENDING_PUBLISHER_REVIEW",
  "PUBLISHER_CONFIRMED",
  "PUBLISHING_IN_PROGRESS",
  "PUBLISHED",
  "PUBLISH_FAILED",
]);

export default function DraftPanel({ pipeline, onRefresh }: Props) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notes, setNotes] = useState("");
  const [showNotes, setShowNotes] = useState(false);
  const [streamedText, setStreamedText] = useState("");
  const streamRef = useRef<EventSource | null>(null);

  const draft = pipeline.draft;
  const state = pipeline.state;
  const inProgress = state === "DRAFT_IN_PROGRESS" || state === "DRAFT_REVISION_IN_PROGRESS";

  useEffect(() => {
    return () => streamRef.current?.close();
  }, []);

  const handleRunDraft = async (withNotes = false) => {
    setBusy(true);
    setError(null);
    setStreamedText("");

    // Start SSE stream for live preview
    const es = new EventSource(`/api/pipeline/${pipeline.content_id}/stream-draft`);
    streamRef.current = es;
    es.onmessage = (e) => {
      if (e.data === "[DONE]") {
        es.close();
        return;
      }
      setStreamedText((prev) => prev + e.data);
    };
    es.onerror = () => es.close();

    try {
      const body: Record<string, string> = {};
      if (withNotes && notes) body.strategist_feedback = notes;
      await runDraft(pipeline.content_id, body);
      onRefresh();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Draft failed");
    } finally {
      setBusy(false);
      setStreamedText("");
      es.close();
    }
  };

  const canDraft =
    state === "RESEARCH_COMPLETE" ||
    state === "DRAFT_REVISION_IN_PROGRESS" ||
    state === "DRAFT_ESCALATED";

  if (!DRAFT_STATES.has(state) && !draft) {
    return <p className="text-github-muted text-sm">Research must complete before drafting.</p>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-github-text">Draft</h3>
          {draft && (
            <span className="text-xs text-github-muted">
              Revision {draft.revision} · {draft.word_count} words
            </span>
          )}
        </div>
        {canDraft && (
          <div className="flex gap-2">
            <button onClick={() => setShowNotes(!showNotes)} className="btn-secondary text-sm">
              {showNotes ? "Hide Notes" : "Add Notes"}
            </button>
            <button onClick={() => handleRunDraft(showNotes)} disabled={busy} className="btn-primary text-sm">
              {busy ? "Writing…" : draft ? "Regenerate" : "Write Draft"}
            </button>
          </div>
        )}
      </div>

      {error && <div className="p-3 bg-red-900/30 border border-github-red rounded text-sm text-red-400">{error}</div>}

      {showNotes && (
        <textarea
          className="input-base w-full resize-none"
          rows={3}
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Feedback or direction for the writer agent…"
        />
      )}

      {state === "DRAFT_ESCALATED" && (
        <div className="p-3 border border-github-red bg-red-900/20 rounded text-sm text-red-400">
          ⚠ Draft escalated — failed evaluation after maximum revisions. Provide feedback and regenerate.
        </div>
      )}

      {inProgress && streamedText && (
        <div className="bg-github-dark border border-github-border rounded p-4">
          <div className="text-xs text-github-muted mb-2 flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full bg-github-blue animate-ping" />
            Streaming draft…
          </div>
          <pre className="text-sm text-github-text whitespace-pre-wrap font-mono leading-relaxed">
            {streamedText}
          </pre>
        </div>
      )}

      {draft && !inProgress && (
        <div className="space-y-3">
          {draft.evaluation && (
            <div className={`p-3 rounded border text-sm ${draft.evaluation.result === "PASS" ? "border-green-700 bg-green-900/20 text-green-400" : "border-red-700 bg-red-900/20 text-red-400"}`}>
              <span className="font-medium">Evaluator: {draft.evaluation.result}</span>
              {draft.evaluation.issues.length > 0 && (
                <ul className="mt-2 space-y-1 text-xs opacity-80">
                  {draft.evaluation.issues.map((issue, i) => (
                    <li key={i}>• [{issue.severity}] {issue.description}</li>
                  ))}
                </ul>
              )}
            </div>
          )}

          <div className="bg-github-dark border border-github-border rounded p-4 max-h-96 overflow-y-auto">
            <pre className="text-sm text-github-text whitespace-pre-wrap leading-relaxed">{draft.primary_draft}</pre>
          </div>

          {draft.formats && (
            <div>
              <h4 className="text-xs text-github-muted uppercase tracking-wide mb-2">Channel Formats</h4>
              <div className="grid gap-2">
                {draft.formats.linkedin && (
                  <FormatCard label="LinkedIn" char_count={draft.formats.linkedin.char_count}>
                    <p className="font-medium text-sm">{draft.formats.linkedin.hook}</p>
                    <p className="text-xs text-github-muted mt-1">{draft.formats.linkedin.body.slice(0, 120)}…</p>
                    <p className="text-xs text-github-blue mt-1">{draft.formats.linkedin.hashtags.join(" ")}</p>
                  </FormatCard>
                )}
                {draft.formats.twitter && (
                  <FormatCard label="Twitter/X" char_count={draft.formats.twitter.thread.reduce((s, t) => s + t.char_count, 0)}>
                    <p className="text-xs text-github-muted">{draft.formats.twitter.total_tweets} tweet thread</p>
                    <p className="text-sm mt-1">{draft.formats.twitter.thread[0]?.tweet}</p>
                  </FormatCard>
                )}
                {draft.formats.email && (
                  <FormatCard label="Email" char_count={draft.formats.email.char_count}>
                    <p className="text-sm font-medium">{draft.formats.email.subject}</p>
                    <p className="text-xs text-github-muted mt-1">{draft.formats.email.preview_text}</p>
                  </FormatCard>
                )}
                {draft.formats.constraint_failures.length > 0 && (
                  <div className="p-2 border border-yellow-700 bg-yellow-900/20 rounded text-xs text-yellow-400">
                    ⚠ Constraint failures: {draft.formats.constraint_failures.join(", ")}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function FormatCard({ label, char_count, children }: { label: string; char_count: number; children: React.ReactNode }) {
  return (
    <div className="border border-github-border rounded p-3 bg-github-dark">
      <div className="flex justify-between items-center mb-2">
        <span className="text-xs font-semibold text-github-muted uppercase">{label}</span>
        <span className="text-xs text-github-muted">{char_count} chars</span>
      </div>
      {children}
    </div>
  );
}

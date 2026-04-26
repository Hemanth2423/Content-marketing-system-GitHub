import { useState } from "react";
import { submitApproval } from "../api/client";
import type { PipelineStatus, ApprovalStage, UserRole } from "../types";

interface Props {
  pipeline: PipelineStatus;
  role: UserRole;
  onRefresh: () => void;
}

export default function ApprovalPanel({ pipeline, role, onRefresh }: Props) {
  const [feedback, setFeedback] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const state = pipeline.state;
  const approvalLog = pipeline.approval_log;

  const activeStage: ApprovalStage | null =
    state === "PENDING_STRATEGIST_REVIEW"
      ? "strategist"
      : state === "PENDING_REVIEWER_REVIEW"
      ? "reviewer"
      : null;

  const canAct = activeStage !== null && (role === activeStage);

  const submit = async (decision: "approve" | "reject") => {
    if (!activeStage) return;
    if (decision === "reject" && feedback.trim().length < 20) {
      setError("Feedback must be at least 20 characters when rejecting.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await submitApproval(pipeline.content_id, activeStage, decision, role, feedback || undefined);
      setFeedback("");
      onRefresh();
    } catch (e: unknown) {
      const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail ?? (e instanceof Error ? e.message : "Approval failed"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-4">
      <h3 className="font-semibold text-github-text">Approvals</h3>

      {error && <div className="p-3 bg-red-900/30 border border-github-red rounded text-sm text-red-400">{error}</div>}

      {/* Stage history */}
      <div className="space-y-2">
        {(["strategist", "reviewer"] as ApprovalStage[]).map((stage) => {
          const entry = approvalLog.stages.find((s) => s.stage === stage);
          const isPending =
            (stage === "strategist" && state === "PENDING_STRATEGIST_REVIEW") ||
            (stage === "reviewer" && state === "PENDING_REVIEWER_REVIEW");
          const isSkipped = stage === "reviewer" && state === "REVIEWER_SKIPPED";

          return (
            <div
              key={stage}
              className={`border rounded p-3 ${
                entry?.decision === "approved"
                  ? "border-green-700 bg-green-900/10"
                  : entry?.decision === "skipped" || isSkipped
                  ? "border-github-border bg-github-dark"
                  : entry?.decision === "rejected"
                  ? "border-github-red bg-red-900/10"
                  : isPending
                  ? "border-github-blue bg-blue-900/10"
                  : "border-github-border"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-github-text capitalize">{stage}</span>
                <span className={`text-xs px-2 py-0.5 rounded-full ${
                  entry?.decision === "approved" ? "bg-green-900 text-green-400" :
                  entry?.decision === "skipped" || isSkipped ? "bg-gray-800 text-github-muted" :
                  entry?.decision === "rejected" ? "bg-red-900 text-red-400" :
                  isPending ? "bg-blue-900 text-blue-400" : "bg-github-dark text-github-muted"
                }`}>
                  {entry
                    ? entry.decision
                    : isSkipped
                    ? "skipped (no legal flags)"
                    : isPending
                    ? "Pending"
                    : "Waiting"}
                </span>
              </div>
              {entry?.feedback && (
                <p className="text-xs text-github-muted mt-2 italic">"{entry.feedback}"</p>
              )}
              {entry?.skip_reason && (
                <p className="text-xs text-github-muted mt-1">Skip reason: {entry.skip_reason}</p>
              )}
              {entry && (
                <p className="text-xs text-github-muted mt-1">
                  {entry.actor_id} · {new Date(entry.timestamp).toLocaleString()}
                </p>
              )}
            </div>
          );
        })}
      </div>

      {/* Action panel */}
      {activeStage && canAct && (
        <div className="border border-github-border rounded p-4 space-y-3">
          <p className="text-sm text-github-muted">
            Reviewing as <strong className="text-github-text capitalize">{activeStage}</strong>
          </p>
          <textarea
            className="input-base w-full resize-none"
            rows={3}
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="Feedback (required for rejection — min 20 chars)…"
          />
          <div className="flex gap-3">
            <button
              onClick={() => submit("reject")}
              disabled={busy}
              className="flex-1 px-4 py-2 rounded border border-github-red text-red-400 hover:bg-red-900/20 text-sm transition-colors disabled:opacity-50"
            >
              Reject
            </button>
            <button
              onClick={() => submit("approve")}
              disabled={busy}
              className="flex-1 btn-primary text-sm"
            >
              {busy ? "Submitting…" : "Approve"}
            </button>
          </div>
        </div>
      )}

      {activeStage && !canAct && (
        <p className="text-sm text-github-muted">
          Waiting for <span className="capitalize text-github-text">{activeStage}</span> review. Switch role to act.
        </p>
      )}

      {/* Legal check running */}
      {state === "LEGAL_CHECK_IN_PROGRESS" && (
        <div className="flex items-center gap-2 text-github-muted text-sm animate-pulse">
          <div className="w-2 h-2 rounded-full bg-github-blue animate-ping" />
          Running legal trigger check…
        </div>
      )}

      {state === "REVIEWER_SKIPPED" && (
        <div className="p-3 border border-github-border rounded text-sm text-github-muted">
          Reviewer stage automatically skipped — no legal flags detected. Compliance check running.
        </div>
      )}
    </div>
  );
}

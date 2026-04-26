import { useState } from "react";
import { resolveCompliance } from "../api/client";
import type { PipelineStatus } from "../types";

interface Props {
  pipeline: PipelineStatus;
  role: string;
  onRefresh: () => void;
}

const COMPLIANCE_STATES = new Set([
  "COMPLIANCE_RULES_CHECK_IN_PROGRESS",
  "COMPLIANCE_RULES_FAILED",
  "STRATEGIST_RESOLVING",
  "COMPLIANCE_JUDGMENT_CHECK_IN_PROGRESS",
  "COMPLIANCE_PASSED",
]);

export default function CompliancePanel({ pipeline, role, onRefresh }: Props) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const state = pipeline.state;

  if (!COMPLIANCE_STATES.has(state)) {
    return (
      <div className="space-y-2">
        <h3 className="font-semibold text-github-text">Compliance</h3>
        <p className="text-github-muted text-sm">
          Compliance check runs automatically after Strategist / Reviewer approval.
        </p>
      </div>
    );
  }

  const handleResolve = async () => {
    setBusy(true);
    setError(null);
    try {
      await resolveCompliance(pipeline.content_id, role);
      onRefresh();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to resolve");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-4">
      <h3 className="font-semibold text-github-text">Compliance (F-04)</h3>

      {error && <div className="p-3 bg-red-900/30 border border-github-red rounded text-sm text-red-400">{error}</div>}

      {(state === "COMPLIANCE_RULES_CHECK_IN_PROGRESS" || state === "COMPLIANCE_JUDGMENT_CHECK_IN_PROGRESS") && (
        <div className="flex items-center gap-2 text-github-muted text-sm animate-pulse">
          <div className="w-2 h-2 rounded-full bg-github-blue animate-ping" />
          {state === "COMPLIANCE_RULES_CHECK_IN_PROGRESS" ? "Running rules engine…" : "Running judgment check…"}
        </div>
      )}

      {state === "COMPLIANCE_PASSED" && (
        <div className="p-4 border border-green-700 bg-green-900/10 rounded">
          <div className="flex items-center gap-2 text-green-400 font-medium">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            Compliance Passed
          </div>
          <p className="text-sm text-github-muted mt-2">
            Rules engine + AI judgment checks passed. Content is now in Publisher review.
          </p>
        </div>
      )}

      {(state === "COMPLIANCE_RULES_FAILED" || state === "STRATEGIST_RESOLVING") && (
        <div className="space-y-3">
          <div className="p-4 border border-github-red bg-red-900/10 rounded">
            <div className="flex items-center gap-2 text-red-400 font-medium mb-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
              Compliance Failed
            </div>
            <p className="text-sm text-github-muted">
              Violations found. Any deterministic product name issues have been auto-fixed. Manual review required for remaining violations.
            </p>
            {state === "STRATEGIST_RESOLVING" && (
              <p className="text-sm text-yellow-400 mt-2">
                Waiting for Strategist to resolve violations and re-submit.
              </p>
            )}
          </div>

          <p className="text-xs text-github-muted">
            Check the Audit Log (below) for the full violation list with locations and offending text.
          </p>

          {state === "STRATEGIST_RESOLVING" && (
            <button
              onClick={handleResolve}
              disabled={busy || role === "observer" || role === "publisher"}
              className="btn-primary w-full text-sm"
            >
              {busy ? "Re-running compliance…" : "Mark Resolved & Re-run Compliance"}
            </button>
          )}
        </div>
      )}
    </div>
  );
}

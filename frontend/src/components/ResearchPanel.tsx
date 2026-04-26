import { useState } from "react";
import { runResearch, acceptLowContext } from "../api/client";
import type { PipelineStatus } from "../types";

interface Props {
  pipeline: PipelineStatus;
  onRefresh: () => void;
}

export default function ResearchPanel({ pipeline, onRefresh }: Props) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const research = pipeline.research;
  const state = pipeline.state;

  const handleRun = async () => {
    setBusy(true);
    setError(null);
    try {
      await runResearch(pipeline.content_id);
      onRefresh();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Research failed");
    } finally {
      setBusy(false);
    }
  };

  const handleAcceptLowContext = async () => {
    setBusy(true);
    try {
      await acceptLowContext(pipeline.content_id);
      onRefresh();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed");
    } finally {
      setBusy(false);
    }
  };

  const canRunResearch = state === "BRIEF_CONFIRMED";

  const inProgress = state === "RESEARCH_IN_PROGRESS";

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-github-text">Research</h3>
        {canRunResearch && (
          <button onClick={handleRun} disabled={busy} className="btn-primary text-sm">
            Run Research
          </button>
        )}
        {state === "RESEARCH_LOW_CONTEXT" && (
          <button onClick={handleAcceptLowContext} disabled={busy} className="btn-secondary text-sm">
            Accept Low Context & Continue
          </button>
        )}
      </div>

      {error && <div className="p-3 bg-red-900/30 border border-github-red rounded text-sm text-red-400">{error}</div>}

      {inProgress && (
        <div className="flex items-center gap-2 text-github-muted text-sm animate-pulse">
          <div className="w-2 h-2 rounded-full bg-github-blue animate-ping" />
          Research in progress…
        </div>
      )}

      {state === "RESEARCH_LOW_CONTEXT" && (
        <div className="p-3 border border-yellow-600 bg-yellow-900/20 rounded text-sm text-yellow-400">
          ⚠ Low context — only {research?.retrieved_chunk_count ?? 0} chunks retrieved above relevance threshold. You can accept and proceed or investigate the knowledge base.
        </div>
      )}

      {research && (
        <div className="space-y-4">
          <div className="flex gap-4 text-xs text-github-muted">
            <span>Chunks: <strong className="text-github-text">{research.retrieved_chunk_count}</strong></span>
            <span>Web search: <strong className={research.web_search_used ? "text-yellow-400" : "text-github-text"}>{research.web_search_used ? "Yes" : "No"}</strong></span>
            {research.evaluation && (
              <span>Eval: <strong className={research.evaluation.result === "PASS" ? "text-green-400" : "text-red-400"}>{research.evaluation.result}</strong></span>
            )}
          </div>

          {research.key_points.length > 0 && (
            <div>
              <h4 className="text-xs text-github-muted mb-2 uppercase tracking-wide">Key Points</h4>
              <ul className="space-y-1">
                {research.key_points.map((p, i) => (
                  <li key={i} className="text-sm text-github-text pl-3 border-l-2 border-github-blue">{p}</li>
                ))}
              </ul>
            </div>
          )}

          {research.suggested_angles.length > 0 && (
            <div>
              <h4 className="text-xs text-github-muted mb-2 uppercase tracking-wide">Suggested Angles</h4>
              <ul className="space-y-1">
                {research.suggested_angles.map((a, i) => (
                  <li key={i} className="text-sm text-github-text pl-3 border-l-2 border-github-accent">{a}</li>
                ))}
              </ul>
            </div>
          )}

          {research.gaps.length > 0 && (
            <div>
              <h4 className="text-xs text-github-muted mb-2 uppercase tracking-wide">Gaps</h4>
              <ul className="space-y-1">
                {research.gaps.map((g, i) => (
                  <li key={i} className="text-sm text-yellow-400 pl-3 border-l-2 border-yellow-600">{g}</li>
                ))}
              </ul>
            </div>
          )}

          {research.sources.length > 0 && (
            <div>
              <h4 className="text-xs text-github-muted mb-2 uppercase tracking-wide">Sources</h4>
              <ul className="space-y-1">
                {research.sources.map((s, i) => (
                  <li key={i} className="text-xs text-github-muted font-mono truncate">{s}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {!research && !inProgress && !canRunResearch && (
        <p className="text-github-muted text-sm">Research not yet started.</p>
      )}
    </div>
  );
}

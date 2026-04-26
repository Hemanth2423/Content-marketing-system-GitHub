import { useState } from "react";
import { confirmPublish, retryPublish } from "../api/client";
import type { PipelineStatus } from "../types";

interface Props {
  pipeline: PipelineStatus;
  role: string;
  onRefresh: () => void;
}

export default function PublishPanel({ pipeline, role, onRefresh }: Props) {
  const [scheduledAt, setScheduledAt] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const state = pipeline.state;
  const canConfirm = state === "PENDING_PUBLISHER_REVIEW" && role === "publisher";
  const canRetry = state === "PUBLISH_FAILED";

  const handleConfirm = async () => {
    if (!scheduledAt) {
      setError("Please select a scheduled date/time.");
      return;
    }
    const dt = new Date(scheduledAt).toISOString();
    setBusy(true);
    setError(null);
    try {
      await confirmPublish(pipeline.content_id, dt, role);
      onRefresh();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Confirm failed");
    } finally {
      setBusy(false);
    }
  };

  const handleRetry = async () => {
    setBusy(true);
    setError(null);
    try {
      await retryPublish(pipeline.content_id);
      onRefresh();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Retry failed");
    } finally {
      setBusy(false);
    }
  };

  const channelResults = pipeline.channel_results ?? {};

  return (
    <div className="space-y-4">
      <h3 className="font-semibold text-github-text">Publish</h3>

      {error && <div className="p-3 bg-red-900/30 border border-github-red rounded text-sm text-red-400">{error}</div>}

      {state === "PENDING_PUBLISHER_REVIEW" && (
        <div className="border border-github-border rounded p-4 space-y-4">
          <p className="text-sm text-github-muted">
            Content has cleared all approval and compliance stages. Schedule and confirm publication.
          </p>

          {pipeline.draft?.formats && (
            <div className="space-y-2">
              <h4 className="text-xs text-github-muted uppercase tracking-wide">Channel Previews</h4>
              {pipeline.draft.formats.linkedin && (
                <ChannelPreview label="LinkedIn">
                  <p className="text-sm font-medium">{pipeline.draft.formats.linkedin.hook}</p>
                  <p className="text-xs text-github-muted mt-1 line-clamp-3">{pipeline.draft.formats.linkedin.body}</p>
                </ChannelPreview>
              )}
              {pipeline.draft.formats.twitter && (
                <ChannelPreview label="Twitter/X">
                  <p className="text-sm">{pipeline.draft.formats.twitter.thread[0]?.tweet}</p>
                  <p className="text-xs text-github-muted mt-1">{pipeline.draft.formats.twitter.total_tweets} tweets in thread</p>
                </ChannelPreview>
              )}
              {pipeline.draft.formats.email && (
                <ChannelPreview label="Email">
                  <p className="text-sm font-medium">{pipeline.draft.formats.email.subject}</p>
                  <p className="text-xs text-github-muted mt-1">{pipeline.draft.formats.email.preview_text}</p>
                </ChannelPreview>
              )}
            </div>
          )}

          {canConfirm ? (
            <div className="space-y-3 pt-2 border-t border-github-border">
              <label className="block text-sm text-github-muted">Scheduled Date & Time</label>
              <input
                type="datetime-local"
                className="input-base w-full"
                value={scheduledAt}
                onChange={(e) => setScheduledAt(e.target.value)}
                min={new Date(Date.now() + 60000).toISOString().slice(0, 16)}
              />
              <button onClick={handleConfirm} disabled={busy} className="btn-primary w-full">
                {busy ? "Scheduling…" : "Confirm & Lock Publish Job"}
              </button>
            </div>
          ) : (
            <p className="text-sm text-github-muted">Switch to Publisher role to confirm.</p>
          )}
        </div>
      )}

      {state === "PUBLISHER_CONFIRMED" && (
        <div className="p-4 border border-github-blue bg-blue-900/10 rounded">
          <p className="text-blue-400 font-medium">Publish job locked</p>
          <p className="text-sm text-github-muted mt-1">
            Scheduled for: {pipeline.scheduled_datetime ? new Date(pipeline.scheduled_datetime).toLocaleString() : "—"}
          </p>
        </div>
      )}

      {state === "PUBLISHING_IN_PROGRESS" && (
        <div className="flex items-center gap-2 text-github-muted text-sm animate-pulse">
          <div className="w-2 h-2 rounded-full bg-github-blue animate-ping" />
          Publishing to channels…
        </div>
      )}

      {state === "PUBLISHED" && (
        <div className="space-y-3">
          <div className="p-4 border border-green-700 bg-green-900/10 rounded">
            <p className="text-green-400 font-semibold">Published</p>
            <p className="text-sm text-github-muted mt-1">Content has been published to all configured channels.</p>
          </div>
          {Object.entries(channelResults).map(([ch, result]) => (
            <div key={ch} className={`border rounded p-3 text-sm ${result.status === "SUCCESS" ? "border-green-700" : "border-github-red"}`}>
              <div className="flex justify-between">
                <span className="capitalize font-medium text-github-text">{ch}</span>
                <span className={result.status === "SUCCESS" ? "text-green-400" : "text-red-400"}>{result.status}</span>
              </div>
              {result.post_id && <p className="text-xs text-github-muted mt-1 font-mono">{result.post_id}</p>}
              {result.note && <p className="text-xs text-github-muted mt-1 italic">{result.note}</p>}
              {result.error && <p className="text-xs text-red-400 mt-1">{result.error}</p>}
            </div>
          ))}
        </div>
      )}

      {state === "PUBLISH_FAILED" && (
        <div className="space-y-3">
          <div className="p-4 border border-github-red bg-red-900/10 rounded">
            <p className="text-red-400 font-semibold">Publish Failed</p>
            <p className="text-sm text-github-muted mt-1">One or more channels failed. Review errors below and retry.</p>
          </div>
          {Object.entries(channelResults).map(([ch, result]) => (
            <div key={ch} className={`border rounded p-3 text-sm ${result.status === "SUCCESS" ? "border-green-700" : "border-github-red"}`}>
              <div className="flex justify-between">
                <span className="capitalize font-medium">{ch}</span>
                <span className={result.status === "SUCCESS" ? "text-green-400" : "text-red-400"}>{result.status}</span>
              </div>
              {result.error && <p className="text-xs text-red-400 mt-1">{result.error}</p>}
            </div>
          ))}
          {canRetry && (
            <button onClick={handleRetry} disabled={busy} className="btn-primary w-full">
              {busy ? "Retrying…" : "Retry Publish"}
            </button>
          )}
        </div>
      )}

      {!["PENDING_PUBLISHER_REVIEW", "PUBLISHER_CONFIRMED", "PUBLISHING_IN_PROGRESS", "PUBLISHED", "PUBLISH_FAILED"].includes(state) && (
        <p className="text-github-muted text-sm">Publisher review becomes available after compliance passes.</p>
      )}
    </div>
  );
}

function ChannelPreview({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="border border-github-border rounded p-3 bg-github-dark">
      <p className="text-xs font-semibold text-github-muted uppercase mb-2">{label}</p>
      {children}
    </div>
  );
}

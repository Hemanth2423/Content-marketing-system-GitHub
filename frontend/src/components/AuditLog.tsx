import { useState, useEffect } from "react";
import { getAuditLog, verifyAuditChain } from "../api/client";
import type { AuditEntry } from "../types";

interface Props {
  contentId: string;
}

const STAGE_FILTERS = ["", "RESEARCH", "DRAFT", "APPROVAL", "COMPLIANCE", "PUBLISH", "STATE_TRANSITION"];

export default function AuditLog({ contentId }: Props) {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [filter, setFilter] = useState("");
  const [expanded, setExpanded] = useState<string | null>(null);
  const [chainValid, setChainValid] = useState<boolean | null>(null);
  const [collapsed, setCollapsed] = useState(true);

  useEffect(() => {
    if (collapsed) return;
    getAuditLog(contentId, filter || undefined).then((r) => setEntries(r.entries));
    verifyAuditChain(contentId).then((r) => setChainValid(r.chain_valid));
  }, [contentId, filter, collapsed]);

  return (
    <div className="border border-github-border rounded">
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="w-full flex items-center justify-between px-4 py-3 text-sm font-medium text-github-text hover:bg-github-surface transition-colors"
      >
        <span>Audit Log</span>
        <div className="flex items-center gap-2">
          {chainValid !== null && (
            <span className={`text-xs px-2 py-0.5 rounded-full ${chainValid ? "bg-green-900 text-green-400" : "bg-red-900 text-red-400"}`}>
              Chain {chainValid ? "valid" : "BROKEN"}
            </span>
          )}
          <svg className={`w-4 h-4 transition-transform ${collapsed ? "" : "rotate-180"}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {!collapsed && (
        <div className="border-t border-github-border">
          <div className="px-4 py-2 flex gap-2 overflow-x-auto">
            {STAGE_FILTERS.map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`text-xs px-3 py-1 rounded-full whitespace-nowrap transition-colors ${
                  filter === f ? "bg-github-blue text-white" : "bg-github-dark text-github-muted border border-github-border hover:border-github-muted"
                }`}
              >
                {f || "All"}
              </button>
            ))}
          </div>

          <div className="divide-y divide-github-border max-h-96 overflow-y-auto">
            {entries.length === 0 && (
              <p className="px-4 py-6 text-sm text-github-muted text-center">No entries</p>
            )}
            {entries.map((e) => (
              <div key={e.entry_id} className="px-4 py-2">
                <button
                  onClick={() => setExpanded(expanded === e.entry_id ? null : e.entry_id)}
                  className="w-full text-left"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-mono text-github-blue">{e.event_type}</span>
                    <span className="text-xs text-github-muted shrink-0">
                      {new Date(e.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <div className="text-xs text-github-muted mt-0.5">
                    {e.actor}{e.actor_id && e.actor_id !== e.actor ? ` · ${e.actor_id}` : ""}
                  </div>
                </button>
                {expanded === e.entry_id && (
                  <div className="mt-2 space-y-1">
                    <pre className="text-xs text-github-muted bg-github-dark rounded p-2 overflow-x-auto">
                      {JSON.stringify(e.payload, null, 2)}
                    </pre>
                    <p className="text-xs text-github-muted font-mono truncate">hash: {e.entry_hash.slice(0, 32)}…</p>
                  </div>
                )}
              </div>
            ))}
          </div>

          <div className="px-4 py-2 border-t border-github-border">
            <a
              href={`/api/audit/${contentId}/export`}
              download
              className="text-xs text-github-blue hover:underline"
            >
              Export CSV
            </a>
          </div>
        </div>
      )}
    </div>
  );
}

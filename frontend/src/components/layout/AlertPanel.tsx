import type { Alert } from "../../types";

const severityColor: Record<string, string> = {
  info: "border-github-blue text-blue-400",
  warning: "border-github-yellow text-yellow-400",
  urgent: "border-orange-500 text-orange-400",
  critical: "border-github-red text-red-400",
};

interface Props {
  alerts: Alert[];
  onDismiss: (id: string) => void;
  onClose: () => void;
}

export default function AlertPanel({ alerts, onDismiss, onClose }: Props) {
  return (
    <div className="fixed top-0 right-0 h-full w-80 bg-github-surface border-l border-github-border z-50 flex flex-col shadow-xl">
      <div className="flex items-center justify-between px-4 py-3 border-b border-github-border">
        <span className="font-semibold text-github-text">Active Alerts</span>
        <button onClick={onClose} className="text-github-muted hover:text-github-text">✕</button>
      </div>
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {alerts.length === 0 && (
          <p className="text-github-muted text-sm text-center mt-8">No active alerts</p>
        )}
        {alerts.map((a) => (
          <div
            key={a.alert_id}
            className={`border rounded-md p-3 bg-github-dark ${severityColor[a.severity] ?? "border-github-border text-github-text"}`}
          >
            <div className="flex items-start justify-between gap-2">
              <div>
                <div className="text-xs font-mono opacity-70 mb-1">{a.alert_type}</div>
                <div className="text-sm">{a.message}</div>
                <div className="text-xs text-github-muted mt-1">
                  {new Date(a.created_at).toLocaleTimeString()}
                </div>
              </div>
              <button
                onClick={() => onDismiss(a.alert_id)}
                className="text-github-muted hover:text-github-text shrink-0 text-xs"
              >
                ✕
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

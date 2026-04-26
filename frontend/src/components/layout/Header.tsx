import type { UserRole } from "../../types";

const ROLES: UserRole[] = ["strategist", "reviewer", "publisher", "observer"];

interface Props {
  role: UserRole;
  onRoleChange: (r: UserRole) => void;
  alertCount: number;
  onAlertsClick: () => void;
}

export default function Header({ role, onRoleChange, alertCount, onAlertsClick }: Props) {
  return (
    <header className="bg-github-surface border-b border-github-border px-6 py-3 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <svg height="24" viewBox="0 0 16 16" className="fill-github-text" aria-hidden="true">
          <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" />
        </svg>
        <span className="font-semibold text-github-text">Content Marketing System</span>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <span className="text-github-muted text-sm">Role:</span>
          <select
            value={role}
            onChange={(e) => onRoleChange(e.target.value as UserRole)}
            className="bg-github-dark border border-github-border rounded px-2 py-1 text-sm text-github-text focus:outline-none focus:border-github-blue"
          >
            {ROLES.map((r) => (
              <option key={r} value={r}>
                {r.charAt(0).toUpperCase() + r.slice(1)}
              </option>
            ))}
          </select>
        </div>

        <button
          onClick={onAlertsClick}
          className="relative flex items-center gap-1.5 px-3 py-1.5 rounded border border-github-border hover:border-github-muted text-sm text-github-text transition-colors"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
          </svg>
          Alerts
          {alertCount > 0 && (
            <span className="absolute -top-1.5 -right-1.5 bg-github-red text-white text-xs rounded-full w-4 h-4 flex items-center justify-center font-bold">
              {alertCount > 9 ? "9+" : alertCount}
            </span>
          )}
        </button>
      </div>
    </header>
  );
}

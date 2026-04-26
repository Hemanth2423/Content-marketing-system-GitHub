import { useState } from "react";
import Header from "./components/layout/Header";
import AlertPanel from "./components/layout/AlertPanel";
import BriefForm from "./components/BriefForm";
import PipelineDashboard from "./components/PipelineDashboard";
import { usePipeline } from "./hooks/usePipeline";
import { useAlerts } from "./hooks/useAlerts";
import type { UserRole } from "./types";

export default function App() {
  const [role, setRole] = useState<UserRole>("strategist");
  const [contentId, setContentId] = useState<string | null>(null);
  const [showAlerts, setShowAlerts] = useState(false);

  const { pipeline, refresh } = usePipeline(contentId);
  const { alerts, dismiss } = useAlerts();

  const activeAlerts = alerts.filter((a) => !a.dismissed);

  return (
    <div className="min-h-screen bg-github-dark text-github-text">
      <Header
        role={role}
        onRoleChange={setRole}
        alertCount={activeAlerts.length}
        onAlertsClick={() => setShowAlerts(!showAlerts)}
      />

      <main className="max-w-4xl mx-auto px-4 py-8">
        {!contentId ? (
          <BriefForm onBriefConfirmed={(id) => setContentId(id)} />
        ) : pipeline ? (
          <PipelineDashboard pipeline={pipeline} role={role} onRefresh={refresh} />
        ) : (
          <div className="flex items-center justify-center h-64">
            <div className="text-github-muted animate-pulse">Loading pipeline…</div>
          </div>
        )}
      </main>

      {showAlerts && (
        <AlertPanel
          alerts={activeAlerts}
          onDismiss={dismiss}
          onClose={() => setShowAlerts(false)}
        />
      )}
    </div>
  );
}

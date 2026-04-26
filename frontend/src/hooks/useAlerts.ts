import { useState, useEffect } from "react";
import { getAlerts, dismissAlert } from "../api/client";
import type { Alert } from "../types";

export function useAlerts() {
  const [alerts, setAlerts] = useState<Alert[]>([]);

  const refresh = async () => {
    try {
      const data = await getAlerts();
      setAlerts(data);
    } catch {
      // silently ignore — alerts are non-critical UI
    }
  };

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 5000);
    return () => clearInterval(id);
  }, []);

  const dismiss = async (alertId: string) => {
    await dismissAlert(alertId);
    setAlerts((prev) => prev.filter((a) => a.alert_id !== alertId));
  };

  return { alerts, dismiss, refresh };
}

import { useState, useEffect, useCallback } from "react";
import { getPipeline } from "../api/client";
import type { PipelineStatus } from "../types";

export function usePipeline(contentId: string | null) {
  const [pipeline, setPipeline] = useState<PipelineStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!contentId) return;
    try {
      const data = await getPipeline(contentId);
      setPipeline(data);
      setError(null);
    } catch (e: unknown) {
      if (e instanceof Error) setError(e.message);
    }
  }, [contentId]);

  useEffect(() => {
    if (!contentId) return;
    setLoading(true);
    refresh().finally(() => setLoading(false));
    const id = setInterval(refresh, 2000);
    return () => clearInterval(id);
  }, [contentId, refresh]);

  return { pipeline, loading, error, refresh };
}

import { useState } from "react";
import { createBrief, enrichBrief, confirmBrief } from "../api/client";
import type { BriefCreate, ContentType, EnrichResponse } from "../types";

const CONTENT_TYPES: ContentType[] = ["tutorial", "announcement", "thought_leadership", "case_study"];

interface Props {
  onBriefConfirmed: (id: string) => void;
}

export default function BriefForm({ onBriefConfirmed }: Props) {
  const [step, setStep] = useState<"form" | "created" | "enriched">("form");
  const [briefId, setBriefId] = useState<string | null>(null);
  const [enrichData, setEnrichData] = useState<EnrichResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Min datetime for requested_publish_date — at least 1 hour from now
  const minDate = new Date(Date.now() + 3600000).toISOString().slice(0, 16);

  const [form, setForm] = useState<BriefCreate>({
    title: "",
    content_type: "tutorial",
    target_audience: "",
    goal: "",
    requested_publish_date: "",
    keywords: [""],
  });

  const set = <K extends keyof BriefCreate>(k: K, v: BriefCreate[K]) =>
    setForm((f) => ({ ...f, [k]: v }));

  const handleSubmit = async () => {
    setBusy(true);
    setError(null);
    try {
      const result = await createBrief({
        ...form,
        keywords: form.keywords.filter(Boolean),
        requested_publish_date: new Date(form.requested_publish_date).toISOString(),
      });
      setBriefId(result.brief_id);
      setStep("created");
    } catch (e: unknown) {
      const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
      if (detail && typeof detail === "object" && "error" in (detail as object)) {
        const d = detail as { error: string; matching_brief_id?: string };
        setError(`${d.error}${d.matching_brief_id ? ` (existing ID: ${d.matching_brief_id})` : ""}`);
      } else {
        setError(typeof detail === "string" ? detail : "Failed to create brief");
      }
    } finally {
      setBusy(false);
    }
  };

  const handleEnrich = async () => {
    if (!briefId) return;
    setBusy(true);
    setError(null);
    try {
      const result = await enrichBrief(briefId);
      setEnrichData(result);
      setStep("enriched");
    } catch (e: unknown) {
      setError("Enrichment failed");
      console.error(e);
    } finally {
      setBusy(false);
    }
  };

  const handleConfirm = async () => {
    if (!briefId) return;
    setBusy(true);
    setError(null);
    try {
      await confirmBrief(briefId);
      onBriefConfirmed(briefId);
    } catch (e: unknown) {
      setError("Confirmation failed");
      console.error(e);
    } finally {
      setBusy(false);
    }
  };

  if (step === "form") {
    return (
      <div className="max-w-2xl mx-auto">
        <h2 className="text-xl font-semibold text-github-text mb-6">New Content Brief</h2>
        {error && <div className="mb-4 p-3 bg-red-900/30 border border-github-red rounded text-sm text-red-400">{error}</div>}

        <div className="space-y-4">
          <Field label="Title (min 10 chars)">
            <input
              className="input-base"
              value={form.title}
              onChange={(e) => set("title", e.target.value)}
              placeholder="e.g. How GitHub Copilot Speeds Up Code Reviews"
            />
          </Field>

          <Field label="Content Type">
            <select className="input-base" value={form.content_type} onChange={(e) => set("content_type", e.target.value as ContentType)}>
              {CONTENT_TYPES.map((t) => <option key={t} value={t}>{t.replace(/_/g, " ")}</option>)}
            </select>
          </Field>

          <Field label="Target Audience">
            <input
              className="input-base"
              value={form.target_audience}
              onChange={(e) => set("target_audience", e.target.value)}
              placeholder="e.g. Senior engineers at mid-size tech companies"
            />
          </Field>

          <Field label="Goal (min 10 chars)">
            <textarea
              className="input-base resize-none"
              rows={2}
              value={form.goal}
              onChange={(e) => set("goal", e.target.value)}
              placeholder="What should this content achieve?"
            />
          </Field>

          <Field label="Requested Publish Date">
            <input
              type="datetime-local"
              className="input-base"
              value={form.requested_publish_date}
              onChange={(e) => set("requested_publish_date", e.target.value)}
              min={minDate}
            />
          </Field>

          <Field label="Keywords (optional)">
            {form.keywords.map((kw, i) => (
              <div key={i} className="flex gap-2 mb-2">
                <input
                  className="input-base flex-1"
                  value={kw}
                  onChange={(e) => {
                    const kws = [...form.keywords];
                    kws[i] = e.target.value;
                    set("keywords", kws);
                  }}
                  placeholder={`Keyword ${i + 1}`}
                />
                {form.keywords.length > 1 && (
                  <button
                    onClick={() => set("keywords", form.keywords.filter((_, j) => j !== i))}
                    className="text-github-muted hover:text-github-red"
                  >✕</button>
                )}
              </div>
            ))}
            <button
              onClick={() => set("keywords", [...form.keywords, ""])}
              className="text-sm text-github-blue hover:underline"
            >+ Add keyword</button>
          </Field>

          <button
            onClick={handleSubmit}
            disabled={busy || form.title.length < 10 || form.goal.length < 10 || !form.requested_publish_date}
            className="btn-primary w-full mt-2"
          >
            {busy ? "Creating…" : "Create Brief"}
          </button>
        </div>
      </div>
    );
  }

  if (step === "created") {
    return (
      <div className="max-w-2xl mx-auto space-y-6">
        <div>
          <h2 className="text-xl font-semibold text-github-text">Brief Created</h2>
          <p className="text-github-muted text-sm mt-1">ID: <span className="font-mono text-github-text">{briefId}</span></p>
        </div>
        {error && <div className="p-3 bg-red-900/30 border border-github-red rounded text-sm text-red-400">{error}</div>}
        <p className="text-sm text-github-muted">
          Run AI enrichment to get keyword suggestions, audience framing, and content angles based on your knowledge base.
        </p>
        <div className="flex gap-3">
          <button onClick={handleEnrich} disabled={busy} className="btn-secondary flex-1">
            {busy ? "Enriching…" : "AI Enrich Brief"}
          </button>
          <button onClick={handleConfirm} disabled={busy} className="btn-primary flex-1">
            {busy ? "Confirming…" : "Skip & Confirm"}
          </button>
        </div>
      </div>
    );
  }

  if (step === "enriched" && enrichData) {
    return (
      <div className="max-w-2xl mx-auto space-y-6">
        <div>
          <h2 className="text-xl font-semibold text-github-text">Enrichment Complete</h2>
          <p className="text-sm text-github-muted mt-1">
            Evaluation: <span className={enrichData.evaluation === "PASS" ? "text-green-400" : "text-yellow-400"}>{enrichData.evaluation}</span>
            {" · "}{enrichData.research_summary.source_count} knowledge chunks retrieved
            {enrichData.research_summary.low_context && <span className="text-yellow-400"> (low context)</span>}
          </p>
        </div>
        {error && <div className="p-3 bg-red-900/30 border border-github-red rounded text-sm text-red-400">{error}</div>}

        <div className="bg-github-surface border border-github-border rounded-lg p-4 space-y-4">
          {enrichData.enrichment.suggested_keywords.length > 0 && (
            <div>
              <h4 className="text-xs text-github-muted uppercase tracking-wide mb-2">Suggested Keywords</h4>
              <div className="flex flex-wrap gap-2">
                {enrichData.enrichment.suggested_keywords.map((kw, i) => (
                  <span key={i} className="text-xs px-2 py-1 bg-github-dark border border-github-border rounded text-github-text">{kw}</span>
                ))}
              </div>
            </div>
          )}
          {enrichData.enrichment.audience_framing && (
            <div>
              <h4 className="text-xs text-github-muted uppercase tracking-wide mb-1">Audience Framing</h4>
              <p className="text-sm text-yellow-400">{enrichData.enrichment.audience_framing}</p>
            </div>
          )}
          {enrichData.enrichment.content_angle && (
            <div>
              <h4 className="text-xs text-github-muted uppercase tracking-wide mb-1">Content Angle</h4>
              <p className="text-sm text-yellow-400">{enrichData.enrichment.content_angle}</p>
            </div>
          )}
          {enrichData.research_summary.key_points.length > 0 && (
            <div>
              <h4 className="text-xs text-github-muted uppercase tracking-wide mb-2">Key Research Points</h4>
              <ul className="space-y-1">
                {enrichData.research_summary.key_points.map((p, i) => (
                  <li key={i} className="text-sm text-github-text pl-3 border-l-2 border-github-blue">{p}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        <button onClick={handleConfirm} disabled={busy} className="btn-primary w-full">
          {busy ? "Confirming…" : "Confirm & Start Pipeline"}
        </button>
      </div>
    );
  }

  return null;
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-sm text-github-muted mb-1">{label}</label>
      {children}
    </div>
  );
}

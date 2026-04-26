import type { PipelineStatus, UserRole } from "../types";
import ResearchPanel from "./ResearchPanel";
import DraftPanel from "./DraftPanel";
import ApprovalPanel from "./ApprovalPanel";
import CompliancePanel from "./CompliancePanel";
import PublishPanel from "./PublishPanel";
import AuditLog from "./AuditLog";

interface Props {
  pipeline: PipelineStatus;
  role: UserRole;
  onRefresh: () => void;
}

const ALL_STATES = [
  "BRIEF_DRAFT", "BRIEF_SUBMITTED", "ENRICHMENT_IN_PROGRESS", "ENRICHMENT_COMPLETE", "BRIEF_CONFIRMED",
  "RESEARCH_IN_PROGRESS", "RESEARCH_COMPLETE", "RESEARCH_LOW_CONTEXT",
  "DRAFT_IN_PROGRESS", "DRAFT_UNDER_EVALUATION", "DRAFT_EVALUATION_PASSED",
  "DRAFT_REVISION_IN_PROGRESS", "DRAFT_ESCALATED",
  "FORMAT_IN_PROGRESS", "FORMAT_COMPLETE",
  "PENDING_STRATEGIST_REVIEW", "STRATEGIST_APPROVED", "LEGAL_CHECK_IN_PROGRESS",
  "PENDING_REVIEWER_REVIEW", "REVIEWER_APPROVED", "REVIEWER_SKIPPED",
  "COMPLIANCE_RULES_CHECK_IN_PROGRESS", "COMPLIANCE_JUDGMENT_CHECK_IN_PROGRESS",
  "COMPLIANCE_RULES_FAILED", "STRATEGIST_RESOLVING", "COMPLIANCE_PASSED",
  "PENDING_PUBLISHER_REVIEW", "PUBLISHER_CONFIRMED", "PUBLISH_JOB_LOCKED",
  "SCHEDULED", "PUBLISHING_IN_PROGRESS", "PUBLISHED",
  "PUBLISH_FAILED", "STALLED", "CANCELLED",
];

const STATE_LABELS: Record<string, string> = {
  BRIEF_DRAFT: "Brief Draft",
  BRIEF_SUBMITTED: "Brief Submitted",
  ENRICHMENT_IN_PROGRESS: "Enriching",
  ENRICHMENT_COMPLETE: "Enriched",
  BRIEF_CONFIRMED: "Brief Confirmed",
  RESEARCH_IN_PROGRESS: "Researching",
  RESEARCH_COMPLETE: "Research Done",
  RESEARCH_LOW_CONTEXT: "Low Context",
  DRAFT_IN_PROGRESS: "Drafting",
  DRAFT_UNDER_EVALUATION: "Evaluating Draft",
  DRAFT_EVALUATION_PASSED: "Draft Passed",
  DRAFT_REVISION_IN_PROGRESS: "Revising",
  DRAFT_ESCALATED: "Escalated",
  FORMAT_IN_PROGRESS: "Formatting",
  FORMAT_COMPLETE: "Format Done",
  PENDING_STRATEGIST_REVIEW: "Strategist Review",
  STRATEGIST_APPROVED: "Strategist Approved",
  LEGAL_CHECK_IN_PROGRESS: "Legal Check",
  PENDING_REVIEWER_REVIEW: "Reviewer Review",
  REVIEWER_APPROVED: "Reviewer Approved",
  REVIEWER_SKIPPED: "Reviewer Skipped",
  COMPLIANCE_RULES_CHECK_IN_PROGRESS: "Rules Check",
  COMPLIANCE_JUDGMENT_CHECK_IN_PROGRESS: "Judgment Check",
  COMPLIANCE_RULES_FAILED: "Compliance Failed",
  STRATEGIST_RESOLVING: "Awaiting Resolution",
  COMPLIANCE_PASSED: "Compliance Passed",
  PENDING_PUBLISHER_REVIEW: "Publisher Review",
  PUBLISHER_CONFIRMED: "Publish Confirmed",
  PUBLISH_JOB_LOCKED: "Job Locked",
  SCHEDULED: "Scheduled",
  PUBLISHING_IN_PROGRESS: "Publishing",
  PUBLISHED: "Published",
  PUBLISH_FAILED: "Publish Failed",
  STALLED: "Stalled",
  CANCELLED: "Cancelled",
};

const STATE_COLOR: Record<string, string> = {
  RESEARCH_LOW_CONTEXT: "bg-yellow-500",
  DRAFT_ESCALATED: "bg-orange-500",
  COMPLIANCE_RULES_FAILED: "bg-github-red",
  STRATEGIST_RESOLVING: "bg-orange-500",
  PUBLISH_FAILED: "bg-github-red",
  STALLED: "bg-github-red",
  CANCELLED: "bg-gray-600",
  PUBLISHED: "bg-green-600",
  COMPLIANCE_PASSED: "bg-green-600",
};

function getProgress(state: string): number {
  const idx = ALL_STATES.indexOf(state);
  if (idx === -1) return 0;
  return Math.round(((idx + 1) / ALL_STATES.length) * 100);
}

type PanelType = "research" | "draft" | "approval" | "compliance" | "publish";

function activePanel(state: string): PanelType {
  if (["BRIEF_CONFIRMED", "RESEARCH_IN_PROGRESS", "RESEARCH_COMPLETE", "RESEARCH_LOW_CONTEXT"].includes(state))
    return "research";
  if ([
    "DRAFT_IN_PROGRESS", "DRAFT_UNDER_EVALUATION", "DRAFT_EVALUATION_PASSED",
    "DRAFT_REVISION_IN_PROGRESS", "DRAFT_ESCALATED", "FORMAT_IN_PROGRESS", "FORMAT_COMPLETE",
  ].includes(state))
    return "draft";
  if ([
    "PENDING_STRATEGIST_REVIEW", "STRATEGIST_APPROVED", "LEGAL_CHECK_IN_PROGRESS",
    "PENDING_REVIEWER_REVIEW", "REVIEWER_APPROVED", "REVIEWER_SKIPPED",
  ].includes(state))
    return "approval";
  if ([
    "COMPLIANCE_RULES_CHECK_IN_PROGRESS", "COMPLIANCE_RULES_FAILED",
    "STRATEGIST_RESOLVING", "COMPLIANCE_JUDGMENT_CHECK_IN_PROGRESS", "COMPLIANCE_PASSED",
  ].includes(state))
    return "compliance";
  return "publish";
}

export default function PipelineDashboard({ pipeline, role, onRefresh }: Props) {
  const progress = getProgress(pipeline.state);
  const panel = activePanel(pipeline.state);
  const stateColor = STATE_COLOR[pipeline.state] ?? "bg-github-blue";
  const stateLabel = STATE_LABELS[pipeline.state] ?? pipeline.state;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-github-surface border border-github-border rounded-lg p-4">
        <div className="flex items-start justify-between mb-3">
          <div>
            <h2 className="font-semibold text-github-text text-lg">{pipeline.brief?.title ?? "Untitled"}</h2>
            <p className="text-xs text-github-muted mt-0.5">
              {pipeline.brief?.content_type?.replace(/_/g, " ")} · <span className="font-mono">{pipeline.content_id.slice(0, 8)}…</span>
            </p>
          </div>
          <span className={`text-xs px-3 py-1 rounded-full text-white font-medium ${stateColor}`}>
            {stateLabel}
          </span>
        </div>

        <div className="w-full bg-github-dark rounded-full h-1.5 mb-1">
          <div
            className={`h-1.5 rounded-full transition-all duration-700 ${stateColor}`}
            style={{ width: `${progress}%` }}
          />
        </div>
        <div className="flex justify-between text-xs text-github-muted">
          <span>Brief</span>
          <span>{progress}%</span>
          <span>Published</span>
        </div>
      </div>

      {/* Pipeline alerts */}
      {pipeline.active_alerts.length > 0 && (
        <div className="space-y-2">
          {pipeline.active_alerts.map((a) => (
            <div
              key={a.alert_id}
              className={`p-3 rounded border text-sm ${
                a.severity === "critical" || a.severity === "urgent"
                  ? "border-github-red bg-red-900/20 text-red-400"
                  : a.severity === "warning"
                  ? "border-yellow-600 bg-yellow-900/20 text-yellow-400"
                  : "border-github-border text-github-muted"
              }`}
            >
              <span className="font-medium">{a.alert_type}</span>: {a.message}
            </div>
          ))}
        </div>
      )}

      {/* Active panel */}
      <div className="bg-github-surface border border-github-border rounded-lg p-4">
        {panel === "research" && <ResearchPanel pipeline={pipeline} onRefresh={onRefresh} />}
        {panel === "draft" && <DraftPanel pipeline={pipeline} onRefresh={onRefresh} />}
        {panel === "approval" && <ApprovalPanel pipeline={pipeline} role={role} onRefresh={onRefresh} />}
        {panel === "compliance" && <CompliancePanel pipeline={pipeline} role={role} onRefresh={onRefresh} />}
        {panel === "publish" && <PublishPanel pipeline={pipeline} role={role} onRefresh={onRefresh} />}
      </div>

      {/* Secondary view-only panels */}
      {panel !== "research" && pipeline.research && (
        <div className="bg-github-surface border border-github-border rounded-lg p-4">
          <ResearchPanel pipeline={pipeline} onRefresh={onRefresh} />
        </div>
      )}
      {!["research", "draft"].includes(panel) && pipeline.draft && (
        <div className="bg-github-surface border border-github-border rounded-lg p-4">
          <DraftPanel pipeline={pipeline} onRefresh={onRefresh} />
        </div>
      )}

      <AuditLog contentId={pipeline.content_id} />
    </div>
  );
}

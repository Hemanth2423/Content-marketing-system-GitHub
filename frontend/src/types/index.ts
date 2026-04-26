export type ContentType = "tutorial" | "announcement" | "thought_leadership" | "case_study";
export type PipelineState = string;
export type ApprovalStage = "strategist" | "reviewer" | "publisher";
export type ApprovalDecision = "approved" | "rejected" | "skipped";
export type AlertSeverity = "info" | "warning" | "urgent" | "critical";
export type AlertType =
  | "SLA_WARNING"
  | "SLA_URGENT"
  | "SLA_BREACH"
  | "AGENT_FAILURE"
  | "COMPLIANCE_FAILURE"
  | "PUBLISH_WINDOW_WARNING"
  | "PUBLISH_FAILURE";

export type UserRole = "strategist" | "reviewer" | "publisher" | "observer";

export interface BriefCreate {
  title: string;
  content_type: ContentType;
  target_audience: string;
  goal: string;
  requested_publish_date: string; // ISO string
  keywords: string[];
}

export interface BriefEnrichment {
  suggested_keywords: string[];
  audience_framing: string;
  content_angle: string;
  similar_past_content_ids: string[];
}

export interface Brief {
  brief_id: string;
  requester_id: string;
  title: string;
  content_type: ContentType;
  target_audience: string;
  goal: string;
  requested_publish_date: string;
  keywords: string[];
  enrichment?: BriefEnrichment;
  confirmed_at?: string;
  created_at: string;
  status: "DRAFT" | "CONFIRMED";
}

export interface EnrichResponse {
  brief_id: string;
  enrichment: BriefEnrichment;
  research_summary: {
    key_points: string[];
    suggested_angles: string[];
    low_context: boolean;
    source_count: number;
  };
  evaluation: string;
}

export interface EvaluationIssue {
  category: string;
  description: string;
  severity: "low" | "medium" | "high";
  suggestion?: string;
}

export interface Evaluation {
  result: "PASS" | "FAIL" | "INCONCLUSIVE";
  issues: EvaluationIssue[];
  confidence: number;
  summary?: string;
}

export interface LinkedInFormat {
  hook: string;
  body: string;
  cta: string;
  hashtags: string[];
  char_count: number;
}

export interface TwitterThread {
  tweet: string;
  char_count: number;
}

export interface TwitterFormat {
  thread: TwitterThread[];
  total_tweets: number;
}

export interface EmailFormat {
  subject: string;
  preview_text: string;
  body: string;
  cta_text: string;
  char_count: number;
}

export interface ChannelFormats {
  linkedin?: LinkedInFormat;
  twitter?: TwitterFormat;
  email?: EmailFormat;
  constraint_failures: string[];
}

export interface ResearchBrief {
  brief_id: string;
  key_points: string[];
  suggested_angles: string[];
  gaps: string[];
  sources: string[];
  retrieved_chunk_count: number;
  web_search_used: boolean;
  low_context: boolean;
  evaluation?: Evaluation;
}

export interface Draft {
  brief_id: string;
  revision: number;
  primary_draft: string;
  word_count: number;
  formats?: ChannelFormats;
  evaluation?: Evaluation;
}

export interface ApprovalEntry {
  stage: ApprovalStage;
  actor_id: string;
  decision: ApprovalDecision;
  timestamp: string;
  feedback?: string;
  skip_reason?: string;
}

export interface ApprovalLog {
  brief_id: string;
  stages: ApprovalEntry[];
}

export interface Alert {
  alert_id: string;
  content_id: string;
  alert_type: AlertType;
  severity: AlertSeverity;
  message: string;
  created_at: string;
  dismissed: boolean;
  dismissed_at?: string;
}

export interface AuditEntry {
  entry_id: string;
  content_id: string;
  event_type: string;
  timestamp: string;
  actor: string;
  actor_id?: string;
  payload: Record<string, unknown>;
  entry_hash: string;
}

export interface PipelineStatus {
  content_id: string;
  state: PipelineState;
  brief?: Brief;
  research?: ResearchBrief;
  draft?: Draft;
  approval_log: ApprovalLog;
  active_alerts: Alert[];
  revision_count: number;
  scheduled_datetime?: string;
  updated_at?: string;
  channel_results?: Record<string, { status: string; post_id?: string; error?: string; note?: string }>;
}

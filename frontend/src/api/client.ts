import axios from "axios";
import type {
  BriefCreate,
  Brief,
  EnrichResponse,
  PipelineStatus,
  ApprovalStage,
  Alert,
  AuditEntry,
} from "../types";

const http = axios.create({ baseURL: "/api" });

// Briefs
export const createBrief = (data: BriefCreate) =>
  http.post<{ brief_id: string; state: string }>("/briefs", data).then((r) => r.data);

export const getBrief = (id: string) =>
  http.get<Brief>(`/briefs/${id}`).then((r) => r.data);

export const enrichBrief = (id: string) =>
  http.post<EnrichResponse>(`/briefs/${id}/enrich`).then((r) => r.data);

export const confirmBrief = (id: string, requester_id = "requester") =>
  http.post(`/briefs/${id}/confirm`, { requester_id }).then((r) => r.data);

// Pipeline
export const getPipeline = (id: string) =>
  http.get<PipelineStatus>(`/pipeline/${id}`).then((r) => r.data);

export const runResearch = (id: string) =>
  http.post(`/pipeline/${id}/research`).then((r) => r.data);

export const runDraft = (id: string, body?: Record<string, string>) =>
  http.post(`/pipeline/${id}/draft`, body ?? {}).then((r) => r.data);

export const acceptLowContext = (id: string) =>
  http.post(`/pipeline/${id}/accept-low-context`).then((r) => r.data);

// Approvals — decision must be "approve" or "reject"
export const submitApproval = (
  id: string,
  stage: ApprovalStage,
  decision: "approve" | "reject",
  actor_id: string,
  feedback?: string
) =>
  http
    .post(`/approvals/${id}`, { stage, decision, actor_id, feedback })
    .then((r) => r.data);

export const resolveCompliance = (id: string, actor_id: string, manual_edit?: string) =>
  http
    .post(`/approvals/${id}/resolve-compliance`, { actor_id, resolution_type: "manual", manual_edit })
    .then((r) => r.data);

// Publish
export const confirmPublish = (
  id: string,
  scheduled_datetime: string,
  actor_id: string
) =>
  http
    .post(`/publish/${id}/confirm`, { scheduled_datetime, actor_id })
    .then((r) => r.data);

export const retryPublish = (id: string) =>
  http.post(`/publish/${id}/retry`).then((r) => r.data);

// Alerts
export const getAlerts = () =>
  http.get<{ alerts: Alert[] }>("/alerts").then((r) => r.data.alerts);

export const dismissAlert = (alertId: string) =>
  http.post(`/alerts/${alertId}/dismiss`).then((r) => r.data);

// Audit
export const getAuditLog = (id: string, stage?: string) =>
  http
    .get<{ entries: AuditEntry[]; count: number }>(
      `/audit/${id}${stage ? `?stage=${stage}` : ""}`
    )
    .then((r) => r.data);

export const verifyAuditChain = (id: string) =>
  http
    .get<{ chain_valid: boolean; broken_at_entry_id?: string }>(`/audit/${id}/verify`)
    .then((r) => r.data);

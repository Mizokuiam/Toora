/**
 * lib/api.ts — Typed fetch helpers for all Toora API routes.
 * All functions use the NEXT_PUBLIC_API_URL environment variable as the base URL.
 */

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${path} → ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

// ── Types ─────────────────────────────────────────────────────────────────────

export interface Integration {
  id: number;
  platform: string;
  status: string;
  connected_at: string | null;
}

export interface AgentStatus {
  status: "running" | "idle" | "waiting_for_approval";
  run_id: number | null;
  last_run: AgentRun | null;
}

export interface AgentRun {
  id: number;
  triggered_by: string;
  triggered_at: string;
  completed_at: string | null;
  status: string;
  summary: string | null;
}

export interface AgentConfig {
  enabled_tools: Record<string, boolean>;
  schedule: string;
  system_prompt: string | null;
  memory: string | null;
  approval_rules: Record<string, boolean>;
}

export interface ActionLog {
  id: number;
  run_id: number;
  tool_used: string;
  input_data: Record<string, unknown> | null;
  output_data: Record<string, unknown> | null;
  requires_approval: boolean;
  approval_status: string | null;
  timestamp: string;
}

export interface PaginatedLogs {
  items: ActionLog[];
  total: number;
  page: number;
  per_page: number;
}

export interface Approval {
  id: number;
  run_id: number;
  action_description: string;
  full_context: Record<string, unknown>;
  telegram_message_id: number | null;
  status: string;
  created_at: string;
  expires_at: string;
  resolved_at: string | null;
}

export interface TodayStats {
  emails_processed: number;
  tasks_created: number;
  approvals_pending: number;
  last_run_at: string | null;
}

// ── Integrations ──────────────────────────────────────────────────────────────

export const listIntegrations = () => apiFetch<Integration[]>("/api/integrations");

export const saveCredentials = (platform: string, credentials: Record<string, string>) =>
  apiFetch<Integration>(`/api/integrations/${platform}`, {
    method: "POST",
    body: JSON.stringify({ credentials }),
  });

export const disconnectIntegration = (platform: string) =>
  apiFetch<{ message: string }>(`/api/integrations/${platform}`, { method: "DELETE" });

export const testConnection = (platform: string) =>
  apiFetch<{ success: boolean; message: string }>(`/api/integrations/${platform}/test`, {
    method: "POST",
  });

export const registerTelegramWebhook = () =>
  apiFetch<{ message: string } | { error: string }>(
    "/api/integrations/telegram/register-webhook",
    { method: "POST" }
  );

// ── Agent ─────────────────────────────────────────────────────────────────────

export const runAgent = (input?: string) =>
  apiFetch<{ message: string }>("/api/agent/run", {
    method: "POST",
    body: JSON.stringify(input ? { input } : {}),
  });

export const getAgentStatus = () => apiFetch<AgentStatus>("/api/agent/status");

export const getAgentConfig = () => apiFetch<AgentConfig>("/api/agent/config");

export const updateAgentConfig = (config: Partial<AgentConfig>) =>
  apiFetch<AgentConfig>("/api/agent/config", {
    method: "PUT",
    body: JSON.stringify(config),
  });

// ── Logs ──────────────────────────────────────────────────────────────────────

export const getLogs = (params: {
  page?: number;
  per_page?: number;
  tool?: string;
  status?: string;
  date_from?: string;
  date_to?: string;
}) => {
  const qs = new URLSearchParams();
  if (params.page) qs.set("page", String(params.page));
  if (params.per_page) qs.set("per_page", String(params.per_page));
  if (params.tool) qs.set("tool", params.tool);
  if (params.status) qs.set("status", params.status);
  if (params.date_from) qs.set("date_from", params.date_from);
  if (params.date_to) qs.set("date_to", params.date_to);
  return apiFetch<PaginatedLogs>(`/api/logs?${qs}`);
};

export const getLog = (id: number) => apiFetch<ActionLog>(`/api/logs/${id}`);

// ── Approvals ─────────────────────────────────────────────────────────────────

export const getApprovals = (status?: string) => {
  const qs = status ? `?status=${status}` : "";
  return apiFetch<Approval[]>(`/api/approvals${qs}`);
};

export const approveAction = (id: number) =>
  apiFetch<Approval>(`/api/approvals/${id}/approve`, { method: "POST" });

export const rejectAction = (id: number) =>
  apiFetch<Approval>(`/api/approvals/${id}/reject`, { method: "POST" });

// ── Stats ─────────────────────────────────────────────────────────────────────

export const getTodayStats = () => apiFetch<TodayStats>("/api/stats/today");

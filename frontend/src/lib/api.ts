import { TicketInput, TriageResult, AccountBrief, OperationsSummary, SupportTicket, SupportAccount, Paginated } from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

/**
 * Submits a support ticket payload to the triage pipeline.
 */
export async function submitTriage(ticket: TicketInput): Promise<TriageResult> {
  const response = await fetch(`${API_BASE_URL}/triage`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(ticket),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Triage request failed with status ${response.status}`);
  }

  return response.json();
}

/**
 * Fetches the deterministic health signals and AI executive brief for an account.
 */
export async function fetchAccountBrief(accountId: string): Promise<AccountBrief> {
  const cleanId = encodeURIComponent(accountId.trim());
  const response = await fetch(`${API_BASE_URL}/accounts/${cleanId}/brief`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to fetch brief for ${accountId}`);
  }

  return response.json();
}

/**
 * Health check to verify FastAPI connection.
 */
export async function checkBackendHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, { cache: "no-store" });
    return response.ok;
  } catch {
    return false;
  }
}

type TicketFilters = { query?: string; status?: string; priority?: string; page?: number };
type AccountFilters = { query?: string; risk?: string; page?: number };

async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, { cache: "no-store", signal });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(typeof body.detail === "string" ? body.detail : `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export function fetchOperationsSummary(signal?: AbortSignal): Promise<OperationsSummary> {
  return getJson<OperationsSummary>("/operations/summary", signal);
}

export function fetchTicketQueue(filters: TicketFilters, signal?: AbortSignal): Promise<Paginated<SupportTicket>> {
  const params = new URLSearchParams({ page: String(filters.page || 1), page_size: "12" });
  if (filters.query?.trim()) params.set("query", filters.query.trim());
  if (filters.status) params.set("status", filters.status);
  if (filters.priority) params.set("priority", filters.priority);
  return getJson<Paginated<SupportTicket>>(`/operations/tickets?${params.toString()}`, signal);
}

export function fetchAccountQueue(filters: AccountFilters, signal?: AbortSignal): Promise<Paginated<SupportAccount>> {
  const params = new URLSearchParams({ page: String(filters.page || 1), page_size: "12" });
  if (filters.query?.trim()) params.set("query", filters.query.trim());
  if (filters.risk) params.set("risk", filters.risk);
  return getJson<Paginated<SupportAccount>>(`/operations/accounts?${params.toString()}`, signal);
}

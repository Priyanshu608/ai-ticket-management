import { TicketInput, TriageResult, AccountBrief } from "./types";

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
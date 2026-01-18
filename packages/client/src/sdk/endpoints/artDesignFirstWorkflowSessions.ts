// packages/client/src/sdk/endpoints/artDesignFirstWorkflowSessions.ts
/**
 * Art Design-First Workflow Sessions SDK (Bundle 32.7.7)
 *
 * SDK helpers for list/delete workflow sessions.
 */

import { apiFetch } from "@/sdk/core/apiFetch";
import type { DesignFirstSession } from "@/types/designFirstWorkflow";

export type WorkflowSessionSummary = {
  session_id: string;
  mode: string;
  state: "draft" | "in_review" | "approved" | "rejected";
  updated_at: string;
  created_at: string;
  risk_bucket?: string | null;
};

export type ListWorkflowSessionsResponse = {
  items: WorkflowSessionSummary[];
  next_cursor?: string | null;
};

export async function listRecentWorkflowSessions(
  limit = 50,
  cursor?: string
): Promise<ListWorkflowSessionsResponse> {
  const qs = new URLSearchParams();
  qs.set("limit", String(limit));
  if (cursor) qs.set("cursor", cursor);
  return apiFetch(`/art/design-first-workflow/sessions/recent?${qs.toString()}`, {
    method: "GET",
  });
}

export async function getWorkflowSession(
  sessionId: string
): Promise<{ session: DesignFirstSession }> {
  return apiFetch(
    `/art/design-first-workflow/sessions/${encodeURIComponent(sessionId)}`,
    { method: "GET" }
  );
}

export async function deleteWorkflowSession(
  sessionId: string
): Promise<{ ok: boolean; session_id: string }> {
  return apiFetch(
    `/art/design-first-workflow/sessions/${encodeURIComponent(sessionId)}`,
    { method: "DELETE" }
  );
}

// packages/client/src/api/rmos.ts
/**
 * RMOS 2.0 API client.
 *
 * Provides functions for interacting with RMOS endpoints:
 * - Mode preview (Directional Workflow 2.0)
 * - Constraint search
 * - Logs
 */

import type {
  ModePreviewRequest,
  ModePreviewResponse,
  ModesListResponse,
  ModeConstraints,
  ConstraintSearchRequest,
  ConstraintSearchResponse,
  RmosLogListResponse,
  RmosLogFilter,
} from "@/types/rmos";

const BASE_URL = "/api/rmos";

// ============================================================
// Mode Preview API
// ============================================================

/**
 * List all available workflow modes.
 */
export async function listModes(): Promise<ModesListResponse> {
  const response = await fetch(`${BASE_URL}/workflow/modes`);
  if (!response.ok) {
    throw new Error(`Failed to list modes: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Preview feasibility for a workflow mode.
 */
export async function previewMode(
  payload: ModePreviewRequest
): Promise<ModePreviewResponse> {
  const response = await fetch(`${BASE_URL}/workflow/mode/preview`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Mode preview failed: ${error}`);
  }
  return response.json();
}

/**
 * Get constraints for a specific mode.
 */
export async function getModeConstraints(
  modeId: string
): Promise<
  ModeConstraints & {
    mode: string;
    hard_limits: Record<string, number>;
    soft_limits: Record<string, number>;
    suggestions: string[];
  }
> {
  const response = await fetch(
    `${BASE_URL}/workflow/mode/${modeId}/constraints`
  );
  if (!response.ok) {
    throw new Error(`Failed to get constraints: ${response.statusText}`);
  }
  return response.json();
}

// ============================================================
// Constraint Search API
// ============================================================

/**
 * Search for feasible rosette designs given constraints.
 */
export async function searchConstraintFirst(
  params: ConstraintSearchRequest
): Promise<ConstraintSearchResponse> {
  const response = await fetch(`${BASE_URL}/constraint/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Constraint search failed: ${error}`);
  }
  return response.json();
}

// ============================================================
// Logs API
// ============================================================

/**
 * Fetch recent RMOS logs with optional filtering.
 */
export async function fetchRecentLogs(
  filter: RmosLogFilter = {}
): Promise<RmosLogListResponse> {
  const params = new URLSearchParams();

  if (filter.limit !== undefined) {
    params.set("limit", String(filter.limit));
  }
  if (filter.source) {
    params.set("source", filter.source);
  }
  if (filter.mode) {
    params.set("mode", filter.mode);
  }
  if (filter.riskBucket) {
    params.set("risk_bucket", filter.riskBucket);
  }

  const queryString = params.toString();
  const url = `${BASE_URL}/logs/recent${queryString ? `?${queryString}` : ""}`;

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch logs: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Export logs as CSV.
 * Returns the CSV content as a string.
 */
export async function exportLogsCsv(
  filter: RmosLogFilter = {}
): Promise<string> {
  const params = new URLSearchParams();

  if (filter.limit !== undefined) {
    params.set("limit", String(filter.limit));
  }
  if (filter.source) {
    params.set("source", filter.source);
  }
  if (filter.mode) {
    params.set("mode", filter.mode);
  }
  if (filter.riskBucket) {
    params.set("risk_bucket", filter.riskBucket);
  }

  const queryString = params.toString();
  const url = `${BASE_URL}/logs/export${queryString ? `?${queryString}` : ""}`;

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to export logs: ${response.statusText}`);
  }
  return response.text();
}

/**
 * Clear all logs (use with caution).
 */
export async function clearLogs(): Promise<{
  cleared: number;
  message: string;
}> {
  const response = await fetch(`${BASE_URL}/logs/clear`, {
    method: "DELETE",
  });
  if (!response.ok) {
    throw new Error(`Failed to clear logs: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Download logs as CSV file.
 */
export async function downloadLogsCsv(
  filter: RmosLogFilter = {}
): Promise<void> {
  const csv = await exportLogsCsv(filter);

  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = "rmos_logs.csv";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

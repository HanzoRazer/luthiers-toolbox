// packages/client/src/api/rmosRuns.ts
/**
 * RMOS Run Artifacts API Client
 *
 * Provides functions for interacting with run artifact endpoints:
 * - List runs (with filtering/pagination)
 * - Get run details
 * - Diff two runs
 * - Download run as JSON
 */

const BASE_URL = "/api/rmos/runs";

// =============================================================================
// Types
// =============================================================================

export interface RunIndexItem {
  run_id: string;
  created_at_utc: string;
  event_type: string;
  status: string;
  workflow_session_id?: string | null;
  tool_id?: string | null;
  material_id?: string | null;
  machine_id?: string | null;
  workflow_mode?: string | null;
  request_hash?: string | null;
  toolpaths_hash?: string | null;
  gcode_hash?: string | null;
  notes?: string | null;
}

export interface RunArtifactDetail {
  run_id: string;
  created_at_utc: string;
  workflow_session_id?: string | null;
  tool_id?: string | null;
  material_id?: string | null;
  machine_id?: string | null;
  workflow_mode?: string | null;
  toolchain_id?: string | null;
  post_processor_id?: string | null;
  geometry_ref?: string | null;
  geometry_hash?: string | null;
  event_type: string;
  status: string;
  feasibility?: Record<string, any> | null;
  request_hash?: string | null;
  toolpaths_hash?: string | null;
  gcode_hash?: string | null;
  attachments?: AttachmentSummary[];
  parent_run_id?: string | null;
  drift_detected?: boolean;
  drift_summary?: string | null;
  gate_decision?: string | null;
  engine_version?: string | null;
  toolchain_version?: string | null;
  config_fingerprint?: string | null;
  notes?: string | null;
  errors?: string[] | null;
}

export interface AttachmentSummary {
  sha256: string;
  kind: string;
  mime: string;
  filename: string;
  size_bytes: number;
  created_at_utc: string;
  download_url?: string;
}

export interface RunDiffResult {
  run_a: string;
  run_b: string;
  severity: "CRITICAL" | "WARNING" | "INFO" | "NONE";
  diffs: DiffEntry[];
  summary: string;
}

export interface DiffEntry {
  field: string;
  a_value: any;
  b_value: any;
  severity: "CRITICAL" | "WARNING" | "INFO";
  message?: string;
}

export interface FetchRunsParams {
  limit?: number;
  event_type?: string;
  status?: string;
  workflow_session_id?: string;
  tool_id?: string;
  material_id?: string;
  machine_id?: string;
}

// =============================================================================
// API Functions
// =============================================================================

/**
 * List run artifacts with optional filtering.
 */
export async function fetchRuns(params: FetchRunsParams = {}): Promise<RunIndexItem[]> {
  const query = new URLSearchParams();
  if (params.limit) query.set("limit", String(params.limit));
  if (params.event_type) query.set("event_type", params.event_type);
  if (params.status) query.set("status", params.status);
  if (params.workflow_session_id) query.set("workflow_session_id", params.workflow_session_id);
  if (params.tool_id) query.set("tool_id", params.tool_id);
  if (params.material_id) query.set("material_id", params.material_id);
  if (params.machine_id) query.set("machine_id", params.machine_id);

  const url = query.toString() ? `${BASE_URL}?${query}` : BASE_URL;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch runs: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Get full details of a single run artifact.
 */
export async function fetchRun(runId: string): Promise<RunArtifactDetail> {
  const response = await fetch(`${BASE_URL}/${runId}`);
  if (!response.ok) {
    if (response.status === 404) {
      throw new Error(`Run ${runId} not found`);
    }
    throw new Error(`Failed to fetch run: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Compute diff between two run artifacts.
 */
export async function fetchRunDiff(runIdA: string, runIdB: string): Promise<RunDiffResult> {
  const response = await fetch(`${BASE_URL}/diff?a=${encodeURIComponent(runIdA)}&b=${encodeURIComponent(runIdB)}`);
  if (!response.ok) {
    if (response.status === 404) {
      throw new Error(`One or both runs not found`);
    }
    throw new Error(`Failed to fetch diff: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Download run artifact as JSON file.
 */
export async function downloadRun(runId: string): Promise<void> {
  const run = await fetchRun(runId);
  const blob = new Blob([JSON.stringify(run, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `run_${runId}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/**
 * List attachments for a run.
 */
export async function fetchRunAttachments(runId: string): Promise<{
  run_id: string;
  count: number;
  attachments: AttachmentSummary[];
}> {
  const response = await fetch(`${BASE_URL}/${runId}/attachments`);
  if (!response.ok) {
    throw new Error(`Failed to fetch attachments: ${response.statusText}`);
  }
  return response.json();
}

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
 * Calls the runs_v2 diff endpoint and transforms to UI-friendly format.
 */
export async function fetchRunDiff(runIdA: string, runIdB: string): Promise<RunDiffResult> {
  const response = await fetch(`/api/rmos/runs_v2/diff/${encodeURIComponent(runIdA)}/${encodeURIComponent(runIdB)}`);
  if (!response.ok) {
    if (response.status === 404) {
      throw new Error(`One or both runs not found`);
    }
    throw new Error(`Failed to fetch diff: ${response.statusText}`);
  }
  
  // Transform raw diff response to UI format
  const raw = await response.json();
  const diffs: DiffEntry[] = [];
  
  // Helper to add diff entries from a diff dict
  const addDiffs = (diffDict: Record<string, { a: any; b: any }>, category: string, severity: "CRITICAL" | "WARNING" | "INFO") => {
    for (const [field, values] of Object.entries(diffDict || {})) {
      diffs.push({
        field: `${category}.${field}`,
        a_value: values.a,
        b_value: values.b,
        severity,
        message: `${field} differs between runs`,
      });
    }
  };
  
  // Decision diffs are most critical
  addDiffs(raw.decision_diff, "decision", "CRITICAL");
  // Feasibility diffs are warnings
  addDiffs(raw.feasibility_diff, "feasibility", "WARNING");
  // Request diffs are informational
  addDiffs(raw.request_diff, "request", "INFO");
  // Hash diffs are informational
  addDiffs(raw.hashes_diff, "hashes", "INFO");
  
  // Attachment diffs
  const attDiff = raw.attachments_diff || {};
  if (attDiff.only_in_a?.length) {
    diffs.push({
      field: "attachments.only_in_a",
      a_value: attDiff.only_in_a,
      b_value: null,
      severity: "INFO",
      message: `${attDiff.only_in_a.length} attachment(s) only in run A`,
    });
  }
  if (attDiff.only_in_b?.length) {
    diffs.push({
      field: "attachments.only_in_b",
      a_value: null,
      b_value: attDiff.only_in_b,
      severity: "INFO",
      message: `${attDiff.only_in_b.length} attachment(s) only in run B`,
    });
  }
  
  // Compute overall severity
  let severity: "CRITICAL" | "WARNING" | "INFO" | "NONE" = "NONE";
  if (diffs.some(d => d.severity === "CRITICAL")) severity = "CRITICAL";
  else if (diffs.some(d => d.severity === "WARNING")) severity = "WARNING";
  else if (diffs.length > 0) severity = "INFO";
  
  // Generate summary
  const summary = diffs.length === 0
    ? "Runs are identical"
    : `Found ${diffs.length} difference(s) across request, feasibility, decision, and attachments`;
  
  return {
    run_a: raw.run_a,
    run_b: raw.run_b,
    severity,
    diffs,
    summary,
  };
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

// =============================================================================
// Advisory Variants (Product Surface)
// =============================================================================

export type VariantStatus = "NEW" | "REVIEWED" | "PROMOTED" | "REJECTED";

export type RiskLevel = "GREEN" | "YELLOW" | "RED" | "UNKNOWN" | "ERROR";

export interface AdvisoryVariantSummary {
  advisory_id: string;               // sha256 (CAS key)
  created_at_utc?: string | null;    // optional; if backend provides
  risk_level?: RiskLevel | null;     // optional
  rating?: number | null;            // optional (1-5)
  notes?: string | null;             // optional (if included)
  status?: VariantStatus | null;     // preferred (server-derived), optional
  promoted_candidate_id?: string | null; // optional
  rejected?: boolean | null;         // optional
  has_preview?: boolean | null;      // optional

  // Rejection details (Undo Reject bundle)
  rejection_reason_code?: string | null;
  rejection_reason_detail?: string | null;
  rejection_operator_note?: string | null;
  rejected_at_utc?: string | null;
}

export interface AdvisoryVariantListResponse {
  items: AdvisoryVariantSummary[];
}

/**
 * List advisory variants for a run.
 * Tolerates both {items:[...]} and [...] response shapes.
 */
export async function listAdvisoryVariants(runId: string): Promise<AdvisoryVariantSummary[]> {
  const res = await fetch(`${BASE_URL}/${encodeURIComponent(runId)}/advisory/variants`, {
    method: "GET",
    headers: { "Accept": "application/json" },
  });
  if (!res.ok) throw new Error(`Failed to load variants (${res.status})`);
  const data = (await res.json()) as any;

  // tolerate both shapes: {items:[...]} or [...]
  const items = Array.isArray(data) ? data : Array.isArray(data?.items) ? data.items : [];
  return items.map((v: any) => ({
    advisory_id: String(v.advisory_id ?? v.advisoryId ?? v.sha256 ?? ""),
    created_at_utc: v.created_at_utc ?? v.createdAt ?? null,
    risk_level: (v.risk_level ?? v.riskLevel ?? null) as RiskLevel | null,
    rating: v.rating ?? null,
    notes: v.notes ?? v.note ?? null,
    status: (v.status ?? null) as VariantStatus | null,
    promoted_candidate_id: v.promoted_candidate_id ?? v.promotedCandidateId ?? null,
    rejected: v.rejected ?? null,
    has_preview: v.has_preview ?? v.hasPreview ?? null,
    rejection_reason_code: v.rejection_reason_code ?? null,
    rejection_reason_detail: v.rejection_reason_detail ?? null,
    rejection_operator_note: v.rejection_operator_note ?? null,
    rejected_at_utc: v.rejected_at_utc ?? null,
  })).filter((x: AdvisoryVariantSummary) => !!x.advisory_id);
}

// =============================================================================
// Variant Rejection (Product Surface)
// =============================================================================

export type RejectReasonCode =
  | "GEOMETRY_UNSAFE"
  | "TEXT_REQUIRES_OUTLINE"
  | "AESTHETIC"
  | "DUPLICATE"
  | "OTHER";

export interface RejectVariantRequest {
  reason_code: RejectReasonCode;
  reason_detail?: string | null;
  operator_note?: string | null;
}

export interface AdvisoryVariantRejectionRecord {
  run_id: string;
  advisory_id: string;
  rejected_at_utc: string;
  reason_code: RejectReasonCode;
  reason_detail?: string | null;
  operator_note?: string | null;
}

/**
 * Reject an advisory variant with a reason code.
 * Returns the persisted rejection record.
 */
export async function rejectAdvisoryVariant(
  runId: string,
  advisoryId: string,
  payload: RejectVariantRequest
): Promise<AdvisoryVariantRejectionRecord> {
  const res = await fetch(
    `${BASE_URL}/${encodeURIComponent(runId)}/advisory/${encodeURIComponent(advisoryId)}/reject`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(payload),
    }
  );
  if (!res.ok) throw new Error(`Reject failed (${res.status})`);
  return (await res.json()) as AdvisoryVariantRejectionRecord;
}

/**
 * Undo/clear a rejection for an advisory variant.
 * Returns whether a rejection was cleared.
 */
export async function unrejectAdvisoryVariant(
  runId: string,
  advisoryId: string
): Promise<{ run_id: string; advisory_id: string; cleared: boolean }> {
  const res = await fetch(
    `${BASE_URL}/${encodeURIComponent(runId)}/advisory/${encodeURIComponent(advisoryId)}/unreject`,
    { method: "POST", headers: { Accept: "application/json" } }
  );
  if (!res.ok) throw new Error(`Unreject failed (${res.status})`);
  return (await res.json()) as { run_id: string; advisory_id: string; cleared: boolean };
}

// =============================================================================
// Bulk Promote (Product Surface)
// =============================================================================

export interface BulkPromoteRequest {
  advisory_ids: string[];
  label?: string | null;
  note?: string | null;
}

export interface BulkPromoteItemResult {
  advisory_id: string;
  success: boolean;
  decision?: "ALLOW" | "BLOCK" | null;
  risk_level?: "GREEN" | "YELLOW" | "RED" | null;
  score?: number | null;
  reason?: string | null;
  manufactured_candidate_id?: string | null;
  error?: string | null;
}

export interface BulkPromoteResponse {
  run_id: string;
  total: number;
  succeeded: number;
  failed: number;
  blocked: number;
  results: BulkPromoteItemResult[];
}

/**
 * Bulk-promote multiple advisory variants to manufacturing candidates.
 * Returns aggregate statistics and per-item results.
 */
export async function bulkPromoteAdvisoryVariants(
  runId: string,
  payload: BulkPromoteRequest
): Promise<BulkPromoteResponse> {
  const res = await fetch(
    `${BASE_URL}/${encodeURIComponent(runId)}/advisory/bulk-promote`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(payload),
    }
  );
  if (!res.ok) throw new Error(`Bulk promote failed (${res.status})`);
  return (await res.json()) as BulkPromoteResponse;
}

// -----------------------------------------------------------------------------
// Advisory Variant Promote API (single-item, product surface)
// -----------------------------------------------------------------------------

export async function promoteAdvisoryVariant(
  apiBase: string,
  runId: string,
  advisoryId: string
): Promise<any> {
  const url =
    `${apiBase}/rmos/runs/${encodeURIComponent(runId)}` +
    `/advisory/${encodeURIComponent(advisoryId)}/promote`;

  const res = await fetch(url, {
    method: "POST",
    headers: { "Accept": "application/json" },
  });
  if (!res.ok) throw new Error(`Promote failed (${res.status})`);
  return await res.json();
}

// -----------------------------------------------------------------------------
// Manufacturing candidate downloads
// -----------------------------------------------------------------------------

export async function downloadManufacturingCandidateZip(
  apiBase: string,
  runId: string,
  candidateId: string
): Promise<Blob> {
  const url =
    `${apiBase}/rmos/runs/${encodeURIComponent(runId)}` +
    `/manufacturing/candidates/${encodeURIComponent(candidateId)}/download-zip`;

  const res = await fetch(url, { method: "GET" });
  if (!res.ok) throw new Error(`Candidate zip download failed (${res.status})`);
  return await res.blob();
}

// Utility: trigger browser save dialog
export function saveBlobToDisk(blob: Blob, filename: string) {
  const a = document.createElement("a");
  const url = URL.createObjectURL(blob);
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

// -----------------------------------------------------------------------------
// Manufacturing candidates (list + decision)
// -----------------------------------------------------------------------------

export type CandidateDecision = "GREEN" | "YELLOW" | "RED";

export type ManufacturingCandidate = {
  candidate_id: string;
  advisory_id?: string | null;

  // optional fields (backend may include some/all)
  score?: number | null;
  risk_level?: "GREEN" | "YELLOW" | "RED" | "UNKNOWN" | "ERROR" | null;
  created_at_utc?: string | null;

  // decision state
  decision?: CandidateDecision | null;  // if backend uses decision
  status?: "PROPOSED" | "ACCEPTED" | "REJECTED" | null; // legacy field
  decision_note?: string | null;
  decided_at_utc?: string | null;

  // audit fields (optional - used for decision history hover)
  decided_by?: string | null;
  decision_history?: Array<{
    decision: CandidateDecision;
    note?: string | null;
    decided_at_utc?: string | null;
    decided_by?: string | null;
  }> | null;
};

export async function fetchManufacturingCandidates(
  apiBase: string,
  runId: string
): Promise<ManufacturingCandidate[]> {
  const url =
    `${apiBase}/rmos/runs/${encodeURIComponent(runId)}` +
    `/manufacturing/candidates`;

  const res = await fetch(url, { method: "GET", headers: { "Accept": "application/json" } });
  if (!res.ok) throw new Error(`Fetch candidates failed (${res.status})`);
  const data = await res.json();
  // Handle { items: [...] } wrapper or raw array
  return Array.isArray(data) ? data : (data?.items ?? []);
}

export async function setManufacturingCandidateDecision(
  apiBase: string,
  runId: string,
  candidateId: string,
  payload: { decision: CandidateDecision; note?: string | null }
): Promise<any> {
  const url =
    `${apiBase}/rmos/runs/${encodeURIComponent(runId)}` +
    `/manufacturing/candidates/${encodeURIComponent(candidateId)}/decision`;

  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json", "Accept": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Set decision failed (${res.status})`);
  return await res.json();
}

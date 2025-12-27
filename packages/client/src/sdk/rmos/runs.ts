/**
 * RMOS Runs Client
 *
 * Type-safe client for /api/rmos/runs endpoints (runs_v2 store).
 */

import { get, post, patch } from "../core/apiFetch";
import type { ApiFetchOptions, PaginatedResponse, Timestamped, IndexedEntity } from "../core/types";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/** Lite run artifact for list views */
export type RunArtifactLite = Timestamped & IndexedEntity & {
  run_id: string;
  status: string;
  event_type?: string;
  workflow_session_id?: string | null;
  mode?: string;
};

/** Full run artifact with all fields */
export type RunArtifact = RunArtifactLite & {
  request_summary?: Record<string, unknown>;
  feasibility?: Record<string, unknown>;
  decision?: RunDecision;
  hashes?: RunHashes;
  outputs?: RunOutputs;
  provenance?: RunProvenance;
  meta?: Record<string, unknown>;
};

export type RunDecision = {
  risk_level: string;
  score?: number | null;
  warnings?: string[];
  block_reason?: string | null;
  details?: Record<string, unknown>;
};

export type RunHashes = {
  feasibility_sha256: string;
  toolpaths_sha256?: string | null;
  gcode_sha256?: string | null;
  opplan_sha256?: string | null;
  snapshot_sha256?: string | null;
};

export type RunOutputs = {
  gcode_text?: string | null;
  opplan_text?: string | null;
};

export type RunProvenance = {
  created_by?: string;
  request_id?: string | null;
  git_sha?: string | null;
  git_branch?: string | null;
  ci_job_id?: string | null;
};

/** Attachment metadata */
export type RunAttachment = {
  attachment_id: string;
  sha256: string;
  kind: string;
  filename: string;
  mime_type: string;
  byte_size: number;
  created_at_utc: string;
};

/** Signed URL for attachment download */
export type SignedAttachment = RunAttachment & {
  signed_url?: string;
};

// ---------------------------------------------------------------------------
// List/Query Parameters
// ---------------------------------------------------------------------------

export type ListRunsParams = {
  limit?: number;
  offset?: number;
  event_type?: string;
  status?: string;
  workflow_session_id?: string;
  tool_id?: string;
  material_id?: string;
  machine_id?: string;
  include_total?: boolean;
  cursor?: string;
};

export type ListRunsResponse = PaginatedResponse<RunArtifactLite>;

export type ListAttachmentsParams = {
  signed?: boolean;
  ttl?: number;
};

export type SignedBatchRequest = {
  sha256s: string[];
  ttl?: number;
  include_kinds?: string[];
  exclude_kinds?: string[];
  kind_prefixes?: string[];
};

export type SignedBatchResponse = {
  signed: SignedAttachment[];
  skipped_filtered: number;
  skipped_invalid_sha: number;
  skipped_not_found: number;
  included_sha256s: string[];
};

// ---------------------------------------------------------------------------
// API Functions
// ---------------------------------------------------------------------------

/**
 * List runs with optional filters.
 */
export async function listRuns(
  params: ListRunsParams = {},
  opts?: ApiFetchOptions
): Promise<ListRunsResponse> {
  const qs = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v === undefined || v === null) return;
    qs.set(k, String(v));
  });
  const q = qs.toString();
  return get<ListRunsResponse>(`/rmos/runs${q ? `?${q}` : ""}`, opts);
}

/**
 * Get a single run by ID.
 */
export async function getRun(
  runId: string,
  opts?: ApiFetchOptions
): Promise<RunArtifact> {
  return get<RunArtifact>(`/rmos/runs/${encodeURIComponent(runId)}`, opts);
}

/**
 * Get recent runs (convenience alias).
 */
export async function getRecentRuns(
  limit = 50,
  opts?: ApiFetchOptions
): Promise<ListRunsResponse> {
  return get<ListRunsResponse>(`/rmos/runs/recent?limit=${limit}`, opts);
}

/**
 * Patch run metadata.
 */
export async function patchRunMeta(
  runId: string,
  meta: Record<string, unknown>,
  opts?: ApiFetchOptions
): Promise<RunArtifact> {
  return patch<RunArtifact>(
    `/rmos/runs/${encodeURIComponent(runId)}/meta`,
    { meta },
    opts
  );
}

/**
 * Get run metadata.
 */
export async function getRunMeta(
  runId: string,
  opts?: ApiFetchOptions
): Promise<Record<string, unknown>> {
  return get<Record<string, unknown>>(
    `/rmos/runs/${encodeURIComponent(runId)}/meta`,
    opts
  );
}

/**
 * List attachments for a run.
 */
export async function listAttachments(
  runId: string,
  params: ListAttachmentsParams = {},
  opts?: ApiFetchOptions
): Promise<{ attachments: SignedAttachment[] }> {
  const qs = new URLSearchParams();
  if (params.signed) qs.set("signed", "1");
  if (params.ttl) qs.set("ttl", String(params.ttl));
  const q = qs.toString();
  return get<{ attachments: SignedAttachment[] }>(
    `/rmos/runs/${encodeURIComponent(runId)}/attachments${q ? `?${q}` : ""}`,
    opts
  );
}

/**
 * Get signed URLs for multiple attachments (bulk pre-signing).
 */
export async function signedBatch(
  runId: string,
  request: SignedBatchRequest,
  opts?: ApiFetchOptions
): Promise<SignedBatchResponse> {
  return post<SignedBatchResponse>(
    `/rmos/runs/${encodeURIComponent(runId)}/attachments/signed-batch`,
    request,
    opts
  );
}

/**
 * Download run as JSON.
 */
export function getRunDownloadUrl(runId: string, baseUrl = "/api"): string {
  return `${baseUrl}/rmos/runs/${encodeURIComponent(runId)}/download`;
}

/**
 * Get attachment download URL.
 */
export function getAttachmentDownloadUrl(
  runId: string,
  attachmentId: string,
  baseUrl = "/api"
): string {
  return `${baseUrl}/rmos/runs/${encodeURIComponent(runId)}/attachments/${encodeURIComponent(attachmentId)}/download`;
}

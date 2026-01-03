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

// ---------------------------------------------------------------------------
// Advisory Variants (H8.3-compliant: co-located types + requestId returns)
// ---------------------------------------------------------------------------

import { getRaw, postRaw } from "../core/apiFetchRaw";

/** Variant triage status */
export type VariantStatus = "NEW" | "REVIEWED" | "PROMOTED" | "REJECTED";

/** Risk levels for quick triage */
export type RiskLevel = "GREEN" | "YELLOW" | "RED";

/** Rejection reason vocabulary */
export type RejectReasonCode =
  | "GEOMETRY_UNSAFE"
  | "TEXT_REQUIRES_OUTLINE"
  | "AESTHETIC"
  | "DUPLICATE"
  | "OTHER";

/** Advisory variant summary for listing */
export type AdvisoryVariantSummary = {
  advisory_id: string;

  // blob-ish fields (present when variant is tied to a blob)
  mime?: string | null;
  filename?: string | null;
  size_bytes?: number | null;

  // preview policy fields (if present)
  has_preview?: boolean | null;
  preview_blocked?: boolean | null;
  preview_block_reason?: string | null;

  // review fields
  rating?: number | null;
  notes?: string | null;

  // state
  promoted?: boolean | null;
  promoted_candidate_id?: string | null;
  status?: VariantStatus | null;
  risk_level?: RiskLevel | "UNKNOWN" | "ERROR" | null;

  // rejection fields
  rejected?: boolean | null;
  rejection_reason_code?: RejectReasonCode | string | null;
  rejection_reason_detail?: string | null;
  rejection_operator_note?: string | null;
  rejected_at_utc?: string | null;

  // timestamps
  created_at_utc?: string | null;
  updated_at_utc?: string | null;
};

export type AdvisoryVariantListResponse = {
  items: AdvisoryVariantSummary[];
  count: number;
  run_id?: string;
};

export type AdvisoryVariantReviewRecord = {
  advisory_id: string;
  status?: VariantStatus | null;
  rating?: number | null;
  notes?: string | null;

  rejected?: boolean | null;
  rejection_reason_code?: RejectReasonCode | string | null;
  rejection_reason_detail?: string | null;
  rejection_operator_note?: string | null;
  rejected_at_utc?: string | null;

  updated_at_utc?: string | null;
  updated_by?: string | null;
};

export type AdvisoryVariantReviewRequest = {
  // Core review
  rating?: number | null;
  notes?: string | null;

  // Status transitions (server may set status automatically; keep optional)
  status?: VariantStatus | null;

  // Rejection controls (pairs with reason codes)
  rejected?: boolean | null;
  rejection_reason_code?: RejectReasonCode | null;
  rejection_reason_detail?: string | null;
  rejection_operator_note?: string | null;

  // Optional: explicit risk_level update if your backend allows it
  risk_level?: RiskLevel | null;
};

export type PromoteVariantResponse = {
  run_id: string;
  advisory_id: string;
  candidate_id?: string | null;
  promoted_candidate_id?: string | null;
  // backend may include updated summary
  variant?: AdvisoryVariantSummary | null;
};

// ---------------------------------------------------------------------------
// Advisory Variant Helpers (with requestId)
// ---------------------------------------------------------------------------

function reqId(response: Response): string {
  return response.headers.get("x-request-id") || "";
}

function enc(s: string): string {
  return encodeURIComponent(s);
}

/** List reviewable advisory variants for a run */
export async function listAdvisoryVariants(
  runId: string,
  opts?: ApiFetchOptions
): Promise<AdvisoryVariantListResponse & { requestId: string }> {
  const { data, response } = await getRaw<AdvisoryVariantListResponse>(
    `/rmos/runs/${enc(runId)}/advisory/variants`,
    opts
  );
  return { ...data, requestId: reqId(response) };
}

/** Review / update a variant (rating/notes/reject fields) */
export async function reviewAdvisoryVariant(
  runId: string,
  advisoryId: string,
  payload: AdvisoryVariantReviewRequest,
  opts?: ApiFetchOptions
): Promise<AdvisoryVariantReviewRecord & { requestId: string }> {
  const { data, response } = await postRaw<AdvisoryVariantReviewRecord>(
    `/rmos/runs/${enc(runId)}/advisory/${enc(advisoryId)}/review`,
    payload,
    opts
  );
  return { ...data, requestId: reqId(response) };
}

/** Promote a variant to a manufacturing candidate */
export async function promoteAdvisoryVariant(
  runId: string,
  advisoryId: string,
  opts?: ApiFetchOptions
): Promise<PromoteVariantResponse & { requestId: string }> {
  const { data, response } = await postRaw<PromoteVariantResponse>(
    `/rmos/runs/${enc(runId)}/advisory/${enc(advisoryId)}/promote`,
    {},
    opts
  );
  return { ...data, requestId: reqId(response) };
}

/** Bulk review advisory variants with shared reason (e.g., bulk reject) */
export type BulkReviewAdvisoryVariantsRequest = {
  advisory_ids: string[];
  rejected?: boolean | null;
  rejection_reason_code?: RejectReasonCode | null;
  rejection_reason_detail?: string | null;
  rejection_operator_note?: string | null;
  status?: VariantStatus | null;
  rating?: number | null;
  notes?: string | null;
};

export type BulkReviewAdvisoryVariantsResponse = {
  updated_count: number;
  advisory_ids: string[];
};

export async function bulkReviewAdvisoryVariants(
  runId: string,
  payload: BulkReviewAdvisoryVariantsRequest,
  opts?: ApiFetchOptions
): Promise<BulkReviewAdvisoryVariantsResponse & { requestId: string }> {
  const { data, response } = await postRaw<BulkReviewAdvisoryVariantsResponse>(
    `/rmos/runs/${enc(runId)}/advisory/bulk-review`,
    payload,
    opts
  );
  return { ...data, requestId: reqId(response) };
}

// ---------------------------------------------------------------------------
// Advisory Blobs (CAS)
// ---------------------------------------------------------------------------

export type AdvisoryBlobSummary = {
  sha256: string;
  mime?: string | null;
  filename?: string | null;
  size_bytes?: number | null;
  // optional preview policy
  preview_blocked?: boolean | null;
  preview_block_reason?: string | null;
};

export type AdvisoryBlobListResponse = {
  items: AdvisoryBlobSummary[];
  count: number;
  run_id?: string;
};

export async function listAdvisoryBlobs(
  runId: string,
  opts?: ApiFetchOptions
): Promise<AdvisoryBlobListResponse & { requestId: string }> {
  const { data, response } = await getRaw<AdvisoryBlobListResponse>(
    `/rmos/runs/${enc(runId)}/advisory/blobs`,
    opts
  );
  return { ...data, requestId: reqId(response) };
}

/**
 * Download a single advisory blob (raw bytes)
 */
export async function downloadAdvisoryBlob(
  runId: string,
  sha256: string,
  opts?: ApiFetchOptions
): Promise<{ blob: Blob; requestId: string }> {
  const { response } = await getRaw<unknown>(
    `/rmos/runs/${enc(runId)}/advisory/blobs/${enc(sha256)}/download`,
    opts
  );
  const b = await response.blob();
  return { blob: b, requestId: reqId(response) };
}

/** Download-all ZIP (server-produced) */
export async function downloadAllAdvisoryBlobsZip(
  runId: string,
  opts?: ApiFetchOptions
): Promise<{ blob: Blob; requestId: string }> {
  const { response } = await getRaw<unknown>(
    `/rmos/runs/${enc(runId)}/advisory/blobs/download-all.zip`,
    opts
  );
  const b = await response.blob();
  return { blob: b, requestId: reqId(response) };
}

// ---------------------------------------------------------------------------
// Manufacturing Candidates
// ---------------------------------------------------------------------------

export type ManufacturingCandidateDecision = RiskLevel | null;

export type ManufacturingCandidateStatus = "PROPOSED" | "ACCEPTED" | "REJECTED";

export type ManufacturingCandidateDecisionHistoryItem = {
  decision: RiskLevel;
  note?: string | null;
  decided_at_utc?: string | null;
  decided_by?: string | null;
};

export type ManufacturingCandidate = {
  candidate_id: string;

  advisory_id?: string | null;
  score?: number | null;
  risk_level?: RiskLevel | "UNKNOWN" | "ERROR" | null;

  created_at_utc?: string | null;

  // Decision protocol (canonical): null until operator decides
  decision?: ManufacturingCandidateDecision; // "GREEN" | "YELLOW" | "RED" | null
  status?: ManufacturingCandidateStatus | null;

  decision_note?: string | null;
  decided_at_utc?: string | null;
  decided_by?: string | null;

  decision_history?: ManufacturingCandidateDecisionHistoryItem[] | null;
};

export type CandidateListResponse = {
  items: ManufacturingCandidate[];
  count: number;
  run_id?: string;
};

export type DecideManufacturingCandidateRequest = {
  decision: RiskLevel | null; // allow explicit null if you support "clear decision"
  note?: string | null;
  decided_by?: string | null; // optional; backend may derive from auth/session
};

export type DecideManufacturingCandidateResponse = {
  run_id?: string;
  candidate_id: string;
  decision?: RiskLevel | null;
  status?: ManufacturingCandidateStatus | null;
  decision_note?: string | null;
  decided_at_utc?: string | null;
  decided_by?: string | null;
  decision_history?: ManufacturingCandidateDecisionHistoryItem[] | null;
};

// ---------------------------------------------------------------------------
// Manufacturing Candidate Functions (with requestId)
// ---------------------------------------------------------------------------

export async function listManufacturingCandidates(
  runId: string,
  opts?: ApiFetchOptions
): Promise<CandidateListResponse & { requestId: string }> {
  const { data, response } = await getRaw<CandidateListResponse>(
    `/rmos/runs/${enc(runId)}/manufacturing/candidates`,
    opts
  );
  return { ...data, requestId: reqId(response) };
}

export async function decideManufacturingCandidate(
  runId: string,
  candidateId: string,
  payload: DecideManufacturingCandidateRequest,
  opts?: ApiFetchOptions
): Promise<DecideManufacturingCandidateResponse & { requestId: string }> {
  const { data, response } = await postRaw<DecideManufacturingCandidateResponse>(
    `/rmos/runs/${enc(runId)}/manufacturing/candidates/${enc(candidateId)}/decision`,
    payload,
    opts
  );
  return { ...data, requestId: reqId(response) };
}

/** Download a single candidate zip */
export async function downloadManufacturingCandidateZip(
  runId: string,
  candidateId: string,
  opts?: ApiFetchOptions
): Promise<{ blob: Blob; requestId: string }> {
  const { response } = await getRaw<unknown>(
    `/rmos/runs/${enc(runId)}/manufacturing/candidates/${enc(candidateId)}/download-zip`,
    opts
  );
  const b = await response.blob();
  return { blob: b, requestId: reqId(response) };
}

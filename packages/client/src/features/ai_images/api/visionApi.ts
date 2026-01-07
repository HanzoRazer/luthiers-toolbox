/**
 * Vision API Client — Canonical Phase B Endpoints
 *
 * Calls the canonical /api/vision/* and /api/rmos/runs/{id}/advisory/* endpoints.
 * Implements the hybrid architecture:
 * - Vision (Producer Plane): Generate assets, get sha256
 * - Advisory (Ledger Plane): Attach sha256 to runs, review, promote
 *
 * @package features/ai_images/api
 */

// ---------------------------------------------------------------------------
// RMOS Runs helpers (used by AiImageGallery auto-create on attach)
// ---------------------------------------------------------------------------

export type CreateRunRequest = {
  /** Recommended default for this flow: "vision_image_review" */
  event_type?: string;
  mode?: string;
  tool_id?: string;
  status?: string;
};

export type CreateRunResponse = {
  run_id: string;
};

/**
 * Create a new RMOS run (canonical backend endpoint).
 * POST /api/rmos/runs
 */
export async function createRun(
  request: CreateRunRequest = {}
): Promise<CreateRunResponse> {
  const r = await fetch("/api/rmos/runs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!r.ok) {
    const text = await r.text().catch(() => "");
    throw new Error(`createRun failed (${r.status}): ${text || r.statusText}`);
  }
  return (await r.json()) as CreateRunResponse;
}

// =============================================================================
// TYPES
// =============================================================================

export type ProviderName = "openai" | "stub";

export interface VisionGenerateRequest {
  prompt: string;
  provider?: ProviderName;
  model?: string;
  size?: string;
  quality?: string;
  num_images?: number;
  meta?: Record<string, unknown>;
}

export interface VisionAsset {
  sha256: string;
  url: string;
  mime: string;
  filename: string;
  size_bytes: number;
  provider: string;
  model: string;
  revised_prompt?: string;
  request_id: string;
}

export interface VisionGenerateResponse {
  assets: VisionAsset[];
  request_id: string;
}

export interface VisionProvider {
  name: string;
  configured: boolean;
}

export interface VisionProvidersResponse {
  providers: VisionProvider[];
}

export interface AdvisoryAttachRequest {
  advisory_id: string;
  kind?: "advisory" | "explanation" | "note";
  mime?: string;
  filename?: string;
  size_bytes?: number;
}

export interface AdvisoryAttachResponse {
  run_id: string;
  advisory_id: string;
  attached: boolean;
  message: string;
}

export type VariantStatus = "NEW" | "REVIEWED" | "PROMOTED" | "REJECTED";
export type RiskLevel = "GREEN" | "YELLOW" | "RED" | "UNKNOWN" | "ERROR";
export type RejectReasonCode =
  | "GEOMETRY_UNSAFE"
  | "TEXT_REQUIRES_OUTLINE"
  | "AESTHETIC"
  | "DUPLICATE"
  | "OTHER";

export interface AdvisoryReviewRequest {
  rejected?: boolean;
  rejection_reason_code?: RejectReasonCode;
  rejection_reason_detail?: string;
  rejection_operator_note?: string;
  status?: VariantStatus;
  rating?: number;
  notes?: string;
  risk_level?: RiskLevel;
}

export interface AdvisoryReviewRecord {
  run_id: string;
  advisory_id: string;
  status: VariantStatus;
  rejected: boolean;
  rating?: number;
  notes?: string;
  risk_level?: RiskLevel;
  rejection_reason_code?: RejectReasonCode;
  rejection_reason_detail?: string;
  rejection_operator_note?: string;
  rejected_at_utc?: string;
  updated_at_utc?: string;
}

export interface PromoteResponse {
  run_id: string;
  advisory_id: string;
  promoted: boolean;
  promoted_candidate_id?: string;
}

// =============================================================================
// API ERROR
// =============================================================================

export class VisionApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string
  ) {
    super(message);
    this.name = "VisionApiError";
  }
}

// =============================================================================
// FETCH HELPERS
// =============================================================================

const DEFAULT_TIMEOUT_MS = 10000;
const GENERATION_TIMEOUT_MS = 120000; // 2 min for image generation

async function fetchJson<T>(
  url: string,
  options: RequestInit & { timeout?: number } = {}
): Promise<T> {
  const { timeout = DEFAULT_TIMEOUT_MS, ...fetchOptions } = options;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...fetchOptions,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        ...fetchOptions.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new VisionApiError(
        error.detail || error.message || `HTTP ${response.status}`,
        response.status,
        error.code
      );
    }

    return response.json();
  } finally {
    clearTimeout(timeoutId);
  }
}

// =============================================================================
// VISION (PRODUCER PLANE) API
// =============================================================================

/**
 * List available AI image providers.
 */
export async function getProviders(): Promise<VisionProvidersResponse> {
  return fetchJson<VisionProvidersResponse>("/api/vision/providers");
}

/**
 * Generate images via AI provider.
 * Returns assets with sha256 identities for subsequent attachment.
 */
export async function generateImages(
  request: VisionGenerateRequest
): Promise<VisionGenerateResponse> {
  return fetchJson<VisionGenerateResponse>("/api/vision/generate", {
    method: "POST",
    body: JSON.stringify(request),
    timeout: GENERATION_TIMEOUT_MS,
  });
}

// =============================================================================
// ADVISORY (LEDGER PLANE) API
// =============================================================================

/**
 * Attach a Vision-generated advisory (by sha256) to an RMOS run.
 */
export async function attachAdvisoryToRun(
  runId: string,
  request: AdvisoryAttachRequest
): Promise<AdvisoryAttachResponse> {
  return fetchJson<AdvisoryAttachResponse>(
    `/api/rmos/runs/${runId}/advisory/attach`,
    {
      method: "POST",
      body: JSON.stringify(request),
    }
  );
}

/**
 * Review an advisory variant (rate, reject, add notes).
 */
export async function reviewAdvisory(
  runId: string,
  advisoryId: string,
  request: AdvisoryReviewRequest
): Promise<AdvisoryReviewRecord> {
  return fetchJson<AdvisoryReviewRecord>(
    `/api/rmos/runs/${runId}/advisory/${advisoryId}/review`,
    {
      method: "POST",
      body: JSON.stringify(request),
    }
  );
}

/**
 * Promote an advisory variant to manufacturing candidate.
 */
export async function promoteAdvisory(
  runId: string,
  advisoryId: string
): Promise<PromoteResponse> {
  return fetchJson<PromoteResponse>(
    `/api/rmos/runs/${runId}/advisory/${advisoryId}/promote`,
    {
      method: "POST",
      body: JSON.stringify({}),
    }
  );
}

// =============================================================================
// RUNS API (for listing runs to attach to)
// =============================================================================

export interface RunSummary {
  run_id: string;
  created_at_utc: string;
  event_type: string;
  status: string;
  mode?: string;
  tool_id?: string;
}

// -----------------------------------------------------------------------------
// RMOS runs: cursor pagination (canonical: GET /api/rmos/runs/query/recent)
// -----------------------------------------------------------------------------
export type RecentRunsQueryResponse = {
  items: RunSummary[];
  next_cursor?: string | null;
};

export async function queryRecentRuns(params?: {
  cursor?: string | null;
  limit?: number;
  event_type?: string | null;
  q?: string | null;
}): Promise<RecentRunsQueryResponse> {
  const p = new URLSearchParams();
  if (params?.cursor) p.set("cursor", params.cursor);
  if (params?.limit) p.set("limit", String(params.limit));
  if (params?.event_type) p.set("event_type", params.event_type);
  if (params?.q) p.set("q", params.q);
  const qs = p.toString();
  return fetchJson<RecentRunsQueryResponse>(`/api/rmos/runs/query/recent${qs ? `?${qs}` : ""}`, {
    method: "GET",
  });
}

export interface RunsListResponse {
  runs: RunSummary[];
  total: number;
}

export interface CreateRunRequest {
  event_type?: string;
  mode?: string;
  tool_id?: string;
  status?: string;
}

export interface CreateRunResponse {
  run_id: string;
}

/**
 * List recent runs (for selecting a run to attach to).
 */
export async function listRecentRuns(
  limit = 20,
  offset = 0
): Promise<RunsListResponse> {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });
  return fetchJson<RunsListResponse>(`/api/rmos/runs?${params}`);
}

/**
 * Create a new RMOS run (canonical: POST /api/rmos/runs)
 * Used by VisionAttachToRunWidget when no runs exist yet.
 */
export async function createRun(
  request: CreateRunRequest = {}
): Promise<CreateRunResponse> {
  return fetchJson<CreateRunResponse>("/api/rmos/runs", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

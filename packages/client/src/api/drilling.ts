// src/api/drilling.ts
//
// Frontend client for the CamIntentV1 Drilling lane (Dev Order 8I).
//
// Calls POST /api/cam/drilling/intent-gcode, the canonical peck-drilling endpoint
// that takes a CamIntentV1 envelope and returns generated G-code + provenance.
// This is the first frontend wired to a real CamIntent operation endpoint — it
// establishes the per-lane client convention (typed request/response) for
// Pocketing/Profile/V-Carve to follow. It uses raw fetch rather than the shared
// fetchJson helper deliberately: fetchJson collapses an error body into a generic
// `HTTP <status>` string, which would discard the structured FastAPI `detail` we
// need to surface the 409 feasibility-block reason in the UI.
//
// Backend contract (services/api/app/cam/routers/drilling/intent_router.py):
//   200 -> DrillingIntentResponse (gcode is a FLAT string here)
//   409 FEASIBILITY_BLOCKED  -> infeasible peck/geometry; detail carries feasibility
//   422 NORMALIZATION_ERROR | INVALID_MODE | INVALID_DESIGN | ADAPTER_ERROR
//   400 TOOLPATH_GENERATION_ERROR

const API_BASE = (import.meta as any).env?.VITE_API_BASE || "/api";

// ---- Request envelope (CamIntentV1) ----

/** A single hole position. depth_mm overrides the design default when set. */
export interface DrillPointV1 {
  x: number;
  y: number;
  depth_mm?: number;
  label?: string;
}

/** Design bucket — the "what" (DrillingDesignV1). */
export interface DrillingDesignV1 {
  holes: DrillPointV1[];
  hole_depth_mm: number;
  hole_diameter_mm: number;
  peck_drilling: boolean;
  peck_depth_mm: number;
}

/** Operational context — the "how" (feeds/speeds, retract). Bounds enforced server-side. */
export interface DrillingContext {
  feed_rate_mm_min?: number;
  spindle_rpm?: number;
  retract_height_mm?: number;
  safe_z_mm?: number;
}

/** CamIntentV1 envelope for the drilling lane. */
export interface DrillingIntentRequest {
  mode: "router_3axis";
  units: "mm";
  tool_id?: string;
  design: DrillingDesignV1;
  context: DrillingContext;
}

// ---- Success response (DrillingIntentResponse) ----

export interface DrillingIntentIssue {
  code: string;
  message: string;
  path: string;
}

export interface DrillingIntentMetadata {
  hole_count: number;
  total_depth_mm: number;
  estimated_time_seconds: number;
  risk_level: string;
}

export interface DrillingIntentResponse {
  gcode: string;
  issues: DrillingIntentIssue[];
  run_id: string;
  hashes: Record<string, string>;
  metadata: DrillingIntentMetadata;
}

// ---- Structured errors (409 / 422 / 400) ----

/** A failed drilling request, carrying the parsed backend `detail` when present. */
export class DrillingIntentError extends Error {
  status: number;
  /** Backend error code, e.g. FEASIBILITY_BLOCKED, INVALID_DESIGN. */
  code: string;
  /** Feasibility report on a 409 block (issues, risk_level, ...). */
  feasibility?: Record<string, any>;
  run_id?: string;

  constructor(
    status: number,
    code: string,
    message: string,
    opts?: { feasibility?: Record<string, any>; run_id?: string }
  ) {
    super(message);
    this.name = "DrillingIntentError";
    this.status = status;
    this.code = code;
    this.feasibility = opts?.feasibility;
    this.run_id = opts?.run_id;
  }
}

/**
 * POST a drilling intent. Resolves to the generated G-code response on 200,
 * throws DrillingIntentError (with parsed `detail`) on 409/422/400.
 *
 * fetchJson throws a generic `HTTP <status>: <body>` Error; we intercept to
 * recover the structured FastAPI `detail` so the UI can surface the real block
 * reason (especially the 409 feasibility path) instead of a raw status string.
 */
export async function generateDrillingGcode(
  request: DrillingIntentRequest
): Promise<DrillingIntentResponse> {
  const url = `${API_BASE}/cam/drilling/intent-gcode`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!res.ok) {
    const detail = await parseErrorDetail(res);
    throw new DrillingIntentError(
      res.status,
      detail.code,
      detail.message,
      { feasibility: detail.feasibility, run_id: detail.run_id }
    );
  }

  return (await res.json()) as DrillingIntentResponse;
}

/** Pull the structured FastAPI `detail` out of an error response, with fallbacks. */
async function parseErrorDetail(res: Response): Promise<{
  code: string;
  message: string;
  feasibility?: Record<string, any>;
  run_id?: string;
}> {
  try {
    const body = await res.json();
    const d = body?.detail ?? body;
    if (d && typeof d === "object") {
      return {
        code: d.error || `HTTP_${res.status}`,
        message: d.message || res.statusText,
        feasibility: d.feasibility,
        run_id: d.run_id,
      };
    }
    return { code: `HTTP_${res.status}`, message: String(d ?? res.statusText) };
  } catch {
    return { code: `HTTP_${res.status}`, message: res.statusText };
  }
}

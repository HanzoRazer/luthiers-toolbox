// src/api/pocketing.ts
//
// Frontend client for the CamIntentV1 Pocketing lane (Dev Order 8J).
//
// Calls POST /api/cam/pocketing/intent-gcode, the adaptive pocket-clearing endpoint
// (L.1 core) that takes a CamIntentV1 envelope and returns generated G-code +
// provenance. Mirrors src/api/drilling.ts — the per-lane CamIntent client
// convention established by the Drilling wire (8I): typed request/response, raw
// fetch (NOT the shared fetchJson helper), so the structured FastAPI `detail` on a
// 409 feasibility block survives to the UI instead of being collapsed into a
// generic `HTTP <status>` string.
//
// Backend contract (services/api/app/cam/routers/pocketing/intent_router.py):
//   200 -> PocketingIntentResponse (gcode is a FLAT string here)
//   409 FEASIBILITY_BLOCKED  -> infeasible pocket/geometry; detail carries feasibility
//   422 NORMALIZATION_ERROR | INVALID_MODE | INVALID_DESIGN | ADAPTER_ERROR
//   400 TOOLPATH_GENERATION_ERROR
//   503 DEPENDENCY_UNAVAILABLE  -> shapely / L.1 core unavailable (env issue, not user input)
//
// NOTE on geometry: this endpoint takes an EXPLICIT boundary polygon (list of
// points), not a DXF/SVG file. The pocketing UI therefore enters geometry directly
// (as DrillingView does for holes); DXF-derived boundaries are a separate, not-yet-
// wired path.

const API_BASE = (import.meta as any).env?.VITE_API_BASE || "/api";

// ---- Request envelope (CamIntentV1) ----

/** A 2D point in a pocket boundary or island (PocketPointV1). */
export interface PocketPointV1 {
  x: number;
  y: number;
}

/** An island (no-cut region) within the pocket (PocketIslandV1). */
export interface PocketIslandV1 {
  boundary: PocketPointV1[];
}

/**
 * Design bucket — the "what" (PocketDesignV1).
 * Backend bounds: pocket_depth_mm (0,200], tool_diameter_mm [0.5,50],
 * stepover_percent [30,70], finish_allowance_mm [0,5]. boundary/island >= 3 pts.
 */
export interface PocketDesignV1 {
  boundary: PocketPointV1[];
  islands: PocketIslandV1[];
  pocket_depth_mm: number;
  tool_diameter_mm: number;
  stepover_percent: number;
  roughing_only: boolean;
  finish_pass: boolean;
  finish_allowance_mm: number;
}

/**
 * Operational context — the "how" (feeds/speeds, heights, path pattern).
 * Bounds enforced server-side. `strategy` is the L.1 path pattern: only "Spiral"
 * or "Lanes" are served by the adapter. No spindle field — the engine emits a
 * fixed S18000.
 */
export interface PocketingContext {
  strategy?: "Spiral" | "Lanes";
  stepdown_mm?: number;
  margin_mm?: number;
  smoothing_radius_mm?: number;
  feed_rate_mm_min?: number;
  plunge_rate_mm_min?: number;
  safe_z_mm?: number;
  retract_z_mm?: number;
}

/** CamIntentV1 envelope for the pocketing lane. */
export interface PocketingIntentRequest {
  mode: "router_3axis";
  units: "mm";
  tool_id?: string;
  design: PocketDesignV1;
  context: PocketingContext;
}

// ---- Success response (PocketingIntentResponse) ----

export interface PocketingIntentIssue {
  code: string;
  message: string;
  path: string;
}

export interface PocketingIntentMetadata {
  pocket_area_mm2: number;
  island_count: number;
  stepover_percent: number;
  estimated_time_seconds: number;
}

export interface PocketingIntentResponse {
  gcode: string;
  issues: PocketingIntentIssue[];
  run_id: string;
  hashes: Record<string, string>;
  metadata: PocketingIntentMetadata;
}

// ---- Structured errors (409 / 422 / 400 / 503) ----

/** A failed pocketing request, carrying the parsed backend `detail` when present. */
export class PocketingIntentError extends Error {
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
    this.name = "PocketingIntentError";
    this.status = status;
    this.code = code;
    this.feasibility = opts?.feasibility;
    this.run_id = opts?.run_id;
  }
}

/**
 * POST a pocketing intent. Resolves to the generated G-code response on 200,
 * throws PocketingIntentError (with parsed `detail`) on 409/422/400/503.
 *
 * Raw fetch (not fetchJson) so the structured FastAPI `detail` — especially the
 * 409 feasibility report — reaches the UI instead of a generic status string.
 */
export async function generatePocketingGcode(
  request: PocketingIntentRequest
): Promise<PocketingIntentResponse> {
  const url = `${API_BASE}/cam/pocketing/intent-gcode`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!res.ok) {
    const detail = await parseErrorDetail(res);
    throw new PocketingIntentError(
      res.status,
      detail.code,
      detail.message,
      { feasibility: detail.feasibility, run_id: detail.run_id }
    );
  }

  return (await res.json()) as PocketingIntentResponse;
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

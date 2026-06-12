// src/api/profiling.ts
//
// Frontend client for the CamIntentV1 Profiling lane (Dev Order 8H).
//
// Calls POST /api/cam/profiling/intent-gcode — the perimeter-profiling endpoint
// that ContourCuttingView wires to (contour-cutting IS perimeter profiling with
// holding tabs; there is no separate /api/cam/contour lane). Mirrors src/api/
// drilling.ts / pocketing.ts: typed request/response, raw fetch (NOT fetchJson)
// so the structured FastAPI `detail` on a 409 feasibility block survives to the UI.
//
// Backend contract (services/api/app/cam/routers/profiling/intent_router.py):
//   200 -> ProfileIntentResponse (gcode is a FLAT string here)
//   409 FEASIBILITY_BLOCKED  -> infeasible geometry/params; detail carries feasibility
//   422 NORMALIZATION_ERROR | INVALID_MODE | INVALID_DESIGN | ADAPTER_ERROR
//   400 TOOLPATH_GENERATION_ERROR
//
// NOTE on geometry: this endpoint takes an EXPLICIT contour polygon (list of
// points), not a DXF/SVG file — the view enters contour points directly, as
// DrillingView/PocketClearingView do for their geometry.

const API_BASE = (import.meta as any).env?.VITE_API_BASE || "/api";

// ---- Request envelope (CamIntentV1) ----

/** A 2D point in the profile contour (ProfilePointV1). */
export interface ProfilePointV1 {
  x: number;
  y: number;
}

/**
 * Design bucket — the "what" (ProfileDesignV1).
 * Backend bounds: tool_diameter_mm (0,50], cut_depth_mm (0,100], tab_count [0,20],
 * tab_width_mm [1,30], tab_height_mm [0.5,10], finishing_allowance_mm [0,5].
 * contour >= 3 points. is_outside: true=outside cut, false=inside (no on-line option).
 */
export interface ProfileDesignV1 {
  contour: ProfilePointV1[];
  is_closed: boolean;
  is_outside: boolean;
  tool_diameter_mm: number;
  cut_depth_mm: number;
  use_tabs: boolean;
  tab_count: number;
  tab_width_mm: number;
  tab_height_mm: number;
  finishing_pass: boolean;
  finishing_allowance_mm: number;
}

/**
 * Operational context — the "how" (feeds/speeds, heights, lead-in radius, direction).
 * Bounds enforced server-side. No spindle field — the profile engine doesn't model it.
 * Lead-in is a RADIUS (lead_in_radius_mm), not a type (arc=radius, direct=0).
 */
export interface ProfilingContext {
  stepdown_mm?: number;
  feed_rate_mm_min?: number;
  feed_rate_z_mm_min?: number;
  plunge_rate_mm_min?: number;
  safe_z_mm?: number;
  retract_z_mm?: number;
  lead_in_radius_mm?: number;
  climb_milling?: boolean;
}

/** CamIntentV1 envelope for the profiling lane. */
export interface ProfilingIntentRequest {
  mode: "router_3axis";
  units: "mm";
  tool_id?: string;
  design: ProfileDesignV1;
  context: ProfilingContext;
}

// ---- Success response (ProfileIntentResponse) ----

export interface ProfilingIntentIssue {
  code: string;
  message: string;
  path: string;
}

export interface ProfilingIntentMetadata {
  pass_count: number;
  tab_count: number;
  total_length_mm: number;
  estimated_time_seconds: number;
}

export interface ProfilingIntentResponse {
  gcode: string;
  issues: ProfilingIntentIssue[];
  run_id: string;
  hashes: Record<string, string>;
  metadata: ProfilingIntentMetadata;
}

// ---- Structured errors (409 / 422 / 400) ----

/** A failed profiling request, carrying the parsed backend `detail` when present. */
export class ProfilingIntentError extends Error {
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
    this.name = "ProfilingIntentError";
    this.status = status;
    this.code = code;
    this.feasibility = opts?.feasibility;
    this.run_id = opts?.run_id;
  }
}

/**
 * POST a profiling intent. Resolves to the generated G-code response on 200,
 * throws ProfilingIntentError (with parsed `detail`) on 409/422/400.
 *
 * Raw fetch (not fetchJson) so the structured FastAPI `detail` — especially the
 * 409 feasibility report — reaches the UI instead of a generic status string.
 */
export async function generateProfilingGcode(
  request: ProfilingIntentRequest
): Promise<ProfilingIntentResponse> {
  const url = `${API_BASE}/cam/profiling/intent-gcode`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!res.ok) {
    const detail = await parseErrorDetail(res);
    throw new ProfilingIntentError(
      res.status,
      detail.code,
      detail.message,
      { feasibility: detail.feasibility, run_id: detail.run_id }
    );
  }

  return (await res.json()) as ProfilingIntentResponse;
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

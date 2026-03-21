/**
 * CAM G-code Animate Simulator SDK (Toolpath Player)
 *
 * Typed helper for per-segment toolpath simulation:
 *   POST /api/cam/gcode/simulate
 *
 * Returns segmented move data for the animated toolpath player.
 * Arcs are pre-interpolated server-side — the renderer only needs lineTo().
 *
 * Usage:
 *   import { simulate } from "@/sdk/endpoints/cam"
 *   const result = await simulate({ gcode })
 *   // result.segments → MoveSegment[] ready to hand to useToolpathPlayerStore
 */

import { apiFetch } from "@/sdk/core/apiFetch";

// ---------------------------------------------------------------------------
// Request
// ---------------------------------------------------------------------------

export interface SimulateRequest {
  /** Raw G-code program text */
  gcode: string;
  /** Input units: "mm" or "inch". Default "mm". */
  units?: "mm" | "inch";
  /** Machine rapid traverse rate (mm/min). Default 3000. */
  rapid_mm_min?: number;
  /** Default feed when F not yet set. Default 500. */
  default_feed_mm_min?: number;
  /**
   * Arc interpolation step (degrees). Default 5.
   * Smaller = smoother curves, more segments.
   * Practical range: 2 (smooth) → 10 (performance).
   */
  arc_resolution_deg?: number;
}

// ---------------------------------------------------------------------------
// Response types
// ---------------------------------------------------------------------------

/** One atomic motion segment. Arcs are already linearised into sub-segments. */
export interface MoveSegment {
  /** Motion type — drives colour coding and line style in the canvas renderer */
  type: "rapid" | "cut" | "arc_cw" | "arc_ccw";
  /** Start position [x, y, z] in mm */
  from_pos: [number, number, number];
  /** End position [x, y, z] in mm */
  to_pos: [number, number, number];
  /** Feed rate for this move (mm/min) */
  feed: number;
  /** Real-time duration of this move in milliseconds */
  duration_ms: number;
  /** 1-based source G-code line index */
  line_number: number;
  /** Raw G-code text — displayed in the HUD */
  line_text: string;
}

/** XYZ bounding box of the entire toolpath */
export interface SimulateBounds {
  x_min: number;
  x_max: number;
  y_min: number;
  y_max: number;
  z_min: number;
  z_max: number;
}

/** Aggregate statistics (mirrors simulate() totals for cross-validation) */
export interface SimulateTotals {
  rapid_mm: number;
  cut_mm: number;
  time_min: number;
  segment_count: number;
}

/** Full simulation response */
export interface SimulateResponse {
  segments: MoveSegment[];
  bounds: SimulateBounds;
  totals: SimulateTotals;
}

// ---------------------------------------------------------------------------
// API call
// ---------------------------------------------------------------------------

/**
 * POST /api/cam/gcode/simulate
 *
 * Simulates G-code and returns per-segment move data for animation.
 * Each segment is one G0/G1/G2/G3 command (arcs expanded into sub-segments).
 *
 * @throws ApiError on non-2xx responses
 */
export async function simulate(req: SimulateRequest): Promise<SimulateResponse> {
  return apiFetch<SimulateResponse>("/cam/gcode/simulate", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

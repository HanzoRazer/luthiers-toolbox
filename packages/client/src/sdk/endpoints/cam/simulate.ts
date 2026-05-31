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
  /** Backend safety ceiling on emitted segments. Default 500000. */
  max_segments?: number;
  /**
   * Optional acceleration (mm/s^2) for trapezoidal timing. When omitted the
   * backend uses constant-velocity timing (instantaneous accel).
   */
  accel_mm_s2?: number;
  /** Junction deviation (mm) for cornering speed when accel is enabled. */
  junction_deviation_mm?: number;
}

// ---------------------------------------------------------------------------
// Response types
// ---------------------------------------------------------------------------

/** One atomic motion segment. Arcs are already linearised into sub-segments. */
export interface MoveSegment {
  /** Motion type — drives colour coding and line style in the canvas renderer */
  type: "rapid" | "cut" | "arc_cw" | "arc_ccw" | "dwell";
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
  /** Tool number for this segment (from T-code) */
  tool_number?: number;
  /** Spindle RPM for this segment (from S-code) */
  spindle_rpm?: number;
  /** Whether spindle is on (M3/M4 vs M5) */
  spindle_on?: boolean;
  /** True when this segment is part of an expanded canned cycle */
  is_cycle?: boolean;
  /** Canned cycle code that produced this segment, e.g. "G83" */
  cycle_kind?: string;
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

/** Tool change event */
export interface ToolChange {
  /** Line number where tool change occurred */
  line_number: number;
  /** Previous tool number */
  from_tool: number;
  /** New tool number */
  to_tool: number;
  /** Position at tool change [x, y, z] */
  position: [number, number, number];
}

/** Multi-tool tracking summary */
export interface ToolsInfo {
  /** List of unique tool numbers used */
  used: number[];
  /** Count of unique tools */
  count: number;
  /** Tool change events */
  changes: ToolChange[];
}

/**
 * Fidelity warnings — populated when the simulation could not faithfully model
 * part of the program. Lets the player show a "limited simulation" banner
 * instead of silently mis-rendering.
 */
export interface SimulateWarnings {
  /** Unrecognised G-codes encountered (not animated) */
  unsupported_g: number[];
  /** Unhandled M-codes encountered */
  unsupported_m: number[];
  /** Work offsets (G54–G59) seen but not applied (program coordinates shown) */
  ignored_offsets: number[];
  /** Canned cycles approximated rather than modelled exactly */
  approx_cycles: number[];
  /** Count of arcs simulated outside the XY plane (G18/G19) */
  non_xy_arcs: number;
  /** Count of arcs that fell back to a straight cut */
  degenerate_arcs: number;
  /** True if the segment cap was hit and segments were dropped */
  truncated: boolean;
  /** Number of segments dropped due to the cap */
  dropped_segments: number;
}

/** Full simulation response */
export interface SimulateResponse {
  segments: MoveSegment[];
  bounds: SimulateBounds;
  totals: SimulateTotals;
  /** Multi-tool tracking (optional for backwards compatibility) */
  tools?: ToolsInfo;
  /** Fidelity warnings (optional for backwards compatibility) */
  warnings?: SimulateWarnings;
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

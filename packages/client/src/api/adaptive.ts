// packages/client/src/api/adaptive.ts
/**
 * Typed client for Adaptive Pocket CAM operations
 * 
 * Provides TypeScript interfaces and functions for:
 * - /api/cam/pocket/adaptive/plan - Generate adaptive toolpath
 * - /api/cam/pocket/adaptive/gcode - Export with post-processor
 * - /api/cam/pocket/adaptive/sim - Simulate toolpath
 */

const base = (import.meta as any).env?.VITE_API_BASE || "/api";

export type Loop = {
  pts: number[][];
};

export type AdaptivePlanIn = {
  loops: Loop[];

  units: "mm" | "inch";
  tool_d: number;
  stepover?: number;
  stepdown?: number;
  margin?: number;
  strategy?: "Spiral" | "Lanes";
  smoothing?: number;
  climb?: boolean;

  feed_xy?: number;
  safe_z?: number;
  z_rough?: number;

  // L.2 parameters
  corner_radius_min?: number;
  target_stepover?: number;
  slowdown_feed_pct?: number;

  // L.3 parameters
  use_trochoids?: boolean;
  trochoid_radius?: number;
  trochoid_pitch?: number;

  jerk_aware?: boolean;
  machine_feed_xy?: number;
  machine_rapid?: number;
  machine_accel?: number;
  machine_jerk?: number;
  corner_tol_mm?: number;

  // M.* parameters
  machine_profile_id?: string | null;
  adopt_overrides?: boolean;
  session_override_factor?: number | null;
};

export type AdaptiveMove = {
  code: string;
  x?: number;
  y?: number;
  z?: number;
  f?: number;
  meta?: {
    slowdown?: number;
    trochoid?: boolean;
    [key: string]: any;
  };
};

export type AdaptiveOverlay = {
  type: string;
  x: number;
  y: number;
  radius?: number;
  severity?: "low" | "medium" | "high";
  [key: string]: any;
};

export type AdaptivePlanOut = {
  moves: AdaptiveMove[];
  stats: {
    length_mm?: number;
    area_mm2?: number;
    time_s?: number;
    time_jerk_s?: number;
    volume_mm3?: number;
    move_count?: number;
    tight_count?: number;
    trochoid_count?: number;
    [key: string]: any;
  };
  overlays?: AdaptiveOverlay[];
};

async function postJson<T>(url: string, body: any): Promise<T> {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const txt = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status}: ${txt || res.statusText}`);
  }
  return res.json() as Promise<T>;
}

/**
 * Generate adaptive pocket toolpath
 * 
 * @param payload - AdaptivePlanIn with loops and parameters
 * @returns AdaptivePlanOut with moves, stats, and overlays
 */
export const planAdaptive = (payload: AdaptivePlanIn) =>
  postJson<AdaptivePlanOut>(`${base}/cam/pocket/adaptive/plan`, payload);

/**
 * Generate adaptive pocket G-code with post-processor headers
 * 
 * @param payload - AdaptivePlanIn plus post_id
 * @returns G-code string
 */
export const exportAdaptiveGcode = async (
  payload: AdaptivePlanIn & { post_id?: string }
): Promise<string> => {
  const res = await fetch(`${base}/cam/pocket/adaptive/gcode`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const txt = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status}: ${txt || res.statusText}`);
  }
  return res.text();
};

/**
 * Simulate adaptive pocket toolpath
 * 
 * @param payload - AdaptivePlanIn with loops and parameters
 * @returns Simulation result with stats and preview
 */
export const simAdaptive = (payload: AdaptivePlanIn) =>
  postJson<{ success: boolean; stats: any; moves: AdaptiveMove[] }>(
    `${base}/cam/pocket/adaptive/sim`,
    payload
  );

/**
 * Plan from DXF types
 */
export type PlanFromDxfIn = {
  dxf_path: string;
  layer?: string;
  units: "mm" | "inch";
  tool_d: number;
  stepover?: number;
  stepdown?: number;
  margin?: number;
  strategy?: "Spiral" | "Lanes";
  feed_xy?: number;
  safe_z?: number;
  z_rough?: number;
};

export type PlanFromDxfOut = {
  loops: Loop[];
  plan: AdaptivePlanOut;
};

/**
 * Plan adaptive pocket from DXF file
 * 
 * Converts DXF geometry directly to adaptive toolpath
 * @param payload - DXF path and tool parameters
 * @returns Loops and adaptive plan
 */
export const planAdaptiveFromDxf = (payload: PlanFromDxfIn) =>
  postJson<PlanFromDxfOut>(
    `${base}/cam/pocket/adaptive/plan_from_dxf`,
    payload
  );

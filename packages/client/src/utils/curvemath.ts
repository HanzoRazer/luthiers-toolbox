/**
 * Curve Math API Client
 * 
 * Advanced curve operations for CAD/CAM applications:
 * - Offset curves (with miter/round/bevel joins)
 * - Auto-filleting of polylines
 * - Curve fairing (smoothing)
 * - Clothoid/biarc blending
 * 
 * All operations work in millimeters.
 */

const API_BASE = import.meta.env.VITE_API_BASE || '/api'

export interface PolylineResult {
  polyline: {
    points: [number, number][]
  }
}

export interface ClothoidResult extends PolylineResult {
  method: 'clothoid' | 'biarc'
}

/**
 * Offset a polyline by a specified distance
 * 
 * @param points - Array of [x, y] coordinates in mm
 * @param distance - Offset distance in mm (positive = left/CCW, negative = right/CW)
 * @param join - Join type: 'round' (smooth arcs), 'miter' (sharp), 'bevel' (flat)
 * @param miterLimit - Maximum miter length (default 4.0)
 * @param arcStepDeg - Arc resolution in degrees (default 8)
 * 
 * @example
 * // Offset pickup cavity 3mm outward with rounded corners
 * const offset = await offsetPolycurve(pickupPoints, 3.0, 'round')
 */
export async function offsetPolycurve(
  points: [number, number][],
  distance: number,
  join: 'round' | 'miter' | 'bevel' = 'round',
  miterLimit = 4.0,
  arcStepDeg = 8.0
): Promise<PolylineResult> {
  const response = await fetch(`${API_BASE}/math/offset/polycurve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      polyline: { points },
      distance,
      join,
      miter_limit: miterLimit,
      arc_step_deg: arcStepDeg
    })
  })
  
  if (!response.ok) {
    throw new Error(`Offset failed: ${response.statusText}`)
  }
  
  return response.json()
}

/**
 * Automatically fillet all corners of a polyline with circular arcs
 * 
 * @param points - Array of [x, y] coordinates in mm
 * @param R - Fillet radius in mm
 * @param arcStepDeg - Arc resolution in degrees (default 10)
 * 
 * @example
 * // Round pickup cavity corners with 6mm radius
 * const filleted = await autoFillet(cavityPoints, 6.0)
 */
export async function autoFillet(
  points: [number, number][],
  R: number,
  arcStepDeg = 10
): Promise<PolylineResult> {
  const response = await fetch(`${API_BASE}/math/fillet/auto`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      polyline: { points },
      R,
      arc_step_deg: arcStepDeg
    })
  })
  
  if (!response.ok) {
    throw new Error(`Fillet failed: ${response.statusText}`)
  }
  
  return response.json()
}

/**
 * Smooth/fair a curve using discrete Laplacian smoothing
 * 
 * @param points - Array of [x, y] coordinates in mm
 * @param lam - Smoothing strength (higher = smoother, default 10)
 * @param preserveEndpoints - Keep first/last points fixed (default true)
 * 
 * @example
 * // Smooth hand-drawn bracing curve
 * const smoothed = await fairCurve(bracingPoints, 15.0, true)
 */
export async function fairCurve(
  points: [number, number][],
  lam = 10,
  preserveEndpoints = true
): Promise<PolylineResult> {
  const response = await fetch(`${API_BASE}/math/fair/curve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      polyline: { points },
      lam,
      preserve_endpoints: preserveEndpoints
    })
  })
  
  if (!response.ok) {
    throw new Error(`Fair curve failed: ${response.statusText}`)
  }
  
  return response.json()
}

/**
 * Create a smooth blend curve (clothoid/biarc) between two points with specified tangents
 * 
 * @param p0 - Start point [x, y] in mm
 * @param t0 - Start tangent vector [dx, dy]
 * @param p1 - End point [x, y] in mm
 * @param t1 - End tangent vector [dx, dy]
 * @param maxStep - Maximum step size in mm (default 1.0)
 * 
 * @example
 * // Create smooth transition between neck and body curves
 * const blend = await blendClothoid(
 *   [100, 200], [1, 0],  // Start point and tangent
 *   [300, 250], [0, 1],  // End point and tangent
 *   1.0
 * )
 */
export async function blendClothoid(
  p0: [number, number],
  t0: [number, number],
  p1: [number, number],
  t1: [number, number],
  maxStep = 1.0
): Promise<ClothoidResult> {
  const response = await fetch(`${API_BASE}/math/blend/clothoid`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      p0,
      t0,
      p1,
      t1,
      max_step: maxStep
    })
  })
  
  if (!response.ok) {
    throw new Error(`Clothoid blend failed: ${response.statusText}`)
  }
  
  return response.json()
}

// ============================================================================
// Client-Side Bi-arc Math (for Overlay Visualization)
// ============================================================================

export interface BiarcArc {
  type: 'arc'
  center: [number, number]
  radius: number
  start_angle: number  // degrees
  end_angle: number    // degrees
}

export interface BiarcLine {
  type: 'line'
  A: [number, number]
  B: [number, number]
}

export type BiarcEntity = BiarcArc | BiarcLine

/**
 * Client-side bi-arc construction for real-time overlay visualization
 * 
 * This is a TypeScript port of the Python bi-arc algorithm from
 * curvemath_router_biarc.py. It allows CurveLab to compute arc centers
 * and radii locally for overlay rendering without server round-trips.
 * 
 * @param p0 - Start point [x, y] in mm
 * @param t0 - Tangent direction at start [dx, dy]
 * @param p1 - End point [x, y] in mm
 * @param t1 - Tangent direction at end [dx, dy]
 * @returns Array of arc/line entities (typically 2 arcs, or 1 line if degenerate)
 * 
 * @example
 * ```typescript
 * const entities = biarcEntitiesTS([0, 0], [1, 0], [100, 50], [0, 1])
 * for (const e of entities) {
 *   if (e.type === 'arc') {
 *     ctx.arc(e.center[0], e.center[1], e.radius, ...)
 *     // Draw center dot + R= label
 *   }
 * }
 * ```
 */
export function biarcEntitiesTS(
  p0: [number, number],
  t0: [number, number],
  p1: [number, number],
  t1: [number, number]
): BiarcEntity[] {
  // Vector math helpers
  const unit = (v: [number, number]): [number, number] => {
    const mag = Math.sqrt(v[0] ** 2 + v[1] ** 2)
    return mag < 1e-12 ? [1, 0] : [v[0] / mag, v[1] / mag]
  }

  const normal = (v: [number, number]): [number, number] => {
    return [-v[1], v[0]]  // Rotate 90° CCW
  }

  const add = (a: [number, number], b: [number, number]): [number, number] => {
    return [a[0] + b[0], a[1] + b[1]]
  }

  const sub = (a: [number, number], b: [number, number]): [number, number] => {
    return [a[0] - b[0], a[1] - b[1]]
  }

  const scale = (v: [number, number], s: number): [number, number] => {
    return [v[0] * s, v[1] * s]
  }

  // Arc from point A with tangent TA to point B
  const arcFromATB = (
    A: [number, number],
    TA: [number, number],
    B: [number, number]
  ): BiarcArc | null => {
    const TA_unit = unit(TA)
    const AB = sub(B, A)
    const dist_AB = Math.sqrt(AB[0] ** 2 + AB[1] ** 2)

    if (dist_AB < 1e-9) return null  // Degenerate: A == B

    const NA = normal(TA_unit)
    const M: [number, number] = [(A[0] + B[0]) / 2, (A[1] + B[1]) / 2]
    const AB_unit: [number, number] = [AB[0] / dist_AB, AB[1] / dist_AB]
    const perp_bisector = normal(AB_unit)

    // Solve for intersection of:
    // - Line through A with direction NA
    // - Line through M with direction perp_bisector
    const det = NA[0] * (-perp_bisector[1]) - NA[1] * (-perp_bisector[0])
    if (Math.abs(det) < 1e-9) return null  // Parallel lines

    const rhs = sub(M, A)
    const s = (rhs[0] * (-perp_bisector[1]) - rhs[1] * (-perp_bisector[0])) / det

    const C = add(A, scale(NA, s))
    const radius = Math.sqrt((A[0] - C[0]) ** 2 + (A[1] - C[1]) ** 2)

    let start_angle = (Math.atan2(A[1] - C[1], A[0] - C[0]) * 180) / Math.PI
    let end_angle = (Math.atan2(B[1] - C[1], B[0] - C[0]) * 180) / Math.PI

    // Go the "short way" around the circle
    const angle_diff = end_angle - start_angle
    if (angle_diff > 180) end_angle -= 360
    else if (angle_diff < -180) end_angle += 360

    return {
      type: 'arc',
      center: C,
      radius,
      start_angle,
      end_angle
    }
  }

  // Main bi-arc algorithm
  const T0 = unit(t0)
  const T1 = unit(t1)

  // Check for parallel tangents
  const cross = T0[0] * T1[1] - T0[1] * T1[0]
  if (Math.abs(cross) < 1e-9) {
    // Degenerate: fallback to line
    return [{ type: 'line', A: p0, B: p1 }]
  }

  // Find intersection of tangent lines
  const det = T0[0] * (-T1[1]) - T0[1] * (-T1[0])
  if (Math.abs(det) < 1e-9) {
    return [{ type: 'line', A: p0, B: p1 }]
  }

  const rhs = sub(p1, p0)
  const s = (rhs[0] * (-T1[1]) - rhs[1] * (-T1[0])) / det

  const mid = add(p0, scale(T0, s))

  // Build arc1: p0 → mid
  const arc1 = arcFromATB(p0, T0, mid)
  if (!arc1) return [{ type: 'line', A: p0, B: p1 }]

  // Build arc2: mid → p1 (reverse T1)
  const T1_reversed: [number, number] = [-T1[0], -T1[1]]
  const arc2 = arcFromATB(mid, T1_reversed, p1)
  if (!arc2) return [{ type: 'line', A: p0, B: p1 }]

  return [arc1, arc2]
}

/**
 * Snap a direction vector to 0/45/90/135/... degrees when shift is held
 * 
 * This is used for tangent snapping in CurveLab's Clothoid mode. When the user
 * holds Shift while picking a tangent, the tangent direction snaps to 45° increments
 * for precise orthogonal/diagonal transitions.
 * 
 * @param v - Direction vector [dx, dy]
 * @param enabled - Whether snapping is enabled (typically from Shift key state)
 * @returns Snapped direction vector maintaining original magnitude
 * 
 * @example
 * ```typescript
 * // User picks tangent with Shift held
 * const rawTangent = [120, 80]  // ~34° angle
 * const snappedTangent = snapDir(rawTangent, true)  // Snaps to 45°
 * // Result: [127.3, 127.3] (45° with similar magnitude)
 * ```
 */
export function snapDir(v: [number, number], enabled: boolean): [number, number] {
  if (!enabled) return v
  
  const ang = Math.atan2(v[1], v[0])
  const step = Math.PI / 4  // 45° in radians
  const snap = Math.round(ang / step) * step
  const len = Math.hypot(v[0], v[1]) || 1
  
  return [Math.cos(snap) * len, Math.sin(snap) * len]
}

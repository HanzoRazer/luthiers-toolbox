/**
 * N17+N18 API Client: Adaptive Polygon Offset + Spiral G-code
 * 
 * N17: Polygon offset with pyclipper (robust multi-pass offsetting)
 * N18: Adaptive spiral G-code generation (continuous toolpath)
 * 
 * Backend: /cam/polygon_offset (N17), /cam/adaptive3/offset_spiral.nc (N18)
 */

const API_BASE_N17 = '/cam'
const API_BASE_N18 = '/cam/adaptive3'

// ============================================================================
// N17: Polygon Offset Interfaces
// ============================================================================

export interface PolygonOffsetRequest {
  polygon: Array<[number, number]>
  tool_dia: number
  stepover: number  // Fraction (0-1), e.g. 0.4 = 40%
  link_mode?: 'arc' | 'linear'
  units?: 'mm' | 'inch'
}

export interface OffsetPreview {
  units: 'mm' | 'inch'
  tool_dia: number
  stepover: number
  step: number
  passes: Array<{
    pass: number
    points: Array<[number, number]>
  }>
  bbox: {
    min_x: number
    min_y: number
    max_x: number
    max_y: number
  }
  meta: {
    total_passes: number
    total_points: number
  }
}

// ============================================================================
// N18: Adaptive Spiral Interfaces
// ============================================================================

export interface AdaptiveSpiralRequest {
  polygon: Array<[number, number]>
  tool_dia: number
  stepover: number  // mm (absolute distance)
  target_engage?: number
  arc_r?: number
  units?: string
  z?: number
  safe_z?: number
  base_feed?: number
  min_feed?: number
  floor_R?: number
  arc_tol?: number
  min_R?: number
  spindle?: number
}

// ============================================================================
// N17 API Functions
// ============================================================================

/**
 * Generate polygon offset preview (JSON with offset rings)
 */
export async function generatePolygonOffsetPreview(
  request: PolygonOffsetRequest
): Promise<OffsetPreview> {
  const response = await fetch(`${API_BASE_N17}/polygon_offset.preview`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request)
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Preview generation failed' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

/**
 * Generate polygon offset G-code (NC file)
 */
export async function generatePolygonOffsetGcode(
  request: PolygonOffsetRequest
): Promise<string> {
  const response = await fetch(`${API_BASE_N17}/polygon_offset.nc`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request)
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'G-code generation failed' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.text()
}

// ============================================================================
// N18 API Functions
// ============================================================================

/**
 * Generate adaptive spiral G-code (continuous toolpath with engagement control)
 */
export async function generateAdaptiveSpiralGcode(
  request: AdaptiveSpiralRequest
): Promise<string> {
  const response = await fetch(`${API_BASE_N18}/offset_spiral.nc`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request)
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Spiral G-code generation failed' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.text()
}

/**
 * DXF Export Utilities for Luthier's Tool Box
 * 
 * Client-side utilities for downloading polylines and bi-arcs as DXF files
 * from the FastAPI backend. Uses fetch API to POST geometry data and trigger
 * browser downloads.
 */

// Support both VITE_API_BASE and legacy VITE_API_BASE_URL for compatibility
const API_BASE = import.meta.env.VITE_API_BASE
  || import.meta.env.VITE_API_BASE_URL
  || (typeof window !== 'undefined' && window.location.hostname === 'localhost' ? 'http://localhost:8000' : '')

/**
 * Download blob from fetch Response
 * 
 * Creates a temporary download link, triggers click, and revokes URL
 * 
 * @param res - Fetch Response object with blob content
 * @param filename - Suggested filename for download
 */
async function downloadBlobFromResponse(res: Response, filename: string): Promise<void> {
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  
  // Cleanup
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

/**
 * Export polyline to DXF format
 * 
 * POSTs polyline data to /exports/polyline_dxf endpoint and triggers download.
 * The server will export as DXF R12 format (using ezdxf or ASCII R12 fallback).
 * 
 * @param points - Array of [x, y] coordinate pairs in mm
 * @param layer - DXF layer name (default: "CURVE")
 * 
 * @example
 * ```typescript
 * const points: [number, number][] = [[0, 0], [100, 0], [100, 50]]
 * await downloadOffsetDXF(points, 'PICKUP_CAVITY')
 * ```
 */
export async function downloadOffsetDXF(
  points: [number, number][],
  layer: string = 'CURVE'
): Promise<void> {
  try {
    const res = await fetch(`${API_BASE}/exports/polyline_dxf`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        polyline: { points },
        layer
      })
    })
    
    if (!res.ok) {
      const error = await res.text()
      throw new Error(`DXF export failed: ${error}`)
    }
    
    await downloadBlobFromResponse(res, 'polycurve.dxf')
  } catch (err) {
    console.error('Failed to export polyline DXF:', err)
    throw err
  }
}

/**
 * Export bi-arc blend to DXF format
 * 
 * POSTs bi-arc parameters to /exports/biarc_dxf endpoint and triggers download.
 * The server will compute two circular arcs (or lines if degenerate) that create
 * a G1-continuous blend between p0 and p1 with specified tangents.
 * 
 * @param p0 - Start point [x, y] in mm
 * @param t0 - Tangent direction at start [dx, dy]
 * @param p1 - End point [x, y] in mm
 * @param t1 - Tangent direction at end [dx, dy]
 * @param layer - DXF layer name (default: "CURVE")
 * 
 * @example
 * ```typescript
 * // Smooth neck-to-body transition
 * await downloadBiarcDXF(
 *   [0, 0],    // Start at origin
 *   [1, 0],    // Horizontal tangent
 *   [100, 50], // End at (100, 50)
 *   [0, 1],    // Vertical tangent
 *   'NECK_TRANSITION'
 * )
 * ```
 */
export async function downloadBiarcDXF(
  p0: [number, number],
  t0: [number, number],
  p1: [number, number],
  t1: [number, number],
  layer: string = 'CURVE'
): Promise<void> {
  try {
    const res = await fetch(`${API_BASE}/exports/biarc_dxf`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        p0,
        t0,
        p1,
        t1,
        layer
      })
    })
    
    if (!res.ok) {
      const error = await res.text()
      throw new Error(`Bi-arc DXF export failed: ${error}`)
    }
    
    await downloadBlobFromResponse(res, 'biarc.dxf')
  } catch (err) {
    console.error('Failed to export bi-arc DXF:', err)
    throw err
  }
}

/**
 * Check DXF export health and capabilities
 * 
 * Queries the /exports/dxf/health endpoint to check if ezdxf is available
 * and what export formats are supported.
 * 
 * @returns Health status and available formats
 * 
 * @example
 * ```typescript
 * const health = await checkDXFHealth()
 * console.log(health.formats)  // ["ezdxf (native)", "ASCII R12 (fallback)"]
 * ```
 */
export async function checkDXFHealth(): Promise<{
  status: string
  ezdxf_version: string | null
  formats: string[]
  note?: string
}> {
  const res = await fetch(`${API_BASE}/exports/dxf/health`)
  if (!res.ok) {
    throw new Error('Health check failed')
  }
  return res.json()
}

/**
 * Radius Dish API client
 *
 * Connects to the parametric G-code generator backend.
 * Replaces the previous static file downloads (only 15ft / 25ft).
 */

const BASE = (import.meta as any).env?.VITE_API_BASE || '/api'
const PREFIX = `${BASE}/v1/radius-dish`

// ── Types ────────────────────────────────────────────────────────────────────

export interface RadiusDishCalcResult {
  radius_mm: number
  radius_ft: number
  dish_width_mm: number
  dish_length_mm: number
  depth_at_width_mm: number
  depth_at_length_mm: number
  max_depth_mm: number
  formula: string
}

export interface BraceCamberResult {
  brace_length_mm: number
  radius_mm: number
  radius_ft: number
  camber_mm: number
  camber_in: number
  formula: string
  note: string
}

export interface CommonRadius {
  ft: number
  mm: number
  use: string
  depth_for_15in_wide_mm: number
}

export interface GcodeRequest {
  radius_ft?: number
  radius_mm?: number
  dish_width_mm?: number
  dish_length_mm?: number
  ball_nose_dia_mm?: number
  stepover_mm?: number
  roughing_stepover_mm?: number
  feed_mm_min?: number
  plunge_mm_min?: number
  safe_z_mm?: number
  finish_allowance_mm?: number
  spindle_rpm?: number
  units?: 'mm' | 'inch'
  include_roughing?: boolean
}

// ── API calls ─────────────────────────────────────────────────────────────────

export async function calculateDish(
  radiusFt: number,
  widthMm: number,
  lengthMm = widthMm,
): Promise<RadiusDishCalcResult> {
  const res = await fetch(`${PREFIX}/calculate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      radius_ft: radiusFt,
      width_mm: widthMm,
      length_mm: lengthMm,
    }),
  })
  if (!res.ok) throw new Error(`Calculate failed: ${res.status}`)
  return res.json()
}

export async function getBraceCamber(
  braceLengthMm: number,
  radiusFt: number,
): Promise<BraceCamberResult> {
  const res = await fetch(`${PREFIX}/brace-camber`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      brace_length_mm: braceLengthMm,
      radius_ft: radiusFt,
    }),
  })
  if (!res.ok) throw new Error(`Camber calc failed: ${res.status}`)
  return res.json()
}

export async function getCommonRadii(): Promise<CommonRadius[]> {
  const res = await fetch(`${PREFIX}/common-radii`)
  if (!res.ok) throw new Error(`Common radii failed: ${res.status}`)
  const data = await res.json()
  return data.radii
}

/**
 * Generate and download G-code for a radius dish.
 * Returns the blob so the caller can trigger a download.
 */
export async function generateGcode(req: GcodeRequest): Promise<{ blob: Blob; filename: string }> {
  const res = await fetch(`${PREFIX}/generate-gcode`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
  if (!res.ok) throw new Error(`G-code generation failed: ${res.status}`)
  const disposition = res.headers.get('Content-Disposition') || ''
  const match = disposition.match(/filename=(.+)/)
  const filename = match ? match[1] : 'radius_dish.nc'
  const blob = await res.blob()
  return { blob, filename }
}

export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

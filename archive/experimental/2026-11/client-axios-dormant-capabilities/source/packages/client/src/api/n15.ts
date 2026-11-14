// N15 Backplot API Client
// Handles G-code visualization and time estimation

import axios from 'axios'

const API_BASE = '/api/cam/gcode'

export interface BackplotRequest {
  gcode: string
  units?: 'mm' | 'inch'
  rapid_mm_min?: number
  default_feed_mm_min?: number
  stroke?: string
}

export interface SimulateResponse {
  travel_mm: number
  cut_mm: number
  t_rapid_min: number
  t_feed_min: number
  t_total_min: number
  points_xy: Array<[number, number]>
}

/**
 * Generate SVG backplot from G-code
 * POST /api/cam/gcode/plot.svg
 * Returns raw SVG string
 */
export async function generateBackplot(request: BackplotRequest): Promise<string> {
  const response = await axios.post(`${API_BASE}/plot.svg`, request, {
    responseType: 'text'
  })
  return response.data
}

/**
 * Estimate machining time from G-code
 * POST /api/cam/gcode/estimate
 */
export async function estimateGcode(request: BackplotRequest): Promise<SimulateResponse> {
  const response = await axios.post(`${API_BASE}/estimate`, request)
  return response.data
}

/**
 * Save G-code to temp storage for pipeline integration
 * POST /api/cam/gcode/save_temp
 */
export async function saveGcodeTemp(gcode: string): Promise<{ gcode_key: string }> {
  const response = await axios.post(`${API_BASE}/save_temp`, { gcode })
  return response.data
}

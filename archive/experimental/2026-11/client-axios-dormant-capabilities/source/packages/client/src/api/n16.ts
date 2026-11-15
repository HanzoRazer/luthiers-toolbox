// N16 Adaptive Benchmark API Client
// Tests adaptive kernel performance (spiral vs trochoid)

import axios from 'axios'

const API_BASE = '/cam/adaptive2'

export interface SpiralRequest {
  width: number
  height: number
  tool_dia: number
  stepover: number
  corner_fillet?: number
}

export interface TrochoidRequest {
  width: number
  height: number
  tool_dia: number
  loop_pitch: number
  amp: number
}

/**
 * Generate offset spiral benchmark
 * POST /cam/adaptive2/offset_spiral.svg
 * Returns raw SVG string
 */
export async function benchmarkOffsetSpiral(request: SpiralRequest): Promise<string> {
  const response = await axios.post(`${API_BASE}/offset_spiral.svg`, request, {
    responseType: 'text'
  })
  return response.data
}

/**
 * Generate trochoid corners benchmark
 * POST /cam/adaptive2/trochoid_corners.svg
 * Returns raw SVG string
 */
export async function benchmarkTrochoidCorners(request: TrochoidRequest): Promise<string> {
  const response = await axios.post(`${API_BASE}/trochoid_corners.svg`, request, {
    responseType: 'text'
  })
  return response.data
}


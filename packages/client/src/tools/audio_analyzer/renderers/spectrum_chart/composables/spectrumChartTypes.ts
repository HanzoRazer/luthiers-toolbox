/**
 * SpectrumChartRenderer type definitions.
 */

// ============================================================================
// Data Types
// ============================================================================

export interface SpectrumRow {
  freq_hz: number
  H_mag: number
  coherence: number
  phase_deg: number
}

export interface PeakData {
  freq_hz: number
  label?: string
  peakIndex: number
  raw: any
}

// ============================================================================
// Event Payload
// ============================================================================

export interface PeakSelectedPayload {
  spectrumRelpath: string
  peakIndex: number
  freq_hz: number
  label?: string
  raw: unknown
}

// ============================================================================
// Constants
// ============================================================================

export const MAX_CHART_POINTS = 2000

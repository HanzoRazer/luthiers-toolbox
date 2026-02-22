/**
 * WsiCurveRenderer types.
 */

export interface WsiRow {
  freq_hz: number
  wsi: number
  loc: number
  grad: number
  phase_disorder: number
  coh_mean: number
  admissible: boolean
}

export interface PeakSelectedPayload {
  spectrumRelpath: string
  peakIndex: number
  freq_hz: number
  label?: string
  raw: unknown
}

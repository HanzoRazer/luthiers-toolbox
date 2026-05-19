/**
 * Residual Trend Types
 *
 * Dev Order 31: Residual consistency trend indicators.
 * Observational only — does NOT calibrate, correct, or recommend changes.
 */

export type ResidualTrendDirection =
  | 'insufficient_data'
  | 'estimate_low'
  | 'estimate_high'
  | 'mixed'

export interface ResidualTrendSummary {
  id: string
  label: string
  direction: ResidualTrendDirection
  availableResidualCount: number
  positiveResidualCount: number
  negativeResidualCount: number
  zeroResidualCount: number
  message: string
  caution: string
}

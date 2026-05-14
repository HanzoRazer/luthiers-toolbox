/**
 * Residual Stability Types
 *
 * Dev Order 32: Residual stability classification.
 * Qualitative and observational only — does NOT validate, calibrate, or correct.
 */

export type ResidualStabilityLevel =
  | 'insufficient'
  | 'sparse'
  | 'stable'
  | 'volatile'

export interface ResidualStabilitySummary {
  id: string
  label: string
  level: ResidualStabilityLevel

  availableResidualCount: number
  largeResidualCount: number
  moderateResidualCount: number
  smallResidualCount: number

  trendDirection: string

  message: string
  caution: string
  notes: string[]
}

/**
 * Residual Coherence Types
 *
 * Dev Order 33: Residual coherence summary layer.
 * Synthesizes interpretation, trend, and stability into a single observational summary.
 * Descriptive only — does NOT calibrate, validate, or correct the model.
 */

export type ResidualCoherenceLevel =
  | 'insufficient'
  | 'sparse'
  | 'coherent'
  | 'mixed'

export interface ResidualCoherenceSummary {
  id: string
  label: string

  level: ResidualCoherenceLevel

  interpretationLevel?: string
  trendDirection?: string
  stabilityLevel?: string

  message: string
  caution: string
  notes: string[]
}

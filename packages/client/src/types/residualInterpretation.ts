/**
 * Residual Interpretation Types
 *
 * Dev Order 30: Qualitative residual magnitude labels.
 * Interpretive guidance only — does NOT calibrate, correct, or validate.
 */

export type ResidualInterpretationLevel =
  | 'insufficient_data'
  | 'small'
  | 'moderate'
  | 'large'

export interface ResidualInterpretationItem {
  id: string
  label: string
  level: ResidualInterpretationLevel
  residual?: number
  percentResidual?: number | null
  unit?: string
  message: string
  caution: string
}

export interface ResidualInterpretationSummary {
  id: string
  label: string
  items: ResidualInterpretationItem[]
  overallLevel: ResidualInterpretationLevel
  notes: string[]
}

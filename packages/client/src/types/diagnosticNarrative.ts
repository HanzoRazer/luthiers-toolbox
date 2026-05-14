/**
 * Diagnostic Narrative Types
 *
 * Dev Order 34: Human-readable diagnostic summary layer.
 * Deterministic rule-based synthesis only — does NOT calibrate,
 * validate, optimize, or predict.
 */

export type DiagnosticNarrativeTone =
  | 'insufficient'
  | 'sparse'
  | 'coherent'
  | 'mixed'

export interface DiagnosticNarrativeSummary {
  id: string
  label: string

  tone: DiagnosticNarrativeTone

  narrative: string

  supportingObservations: string[]

  caution: string

  provenanceReminder: string
}

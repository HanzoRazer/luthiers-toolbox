/**
 * Shared workflow types for NECK-A, Aperture, and future diagnostic workflows.
 */

export type WorkflowGateLevel = 'green' | 'yellow' | 'red'

export interface WorkflowDiagnostic {
  id: string
  gate: WorkflowGateLevel
  message: string
  probable_causes?: string[]
  recommended_checks?: string[]
  recommended_actions?: string[]
  confidence?: number
}

export interface WorkflowResponse {
  overall_gate: WorkflowGateLevel
  diagnostics: WorkflowDiagnostic[]
}

export interface WorkflowPrerequisite {
  label: string
  satisfied: boolean
}

/**
 * Diagnostic Snapshot Import Validation Types
 *
 * Dev Order 39: Import validation scaffold.
 * Validates exported diagnostic snapshot JSON files without restoring them.
 * Does NOT mutate state, restore sessions, or perform calibration.
 */

export type DiagnosticSnapshotImportGate = 'green' | 'yellow' | 'red'

export interface DiagnosticSnapshotImportDiagnostic {
  id: string
  gate: DiagnosticSnapshotImportGate
  message: string
  recommendedAction?: string
}

export interface DiagnosticSnapshotImportValidation {
  overallGate: DiagnosticSnapshotImportGate
  valid: boolean
  schemaVersion?: string
  kind?: string
  sectionCount?: number
  createdAtIso?: string
  diagnostics: DiagnosticSnapshotImportDiagnostic[]
}

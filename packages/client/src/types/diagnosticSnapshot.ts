/**
 * Diagnostic Snapshot Types
 *
 * Dev Order 36: Diagnostic session snapshot scaffold.
 * Dev Order 37: Export preparation — schema versioning, normalization, export readiness.
 * Dev Order 38: JSON export — client-side snapshot download.
 * Captures observational diagnostic state for future export workflows.
 * Does NOT persist, calibrate, or predict.
 */

export interface DiagnosticSnapshotSection {
  label: string
  available: boolean
  summary: string
}

export interface DiagnosticSnapshot {
  schemaVersion: 'diagnostic-snapshot.v1'
  kind: 'aperture-diagnostic-snapshot'

  id: string

  createdAtIso: string

  referenceLabel: string
  candidateLabel: string

  sections: DiagnosticSnapshotSection[]

  readinessLevel?: string

  narrativeSummary?: string

  provenanceReminder: string

  observationalOnly: true

  exportReady: boolean
  exportWarnings: string[]
}

export type DiagnosticSnapshotExportStatus =
  | 'prepared_not_exported'
  | 'exported_json'

export interface DiagnosticSnapshotExportMetadata {
  schemaVersion: 'diagnostic-snapshot.v1'
  kind: 'aperture-diagnostic-snapshot'
  generatedBy: 'aperture-workspace'
  exportPreparedAtIso: string
  exportStatus: DiagnosticSnapshotExportStatus
}

export interface DiagnosticSnapshotJsonExport {
  exportMetadata: DiagnosticSnapshotExportMetadata
  snapshot: DiagnosticSnapshot
}

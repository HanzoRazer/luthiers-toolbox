/**
 * Diagnostic Snapshot JSON Export Utility
 *
 * Dev Order 38: Client-side JSON export of diagnostic snapshots.
 *
 * Observational only — does NOT persist to backend, generate reports,
 * import sessions, or export calibrated predictions.
 */

import type {
  DiagnosticSnapshot,
  DiagnosticSnapshotExportMetadata,
  DiagnosticSnapshotJsonExport,
} from '@/types/diagnosticSnapshot'
import { normalizeDiagnosticSnapshotForExport } from './diagnosticSnapshot'

const SCHEMA_VERSION = 'diagnostic-snapshot.v1' as const
const SNAPSHOT_KIND = 'aperture-diagnostic-snapshot' as const

/**
 * Check if a diagnostic snapshot is ready for export.
 */
export function canExportDiagnosticSnapshot(snapshot: DiagnosticSnapshot): boolean {
  return snapshot.exportReady === true
}

/**
 * Create export metadata for a JSON export.
 */
function createJsonExportMetadata(): DiagnosticSnapshotExportMetadata {
  return {
    schemaVersion: SCHEMA_VERSION,
    kind: SNAPSHOT_KIND,
    generatedBy: 'aperture-workspace',
    exportPreparedAtIso: new Date().toISOString(),
    exportStatus: 'exported_json',
  }
}

/**
 * Create a JSON export payload from a diagnostic snapshot.
 */
export function createDiagnosticSnapshotJsonExport(
  snapshot: DiagnosticSnapshot
): DiagnosticSnapshotJsonExport {
  const normalizedSnapshot = normalizeDiagnosticSnapshotForExport(snapshot)

  return {
    exportMetadata: createJsonExportMetadata(),
    snapshot: normalizedSnapshot,
  }
}

/**
 * Generate a default filename for the snapshot export.
 */
function generateExportFilename(): string {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  const hours = String(now.getHours()).padStart(2, '0')
  const minutes = String(now.getMinutes()).padStart(2, '0')
  const seconds = String(now.getSeconds()).padStart(2, '0')

  return `aperture-diagnostic-snapshot-${year}${month}${day}-${hours}${minutes}${seconds}.json`
}

/**
 * Download a diagnostic snapshot as a JSON file.
 * Throws if the snapshot is not export-ready.
 */
export function downloadDiagnosticSnapshotJson(
  snapshot: DiagnosticSnapshot,
  filename?: string
): void {
  if (!canExportDiagnosticSnapshot(snapshot)) {
    throw new Error('Diagnostic snapshot is not export-ready.')
  }

  const payload = createDiagnosticSnapshotJsonExport(snapshot)
  const jsonString = JSON.stringify(payload, null, 2)
  const blob = new Blob([jsonString], { type: 'application/json' })
  const url = URL.createObjectURL(blob)

  const link = document.createElement('a')
  link.href = url
  link.download = filename ?? generateExportFilename()
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)

  URL.revokeObjectURL(url)
}

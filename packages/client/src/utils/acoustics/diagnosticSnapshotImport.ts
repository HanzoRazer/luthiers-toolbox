/**
 * Diagnostic Snapshot Import Validation Utility
 *
 * Dev Order 39: Validates exported diagnostic snapshot JSON files
 * without restoring them into application state.
 *
 * Validation only — does NOT mutate state, restore sessions, or perform calibration.
 */

import type {
  DiagnosticSnapshotImportGate,
  DiagnosticSnapshotImportDiagnostic,
  DiagnosticSnapshotImportValidation,
} from '@/types/diagnosticSnapshotImport'

const EXPECTED_SCHEMA_VERSION = 'diagnostic-snapshot.v1'
const EXPECTED_KIND = 'aperture-diagnostic-snapshot'

/**
 * Validate a parsed JSON payload as a diagnostic snapshot export.
 * Returns validation result with diagnostics.
 */
export function validateDiagnosticSnapshotJsonImport(
  payload: unknown
): DiagnosticSnapshotImportValidation {
  const diagnostics: DiagnosticSnapshotImportDiagnostic[] = []

  // Check payload is an object
  if (!payload || typeof payload !== 'object') {
    diagnostics.push({
      id: 'invalid-payload',
      gate: 'red',
      message: 'Payload is not a valid object.',
      recommendedAction: 'Ensure the file contains valid JSON.',
    })
    return createResult('red', false, diagnostics)
  }

  const obj = payload as Record<string, unknown>

  // Check exportMetadata exists
  if (!obj.exportMetadata || typeof obj.exportMetadata !== 'object') {
    diagnostics.push({
      id: 'missing-export-metadata',
      gate: 'red',
      message: 'Missing exportMetadata field.',
      recommendedAction: 'This file may not be a valid diagnostic snapshot export.',
    })
    return createResult('red', false, diagnostics)
  }

  // Check snapshot exists
  if (!obj.snapshot || typeof obj.snapshot !== 'object') {
    diagnostics.push({
      id: 'missing-snapshot',
      gate: 'red',
      message: 'Missing snapshot field.',
      recommendedAction: 'This file may not be a valid diagnostic snapshot export.',
    })
    return createResult('red', false, diagnostics)
  }

  const snapshot = obj.snapshot as Record<string, unknown>
  const exportMetadata = obj.exportMetadata as Record<string, unknown>

  // Check schemaVersion
  const schemaVersion = snapshot.schemaVersion as string | undefined
  if (!schemaVersion) {
    diagnostics.push({
      id: 'missing-schema-version',
      gate: 'red',
      message: 'Missing schemaVersion in snapshot.',
      recommendedAction: 'Snapshot must include a schemaVersion field.',
    })
    return createResult('red', false, diagnostics)
  }

  if (schemaVersion !== EXPECTED_SCHEMA_VERSION) {
    diagnostics.push({
      id: 'schema-version-mismatch',
      gate: 'red',
      message: `Schema version "${schemaVersion}" is not supported. Expected "${EXPECTED_SCHEMA_VERSION}".`,
      recommendedAction: 'This snapshot was created with an incompatible schema version.',
    })
    return createResult('red', false, diagnostics, { schemaVersion })
  }

  // Check kind
  const kind = snapshot.kind as string | undefined
  if (kind !== EXPECTED_KIND) {
    diagnostics.push({
      id: 'kind-mismatch',
      gate: 'red',
      message: `Snapshot kind "${kind}" is not supported. Expected "${EXPECTED_KIND}".`,
      recommendedAction: 'This snapshot is not an aperture diagnostic snapshot.',
    })
    return createResult('red', false, diagnostics, { schemaVersion, kind })
  }

  // Check observationalOnly
  if (snapshot.observationalOnly !== true) {
    diagnostics.push({
      id: 'not-observational',
      gate: 'red',
      message: 'Snapshot is not marked as observationalOnly.',
      recommendedAction: 'Only observational snapshots are supported.',
    })
    return createResult('red', false, diagnostics, { schemaVersion, kind })
  }

  // Check sections array
  const sections = snapshot.sections
  if (!Array.isArray(sections)) {
    diagnostics.push({
      id: 'invalid-sections',
      gate: 'red',
      message: 'Snapshot sections is not an array.',
      recommendedAction: 'Snapshot must contain a sections array.',
    })
    return createResult('red', false, diagnostics, { schemaVersion, kind })
  }

  const sectionCount = sections.length
  const createdAtIso = snapshot.createdAtIso as string | undefined

  // Yellow checks

  // Check exportStatus
  if (!exportMetadata.exportStatus) {
    diagnostics.push({
      id: 'missing-export-status',
      gate: 'yellow',
      message: 'Export metadata is missing exportStatus.',
    })
  }

  // Check zero sections
  if (sectionCount === 0) {
    diagnostics.push({
      id: 'zero-sections',
      gate: 'yellow',
      message: 'Snapshot contains zero sections.',
    })
  }

  // Check export warnings
  const exportWarnings = snapshot.exportWarnings
  if (Array.isArray(exportWarnings) && exportWarnings.length > 0) {
    diagnostics.push({
      id: 'has-export-warnings',
      gate: 'yellow',
      message: `Snapshot has ${exportWarnings.length} export warning(s).`,
    })
  }

  // Check timestamp
  if (!createdAtIso) {
    diagnostics.push({
      id: 'missing-timestamp',
      gate: 'yellow',
      message: 'Snapshot is missing createdAtIso timestamp.',
    })
  } else {
    const date = new Date(createdAtIso)
    if (isNaN(date.getTime())) {
      diagnostics.push({
        id: 'invalid-timestamp',
        gate: 'yellow',
        message: 'Snapshot createdAtIso timestamp is invalid.',
      })
    }
  }

  // Determine overall gate
  const hasRed = diagnostics.some((d) => d.gate === 'red')
  const hasYellow = diagnostics.some((d) => d.gate === 'yellow')

  let overallGate: DiagnosticSnapshotImportGate = 'green'
  if (hasRed) {
    overallGate = 'red'
  } else if (hasYellow) {
    overallGate = 'yellow'
  }

  const valid = overallGate !== 'red'

  return {
    overallGate,
    valid,
    schemaVersion,
    kind,
    sectionCount,
    createdAtIso,
    diagnostics,
  }
}

function createResult(
  overallGate: DiagnosticSnapshotImportGate,
  valid: boolean,
  diagnostics: DiagnosticSnapshotImportDiagnostic[],
  metadata?: {
    schemaVersion?: string
    kind?: string
    sectionCount?: number
    createdAtIso?: string
  }
): DiagnosticSnapshotImportValidation {
  return {
    overallGate,
    valid,
    schemaVersion: metadata?.schemaVersion,
    kind: metadata?.kind,
    sectionCount: metadata?.sectionCount,
    createdAtIso: metadata?.createdAtIso,
    diagnostics,
  }
}

export function getImportGateColor(gate: DiagnosticSnapshotImportGate): 'green' | 'yellow' | 'red' {
  return gate
}

export function getImportGateLabel(gate: DiagnosticSnapshotImportGate): string {
  switch (gate) {
    case 'green':
      return 'Valid'
    case 'yellow':
      return 'Valid with Warnings'
    case 'red':
      return 'Invalid'
  }
}

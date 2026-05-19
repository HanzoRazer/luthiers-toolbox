/**
 * Diagnostic Session Snapshot Utility
 *
 * Dev Order 36: Creates structured observational diagnostic snapshots
 * for future export workflows.
 * Dev Order 37: Export preparation — schema versioning, normalization, export readiness.
 *
 * Observational only — does NOT persist, calibrate, or predict.
 */

import type { DiagnosticNarrativeSummary } from '@/types/diagnosticNarrative'
import type { CalibrationReadiness } from '@/types/calibration'
import type { ResidualCoherenceSummary } from '@/types/residualCoherence'
import type {
  DiagnosticSnapshot,
  DiagnosticSnapshotSection,
  DiagnosticSnapshotExportMetadata,
} from '@/types/diagnosticSnapshot'

const SCHEMA_VERSION = 'diagnostic-snapshot.v1' as const
const SNAPSHOT_KIND = 'aperture-diagnostic-snapshot' as const

const PROVENANCE_REMINDER =
  'All diagnostic summaries remain observational and non-calibrated. Snapshots document state only and do not validate predictions.'

export function createDiagnosticSnapshot(params: {
  id: string

  referenceNarrative?: DiagnosticNarrativeSummary
  candidateNarrative?: DiagnosticNarrativeSummary

  calibrationReadiness?: CalibrationReadiness

  referenceCoherence?: ResidualCoherenceSummary
  candidateCoherence?: ResidualCoherenceSummary
}): DiagnosticSnapshot {
  const {
    id,
    referenceNarrative,
    candidateNarrative,
    calibrationReadiness,
    referenceCoherence,
    candidateCoherence,
  } = params

  const sections: DiagnosticSnapshotSection[] = []

  // Reference Diagnostic Narrative
  sections.push({
    label: 'Reference Diagnostic Narrative',
    available: !!referenceNarrative,
    summary: referenceNarrative?.narrative ?? 'No narrative available',
  })

  // Candidate Diagnostic Narrative
  sections.push({
    label: 'Candidate Diagnostic Narrative',
    available: !!candidateNarrative,
    summary: candidateNarrative?.narrative ?? 'No narrative available',
  })

  // Reference Residual Coherence
  sections.push({
    label: 'Reference Residual Coherence',
    available: !!referenceCoherence,
    summary: referenceCoherence
      ? `${referenceCoherence.level}: ${referenceCoherence.message}`
      : 'No coherence data available',
  })

  // Candidate Residual Coherence
  sections.push({
    label: 'Candidate Residual Coherence',
    available: !!candidateCoherence,
    summary: candidateCoherence
      ? `${candidateCoherence.level}: ${candidateCoherence.message}`
      : 'No coherence data available',
  })

  // Calibration Readiness
  sections.push({
    label: 'Calibration Readiness',
    available: !!calibrationReadiness,
    summary: calibrationReadiness
      ? `${calibrationReadiness.overallGate}: ${calibrationReadiness.readyForCalibration ? 'Ready' : 'Not ready'}`
      : 'No readiness data available',
  })

  // Derive top-level summaries
  const readinessLevel = calibrationReadiness?.overallGate

  const narrativeSummary = deriveNarrativeSummary(referenceNarrative, candidateNarrative)

  // Generate export warnings
  const exportWarnings = generateExportWarnings(sections)

  return {
    schemaVersion: SCHEMA_VERSION,
    kind: SNAPSHOT_KIND,
    id,
    createdAtIso: new Date().toISOString(),
    referenceLabel: 'Reference',
    candidateLabel: 'Candidate',
    sections,
    readinessLevel,
    narrativeSummary,
    provenanceReminder: PROVENANCE_REMINDER,
    observationalOnly: true,
    exportReady: true,
    exportWarnings,
  }
}

function generateExportWarnings(sections: DiagnosticSnapshotSection[]): string[] {
  const warnings: string[] = []

  const unavailableCount = sections.filter((s) => !s.available).length
  if (unavailableCount > 0) {
    warnings.push('Some diagnostic sections are currently unavailable.')
  }

  const availableCount = sections.filter((s) => s.available).length
  if (availableCount < sections.length / 2) {
    warnings.push('Snapshot contains limited observational data.')
  }

  warnings.push('Snapshot is observational only.')

  return warnings
}

function deriveNarrativeSummary(
  reference?: DiagnosticNarrativeSummary,
  candidate?: DiagnosticNarrativeSummary
): string | undefined {
  if (!reference && !candidate) {
    return undefined
  }

  const parts: string[] = []

  if (reference) {
    parts.push(`Reference: ${reference.tone}`)
  }

  if (candidate) {
    parts.push(`Candidate: ${candidate.tone}`)
  }

  return parts.join(' | ')
}

export function countAvailableSections(snapshot: DiagnosticSnapshot): number {
  return snapshot.sections.filter((s) => s.available).length
}

export function getSnapshotGateColor(
  readinessLevel?: string
): 'green' | 'yellow' | 'red' {
  switch (readinessLevel) {
    case 'green':
      return 'green'
    case 'yellow':
      return 'yellow'
    case 'red':
      return 'red'
    default:
      return 'yellow'
  }
}

/**
 * Normalize a diagnostic snapshot for export.
 * Ensures schema version, kind, export readiness, and JSON-safe structure.
 */
export function normalizeDiagnosticSnapshotForExport(
  snapshot: DiagnosticSnapshot
): DiagnosticSnapshot {
  const warnings: string[] = [...snapshot.exportWarnings]

  // Validate required fields
  const missingFields: string[] = []

  if (!snapshot.schemaVersion) missingFields.push('schemaVersion')
  if (!snapshot.kind) missingFields.push('kind')
  if (!snapshot.id) missingFields.push('id')
  if (!snapshot.createdAtIso) missingFields.push('createdAtIso')
  if (!snapshot.sections) missingFields.push('sections')
  if (snapshot.observationalOnly !== true) missingFields.push('observationalOnly')

  const exportReady = missingFields.length === 0

  if (!exportReady) {
    warnings.unshift(`Missing required fields: ${missingFields.join(', ')}`)
  }

  // Return normalized snapshot with JSON-safe values
  return removeUndefinedFields({
    schemaVersion: snapshot.schemaVersion ?? SCHEMA_VERSION,
    kind: snapshot.kind ?? SNAPSHOT_KIND,
    id: snapshot.id,
    createdAtIso: snapshot.createdAtIso,
    referenceLabel: snapshot.referenceLabel,
    candidateLabel: snapshot.candidateLabel,
    sections: snapshot.sections,
    readinessLevel: snapshot.readinessLevel,
    narrativeSummary: snapshot.narrativeSummary,
    provenanceReminder: snapshot.provenanceReminder,
    observationalOnly: true as const,
    exportReady,
    exportWarnings: warnings,
  })
}

/**
 * Create export metadata for a diagnostic snapshot.
 * Does NOT perform export — only generates metadata structure.
 */
export function createDiagnosticSnapshotExportMetadata(): DiagnosticSnapshotExportMetadata {
  return {
    schemaVersion: SCHEMA_VERSION,
    kind: SNAPSHOT_KIND,
    generatedBy: 'aperture-workspace',
    exportPreparedAtIso: new Date().toISOString(),
    exportStatus: 'prepared_not_exported',
  }
}

/**
 * Remove undefined fields from an object for JSON safety.
 */
function removeUndefinedFields<T extends Record<string, unknown>>(obj: T): T {
  const result: Record<string, unknown> = {}

  for (const [key, value] of Object.entries(obj)) {
    if (value !== undefined) {
      result[key] = value
    }
  }

  return result as T
}

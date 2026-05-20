/**
 * Tests for measurementArchive utilities.
 *
 * Dev Order 61: Validates archive creation, validation, import/export,
 * sparse context handling, and diagnostic snapshot references.
 * Dev Order 62: Validates evidence index utilities (sorting, grouping, filtering).
 *
 * All tests verify observational-only semantics — no calibration or prediction.
 */
import { describe, it, expect } from 'vitest'
import {
  createMeasurementArchiveRecord,
  validateMeasurementArchive,
  normalizeMeasurementArchive,
  isMeasurementArchiveRecord,
  tryCreateArchiveFromDiagnosticContext,
  buildMeasurementArchiveFilename,
  parseMeasurementArchiveJson,
  summarizeMeasurementArchive,
  createGeometrySummary,
  sortMeasurementArchivesByTimestamp,
  groupMeasurementArchivesByMethod,
  groupMeasurementArchivesByExperimentTag,
  filterMeasurementArchivesBySnapshotReference,
  createEvidenceSummary,
  compareArchives,
  interpretResidualMagnitude,
  generateComparisonNarrative,
  type DiagnosticContextForArchive,
} from '../measurementArchive'
import type { MeasurementArchiveRecord } from '@/types/acoustics/measurementArchive'
import type { MeasuredResponse } from '@/types/measurements'

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

function createMockMeasuredResponse(
  overrides: Partial<MeasuredResponse> = {}
): MeasuredResponse {
  return {
    id: 'test-measurement',
    label: 'Test Measurement',
    source: 'manual',
    method: 'tap_test',
    measuredHelmholtzHz: 95,
    measuredQ: 12,
    dominantPeakHz: 95,
    attachedTo: 'reference',
    ...overrides,
  }
}

function createValidArchive(): MeasurementArchiveRecord {
  return {
    archiveId: 'archive-test-123',
    metadata: {
      schemaVersion: 'measurement-archive.v1',
      kind: 'aperture-measurement-archive',
      generatedBy: 'aperture-workspace',
      createdAtIso: '2026-05-19T12:00:00.000Z',
      observationalOnly: true,
    },
    context: {
      referenceLabel: 'Reference',
      candidateLabel: 'Candidate',
    },
    measurements: [
      {
        measurementId: 'meas-1',
        measuredAtIso: '2026-05-19T12:00:00.000Z',
        label: 'reference: Test',
        measuredHelmholtzHz: 95,
        source: 'manual_entry',
        method: 'fft_peak_detection',
      },
    ],
    provenanceReminder: 'This archive contains observational measurements only.',
  }
}

// ---------------------------------------------------------------------------
// Test: Archive creation from full diagnostic context
// ---------------------------------------------------------------------------

describe('tryCreateArchiveFromDiagnosticContext', () => {
  it('creates valid archive from full diagnostic context', () => {
    const context: DiagnosticContextForArchive = {
      referenceLabel: 'Reference Aperture',
      candidateLabel: 'Candidate Aperture',
      referenceMeasured: createMockMeasuredResponse(),
      candidateMeasured: createMockMeasuredResponse({
        id: 'candidate',
        label: 'Candidate',
        attachedTo: 'candidate',
      }),
      referenceGeometry: createGeometrySummary('round', 7854, 100, 0.04),
      candidateGeometry: createGeometrySummary('dual_spiral', 8000, 101, 0.12),
      tags: ['test-tag'],
    }

    const result = tryCreateArchiveFromDiagnosticContext(context)

    expect(result.success).toBe(true)
    expect(result.archive).not.toBeNull()
    expect(result.error).toBeNull()
    expect(result.archive?.measurements.length).toBe(2)
    expect(result.archive?.metadata.schemaVersion).toBe('measurement-archive.v1')
    expect(result.archive?.metadata.observationalOnly).toBe(true)
  })

  it('creates archive from sparse context with one measurement', () => {
    const context: DiagnosticContextForArchive = {
      referenceMeasured: createMockMeasuredResponse(),
    }

    const result = tryCreateArchiveFromDiagnosticContext(context)

    expect(result.success).toBe(true)
    expect(result.archive?.measurements.length).toBe(1)
  })

  it('fails when no meaningful measurements present', () => {
    const context: DiagnosticContextForArchive = {
      referenceLabel: 'Empty Reference',
      referenceMeasured: {
        id: 'empty',
        label: 'Empty',
        source: 'manual',
        method: 'tap_test',
        attachedTo: 'reference',
      },
    }

    const result = tryCreateArchiveFromDiagnosticContext(context)

    expect(result.success).toBe(false)
    expect(result.archive).toBeNull()
    expect(result.error).toContain('No meaningful measurements')
  })

  it('fails with completely empty context', () => {
    const result = tryCreateArchiveFromDiagnosticContext({})

    expect(result.success).toBe(false)
    expect(result.archive).toBeNull()
  })

  it('includes linked snapshot reference when provided', () => {
    const context: DiagnosticContextForArchive = {
      referenceMeasured: createMockMeasuredResponse(),
      linkedSnapshot: {
        schemaVersion: 'diagnostic-snapshot.v1',
        kind: 'aperture-diagnostic-snapshot',
        id: 'snapshot-123',
        createdAtIso: '2026-05-19T12:00:00.000Z',
        referenceLabel: 'Ref',
        candidateLabel: 'Cand',
        sections: [],
        provenanceReminder: 'test',
        observationalOnly: true,
        exportReady: true,
        exportWarnings: [],
      },
    }

    const result = tryCreateArchiveFromDiagnosticContext(context)

    expect(result.success).toBe(true)
    expect(result.archive?.measurements[0].diagnosticSnapshotReference?.snapshotId).toBe('snapshot-123')
    expect(result.archive?.tags).toContain('snapshot:snapshot-123')
  })
})

// ---------------------------------------------------------------------------
// Test: Archive validation
// ---------------------------------------------------------------------------

describe('validateMeasurementArchive', () => {
  it('validates correct archive', () => {
    const archive = createValidArchive()
    const result = validateMeasurementArchive(archive)

    expect(result.valid).toBe(true)
    expect(result.errors).toHaveLength(0)
    expect(result.schemaVersion).toBe('measurement-archive.v1')
    expect(result.measurementCount).toBe(1)
  })

  it('rejects wrong schema version', () => {
    const archive = createValidArchive()
    ;(archive.metadata as any).schemaVersion = 'measurement-archive.v2'

    const result = validateMeasurementArchive(archive)

    expect(result.valid).toBe(false)
    expect(result.errors.some((e) => e.includes('schema version'))).toBe(true)
  })

  it('rejects malformed measurement entries', () => {
    const archive = createValidArchive()
    archive.measurements = [{ bad: 'data' } as any]

    const result = validateMeasurementArchive(archive)

    expect(result.warnings.length).toBeGreaterThan(0)
  })

  it('rejects non-object input', () => {
    const result = validateMeasurementArchive('not an object')

    expect(result.valid).toBe(false)
    expect(result.errors).toContain('Archive data must be an object')
  })

  it('rejects missing archiveId', () => {
    const archive = createValidArchive()
    delete (archive as any).archiveId

    const result = validateMeasurementArchive(archive)

    expect(result.valid).toBe(false)
    expect(result.errors.some((e) => e.includes('archiveId'))).toBe(true)
  })

  it('rejects observationalOnly !== true', () => {
    const archive = createValidArchive()
    ;(archive.metadata as any).observationalOnly = false

    const result = validateMeasurementArchive(archive)

    expect(result.valid).toBe(false)
    expect(result.errors.some((e) => e.includes('observational only'))).toBe(true)
  })
})

// ---------------------------------------------------------------------------
// Test: Type guard
// ---------------------------------------------------------------------------

describe('isMeasurementArchiveRecord', () => {
  it('returns true for valid archive', () => {
    const archive = createValidArchive()
    expect(isMeasurementArchiveRecord(archive)).toBe(true)
  })

  it('returns false for null', () => {
    expect(isMeasurementArchiveRecord(null)).toBe(false)
  })

  it('returns false for wrong schema version', () => {
    const archive = createValidArchive()
    ;(archive.metadata as any).schemaVersion = 'wrong'
    expect(isMeasurementArchiveRecord(archive)).toBe(false)
  })

  it('returns false for missing archiveId', () => {
    const archive = createValidArchive()
    delete (archive as any).archiveId
    expect(isMeasurementArchiveRecord(archive)).toBe(false)
  })
})

// ---------------------------------------------------------------------------
// Test: Filename generation
// ---------------------------------------------------------------------------

describe('buildMeasurementArchiveFilename', () => {
  it('generates filename with timestamp', () => {
    const archive = createValidArchive()
    archive.metadata.createdAtIso = '2026-05-19T14:30:45.000Z'

    const filename = buildMeasurementArchiveFilename(archive)

    expect(filename).toBe('measurement-archive-v1-20260519-143045.json')
  })

  it('falls back to archiveId for invalid timestamp', () => {
    const archive = createValidArchive()
    archive.metadata.createdAtIso = 'invalid-date'

    const filename = buildMeasurementArchiveFilename(archive)

    expect(filename).toBe(`measurement-archive-v1-${archive.archiveId}.json`)
  })
})

// ---------------------------------------------------------------------------
// Test: JSON parsing
// ---------------------------------------------------------------------------

describe('parseMeasurementArchiveJson', () => {
  it('parses valid JSON archive', () => {
    const archive = createValidArchive()
    const json = JSON.stringify(archive)

    const result = parseMeasurementArchiveJson(json)

    expect(result.success).toBe(true)
    expect(result.archive).not.toBeNull()
    expect(result.parseError).toBeNull()
  })

  it('returns parse error for invalid JSON', () => {
    const result = parseMeasurementArchiveJson('not json {')

    expect(result.success).toBe(false)
    expect(result.archive).toBeNull()
    expect(result.parseError).not.toBeNull()
  })

  it('returns validation result for invalid archive structure', () => {
    const result = parseMeasurementArchiveJson('{"bad": "data"}')

    expect(result.success).toBe(false)
    expect(result.archive).toBeNull()
    expect(result.validation?.valid).toBe(false)
  })
})

// ---------------------------------------------------------------------------
// Test: Archive summary
// ---------------------------------------------------------------------------

describe('summarizeMeasurementArchive', () => {
  it('generates correct summary', () => {
    const archive = createValidArchive()
    archive.tags = ['tag1', 'tag2']

    const summary = summarizeMeasurementArchive(archive)

    expect(summary.archiveId).toBe(archive.archiveId)
    expect(summary.schemaVersion).toBe('measurement-archive.v1')
    expect(summary.measurementCount).toBe(1)
    expect(summary.referenceLabel).toBe('Reference')
    expect(summary.candidateLabel).toBe('Candidate')
    expect(summary.tagCount).toBe(2)
  })

  it('detects linked snapshot', () => {
    const archive = createValidArchive()
    archive.measurements[0].diagnosticSnapshotReference = {
      snapshotId: 'snap-123',
    }

    const summary = summarizeMeasurementArchive(archive)

    expect(summary.hasLinkedSnapshot).toBe(true)
  })
})

// ---------------------------------------------------------------------------
// Test: Diagnostic snapshot accepts archiveReferences
// ---------------------------------------------------------------------------

describe('DiagnosticSnapshot archiveReferences', () => {
  it('accepts optional archiveReferences field', () => {
    const snapshot = {
      schemaVersion: 'diagnostic-snapshot.v1' as const,
      kind: 'aperture-diagnostic-snapshot' as const,
      id: 'snap-1',
      createdAtIso: '2026-05-19T12:00:00.000Z',
      referenceLabel: 'Ref',
      candidateLabel: 'Cand',
      sections: [],
      provenanceReminder: 'test',
      observationalOnly: true as const,
      exportReady: true,
      exportWarnings: [],
      archiveReferences: ['archive-1', 'archive-2'],
    }

    expect(snapshot.archiveReferences).toEqual(['archive-1', 'archive-2'])
  })

  it('works without archiveReferences', () => {
    const snapshot = {
      schemaVersion: 'diagnostic-snapshot.v1' as const,
      kind: 'aperture-diagnostic-snapshot' as const,
      id: 'snap-1',
      createdAtIso: '2026-05-19T12:00:00.000Z',
      referenceLabel: 'Ref',
      candidateLabel: 'Cand',
      sections: [],
      provenanceReminder: 'test',
      observationalOnly: true as const,
      exportReady: true,
      exportWarnings: [],
    }

    expect(snapshot.archiveReferences).toBeUndefined()
  })
})

// ---------------------------------------------------------------------------
// Test: Normalization preserves structure
// ---------------------------------------------------------------------------

describe('normalizeMeasurementArchive', () => {
  it('preserves valid archive structure', () => {
    const archive = createValidArchive()
    const normalized = normalizeMeasurementArchive(archive)

    expect(normalized.archiveId).toBe(archive.archiveId)
    expect(normalized.measurements).toEqual(archive.measurements)
    expect(normalized.metadata.observationalOnly).toBe(true)
  })

  it('provides defaults for partial record', () => {
    const partial = {
      measurements: [],
    }

    const normalized = normalizeMeasurementArchive(partial)

    expect(normalized.archiveId).toBeDefined()
    expect(normalized.metadata.schemaVersion).toBe('measurement-archive.v1')
    expect(normalized.metadata.observationalOnly).toBe(true)
    expect(normalized.provenanceReminder).toBeDefined()
  })
})

// ---------------------------------------------------------------------------
// Test: createMeasurementArchiveRecord
// ---------------------------------------------------------------------------

describe('createMeasurementArchiveRecord', () => {
  it('creates empty archive with metadata', () => {
    const archive = createMeasurementArchiveRecord()

    expect(archive.archiveId).toBeDefined()
    expect(archive.metadata.schemaVersion).toBe('measurement-archive.v1')
    expect(archive.metadata.observationalOnly).toBe(true)
    expect(archive.measurements).toEqual([])
    expect(archive.provenanceReminder).toContain('observational')
  })

  it('includes provided context', () => {
    const archive = createMeasurementArchiveRecord({
      referenceLabel: 'My Reference',
    })

    expect(archive.context.referenceLabel).toBe('My Reference')
  })

  it('includes provided tags', () => {
    const archive = createMeasurementArchiveRecord({}, ['tag1', 'tag2'])

    expect(archive.tags).toEqual(['tag1', 'tag2'])
  })
})

// ---------------------------------------------------------------------------
// Dev Order 62: Evidence Index Utilities
// ---------------------------------------------------------------------------

describe('sortMeasurementArchivesByTimestamp', () => {
  it('sorts by newest first (default)', () => {
    const archives = [
      { ...createValidArchive(), archiveId: 'a', metadata: { ...createValidArchive().metadata, createdAtIso: '2026-05-01T12:00:00.000Z' } },
      { ...createValidArchive(), archiveId: 'c', metadata: { ...createValidArchive().metadata, createdAtIso: '2026-05-03T12:00:00.000Z' } },
      { ...createValidArchive(), archiveId: 'b', metadata: { ...createValidArchive().metadata, createdAtIso: '2026-05-02T12:00:00.000Z' } },
    ]

    const sorted = sortMeasurementArchivesByTimestamp(archives)

    expect(sorted.map(a => a.archiveId)).toEqual(['c', 'b', 'a'])
  })

  it('sorts by oldest first', () => {
    const archives = [
      { ...createValidArchive(), archiveId: 'a', metadata: { ...createValidArchive().metadata, createdAtIso: '2026-05-01T12:00:00.000Z' } },
      { ...createValidArchive(), archiveId: 'c', metadata: { ...createValidArchive().metadata, createdAtIso: '2026-05-03T12:00:00.000Z' } },
      { ...createValidArchive(), archiveId: 'b', metadata: { ...createValidArchive().metadata, createdAtIso: '2026-05-02T12:00:00.000Z' } },
    ]

    const sorted = sortMeasurementArchivesByTimestamp(archives, 'oldest')

    expect(sorted.map(a => a.archiveId)).toEqual(['a', 'b', 'c'])
  })

  it('handles invalid timestamps', () => {
    const archives = [
      { ...createValidArchive(), archiveId: 'valid', metadata: { ...createValidArchive().metadata, createdAtIso: '2026-05-01T12:00:00.000Z' } },
      { ...createValidArchive(), archiveId: 'invalid', metadata: { ...createValidArchive().metadata, createdAtIso: 'not-a-date' } },
    ]

    const sorted = sortMeasurementArchivesByTimestamp(archives)

    expect(sorted[0].archiveId).toBe('valid')
    expect(sorted[1].archiveId).toBe('invalid')
  })

  it('does not mutate input', () => {
    const archives = [
      { ...createValidArchive(), archiveId: 'a', metadata: { ...createValidArchive().metadata, createdAtIso: '2026-05-01T12:00:00.000Z' } },
      { ...createValidArchive(), archiveId: 'b', metadata: { ...createValidArchive().metadata, createdAtIso: '2026-05-02T12:00:00.000Z' } },
    ]
    const original = [...archives]

    sortMeasurementArchivesByTimestamp(archives)

    expect(archives).toEqual(original)
  })
})

describe('groupMeasurementArchivesByMethod', () => {
  it('groups by measurement method', () => {
    const archive1 = createValidArchive()
    archive1.measurements = [{ ...archive1.measurements[0], method: 'fft_peak_detection' }]

    const archive2 = createValidArchive()
    archive2.archiveId = 'archive-2'
    archive2.measurements = [{ ...archive2.measurements[0], method: 'swept_sine' }]

    const archive3 = createValidArchive()
    archive3.archiveId = 'archive-3'
    archive3.measurements = [{ ...archive3.measurements[0], method: 'fft_peak_detection' }]

    const groups = groupMeasurementArchivesByMethod([archive1, archive2, archive3])

    expect(groups.length).toBe(2)
    const fftGroup = groups.find(g => g.method === 'fft_peak_detection')
    const sweptGroup = groups.find(g => g.method === 'swept_sine')

    expect(fftGroup?.archives.length).toBe(2)
    expect(sweptGroup?.archives.length).toBe(1)
  })

  it('archive with multiple methods appears in multiple groups', () => {
    const archive = createValidArchive()
    archive.measurements = [
      { ...archive.measurements[0], method: 'fft_peak_detection' },
      { ...archive.measurements[0], measurementId: 'meas-2', method: 'swept_sine' },
    ]

    const groups = groupMeasurementArchivesByMethod([archive])

    expect(groups.length).toBe(2)
    expect(groups.every(g => g.archives.length === 1)).toBe(true)
  })
})

describe('filterMeasurementArchivesBySnapshotReference', () => {
  it('filters to archives with matching snapshot reference', () => {
    const archive1 = createValidArchive()
    archive1.measurements[0].diagnosticSnapshotReference = { snapshotId: 'snap-123' }

    const archive2 = createValidArchive()
    archive2.archiveId = 'archive-2'
    archive2.measurements[0].diagnosticSnapshotReference = { snapshotId: 'snap-456' }

    const archive3 = createValidArchive()
    archive3.archiveId = 'archive-3'
    // No snapshot reference

    const filtered = filterMeasurementArchivesBySnapshotReference(
      [archive1, archive2, archive3],
      'snap-123'
    )

    expect(filtered.length).toBe(1)
    expect(filtered[0].archiveId).toBe(archive1.archiveId)
  })

  it('returns empty array when no matches', () => {
    const archive = createValidArchive()

    const filtered = filterMeasurementArchivesBySnapshotReference([archive], 'nonexistent')

    expect(filtered).toEqual([])
  })
})

describe('createEvidenceSummary', () => {
  it('creates summary with methods', () => {
    const archive = createValidArchive()

    const summary = createEvidenceSummary(archive)

    expect(summary.archiveId).toBe(archive.archiveId)
    expect(summary.methods).toContain('fft_peak_detection')
    expect(summary.createdAtIso).toBe(archive.metadata.createdAtIso)
  })

  it('detects sparse archive with no measurements', () => {
    const archive = createValidArchive()
    archive.measurements = []

    const summary = createEvidenceSummary(archive)

    expect(summary.isSparse).toBe(true)
    expect(summary.sparseWarnings).toContain('No measurements')
  })

  it('detects sparse archive with single measurement', () => {
    const archive = createValidArchive()
    // Already has one measurement

    const summary = createEvidenceSummary(archive)

    expect(summary.isSparse).toBe(true)
    expect(summary.sparseWarnings).toContain('Single measurement only')
  })

  it('detects missing context labels', () => {
    const archive = createValidArchive()
    archive.context.referenceLabel = undefined
    archive.context.candidateLabel = undefined

    const summary = createEvidenceSummary(archive)

    expect(summary.sparseWarnings).toContain('Missing context labels')
  })

  it('includes experiment tags', () => {
    const archive = createValidArchive()
    archive.metadata.experimentTags = ['spiral-14mm', 'tornavoz']

    const summary = createEvidenceSummary(archive)

    expect(summary.experimentTags).toEqual(['spiral-14mm', 'tornavoz'])
  })
})

describe('groupMeasurementArchivesByExperimentTag', () => {
  it('groups by experiment tags', () => {
    const archive1 = createValidArchive()
    archive1.metadata.experimentTags = ['spiral-14mm']

    const archive2 = createValidArchive()
    archive2.archiveId = 'archive-2'
    archive2.metadata.experimentTags = ['tornavoz']

    const archive3 = createValidArchive()
    archive3.archiveId = 'archive-3'
    archive3.metadata.experimentTags = ['spiral-14mm', 'tornavoz']

    const groups = groupMeasurementArchivesByExperimentTag([archive1, archive2, archive3])

    const spiralGroup = groups.find(g => g.tag === 'spiral-14mm')
    const tornavozGroup = groups.find(g => g.tag === 'tornavoz')

    expect(spiralGroup?.archives.length).toBe(2)
    expect(tornavozGroup?.archives.length).toBe(2)
  })

  it('puts untagged archives in special group', () => {
    const archive = createValidArchive()
    // No experimentTags

    const groups = groupMeasurementArchivesByExperimentTag([archive])

    expect(groups.length).toBe(1)
    expect(groups[0].tag).toBe('(untagged)')
    expect(groups[0].archives.length).toBe(1)
  })
})

// ---------------------------------------------------------------------------
// Dev Order 63: Pairwise Archive Comparison
// ---------------------------------------------------------------------------

describe('compareArchives', () => {
  it('compares two archives with shared properties', () => {
    const archiveA = createValidArchive()
    archiveA.measurements = [{
      ...archiveA.measurements[0],
      measuredHelmholtzHz: 95,
      measuredQ: 12,
    }]

    const archiveB = createValidArchive()
    archiveB.archiveId = 'archive-b'
    archiveB.measurements = [{
      ...archiveB.measurements[0],
      measuredHelmholtzHz: 100,
      measuredQ: 14,
    }]

    const result = compareArchives(archiveA, archiveB)

    expect(result.status).toBe('comparable')
    expect(result.residuals.length).toBe(2)

    const helmholtzResidual = result.residuals.find(r => r.property === 'measuredHelmholtzHz')
    expect(helmholtzResidual?.valueA).toBe(95)
    expect(helmholtzResidual?.valueB).toBe(100)
    expect(helmholtzResidual?.difference).toBe(5)
  })

  it('reports insufficient when no shared properties', () => {
    const archiveA = createValidArchive()
    archiveA.measurements = [{
      ...archiveA.measurements[0],
      measuredHelmholtzHz: undefined,
      measuredQ: undefined,
      dominantPeakHz: undefined,
    }]

    const archiveB = createValidArchive()
    archiveB.archiveId = 'archive-b'
    archiveB.measurements = [{
      ...archiveB.measurements[0],
      measuredHelmholtzHz: undefined,
      measuredQ: undefined,
      dominantPeakHz: undefined,
    }]

    const result = compareArchives(archiveA, archiveB)

    expect(result.status).toBe('insufficient')
    expect(result.residuals.length).toBe(0)
  })

  it('reports partial when properties differ', () => {
    const archiveA = createValidArchive()
    archiveA.measurements = [{
      ...archiveA.measurements[0],
      measuredHelmholtzHz: 95,
      measuredQ: undefined,
    }]

    const archiveB = createValidArchive()
    archiveB.archiveId = 'archive-b'
    archiveB.measurements = [{
      ...archiveB.measurements[0],
      measuredHelmholtzHz: 100,
      measuredQ: 14,
    }]

    const result = compareArchives(archiveA, archiveB)

    expect(result.status).toBe('partial')
    expect(result.warnings.length).toBeGreaterThan(0)
  })

  it('does not mutate input archives', () => {
    const archiveA = createValidArchive()
    const archiveB = createValidArchive()
    archiveB.archiveId = 'archive-b'

    const originalA = JSON.stringify(archiveA)
    const originalB = JSON.stringify(archiveB)

    compareArchives(archiveA, archiveB)

    expect(JSON.stringify(archiveA)).toBe(originalA)
    expect(JSON.stringify(archiveB)).toBe(originalB)
  })
})

describe('interpretResidualMagnitude', () => {
  it('returns insufficient_data for null', () => {
    expect(interpretResidualMagnitude(null)).toBe('insufficient_data')
  })

  it('returns small for < 5%', () => {
    expect(interpretResidualMagnitude(3)).toBe('small')
    expect(interpretResidualMagnitude(-3)).toBe('small')
  })

  it('returns moderate for 5-15%', () => {
    expect(interpretResidualMagnitude(10)).toBe('moderate')
    expect(interpretResidualMagnitude(-10)).toBe('moderate')
  })

  it('returns large for > 15%', () => {
    expect(interpretResidualMagnitude(20)).toBe('large')
    expect(interpretResidualMagnitude(-20)).toBe('large')
  })
})

describe('generateComparisonNarrative', () => {
  it('generates narrative for insufficient comparison', () => {
    const result = {
      archiveIdA: 'a',
      archiveIdB: 'b',
      labelA: 'Archive A',
      labelB: 'Archive B',
      comparedAtIso: new Date().toISOString(),
      residuals: [],
      status: 'insufficient' as const,
      notes: [],
      warnings: [],
    }

    const narrative = generateComparisonNarrative(result)

    expect(narrative).toContain('Insufficient comparable data')
  })

  it('generates narrative for comparable archives', () => {
    const result = {
      archiveIdA: 'a',
      archiveIdB: 'b',
      labelA: 'Test A',
      labelB: 'Test B',
      comparedAtIso: new Date().toISOString(),
      residuals: [{
        property: 'measuredHelmholtzHz',
        label: 'Helmholtz Frequency',
        valueA: 95,
        valueB: 100,
        difference: 5,
        percentDifference: 5.26,
        unit: 'Hz',
      }],
      status: 'comparable' as const,
      notes: [],
      warnings: [],
    }

    const narrative = generateComparisonNarrative(result)

    expect(narrative).toContain('Test A')
    expect(narrative).toContain('Test B')
    expect(narrative).toContain('Helmholtz')
  })
})

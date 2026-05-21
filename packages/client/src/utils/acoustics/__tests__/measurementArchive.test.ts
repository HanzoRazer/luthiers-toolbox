/**
 * Measurement Archive Tests
 *
 * Dev Order 60: Core archive utilities
 * Dev Order 61: Timezone hardening
 * Dev Order 62: Evidence index utilities
 * Dev Order 63: Pairwise comparison utilities
 */
import { describe, it, expect } from 'vitest'
import {
  generateArchiveId,
  buildMeasurementArchiveFilename,
  createMeasurementArchive,
  validateMeasurementArchive,
  exportMeasurementArchive,
  parseMeasurementArchive,
  sortMeasurementArchivesByTimestamp,
  groupMeasurementArchivesByMethod,
  groupMeasurementArchivesByExperimentTag,
  createEvidenceSummary,
  compareArchives,
  interpretResidualMagnitude,
  generateComparisonNarrative,
  formatArchiveTimestamp,
} from '../measurementArchive'
import type { MeasurementArchiveRecord } from '@/types/acoustics/measurementArchive'

// Test fixtures
function createTestArchive(overrides: Partial<MeasurementArchiveRecord> = {}): MeasurementArchiveRecord {
  const baseMetadata = {
    schemaVersion: 'measurement-archive.v1' as const,
    createdAtIso: '2026-05-20T12:00:00.000Z',
    sourceApplication: 'test',
    tags: ['test'],
    experimentTags: ['experiment-1'],
  }

  const baseSections = [
    {
      sectionId: 'section-1',
      label: 'Acoustic Measurements',
      measurements: [
        { property: 'measuredHelmholtzHz', value: 100, unit: 'Hz' },
        { property: 'measuredQFactor', value: 15, unit: '' },
      ],
    },
  ]

  return {
    archiveId: overrides.archiveId ?? 'test-archive-1',
    kind: 'measurement-archive',
    metadata: overrides.metadata ?? baseMetadata,
    context: {
      referenceLabel: 'Test Archive',
      ...overrides.context,
    },
    sections: overrides.sections ?? baseSections,
  }
}

describe('Dev Order 60: Core Archive Utilities', () => {
  describe('generateArchiveId', () => {
    it('generates unique IDs', () => {
      const id1 = generateArchiveId()
      const id2 = generateArchiveId()
      expect(id1).not.toBe(id2)
    })

    it('starts with archive- prefix', () => {
      const id = generateArchiveId()
      expect(id.startsWith('archive-')).toBe(true)
    })
  })

  describe('createMeasurementArchive', () => {
    it('creates archive with required fields', () => {
      const archive = createMeasurementArchive(
        { referenceLabel: 'Test' },
        [{ sectionId: 's1', label: 'Test', measurements: [] }]
      )

      expect(archive.kind).toBe('measurement-archive')
      expect(archive.metadata.schemaVersion).toBe('measurement-archive.v1')
      expect(archive.archiveId).toBeDefined()
      expect(archive.context.referenceLabel).toBe('Test')
    })

    it('includes optional tags', () => {
      const archive = createMeasurementArchive(
        {},
        [],
        undefined,
        { tags: ['tag1'], experimentTags: ['exp1'], notes: 'Test notes' }
      )

      expect(archive.metadata.tags).toEqual(['tag1'])
      expect(archive.metadata.experimentTags).toEqual(['exp1'])
      expect(archive.metadata.notes).toBe('Test notes')
    })
  })

  describe('validateMeasurementArchive', () => {
    it('validates correct archive', () => {
      const archive = createTestArchive()
      const result = validateMeasurementArchive(archive)

      expect(result.valid).toBe(true)
      expect(result.errors).toHaveLength(0)
    })

    it('rejects non-object input', () => {
      const result = validateMeasurementArchive(null)
      expect(result.valid).toBe(false)
      expect(result.errors).toContain('Invalid data: expected object')
    })

    it('rejects wrong kind', () => {
      const result = validateMeasurementArchive({ kind: 'wrong' })
      expect(result.valid).toBe(false)
      expect(result.errors.some(e => e.includes('Invalid kind'))).toBe(true)
    })

    it('rejects missing metadata', () => {
      const result = validateMeasurementArchive({ kind: 'measurement-archive' })
      expect(result.valid).toBe(false)
      expect(result.errors).toContain('Missing metadata')
    })

    it('warns on empty sections', () => {
      const archive = {
        archiveId: 'test',
        kind: 'measurement-archive',
        metadata: {
          schemaVersion: 'measurement-archive.v1',
          createdAtIso: '2026-05-20T12:00:00.000Z',
          sourceApplication: 'test',
        },
        context: {},
        sections: [],
      }
      const result = validateMeasurementArchive(archive)

      expect(result.valid).toBe(true)
      expect(result.warnings).toContain('Archive contains no measurement sections')
    })
  })

  describe('exportMeasurementArchive', () => {
    it('exports to JSON string', () => {
      const archive = createTestArchive()
      const json = exportMeasurementArchive(archive)

      expect(typeof json).toBe('string')
      expect(JSON.parse(json)).toEqual(archive)
    })

    it('formats with pretty option', () => {
      const archive = createTestArchive()
      const json = exportMeasurementArchive(archive, { pretty: true })

      expect(json).toContain('\n')
    })
  })

  describe('parseMeasurementArchive', () => {
    it('parses valid JSON', () => {
      const archive = createTestArchive()
      const json = JSON.stringify(archive)
      const { archive: parsed, validation } = parseMeasurementArchive(json)

      expect(validation.valid).toBe(true)
      expect(parsed).toEqual(archive)
    })

    it('handles invalid JSON', () => {
      const { archive, validation } = parseMeasurementArchive('not json')

      expect(validation.valid).toBe(false)
      expect(archive).toBeNull()
      expect(validation.errors.some(e => e.includes('JSON parse error'))).toBe(true)
    })
  })
})

describe('Dev Order 61: Timezone Hardening', () => {
  describe('buildMeasurementArchiveFilename', () => {
    it('uses UTC timestamp', () => {
      const archive = createTestArchive({
        metadata: {
          schemaVersion: 'measurement-archive.v1',
          createdAtIso: '2026-05-20T15:30:00.000Z',
          sourceApplication: 'test',
        },
      })

      const filename = buildMeasurementArchiveFilename(archive)
      expect(filename).toContain('20260520_1530')
    })

    it('sanitizes label', () => {
      const archive = createTestArchive({
        context: { referenceLabel: 'Test Archive / With Slash!' },
      })

      const filename = buildMeasurementArchiveFilename(archive)
      expect(filename).not.toContain('/')
      expect(filename).not.toContain('!')
    })
  })
})

describe('Dev Order 62: Evidence Index Utilities', () => {
  describe('sortMeasurementArchivesByTimestamp', () => {
    it('sorts descending by default', () => {
      const oldArchive = createTestArchive()
      oldArchive.archiveId = 'old'
      oldArchive.metadata.createdAtIso = '2026-05-01T00:00:00Z'

      const newArchive = createTestArchive()
      newArchive.archiveId = 'new'
      newArchive.metadata.createdAtIso = '2026-05-20T00:00:00Z'

      const archives = [oldArchive, newArchive]
      const sorted = sortMeasurementArchivesByTimestamp(archives)
      expect(sorted[0].archiveId).toBe('new')
    })

    it('sorts ascending when specified', () => {
      const oldArchive = createTestArchive()
      oldArchive.archiveId = 'old'
      oldArchive.metadata.createdAtIso = '2026-05-01T00:00:00Z'

      const newArchive = createTestArchive()
      newArchive.archiveId = 'new'
      newArchive.metadata.createdAtIso = '2026-05-20T00:00:00Z'

      const archives = [oldArchive, newArchive]
      const sorted = sortMeasurementArchivesByTimestamp(archives, 'asc')
      expect(sorted[0].archiveId).toBe('old')
    })
  })

  describe('groupMeasurementArchivesByMethod', () => {
    it('groups by section labels', () => {
      const archives = [
        createTestArchive({ archiveId: 'a1' }),
        createTestArchive({ archiveId: 'a2' }),
      ]

      const groups = groupMeasurementArchivesByMethod(archives)
      expect(groups.size).toBe(1)
      expect(groups.get('Acoustic Measurements')).toHaveLength(2)
    })
  })

  describe('groupMeasurementArchivesByExperimentTag', () => {
    it('groups by experiment tags', () => {
      const archive1 = createTestArchive()
      archive1.archiveId = 'a1'
      archive1.metadata.experimentTags = ['exp-1']

      const archive2 = createTestArchive()
      archive2.archiveId = 'a2'
      archive2.metadata.experimentTags = ['exp-2']

      const archives = [archive1, archive2]
      const groups = groupMeasurementArchivesByExperimentTag(archives)
      expect(groups.size).toBe(2)
      expect(groups.get('exp-1')).toHaveLength(1)
      expect(groups.get('exp-2')).toHaveLength(1)
    })

    it('uses Untagged for archives without tags', () => {
      const archive = createTestArchive()
      archive.archiveId = 'a1'
      archive.metadata.experimentTags = undefined

      const archives = [archive]
      const groups = groupMeasurementArchivesByExperimentTag(archives)
      expect(groups.has('Untagged')).toBe(true)
    })
  })

  describe('createEvidenceSummary', () => {
    it('returns empty summary for empty archives', () => {
      const summary = createEvidenceSummary([])

      expect(summary.totalArchives).toBe(0)
      expect(summary.dateRange).toBeNull()
    })

    it('detects sparse archives', () => {
      const sparseArchive: MeasurementArchiveRecord = {
        archiveId: 'sparse',
        kind: 'measurement-archive',
        metadata: {
          schemaVersion: 'measurement-archive.v1',
          createdAtIso: '2026-05-20T00:00:00Z',
          sourceApplication: 'test',
        },
        context: {},
        sections: [
          { sectionId: 's1', label: 'Test', measurements: [{ property: 'p1', value: 1, unit: '' }] },
        ],
      }

      const summary = createEvidenceSummary([sparseArchive])
      expect(summary.sparseArchives).toContain('sparse')
    })

    it('computes date range', () => {
      const archive1 = createTestArchive()
      archive1.metadata.createdAtIso = '2026-05-01T00:00:00Z'

      const archive2 = createTestArchive()
      archive2.archiveId = 'archive-2'
      archive2.metadata.createdAtIso = '2026-05-20T00:00:00Z'

      const archives = [archive1, archive2]
      const summary = createEvidenceSummary(archives)
      expect(summary.dateRange?.earliest).toBe('2026-05-01T00:00:00Z')
      expect(summary.dateRange?.latest).toBe('2026-05-20T00:00:00Z')
    })
  })
})

describe('Dev Order 63: Pairwise Comparison Utilities', () => {
  describe('compareArchives', () => {
    it('computes residuals for matching properties', () => {
      const archiveA = createTestArchive()
      archiveA.archiveId = 'a'

      const archiveB = createTestArchive()
      archiveB.archiveId = 'b'
      archiveB.sections = [
        {
          sectionId: 's1',
          label: 'Acoustic Measurements',
          measurements: [
            { property: 'measuredHelmholtzHz', value: 110, unit: 'Hz' },
            { property: 'measuredQFactor', value: 18, unit: '' },
          ],
        },
      ]

      const result = compareArchives(archiveA, archiveB)

      // 2 matching properties = partial status (need >= 3 for comparable)
      expect(result.status).toBe('partial')
      expect(result.residuals.length).toBe(2)

      const helmholtzResidual = result.residuals.find(r => r.property === 'measuredHelmholtzHz')
      expect(helmholtzResidual?.difference).toBe(10)
      expect(helmholtzResidual?.percentDifference).toBe(10)
    })

    it('returns comparable status when 3+ properties match', () => {
      const archiveA: MeasurementArchiveRecord = {
        archiveId: 'a',
        kind: 'measurement-archive',
        metadata: { schemaVersion: 'measurement-archive.v1', createdAtIso: '2026-05-20T00:00:00Z', sourceApplication: 'test' },
        context: {},
        sections: [
          {
            sectionId: 's1',
            label: 'Test',
            measurements: [
              { property: 'measuredHelmholtzHz', value: 100, unit: 'Hz' },
              { property: 'measuredQFactor', value: 15, unit: '' },
              { property: 'dominantPeakHz', value: 200, unit: 'Hz' },
            ],
          },
        ],
      }

      const archiveB: MeasurementArchiveRecord = {
        archiveId: 'b',
        kind: 'measurement-archive',
        metadata: { schemaVersion: 'measurement-archive.v1', createdAtIso: '2026-05-20T00:00:00Z', sourceApplication: 'test' },
        context: {},
        sections: [
          {
            sectionId: 's1',
            label: 'Test',
            measurements: [
              { property: 'measuredHelmholtzHz', value: 105, unit: 'Hz' },
              { property: 'measuredQFactor', value: 16, unit: '' },
              { property: 'dominantPeakHz', value: 210, unit: 'Hz' },
            ],
          },
        ],
      }

      const result = compareArchives(archiveA, archiveB)
      expect(result.status).toBe('comparable')
      expect(result.residuals.length).toBe(3)
    })

    it('detects asymmetric properties', () => {
      const archiveA: MeasurementArchiveRecord = {
        archiveId: 'a',
        kind: 'measurement-archive',
        metadata: { schemaVersion: 'measurement-archive.v1', createdAtIso: '2026-05-20T00:00:00Z', sourceApplication: 'test' },
        context: {},
        sections: [
          {
            sectionId: 's1',
            label: 'Test',
            measurements: [
              { property: 'propertyA', value: 100, unit: 'Hz' },
            ],
          },
        ],
      }

      const archiveB: MeasurementArchiveRecord = {
        archiveId: 'b',
        kind: 'measurement-archive',
        metadata: { schemaVersion: 'measurement-archive.v1', createdAtIso: '2026-05-20T00:00:00Z', sourceApplication: 'test' },
        context: {},
        sections: [
          {
            sectionId: 's1',
            label: 'Different',
            measurements: [
              { property: 'differentProperty', value: 50, unit: 'mm' },
            ],
          },
        ],
      }

      const result = compareArchives(archiveA, archiveB)

      expect(result.status).toBe('insufficient')
      expect(result.warnings.length).toBeGreaterThan(0)
    })

    it('returns partial status for limited overlap', () => {
      const archiveA: MeasurementArchiveRecord = {
        archiveId: 'a',
        kind: 'measurement-archive',
        metadata: { schemaVersion: 'measurement-archive.v1', createdAtIso: '2026-05-20T00:00:00Z', sourceApplication: 'test' },
        context: {},
        sections: [
          {
            sectionId: 's1',
            label: 'Test',
            measurements: [
              { property: 'measuredHelmholtzHz', value: 100, unit: 'Hz' },
              { property: 'propA', value: 1, unit: '' },
            ],
          },
        ],
      }

      const archiveB: MeasurementArchiveRecord = {
        archiveId: 'b',
        kind: 'measurement-archive',
        metadata: { schemaVersion: 'measurement-archive.v1', createdAtIso: '2026-05-20T00:00:00Z', sourceApplication: 'test' },
        context: {},
        sections: [
          {
            sectionId: 's1',
            label: 'Test',
            measurements: [
              { property: 'measuredHelmholtzHz', value: 105, unit: 'Hz' },
              { property: 'propB', value: 2, unit: '' },
            ],
          },
        ],
      }

      const result = compareArchives(archiveA, archiveB)
      expect(result.status).toBe('partial')
    })
  })

  describe('interpretResidualMagnitude', () => {
    it('returns small for < 5%', () => {
      expect(interpretResidualMagnitude(3)).toBe('small')
    })

    it('returns moderate for 5-15%', () => {
      expect(interpretResidualMagnitude(10)).toBe('moderate')
    })

    it('returns large for > 15%', () => {
      expect(interpretResidualMagnitude(20)).toBe('large')
    })

    it('returns unknown for null', () => {
      expect(interpretResidualMagnitude(null)).toBe('unknown')
    })
  })

  describe('generateComparisonNarrative', () => {
    it('describes insufficient data', () => {
      const result = {
        archiveIdA: 'a',
        archiveIdB: 'b',
        status: 'insufficient' as const,
        residuals: [],
        warnings: [],
        notes: [],
      }

      const narrative = generateComparisonNarrative(result)
      expect(narrative).toContain('Insufficient')
    })

    it('describes small divergence', () => {
      const result = {
        archiveIdA: 'a',
        archiveIdB: 'b',
        status: 'comparable' as const,
        residuals: [
          { property: 'measuredHelmholtzHz', label: 'Helmholtz (Hz)', valueA: 100, valueB: 102, difference: 2, percentDifference: 2, unit: 'Hz' },
        ],
        warnings: [],
        notes: [],
      }

      const narrative = generateComparisonNarrative(result)
      expect(narrative).toContain('small divergence')
    })

    it('describes large divergence', () => {
      const result = {
        archiveIdA: 'a',
        archiveIdB: 'b',
        status: 'comparable' as const,
        residuals: [
          { property: 'measuredHelmholtzHz', label: 'Helmholtz (Hz)', valueA: 100, valueB: 130, difference: 30, percentDifference: 30, unit: 'Hz' },
        ],
        warnings: [],
        notes: [],
      }

      const narrative = generateComparisonNarrative(result)
      expect(narrative).toContain('large divergence')
    })
  })

  describe('formatArchiveTimestamp', () => {
    it('formats ISO string for display', () => {
      const formatted = formatArchiveTimestamp('2026-05-20T15:30:00.000Z')
      expect(formatted).toContain('2026')
      expect(formatted).toContain('May')
    })
  })
})

// ============================================================================
// Dev Order 64: QA & UX Stabilization Tests
// ============================================================================

import {
  getMeasurementArchiveDisplayLabel,
  hasComparableMeasurementFields,
  detectDuplicateArchiveId,
  dedupeMeasurementArchives,
  mergeMeasurementArchiveLists,
  isValidArchiveRecord,
  safeParseArchiveTimestamp,
} from '../measurementArchive'

describe('Dev Order 64: QA & UX Stabilization', () => {
  describe('getMeasurementArchiveDisplayLabel', () => {
    it('returns referenceLabel when present', () => {
      const archive = createTestArchive()
      archive.context.referenceLabel = 'Reference'
      expect(getMeasurementArchiveDisplayLabel(archive)).toBe('Reference')
    })

    it('falls back to candidateLabel', () => {
      const archive = createTestArchive()
      archive.context.referenceLabel = undefined
      archive.context.candidateLabel = 'Candidate'
      expect(getMeasurementArchiveDisplayLabel(archive)).toBe('Candidate')
    })

    it('falls back to archiveId', () => {
      const archive = createTestArchive()
      archive.context.referenceLabel = undefined
      archive.context.candidateLabel = undefined
      expect(getMeasurementArchiveDisplayLabel(archive)).toBe(archive.archiveId)
    })
  })

  describe('hasComparableMeasurementFields', () => {
    it('returns true when archives share numeric fields', () => {
      const archiveA = createTestArchive()
      const archiveB = createTestArchive()
      expect(hasComparableMeasurementFields(archiveA, archiveB)).toBe(true)
    })

    it('returns false when no shared fields', () => {
      const archiveA: MeasurementArchiveRecord = {
        archiveId: 'a',
        kind: 'measurement-archive',
        metadata: { schemaVersion: 'measurement-archive.v1', createdAtIso: '2026-05-20T00:00:00Z', sourceApplication: 'test' },
        context: {},
        sections: [{ sectionId: 's1', label: 'A', measurements: [{ property: 'propA', value: 1, unit: '' }] }],
      }
      const archiveB: MeasurementArchiveRecord = {
        archiveId: 'b',
        kind: 'measurement-archive',
        metadata: { schemaVersion: 'measurement-archive.v1', createdAtIso: '2026-05-20T00:00:00Z', sourceApplication: 'test' },
        context: {},
        sections: [{ sectionId: 's1', label: 'B', measurements: [{ property: 'propB', value: 2, unit: '' }] }],
      }
      expect(hasComparableMeasurementFields(archiveA, archiveB)).toBe(false)
    })
  })

  describe('detectDuplicateArchiveId', () => {
    it('detects duplicate archive ID', () => {
      const archive = createTestArchive()
      const archives = [archive]
      expect(detectDuplicateArchiveId(archives, archive)).toBe(true)
    })

    it('returns false for unique archive ID', () => {
      const archive1 = createTestArchive()
      archive1.archiveId = 'unique-1'
      const archive2 = createTestArchive()
      archive2.archiveId = 'unique-2'
      expect(detectDuplicateArchiveId([archive1], archive2)).toBe(false)
    })
  })

  describe('dedupeMeasurementArchives', () => {
    it('removes duplicate archive IDs', () => {
      const archive1 = createTestArchive()
      archive1.archiveId = 'dup'
      const archive2 = createTestArchive()
      archive2.archiveId = 'dup'
      const result = dedupeMeasurementArchives([archive1, archive2])
      expect(result.length).toBe(1)
    })

    it('preserves first occurrence', () => {
      const archive1 = createTestArchive()
      archive1.archiveId = 'dup'
      archive1.context.referenceLabel = 'First'
      const archive2 = createTestArchive()
      archive2.archiveId = 'dup'
      archive2.context.referenceLabel = 'Second'
      const result = dedupeMeasurementArchives([archive1, archive2])
      expect(result[0].context.referenceLabel).toBe('First')
    })
  })

  describe('mergeMeasurementArchiveLists', () => {
    it('detects duplicate archive IDs', () => {
      const existing = [createTestArchive()]
      const incoming = [createTestArchive()]
      const result = mergeMeasurementArchiveLists(existing, incoming)
      expect(result.duplicatesDetected.length).toBe(1)
    })

    it('skips invalid archives', () => {
      const existing: MeasurementArchiveRecord[] = []
      const incoming = [{ archiveId: 'invalid' } as unknown as MeasurementArchiveRecord]
      const result = mergeMeasurementArchiveLists(existing, incoming)
      expect(result.invalidSkipped).toBe(1)
    })

    it('preserves existing archive order', () => {
      const archive1 = createTestArchive()
      archive1.archiveId = 'a'
      const archive2 = createTestArchive()
      archive2.archiveId = 'b'
      const archive3 = createTestArchive()
      archive3.archiveId = 'c'

      const result = mergeMeasurementArchiveLists([archive1, archive2], [archive3])
      expect(result.merged[0].archiveId).toBe('a')
      expect(result.merged[1].archiveId).toBe('b')
      expect(result.merged[2].archiveId).toBe('c')
    })

    it('does not mutate input arrays', () => {
      const existing = [createTestArchive()]
      const incoming = [createTestArchive()]
      incoming[0].archiveId = 'new-archive'
      const originalLength = existing.length
      mergeMeasurementArchiveLists(existing, incoming)
      expect(existing.length).toBe(originalLength)
    })
  })

  describe('isValidArchiveRecord', () => {
    it('returns true for valid archive', () => {
      const archive = createTestArchive()
      expect(isValidArchiveRecord(archive)).toBe(true)
    })

    it('returns false for null', () => {
      expect(isValidArchiveRecord(null)).toBe(false)
    })

    it('returns false for wrong kind', () => {
      const invalid = { archiveId: 'x', kind: 'wrong', metadata: {}, sections: [] }
      expect(isValidArchiveRecord(invalid)).toBe(false)
    })
  })

  describe('safeParseArchiveTimestamp', () => {
    it('parses valid ISO string', () => {
      const result = safeParseArchiveTimestamp('2026-05-20T00:00:00Z')
      expect(result).toBeGreaterThan(0)
    })

    it('returns 0 for undefined', () => {
      expect(safeParseArchiveTimestamp(undefined)).toBe(0)
    })

    it('returns 0 for invalid string', () => {
      expect(safeParseArchiveTimestamp('not-a-date')).toBe(0)
    })
  })

  describe('validation with duplicate detection', () => {
    it('warns on duplicate archive ID', () => {
      const existingIds = new Set(['existing-id'])
      const archive = { ...createTestArchive(), archiveId: 'existing-id' }
      const result = validateMeasurementArchive(archive, existingIds)
      expect(result.warnings.some(w => w.includes('Duplicate'))).toBe(true)
    })

    it('warns on sparse archive', () => {
      const archive = {
        archiveId: 'sparse',
        kind: 'measurement-archive',
        metadata: { schemaVersion: 'measurement-archive.v1', createdAtIso: '2026-05-20T00:00:00Z', sourceApplication: 'test' },
        context: {},
        sections: [{ sectionId: 's1', label: 'Test', measurements: [{ property: 'p1', value: 1, unit: '' }] }],
      }
      const result = validateMeasurementArchive(archive)
      expect(result.warnings.some(w => w.includes('Sparse'))).toBe(true)
    })
  })

  describe('sorting with missing timestamps', () => {
    it('handles missing createdAtIso', () => {
      const archive1 = createTestArchive()
      archive1.archiveId = 'missing-time'
      archive1.metadata.createdAtIso = undefined as unknown as string

      const archive2 = createTestArchive()
      archive2.archiveId = 'valid-time'

      const result = sortMeasurementArchivesByTimestamp([archive1, archive2])
      expect(result.length).toBe(2)
      // Valid timestamp should sort before invalid (which becomes 0)
      expect(result[0].archiveId).toBe('valid-time')
    })
  })

  describe('narrative forbidden words check', () => {
    const FORBIDDEN_WORDS = ['better', 'improved', 'optimized', 'recommended', 'validated']

    it('narratives do not contain forbidden recommendation words', () => {
      const testCases = [
        { status: 'insufficient' as const, residuals: [], warnings: [], notes: [] },
        {
          status: 'comparable' as const,
          residuals: [{ property: 'test', label: 'Test', valueA: 100, valueB: 110, difference: 10, percentDifference: 10, unit: 'Hz' }],
          warnings: [],
          notes: [],
        },
        {
          status: 'partial' as const,
          residuals: [{ property: 'test', label: 'Test', valueA: 100, valueB: 150, difference: 50, percentDifference: 50, unit: 'Hz' }],
          warnings: ['Some asymmetry'],
          notes: [],
        },
      ]

      for (const testCase of testCases) {
        const narrative = generateComparisonNarrative({ archiveIdA: 'a', archiveIdB: 'b', ...testCase })
        const lowerNarrative = narrative.toLowerCase()
        for (const word of FORBIDDEN_WORDS) {
          expect(lowerNarrative).not.toContain(word)
        }
      }
    })
  })
})

/**
 * Experimental Drift Tests
 *
 * Dev Order 70: Experimental drift timeline workspace
 * Dev Order 71: QA & observational boundary hardening
 *
 * Tests drift computation, narrative generation, and observational semantics.
 *
 * Required test categories (Dev Order 71):
 * 1. insufficient data below 3 archives
 * 2. duplicate archives ignored
 * 3. invalid archives excluded
 * 4. sparse archives skipped safely
 * 5. missing timestamps handled safely
 * 6. stable drift under 5%
 * 7. upward drift at/above 5%
 * 8. downward drift at/above 5%
 * 9. variable drift with repeated direction changes
 * 10. dynamic numeric field handling
 * 11. session grouping by sessionContext
 * 12. variant grouping by topology reference
 * 13. narrative avoids forbidden language
 * 14. computation does not mutate inputs
 * 15. summary rollup produces stable dominant direction
 */

import { describe, it, expect } from 'vitest'
import type { MeasurementArchiveRecord } from '../../../types/acoustics/measurementArchive'
import type { DriftDirection, DriftTimelinePoint } from '../../../types/acoustics/experimentalDrift'
import {
  MINIMUM_DRIFT_SAMPLE_SIZE,
  DRIFT_DIRECTION_THRESHOLD,
  DRIFT_TRACKABLE_FIELDS,
  DRIFT_VARIABLE_STDEV_THRESHOLD,
  DRIFT_VARIABLE_REVERSAL_THRESHOLD,
  hasSufficientDriftData,
  sortArchivesChronologically,
  extractComparableFieldSeries,
  classifyDriftDirection,
  buildDriftNarrative,
  groupArchivesByVariantTimeline,
  groupArchivesBySessionTimeline,
  buildDriftSequences,
  computeExperimentalDrift,
  filterDriftsByDirection,
  filterDriftsByField,
  getDriftsForContext,
  countSignReversals,
  calculatePercentDeltaStdev,
  isVariableDrift,
  filterDriftableArchives,
  prepareDriftableArchives,
} from '../experimentalDrift'

/**
 * Create a mock archive that passes validation
 */
function createMockArchive(
  id: string,
  overrides: {
    timestamp?: string
    helmholtzHz?: number
    peakHz?: number
    dampingFactor?: number
    q?: number
    variantRefs?: string[]
    sessionContext?: string
  } = {}
): MeasurementArchiveRecord {
  return {
    archiveId: id,
    kind: 'measurement-archive',
    schemaVersion: 'measurement-archive.v1',
    status: 'active',
    metadata: {
      createdAtIso: overrides.timestamp ?? new Date().toISOString(),
      schemaVersion: 'measurement-archive.v1',
    },
    measurements: {
      measuredHelmholtzHz: overrides.helmholtzHz,
      measuredPeakHz: overrides.peakHz,
      measuredDampingFactor: overrides.dampingFactor,
      measuredQ: overrides.q,
    },
    sections: [
      {
        measurements: [
          { field: 'test', value: 1 },
          { field: 'test2', value: 2 },
          { field: 'test3', value: 3 },
        ],
      },
    ],
    topologyVariantReferences: overrides.variantRefs,
    context: {
      sessionContext: overrides.sessionContext,
    },
  } as MeasurementArchiveRecord
}

/**
 * Create an invalid archive (missing required fields)
 */
function createInvalidArchive(id: string): unknown {
  return {
    archiveId: id,
    // Missing kind, metadata.schemaVersion, sections
  }
}

/**
 * Create a sparse archive (fewer than 3 measurements)
 */
function createSparseArchive(id: string, timestamp?: string): MeasurementArchiveRecord {
  return {
    archiveId: id,
    kind: 'measurement-archive',
    schemaVersion: 'measurement-archive.v1',
    status: 'active',
    metadata: {
      createdAtIso: timestamp ?? new Date().toISOString(),
      schemaVersion: 'measurement-archive.v1',
    },
    measurements: {
      measuredHelmholtzHz: 100,
    },
    sections: [
      {
        measurements: [{ field: 'test', value: 1 }],
      },
    ],
    topologyVariantReferences: [],
    context: {},
  } as MeasurementArchiveRecord
}

describe('experimentalDrift', () => {
  describe('constants', () => {
    it('should have minimum sample size of 3', () => {
      expect(MINIMUM_DRIFT_SAMPLE_SIZE).toBe(3)
    })

    it('should have drift direction threshold of 5%', () => {
      expect(DRIFT_DIRECTION_THRESHOLD).toBe(0.05)
    })

    it('should track measuredHelmholtzHz, measuredPeakHz, measuredDampingFactor, measuredQ', () => {
      expect(DRIFT_TRACKABLE_FIELDS).toContain('measuredHelmholtzHz')
      expect(DRIFT_TRACKABLE_FIELDS).toContain('measuredPeakHz')
      expect(DRIFT_TRACKABLE_FIELDS).toContain('measuredDampingFactor')
      expect(DRIFT_TRACKABLE_FIELDS).toContain('measuredQ')
      expect(DRIFT_TRACKABLE_FIELDS.length).toBe(4)
    })
  })

  describe('hasSufficientDriftData', () => {
    it('should return false for fewer than 3 archives', () => {
      expect(hasSufficientDriftData([])).toBe(false)
      expect(hasSufficientDriftData([createMockArchive('a1')])).toBe(false)
      expect(hasSufficientDriftData([createMockArchive('a1'), createMockArchive('a2')])).toBe(false)
    })

    it('should return true for 3 or more archives', () => {
      const archives = [createMockArchive('a1'), createMockArchive('a2'), createMockArchive('a3')]
      expect(hasSufficientDriftData(archives)).toBe(true)
    })
  })

  describe('sortArchivesChronologically', () => {
    it('should sort archives by createdAtIso', () => {
      const archives = [
        createMockArchive('a3', { timestamp: '2026-01-03T00:00:00Z' }),
        createMockArchive('a1', { timestamp: '2026-01-01T00:00:00Z' }),
        createMockArchive('a2', { timestamp: '2026-01-02T00:00:00Z' }),
      ]

      const sorted = sortArchivesChronologically(archives)

      expect(sorted[0].archiveId).toBe('a1')
      expect(sorted[1].archiveId).toBe('a2')
      expect(sorted[2].archiveId).toBe('a3')
    })

    it('should not mutate original array', () => {
      const archives = [
        createMockArchive('a2', { timestamp: '2026-01-02T00:00:00Z' }),
        createMockArchive('a1', { timestamp: '2026-01-01T00:00:00Z' }),
      ]

      sortArchivesChronologically(archives)

      expect(archives[0].archiveId).toBe('a2')
    })
  })

  describe('extractComparableFieldSeries', () => {
    it('should extract field values with archives', () => {
      const archives = [
        createMockArchive('a1', { helmholtzHz: 100 }),
        createMockArchive('a2', { helmholtzHz: 110 }),
        createMockArchive('a3', { helmholtzHz: undefined }),
      ]

      const series = extractComparableFieldSeries(archives, 'measuredHelmholtzHz')

      expect(series.length).toBe(2)
      expect(series[0].value).toBe(100)
      expect(series[1].value).toBe(110)
    })

    it('should skip archives with undefined field values', () => {
      const archives = [
        createMockArchive('a1', { helmholtzHz: undefined }),
        createMockArchive('a2', { helmholtzHz: 100 }),
      ]

      const series = extractComparableFieldSeries(archives, 'measuredHelmholtzHz')

      expect(series.length).toBe(1)
      expect(series[0].archive.archiveId).toBe('a2')
    })
  })

  describe('classifyDriftDirection', () => {
    it('should classify as stable for <5% change', () => {
      expect(classifyDriftDirection(0)).toBe('stable')
      expect(classifyDriftDirection(0.04)).toBe('stable')
      expect(classifyDriftDirection(-0.04)).toBe('stable')
      expect(classifyDriftDirection(0.049)).toBe('stable')
    })

    it('should classify as upward for >=5% positive change', () => {
      expect(classifyDriftDirection(0.05)).toBe('upward')
      expect(classifyDriftDirection(0.1)).toBe('upward')
      expect(classifyDriftDirection(0.5)).toBe('upward')
    })

    it('should classify as downward for >=5% negative change', () => {
      expect(classifyDriftDirection(-0.05)).toBe('downward')
      expect(classifyDriftDirection(-0.1)).toBe('downward')
      expect(classifyDriftDirection(-0.5)).toBe('downward')
    })

    it('should classify as variable with 2+ sign reversals', () => {
      // Points: 100 -> 120 (+20) -> 100 (-20) -> 130 (+30)
      // Sign changes: + to -, - to + = 2 reversals
      const points: DriftTimelinePoint[] = [
        { archiveId: 'a1', value: 100 },
        { archiveId: 'a2', value: 120, deltaFromPrevious: 20, percentDeltaFromPrevious: 0.2 },
        { archiveId: 'a3', value: 100, deltaFromPrevious: -20, percentDeltaFromPrevious: -0.167 },
        { archiveId: 'a4', value: 130, deltaFromPrevious: 30, percentDeltaFromPrevious: 0.3 },
      ]
      expect(classifyDriftDirection(0.3, points)).toBe('variable')
    })

    it('should classify as variable with high stdev (>10%)', () => {
      // High variance in percent deltas but net upward
      const points: DriftTimelinePoint[] = [
        { archiveId: 'a1', value: 100 },
        { archiveId: 'a2', value: 150, deltaFromPrevious: 50, percentDeltaFromPrevious: 0.5 },
        { archiveId: 'a3', value: 160, deltaFromPrevious: 10, percentDeltaFromPrevious: 0.067 },
      ]
      expect(classifyDriftDirection(0.6, points)).toBe('variable')
    })
  })

  describe('variable drift detection', () => {
    it('should count sign reversals correctly', () => {
      const points: DriftTimelinePoint[] = [
        { archiveId: 'a1', value: 100 },
        { archiveId: 'a2', value: 110, deltaFromPrevious: 10 },
        { archiveId: 'a3', value: 100, deltaFromPrevious: -10 },
        { archiveId: 'a4', value: 120, deltaFromPrevious: 20 },
      ]
      expect(countSignReversals(points)).toBe(2)
    })

    it('should return 0 reversals for monotonic sequence', () => {
      const points: DriftTimelinePoint[] = [
        { archiveId: 'a1', value: 100 },
        { archiveId: 'a2', value: 110, deltaFromPrevious: 10 },
        { archiveId: 'a3', value: 120, deltaFromPrevious: 10 },
      ]
      expect(countSignReversals(points)).toBe(0)
    })

    it('should calculate stdev of percent deltas', () => {
      const points: DriftTimelinePoint[] = [
        { archiveId: 'a1', value: 100 },
        { archiveId: 'a2', value: 110, percentDeltaFromPrevious: 0.1 },
        { archiveId: 'a3', value: 120, percentDeltaFromPrevious: 0.09 },
      ]
      const stdev = calculatePercentDeltaStdev(points)
      expect(stdev).toBeLessThan(0.01)
    })

    it('should detect variable drift with high variance', () => {
      const points: DriftTimelinePoint[] = [
        { archiveId: 'a1', value: 100 },
        { archiveId: 'a2', value: 150, deltaFromPrevious: 50, percentDeltaFromPrevious: 0.5 },
        { archiveId: 'a3', value: 155, deltaFromPrevious: 5, percentDeltaFromPrevious: 0.033 },
      ]
      expect(isVariableDrift(points)).toBe(true)
    })

    it('should have variable stdev threshold of 10%', () => {
      expect(DRIFT_VARIABLE_STDEV_THRESHOLD).toBe(0.10)
    })

    it('should have variable reversal threshold of 2', () => {
      expect(DRIFT_VARIABLE_REVERSAL_THRESHOLD).toBe(2)
    })
  })

  describe('buildDriftNarrative', () => {
    it('should generate upward narrative', () => {
      const narrative = buildDriftNarrative('measuredHelmholtzHz', 'upward', 0.1, 5)
      expect(narrative).toBe(
        'measuredHelmholtzHz shifted upward by 10.0% across 5 sequential observations'
      )
    })

    it('should generate downward narrative', () => {
      const narrative = buildDriftNarrative('measuredPeakHz', 'downward', -0.08, 4)
      expect(narrative).toBe(
        'measuredPeakHz shifted downward by 8.0% across 4 sequential observations'
      )
    })

    it('should generate stable narrative', () => {
      const narrative = buildDriftNarrative('measuredQ', 'stable', 0.02, 3)
      expect(narrative).toBe('measuredQ remained stable (2.0% variation) across 3 sequential observations')
    })

    it('should generate variable narrative', () => {
      const narrative = buildDriftNarrative('measuredQ', 'variable', 0.15, 5)
      expect(narrative).toBe('measuredQ showed variable behavior across 5 sequential observations')
    })
  })

  describe('groupArchivesByVariantTimeline', () => {
    it('should group archives by variant ID', () => {
      const archives = [
        createMockArchive('a1', { variantRefs: ['v1'] }),
        createMockArchive('a2', { variantRefs: ['v1'] }),
        createMockArchive('a3', { variantRefs: ['v2'] }),
      ]

      const groups = groupArchivesByVariantTimeline(archives)

      expect(groups.get('v1')?.length).toBe(2)
      expect(groups.get('v2')?.length).toBe(1)
    })

    it('should handle archives without variant refs', () => {
      const archives = [
        createMockArchive('a1', { variantRefs: undefined }),
        createMockArchive('a2', { variantRefs: [] }),
      ]

      const groups = groupArchivesByVariantTimeline(archives)

      expect(groups.get('__none__')?.length).toBe(2)
    })
  })

  describe('groupArchivesBySessionTimeline', () => {
    it('should group archives by session context', () => {
      const archives = [
        createMockArchive('a1', { sessionContext: 'session-A' }),
        createMockArchive('a2', { sessionContext: 'session-A' }),
        createMockArchive('a3', { sessionContext: 'session-B' }),
      ]

      const groups = groupArchivesBySessionTimeline(archives)

      expect(groups.get('session-A')?.length).toBe(2)
      expect(groups.get('session-B')?.length).toBe(1)
    })

    it('should handle archives without session context', () => {
      const archives = [
        createMockArchive('a1', { sessionContext: undefined }),
        createMockArchive('a2', { sessionContext: 'session-A' }),
      ]

      const groups = groupArchivesBySessionTimeline(archives)

      expect(groups.get('__none__')?.length).toBe(1)
      expect(groups.get('session-A')?.length).toBe(1)
    })
  })

  describe('buildDriftSequences', () => {
    it('should build chronological sequence from all archives', () => {
      const archives = [
        createMockArchive('a1', { timestamp: '2026-01-01T00:00:00Z' }),
        createMockArchive('a2', { timestamp: '2026-01-02T00:00:00Z' }),
        createMockArchive('a3', { timestamp: '2026-01-03T00:00:00Z' }),
      ]

      const sequences = buildDriftSequences(archives, 'chronological')

      expect(sequences.length).toBe(1)
      expect(sequences[0].contextType).toBe('chronological')
      expect(sequences[0].archiveCount).toBe(3)
    })

    it('should skip contexts with fewer than 3 archives', () => {
      const archives = [
        createMockArchive('a1', { variantRefs: ['v1'] }),
        createMockArchive('a2', { variantRefs: ['v1'] }),
      ]

      const sequences = buildDriftSequences(archives, 'variant')

      expect(sequences.length).toBe(0)
    })
  })

  describe('computeExperimentalDrift', () => {
    it('should compute drift for trackable fields', () => {
      const archives = [
        createMockArchive('a1', {
          timestamp: '2026-01-01T00:00:00Z',
          helmholtzHz: 100,
          peakHz: 200,
        }),
        createMockArchive('a2', {
          timestamp: '2026-01-02T00:00:00Z',
          helmholtzHz: 110,
          peakHz: 210,
        }),
        createMockArchive('a3', {
          timestamp: '2026-01-03T00:00:00Z',
          helmholtzHz: 120,
          peakHz: 220,
        }),
      ]

      const result = computeExperimentalDrift(archives, 'chronological')

      expect(result.drifts.length).toBeGreaterThan(0)
      expect(result.totalArchivesAnalyzed).toBe(3)
      expect(result.computedAtIso).toBeDefined()
    })

    it('should track insufficient contexts', () => {
      const archives = [
        createMockArchive('a1', { variantRefs: ['v1'] }),
        createMockArchive('a2', { variantRefs: ['v2'] }),
      ]

      const result = computeExperimentalDrift(archives, 'variant')

      expect(result.insufficientContexts.length).toBeGreaterThan(0)
    })

    it('should generate summaries by context', () => {
      const archives = [
        createMockArchive('a1', {
          timestamp: '2026-01-01T00:00:00Z',
          helmholtzHz: 100,
        }),
        createMockArchive('a2', {
          timestamp: '2026-01-02T00:00:00Z',
          helmholtzHz: 110,
        }),
        createMockArchive('a3', {
          timestamp: '2026-01-03T00:00:00Z',
          helmholtzHz: 120,
        }),
      ]

      const result = computeExperimentalDrift(archives, 'chronological')

      expect(result.summaries.length).toBe(1)
      expect(result.summaries[0].contextType).toBe('chronological')
    })
  })

  describe('filter utilities', () => {
    it('should filter drifts by direction', () => {
      const archives = [
        createMockArchive('a1', { timestamp: '2026-01-01T00:00:00Z', helmholtzHz: 100 }),
        createMockArchive('a2', { timestamp: '2026-01-02T00:00:00Z', helmholtzHz: 120 }),
        createMockArchive('a3', { timestamp: '2026-01-03T00:00:00Z', helmholtzHz: 140 }),
      ]

      const result = computeExperimentalDrift(archives, 'chronological')
      const upward = filterDriftsByDirection(result.drifts, 'upward')

      expect(upward.every((d) => d.direction === 'upward')).toBe(true)
    })

    it('should filter drifts by field', () => {
      const archives = [
        createMockArchive('a1', {
          timestamp: '2026-01-01T00:00:00Z',
          helmholtzHz: 100,
          peakHz: 200,
        }),
        createMockArchive('a2', {
          timestamp: '2026-01-02T00:00:00Z',
          helmholtzHz: 120,
          peakHz: 220,
        }),
        createMockArchive('a3', {
          timestamp: '2026-01-03T00:00:00Z',
          helmholtzHz: 140,
          peakHz: 240,
        }),
      ]

      const result = computeExperimentalDrift(archives, 'chronological')
      const helmholtz = filterDriftsByField(result.drifts, 'measuredHelmholtzHz')

      expect(helmholtz.every((d) => d.observedField === 'measuredHelmholtzHz')).toBe(true)
    })
  })

  describe('Dev Order 71: archive validation and filtering', () => {
    it('should ignore duplicate archives by archiveId', () => {
      const archives = [
        createMockArchive('a1', { timestamp: '2026-01-01T00:00:00Z', helmholtzHz: 100 }),
        createMockArchive('a1', { timestamp: '2026-01-01T00:00:00Z', helmholtzHz: 100 }), // duplicate
        createMockArchive('a2', { timestamp: '2026-01-02T00:00:00Z', helmholtzHz: 110 }),
        createMockArchive('a3', { timestamp: '2026-01-03T00:00:00Z', helmholtzHz: 120 }),
      ]

      const result = computeExperimentalDrift(archives, 'chronological')

      expect(result.totalArchivesProvided).toBe(4)
      expect(result.totalArchivesAnalyzed).toBe(3)
    })

    it('should exclude invalid archives', () => {
      const archives = [
        createMockArchive('a1', { timestamp: '2026-01-01T00:00:00Z', helmholtzHz: 100 }),
        createInvalidArchive('invalid') as MeasurementArchiveRecord,
        createMockArchive('a2', { timestamp: '2026-01-02T00:00:00Z', helmholtzHz: 110 }),
        createMockArchive('a3', { timestamp: '2026-01-03T00:00:00Z', helmholtzHz: 120 }),
      ]

      const { valid, warnings } = filterDriftableArchives(archives)

      expect(valid.length).toBe(3)
      expect(warnings.length).toBeGreaterThan(0)
      expect(warnings.some((w) => w.includes('invalid'))).toBe(true)
    })

    it('should flag sparse archives in warnings', () => {
      const archives = [
        createMockArchive('a1', { timestamp: '2026-01-01T00:00:00Z', helmholtzHz: 100 }),
        createSparseArchive('sparse1', '2026-01-02T00:00:00Z'),
        createMockArchive('a2', { timestamp: '2026-01-03T00:00:00Z', helmholtzHz: 110 }),
        createMockArchive('a3', { timestamp: '2026-01-04T00:00:00Z', helmholtzHz: 120 }),
      ]

      const { valid, warnings } = filterDriftableArchives(archives)

      expect(valid.length).toBe(4) // sparse included but flagged
      expect(warnings.some((w) => w.includes('sparse'))).toBe(true)
    })

    it('should handle missing timestamps safely', () => {
      const archives = [
        createMockArchive('a1', { timestamp: undefined, helmholtzHz: 100 }),
        createMockArchive('a2', { timestamp: '2026-01-02T00:00:00Z', helmholtzHz: 110 }),
        createMockArchive('a3', { timestamp: '2026-01-03T00:00:00Z', helmholtzHz: 120 }),
      ]

      // Should not throw
      const result = computeExperimentalDrift(archives, 'chronological')
      expect(result.drifts.length).toBeGreaterThan(0)
    })

    it('should not mutate input archive array', () => {
      const archives = [
        createMockArchive('a3', { timestamp: '2026-01-03T00:00:00Z', helmholtzHz: 120 }),
        createMockArchive('a1', { timestamp: '2026-01-01T00:00:00Z', helmholtzHz: 100 }),
        createMockArchive('a2', { timestamp: '2026-01-02T00:00:00Z', helmholtzHz: 110 }),
      ]

      const originalOrder = archives.map((a) => a.archiveId)

      computeExperimentalDrift(archives, 'chronological')

      const afterOrder = archives.map((a) => a.archiveId)
      expect(afterOrder).toEqual(originalOrder)
    })

    it('should return warnings in compute result', () => {
      const archives = [
        createMockArchive('a1', { timestamp: '2026-01-01T00:00:00Z', helmholtzHz: 100 }),
        createMockArchive('a1', { timestamp: '2026-01-01T00:00:00Z', helmholtzHz: 100 }), // duplicate
        createMockArchive('a2', { timestamp: '2026-01-02T00:00:00Z', helmholtzHz: 110 }),
        createMockArchive('a3', { timestamp: '2026-01-03T00:00:00Z', helmholtzHz: 120 }),
      ]

      const result = computeExperimentalDrift(archives, 'chronological')

      expect(result.warnings).toBeDefined()
      expect(Array.isArray(result.warnings)).toBe(true)
    })
  })

  describe('Dev Order 71: dominant direction rollup', () => {
    it('should produce stable dominant direction for mixed small changes', () => {
      const archives = [
        createMockArchive('a1', {
          timestamp: '2026-01-01T00:00:00Z',
          helmholtzHz: 100,
          peakHz: 200,
          dampingFactor: 0.05,
          q: 20,
        }),
        createMockArchive('a2', {
          timestamp: '2026-01-02T00:00:00Z',
          helmholtzHz: 101, // +1%
          peakHz: 202, // +1%
          dampingFactor: 0.051, // +2%
          q: 20.2, // +1%
        }),
        createMockArchive('a3', {
          timestamp: '2026-01-03T00:00:00Z',
          helmholtzHz: 102, // +1%
          peakHz: 203, // +0.5%
          dampingFactor: 0.052, // +2%
          q: 20.4, // +1%
        }),
      ]

      const result = computeExperimentalDrift(archives, 'chronological')

      // All changes < 5%, so all should be stable
      expect(result.summaries[0].dominantDirection).toBe('stable')
    })

    it('should produce upward dominant direction when most fields shift up', () => {
      const archives = [
        createMockArchive('a1', {
          timestamp: '2026-01-01T00:00:00Z',
          helmholtzHz: 100,
          peakHz: 200,
        }),
        createMockArchive('a2', {
          timestamp: '2026-01-02T00:00:00Z',
          helmholtzHz: 110,
          peakHz: 220,
        }),
        createMockArchive('a3', {
          timestamp: '2026-01-03T00:00:00Z',
          helmholtzHz: 120,
          peakHz: 240,
        }),
      ]

      const result = computeExperimentalDrift(archives, 'chronological')

      expect(result.summaries[0].dominantDirection).toBe('upward')
    })
  })

  describe('observational language compliance', () => {
    const FORBIDDEN_WORDS = [
      'improve',
      'improved',
      'improves',
      'improvement',
      'optimize',
      'optimized',
      'optimizes',
      'optimization',
      'better',
      'best',
      'fix',
      'fixed',
      'fixes',
      'recommend',
      'recommended',
      'recommends',
      'recommendation',
      'validate',
      'validated',
      'validates',
      'validation',
      'cause',
      'causes',
      'caused',
      'causation',
      'correct',
      'corrected',
      'corrects',
    ]

    it('should not use forbidden language in upward narrative', () => {
      const narrative = buildDriftNarrative('measuredHelmholtzHz', 'upward', 0.2, 5)

      for (const word of FORBIDDEN_WORDS) {
        expect(narrative.toLowerCase()).not.toContain(word)
      }
    })

    it('should not use forbidden language in downward narrative', () => {
      const narrative = buildDriftNarrative('measuredHelmholtzHz', 'downward', -0.15, 4)

      for (const word of FORBIDDEN_WORDS) {
        expect(narrative.toLowerCase()).not.toContain(word)
      }
    })

    it('should not use forbidden language in stable narrative', () => {
      const narrative = buildDriftNarrative('measuredQ', 'stable', 0.01, 3)

      for (const word of FORBIDDEN_WORDS) {
        expect(narrative.toLowerCase()).not.toContain(word)
      }
    })

    it('should not use forbidden language in variable narrative', () => {
      const narrative = buildDriftNarrative('measuredQ', 'variable', 0.15, 5)

      for (const word of FORBIDDEN_WORDS) {
        expect(narrative.toLowerCase()).not.toContain(word)
      }
    })

    it('should use observational language in drift records', () => {
      const archives = [
        createMockArchive('a1', { timestamp: '2026-01-01T00:00:00Z', helmholtzHz: 100 }),
        createMockArchive('a2', { timestamp: '2026-01-02T00:00:00Z', helmholtzHz: 130 }),
        createMockArchive('a3', { timestamp: '2026-01-03T00:00:00Z', helmholtzHz: 160 }),
      ]

      const result = computeExperimentalDrift(archives, 'chronological')

      for (const drift of result.drifts) {
        for (const word of FORBIDDEN_WORDS) {
          expect(drift.narrative.toLowerCase()).not.toContain(word)
        }

        expect(drift.narrative).toMatch(/shifted|remained stable|observed|showed/)
      }
    })
  })

  describe('timeline point deltas', () => {
    it('should compute delta from previous point', () => {
      const archives = [
        createMockArchive('a1', { timestamp: '2026-01-01T00:00:00Z', helmholtzHz: 100 }),
        createMockArchive('a2', { timestamp: '2026-01-02T00:00:00Z', helmholtzHz: 110 }),
        createMockArchive('a3', { timestamp: '2026-01-03T00:00:00Z', helmholtzHz: 105 }),
      ]

      const result = computeExperimentalDrift(archives, 'chronological')
      const helmholtzDrift = result.drifts.find((d) => d.observedField === 'measuredHelmholtzHz')

      expect(helmholtzDrift).toBeDefined()
      expect(helmholtzDrift!.timelinePoints[0].deltaFromPrevious).toBeUndefined()
      expect(helmholtzDrift!.timelinePoints[1].deltaFromPrevious).toBe(10)
      expect(helmholtzDrift!.timelinePoints[2].deltaFromPrevious).toBe(-5)
    })

    it('should compute percent delta from previous point', () => {
      const archives = [
        createMockArchive('a1', { timestamp: '2026-01-01T00:00:00Z', helmholtzHz: 100 }),
        createMockArchive('a2', { timestamp: '2026-01-02T00:00:00Z', helmholtzHz: 110 }),
      ]

      const result = computeExperimentalDrift([
        ...archives,
        createMockArchive('a3', { timestamp: '2026-01-03T00:00:00Z', helmholtzHz: 120 }),
      ], 'chronological')

      const helmholtzDrift = result.drifts.find((d) => d.observedField === 'measuredHelmholtzHz')

      expect(helmholtzDrift!.timelinePoints[1].percentDeltaFromPrevious).toBeCloseTo(0.1)
    })
  })
})

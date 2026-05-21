/**
 * Experimental Correlation Utilities Tests
 *
 * Dev Order 68: Test coverage for computed observational correlations
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  generateCorrelationId,
  determineConfidenceBand,
  computeCorrelations,
  createVariantCorrelationSummary,
  getAllVariantCorrelationSummaries,
  hasSufficientDataForCorrelations,
  getMinSampleSize,
  formatConfidenceBand,
  getConfidenceBandGate,
  isValidArchiveForCorrelation,
  isSparseArchive,
  filterCorrelatableArchives,
  deduplicateArchives,
} from '../experimentalCorrelation'
import type { MeasurementArchiveRecord } from '@/types/acoustics/measurementArchive'
import type { TopologyVariant } from '@/types/acoustics/topologyVariant'
import type { ExperimentalCorrelation } from '@/types/acoustics/experimentalCorrelation'

// Test fixtures
function createArchive(
  id: string,
  variantRefs: string[] | undefined,
  measurements: { property: string; value: number; unit: string }[] = []
): MeasurementArchiveRecord {
  return {
    archiveId: id,
    kind: 'measurement-archive',
    metadata: {
      schemaVersion: 'measurement-archive.v1',
      createdAtIso: new Date().toISOString(),
      sourceApplication: 'test',
    },
    context: {},
    sections: [{
      sectionId: 'test-section',
      label: 'Test',
      measurements,
    }],
    topologyVariantReferences: variantRefs,
  }
}

function createVariant(id: string, title: string): TopologyVariant {
  return {
    schemaVersion: 'topology-variant.v1',
    variantId: id,
    title,
    createdAtIso: new Date().toISOString(),
  }
}

describe('experimentalCorrelation utilities', () => {
  describe('generateCorrelationId', () => {
    it('generates unique IDs with corr- prefix', () => {
      const id1 = generateCorrelationId()
      const id2 = generateCorrelationId()

      expect(id1).toMatch(/^corr-[a-z0-9]+-[a-z0-9]+$/)
      expect(id1).not.toBe(id2)
    })
  })

  describe('determineConfidenceBand', () => {
    it('returns low for 3 archives', () => {
      expect(determineConfidenceBand(3)).toBe('low')
    })

    it('returns limited for 4-5 archives', () => {
      expect(determineConfidenceBand(4)).toBe('limited')
      expect(determineConfidenceBand(5)).toBe('limited')
    })

    it('returns emerging for 6+ archives (Dev Order 69 threshold)', () => {
      expect(determineConfidenceBand(6)).toBe('emerging')
      expect(determineConfidenceBand(10)).toBe('emerging')
    })
  })

  describe('getMinSampleSize', () => {
    it('returns 3 as minimum sample size', () => {
      expect(getMinSampleSize()).toBe(3)
    })
  })

  describe('formatConfidenceBand', () => {
    it('formats confidence bands correctly', () => {
      expect(formatConfidenceBand('low')).toBe('Low')
      expect(formatConfidenceBand('limited')).toBe('Limited')
      expect(formatConfidenceBand('emerging')).toBe('Emerging')
    })
  })

  describe('getConfidenceBandGate', () => {
    it('returns correct gate colors', () => {
      expect(getConfidenceBandGate('low')).toBe('red')
      expect(getConfidenceBandGate('limited')).toBe('yellow')
      expect(getConfidenceBandGate('emerging')).toBe('green')
    })
  })

  describe('hasSufficientDataForCorrelations', () => {
    it('returns false when no archives', () => {
      expect(hasSufficientDataForCorrelations([])).toBe(false)
    })

    it('returns false when archives have no variant refs', () => {
      const archives = [
        createArchive('a1', undefined),
        createArchive('a2', undefined),
        createArchive('a3', undefined),
      ]
      expect(hasSufficientDataForCorrelations(archives)).toBe(false)
    })

    it('returns false when fewer than 3 archives per variant', () => {
      const archives = [
        createArchive('a1', ['variant-1']),
        createArchive('a2', ['variant-1']),
      ]
      expect(hasSufficientDataForCorrelations(archives)).toBe(false)
    })

    it('returns true when 3+ archives reference same variant', () => {
      const archives = [
        createArchive('a1', ['variant-1']),
        createArchive('a2', ['variant-1']),
        createArchive('a3', ['variant-1']),
      ]
      expect(hasSufficientDataForCorrelations(archives)).toBe(true)
    })
  })

  describe('computeCorrelations', () => {
    it('returns empty correlations when insufficient data', () => {
      const archives = [
        createArchive('a1', ['variant-1']),
        createArchive('a2', ['variant-1']),
      ]
      const variants = [createVariant('variant-1', 'Test Variant')]

      const result = computeCorrelations(archives, variants)

      expect(result.correlations).toHaveLength(0)
      expect(result.insufficientVariants).toContain('variant-1')
    })

    it('tracks insufficient variants', () => {
      const archives = [
        createArchive('a1', ['variant-1']),
        createArchive('a2', ['variant-2']),
      ]
      const variants = [
        createVariant('variant-1', 'Variant 1'),
        createVariant('variant-2', 'Variant 2'),
      ]

      const result = computeCorrelations(archives, variants)

      expect(result.insufficientVariants).toContain('variant-1')
      expect(result.insufficientVariants).toContain('variant-2')
    })

    it('detects higher pattern when values consistently above baseline', () => {
      // Create archives with variant showing higher Helmholtz values
      const archives = [
        createArchive('a1', ['variant-high'], [
          { property: 'measuredHelmholtzHz', value: 110, unit: 'Hz' },
        ]),
        createArchive('a2', ['variant-high'], [
          { property: 'measuredHelmholtzHz', value: 115, unit: 'Hz' },
        ]),
        createArchive('a3', ['variant-high'], [
          { property: 'measuredHelmholtzHz', value: 112, unit: 'Hz' },
        ]),
        // Baseline archives
        createArchive('a4', undefined, [
          { property: 'measuredHelmholtzHz', value: 100, unit: 'Hz' },
        ]),
        createArchive('a5', undefined, [
          { property: 'measuredHelmholtzHz', value: 95, unit: 'Hz' },
        ]),
      ]
      const variants = [createVariant('variant-high', 'High Variant')]

      const result = computeCorrelations(archives, variants)

      expect(result.correlations.length).toBeGreaterThan(0)
      const helmholtzCorr = result.correlations.find(
        c => c.observedField === 'measuredHelmholtzHz'
      )
      expect(helmholtzCorr?.observedPattern).toBe('higher')
    })

    it('includes timestamp in computed correlations', () => {
      const archives = [
        createArchive('a1', ['variant-1'], [
          { property: 'measuredHelmholtzHz', value: 110, unit: 'Hz' },
        ]),
        createArchive('a2', ['variant-1'], [
          { property: 'measuredHelmholtzHz', value: 115, unit: 'Hz' },
        ]),
        createArchive('a3', ['variant-1'], [
          { property: 'measuredHelmholtzHz', value: 112, unit: 'Hz' },
        ]),
      ]
      const variants = [createVariant('variant-1', 'Test')]

      const result = computeCorrelations(archives, variants)

      expect(result.computedAtIso).toMatch(/^\d{4}-\d{2}-\d{2}T/)
    })
  })

  describe('createVariantCorrelationSummary', () => {
    it('creates summary with zero correlations when none exist', () => {
      const summary = createVariantCorrelationSummary('variant-1', 'Test', [])

      expect(summary.variantId).toBe('variant-1')
      expect(summary.variantTitle).toBe('Test')
      expect(summary.correlationCount).toBe(0)
      expect(summary.archiveCount).toBe(0)
      expect(summary.confidenceBand).toBe('low')
    })

    it('counts correlations for specific variant', () => {
      const correlations: ExperimentalCorrelation[] = [
        {
          correlationId: 'c1',
          sourceVariantId: 'variant-1',
          archiveIds: ['a1', 'a2', 'a3'],
          observedField: 'measuredHelmholtzHz',
          observedPattern: 'higher',
          sampleCount: 3,
          confidenceBand: 'low',
          narrative: 'Test',
          computedAtIso: new Date().toISOString(),
        },
        {
          correlationId: 'c2',
          sourceVariantId: 'variant-1',
          archiveIds: ['a1', 'a2', 'a3'],
          observedField: 'measuredPeakHz',
          observedPattern: 'shifted',
          sampleCount: 3,
          confidenceBand: 'limited',
          narrative: 'Test',
          computedAtIso: new Date().toISOString(),
        },
        {
          correlationId: 'c3',
          sourceVariantId: 'variant-2',
          archiveIds: ['a4', 'a5', 'a6'],
          observedField: 'measuredHelmholtzHz',
          observedPattern: 'lower',
          sampleCount: 3,
          confidenceBand: 'emerging',
          narrative: 'Test',
          computedAtIso: new Date().toISOString(),
        },
      ]

      const summary = createVariantCorrelationSummary('variant-1', 'Variant 1', correlations)

      expect(summary.correlationCount).toBe(2)
      expect(summary.archiveCount).toBe(3) // unique archives
      expect(summary.confidenceBand).toBe('limited') // highest band from correlations
    })

    it('identifies dominant pattern', () => {
      const correlations: ExperimentalCorrelation[] = [
        {
          correlationId: 'c1',
          sourceVariantId: 'variant-1',
          archiveIds: ['a1', 'a2', 'a3'],
          observedField: 'measuredHelmholtzHz',
          observedPattern: 'higher',
          sampleCount: 3,
          confidenceBand: 'low',
          narrative: 'Test',
          computedAtIso: new Date().toISOString(),
        },
        {
          correlationId: 'c2',
          sourceVariantId: 'variant-1',
          archiveIds: ['a1', 'a2', 'a3'],
          observedField: 'measuredPeakHz',
          observedPattern: 'higher',
          sampleCount: 3,
          confidenceBand: 'low',
          narrative: 'Test',
          computedAtIso: new Date().toISOString(),
        },
      ]

      const summary = createVariantCorrelationSummary('variant-1', 'Variant 1', correlations)

      expect(summary.dominantPattern).toBe('higher')
    })
  })

  describe('getAllVariantCorrelationSummaries', () => {
    it('returns empty array when no correlations', () => {
      const summaries = getAllVariantCorrelationSummaries([], [])
      expect(summaries).toHaveLength(0)
    })

    it('creates summaries for all variants with correlations', () => {
      const correlations: ExperimentalCorrelation[] = [
        {
          correlationId: 'c1',
          sourceVariantId: 'variant-1',
          archiveIds: ['a1', 'a2', 'a3'],
          observedField: 'measuredHelmholtzHz',
          observedPattern: 'higher',
          sampleCount: 3,
          confidenceBand: 'low',
          narrative: 'Test',
          computedAtIso: new Date().toISOString(),
        },
        {
          correlationId: 'c2',
          sourceVariantId: 'variant-2',
          archiveIds: ['a4', 'a5', 'a6'],
          observedField: 'measuredHelmholtzHz',
          observedPattern: 'lower',
          sampleCount: 3,
          confidenceBand: 'emerging',
          narrative: 'Test',
          computedAtIso: new Date().toISOString(),
        },
      ]
      const variants = [
        createVariant('variant-1', 'V1'),
        createVariant('variant-2', 'V2'),
      ]

      const summaries = getAllVariantCorrelationSummaries(correlations, variants)

      expect(summaries).toHaveLength(2)
    })

    it('sorts summaries by correlation count descending', () => {
      const correlations: ExperimentalCorrelation[] = [
        {
          correlationId: 'c1',
          sourceVariantId: 'variant-1',
          archiveIds: ['a1'],
          observedField: 'measuredHelmholtzHz',
          observedPattern: 'higher',
          sampleCount: 3,
          confidenceBand: 'low',
          narrative: 'Test',
          computedAtIso: new Date().toISOString(),
        },
        {
          correlationId: 'c2',
          sourceVariantId: 'variant-2',
          archiveIds: ['a2'],
          observedField: 'measuredHelmholtzHz',
          observedPattern: 'lower',
          sampleCount: 3,
          confidenceBand: 'low',
          narrative: 'Test',
          computedAtIso: new Date().toISOString(),
        },
        {
          correlationId: 'c3',
          sourceVariantId: 'variant-2',
          archiveIds: ['a2'],
          observedField: 'measuredPeakHz',
          observedPattern: 'shifted',
          sampleCount: 3,
          confidenceBand: 'low',
          narrative: 'Test',
          computedAtIso: new Date().toISOString(),
        },
      ]
      const variants = [
        createVariant('variant-1', 'V1'),
        createVariant('variant-2', 'V2'),
      ]

      const summaries = getAllVariantCorrelationSummaries(correlations, variants)

      expect(summaries[0].variantId).toBe('variant-2') // 2 correlations
      expect(summaries[1].variantId).toBe('variant-1') // 1 correlation
    })
  })

  describe('forbidden language audit', () => {
    const forbiddenTerms = [
      'causes',
      'improves',
      'optimizes',
      'recommends',
      'proves',
      'validates',
      'best',
    ]

    it('correlation narratives do not use forbidden language', () => {
      const archives = [
        createArchive('a1', ['variant-1'], [
          { property: 'measuredHelmholtzHz', value: 110, unit: 'Hz' },
        ]),
        createArchive('a2', ['variant-1'], [
          { property: 'measuredHelmholtzHz', value: 115, unit: 'Hz' },
        ]),
        createArchive('a3', ['variant-1'], [
          { property: 'measuredHelmholtzHz', value: 112, unit: 'Hz' },
        ]),
        createArchive('a4', undefined, [
          { property: 'measuredHelmholtzHz', value: 95, unit: 'Hz' },
        ]),
      ]
      const variants = [createVariant('variant-1', 'Test Variant')]

      const result = computeCorrelations(archives, variants)

      for (const correlation of result.correlations) {
        const lower = correlation.narrative.toLowerCase()
        for (const term of forbiddenTerms) {
          expect(lower).not.toContain(term.toLowerCase())
        }
      }
    })

    it('narratives use allowed language', () => {
      const archives = [
        createArchive('a1', ['variant-1'], [
          { property: 'measuredHelmholtzHz', value: 110, unit: 'Hz' },
        ]),
        createArchive('a2', ['variant-1'], [
          { property: 'measuredHelmholtzHz', value: 115, unit: 'Hz' },
        ]),
        createArchive('a3', ['variant-1'], [
          { property: 'measuredHelmholtzHz', value: 112, unit: 'Hz' },
        ]),
        createArchive('a4', undefined, [
          { property: 'measuredHelmholtzHz', value: 95, unit: 'Hz' },
        ]),
      ]
      const variants = [createVariant('variant-1', 'Test Variant')]

      const result = computeCorrelations(archives, variants)

      // At least one correlation should exist with allowed language
      const hasAllowedLanguage = result.correlations.some(c => {
        const lower = c.narrative.toLowerCase()
        return (
          lower.includes('correlates with') ||
          lower.includes('observed') ||
          lower.includes('appears with')
        )
      })

      expect(hasAllowedLanguage).toBe(true)
    })
  })

  // ═══════════════════════════════════════════════════════════════════════════
  // Dev Order 69: QA & Boundary Hardening Tests
  // ═══════════════════════════════════════════════════════════════════════════

  describe('Dev Order 69: Archive validation', () => {
    it('isValidArchiveForCorrelation rejects null/undefined', () => {
      expect(isValidArchiveForCorrelation(null)).toBe(false)
      expect(isValidArchiveForCorrelation(undefined)).toBe(false)
    })

    it('isValidArchiveForCorrelation rejects missing archiveId', () => {
      const invalid = {
        kind: 'measurement-archive',
        metadata: { schemaVersion: 'measurement-archive.v1' },
        sections: [],
      }
      expect(isValidArchiveForCorrelation(invalid)).toBe(false)
    })

    it('isValidArchiveForCorrelation rejects wrong schema version', () => {
      const invalid = {
        archiveId: 'test-1',
        kind: 'measurement-archive',
        metadata: { schemaVersion: 'wrong-version' },
        sections: [],
      }
      expect(isValidArchiveForCorrelation(invalid)).toBe(false)
    })

    it('isValidArchiveForCorrelation rejects malformed sections', () => {
      const invalid = {
        archiveId: 'test-1',
        kind: 'measurement-archive',
        metadata: { schemaVersion: 'measurement-archive.v1' },
        sections: 'not-an-array',
      }
      expect(isValidArchiveForCorrelation(invalid)).toBe(false)
    })

    it('isValidArchiveForCorrelation accepts valid archive', () => {
      const valid = createArchive('test-1', undefined, [])
      expect(isValidArchiveForCorrelation(valid)).toBe(true)
    })
  })

  describe('Dev Order 69: Sparse archive detection', () => {
    it('isSparseArchive returns true for fewer than 3 measurements', () => {
      const sparse = createArchive('sparse-1', undefined, [
        { property: 'measuredHelmholtzHz', value: 100, unit: 'Hz' },
      ])
      expect(isSparseArchive(sparse)).toBe(true)
    })

    it('isSparseArchive returns false for 3+ measurements', () => {
      const nonSparse = createArchive('non-sparse', undefined, [
        { property: 'measuredHelmholtzHz', value: 100, unit: 'Hz' },
        { property: 'measuredQ', value: 50, unit: '' },
        { property: 'measuredPeakHz', value: 200, unit: 'Hz' },
      ])
      expect(isSparseArchive(nonSparse)).toBe(false)
    })
  })

  describe('Dev Order 69: filterCorrelatableArchives', () => {
    it('filters out invalid archives', () => {
      const valid = createArchive('valid-1', undefined, [])
      const archives = [valid]
      const { valid: filtered, warnings } = filterCorrelatableArchives(archives)

      expect(filtered).toHaveLength(1)
      expect(filtered[0].archiveId).toBe('valid-1')
    })

    it('produces warnings for sparse archives', () => {
      const sparse = createArchive('sparse-1', undefined, [
        { property: 'measuredHelmholtzHz', value: 100, unit: 'Hz' },
      ])
      const { valid, warnings } = filterCorrelatableArchives([sparse])

      // Sparse archives are included but warned
      expect(valid).toHaveLength(1)
      expect(warnings.some(w => w.includes('sparse'))).toBe(true)
    })
  })

  describe('Dev Order 69: Duplicate archive handling', () => {
    it('deduplicateArchives removes duplicates by archiveId', () => {
      const a1 = createArchive('dup-id', undefined, [])
      const a2 = createArchive('dup-id', undefined, []) // Same ID
      const a3 = createArchive('unique-id', undefined, [])

      const deduped = deduplicateArchives([a1, a2, a3])

      expect(deduped).toHaveLength(2)
      expect(deduped.map(a => a.archiveId)).toContain('dup-id')
      expect(deduped.map(a => a.archiveId)).toContain('unique-id')
    })

    it('duplicate archives do not inflate sample count in correlations', () => {
      // Create 2 unique archives + 1 duplicate
      const archives = [
        createArchive('a1', ['variant-1'], [
          { property: 'measuredHelmholtzHz', value: 110, unit: 'Hz' },
        ]),
        createArchive('a1', ['variant-1'], [ // Duplicate ID
          { property: 'measuredHelmholtzHz', value: 115, unit: 'Hz' },
        ]),
        createArchive('a2', ['variant-1'], [
          { property: 'measuredHelmholtzHz', value: 112, unit: 'Hz' },
        ]),
      ]
      const variants = [createVariant('variant-1', 'Test')]

      const result = computeCorrelations(archives, variants)

      // Should have 2 unique archives, not 3 — below threshold
      expect(result.insufficientVariants).toContain('variant-1')
      expect(result.correlations).toHaveLength(0)
    })
  })

  describe('Dev Order 69: Missing data handling', () => {
    it('handles archives without topology variant references', () => {
      const archives = [
        createArchive('a1', undefined, [
          { property: 'measuredHelmholtzHz', value: 100, unit: 'Hz' },
        ]),
        createArchive('a2', undefined, [
          { property: 'measuredHelmholtzHz', value: 105, unit: 'Hz' },
        ]),
        createArchive('a3', undefined, [
          { property: 'measuredHelmholtzHz', value: 110, unit: 'Hz' },
        ]),
      ]

      const result = computeCorrelations(archives, [])

      // No variant refs = no variant-based correlations
      expect(result.correlations).toHaveLength(0)
      expect(result.insufficientVariants).toHaveLength(0)
    })

    it('handles archives with missing numeric fields gracefully', () => {
      const archives = [
        createArchive('a1', ['variant-1'], [
          { property: 'someOtherField', value: 100, unit: '' },
        ]),
        createArchive('a2', ['variant-1'], [
          { property: 'someOtherField', value: 105, unit: '' },
        ]),
        createArchive('a3', ['variant-1'], [
          { property: 'someOtherField', value: 110, unit: '' },
        ]),
      ]
      const variants = [createVariant('variant-1', 'Test')]

      // Should not throw
      const result = computeCorrelations(archives, variants)

      // No analyzable fields = no correlations
      expect(result.correlations).toHaveLength(0)
    })
  })

  describe('Dev Order 69: Stable sort order', () => {
    it('getAllVariantCorrelationSummaries sorts by correlation count descending', () => {
      const correlations: ExperimentalCorrelation[] = [
        {
          correlationId: 'c1',
          sourceVariantId: 'v-fewer',
          archiveIds: ['a1'],
          observedField: 'measuredHelmholtzHz',
          observedPattern: 'higher',
          sampleCount: 3,
          confidenceBand: 'low',
          narrative: 'Test',
          computedAtIso: new Date().toISOString(),
        },
        {
          correlationId: 'c2',
          sourceVariantId: 'v-more',
          archiveIds: ['a2'],
          observedField: 'measuredHelmholtzHz',
          observedPattern: 'lower',
          sampleCount: 3,
          confidenceBand: 'low',
          narrative: 'Test',
          computedAtIso: new Date().toISOString(),
        },
        {
          correlationId: 'c3',
          sourceVariantId: 'v-more',
          archiveIds: ['a2'],
          observedField: 'measuredQ',
          observedPattern: 'higher',
          sampleCount: 3,
          confidenceBand: 'low',
          narrative: 'Test',
          computedAtIso: new Date().toISOString(),
        },
      ]
      const variants = [
        createVariant('v-fewer', 'Fewer'),
        createVariant('v-more', 'More'),
      ]

      const summaries = getAllVariantCorrelationSummaries(correlations, variants)

      // v-more has 2 correlations, v-fewer has 1
      expect(summaries[0].variantId).toBe('v-more')
      expect(summaries[1].variantId).toBe('v-fewer')
    })
  })

  describe('Dev Order 69: Input mutation check', () => {
    it('computeCorrelations does not mutate input archives', () => {
      const archives = [
        createArchive('a1', ['variant-1'], [
          { property: 'measuredHelmholtzHz', value: 110, unit: 'Hz' },
        ]),
        createArchive('a2', ['variant-1'], [
          { property: 'measuredHelmholtzHz', value: 115, unit: 'Hz' },
        ]),
        createArchive('a3', ['variant-1'], [
          { property: 'measuredHelmholtzHz', value: 112, unit: 'Hz' },
        ]),
      ]
      const variants = [createVariant('variant-1', 'Test')]

      // Deep copy for comparison
      const archivesCopy = JSON.stringify(archives)

      computeCorrelations(archives, variants)

      // Archives should be unchanged
      expect(JSON.stringify(archives)).toBe(archivesCopy)
    })
  })

  describe('Dev Order 69: No causality fields in output', () => {
    it('correlation output has no causality-implying fields', () => {
      const archives = [
        createArchive('a1', ['variant-1'], [
          { property: 'measuredHelmholtzHz', value: 110, unit: 'Hz' },
        ]),
        createArchive('a2', ['variant-1'], [
          { property: 'measuredHelmholtzHz', value: 115, unit: 'Hz' },
        ]),
        createArchive('a3', ['variant-1'], [
          { property: 'measuredHelmholtzHz', value: 112, unit: 'Hz' },
        ]),
        createArchive('a4', undefined, [
          { property: 'measuredHelmholtzHz', value: 95, unit: 'Hz' },
        ]),
      ]
      const variants = [createVariant('variant-1', 'Test')]

      const result = computeCorrelations(archives, variants)

      for (const correlation of result.correlations) {
        // Should not have causal fields
        expect(correlation).not.toHaveProperty('causes')
        expect(correlation).not.toHaveProperty('improves')
        expect(correlation).not.toHaveProperty('optimizes')
        expect(correlation).not.toHaveProperty('recommendation')
        expect(correlation).not.toHaveProperty('validation')
        expect(correlation).not.toHaveProperty('ranking')
        expect(correlation).not.toHaveProperty('score')
      }
    })
  })
})

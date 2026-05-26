/**
 * Experiment Note Tests
 *
 * Dev Order 74: Measurement Lab experiment notes layer
 * Dev Order 75: QA & Measurement Lab notebook hardening
 *
 * Tests note creation, validation, filtering, and summarization.
 *
 * Required test cases (Dev Order 74):
 * 1. creates valid note
 * 2. rejects empty note
 * 3. trims note text
 * 4. preserves tags
 * 5. filters by target
 * 6. summarizes notes by target type
 * 7. deduplicates note IDs
 * 8. normalize does not mutate input
 * 9. invalid target type rejected
 * 10. label generation stable
 * 11. missing optional fields handled safely
 * 12. updatedAt preserved when present
 *
 * QA test cases (Dev Order 75):
 * 13. createExperimentNote does not mutate input params
 * 14. filterNotesByTarget does not mutate input array
 * 15. summarizeExperimentNotes does not mutate input array
 * 16. dedupeExperimentNotes does not mutate input array
 * 17. utility output strings contain no forbidden language
 */

import { describe, it, expect } from 'vitest'
import type { ExperimentNote, ExperimentNoteTargetType } from '../../../types/acoustics/experimentNote'
import {
  VALID_TARGET_TYPES,
  isValidTargetType,
  normalizeTags,
  validateExperimentNote,
  createExperimentNote,
  normalizeExperimentNote,
  filterNotesByTarget,
  filterNotesByTargetId,
  summarizeExperimentNotes,
  dedupeExperimentNotes,
  buildExperimentNoteLabel,
  getTargetTypeLabel,
} from '../experimentNote'

/**
 * Create a mock note for testing
 */
function createMockNote(
  id: string,
  overrides: Partial<ExperimentNote> = {}
): ExperimentNote {
  return {
    noteId: id,
    targetType: 'archive',
    targetId: 'archive-001',
    text: 'Test observation',
    createdAt: new Date().toISOString(),
    ...overrides,
  }
}

describe('experimentNote', () => {
  describe('VALID_TARGET_TYPES', () => {
    it('should include all expected target types', () => {
      expect(VALID_TARGET_TYPES).toContain('archive')
      expect(VALID_TARGET_TYPES).toContain('topologyVariant')
      expect(VALID_TARGET_TYPES).toContain('residualComparison')
      expect(VALID_TARGET_TYPES).toContain('correlation')
      expect(VALID_TARGET_TYPES).toContain('driftRecord')
      expect(VALID_TARGET_TYPES).toContain('driftSynthesis')
      expect(VALID_TARGET_TYPES.length).toBe(6)
    })
  })

  describe('isValidTargetType', () => {
    it('should return true for valid target types', () => {
      expect(isValidTargetType('archive')).toBe(true)
      expect(isValidTargetType('topologyVariant')).toBe(true)
      expect(isValidTargetType('driftRecord')).toBe(true)
    })

    it('should return false for invalid target types', () => {
      expect(isValidTargetType('invalid')).toBe(false)
      expect(isValidTargetType('')).toBe(false)
      expect(isValidTargetType('ARCHIVE')).toBe(false)
    })
  })

  describe('normalizeTags', () => {
    it('should split comma-separated tags', () => {
      const result = normalizeTags('foo, bar, baz')
      expect(result).toEqual(['foo', 'bar', 'baz'])
    })

    it('should trim whitespace from tags', () => {
      const result = normalizeTags('  foo  ,  bar  ')
      expect(result).toEqual(['foo', 'bar'])
    })

    it('should remove empty tags', () => {
      const result = normalizeTags('foo, , bar, , ')
      expect(result).toEqual(['foo', 'bar'])
    })

    it('should deduplicate tags', () => {
      const result = normalizeTags('foo, bar, foo, baz, bar')
      expect(result).toEqual(['foo', 'bar', 'baz'])
    })

    it('should handle empty input', () => {
      expect(normalizeTags('')).toEqual([])
      expect(normalizeTags(null as unknown as string)).toEqual([])
      expect(normalizeTags(undefined as unknown as string)).toEqual([])
    })
  })

  describe('validateExperimentNote', () => {
    it('should return null for valid note', () => {
      const note = createMockNote('n1')
      expect(validateExperimentNote(note)).toBeNull()
    })

    it('should reject missing target type', () => {
      const note = { targetId: 'id', text: 'text' }
      expect(validateExperimentNote(note)).toBe('Target type is required')
    })

    it('should reject invalid target type', () => {
      const note = { targetType: 'invalid' as ExperimentNoteTargetType, targetId: 'id', text: 'text' }
      expect(validateExperimentNote(note)).toBe('Invalid target type: invalid')
    })

    it('should reject missing target ID', () => {
      const note = { targetType: 'archive' as ExperimentNoteTargetType, text: 'text' }
      expect(validateExperimentNote(note)).toBe('Target ID is required')
    })

    it('should reject empty target ID', () => {
      const note = { targetType: 'archive' as ExperimentNoteTargetType, targetId: '   ', text: 'text' }
      expect(validateExperimentNote(note)).toBe('Target ID is required')
    })

    it('should reject missing text', () => {
      const note = { targetType: 'archive' as ExperimentNoteTargetType, targetId: 'id' }
      expect(validateExperimentNote(note)).toBe('Note text is required')
    })

    it('should reject empty text', () => {
      const note = { targetType: 'archive' as ExperimentNoteTargetType, targetId: 'id', text: '   ' }
      expect(validateExperimentNote(note)).toBe('Note text is required')
    })
  })

  describe('createExperimentNote', () => {
    it('should create valid note with required fields', () => {
      const note = createExperimentNote({
        targetType: 'archive',
        targetId: 'archive-001',
        text: 'Observed stable resonance',
      })

      expect(note.noteId).toMatch(/^note-/)
      expect(note.targetType).toBe('archive')
      expect(note.targetId).toBe('archive-001')
      expect(note.text).toBe('Observed stable resonance')
      expect(note.createdAt).toBeDefined()
      expect(note.tags).toBeUndefined()
    })

    it('should trim note text', () => {
      const note = createExperimentNote({
        targetType: 'archive',
        targetId: 'id',
        text: '  Observation with spaces  ',
      })

      expect(note.text).toBe('Observation with spaces')
    })

    it('should trim target ID', () => {
      const note = createExperimentNote({
        targetType: 'archive',
        targetId: '  archive-001  ',
        text: 'text',
      })

      expect(note.targetId).toBe('archive-001')
    })

    it('should preserve normalized tags', () => {
      const note = createExperimentNote({
        targetType: 'driftRecord',
        targetId: 'drift-001',
        text: 'Upward trend observed',
        tags: 'helmholtz, trend, helmholtz',
      })

      expect(note.tags).toEqual(['helmholtz', 'trend'])
    })

    it('should omit tags if empty after normalization', () => {
      const note = createExperimentNote({
        targetType: 'archive',
        targetId: 'id',
        text: 'text',
        tags: '  ,  ,  ',
      })

      expect(note.tags).toBeUndefined()
    })

    it('should throw for empty note text', () => {
      expect(() =>
        createExperimentNote({
          targetType: 'archive',
          targetId: 'id',
          text: '',
        })
      ).toThrow('Note text is required')
    })

    it('should throw for invalid target type', () => {
      expect(() =>
        createExperimentNote({
          targetType: 'invalid' as ExperimentNoteTargetType,
          targetId: 'id',
          text: 'text',
        })
      ).toThrow('Invalid target type')
    })
  })

  describe('normalizeExperimentNote', () => {
    it('should not mutate input', () => {
      const original = createMockNote('n1', { text: '  text  ' })
      const originalText = original.text

      normalizeExperimentNote(original)

      expect(original.text).toBe(originalText)
    })

    it('should trim text', () => {
      const note = createMockNote('n1', { text: '  observation  ' })
      const normalized = normalizeExperimentNote(note)

      expect(normalized.text).toBe('observation')
    })

    it('should trim target ID', () => {
      const note = createMockNote('n1', { targetId: '  archive-001  ' })
      const normalized = normalizeExperimentNote(note)

      expect(normalized.targetId).toBe('archive-001')
    })

    it('should dedupe and trim tags', () => {
      const note = createMockNote('n1', { tags: ['foo', ' bar ', 'foo', '  baz  '] })
      const normalized = normalizeExperimentNote(note)

      expect(normalized.tags).toEqual(['foo', 'bar', 'baz'])
    })

    it('should remove empty tags', () => {
      const note = createMockNote('n1', { tags: ['foo', '', '  ', 'bar'] })
      const normalized = normalizeExperimentNote(note)

      expect(normalized.tags).toEqual(['foo', 'bar'])
    })

    it('should remove tags field if all tags empty', () => {
      const note = createMockNote('n1', { tags: ['', '  ', ''] })
      const normalized = normalizeExperimentNote(note)

      expect(normalized.tags).toBeUndefined()
    })

    it('should preserve updatedAt when present', () => {
      const updatedAt = '2026-05-22T10:00:00Z'
      const note = createMockNote('n1', { updatedAt })
      const normalized = normalizeExperimentNote(note)

      expect(normalized.updatedAt).toBe(updatedAt)
    })
  })

  describe('filterNotesByTarget', () => {
    it('should filter notes by target type', () => {
      const notes = [
        createMockNote('n1', { targetType: 'archive' }),
        createMockNote('n2', { targetType: 'driftRecord' }),
        createMockNote('n3', { targetType: 'archive' }),
        createMockNote('n4', { targetType: 'correlation' }),
      ]

      const archiveNotes = filterNotesByTarget(notes, 'archive')

      expect(archiveNotes.length).toBe(2)
      expect(archiveNotes.every((n) => n.targetType === 'archive')).toBe(true)
    })

    it('should return empty array if no matches', () => {
      const notes = [createMockNote('n1', { targetType: 'archive' })]

      const result = filterNotesByTarget(notes, 'driftSynthesis')

      expect(result).toEqual([])
    })
  })

  describe('filterNotesByTargetId', () => {
    it('should filter notes by target ID', () => {
      const notes = [
        createMockNote('n1', { targetId: 'archive-001' }),
        createMockNote('n2', { targetId: 'archive-002' }),
        createMockNote('n3', { targetId: 'archive-001' }),
      ]

      const result = filterNotesByTargetId(notes, 'archive-001')

      expect(result.length).toBe(2)
      expect(result.every((n) => n.targetId === 'archive-001')).toBe(true)
    })
  })

  describe('summarizeExperimentNotes', () => {
    it('should summarize notes by target type', () => {
      const notes = [
        createMockNote('n1', { targetType: 'archive', targetId: 'a1' }),
        createMockNote('n2', { targetType: 'archive', targetId: 'a2' }),
        createMockNote('n3', { targetType: 'archive', targetId: 'a1' }),
        createMockNote('n4', { targetType: 'driftRecord', targetId: 'd1' }),
      ]

      const summaries = summarizeExperimentNotes(notes)

      const archiveSummary = summaries.find((s) => s.targetType === 'archive')
      expect(archiveSummary).toBeDefined()
      expect(archiveSummary!.noteCount).toBe(3)
      expect(archiveSummary!.targetIds).toContain('a1')
      expect(archiveSummary!.targetIds).toContain('a2')
      expect(archiveSummary!.targetIds.length).toBe(2)

      const driftSummary = summaries.find((s) => s.targetType === 'driftRecord')
      expect(driftSummary).toBeDefined()
      expect(driftSummary!.noteCount).toBe(1)
      expect(driftSummary!.targetIds).toEqual(['d1'])
    })

    it('should return empty array for no notes', () => {
      expect(summarizeExperimentNotes([])).toEqual([])
    })
  })

  describe('dedupeExperimentNotes', () => {
    it('should remove duplicate note IDs', () => {
      const notes = [
        createMockNote('n1'),
        createMockNote('n2'),
        createMockNote('n1'),
        createMockNote('n3'),
        createMockNote('n2'),
      ]

      const deduped = dedupeExperimentNotes(notes)

      expect(deduped.length).toBe(3)
      expect(deduped.map((n) => n.noteId)).toEqual(['n1', 'n2', 'n3'])
    })

    it('should keep first occurrence', () => {
      const notes = [
        createMockNote('n1', { text: 'first' }),
        createMockNote('n1', { text: 'second' }),
      ]

      const deduped = dedupeExperimentNotes(notes)

      expect(deduped.length).toBe(1)
      expect(deduped[0].text).toBe('first')
    })
  })

  describe('buildExperimentNoteLabel', () => {
    it('should build label with target info and text preview', () => {
      const note = createMockNote('n1', {
        targetType: 'archive',
        targetId: 'archive-001',
        text: 'Stable resonance observed',
      })

      const label = buildExperimentNoteLabel(note)

      expect(label).toBe('[archive] archive-001 — Stable resonance observed')
    })

    it('should truncate long text', () => {
      const longText = 'This is a very long observation that exceeds the maximum length for display'
      const note = createMockNote('n1', { text: longText })

      const label = buildExperimentNoteLabel(note, 30)

      expect(label).toContain('...')
      expect(label.length).toBeLessThan(100)
    })

    it('should produce stable output for same input', () => {
      const note = createMockNote('n1')

      const label1 = buildExperimentNoteLabel(note)
      const label2 = buildExperimentNoteLabel(note)

      expect(label1).toBe(label2)
    })
  })

  describe('getTargetTypeLabel', () => {
    it('should return human-readable labels', () => {
      expect(getTargetTypeLabel('archive')).toBe('Archive')
      expect(getTargetTypeLabel('topologyVariant')).toBe('Topology Variant')
      expect(getTargetTypeLabel('residualComparison')).toBe('Residual Comparison')
      expect(getTargetTypeLabel('correlation')).toBe('Correlation')
      expect(getTargetTypeLabel('driftRecord')).toBe('Drift Record')
      expect(getTargetTypeLabel('driftSynthesis')).toBe('Drift Synthesis')
    })
  })

  describe('missing optional fields', () => {
    it('should handle note without tags', () => {
      const note = createMockNote('n1')
      delete note.tags

      expect(() => normalizeExperimentNote(note)).not.toThrow()
      expect(filterNotesByTarget([note], 'archive').length).toBe(1)
    })

    it('should handle note without updatedAt', () => {
      const note = createMockNote('n1')
      delete note.updatedAt

      const normalized = normalizeExperimentNote(note)
      expect(normalized.updatedAt).toBeUndefined()
    })

    it('should preserve all fields through normalize', () => {
      const note: ExperimentNote = {
        noteId: 'n1',
        targetType: 'driftRecord',
        targetId: 'drift-001',
        text: 'Observation',
        createdAt: '2026-05-22T09:00:00Z',
        updatedAt: '2026-05-22T10:00:00Z',
        tags: ['tag1', 'tag2'],
      }

      const normalized = normalizeExperimentNote(note)

      expect(normalized.noteId).toBe(note.noteId)
      expect(normalized.targetType).toBe(note.targetType)
      expect(normalized.targetId).toBe(note.targetId)
      expect(normalized.createdAt).toBe(note.createdAt)
      expect(normalized.updatedAt).toBe(note.updatedAt)
    })
  })

  describe('Dev Order 75: immutability verification', () => {
    it('createExperimentNote should not mutate input params', () => {
      const params = {
        targetType: 'archive' as ExperimentNoteTargetType,
        targetId: '  archive-001  ',
        text: '  observation  ',
        tags: 'foo, bar',
      }

      const originalTargetId = params.targetId
      const originalText = params.text
      const originalTags = params.tags

      createExperimentNote(params)

      expect(params.targetId).toBe(originalTargetId)
      expect(params.text).toBe(originalText)
      expect(params.tags).toBe(originalTags)
    })

    it('filterNotesByTarget should not mutate input array', () => {
      const notes = [
        createMockNote('n1', { targetType: 'archive' }),
        createMockNote('n2', { targetType: 'driftRecord' }),
      ]

      const originalLength = notes.length
      const originalFirst = notes[0]

      filterNotesByTarget(notes, 'archive')

      expect(notes.length).toBe(originalLength)
      expect(notes[0]).toBe(originalFirst)
    })

    it('summarizeExperimentNotes should not mutate input array', () => {
      const notes = [
        createMockNote('n1', { targetType: 'archive' }),
        createMockNote('n2', { targetType: 'driftRecord' }),
      ]

      const originalLength = notes.length
      const originalFirst = notes[0]

      summarizeExperimentNotes(notes)

      expect(notes.length).toBe(originalLength)
      expect(notes[0]).toBe(originalFirst)
    })

    it('dedupeExperimentNotes should not mutate input array', () => {
      const notes = [
        createMockNote('n1'),
        createMockNote('n1'),
        createMockNote('n2'),
      ]

      const originalLength = notes.length
      const originalFirst = notes[0]

      dedupeExperimentNotes(notes)

      expect(notes.length).toBe(originalLength)
      expect(notes[0]).toBe(originalFirst)
    })
  })

  describe('Dev Order 75: observational language compliance', () => {
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
      'calibrate',
      'calibrated',
      'calibrates',
      'calibration',
      'prove',
      'proves',
      'proven',
      'proved',
      'cause',
      'causes',
      'caused',
      'causation',
      'correct',
      'corrected',
      'corrects',
      'authority',
      'authoritative',
    ]

    it('buildExperimentNoteLabel should not contain forbidden language', () => {
      const note = createMockNote('n1', {
        targetType: 'archive',
        targetId: 'archive-001',
        text: 'Observed stable resonance pattern',
      })

      const label = buildExperimentNoteLabel(note)

      for (const word of FORBIDDEN_WORDS) {
        expect(label.toLowerCase()).not.toContain(word)
      }
    })

    it('getTargetTypeLabel should not contain forbidden language for any type', () => {
      for (const targetType of VALID_TARGET_TYPES) {
        const label = getTargetTypeLabel(targetType)

        for (const word of FORBIDDEN_WORDS) {
          expect(label.toLowerCase()).not.toContain(word)
        }
      }
    })

    it('validateExperimentNote error messages should not contain forbidden language', () => {
      const errorCases = [
        { targetId: 'id', text: 'text' },
        { targetType: 'invalid' as ExperimentNoteTargetType, targetId: 'id', text: 'text' },
        { targetType: 'archive' as ExperimentNoteTargetType, text: 'text' },
        { targetType: 'archive' as ExperimentNoteTargetType, targetId: 'id' },
      ]

      for (const testCase of errorCases) {
        const error = validateExperimentNote(testCase)
        if (error) {
          for (const word of FORBIDDEN_WORDS) {
            expect(error.toLowerCase()).not.toContain(word)
          }
        }
      }
    })
  })
})

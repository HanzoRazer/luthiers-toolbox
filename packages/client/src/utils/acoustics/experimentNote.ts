/**
 * Experiment Note Utilities
 *
 * Dev Order 74: Measurement Lab experiment notes layer
 *
 * Notes are human-entered observational annotations that attach to
 * Measurement Lab records. Notes preserve interpretation alongside
 * archives, residuals, correlations, drift timelines, and synthesis.
 *
 * OBSERVATIONAL ONLY:
 * - Notes do NOT establish authority
 * - Notes do NOT alter measurement data
 * - Notes do NOT imply calibration or recommendation
 *
 * Schema: experiment-note.v1
 * Storage: in-memory only (no persistence backend)
 */

import type {
  ExperimentNote,
  ExperimentNoteTargetType,
  ExperimentNoteSummary,
} from '../../types/acoustics/experimentNote'

/** Valid target types for experiment notes */
export const VALID_TARGET_TYPES: ExperimentNoteTargetType[] = [
  'archive',
  'topologyVariant',
  'residualComparison',
  'correlation',
  'driftRecord',
  'driftSynthesis',
]

/**
 * Generate a unique note ID
 */
function generateNoteId(): string {
  return `note-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

/**
 * Check if a target type is valid
 */
export function isValidTargetType(targetType: string): targetType is ExperimentNoteTargetType {
  return VALID_TARGET_TYPES.includes(targetType as ExperimentNoteTargetType)
}

/**
 * Normalize tags from comma-separated input
 * Trims whitespace, removes empty tags, deduplicates
 */
export function normalizeTags(input: string): string[] {
  if (!input || typeof input !== 'string') {
    return []
  }

  const tags = input
    .split(',')
    .map((tag) => tag.trim())
    .filter((tag) => tag.length > 0)

  return [...new Set(tags)]
}

/**
 * Validate an experiment note
 * Returns error message if invalid, null if valid
 */
export function validateExperimentNote(note: Partial<ExperimentNote>): string | null {
  if (!note.targetType) {
    return 'Target type is required'
  }

  if (!isValidTargetType(note.targetType)) {
    return `Invalid target type: ${note.targetType}`
  }

  if (!note.targetId || typeof note.targetId !== 'string' || note.targetId.trim().length === 0) {
    return 'Target ID is required'
  }

  if (!note.text || typeof note.text !== 'string' || note.text.trim().length === 0) {
    return 'Note text is required'
  }

  return null
}

/**
 * Create an experiment note
 * Returns the note or throws if validation fails
 */
export function createExperimentNote(params: {
  targetType: ExperimentNoteTargetType
  targetId: string
  text: string
  tags?: string
}): ExperimentNote {
  const trimmedText = params.text.trim()
  const trimmedTargetId = params.targetId.trim()

  const note: ExperimentNote = {
    noteId: generateNoteId(),
    targetType: params.targetType,
    targetId: trimmedTargetId,
    text: trimmedText,
    createdAt: new Date().toISOString(),
  }

  if (params.tags) {
    const normalizedTags = normalizeTags(params.tags)
    if (normalizedTags.length > 0) {
      note.tags = normalizedTags
    }
  }

  const error = validateExperimentNote(note)
  if (error) {
    throw new Error(error)
  }

  return note
}

/**
 * Normalize an experiment note (immutable)
 * Trims text, normalizes tags, preserves all fields
 */
export function normalizeExperimentNote(note: ExperimentNote): ExperimentNote {
  const normalized: ExperimentNote = {
    ...note,
    text: note.text.trim(),
    targetId: note.targetId.trim(),
  }

  if (note.tags && note.tags.length > 0) {
    const deduped = [...new Set(note.tags.map((t) => t.trim()).filter((t) => t.length > 0))]
    if (deduped.length > 0) {
      normalized.tags = deduped
    } else {
      delete normalized.tags
    }
  }

  return normalized
}

/**
 * Filter notes by target type
 */
export function filterNotesByTarget(
  notes: ExperimentNote[],
  targetType: ExperimentNoteTargetType
): ExperimentNote[] {
  return notes.filter((note) => note.targetType === targetType)
}

/**
 * Filter notes by target ID
 */
export function filterNotesByTargetId(notes: ExperimentNote[], targetId: string): ExperimentNote[] {
  return notes.filter((note) => note.targetId === targetId)
}

/**
 * Summarize notes by target type
 */
export function summarizeExperimentNotes(notes: ExperimentNote[]): ExperimentNoteSummary[] {
  const summaryMap = new Map<ExperimentNoteTargetType, Set<string>>()

  for (const note of notes) {
    const existing = summaryMap.get(note.targetType) ?? new Set<string>()
    existing.add(note.targetId)
    summaryMap.set(note.targetType, existing)
  }

  const summaries: ExperimentNoteSummary[] = []

  for (const [targetType, targetIds] of summaryMap) {
    summaries.push({
      targetType,
      noteCount: notes.filter((n) => n.targetType === targetType).length,
      targetIds: [...targetIds],
    })
  }

  return summaries
}

/**
 * Deduplicate notes by noteId
 * Keeps first occurrence of each noteId
 */
export function dedupeExperimentNotes(notes: ExperimentNote[]): ExperimentNote[] {
  const seen = new Set<string>()
  const result: ExperimentNote[] = []

  for (const note of notes) {
    if (!seen.has(note.noteId)) {
      seen.add(note.noteId)
      result.push(note)
    }
  }

  return result
}

/**
 * Build a display label for a note
 * Format: "[targetType] targetId — text preview"
 */
export function buildExperimentNoteLabel(note: ExperimentNote, maxLength = 60): string {
  const prefix = `[${note.targetType}] ${note.targetId}`
  const textPreview =
    note.text.length > maxLength ? `${note.text.slice(0, maxLength - 3)}...` : note.text

  return `${prefix} — ${textPreview}`
}

/**
 * Get human-readable label for target type
 */
export function getTargetTypeLabel(targetType: ExperimentNoteTargetType): string {
  switch (targetType) {
    case 'archive':
      return 'Archive'
    case 'topologyVariant':
      return 'Topology Variant'
    case 'residualComparison':
      return 'Residual Comparison'
    case 'correlation':
      return 'Correlation'
    case 'driftRecord':
      return 'Drift Record'
    case 'driftSynthesis':
      return 'Drift Synthesis'
    default:
      return targetType
  }
}

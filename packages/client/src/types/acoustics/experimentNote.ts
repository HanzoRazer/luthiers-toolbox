/**
 * Experiment Note Types
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

/**
 * Target types that notes can attach to
 */
export type ExperimentNoteTargetType =
  | 'archive'
  | 'topologyVariant'
  | 'residualComparison'
  | 'correlation'
  | 'driftRecord'
  | 'driftSynthesis'

/**
 * Target reference for a note
 */
export interface ExperimentNoteTarget {
  /** Type of the target record */
  targetType: ExperimentNoteTargetType

  /** ID of the target record */
  targetId: string
}

/**
 * Core experiment note record
 *
 * Represents a human-entered observational annotation attached to
 * a Measurement Lab record.
 */
export interface ExperimentNote {
  /** Unique note identifier */
  noteId: string

  /** Type of the target record */
  targetType: ExperimentNoteTargetType

  /** ID of the target record */
  targetId: string

  /** Note text content */
  text: string

  /** ISO timestamp when note was created */
  createdAt: string

  /** ISO timestamp when note was last updated (future expansion) */
  updatedAt?: string

  /** Optional tags for categorization */
  tags?: string[]
}

/**
 * Summary of notes for a target type
 */
export interface ExperimentNoteSummary {
  /** Target type being summarized */
  targetType: ExperimentNoteTargetType

  /** Number of notes for this target type */
  noteCount: number

  /** Unique target IDs with notes */
  targetIds: string[]
}

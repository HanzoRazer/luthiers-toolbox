/**
 * Experimental Drift Types
 *
 * Dev Order 70: Experimental drift timeline workspace
 *
 * Drift represents measured acoustic change observed across sequential archives.
 * Drift is observational only — it describes temporal patterns without implying
 * causation, optimization, or design superiority.
 *
 * OBSERVATIONAL ONLY:
 * - Drift does NOT imply improvement or degradation
 * - No optimization, recommendation, or prediction semantics
 * - No authority claims about acoustic behavior
 *
 * Allowed language: shifted, diverged, stabilized, observed, repeatedly observed
 * Forbidden language: improved, optimized, better, fixed, recommended, validated
 *
 * Schema: experimental-drift.v1
 * Storage: in-memory only (no persistence backend)
 */

/**
 * Direction of observed drift
 */
export type DriftDirection = 'upward' | 'downward' | 'stable' | 'variable'

/**
 * Context type for drift grouping
 */
export type DriftContextType = 'variant' | 'session' | 'chronological'

/**
 * Single point in a drift timeline
 */
export interface DriftTimelinePoint {
  /** Archive ID for this point */
  archiveId: string

  /** Timestamp (createdAtIso from archive metadata) */
  timestamp?: string

  /** Measured value for the tracked field */
  value: number

  /** Delta from previous point in sequence */
  deltaFromPrevious?: number

  /** Percentage delta from previous point */
  percentDeltaFromPrevious?: number

  /** Topology variant ID if archive has variant reference */
  variantId?: string

  /** Session context from archive */
  sessionContext?: string
}

/**
 * Change observation for a specific field
 */
export interface DriftFieldChange {
  /** Field name (e.g., measuredHelmholtzHz) */
  field: string

  /** Starting value in sequence */
  startValue: number

  /** Ending value in sequence */
  endValue: number

  /** Net change */
  netDelta: number

  /** Net percentage change */
  netPercentDelta: number

  /** Classified direction */
  direction: DriftDirection
}

/**
 * Sequence of archives for drift analysis
 */
export interface DriftSequence {
  /** Unique sequence identifier */
  sequenceId: string

  /** Context ID (variant ID, session context, or 'all') */
  contextId: string

  /** Context label for display */
  contextLabel: string

  /** Type of grouping */
  contextType: DriftContextType

  /** Ordered archive IDs in sequence */
  archiveIds: string[]

  /** Number of archives */
  archiveCount: number
}

/**
 * Core experimental drift record
 *
 * Represents observed drift for a single field across a sequence of archives.
 */
export interface ExperimentalDriftRecord {
  /** Unique drift identifier */
  driftId: string

  /** Archive IDs in chronological order */
  archiveIds: string[]

  /** The measurement field being tracked */
  observedField: string

  /** Classified drift direction */
  direction: DriftDirection

  /** Number of archives in the sample */
  sampleCount: number

  /** Ordered timeline points */
  timelinePoints: DriftTimelinePoint[]

  /** Human-readable narrative describing the drift */
  narrative: string

  /** Context ID (variant ID, session context, or 'chronological') */
  contextId?: string

  /** Context type */
  contextType?: DriftContextType

  /** ISO timestamp when drift was computed */
  computedAtIso: string
}

/**
 * Summary of drift observations for a context (variant/session/chronological)
 */
export interface ExperimentalDriftSummary {
  /** Context identifier */
  contextId: string

  /** Human-readable context label */
  contextLabel: string

  /** Type of context grouping */
  contextType: DriftContextType

  /** Number of drift records for this context */
  driftCount: number

  /** Number of unique archives */
  archiveCount: number

  /** Dominant drift direction across fields */
  dominantDirection: DriftDirection
}

/**
 * Observation about drift behavior
 */
export interface DriftObservation {
  /** Field being observed */
  field: string

  /** Direction of drift */
  direction: DriftDirection

  /** Net percentage change */
  percentChange: number

  /** Narrative description */
  narrative: string
}

/**
 * Result of computing drift from archives
 */
export interface DriftComputeResult {
  /** Computed drift records */
  drifts: ExperimentalDriftRecord[]

  /** Summaries by context */
  summaries: ExperimentalDriftSummary[]

  /** Contexts with insufficient data (<3 archives) */
  insufficientContexts: string[]

  /** Total archives analyzed */
  totalArchivesAnalyzed: number

  /** ISO timestamp when drift was computed */
  computedAtIso: string
}

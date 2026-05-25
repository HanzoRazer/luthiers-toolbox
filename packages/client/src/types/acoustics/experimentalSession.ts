/**
 * ExperimentalSessionRecord — first-class continuity object for Measurement Lab.
 *
 * Groups measurement archives, tracks chronology, preserves operator framing,
 * and links topology variants. Observational only — no recommendation authority.
 *
 * @since Dev Order 85 (2026-05-24)
 */

/**
 * Session record schema version for future migration support.
 */
export const EXPERIMENTAL_SESSION_SCHEMA_VERSION = 'experimental-session.v1' as const;

/**
 * ExperimentalSessionRecord groups measurement archives into a named,
 * operator-framed continuity object.
 *
 * Observational semantics:
 * - No recommendation authority
 * - No correctness claims
 * - Archive order in `archiveIds` IS iteration order (no separate field)
 */
export interface ExperimentalSessionRecord {
  /**
   * Unique session identifier.
   * Format: "experimental-session-YYYYMMDD-HHmmss"
   */
  sessionId: string;

  /**
   * Human-readable session title.
   * Examples: "Spruce vs Cedar Tap Comparison", "Humidity Drift Series A"
   */
  title: string;

  /**
   * Optional objective statement — what the operator is exploring.
   * Framing only, not a hypothesis to be proven.
   */
  objective?: string;

  /**
   * Optional constraints the operator wants to track.
   * Example: "All measurements at 45% RH, same room, same mallet"
   */
  constraints?: string;

  /**
   * Optional freeform notes.
   */
  notes?: string;

  /**
   * Ordered list of archive IDs included in this session.
   * Array order IS iteration order — no separate iterationOrder field.
   * Plain string format matching MeasurementArchive.archiveId.
   */
  archiveIds: string[];

  /**
   * Topology variants referenced by this session.
   * Format: "topology-variant-YYYYMMDD-HHmmss"
   */
  variantIds: string[];

  /**
   * ISO timestamp when session was created.
   */
  startedAt: string;

  /**
   * ISO timestamp of last modification.
   */
  updatedAt: string;

  /**
   * Schema version for migration support.
   */
  schemaVersion: typeof EXPERIMENTAL_SESSION_SCHEMA_VERSION;
}

/**
 * Summary statistics for a session — computed, not stored.
 */
export interface ExperimentalSessionSummary {
  sessionId: string;
  title: string;
  archiveCount: number;
  variantCount: number;
  dateRange: {
    earliest: string | null;
    latest: string | null;
  };
  durationDays: number | null;
}

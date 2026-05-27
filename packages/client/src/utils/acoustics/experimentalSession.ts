/**
 * Experimental Session utilities — pure functions for session lifecycle.
 *
 * Observational only — no recommendation authority, no correctness claims.
 *
 * @since Dev Order 85 (2026-05-24)
 */

import type {
  ExperimentalSessionRecord,
  ExperimentalSessionSummary,
} from '@/types/acoustics/experimentalSession';
import { EXPERIMENTAL_SESSION_SCHEMA_VERSION } from '@/types/acoustics/experimentalSession';
import type { MeasurementArchiveRecord } from '@/types/acoustics/measurementArchive';

/**
 * Generate a session ID with UTC timestamp.
 * Format: "experimental-session-YYYYMMDD-HHmmss"
 */
function generateSessionId(now: Date = new Date()): string {
  const pad = (n: number) => n.toString().padStart(2, '0');
  const year = now.getUTCFullYear();
  const month = pad(now.getUTCMonth() + 1);
  const day = pad(now.getUTCDate());
  const hours = pad(now.getUTCHours());
  const minutes = pad(now.getUTCMinutes());
  const seconds = pad(now.getUTCSeconds());
  return `experimental-session-${year}${month}${day}-${hours}${minutes}${seconds}`;
}

/**
 * Create a new experimental session.
 *
 * @param title - Human-readable session title
 * @param options - Optional objective, constraints, notes
 * @param now - Optional timestamp for testing
 */
export function createExperimentalSession(
  title: string,
  options?: {
    objective?: string;
    constraints?: string;
    notes?: string;
  },
  now: Date = new Date()
): ExperimentalSessionRecord {
  const timestamp = now.toISOString();
  return {
    sessionId: generateSessionId(now),
    title,
    objective: options?.objective,
    constraints: options?.constraints,
    notes: options?.notes,
    archiveIds: [],
    variantIds: [],
    startedAt: timestamp,
    updatedAt: timestamp,
    schemaVersion: EXPERIMENTAL_SESSION_SCHEMA_VERSION,
  };
}

/**
 * Append an archive to a session, returning a new session object.
 * Immutable — does not mutate the input session.
 *
 * @param session - The session to append to
 * @param archiveId - Archive ID to append
 * @param now - Optional timestamp for testing
 */
export function appendArchiveToSession(
  session: ExperimentalSessionRecord,
  archiveId: string,
  now: Date = new Date()
): ExperimentalSessionRecord {
  if (session.archiveIds.includes(archiveId)) {
    return session;
  }
  return {
    ...session,
    archiveIds: [...session.archiveIds, archiveId],
    updatedAt: now.toISOString(),
  };
}

/**
 * Sort archives within a session by their captured timestamps.
 * Returns a new session with archiveIds reordered chronologically.
 *
 * @param session - The session to sort
 * @param archives - Map of archiveId to MeasurementArchiveRecord for timestamp lookup
 * @param now - Optional timestamp for testing
 */
export function sortSessionArchives(
  session: ExperimentalSessionRecord,
  archives: Map<string, MeasurementArchiveRecord>,
  now: Date = new Date()
): ExperimentalSessionRecord {
  const sortedIds = [...session.archiveIds].sort((a, b) => {
    const archiveA = archives.get(a);
    const archiveB = archives.get(b);

    if (!archiveA && !archiveB) return 0;
    if (!archiveA) return 1;
    if (!archiveB) return -1;

    const timeA = archiveA.metadata?.createdAtIso
      ? new Date(archiveA.metadata.createdAtIso).getTime()
      : 0;
    const timeB = archiveB.metadata?.createdAtIso
      ? new Date(archiveB.metadata.createdAtIso).getTime()
      : 0;

    return timeA - timeB;
  });

  const orderChanged =
    sortedIds.length !== session.archiveIds.length ||
    sortedIds.some((id, i) => id !== session.archiveIds[i]);

  if (!orderChanged) {
    return session;
  }

  return {
    ...session,
    archiveIds: sortedIds,
    updatedAt: now.toISOString(),
  };
}

/**
 * Build summary statistics for a session.
 * Computed from archives — not stored on the session.
 *
 * @param session - The session to summarize
 * @param archives - Map of archiveId to MeasurementArchiveRecord for timestamp lookup
 */
export function buildSessionSummary(
  session: ExperimentalSessionRecord,
  archives: Map<string, MeasurementArchiveRecord>
): ExperimentalSessionSummary {
  const timestamps: number[] = [];

  for (const archiveId of session.archiveIds) {
    const archive = archives.get(archiveId);
    if (archive?.metadata?.createdAtIso) {
      timestamps.push(new Date(archive.metadata.createdAtIso).getTime());
    }
  }

  let earliest: string | null = null;
  let latest: string | null = null;
  let durationDays: number | null = null;

  if (timestamps.length > 0) {
    const minTs = Math.min(...timestamps);
    const maxTs = Math.max(...timestamps);
    earliest = new Date(minTs).toISOString();
    latest = new Date(maxTs).toISOString();
    durationDays = Math.round((maxTs - minTs) / (1000 * 60 * 60 * 24));
  }

  return {
    sessionId: session.sessionId,
    title: session.title,
    archiveCount: session.archiveIds.length,
    variantCount: session.variantIds.length,
    dateRange: {
      earliest,
      latest,
    },
    durationDays,
  };
}

/**
 * Link a topology variant to a session, returning a new session object.
 * Immutable — does not mutate the input session.
 *
 * @param session - The session to link to
 * @param variantId - Variant ID to link
 * @param now - Optional timestamp for testing
 */
export function linkVariantToSession(
  session: ExperimentalSessionRecord,
  variantId: string,
  now: Date = new Date()
): ExperimentalSessionRecord {
  if (session.variantIds.includes(variantId)) {
    return session;
  }
  return {
    ...session,
    variantIds: [...session.variantIds, variantId],
    updatedAt: now.toISOString(),
  };
}

// packages/client/src/sdk/endpoints/rmosAcousticsIngest.ts
/**
 * RMOS Acoustics Ingest Audit SDK Endpoints
 *
 * Typed SDK helpers for browsing and retrieving ingest events.
 * These track every /import-zip call (accepted, rejected, quarantined).
 */

import { get } from "@/sdk/core/apiFetch";
import type {
  IngestEventsBrowseParams,
  IngestEventsBrowseResponse,
  IngestEventDetail,
  IngestEventSummary,
} from "@/types/rmosAcousticsIngest";

const BASE = "/rmos/acoustics/ingest";

// ─────────────────────────────────────────────────────────────
// Browse Events
// ─────────────────────────────────────────────────────────────

/**
 * Browse ingest events with pagination and optional outcome filter.
 * Returns newest events first (sorted by created_at_utc DESC).
 *
 * @param params - Optional filters (limit, cursor, outcome)
 * @returns Paginated list of ingest event summaries
 */
export async function browseIngestEvents(
  params: IngestEventsBrowseParams = {}
): Promise<IngestEventsBrowseResponse> {
  const searchParams = new URLSearchParams();
  if (params.limit !== undefined) {
    searchParams.set("limit", String(params.limit));
  }
  if (params.cursor) {
    searchParams.set("cursor", params.cursor);
  }
  if (params.outcome) {
    searchParams.set("outcome", params.outcome);
  }

  const query = searchParams.toString();
  const path = query ? `${BASE}/events?${query}` : `${BASE}/events`;

  return get<IngestEventsBrowseResponse>(path);
}

// ─────────────────────────────────────────────────────────────
// Get Event Detail
// ─────────────────────────────────────────────────────────────

/**
 * Get full detail for a single ingest event.
 *
 * @param eventId - The event_id (e.g., "ingest_abc123...")
 * @returns Full event detail including error/validation payloads
 */
export async function getIngestEvent(
  eventId: string
): Promise<IngestEventDetail> {
  return get<IngestEventDetail>(`${BASE}/events/${eventId}`);
}

// ─────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────

/**
 * Format timestamp for display in local timezone.
 *
 * @param isoUtc - ISO timestamp (e.g., "2026-01-21T15:30:00Z")
 * @returns Formatted local string
 */
export function formatTimestamp(isoUtc: string): string {
  try {
    return new Date(isoUtc).toLocaleString();
  } catch {
    return isoUtc;
  }
}

/**
 * Format timestamp as relative time (e.g., "5 minutes ago").
 *
 * @param isoUtc - ISO timestamp
 * @returns Relative time string
 */
export function formatRelativeTime(isoUtc: string): string {
  try {
    const date = new Date(isoUtc);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHr = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHr / 24);

    if (diffSec < 60) return "just now";
    if (diffMin < 60) return `${diffMin}m ago`;
    if (diffHr < 24) return `${diffHr}h ago`;
    if (diffDay < 7) return `${diffDay}d ago`;
    return date.toLocaleDateString();
  } catch {
    return isoUtc;
  }
}

/**
 * Get a summary line for an event (for table display).
 *
 * @param event - Ingest event summary
 * @returns Human-readable summary
 */
export function getEventSummary(event: IngestEventSummary): string {
  const parts: string[] = [];

  if (event.uploader_filename) {
    parts.push(event.uploader_filename);
  }

  if (event.outcome === "accepted" && event.run_id) {
    parts.push(`-> ${event.run_id.slice(0, 8)}...`);
  }

  if (event.outcome === "rejected" && event.error_code) {
    parts.push(`(${event.error_code})`);
  }

  if (event.outcome === "quarantined") {
    parts.push("(internal error)");
  }

  return parts.join(" ") || event.event_id;
}

/**
 * Format file size for display.
 *
 * @param bytes - Size in bytes (may be null)
 * @returns Human-readable size string
 */
export function formatSize(bytes: number | null | undefined): string {
  if (bytes == null) return "-";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/**
 * Get run viewer link for accepted events.
 *
 * @param event - Ingest event with run_id
 * @returns Router path or null
 */
export function getRunViewerLink(event: IngestEventSummary): string | null {
  if (event.outcome === "accepted" && event.run_id) {
    return `/rmos/run/${event.run_id}`;
  }
  return null;
}

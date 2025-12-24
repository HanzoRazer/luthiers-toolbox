// packages/client/src/api/rmosLogsClient.ts
/**
 * RMOS Logs API Client - H2 Hardening Bundle
 *
 * Cursor-based pagination and server-side filtering for scalable log viewing.
 *
 * Features:
 * - Cursor-based pagination (scales better than offset)
 * - Server-side filtering (mode, tool_id, risk_level, status, source)
 * - Exponential backoff for polling
 * - Type-safe response handling
 */

const BASE_URL = "/api/rmos/logs";

// =============================================================================
// Types
// =============================================================================

export interface RunLogEntry {
  run_id: string;
  created_at_utc: string;
  mode: string;
  tool_id: string;
  status: string;
  risk_level: string;
  score?: number | null;
  warnings: string[];
  source?: string | null;
}

export interface RecentLogsResponse {
  entries: RunLogEntry[];
  next_cursor: string | null;
  has_more: boolean;
  filters_applied: Record<string, string | null>;
}

export interface FetchLogsParams {
  limit?: number;
  cursor?: string | null;
  mode?: string | null;
  tool_id?: string | null;
  risk_level?: string | null;
  status?: string | null;
  source?: string | null;
}

export interface RunDetailsResponse {
  run_id: string;
  created_at_utc: string;
  mode: string;
  tool_id: string;
  status: string;
  request_summary: Record<string, any>;
  feasibility: Record<string, any>;
  decision: Record<string, any>;
  hashes: Record<string, any>;
  outputs: Record<string, any>;
  meta: Record<string, any>;
}

// =============================================================================
// Backoff State
// =============================================================================

const BACKOFF_INITIAL_MS = 5000;
const BACKOFF_MAX_MS = 30000;
const BACKOFF_FACTOR = 2;

let _backoffMs = BACKOFF_INITIAL_MS;
let _consecutiveErrors = 0;

/**
 * Reset backoff to initial value (call on successful fetch).
 */
export function resetBackoff(): void {
  _backoffMs = BACKOFF_INITIAL_MS;
  _consecutiveErrors = 0;
}

/**
 * Get current backoff interval in milliseconds.
 */
export function getBackoffMs(): number {
  return _backoffMs;
}

/**
 * Increment backoff after an error (exponential with cap).
 */
export function incrementBackoff(): number {
  _consecutiveErrors++;
  _backoffMs = Math.min(_backoffMs * BACKOFF_FACTOR, BACKOFF_MAX_MS);
  return _backoffMs;
}

// =============================================================================
// API Functions
// =============================================================================

/**
 * Fetch recent logs with cursor-based pagination and filtering.
 *
 * Uses the /recent/v2 endpoint for cursor support.
 */
export async function fetchRecentLogs(params: FetchLogsParams = {}): Promise<RecentLogsResponse> {
  const query = new URLSearchParams();

  if (params.limit) query.set("limit", String(params.limit));
  if (params.cursor) query.set("cursor", params.cursor);
  if (params.mode) query.set("mode", params.mode);
  if (params.tool_id) query.set("tool_id", params.tool_id);
  if (params.risk_level) query.set("risk_level", params.risk_level);
  if (params.status) query.set("status", params.status);
  if (params.source) query.set("source", params.source);

  const url = `${BASE_URL}/recent/v2?${query.toString()}`;

  try {
    const response = await fetch(url);
    if (!response.ok) {
      incrementBackoff();
      throw new Error(`Failed to fetch logs: ${response.status} ${response.statusText}`);
    }

    resetBackoff();
    return response.json();
  } catch (error) {
    incrementBackoff();
    throw error;
  }
}

/**
 * Fetch next page of logs using cursor from previous response.
 */
export async function fetchNextPage(
  prevResponse: RecentLogsResponse,
  params: Omit<FetchLogsParams, "cursor"> = {}
): Promise<RecentLogsResponse> {
  if (!prevResponse.next_cursor) {
    return {
      entries: [],
      next_cursor: null,
      has_more: false,
      filters_applied: prevResponse.filters_applied,
    };
  }

  return fetchRecentLogs({
    ...params,
    cursor: prevResponse.next_cursor,
  });
}

/**
 * Fetch full details for a single run.
 */
export async function fetchRunDetails(runId: string): Promise<RunDetailsResponse> {
  const response = await fetch(`${BASE_URL}/${encodeURIComponent(runId)}`);
  if (!response.ok) {
    if (response.status === 404) {
      throw new Error(`Run ${runId} not found`);
    }
    throw new Error(`Failed to fetch run: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Check if there are newer runs than the given timestamp.
 *
 * Returns the count of newer entries (0 if none).
 */
export async function checkForNewerRuns(
  newestTimestamp: string,
  params: Omit<FetchLogsParams, "cursor" | "limit"> = {}
): Promise<{ count: number; newest?: RunLogEntry }> {
  try {
    const response = await fetchRecentLogs({
      ...params,
      limit: 50, // Check a reasonable batch
    });

    // Count entries newer than our timestamp
    const newerEntries = response.entries.filter(
      (e) => e.created_at_utc > newestTimestamp
    );

    return {
      count: newerEntries.length,
      newest: newerEntries[0],
    };
  } catch {
    return { count: 0 };
  }
}

// =============================================================================
// Storage Keys for User Preferences
// =============================================================================

const SOFT_CAP_KEY_PREFIX = "rmos_logs_soft_cap_";

/**
 * Get the soft refresh cap for a filter combination.
 */
export function getSoftCap(mode?: string, source?: string): number {
  const key = `${SOFT_CAP_KEY_PREFIX}${mode || "all"}_${source || "all"}`;
  const stored = localStorage.getItem(key);
  return stored ? parseInt(stored, 10) : 25; // Default 25
}

/**
 * Set the soft refresh cap for a filter combination.
 */
export function setSoftCap(cap: number, mode?: string, source?: string): void {
  const key = `${SOFT_CAP_KEY_PREFIX}${mode || "all"}_${source || "all"}`;
  localStorage.setItem(key, String(cap));
}

/**
 * Reset the soft refresh cap for a filter combination to default.
 */
export function resetSoftCap(mode?: string, source?: string): void {
  const key = `${SOFT_CAP_KEY_PREFIX}${mode || "all"}_${source || "all"}`;
  localStorage.removeItem(key);
}

/**
 * RMOS Logs Client - Bundle 31.0.27.1
 *
 * Client for the RMOS Logs v2 API with filtering and run details.
 * Includes exponential backoff for polling resilience.
 */

const API_BASE = '/api/rmos/logs';

// =============================================================================
// EXPONENTIAL BACKOFF POLLING
// =============================================================================

export interface BackoffConfig {
  baseIntervalMs: number;      // Starting interval (default: 5000)
  maxIntervalMs: number;       // Maximum interval (default: 30000)
  multiplier: number;          // Backoff multiplier (default: 2)
  resetOnSuccess: boolean;     // Reset to base on success (default: true)
}

const DEFAULT_BACKOFF_CONFIG: BackoffConfig = {
  baseIntervalMs: 5000,
  maxIntervalMs: 30000,
  multiplier: 2,
  resetOnSuccess: true,
};

export interface PollerState {
  currentIntervalMs: number;
  consecutiveFailures: number;
  lastSuccessTime: number | null;
  lastFailureTime: number | null;
  isRunning: boolean;
}

export type PollerCallback = (data: RecentLogsResponse) => void;
export type PollerErrorCallback = (error: Error, state: PollerState) => void;

/**
 * Creates a polling manager with exponential backoff.
 *
 * Usage:
 *   const poller = createLogsPoller(
 *     { mode: 'art_studio' },
 *     (data) => console.log('Got logs:', data.entries.length),
 *     (err, state) => console.log('Error, backing off to', state.currentIntervalMs)
 *   );
 *   poller.start();
 *   // Later...
 *   poller.stop();
 */
export function createLogsPoller(
  filters: LogFilters,
  onData: PollerCallback,
  onError?: PollerErrorCallback,
  config: Partial<BackoffConfig> = {}
) {
  const cfg: BackoffConfig = { ...DEFAULT_BACKOFF_CONFIG, ...config };

  const state: PollerState = {
    currentIntervalMs: cfg.baseIntervalMs,
    consecutiveFailures: 0,
    lastSuccessTime: null,
    lastFailureTime: null,
    isRunning: false,
  };

  let timeoutId: ReturnType<typeof setTimeout> | null = null;

  async function poll() {
    if (!state.isRunning) return;

    try {
      const data = await fetchRecentLogs(filters);

      // Success - reset backoff
      if (cfg.resetOnSuccess) {
        state.currentIntervalMs = cfg.baseIntervalMs;
      }
      state.consecutiveFailures = 0;
      state.lastSuccessTime = Date.now();

      onData(data);
    } catch (error) {
      // Failure - apply exponential backoff
      state.consecutiveFailures++;
      state.lastFailureTime = Date.now();

      // Increase interval with exponential backoff
      state.currentIntervalMs = Math.min(
        state.currentIntervalMs * cfg.multiplier,
        cfg.maxIntervalMs
      );

      if (onError) {
        onError(error instanceof Error ? error : new Error(String(error)), state);
      }
    }

    // Schedule next poll
    if (state.isRunning) {
      timeoutId = setTimeout(poll, state.currentIntervalMs);
    }
  }

  return {
    /** Start polling */
    start() {
      if (state.isRunning) return;
      state.isRunning = true;
      state.currentIntervalMs = cfg.baseIntervalMs;
      poll(); // Immediate first poll
    },

    /** Stop polling */
    stop() {
      state.isRunning = false;
      if (timeoutId) {
        clearTimeout(timeoutId);
        timeoutId = null;
      }
    },

    /** Get current state */
    getState(): PollerState {
      return { ...state };
    },

    /** Force immediate poll (resets backoff) */
    pollNow() {
      if (timeoutId) {
        clearTimeout(timeoutId);
        timeoutId = null;
      }
      state.currentIntervalMs = cfg.baseIntervalMs;
      poll();
    },

    /** Update filters (takes effect on next poll) */
    setFilters(newFilters: LogFilters) {
      Object.assign(filters, newFilters);
    },
  };
}

export interface RunLogEntry {
  run_id: string;
  created_at_utc: string;
  mode: string;
  tool_id: string;
  status: string;
  risk_level: string;
  score: number | null;
  warnings: string[];
  source: string | null;
}

export interface RecentLogsResponse {
  entries: RunLogEntry[];
  total: number;
  filters_applied: {
    mode: string | null;
    tool_id: string | null;
    risk_level: string | null;
    status: string | null;
    source: string | null;
  };
}

export interface RunDetails {
  run_id: string;
  created_at_utc: string;
  mode: string;
  tool_id: string;
  status: string;
  request_summary: Record<string, unknown>;
  feasibility: Record<string, unknown>;
  decision: {
    risk_level: string;
    score: number | null;
    block_reason: string | null;
    warnings: string[];
    details: Record<string, unknown>;
  };
  hashes: {
    feasibility_sha256: string;
    toolpaths_sha256: string | null;
    gcode_sha256: string | null;
  };
  outputs: Record<string, unknown>;
  meta: Record<string, unknown>;
}

export interface LogFilters {
  mode?: string;
  tool_id?: string;
  risk_level?: string;
  status?: string;
  source?: string;
  limit?: number;
}

/**
 * Build query string from filters.
 */
function buildQuery(filters: LogFilters): string {
  const params = new URLSearchParams();
  if (filters.mode) params.set('mode', filters.mode);
  if (filters.tool_id) params.set('tool_id', filters.tool_id);
  if (filters.risk_level) params.set('risk_level', filters.risk_level);
  if (filters.status) params.set('status', filters.status);
  if (filters.source) params.set('source', filters.source);
  if (filters.limit) params.set('limit', String(filters.limit));
  return params.toString();
}

/**
 * Fetch recent logs with optional filters.
 */
export async function fetchRecentLogs(filters: LogFilters = {}): Promise<RecentLogsResponse> {
  const query = buildQuery(filters);
  const url = `${API_BASE}/recent${query ? '?' + query : ''}`;

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch logs: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch full details for a single run.
 */
export async function fetchRunDetails(runId: string): Promise<RunDetails> {
  const url = `${API_BASE}/${encodeURIComponent(runId)}`;

  const response = await fetch(url);
  if (!response.ok) {
    if (response.status === 404) {
      throw new Error(`Run not found: ${runId}`);
    }
    throw new Error(`Failed to fetch run details: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

/**
 * Build cURL command for fetching recent logs with current filters.
 */
export function buildCurlForLogs(filters: LogFilters, baseUrl: string = ''): string {
  const query = buildQuery(filters);
  const url = `${baseUrl}${API_BASE}/recent${query ? '?' + query : ''}`;
  return `curl -X GET '${url}' -H 'Accept: application/json'`;
}

/**
 * Build cURL command for fetching a specific run.
 */
export function buildCurlForRun(runId: string, baseUrl: string = ''): string {
  const url = `${baseUrl}${API_BASE}/${encodeURIComponent(runId)}`;
  return `curl -X GET '${url}' -H 'Accept: application/json'`;
}

/**
 * Copy text to clipboard with fallback for older browsers.
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(text);
      return true;
    }
    // Fallback for older browsers
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    const success = document.execCommand('copy');
    document.body.removeChild(textarea);
    return success;
  } catch {
    return false;
  }
}

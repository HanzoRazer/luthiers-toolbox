/**
 * SDK Core Types
 *
 * Common types used across all domain clients.
 */

/** Options for all SDK fetch calls */
export type ApiFetchOptions = {
  /** Override base URL (defaults to VITE_API_BASE or /api) */
  baseUrl?: string;
  /** Optional request ID for tracing */
  requestId?: string;
  /** Additional headers */
  headers?: Record<string, string>;
  /** AbortSignal for cancellation */
  signal?: AbortSignal;
};

/** Standard paginated list response */
export type PaginatedResponse<T> = {
  items: T[];
  total?: number;
  next_cursor?: string;
};

/** Common timestamp fields */
export type Timestamped = {
  created_at_utc: string;
  updated_at_utc?: string;
};

/** Common index fields for runs/artifacts */
export type IndexedEntity = {
  tool_id?: string | null;
  material_id?: string | null;
  machine_id?: string | null;
};

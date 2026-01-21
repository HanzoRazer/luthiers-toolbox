// packages/client/src/types/rmosAcoustics.ts
/**
 * RMOS Acoustics API Types
 *
 * Types for the Acoustics Library attachment index and import API.
 * Extracted from live API: 2026-01-17
 */

// ============================================================
// Import ZIP Endpoint
// ============================================================

export type ImportZipOptions = {
  session_id?: string;
  batch_label?: string;
};

export type ImportResponse = {
  run_id: string;
  run_json_path: string;
  attachments_written: number;
  attachments_deduped: number;
  index_updated: boolean;
  mode?: string;
  event_type?: string | null;
  bundle_id?: string | null;
  bundle_sha256?: string | null;
};

// ============================================================
// Attachment Meta Browse
// ============================================================

export type AttachmentMetaEntry = {
  sha256: string;
  kind: string;
  mime: string;
  filename: string;
  size_bytes: number;
  created_at_utc: string;
  first_seen_run_id: string;
  last_seen_run_id: string;
  first_seen_at_utc: string;
  last_seen_at_utc: string;
  ref_count: number;
  attachment_url?: string;
  // Validation report fields (viewer_pack only)
  validation_passed?: boolean;
  validation_errors?: number;
  validation_warnings?: number;
};

export type BrowseParams = {
  limit?: number;
  cursor?: string;
  kind?: string;
  mime_prefix?: string;
  include_urls?: boolean;
};

export type BrowseResponse = {
  count: number;
  total_in_index: number;
  limit: number;
  kind_filter: string | null;
  mime_prefix_filter: string | null;
  next_cursor: string | null;
  entries: AttachmentMetaEntry[];
};

// ============================================================
// Facets
// ============================================================

export type FacetCountKind = {
  kind: string;
  count: number;
};

export type FacetCountMime = {
  mime: string;
  count: number;
};

export type FacetsResponse = {
  schema_version?: string;
  total: number;
  kinds: FacetCountKind[];
  mime_prefixes: { mime_prefix: string; count: number }[];
  mime_exact: FacetCountMime[];
  size_buckets: { bucket: string; count: number }[];
  note?: string;
};

// ============================================================
// Exists Check
// ============================================================

export type ExistsResponse = {
  sha256: string;
  in_index: boolean;
  in_store: boolean;
  size_bytes?: number;
  index_kind?: string;
  index_mime?: string;
  index_filename?: string;
  index_size_bytes?: number;
};

// ============================================================
// Rebuild Index
// ============================================================

export type RebuildResponse = {
  ok: boolean;
  runs_scanned: number;
  attachments_indexed: number;
  unique_sha256: number;
};

// ============================================================
// Recent Attachments
// ============================================================

export type RecentParams = {
  limit?: number;
  cursor?: string;
  kind?: string;
  include_urls?: boolean;
};

export type RecentResponse = {
  schema_version: string;
  source: "attachment_recent_index";
  count: number;
  limit: number;
  kind_filter: string | null;
  next_cursor: string | null;
  entries: AttachmentMetaEntry[];
};

// ============================================================
// Runs Browse (Session/Run-centric Library)
// ============================================================

export type RunSummary = {
  run_id: string;
  created_at_utc: string;
  mode: string;
  status: string;
  session_id: string | null;
  batch_label: string | null;
  event_type: string | null;
  attachment_count: number;
  viewer_pack_count: number;
  kinds_present: string[];
  primary_viewer_pack_sha256: string | null;
};

export type RunsBrowseParams = {
  limit?: number;
  cursor?: string;
  session_id?: string;
  batch_label?: string;
  include_urls?: boolean;
};

export type RunsBrowseResponse = {
  schema_version: string;
  count: number;
  limit: number;
  session_id_filter: string | null;
  batch_label_filter: string | null;
  next_cursor: string | null;
  runs: RunSummary[];
};

export type RunAttachmentEntry = {
  sha256: string;
  kind: string | null;
  mime: string | null;
  filename: string | null;
  size_bytes: number | null;
  created_at_utc: string | null;
  download_url?: string;
};

export type RunDetailParams = {
  include_urls?: boolean;
};

export type RunDetailResponse = {
  schema_version: string;
  run_id: string;
  created_at_utc: string;
  mode: string;
  status: string;
  tool_id: string;
  session_id: string | null;
  batch_label: string | null;
  event_type: string | null;
  request_summary: Record<string, unknown>;
  meta: Record<string, unknown>;
  attachment_count: number;
  attachments: RunAttachmentEntry[];
};

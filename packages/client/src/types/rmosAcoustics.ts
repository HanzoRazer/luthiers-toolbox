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

export type FacetsResponse = {
  facets: {
    kind: Record<string, number>;
    mime: Record<string, number>;
  };
  total_attachments: number;
  index_version: string;
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

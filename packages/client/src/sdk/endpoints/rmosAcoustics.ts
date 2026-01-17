// packages/client/src/sdk/endpoints/rmosAcoustics.ts
/**
 * RMOS Acoustics SDK Endpoints
 *
 * Typed SDK helpers for the Acoustics Library attachment index and import API.
 * Connects to viewer_pack evidence bundles from tap_tone_pi.
 */

import { get, post } from "@/sdk/core/apiFetch";
import { postFormRaw } from "@/sdk/core/apiFetchRaw";
import type {
  AttachmentMetaEntry,
  BrowseParams,
  BrowseResponse,
  ExistsResponse,
  FacetsResponse,
  ImportResponse,
  ImportZipOptions,
  RebuildResponse,
  RecentParams,
  RecentResponse,
} from "@/types/rmosAcoustics";

const BASE = "/rmos/acoustics";

// ─────────────────────────────────────────────────────────────
// Import
// ─────────────────────────────────────────────────────────────

/**
 * Import a viewer_pack ZIP containing manifest.json + attachments.
 *
 * @param file - The ZIP file to import
 * @param options - Optional session_id and batch_label
 * @returns Import result with run_id and attachment counts
 */
export async function importZip(
  file: File,
  options?: ImportZipOptions
): Promise<ImportResponse> {
  const formData = new FormData();
  formData.append("file", file);
  if (options?.session_id) {
    formData.append("session_id", options.session_id);
  }
  if (options?.batch_label) {
    formData.append("batch_label", options.batch_label);
  }

  const { data } = await postFormRaw<ImportResponse>(
    `${BASE}/import-zip`,
    formData
  );
  return data;
}

// ─────────────────────────────────────────────────────────────
// Browse & Query
// ─────────────────────────────────────────────────────────────

/**
 * Browse the attachment meta index with pagination and filters.
 *
 * @param params - Optional filters (limit, cursor, kind, mime_prefix, include_urls)
 * @returns Paginated list of attachment entries
 */
export async function browse(params: BrowseParams = {}): Promise<BrowseResponse> {
  const searchParams = new URLSearchParams();
  if (params.limit !== undefined) {
    searchParams.set("limit", String(params.limit));
  }
  if (params.cursor) {
    searchParams.set("cursor", params.cursor);
  }
  if (params.kind) {
    searchParams.set("kind", params.kind);
  }
  if (params.mime_prefix) {
    searchParams.set("mime_prefix", params.mime_prefix);
  }
  if (params.include_urls) {
    searchParams.set("include_urls", "true");
  }

  const query = searchParams.toString();
  const path = query
    ? `${BASE}/index/attachment_meta?${query}`
    : `${BASE}/index/attachment_meta`;

  return get<BrowseResponse>(path);
}

/**
 * Get facet counts (kind and MIME type distributions).
 *
 * @returns Facet counts and index metadata
 */
export async function getFacets(): Promise<FacetsResponse> {
  return get<FacetsResponse>(`${BASE}/index/attachment_meta/facets`);
}

/**
 * Get recent attachments from precomputed recency index.
 * Fast O(K) where K is max_recent_entries (default 5000).
 *
 * @param params - Optional filters (limit, cursor, kind, include_urls)
 * @returns Paginated list of recent attachment entries (sorted by created_at_utc DESC)
 */
export async function getRecent(params: RecentParams = {}): Promise<RecentResponse> {
  const searchParams = new URLSearchParams();
  if (params.limit !== undefined) {
    searchParams.set("limit", String(params.limit));
  }
  if (params.cursor) {
    searchParams.set("cursor", params.cursor);
  }
  if (params.kind) {
    searchParams.set("kind", params.kind);
  }
  if (params.include_urls) {
    searchParams.set("include_urls", "true");
  }

  const query = searchParams.toString();
  const path = query
    ? `${BASE}/index/attachment_meta/recent?${query}`
    : `${BASE}/index/attachment_meta/recent`;

  return get<RecentResponse>(path);
}

/**
 * Check if an attachment exists in the index and store.
 *
 * @param sha256 - Content hash of the attachment
 * @returns Existence status and metadata
 */
export async function checkExists(sha256: string): Promise<ExistsResponse> {
  return get<ExistsResponse>(`${BASE}/index/attachment_meta/${sha256}/exists`);
}

// ─────────────────────────────────────────────────────────────
// Index Management
// ─────────────────────────────────────────────────────────────

/**
 * Rebuild the attachment meta index from all runs.
 * Use this if facets are empty or index is stale.
 *
 * @returns Rebuild statistics
 */
export async function rebuildIndex(): Promise<RebuildResponse> {
  return post<RebuildResponse>(`${BASE}/index/rebuild_attachment_meta`);
}

// ─────────────────────────────────────────────────────────────
// Downloads & Helpers
// ─────────────────────────────────────────────────────────────

/**
 * Get the download URL for an attachment.
 * Returns a path that can be used directly or with the API base.
 *
 * @param sha256 - Content hash of the attachment
 * @returns Download URL path
 */
export function getDownloadUrl(sha256: string): string {
  return `/api${BASE}/attachments/${sha256}`;
}

/**
 * Check if an attachment entry is a viewer pack.
 *
 * @param entry - Attachment meta entry
 * @returns True if this is a viewer_pack
 */
export function isViewerPack(entry: AttachmentMetaEntry): boolean {
  return (
    entry.kind === "viewer_pack" ||
    (entry.mime === "application/zip" && entry.filename.includes("viewer"))
  );
}

/**
 * Format file size for display.
 *
 * @param bytes - Size in bytes
 * @returns Human-readable size string
 */
export function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

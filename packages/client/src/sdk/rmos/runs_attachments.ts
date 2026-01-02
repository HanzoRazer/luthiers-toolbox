/**
 * RMOS Run Attachments Client
 *
 * Bundle 16-17: Type-safe client for run attachments with path normalization.
 *
 * Contract: RMOS_RUNS_V2_ATTACHMENTS_CONTRACT_v1.md
 */

import { get } from "../core/apiFetch";
import type { ApiFetchOptions } from "../core/types";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/**
 * Normalized attachment row (Bundle 17 contract).
 *
 * Required keys:
 * - att_id: Always present (stable identifier)
 * - path: Always present (normalized to forward slashes)
 *
 * Optional:
 * - sha256, size_bytes, content_type, signed_url
 */
export type RunAttachmentRow = {
  att_id: string;
  path: string;
  sha256?: string;
  size_bytes?: number;
  content_type?: string;
  signed_url?: string;
};

/** Attachments list response */
export type RunAttachmentsListResponse = {
  attachments: RunAttachmentRow[];
};

// ---------------------------------------------------------------------------
// API Functions
// ---------------------------------------------------------------------------

/**
 * List attachments for a run with normalized paths.
 *
 * @param baseUrl - API base URL (pass "" to use default)
 * @param runId - Run ID to list attachments for
 * @param requestId - Optional X-Request-Id for tracing
 * @param includeSignedUrls - Include signed_url in each row (default false)
 */
export async function listAttachments(
  baseUrl: string,
  runId: string,
  requestId?: string,
  includeSignedUrls: boolean = false
): Promise<{ data: RunAttachmentsListResponse; requestId: string }> {
  const params = new URLSearchParams();
  if (includeSignedUrls) {
    params.set("include_signed_urls", "1");
  }
  const qs = params.toString();

  const opts: ApiFetchOptions = { requestId };
  if (baseUrl) {
    opts.baseUrl = baseUrl;
  }

  const data = await get<RunAttachmentsListResponse>(
    `/rmos/runs/${encodeURIComponent(runId)}/attachments${qs ? `?${qs}` : ""}`,
    opts
  );

  return { data, requestId: requestId || "auto" };
}

/**
 * Fetch attachment content as text.
 *
 * Strategy:
 * 1. If attachment has signed_url, fetch directly
 * 2. Otherwise, fetch via API endpoint
 *
 * @param baseUrl - API base URL
 * @param runId - Run ID
 * @param attachment - Attachment row (from list response)
 * @param requestId - Optional X-Request-Id
 */
export async function fetchText(
  baseUrl: string,
  runId: string,
  attachment: RunAttachmentRow,
  requestId?: string
): Promise<{ text: string; source: "signed_url" | "api" }> {
  // Prefer signed_url if available
  if (attachment.signed_url) {
    const res = await fetch(attachment.signed_url);
    if (!res.ok) {
      throw new Error(`Signed URL fetch failed: ${res.status}`);
    }
    const text = await res.text();
    return { text, source: "signed_url" };
  }

  // Fallback: API endpoint
  const url = `${baseUrl || ""}/api/rmos/runs/${encodeURIComponent(runId)}/attachments/${encodeURIComponent(attachment.att_id)}`;
  const headers: Record<string, string> = {};
  if (requestId) {
    headers["X-Request-Id"] = requestId;
  }

  const res = await fetch(url, { headers });
  if (!res.ok) {
    throw new Error(`Attachment fetch failed: ${res.status}`);
  }
  const text = await res.text();
  return { text, source: "api" };
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Get the attachment ID from a row (normalized).
 */
function _getAttachmentId(row: RunAttachmentRow): string {
  return row.att_id;
}

/**
 * Get the attachment path from a row (normalized).
 */
function _getAttachmentPath(row: RunAttachmentRow): string {
  return row.path;
}

// ---------------------------------------------------------------------------
// Export namespace-style object
// ---------------------------------------------------------------------------

export const rmosRunAttachments = {
  list: listAttachments,
  fetchText,
  _getAttachmentId,
  _getAttachmentPath,
};

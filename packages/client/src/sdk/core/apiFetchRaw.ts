/**
 * Raw API Fetch (H8.3 Transport)
 *
 * Variant of apiFetch that returns both parsed data AND the Response object.
 * This enables endpoint helpers to parse custom headers (e.g., X-CAM-Summary).
 *
 * Use this when you need access to response headers in typed helpers.
 */

import { ApiError } from "./errors";
import { handleDeprecationHeaders, generateRequestId } from "./headers";
import { assertRequestIdHeader } from "./assertRequestId";
import type { ApiFetchOptions } from "./types";

const DEFAULT_BASE = (import.meta as any).env?.VITE_API_BASE || "/api";

/**
 * Read response body as JSON if content-type indicates JSON, otherwise as text.
 */
async function readMaybeJson(res: Response): Promise<unknown> {
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) {
    return res.json();
  }
  return res.text();
}

/**
 * Raw fetch function that returns both data and Response object.
 *
 * @param path - API path (e.g., "/cam/roughing_gcode")
 * @param init - Fetch init with required method
 * @param opts - SDK options (baseUrl, requestId, headers, signal)
 * @returns Object with { data, response } for header access
 * @throws ApiError on non-2xx responses
 */
export async function apiFetchRaw<T>(
  path: string,
  init: RequestInit & { method: string },
  opts: ApiFetchOptions = {}
): Promise<{ data: T; response: Response }> {
  const baseUrl = opts.baseUrl ?? DEFAULT_BASE;
  const url = `${baseUrl}${path.startsWith("/") ? "" : "/"}${path}`;

  // Build headers
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(opts.headers ?? {}),
    ...(init.headers ? (init.headers as Record<string, string>) : {}),
  };

  // Add or generate request ID
  const requestId = opts.requestId ?? generateRequestId();
  headers["X-Request-Id"] = requestId;

  const res = await fetch(url, {
    ...init,
    headers,
    signal: opts.signal,
  });

  // Handle deprecation headers (non-blocking)
  handleDeprecationHeaders(res, { url, method: init.method });

  // Enterprise-safe request-id enforcement
  assertRequestIdHeader(res, { endpoint: path, method: init.method });

  // Error handling
  if (!res.ok) {
    const details = await readMaybeJson(res);
    throw new ApiError(`API ${res.status} for ${init.method} ${path}`, {
      status: res.status,
      url,
      details,
    });
  }

  const data = (await readMaybeJson(res)) as T;
  return { data, response: res };
}

/**
 * POST request helper (raw variant)
 */
export function postRaw<T>(
  path: string,
  body?: unknown,
  opts?: ApiFetchOptions
): Promise<{ data: T; response: Response }> {
  return apiFetchRaw<T>(
    path,
    {
      method: "POST",
      body: body !== undefined ? JSON.stringify(body) : undefined,
    },
    opts
  );
}

/**
 * POST with FormData (no Content-Type override)
 */
export function postFormRaw<T>(
  path: string,
  formData: FormData,
  opts?: ApiFetchOptions
): Promise<{ data: T; response: Response }> {
  const headers = { ...(opts?.headers ?? {}) };
  delete headers["Content-Type"]; // Let browser set multipart boundary

  return apiFetchRaw<T>(
    path,
    {
      method: "POST",
      body: formData,
      headers,
    },
    { ...opts, headers }
  );
}

/**
 * SDK Core Fetch
 *
 * Central fetch wrapper with:
 * - Base URL handling
 * - X-Request-Id propagation
 * - Deprecation header detection
 * - Consistent error handling
 */

import { ApiError } from "./errors";
import { handleDeprecationHeaders, generateRequestId } from "./headers";
import { assertRequestIdHeader } from "./assertRequestId";
import type { ApiFetchOptions } from "./types";

const DEFAULT_BASE =
  (import.meta as any).env?.VITE_API_BASE || "/api";

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
 * Core fetch function for all SDK calls.
 *
 * @param path - API path (e.g., "/rmos/runs")
 * @param init - Fetch init with required method
 * @param opts - SDK options (baseUrl, requestId, headers, signal)
 * @returns Parsed response body
 * @throws ApiError on non-2xx responses
 */
export async function apiFetch<T>(
  path: string,
  init: RequestInit & { method: string },
  opts: ApiFetchOptions = {}
): Promise<T> {
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

  // Enterprise-safe request-id enforcement (configurable via VITE_REQUIRE_REQUEST_ID)
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

  return (await readMaybeJson(res)) as T;
}

/**
 * GET request helper
 */
export function get<T>(path: string, opts?: ApiFetchOptions): Promise<T> {
  return apiFetch<T>(path, { method: "GET" }, opts);
}

/**
 * POST request helper
 */
export function post<T>(
  path: string,
  body?: unknown,
  opts?: ApiFetchOptions
): Promise<T> {
  return apiFetch<T>(
    path,
    {
      method: "POST",
      body: body !== undefined ? JSON.stringify(body) : undefined,
    },
    opts
  );
}

/**
 * PATCH request helper
 */
export function patch<T>(
  path: string,
  body?: unknown,
  opts?: ApiFetchOptions
): Promise<T> {
  return apiFetch<T>(
    path,
    {
      method: "PATCH",
      body: body !== undefined ? JSON.stringify(body) : undefined,
    },
    opts
  );
}

/**
 * PUT request helper
 */
export function put<T>(
  path: string,
  body?: unknown,
  opts?: ApiFetchOptions
): Promise<T> {
  return apiFetch<T>(
    path,
    {
      method: "PUT",
      body: body !== undefined ? JSON.stringify(body) : undefined,
    },
    opts
  );
}

/**
 * DELETE request helper
 */
export function del<T>(path: string, opts?: ApiFetchOptions): Promise<T> {
  return apiFetch<T>(path, { method: "DELETE" }, opts);
}

export { ApiFetchOptions };

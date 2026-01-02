/**
 * Deprecation Banner (H8.5)
 *
 * Re-exports deprecation handling from headers.ts for http.ts compatibility.
 * The canonical implementation is in headers.ts.
 *
 * Contract: ROUTING_TRUTH_CONTRACT_v1.md
 */

import { handleDeprecationHeaders, resetDeprecationWarning } from "./headers";

/**
 * Check response headers for deprecation markers and log console warning.
 *
 * Call this after every fetch() in the SDK transport layer.
 * Only logs once per browser session to avoid console spam.
 *
 * @param resp - The Response object from fetch()
 * @param url - Optional URL (extracted from response if not provided)
 * @param method - Optional HTTP method (defaults to "GET")
 */
export function noteDeprecationFromResponse(
  resp: Response,
  url?: string,
  method?: string
): void {
  handleDeprecationHeaders(resp, {
    url: url ?? resp.url ?? "unknown",
    method: method ?? "GET",
  });
}

export { resetDeprecationWarning };

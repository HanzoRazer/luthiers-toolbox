/**
 * Request ID Assertion Helper
 *
 * Enterprise-grade enforcement of X-Request-Id header presence.
 * Ensures request tracing is maintained end-to-end.
 *
 * Modes:
 *   - strict: throws Error (CI / enterprise mode)
 *   - warn:   console.warn only (default for dev)
 *   - off:    no-op (for intentional negative tests)
 */

export type RequestIdAssertMode = "strict" | "warn" | "off";

export type RequestIdAssertOptions = {
  /** Assertion mode (defaults based on VITE_REQUIRE_REQUEST_ID env) */
  mode?: RequestIdAssertMode;
  /** Endpoint path for context in error messages */
  endpoint?: string;
  /** HTTP method for context in error messages */
  method?: string;
};

const DEFAULT_MODE: RequestIdAssertMode =
  (import.meta as any).env?.VITE_REQUIRE_REQUEST_ID === "true"
    ? "strict"
    : "warn";

/**
 * Assert that a response includes X-Request-Id header.
 *
 * This enforces the contract that all API responses must include
 * a request ID for tracing and debugging.
 *
 * @param response - Fetch Response object
 * @param opts - Assertion options
 * @throws Error in strict mode if header is missing
 *
 * @example
 * // Default behavior (warn in dev, strict if VITE_REQUIRE_REQUEST_ID=true)
 * assertRequestIdHeader(response, { endpoint: "/api/runs", method: "GET" });
 *
 * @example
 * // Explicit strict mode
 * assertRequestIdHeader(response, { mode: "strict" });
 *
 * @example
 * // Opt-out for negative tests
 * assertRequestIdHeader(response, { mode: "off" });
 */
export function assertRequestIdHeader(
  response: Response,
  opts: RequestIdAssertOptions = {}
): void {
  const mode = opts.mode ?? DEFAULT_MODE;

  if (mode === "off") return;

  const requestId = response.headers.get("X-Request-Id");

  if (requestId) return;

  const label = "[sdk][request-id] Missing X-Request-Id";
  const context = {
    endpoint: opts.endpoint,
    method: opts.method,
    status: response.status,
    url: response.url,
  };

  if (mode === "strict") {
    throw new Error(`${label} ${JSON.stringify(context)}`);
  }

  // warn mode
  // eslint-disable-next-line no-console
  console.warn(label, context);
}

/**
 * Check if request ID enforcement is in strict mode.
 * Useful for conditional test logic.
 */
export function isRequestIdStrict(): boolean {
  return DEFAULT_MODE === "strict";
}

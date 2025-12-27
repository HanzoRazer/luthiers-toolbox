/**
 * SDK Header Utilities
 *
 * Handles deprecation headers, X-Request-Id propagation, and related concerns.
 */

export type DeprecationEvent = {
  url: string;
  method: string;
  deprecation?: string | null;
  sunset?: string | null;
  link?: string | null;
  lane?: string | null;
};

let onDeprecation: ((e: DeprecationEvent) => void) | null = null;

/**
 * Set a global handler for deprecation warnings.
 * Called whenever a response includes Deprecation headers.
 */
export function setDeprecationHandler(
  fn: ((e: DeprecationEvent) => void) | null
): void {
  onDeprecation = fn;
}

/**
 * Check response headers for deprecation signals and invoke handler.
 */
export function handleDeprecationHeaders(
  res: Response,
  info: { url: string; method: string }
): void {
  const deprecation = res.headers.get("Deprecation");
  const sunset = res.headers.get("Sunset");
  const link = res.headers.get("Link");
  const lane = res.headers.get("X-Deprecated-Lane");

  if (deprecation || sunset || link) {
    onDeprecation?.({
      url: info.url,
      method: info.method,
      deprecation,
      sunset,
      link,
      lane,
    });
  }
}

/**
 * Generate a unique request ID (UUID v4 style).
 */
export function generateRequestId(): string {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  // Fallback for older browsers
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

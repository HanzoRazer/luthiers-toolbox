/**
 * Deprecation Banner (H8.5)
 *
 * Detects deprecated API endpoints via response headers and logs
 * a one-time console warning per session.
 *
 * Contract: ROUTING_TRUTH_CONTRACT_v1.md
 *
 * Headers detected:
 *   - Deprecation: true
 *   - Sunset: <ISO date>
 *   - X-Deprecated-Lane: <lane_key>
 *   - Link: <successor>; rel="successor-version"
 */

let hasWarned = false;

/**
 * Check response headers for deprecation markers and log console warning.
 *
 * Call this after every fetch() in the SDK transport layer.
 * Only logs once per browser session to avoid console spam.
 *
 * @param resp - The Response object from fetch()
 */
export function noteDeprecationFromResponse(resp: Response): void {
  const dep = resp.headers.get("Deprecation");
  if (!dep || dep.toLowerCase() !== "true") return;

  const lane = resp.headers.get("X-Deprecated-Lane") || "unknown_lane";
  const sunset = resp.headers.get("Sunset") || "unknown_date";
  const link = resp.headers.get("Link") || "";

  // One-line banner (once per session)
  if (!hasWarned) {
    hasWarned = true;
    // eslint-disable-next-line no-console
    console.warn(
      `[DEPRECATION] deprecated lane=${lane} sunset=${sunset} ${link}`.trim()
    );
  }
}

/**
 * Reset warning state (for testing).
 */
export function resetDeprecationWarning(): void {
  hasWarned = false;
}

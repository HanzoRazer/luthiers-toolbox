/**
 * SDK Auth Integration
 *
 * Provides auth header injection for SDK calls.
 * Integrates with the auth store to automatically include Bearer tokens.
 */

import { getAccessToken } from "@/auth/supabase";

/**
 * Get the Authorization header value if authenticated.
 * Returns undefined if not authenticated (allows unauthenticated calls).
 */
export async function getAuthHeader(): Promise<string | undefined> {
  const token = await getAccessToken();
  return token ? `Bearer ${token}` : undefined;
}

/**
 * Build headers object with auth if available.
 * Merges with existing headers.
 */
export async function withAuthHeaders(
  headers: Record<string, string> = {}
): Promise<Record<string, string>> {
  const authHeader = await getAuthHeader();

  if (authHeader) {
    return {
      ...headers,
      Authorization: authHeader,
    };
  }

  return headers;
}

/**
 * Check if we should skip auth for a given path.
 * Some endpoints are public and don't need authentication.
 */
export function shouldSkipAuth(path: string): boolean {
  const publicPaths = [
    "/health",
    "/api/health",
    "/metrics",
    "/api/_meta",
  ];

  return publicPaths.some((p) => path.startsWith(p));
}

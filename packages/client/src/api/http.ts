/**
 * HTTP Helper - Bundle 31.0.5
 *
 * Simple fetch wrapper for API calls.
 */

export async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });

  // DEV-ONLY deprecation banner (Guardrail 3)
  if (import.meta.env.DEV) {
    const deprecated = res.headers.get("Deprecation");
    if (deprecated === "true") {
      const lane = res.headers.get("X-Deprecated-Lane") || "unknown";
      const successor = res.headers.get("Link") || "";
      console.warn(
        `[DEPRECATED API HIT] ${res.url} lane=${lane} successor=${successor}`
      );
    }
  }

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status} ${res.statusText}: ${text}`);
  }

  return (await res.json()) as T;
}

/**
 * HTTP Helpers
 * 
 * Shared fetch utilities for all AI Images API clients.
 * 
 * @package features/ai_images/api
 */

// =============================================================================
// CONFIGURATION
// =============================================================================

/** Base URL for API calls - uses VITE_API_BASE for cross-origin deployments */
const API_BASE = (import.meta as any).env?.VITE_API_BASE || '';

/** Default timeout for requests */
const DEFAULT_TIMEOUT_MS = 10000;

/** Prepend base URL if path is relative */
function resolveUrl(url: string): string {
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return url;
  }
  return `${API_BASE}${url}`;
}

/** Extended timeout for generation requests */
export const GENERATION_TIMEOUT_MS = 60000;

// =============================================================================
// ERROR CLASS
// =============================================================================

export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode: number = 500,
    public details?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// =============================================================================
// FETCH HELPERS
// =============================================================================

interface FetchOptions extends RequestInit {
  timeout?: number;
}

/**
 * Fetch with timeout and error handling.
 */
export async function fetchWithTimeout(
  url: string,
  options: FetchOptions = {}
): Promise<Response> {
  const { timeout = DEFAULT_TIMEOUT_MS, ...fetchOptions } = options;
  
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);
  
  try {
    const response = await fetch(url, {
      ...fetchOptions,
      signal: controller.signal,
    });

    // DEV-ONLY deprecation banner (Guardrail 3)
    if (import.meta.env.DEV) {
      const deprecated = response.headers.get("Deprecation");
      if (deprecated === "true") {
        const lane = response.headers.get("X-Deprecated-Lane") || "unknown";
        const successor = response.headers.get("Link") || "";
        console.warn(
          `[DEPRECATED API HIT] ${response.url} lane=${lane} successor=${successor}`
        );
      }
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new ApiError(
        error.detail || error.message || `HTTP ${response.status}`,
        response.status,
        error
      );
    }
    
    return response;
  } catch (err) {
    if (err instanceof ApiError) throw err;
    if ((err as Error).name === 'AbortError') {
      throw new ApiError('Request timed out', 408);
    }
    throw new ApiError((err as Error).message || 'Network error', 0);
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * POST JSON request.
 */
export async function postJson<T>(
  url: string,
  body: unknown,
  timeout?: number
): Promise<T> {
  const response = await fetchWithTimeout(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
    timeout,
  });
  return response.json();
}

/**
 * GET request returning JSON.
 */
export async function getJson<T>(url: string, timeout?: number): Promise<T> {
  const response = await fetchWithTimeout(url, { timeout });
  return response.json();
}

/**
 * PATCH JSON request.
 */
export async function patchJson<T>(
  url: string,
  body: unknown,
  timeout?: number
): Promise<T> {
  const response = await fetchWithTimeout(url, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
    timeout,
  });
  return response.json();
}

/**
 * PUT JSON request.
 */
export async function putJson<T>(
  url: string,
  body: unknown,
  timeout?: number
): Promise<T> {
  const response = await fetchWithTimeout(url, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
    timeout,
  });
  return response.json();
}

/**
 * DELETE request.
 */
export async function deleteJson<T = void>(
  url: string,
  timeout?: number
): Promise<T> {
  const response = await fetchWithTimeout(url, {
    method: 'DELETE',
    timeout,
  });
  
  // Some DELETE endpoints return empty response
  const text = await response.text();
  if (!text) return undefined as T;
  return JSON.parse(text);
}

/**
 * POST FormData request.
 */
export async function postFormData<T>(
  url: string,
  formData: FormData,
  timeout?: number
): Promise<T> {
  const response = await fetchWithTimeout(url, {
    method: 'POST',
    body: formData,
    timeout,
  });
  return response.json();
}

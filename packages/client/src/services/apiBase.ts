/**
 * API Base Configuration
 * ======================
 *
 * Centralized API configuration and utilities.
 * All API services should use this as the foundation.
 *
 * Wave 20: Option C API Restructuring
 * Wave 26: Unified cross-origin support
 */

// Environment-based API URL - supports both env var names for compatibility
export const API_BASE = import.meta.env.VITE_API_BASE
  || import.meta.env.VITE_API_URL
  || (typeof window !== 'undefined' && window.location.hostname === 'localhost' ? 'http://localhost:8000' : '');

/**
 * Resolve a URL path to a full URL with API_BASE prefix.
 * - Absolute URLs (http://, https://, data:) pass through unchanged
 * - Relative URLs (/api/...) get API_BASE prepended
 *
 * @example
 * resolveApiUrl('/api/vision/generate') => 'https://api.example.com/api/vision/generate'
 * resolveApiUrl('https://other.com/path') => 'https://other.com/path'
 */
export function resolveApiUrl(url: string): string {
  if (!url) return url;
  if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('data:')) {
    return url;
  }
  return `${API_BASE}${url.startsWith('/') ? '' : '/'}${url}`;
}

/**
 * Build a full API URL from path segments.
 * Normalizes slashes and handles edge cases.
 */
export function buildUrl(...segments: string[]): string {
  const path = segments
    .map(s => s.replace(/^\/+|\/+$/g, '')) // trim slashes
    .filter(Boolean)
    .join('/');
  return `${API_BASE}/${path}`;
}

// ============================================================================
// DROP-IN FETCH REPLACEMENT
// ============================================================================

/**
 * Drop-in replacement for fetch() that automatically resolves relative URLs.
 *
 * Use this instead of fetch() for API calls:
 *
 * @example
 * // Before (breaks on Railway):
 * const res = await fetch('/api/vision/generate', { method: 'POST', body });
 *
 * // After (works everywhere):
 * import { api } from '@/services/apiBase';
 * const res = await api('/api/vision/generate', { method: 'POST', body });
 *
 * // Or use the JSON helpers:
 * const data = await api.get('/api/machines');
 * const result = await api.post('/api/vision/generate', { prompt: '...' });
 */
export async function api(url: string, options?: RequestInit): Promise<Response> {
  return fetch(resolveApiUrl(url), options);
}

/**
 * GET request with automatic JSON parsing.
 */
api.get = async function<T = unknown>(url: string, options?: RequestInit): Promise<T> {
  const res = await api(url, { ...options, method: 'GET' });
  if (!res.ok) {
    throw new ApiError(res.status, res.statusText, await res.text().catch(() => ''), url);
  }
  return res.json();
};

/**
 * POST request with automatic JSON serialization and parsing.
 */
api.post = async function<T = unknown>(url: string, body?: unknown, options?: RequestInit): Promise<T> {
  const res = await api(url, {
    ...options,
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    throw new ApiError(res.status, res.statusText, await res.text().catch(() => ''), url);
  }
  return res.json();
};

/**
 * PUT request with automatic JSON serialization and parsing.
 */
api.put = async function<T = unknown>(url: string, body?: unknown, options?: RequestInit): Promise<T> {
  const res = await api(url, {
    ...options,
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    throw new ApiError(res.status, res.statusText, await res.text().catch(() => ''), url);
  }
  return res.json();
};

/**
 * DELETE request.
 */
api.delete = async function<T = unknown>(url: string, options?: RequestInit): Promise<T> {
  const res = await api(url, { ...options, method: 'DELETE' });
  if (!res.ok) {
    throw new ApiError(res.status, res.statusText, await res.text().catch(() => ''), url);
  }
  return res.json();
};

/**
 * Resolve an asset URL (for images, downloads, etc).
 * Same as resolveApiUrl but exported with a clearer name for templates.
 */
export const resolveAssetUrl = resolveApiUrl;

/**
 * Standard fetch wrapper with JSON handling and error normalization.
 */
export async function apiFetch<T>(
  url: string,
  options: RequestInit = {}
): Promise<T> {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorBody = await response.text().catch(() => 'Unknown error');
    throw new ApiError(response.status, response.statusText, errorBody, url);
  }

  // Check for deprecation header
  const deprecatedRoute = response.headers.get('X-Deprecated-Route');
  const newRoute = response.headers.get('X-New-Route');
  if (deprecatedRoute === 'true' && newRoute) {
    console.warn(`[API] Deprecated route used: ${url} → Migrate to: ${newRoute}`);
  }

  return response.json();
}

/**
 * Fetch with fallback to legacy endpoint on 404.
 * Use this during migration period.
 */
export async function apiFetchWithFallback<T>(
  canonicalUrl: string,
  legacyUrl: string,
  options: RequestInit = {}
): Promise<T> {
  try {
    return await apiFetch<T>(canonicalUrl, options);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      console.warn(`[API] Canonical endpoint not found, falling back: ${canonicalUrl} → ${legacyUrl}`);
      return apiFetch<T>(legacyUrl, options);
    }
    throw error;
  }
}

/**
 * Custom API error with structured information.
 */
export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public body: string,
    public url: string
  ) {
    super(`API Error ${status}: ${statusText} at ${url}`);
    this.name = 'ApiError';
  }
}

/**
 * Type guard for ApiError.
 */
export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError;
}

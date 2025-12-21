/**
 * API Base Configuration
 * ======================
 * 
 * Centralized API configuration and utilities.
 * All API services should use this as the foundation.
 * 
 * Wave 20: Option C API Restructuring
 */

// Environment-based API URL
export const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

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

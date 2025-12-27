/**
 * SDK Error Types
 *
 * Structured error class for API failures with status, URL, and response details.
 */

export class ApiError extends Error {
  status: number;
  url: string;
  details?: unknown;
  requestId?: string;

  constructor(
    message: string,
    opts: { status: number; url: string; details?: unknown; requestId?: string }
  ) {
    super(message);
    this.name = "ApiError";
    this.status = opts.status;
    this.url = opts.url;
    this.details = opts.details;
    this.requestId = opts.requestId;
  }

  /** Check if error is a specific HTTP status */
  is(status: number): boolean {
    return this.status === status;
  }

  /** Check if error is a client error (4xx) */
  isClientError(): boolean {
    return this.status >= 400 && this.status < 500;
  }

  /** Check if error is a server error (5xx) */
  isServerError(): boolean {
    return this.status >= 500;
  }

  /** Extract error code from details if present */
  getErrorCode(): string | undefined {
    if (
      this.details &&
      typeof this.details === "object" &&
      "error" in this.details
    ) {
      return String((this.details as Record<string, unknown>).error);
    }
    return undefined;
  }
}

/**
 * Frontend-safe error string normalizer (H8.3.2).
 * - Always returns a string suitable for UI display
 * - Includes request-id when available for correlation
 * - Handles ApiError, Error, and unknown types gracefully
 *
 * @example
 * ```ts
 * try {
 *   await sdk.cam.roughingGcode(payload);
 * } catch (e) {
 *   errorMessage.value = formatApiErrorForUi(e);
 * }
 * ```
 */
export function formatApiErrorForUi(err: unknown): string {
  if (err instanceof ApiError) {
    const rid = err.requestId ? ` (request-id: ${err.requestId})` : "";
    return `${err.message}${rid}`;
  }
  if (err instanceof Error) return err.message;
  try {
    return JSON.stringify(err);
  } catch {
    return String(err);
  }
}

/**
 * SDK Error Types
 *
 * Structured error class for API failures with status, URL, and response details.
 */

export class ApiError extends Error {
  status: number;
  url: string;
  details?: unknown;

  constructor(
    message: string,
    opts: { status: number; url: string; details?: unknown }
  ) {
    super(message);
    this.name = "ApiError";
    this.status = opts.status;
    this.url = opts.url;
    this.details = opts.details;
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

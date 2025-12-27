// Frontend-safe SDK transport wrapper
// H8.2.1: SDK skeleton + request wrapper + strict request-id check

export type SdkStrictMode = "off" | "warn" | "error";

export type SdkRequestOptions = {
  /**
   * Base URL prefix for API requests.
   * Default: "" (same-origin)
   */
  baseUrl?: string;

  /**
   * Optional client-supplied request id.
   * If omitted, one will be generated.
   */
  requestId?: string;

  /**
   * Strict enforcement of request-id echo header on responses.
   *
   * - "off": do nothing
   * - "warn": console.warn if missing
   * - "error": throw if missing
   *
   * Default: "warn"
   */
  strictRequestId?: SdkStrictMode;

  /**
   * Optional observer hook for telemetry / debugging.
   */
  onEvent?: (evt: SdkTransportEvent) => void;
};

export type SdkTransportEvent =
  | {
      kind: "request";
      requestId: string;
      url: string;
      method: string;
    }
  | {
      kind: "response";
      requestId: string;
      url: string;
      method: string;
      status: number;
      hasRequestIdHeader: boolean;
    }
  | {
      kind: "error";
      requestId: string;
      url: string;
      method: string;
      message: string;
    };

/**
 * Generate a short client-side request id.
 * Server will echo this back via RequestIdMiddleware.
 */
export function generateRequestId(prefix = "sdk_req_"): string {
  try {
    const raw = crypto.randomUUID().replace(/-/g, "").slice(0, 12);
    return `${prefix}${raw}`;
  } catch {
    const raw = Math.random().toString(16).slice(2, 14);
    return `${prefix}${raw}`;
  }
}

/**
 * Enforce presence of X-Request-Id on responses.
 */
export function assertRequestIdHeader(
  response: Response,
  opts: {
    strict: SdkStrictMode;
    requestId: string;
    url: string;
    method: string;
  }
): void {
  const headerVal =
    response.headers.get("x-request-id") ||
    response.headers.get("X-Request-Id");

  if (headerVal) return;

  const msg = `[SDK] Missing X-Request-Id response header (${opts.method} ${opts.url}) for requestId=${opts.requestId}`;

  if (opts.strict === "off") return;
  if (opts.strict === "warn") {
    // eslint-disable-next-line no-console
    console.warn(msg);
    return;
  }
  throw new Error(msg);
}

/**
 * Core SDK request wrapper.
 *
 * This is the ONLY place fetch() should be called by SDK consumers.
 */
export async function sdkRequest(
  path: string,
  init: RequestInit,
  opts: SdkRequestOptions = {}
): Promise<Response> {
  const baseUrl = opts.baseUrl ?? "";
  const url = `${baseUrl}${path}`;

  const method = (init.method || "GET").toUpperCase();
  const requestId = opts.requestId ?? generateRequestId();
  const strict = opts.strictRequestId ?? "warn";

  const headers = new Headers(init.headers || {});
  headers.set("X-Request-Id", requestId);

  opts.onEvent?.({
    kind: "request",
    requestId,
    url,
    method,
  });

  let response: Response;
  try {
    response = await fetch(url, {
      ...init,
      headers,
    });
  } catch (err: any) {
    opts.onEvent?.({
      kind: "error",
      requestId,
      url,
      method,
      message: String(err),
    });
    throw err;
  }

  const hasRequestIdHeader = Boolean(
    response.headers.get("x-request-id") ||
      response.headers.get("X-Request-Id")
  );

  opts.onEvent?.({
    kind: "response",
    requestId,
    url,
    method,
    status: response.status,
    hasRequestIdHeader,
  });

  assertRequestIdHeader(response, {
    strict,
    requestId,
    url,
    method,
  });

  return response;
}

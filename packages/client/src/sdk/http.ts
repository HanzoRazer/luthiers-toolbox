// Frontend-safe SDK transport wrapper
// H8.2.1: SDK skeleton + request wrapper + strict request-id check + error normalization

import { SdkHttpError, type StrictRequestIdMode } from "./errors";

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
  strictRequestId?: StrictRequestIdMode;

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
 * Core SDK request wrapper.
 *
 * This is the ONLY place fetch() should be called by SDK consumers.
 * Throws SdkHttpError on failures with consistent request-id correlation.
 */
export async function sdkRequest(
  path: string,
  init: RequestInit = {},
  opts: SdkRequestOptions = {}
): Promise<Response> {
  const baseUrl = opts.baseUrl ?? "";
  const url = `${baseUrl}${path}`;

  const method = (init.method || "GET").toUpperCase();
  const strict = opts.strictRequestId ?? "warn";

  // Ensure we have a Headers object we can mutate
  const headers = new Headers(init.headers || {});
  let outgoingReqId = headers.get("x-request-id") || headers.get("X-Request-Id");
  if (!outgoingReqId) {
    outgoingReqId = opts.requestId ?? generateRequestId();
    headers.set("X-Request-Id", outgoingReqId);
  }

  opts.onEvent?.({
    kind: "request",
    requestId: outgoingReqId,
    url,
    method,
  });

  let resp: Response;
  try {
    resp = await fetch(url, { ...init, headers });
  } catch (e) {
    // Network failure: no response, but we still have outgoing request id
    opts.onEvent?.({
      kind: "error",
      requestId: outgoingReqId,
      url,
      method,
      message: String(e),
    });
    throw new SdkHttpError({
      kind: "network",
      message: `Network error calling ${method} ${url}.`,
      url,
      method,
      requestId: outgoingReqId,
      details: e instanceof Error ? e.message : e,
    });
  }

  // Request-id echo enforcement (enterprise-safe)
  const echoedReqId = resp.headers.get("x-request-id") || resp.headers.get("X-Request-Id") || undefined;

  const hasRequestIdHeader = Boolean(echoedReqId);

  opts.onEvent?.({
    kind: "response",
    requestId: echoedReqId || outgoingReqId,
    url,
    method,
    status: resp.status,
    hasRequestIdHeader,
  });

  if (!echoedReqId) {
    const msg = `Missing X-Request-Id in response for ${method} ${url}.`;
    if (strict === "error") {
      throw new SdkHttpError({
        kind: "http",
        message: msg,
        status: resp.status,
        url,
        method,
        requestId: outgoingReqId,
      });
    } else if (strict === "warn") {
      // eslint-disable-next-line no-console
      console.warn(msg, { url, method, requestId: outgoingReqId });
    }
  }

  if (!resp.ok) {
    // Best-effort parse for details; keep UI-safe message
    const contentType = resp.headers.get("content-type") || "";
    let bodyText: string | undefined;
    let bodyJson: any = undefined;

    try {
      if (contentType.includes("application/json")) {
        bodyJson = await resp.clone().json();
      } else {
        bodyText = await resp.clone().text();
      }
    } catch {
      // ignore parse errors, keep minimal
    }

    const requestId = echoedReqId ?? outgoingReqId;

    // UI-safe message with incident correlation
    const base = `Request failed (${resp.status}) for ${method} ${url}.`;
    const hint =
      bodyJson?.detail
        ? String(bodyJson.detail)
        : bodyJson?.message
          ? String(bodyJson.message)
          : bodyText && bodyText.trim()
            ? bodyText.trim().slice(0, 240)
            : undefined;

    const message = hint ? `${base} ${hint}` : base;

    throw new SdkHttpError({
      kind: "http",
      message,
      status: resp.status,
      url,
      method,
      requestId,
      details: bodyJson ?? bodyText,
    });
  }

  return resp;
}

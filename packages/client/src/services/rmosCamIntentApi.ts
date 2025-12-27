/* eslint-disable @typescript-eslint/no-explicit-any */

/**
 * RMOS CAM Intent SDK surface (frontend-safe).
 *
 * Canonical endpoint:
 *   POST /api/rmos/cam/intent/normalize
 *
 * Contract:
 *   request:  { intent: CamIntentV1, normalize_to_units?: "mm"|"inch", strict?: boolean }
 *   response: { intent: CamIntentV1, issues: CamIntentIssue[], normalized_at_utc: string }
 *
 * Notes:
 *  - This module is "frontend-safe": no Node-only APIs, no process.env access.
 *  - You can use `strict: true` to make server reject non-normalizable intents (422).
 */

export type CamModeV1 = "router_3axis" | "saw";
export type CamUnitsV1 = "mm" | "inch";

export type CamIntentIssueSeverity = "INFO" | "WARN" | "ERROR";

export interface CamIntentIssue {
  code: string;
  message: string;
  severity: CamIntentIssueSeverity;
  path?: string;
  hint?: string;
}

export interface CamIntentV1 {
  mode: CamModeV1;
  units?: CamUnitsV1;

  tool_id?: string | null;
  material_id?: string | null;
  machine_id?: string | null;

  design?: Record<string, any>;
  context?: Record<string, any>;
  options?: Record<string, any>;

  requested_by?: string | null;
  created_at_utc?: string | null;
}

export interface NormalizeCamIntentRequest {
  intent: CamIntentV1;
  normalize_to_units?: CamUnitsV1;
  strict?: boolean;
}

export interface NormalizeCamIntentResponse {
  intent: CamIntentV1;
  issues: CamIntentIssue[];
  normalized_at_utc: string;
}

export type NormalizeCamIntentResult = Pick<NormalizeCamIntentResponse, "intent" | "issues">;

export class RmosApiError extends Error {
  status: number;
  detail: any;
  constructor(message: string, status: number, detail: any) {
    super(message);
    this.name = "RmosApiError";
    this.status = status;
    this.detail = detail;
  }
}

function getApiBaseUrl(): string {
  // Vite: import.meta.env is available in the browser build.
  // Fallback keeps local dev simple.
  const v = (import.meta as any)?.env?.VITE_API_URL;
  return typeof v === "string" && v.length > 0 ? v : "http://localhost:8000/api";
}

function pickRequestIdHeader(): Record<string, string> {
  // Best-effort: if caller wants to supply a request-id, they can pass it explicitly.
  // We DO NOT auto-generate here (keep SDK deterministic and testable).
  return {};
}

/**
 * normalizeCamIntent()
 *
 * Calls RMOS endpoint and returns { intent, issues } for the caller to standardize on.
 *
 * Usage:
 *   const { intent, issues } = await normalizeCamIntent({ intent, strict: false })
 *
 * Strict mode:
 *   strict=true => server may respond 422 with detail {message, issues}
 */
export async function normalizeCamIntent(
  req: NormalizeCamIntentRequest,
  opts?: { apiBaseUrl?: string; requestId?: string }
): Promise<NormalizeCamIntentResult> {
  const apiBaseUrl = opts?.apiBaseUrl ?? getApiBaseUrl();

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...pickRequestIdHeader(),
  };
  if (opts?.requestId) headers["X-Request-Id"] = opts.requestId;

  const r = await fetch(`${apiBaseUrl}/rmos/cam/intent/normalize`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      intent: req.intent,
      normalize_to_units: req.normalize_to_units ?? "mm",
      strict: req.strict ?? false,
    }),
  });

  // Common success path
  if (r.ok) {
    const data = (await r.json()) as NormalizeCamIntentResponse;
    return { intent: data.intent, issues: data.issues ?? [] };
  }

  // Error path: normalize server error into a stable shape
  let detail: any = null;
  try {
    detail = await r.json();
  } catch {
    // ignore
  }

  const msg =
    (detail && detail.detail && (detail.detail.message || detail.detail.error)) ||
    (detail && (detail.message || detail.error)) ||
    `RMOS normalizeCamIntent failed (${r.status})`;

  throw new RmosApiError(String(msg), r.status, detail);
}

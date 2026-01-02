/**
 * RMOS Operations Client
 *
 * Type-safe client for /api/rmos/operations endpoints (Operation Lane).
 *
 * Bundle 05: Frontend SDK wiring for RMOS Operation Lane
 * Reference: docs/OPERATION_EXECUTION_GOVERNANCE_v1.md
 */

import { get, post } from "../core/apiFetch";
import type { ApiFetchOptions } from "../core/types";
import type { RunArtifact } from "./runs";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/** CAM Intent V1 envelope - kept flexible during CAM migration */
export type CamIntentV1 = Record<string, unknown>;

/** Feasibility result from server */
export type FeasibilityResult = {
  risk_level?: "GREEN" | "YELLOW" | "RED" | "UNKNOWN" | string;
  risk?: string;
  score?: number;
  warnings?: string[];
  block_reason?: string | null;
  details?: Record<string, unknown>;
};

/** Execute request payload */
export type ExecuteOperationRequest = {
  cam_intent_v1: CamIntentV1;
  feasibility: FeasibilityResult;
  parent_plan_run_id?: string;
  meta?: Record<string, unknown>;
};

/** Execute response */
export type ExecuteOperationResponse = {
  run_id: string;
  status: string;
  risk_level: string;
  event_type: string;
  block_reason?: string | null;
  gcode_sha256?: string | null;
  warnings?: string[];
};

/** Plan request payload */
export type PlanOperationRequest = {
  cam_intent_v1: CamIntentV1;
  feasibility?: FeasibilityResult;
  meta?: Record<string, unknown>;
};

/** Plan response */
export type PlanOperationResponse = {
  run_id: string;
  status: string;
  risk_level?: string | null;
  event_type: string;
  plan?: Record<string, unknown>;
  warnings?: string[];
};

// ---------------------------------------------------------------------------
// API Functions - Generic
// ---------------------------------------------------------------------------

/**
 * Execute an operation for a specific tool.
 *
 * @param toolId - Tool identifier (e.g., 'saw_v1', 'cam_roughing_v1')
 * @param request - Execute request payload
 * @param opts - SDK options
 * @returns Execution result (or 409 Conflict if blocked)
 */
export async function executeOperation(
  toolId: string,
  request: ExecuteOperationRequest,
  opts?: ApiFetchOptions
): Promise<ExecuteOperationResponse> {
  return post<ExecuteOperationResponse>(
    `/rmos/operations/${encodeURIComponent(toolId)}/execute`,
    request,
    opts
  );
}

/**
 * Create an operation plan for a specific tool.
 *
 * @param toolId - Tool identifier
 * @param request - Plan request payload
 * @param opts - SDK options
 */
export async function planOperation(
  toolId: string,
  request: PlanOperationRequest,
  opts?: ApiFetchOptions
): Promise<PlanOperationResponse> {
  return post<PlanOperationResponse>(
    `/rmos/operations/${encodeURIComponent(toolId)}/plan`,
    request,
    opts
  );
}

/**
 * Export a run as a ZIP file.
 * Returns a Blob that can be downloaded.
 *
 * @param runId - Run ID to export
 * @param opts - SDK options (baseUrl, requestId)
 */
export async function exportOperationZip(
  runId: string,
  opts: ApiFetchOptions = {}
): Promise<{ blob: Blob; filename: string; requestId: string }> {
  const baseUrl = opts.baseUrl ?? "/api";
  const url = `${baseUrl}/rmos/operations/${encodeURIComponent(runId)}/export.zip`;

  const headers: Record<string, string> = {
    ...(opts.headers ?? {}),
  };

  // Generate or use provided request ID
  const requestId =
    opts.requestId ?? `req_${Date.now()}_${Math.random().toString(16).slice(2)}`;
  headers["X-Request-Id"] = requestId;

  const res = await fetch(url, {
    method: "GET",
    headers,
    signal: opts.signal,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Export failed (${res.status}): ${text}`);
  }

  const blob = await res.blob();

  // Extract filename from Content-Disposition
  const cd = res.headers.get("Content-Disposition") ?? "";
  const match = cd.match(/filename="([^"]+)"/i);
  const filename = match?.[1] ?? `${runId}.zip`;

  const echoedRequestId = res.headers.get("X-Request-Id") ?? requestId;

  return { blob, filename, requestId: echoedRequestId };
}

/**
 * Download export ZIP directly to browser.
 *
 * @param runId - Run ID to export
 * @param opts - SDK options
 */
export async function downloadExportZip(
  runId: string,
  opts?: ApiFetchOptions
): Promise<{ requestId: string }> {
  const { blob, filename, requestId } = await exportOperationZip(runId, opts);

  // Trigger download via anchor element
  const objUrl = URL.createObjectURL(blob);
  try {
    const a = document.createElement("a");
    a.href = objUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
  } finally {
    URL.revokeObjectURL(objUrl);
  }

  return { requestId };
}

// ---------------------------------------------------------------------------
// API Functions - Saw V1 (Bundle 02)
// ---------------------------------------------------------------------------

/**
 * Execute a saw operation (saw_v1).
 */
export async function executeSawV1(
  request: ExecuteOperationRequest,
  opts?: ApiFetchOptions
): Promise<ExecuteOperationResponse> {
  return executeOperation("saw_v1", request, opts);
}

/**
 * Create a saw operation plan (saw_v1).
 */
export async function planSawV1(
  request: PlanOperationRequest,
  opts?: ApiFetchOptions
): Promise<PlanOperationResponse> {
  return planOperation("saw_v1", request, opts);
}

// ---------------------------------------------------------------------------
// API Functions - CAM Roughing V1 (Bundle 03)
// ---------------------------------------------------------------------------

/**
 * Execute/promote a CAM roughing operation (cam_roughing_v1).
 */
export async function executeCamRoughingV1(
  request: ExecuteOperationRequest,
  opts?: ApiFetchOptions
): Promise<ExecuteOperationResponse> {
  return executeOperation("cam_roughing_v1", request, opts);
}

/**
 * Create a CAM roughing operation plan (cam_roughing_v1).
 */
export async function planCamRoughingV1(
  request: PlanOperationRequest,
  opts?: ApiFetchOptions
): Promise<PlanOperationResponse> {
  return planOperation("cam_roughing_v1", request, opts);
}

// ---------------------------------------------------------------------------
// Convenience Object (for namespace-style imports)
// ---------------------------------------------------------------------------

export const rmosOperations = {
  execute: executeOperation,
  plan: planOperation,
  exportZip: exportOperationZip,
  downloadZip: downloadExportZip,

  // Saw v1
  executeSawV1,
  planSawV1,

  // CAM Roughing v1
  executeCamRoughingV1,
  planCamRoughingV1,
};

/**
 * RMOS Workflow Client
 *
 * Type-safe client for /api/rmos/workflow endpoints.
 * Canonical workflow session lifecycle management.
 */

import { get, post } from "../core/apiFetch";
import type { ApiFetchOptions } from "../core/types";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type WorkflowMode = "DESIGN_FIRST" | "CONTEXT_FIRST" | "PARALLEL";

export type WorkflowState =
  | "DRAFT"
  | "CONTEXT_READY"
  | "FEASIBILITY_REQUESTED"
  | "FEASIBILITY_READY"
  | "APPROVED"
  | "REJECTED"
  | "DESIGN_REVISION_REQUIRED"
  | "TOOLPATHS_REQUESTED"
  | "TOOLPATHS_READY"
  | "ARCHIVED";

export type ActorRole = "USER" | "OPERATOR" | "ADMIN" | "SYSTEM";

export type RiskBucket = "GREEN" | "YELLOW" | "RED" | "UNKNOWN";

/** Session state for list views */
export type WorkflowSessionLite = {
  session_id: string;
  mode: WorkflowMode;
  state: WorkflowState;
  events_count: number;
  feasibility_artifact_id?: string | null;
  toolpaths_artifact_id?: string | null;
};

/** Full session state response */
export type WorkflowSessionState = WorkflowSessionLite & {
  next_step: string;
  last_feasibility_artifact_id?: string | null;
  last_toolpaths_artifact_id?: string | null;
};

/** Session event for audit log */
export type WorkflowEvent = {
  ts_utc: string;
  actor: ActorRole;
  action: string;
  from_state: WorkflowState;
  to_state: WorkflowState;
  summary?: string;
  details?: Record<string, unknown>;
};

/** Transition response */
export type TransitionResponse = {
  session_id: string;
  state: WorkflowState;
  previous_state: WorkflowState;
  next_step: string;
  run_artifact_id?: string | null;
};

/** Approval response */
export type ApproveResponse = {
  session_id: string;
  state: WorkflowState;
  approved: boolean;
  message: string;
  run_artifact_id?: string | null;
};

/** Generator metadata */
export type GeneratorInfo = {
  key: string;
  name: string;
  description: string;
  category: string;
  version: string;
};

/** Snapshot save response */
export type SaveSnapshotResponse = {
  session_id: string;
  snapshot_id: string;
  name: string;
  created_at: string;
};

// ---------------------------------------------------------------------------
// Request Types
// ---------------------------------------------------------------------------

export type CreateSessionRequest = {
  mode?: WorkflowMode;
  tool_id?: string;
  material_id?: string;
  machine_id?: string;
};

export type SetDesignRequest = {
  session_id: string;
  design: Record<string, unknown>;
};

export type SetContextRequest = {
  session_id: string;
  context: Record<string, unknown>;
};

export type StoreFeasibilityRequest = {
  session_id: string;
  score: number;
  risk_bucket: RiskBucket;
  warnings?: string[];
  meta?: Record<string, unknown>;
};

export type ApproveRequest = {
  session_id: string;
  actor?: ActorRole;
  note?: string;
};

export type RejectRequest = {
  session_id: string;
  actor?: ActorRole;
  reason: string;
};

export type StoreToolpathsRequest = {
  session_id: string;
  plan_id: string;
  toolpaths_data?: Record<string, unknown>;
  gcode_text?: string;
  meta?: Record<string, unknown>;
};

export type RevisionRequest = {
  session_id: string;
  actor?: ActorRole;
  reason: string;
};

export type SaveSnapshotRequest = {
  name?: string;
  tags?: string[];
};

// ---------------------------------------------------------------------------
// API Functions
// ---------------------------------------------------------------------------

/**
 * List all workflow sessions.
 */
export async function listSessions(
  params: { limit?: number; state?: WorkflowState } = {},
  opts?: ApiFetchOptions
): Promise<{ sessions: WorkflowSessionLite[]; total: number }> {
  const qs = new URLSearchParams();
  if (params.limit) qs.set("limit", String(params.limit));
  if (params.state) qs.set("state", params.state);
  const q = qs.toString();
  return get<{ sessions: WorkflowSessionLite[]; total: number }>(
    `/rmos/workflow/sessions${q ? `?${q}` : ""}`,
    opts
  );
}

/**
 * Get a single session by ID.
 */
export async function getSession(
  sessionId: string,
  opts?: ApiFetchOptions
): Promise<WorkflowSessionState> {
  return get<WorkflowSessionState>(
    `/rmos/workflow/sessions/${encodeURIComponent(sessionId)}`,
    opts
  );
}

/**
 * Get session snapshot (diff-viewer compatible).
 */
export async function getSessionSnapshot(
  sessionId: string,
  opts?: ApiFetchOptions
): Promise<Record<string, unknown>> {
  return get<Record<string, unknown>>(
    `/rmos/workflow/sessions/${encodeURIComponent(sessionId)}/snapshot`,
    opts
  );
}

/**
 * Get session event audit log.
 */
export async function getSessionEvents(
  sessionId: string,
  opts?: ApiFetchOptions
): Promise<{ session_id: string; events: WorkflowEvent[] }> {
  return get<{ session_id: string; events: WorkflowEvent[] }>(
    `/rmos/workflow/sessions/${encodeURIComponent(sessionId)}/events`,
    opts
  );
}

/**
 * Create a new workflow session.
 */
export async function createSession(
  request: CreateSessionRequest = {},
  opts?: ApiFetchOptions
): Promise<{ session_id: string; mode: string; state: string; next_step: string }> {
  return post<{ session_id: string; mode: string; state: string; next_step: string }>(
    "/rmos/workflow/sessions",
    request,
    opts
  );
}

/**
 * Set design parameters for a session.
 */
export async function setDesign(
  sessionId: string,
  design: Record<string, unknown>,
  opts?: ApiFetchOptions
): Promise<TransitionResponse> {
  return post<TransitionResponse>(
    `/rmos/workflow/sessions/${encodeURIComponent(sessionId)}/design`,
    { session_id: sessionId, design },
    opts
  );
}

/**
 * Set context for a session.
 */
export async function setContext(
  sessionId: string,
  context: Record<string, unknown>,
  opts?: ApiFetchOptions
): Promise<TransitionResponse> {
  return post<TransitionResponse>(
    `/rmos/workflow/sessions/${encodeURIComponent(sessionId)}/context`,
    { session_id: sessionId, context },
    opts
  );
}

/**
 * Request feasibility evaluation.
 */
export async function requestFeasibility(
  sessionId: string,
  opts?: ApiFetchOptions
): Promise<TransitionResponse> {
  return post<TransitionResponse>(
    `/rmos/workflow/sessions/${encodeURIComponent(sessionId)}/feasibility/request`,
    {},
    opts
  );
}

/**
 * Store feasibility result.
 */
export async function storeFeasibility(
  sessionId: string,
  result: Omit<StoreFeasibilityRequest, "session_id">,
  opts?: ApiFetchOptions
): Promise<TransitionResponse> {
  return post<TransitionResponse>(
    `/rmos/workflow/sessions/${encodeURIComponent(sessionId)}/feasibility/store`,
    { session_id: sessionId, ...result },
    opts
  );
}

/**
 * Approve a session for toolpath generation.
 */
export async function approve(
  request: ApproveRequest,
  opts?: ApiFetchOptions
): Promise<ApproveResponse> {
  return post<ApproveResponse>("/rmos/workflow/approve", request, opts);
}

/**
 * Reject a session.
 */
export async function reject(
  request: RejectRequest,
  opts?: ApiFetchOptions
): Promise<TransitionResponse> {
  return post<TransitionResponse>("/rmos/workflow/reject", request, opts);
}

/**
 * Request toolpath generation.
 */
export async function requestToolpaths(
  sessionId: string,
  opts?: ApiFetchOptions
): Promise<TransitionResponse> {
  return post<TransitionResponse>(
    `/rmos/workflow/sessions/${encodeURIComponent(sessionId)}/toolpaths/request`,
    {},
    opts
  );
}

/**
 * Store generated toolpaths.
 */
export async function storeToolpaths(
  sessionId: string,
  data: Omit<StoreToolpathsRequest, "session_id">,
  opts?: ApiFetchOptions
): Promise<TransitionResponse> {
  return post<TransitionResponse>(
    `/rmos/workflow/sessions/${encodeURIComponent(sessionId)}/toolpaths/store`,
    { session_id: sessionId, ...data },
    opts
  );
}

/**
 * Require design revision.
 */
export async function requireRevision(
  sessionId: string,
  reason: string,
  actor?: ActorRole,
  opts?: ApiFetchOptions
): Promise<TransitionResponse> {
  return post<TransitionResponse>(
    `/rmos/workflow/sessions/${encodeURIComponent(sessionId)}/revision`,
    { session_id: sessionId, reason, actor },
    opts
  );
}

/**
 * Archive a session.
 */
export async function archive(
  sessionId: string,
  note?: string,
  opts?: ApiFetchOptions
): Promise<TransitionResponse> {
  return post<TransitionResponse>(
    `/rmos/workflow/sessions/${encodeURIComponent(sessionId)}/archive`,
    { note },
    opts
  );
}

/**
 * Save session state as a named snapshot.
 */
export async function saveSnapshot(
  sessionId: string,
  request: SaveSnapshotRequest = {},
  opts?: ApiFetchOptions
): Promise<SaveSnapshotResponse> {
  return post<SaveSnapshotResponse>(
    `/rmos/workflow/sessions/${encodeURIComponent(sessionId)}/save-snapshot`,
    request,
    opts
  );
}

/**
 * List available workflow generators.
 */
export async function listGenerators(
  opts?: ApiFetchOptions
): Promise<{ generators: GeneratorInfo[]; count: number }> {
  return get<{ generators: GeneratorInfo[]; count: number }>(
    "/rmos/workflow/generators",
    opts
  );
}

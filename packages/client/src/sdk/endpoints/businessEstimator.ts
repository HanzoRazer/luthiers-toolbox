// packages/client/src/sdk/endpoints/businessEstimator.ts
/**
 * Business Estimator SDK - API client for cost estimation endpoints.
 */
import { get, post, patch, del } from "../core/apiFetch";
import type {
  EstimateRequest,
  EstimateResult,
  ComplexityFactors,
  LearningCurveProjection,
} from "@/types/businessEstimator";

// ============================================================================
// TYPES
// ============================================================================

export interface EstimateResponse {
  ok: boolean;
  estimate: EstimateResult;
}

export interface Goal {
  id: string;
  created_at: string;
  updated_at: string;
  name: string;
  instrument_type: string;
  target_cost: number;
  target_hours: number;
  current_best_cost: number | null;
  current_best_hours: number | null;
  progress_pct: number;
  status: "active" | "achieved" | "archived";
  deadline: string | null;
  notes: string | null;
  estimate_ids: string[];
}

export interface GoalResponse {
  ok: boolean;
  goal: Goal;
}

export interface GoalListResponse {
  ok: boolean;
  goals: Goal[];
  total: number;
}

export interface GoalCreateRequest {
  name: string;
  instrument_type: string;
  target_cost: number;
  target_hours: number;
  deadline?: string;
  notes?: string;
}

export interface GoalUpdateRequest {
  name?: string;
  target_cost?: number;
  target_hours?: number;
  status?: "active" | "achieved" | "archived";
  deadline?: string;
  notes?: string;
}

export interface LearningCurveRequest {
  first_unit_hours: number;
  quantity: number;
  learning_rate: number;
  hourly_rate: number;
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

export function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

const GROUP_COLORS: Record<string, string> = {
  body: "#4080f0",
  neck: "#40c080",
  finish: "#f0a040",
  assembly: "#c060a0",
  setup: "#8060c0",
  default: "#506090",
};

export function getGroupColor(taskId: string): string {
  if (taskId.includes("body") || taskId.includes("sides")) return GROUP_COLORS.body;
  if (taskId.includes("neck") || taskId.includes("fretboard")) return GROUP_COLORS.neck;
  if (taskId.includes("finish")) return GROUP_COLORS.finish;
  if (taskId.includes("assembly") || taskId.includes("attach")) return GROUP_COLORS.assembly;
  if (taskId.includes("setup") || taskId.includes("qc")) return GROUP_COLORS.setup;
  return GROUP_COLORS.default;
}

// ============================================================================
// ESTIMATE ENDPOINTS
// ============================================================================

export async function createEstimate(request: EstimateRequest): Promise<EstimateResult> {
  const response = await post<EstimateResponse>(
    "/business/estimate/parametric",
    request
  );
  return response.estimate;
}

export async function getComplexityFactors(): Promise<ComplexityFactors> {
  return get<ComplexityFactors>("/business/estimate/factors");
}

export async function getLearningCurveProjection(
  request: LearningCurveRequest
): Promise<LearningCurveProjection> {
  return post<LearningCurveProjection>(
    "/business/estimate/learning-curve",
    request
  );
}

// ============================================================================
// GOAL ENDPOINTS
// ============================================================================

export async function listGoals(): Promise<GoalListResponse> {
  return get<GoalListResponse>("/business/goals");
}

export async function createGoal(request: GoalCreateRequest): Promise<GoalResponse> {
  return post<GoalResponse>("/business/goals", request);
}

export async function getGoal(goalId: string): Promise<GoalResponse> {
  return get<GoalResponse>("/business/goals/" + goalId);
}

export async function updateGoal(
  goalId: string,
  request: GoalUpdateRequest
): Promise<GoalResponse> {
  return patch<GoalResponse>("/business/goals/" + goalId, request);
}

export async function deleteGoal(goalId: string): Promise<void> {
  await del<void>("/business/goals/" + goalId);
}

export async function linkEstimateToGoal(
  goalId: string,
  estimateId: string
): Promise<GoalResponse> {
  return post<GoalResponse>(
    "/business/goals/" + goalId + "/link-estimate/" + estimateId
  );
}

// packages/client/src/types/rmos.ts
/**
 * RMOS 2.0 TypeScript types.
 *
 * Types for Directional Workflow, Feasibility, and Logging APIs.
 */

// ============================================================
// Risk & Feasibility
// ============================================================

export type RiskBucket = "GREEN" | "YELLOW" | "RED";

export type DirectionalMode =
  | "design_first"
  | "constraint_first"
  | "ai_assisted";

export interface RosetteRingParam {
  ring_index: number;
  width_mm: number;
  tile_length_mm?: number | null;
}

export interface RosetteParamSpec {
  outer_diameter_mm: number;
  inner_diameter_mm: number;
  ring_params: RosetteRingParam[];
  depth_mm?: number;
}

export interface RmosContextSnapshot {
  material_id?: string | null;
  tool_id?: string | null;
  machine_profile_id?: string | null;
  risk_tolerance?: RiskBucket | null;
  max_cut_time_min?: number | null;
  waste_tolerance?: number | null;
}

export interface FeasibilityResult {
  score: number;
  risk_bucket: RiskBucket;
  efficiency: number;
  estimated_cut_time_seconds: number;
  warnings: string[];
}

// ============================================================
// Mode Preview API
// ============================================================

export interface ModeConstraints {
  mode: DirectionalMode;
  hard_limits: Record<string, number>;
  soft_limits: Record<string, number>;
  suggestions: string[];
}

export interface ModePreviewRequest {
  mode: DirectionalMode;
  tool_id?: string;
  material_id?: string;
  machine_profile?: string;
  goal_speed?: number;
  goal_quality?: number;
  goal_tool_life?: number;
}

export interface ModePreviewResponse {
  mode: DirectionalMode;
  constraints: ModeConstraints;
  feasibility_score: number | null;
  risk_level: RiskBucket | null;
  warnings: string[];
  recommendations: string[];
}

export interface ModeInfo {
  id: string;
  name: string;
  description: string;
  best_for: string[];
}

export interface ModesListResponse {
  modes: ModeInfo[];
  default_mode: string;
}

// ============================================================
// Constraint Search API
// ============================================================

export interface ConstraintSearchRequest {
  material_id: string;
  tool_id: string;
  outer_diameter_mm_min: number;
  outer_diameter_mm_max: number;
  ring_count_min?: number;
  ring_count_max?: number;
  max_candidates?: number;
  max_trials?: number;
  max_cut_time_min?: number | null;
  waste_tolerance?: number | null;
}

export interface FeasibilitySnapshot {
  score: number;
  risk_bucket: RiskBucket;
  efficiency: number;
  estimated_cut_time_seconds: number;
  warnings: string[];
}

export interface ConstraintSearchCandidate {
  rank: number;
  design: RosetteParamSpec;
  feasibility: FeasibilitySnapshot;
}

export interface ConstraintSearchResponse {
  candidates: ConstraintSearchCandidate[];
  total_trials: number;
  total_passed: number;
}

// ============================================================
// RMOS Logs API
// ============================================================

export interface RosetteDesignSnapshot {
  outer_diameter_mm: number;
  inner_diameter_mm: number;
  ring_count: number;
  ring_params: RosetteRingParam[];
  depth_mm?: number;
}

export interface RmosLogEntry {
  id: number;
  timestamp: string; // ISO string
  source: string;
  mode: string | null;

  // Full design snapshot (for jump-to-design)
  design: RosetteDesignSnapshot;

  design_outer_diameter_mm: number;
  design_inner_diameter_mm: number;
  ring_count: number;

  overall_score: number;
  risk_bucket: RiskBucket;
  estimated_cut_time_min: number;
  material_efficiency: number;

  material_id?: string | null;
  tool_id?: string | null;
  machine_profile_id?: string | null;

  warnings: string[];
}

export interface RmosLogListResponse {
  entries: RmosLogEntry[];
  total: number;
}

export interface RmosLogFilter {
  limit?: number;
  source?: string;
  mode?: string;
  riskBucket?: RiskBucket;
}

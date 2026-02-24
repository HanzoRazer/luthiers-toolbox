// packages/client/src/types/businessEstimator.ts
/**
 * Business Engineering Estimator Types
 *
 * Types for the parametric cost estimation API.
 * Pro feature - requires license.
 */

// ============================================================================
// ENUMS (mirror backend schemas)
// ============================================================================

export type InstrumentType =
  | "acoustic_dreadnought"
  | "acoustic_om"
  | "acoustic_parlor"
  | "classical"
  | "electric_solid"
  | "electric_hollow"
  | "electric_semi_hollow"
  | "bass_4"
  | "bass_5"
  | "ukulele";

export type BuilderExperience =
  | "beginner"
  | "intermediate"
  | "experienced"
  | "master";

export type BodyComplexity =
  | "standard"
  | "cutaway_soft"
  | "cutaway_florentine"
  | "cutaway_venetian"
  | "double_cutaway"
  | "arm_bevel"
  | "tummy_cut"
  | "carved_top";

export type BindingComplexity =
  | "none"
  | "single"
  | "multiple"
  | "herringbone";

export type NeckComplexity =
  | "standard"
  | "volute"
  | "scarf_joint"
  | "multi_scale";

export type FretboardInlay =
  | "none"
  | "dots"
  | "blocks"
  | "trapezoids"
  | "custom";

export type FinishType =
  | "oil"
  | "wax"
  | "shellac_wipe"
  | "shellac_french_polish"
  | "nitro_solid"
  | "nitro_burst"
  | "nitro_vintage"
  | "poly_solid"
  | "poly_burst";

export type RosetteComplexity =
  | "none"
  | "simple_rings"
  | "mosaic"
  | "custom_art";

// ============================================================================
// REQUEST TYPES
// ============================================================================

export interface EstimateRequest {
  instrument_type: InstrumentType;
  builder_experience: BuilderExperience;
  body_complexity: BodyComplexity;
  binding_body_complexity: BindingComplexity;
  neck_complexity: NeckComplexity;
  fretboard_inlay: FretboardInlay;
  finish_type: FinishType;
  rosette_complexity: RosetteComplexity;
  batch_size?: number;
  hourly_rate?: number;
  include_materials?: boolean;
}

export interface QuoteRequest {
  estimate_request: EstimateRequest;
  customer_name?: string;
  markup_pct?: number;
  validity_days?: number;
  notes?: string;
}

export interface LearningCurveParams {
  first_unit_hours: number;
  quantity: number;
  learning_rate?: number;
  hourly_rate?: number;
}

// ============================================================================
// RESPONSE TYPES
// ============================================================================

export interface WBSTask {
  task_id: string;
  task_name: string;
  base_hours: number;
  complexity_multiplier: number;
  adjusted_hours: number;
  labor_cost: number;
  notes: string | null;
}

export interface MaterialEstimate {
  category: string;
  base_cost: number;
  waste_factor: number;
  adjusted_cost: number;
}

export interface LearningCurvePoint {
  unit_number: number;
  hours_per_unit: number;
  cumulative_hours: number;
  cumulative_cost: number;
}

export interface LearningCurveProjection {
  first_unit_hours: number;
  learning_rate: number;
  quantity: number;
  points: LearningCurvePoint[];
  average_hours_per_unit: number;
  total_hours: number;
  efficiency_gain_pct: number;
}

export interface EstimateResult {
  instrument_type: string;
  quantity: number;
  first_unit_hours: number;
  average_hours_per_unit: number;
  total_hours: number;
  labor_cost_per_unit: number;
  material_cost_per_unit: number;
  total_cost_per_unit: number;
  total_project_cost: number;
  wbs_tasks: WBSTask[];
  material_breakdown: MaterialEstimate[];
  learning_curve: LearningCurveProjection | null;
  complexity_factors_applied: Record<string, number>;
  total_complexity_multiplier: number;
  experience_level: string;
  experience_multiplier: number;
  confidence_level: string;
  risk_factors: string[];
  estimate_range_low: number;
  estimate_range_high: number;
  notes: string[];
}

export interface QuoteResult {
  quote_id: string;
  customer_name: string | null;
  estimate: EstimateResult;
  markup_pct: number;
  final_price: number;
  valid_until: string;
  terms: string;
  notes: string | null;
}

export interface ComplexityFactors {
  body: Record<string, number>;
  binding_body: Record<string, number>;
  neck: Record<string, number>;
  fretboard_inlay: Record<string, number>;
  finish: Record<string, number>;
  rosette: Record<string, number>;
  experience: Record<string, number>;
}

export interface WBSPhaseTask {
  task_id: string;
  name: string;
  base_hours: number;
  complexity_group: string | null;
}

export interface WBSTemplate {
  instrument_type: string;
  total_baseline_hours: number;
  task_count: number;
  phases: Record<string, WBSPhaseTask[]>;
}

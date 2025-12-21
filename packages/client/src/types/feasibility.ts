/**
 * Feasibility Types - Bundle 31.0.6
 */

import type { RosetteParamSpec } from "./rosette";

export type RiskBucket = "GREEN" | "YELLOW" | "RED";

export type RingFeasibilityDiagnostic = {
  ring_index: number;
  label?: string | null;
  risk_bucket: RiskBucket;
  score?: number | null;
  warnings?: string[];
  metrics?: Record<string, any> | null;
};

export type RosetteFeasibilitySummary = {
  suggestion_id?: string | null;
  overall_score: number;
  risk_bucket: RiskBucket;
  material_efficiency: number;
  estimated_cut_time_min: number;
  warnings: string[];
  ring_diagnostics?: RingFeasibilityDiagnostic[] | null;
  ring_count?: number | null;
};

export type RosetteFeasibilityBatchRequest = {
  specs: RosetteParamSpec[];
  suggestion_ids?: string[] | null;
};

export type RosetteFeasibilityBatchResponse = {
  summaries: RosetteFeasibilitySummary[];
};

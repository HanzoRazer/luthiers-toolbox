/**
 * RMOS Analytics Type Definitions (MM-4)
 * 
 * Material-aware lane analytics with fragility scoring.
 */

export type RiskGrade = 'GREEN' | 'YELLOW' | 'RED' | 'unknown';
export type Lane = 'safe' | 'tuned_v1' | 'tuned_v2' | 'experimental' | 'archived' | 'unknown';

export interface MaterialRiskSummary {
  material_type: string;
  job_count: number;
  avg_fragility?: number | null;
  worst_fragility?: number | null;
}

export interface LaneRiskSummary {
  lane: Lane;
  job_count: number;
  avg_risk_score?: number | null;
  grade_counts: Record<RiskGrade | string, number>;

  // MM-4 additions:
  avg_fragility_score?: number | null;
  dominant_material_types: string[];
}

export interface GlobalRiskSummary {
  total_jobs: number;
  total_presets: number;
  avg_risk_score?: number | null;
  grade_counts: Record<RiskGrade | string, number>;

  // MM-4 additions:
  overall_fragility_score?: number | null;
  material_risk_by_type: MaterialRiskSummary[];
}

export interface RecentRunItem {
  job_id: string;
  preset_id?: string | null;
  created_at: string;
  lane: Lane;
  job_type: string;
  risk_grade: RiskGrade;
  doc_grade?: RiskGrade | null;
  gantry_grade?: RiskGrade | null;

  // MM-4: worst fragility per job
  worst_fragility_score?: number | null;
}

export interface LaneTransition {
  from_lane: Lane;
  to_lane: Lane;
  count: number;
}

export interface LaneAnalyticsResponse {
  global_summary: GlobalRiskSummary;
  lane_summaries: LaneRiskSummary[];
  recent_runs: RecentRunItem[];
  lane_transitions: LaneTransition[];

  // MM-4: explicit global material breakdown
  material_risk_global: MaterialRiskSummary[];
}

export interface RiskTimelinePoint {
  job_id: string;
  created_at: string;
  lane: Lane;
  risk_grade: RiskGrade;
  risk_score?: number | null;
  worst_fragility_score?: number | null;
}

export interface RiskTimelineResponse {
  preset_id: string;
  points: RiskTimelinePoint[];
}

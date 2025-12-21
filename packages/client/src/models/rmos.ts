// packages/client/src/models/rmos.ts

export type RiskGrade = 'GREEN' | 'YELLOW' | 'RED';

export interface RosetteRingBand {
  id: string;
  index: number; // 0 = outermost
  radius_mm: number;
  width_mm: number;
  color_hint?: string | null;
  strip_family_id: string;
  slice_angle_deg: number;
  tile_length_override_mm?: number | null;
}

export interface RosettePattern {
  id: string;
  name: string;
  center_x_mm: number;
  center_y_mm: number;
  ring_bands: RosetteRingBand[];
  default_slice_thickness_mm: number;
  default_passes: number;
  default_workholding: string;
  default_tool_id?: string | null;
}

export interface RingRequirement {
  ring_index: number;
  strip_family_id: string;
  radius_mm: number;
  width_mm: number;
  circumference_mm: number;
  tiles_per_guitar: number;
  total_tiles: number;
  tile_length_mm: number;
}

export interface StripFamilyPlan {
  strip_family_id: string;
  color_hint?: string | null;
  slice_angle_deg: number;
  tile_length_mm: number;
  total_tiles_needed: number;
  tiles_per_meter: number;
  total_strip_length_m: number;
  suggested_stick_length_mm: number;
  sticks_needed: number;
  ring_indices: number[];
}

export interface ManufacturingPlan {
  pattern: RosettePattern;
  guitars: number;
  ring_requirements: RingRequirement[];
  strip_plans: StripFamilyPlan[];
  notes?: string | null;
}

export interface SliceRiskSummary {
  index: number;
  kind: 'line' | 'ring';
  offset_mm: number;
  risk_grade: RiskGrade;
  rim_speed_m_min: number;
  doc_grade: RiskGrade;
  gantry_grade: RiskGrade;
}

export interface BaseJobLog {
  id: string;
  created_at: string;
  job_type: string;
  pipeline_id?: string | null;
  node_id?: string | null;
  extra?: Record<string, any>;
}

export interface SawBatchJobLog extends BaseJobLog {
  job_type: 'saw_slice_batch' | 'saw_slice';
  machine_profile?: string | null;
  machine_gantry_span_mm?: number | null;
  tool_id: string;
  material: string;
  workholding: string;
  num_slices: number;
  slice_thickness_mm: number;
  passes: number;
  overall_risk_grade: RiskGrade;
  slice_risks: SliceRiskSummary[];
  yield_estimate?: number | null;
  best_slice_indices: number[];
  operator_notes?: string | null;
}

export interface RosettePlanJobLog extends BaseJobLog {
  job_type: 'rosette_plan';
  plan_pattern_id: string;
  plan_guitars: number;
  plan_total_tiles: number;
  summary_risk_grade: RiskGrade;
}

export type JobLogEntry = SawBatchJobLog | RosettePlanJobLog;

export interface SawSliceBatchOpCircle {
  id: string;
  op_type: 'saw_slice_batch';
  tool_id: string;
  geometry_source: 'circle_param';
  base_circle: {
    center_x_mm: number;
    center_y_mm: number;
    radius_mm: number;
  };
  num_rings: number;
  radial_step_mm: number;
  radial_sign: number;
  slice_thickness_mm: number;
  passes: number;
  material: string;
  workholding: string;
}

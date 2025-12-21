// packages/client/src/types/curvelab.ts
// Shared CurveLab preflight + DXF validation models

export type CurveUnits = "mm" | "inch";

export interface CurvePoint {
  x: number;
  y: number;
}

export interface CurveBiarcEntity {
  type: "arc" | "line";
  radius?: number | null;
  center?: CurvePoint | null;
  start_angle?: number | null;
  end_angle?: number | null;
  a?: CurvePoint | null;
  b?: CurvePoint | null;
}

export interface CurvePreflightRequest {
  points: CurvePoint[];
  units: CurveUnits;
  tolerance_mm?: number;
  layer?: string;
  biarc_entities?: CurveBiarcEntity[] | null;
}

export type ValidationSeverity = "error" | "warning" | "info";
export type ValidationCategory =
  | "format"
  | "geometry"
  | "units"
  | "layers"
  | "compatibility";

export interface ValidationIssue {
  severity: ValidationSeverity;
  category: ValidationCategory;
  message: string;
  details?: string | null;
  fix_available?: boolean;
  fix_description?: string | null;
}

export interface PolylineMetrics {
  point_count: number;
  length: number;
  length_units: string;
  closed: boolean;
  closure_gap: number;
  closure_units: string;
  duplicate_count: number;
  duplicate_indices: number[];
  bounding_box: Record<string, number>;
}

export interface BiarcMetrics {
  entity_count: number;
  arcs: number;
  lines: number;
  min_radius?: number | null;
  max_radius?: number | null;
  radius_units: string;
}

export interface CurvePreflightResponse {
  units: CurveUnits;
  tolerance_mm: number;
  issues: ValidationIssue[];
  errors_count: number;
  warnings_count: number;
  info_count: number;
  polyline: PolylineMetrics;
  biarc?: BiarcMetrics | null;
  cam_ready: boolean;
  recommended_actions: string[];
}

export interface GeometrySummary {
  lines: number;
  arcs: number;
  circles: number;
  polylines: number;
  lwpolylines: number;
  splines: number;
  ellipses: number;
  text: number;
  other: number;
  total: number;
}

export interface LayerInfo {
  name: string;
  entity_count: number;
  geometry_types: string[];
  color?: number | null;
  frozen: boolean;
  locked: boolean;
}

export interface ValidationReport {
  filename: string;
  filesize_bytes: number;
  dxf_version: string;
  units?: string | null;
  issues: ValidationIssue[];
  errors_count: number;
  warnings_count: number;
  info_count: number;
  geometry: GeometrySummary;
  layers: LayerInfo[];
  cam_ready: boolean;
  recommended_actions: string[];
}

export type AutoFixOption =
  | "convert_to_r12"
  | "close_open_polylines"
  | "explode_splines"
  | "merge_duplicate_layers"
  | "set_units_mm";

export interface AutoFixRequest {
  dxf_base64: string;
  filename: string;
  fixes: AutoFixOption[];
}

export interface AutoFixResponse {
  fixed_dxf_base64: string;
  fixes_applied: string[];
  validation_report: ValidationReport;
}

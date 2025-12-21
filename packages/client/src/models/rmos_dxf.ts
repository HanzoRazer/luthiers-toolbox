export interface DxfGuidedSlicePreviewRequest {
  op_id: string;
  tool_id: string;
  dxf_path: string;
  layer?: string | null;
  entity_index?: number | null;
  unit_scale?: number;
  slice_thickness_mm?: number;
  passes?: number;
  material?: string;
  workholding?: string;
}

export interface DxfGuidedBatchPreviewRequest {
  op_id: string;
  tool_id: string;
  dxf_path: string;
  layer?: string | null;
  max_entities?: number | null;
  unit_scale?: number;
  slice_thickness_mm?: number;
  passes?: number;
  material?: string;
  workholding?: string;
}

export type RiskGrade = 'GREEN' | 'YELLOW' | 'RED';

export interface DxfBatchPreviewResponse {
  op_id: string;
  tool_id: string;
  mode: string;
  dxf_path: string;
  num_slices: number;
  overall_risk_grade: RiskGrade;
  slice_risks: Array<{
    index: number;
    kind: 'line' | 'circle';
    layer: string;
    risk_grade: RiskGrade;
    rim_speed_m_min: number;
    doc_grade: RiskGrade;
    gantry_grade: RiskGrade;
  }>;
  gcode: string;
}

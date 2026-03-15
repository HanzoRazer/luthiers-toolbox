/**
 * RMOS Rosette CAM Types
 *
 * Types for rosette CNC/CAM operations exposed via /api/rmos/rosette/*.
 * Mirrors services/api/app/rmos/rosette_cam_router.py
 */

// ── Ring Configuration ───────────────────────────────────────────

export interface RingConfig {
  ring_id?: number;
  radius_mm: number;
  width_mm: number;
  tile_length_mm?: number;
  kerf_mm?: number;
  herringbone_angle_deg?: number;
  twist_angle_deg?: number;
}

// ── Segment Ring ─────────────────────────────────────────────────

export interface SegmentRingRequest {
  ring?: RingConfig;
  ring_id?: number;
  radius_mm?: number;
  width_mm?: number;
  tile_length_mm?: number;
  kerf_mm?: number;
  tile_count?: number;
}

export interface TileSegment {
  tile_id: number;
  theta_start_rad: number;
  theta_end_rad: number;
  inner_radius_mm: number;
  outer_radius_mm: number;
  arc_length_mm: number;
  corners: Array<{ x: number; y: number }>;
}

export interface SegmentRingResponse {
  ok: boolean;
  segmentation_id?: string;
  ring_id?: number;
  tile_count?: number;
  tile_length_mm?: number;
  segments?: TileSegment[];
  error?: string;
}

// ── Generate Slices ──────────────────────────────────────────────

export interface GenerateSlicesRequest {
  ring?: RingConfig;
  ring_id?: number;
  radius_mm?: number;
  width_mm?: number;
  tile_count?: number;
}

export interface Slice {
  slice_id: number;
  angle_rad: number;
  inner_point: { x: number; y: number };
  outer_point: { x: number; y: number };
}

export interface GenerateSlicesResponse {
  ok: boolean;
  batch_id?: string;
  ring_id?: number;
  slices?: Slice[];
  error?: string;
}

// ── Preview ──────────────────────────────────────────────────────

export interface PreviewRosetteRequest {
  pattern_id?: string;
  rings?: RingConfig[];
  ring_id?: number;
  radius_mm?: number;
  width_mm?: number;
}

export interface RingPreview {
  ring_id: number;
  radius_mm: number;
  width_mm: number;
  tile_length_mm: number;
  kerf_mm: number;
}

export interface PreviewRosetteResponse {
  ok: boolean;
  pattern_id?: string;
  preview?: unknown;
  rings?: RingPreview[];
  error?: string;
}

// ── Export CNC ───────────────────────────────────────────────────

export type MaterialType = "hardwood" | "softwood" | "composite";
export type MachineProfile = "grbl" | "fanuc";

export interface ExportCncRequest {
  ring?: RingConfig;
  ring_id?: number;
  radius_mm?: number;
  width_mm?: number;
  tile_count?: number;
  material?: MaterialType;
  origin_x_mm?: number;
  origin_y_mm?: number;
  rotation_deg?: number;
  machine_profile?: MachineProfile;
  safe_z_mm?: number;
  spindle_rpm?: number;
  tool_id?: number;
}

export interface SafetyDecision {
  decision: string;
  risk_level: string;
  requires_override: boolean;
  reasons: string[];
}

export interface ExportCncResponse {
  ok: boolean;
  gcode?: string;
  job_id?: string;
  ring_id?: number;
  segment_count?: number;
  estimated_runtime_sec?: number;
  safety?: SafetyDecision;
  metadata?: Record<string, unknown>;
  error?: string;
}

// ── CNC History ──────────────────────────────────────────────────

export interface CncJob {
  job_id: string;
  job_type: string;
  created_at: string;
  post_preset?: string;
  rings?: number;
  z_passes?: number;
  length_mm?: number;
  gcode_lines?: number;
  meta?: Record<string, unknown>;
  status?: string;
}

export interface CncHistoryResponse {
  jobs: CncJob[];
  total: number;
}

export interface CncJobDetailResponse {
  job_id: string;
  job_type: string;
  created_at: string;
  post_preset?: string;
  rings?: number;
  z_passes?: number;
  length_mm?: number;
  gcode_lines?: number;
  meta?: Record<string, unknown>;
  status: string;
}

/**
 * ReliefKernelLab types.
 */

export interface ComparisonRow {
  name: string
  est_time_s: number
  risk_score: number
  thin_floor_count: number
  high_load_count: number
  avg_floor_thickness: number
  min_floor_thickness: number
  max_load_index: number
}

export interface SimBridgeIssue {
  type: string
  severity: string
  x: number
  y: number
  z?: number
  extra_time_s?: number
  note?: string
  meta?: Record<string, unknown>
}

export interface SimBridgeOverlay {
  type: string
  x: number
  y: number
  z?: number
  intensity?: number
  severity?: string
  meta?: Record<string, unknown>
}

export interface SimBridgeStats {
  avg_floor_thickness: number
  min_floor_thickness: number
  max_load_index: number
  avg_load_index: number
  total_removed_volume: number
  cell_count: number
}

export interface SimBridgeOutput {
  issues: SimBridgeIssue[]
  overlays: SimBridgeOverlay[]
  stats: SimBridgeStats
  risk_score: number
  meta?: Record<string, unknown>
}

export interface HeightmapData {
  z_grid: number[][]
  origin_x: number
  origin_y: number
  cell_size_xy: number
  units: string
  width: number
  height: number
  z_min: number
  z_max: number
}

export interface FinishingResult {
  moves: Array<{ x?: number; y?: number; z?: number }>
  stats: {
    est_time_s: number
    length_xy: number
    min_z: number
    max_z: number
  }
}

export interface PresetParams {
  scallop_height: number
  stepdown: number
  use_dynamic_scallop: boolean
  min_floor_thickness: number
  high_load_index: number
  med_load_index: number
}

export const PRESETS: Record<string, PresetParams> = {
  Safe: {
    scallop_height: 0.03,
    stepdown: 0.25,
    use_dynamic_scallop: true,
    min_floor_thickness: 0.9,
    high_load_index: 1.6,
    med_load_index: 1.2
  },
  Standard: {
    scallop_height: 0.05,
    stepdown: 0.4,
    use_dynamic_scallop: true,
    min_floor_thickness: 0.7,
    high_load_index: 2.0,
    med_load_index: 1.5
  },
  Aggressive: {
    scallop_height: 0.08,
    stepdown: 0.6,
    use_dynamic_scallop: true,
    min_floor_thickness: 0.5,
    high_load_index: 2.6,
    med_load_index: 1.9
  }
}

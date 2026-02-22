/**
 * RosetteCompare type definitions.
 */

// ============================================================================
// Path Types
// ============================================================================

export interface RosettePath {
  points: [number, number][]
}

// ============================================================================
// Job Types
// ============================================================================

export interface RosettePreview {
  job_id: string
  pattern_type: string
  segments: number
  inner_radius: number
  outer_radius: number
  units: string
  preset: string | null
  name: string | null
  paths: RosettePath[]
  bbox: [number, number, number, number]
}

export interface RosetteJob {
  job_id: string
  name: string | null
  preset: string | null
  created_at: string
  preview: RosettePreview
}

// ============================================================================
// Diff Types
// ============================================================================

export interface RosetteDiffSummary {
  job_id_a: string
  job_id_b: string
  pattern_type_a: string
  pattern_type_b: string
  pattern_type_same: boolean
  segments_a: number
  segments_b: number
  segments_delta: number
  inner_radius_a: number
  inner_radius_b: number
  inner_radius_delta: number
  outer_radius_a: number
  outer_radius_b: number
  outer_radius_delta: number
  units_a: string
  units_b: string
  units_same: boolean
  bbox_union: [number, number, number, number]
  bbox_a: [number, number, number, number]
  bbox_b: [number, number, number, number]
  preset_a?: string
  preset_b?: string
}

export interface RosetteCompareResult {
  job_a: RosettePreview
  job_b: RosettePreview
  diff_summary: RosetteDiffSummary
}

// ============================================================================
// Snapshot Types
// ============================================================================

export interface CompareSnapshot {
  id: number
  job_id_a: string
  job_id_b: string
  lane: string | null
  risk_score: number
  diff_summary: RosetteDiffSummary
  note: string | null
  created_at: string
}

export interface GroupedSnapshots {
  presetLabel: string
  snapshots: CompareSnapshot[]
  avgRisk: number
}

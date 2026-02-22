/**
 * MultiRunComparisonView type definitions.
 */

// ============================================================================
// Preset Types
// ============================================================================

export interface Preset {
  id: string
  name: string
  kind: string
  job_source_id?: string
  created_at: string
}

// ============================================================================
// Comparison Types
// ============================================================================

export interface ComparisonRun {
  preset_id: string
  preset_name: string
  job_source_id?: string
  run_id?: string
  sim_time_s?: number
  sim_energy_j?: number
  sim_move_count?: number
  sim_issue_count?: number
  sim_max_dev_pct?: number
  stepover?: number
  feed_xy?: number
  strategy?: string
  efficiency_score?: number
  created_at?: string
}

export interface ComparisonResult {
  runs: ComparisonRun[]
  avg_time_s?: number
  min_time_s?: number
  max_time_s?: number
  avg_energy_j?: number
  avg_move_count?: number
  time_trend?: string
  energy_trend?: string
  best_run_id?: string
  worst_run_id?: string
  recommendations: string[]
}

// ============================================================================
// Storage Keys
// ============================================================================

export const STORAGE_KEYS = {
  SELECTED_PRESETS: 'multirun.selectedPresets',
  LAST_COMPARISON: 'multirun.lastComparison',
  LAST_UPDATED: 'multirun.lastUpdated'
} as const

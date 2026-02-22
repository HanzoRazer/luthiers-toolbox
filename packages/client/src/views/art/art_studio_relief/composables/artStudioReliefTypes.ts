/**
 * ArtStudioRelief types and constants.
 */
import type { RiskAnalytics } from '@/api/camRisk'

// ============================================================================
// Severity
// ============================================================================

export const SEVERITY_OPTIONS = ['info', 'low', 'medium', 'high', 'critical'] as const
export type SeverityOption = (typeof SEVERITY_OPTIONS)[number]

// ============================================================================
// Preset Config
// ============================================================================

export interface ReliefPresetFinishing {
  tool_d?: number
  scallop_height?: number
  stepdown?: number
  use_dynamic_scallop?: boolean
}

export interface ReliefPresetSimThresholds {
  min_floor_thickness?: number
  high_load_index?: number
  med_load_index?: number
}

export interface ReliefPresetConfig {
  name: string
  finishing?: ReliefPresetFinishing
  sim_thresholds?: ReliefPresetSimThresholds
}

// ============================================================================
// Risk Analytics Return
// ============================================================================

export { type RiskAnalytics }

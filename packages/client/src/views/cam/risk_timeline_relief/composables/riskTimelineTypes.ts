/**
 * RiskTimelineRelief types.
 */

export type PresetFilter = 'Any' | 'Safe' | 'Standard' | 'Aggressive' | 'Custom'

export interface SeverityCounts {
  info?: number
  low?: number
  medium?: number
  high?: number
  critical?: number
  [key: string]: number | undefined
}

export interface RiskPresetMeta {
  name?: string
  source?: string
  config?: unknown
}

export interface ReliefSimStats {
  avg_floor_thickness?: number
  min_floor_thickness?: number
  max_load_index?: number
  avg_load_index?: number
  total_removed_volume?: number
}

export interface RiskJob {
  id: string
  pipeline_id?: string
  pipelineId?: string
  op_id?: string
  opId?: string
  created_at?: string
  timestamp?: string
  analytics?: {
    risk_score?: number
    total_issues?: number
    severity_counts?: SeverityCounts
  }
  meta?: {
    preset?: RiskPresetMeta
    relief_sim_bridge?: ReliefSimStats
    sim_stats?: ReliefSimStats
    stock_thickness?: number
    [key: string]: unknown
  }
}

export interface RiskSummary {
  jobsCount: number
  avgRisk: number
  totalCritical: number
}

export interface DateWindow {
  from: Date | null
  to: Date | null
}

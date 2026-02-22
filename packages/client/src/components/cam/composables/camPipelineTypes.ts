/**
 * CamPipeline type definitions.
 */

// ============================================================================
// Pipeline Operation Types
// ============================================================================

export type PipelineOpKind =
  | 'dxf_preflight'
  | 'adaptive_plan'
  | 'adaptive_plan_run'
  | 'export_post'
  | 'simulate_gcode'

export interface PipelineOpResult {
  kind: PipelineOpKind
  ok: boolean
  error?: string | null
  payload?: any
}

export interface PipelineResponse {
  ops: PipelineOpResult[]
  summary: Record<string, any>
}

// ============================================================================
// Preset Types
// ============================================================================

export interface PipelinePreset {
  id: string
  name: string
  description?: string | null
  units: 'mm' | 'inch'
  machine_id?: string | null
  post_id?: string | null
}

// ============================================================================
// Inspector Types
// ============================================================================

export interface MachineProfile {
  id: string
  name: string
  max_feed_xy?: number
  rapid?: number
  accel?: number
  jerk?: number
  safe_z_default?: number
  [key: string]: any
}

export interface PostProfile {
  id: string
  name: string
  post?: string
  post_mode?: string
  line_numbers?: boolean
  [key: string]: any
}

// ============================================================================
// Normalization Types
// ============================================================================

export interface NormalizationIssue {
  code?: string
  message: string
  severity?: string
  path?: string
}

export interface NormalizationEntry {
  path: string
  issues: NormalizationIssue[]
}

// ============================================================================
// Emits
// ============================================================================

export interface CamPipelineEmits {
  (e: 'adaptive-plan-ready', payload: { moves: any[]; stats: any; overlays?: any[] }): void
  (e: 'sim-result-ready', payload: { issues: any[]; moves: any[]; summary: any }): void
}

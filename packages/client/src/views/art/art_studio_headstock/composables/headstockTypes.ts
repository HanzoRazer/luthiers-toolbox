/**
 * ArtStudioHeadstock types and constants.
 */
import type { PipelineOp } from '@/api/pipeline'
import type { RiskBackplotMoveOut } from '@/api/camRisk'

export type SeverityOption = 'info' | 'low' | 'medium' | 'high' | 'critical'

export const SEVERITY_OPTIONS: SeverityOption[] = ['info', 'low', 'medium', 'high', 'critical']

export interface SeverityCounts {
  info: number
  low: number
  medium: number
  high: number
  critical: number
}

export interface HeadstockBackplotSnapshot {
  moves: RiskBackplotMoveOut[]
  overlays: Record<string, unknown>[]
  meta: Record<string, unknown>
}

/**
 * Default headstock pipeline ops.
 * Follows the same pattern as rosette, but tuned for shallow logo engraving.
 */
export const HEADSTOCK_OPS: PipelineOp[] = [
  {
    id: 'headstock_adaptive',
    op: 'AdaptivePocket',
    from_layer: 'LOGO',
    input: {
      tool_d: 1.5,
      stepover: 0.3,
      stepdown: 0.4,
      margin: 0.05,
      strategy: 'Spiral',
      feed_xy: 600.0,
      safe_z: 3.0,
      z_rough: -0.8
    }
  } as PipelineOp,
  {
    id: 'headstock_helix',
    op: 'HelicalEntry',
    from_op: 'headstock_adaptive',
    input: {
      ramp_angle_deg: 3.0,
      pitch_mm: 1.2
    }
  } as PipelineOp,
  {
    id: 'headstock_post',
    op: 'PostProcess',
    from_op: 'headstock_helix',
    input: {
      post_preset: 'GRBL'
    }
  } as PipelineOp,
  {
    id: 'headstock_sim',
    op: 'Simulate',
    from_op: 'headstock_post',
    input: {
      stock_thickness: 3.0
    }
  } as PipelineOp
]

export const DEFAULT_DXF_PATH = 'workspace/art/headstock/demo_headstock_logo.dxf'

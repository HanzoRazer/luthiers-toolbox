/**
 * Type definitions for Bridge Lab workflow.
 */

// ============================================================================
// Machine Types
// ============================================================================

export interface MachineLimits {
  min_x?: number | null
  max_x?: number | null
  min_y?: number | null
  max_y?: number | null
  min_z?: number | null
  max_z?: number | null
}

export interface MachineCamDefaults {
  tool_d?: number | null
  stepover?: number | null
  stepdown?: number | null
  feed_xy?: number | null
  safe_z?: number | null
  z_rough?: number | null
}

export interface Machine {
  id: string
  name: string
  controller?: string | null
  units?: string | null
  limits?: MachineLimits | null
  camDefaults?: MachineCamDefaults | null
}

// ============================================================================
// Adaptive Parameters
// ============================================================================

export interface AdaptiveParams {
  tool_d: number
  units: 'mm' | 'inch'
  geometry_layer: string
  stepover: number
  stepdown: number
  margin: number
  strategy: 'Spiral' | 'Lanes'
  feed_xy: number
  safe_z: number
  z_rough: number
}

export const DEFAULT_ADAPTIVE_PARAMS: AdaptiveParams = {
  tool_d: 6.0,
  units: 'mm',
  geometry_layer: 'GEOMETRY',
  stepover: 0.45,
  stepdown: 2.0,
  margin: 0.5,
  strategy: 'Spiral',
  feed_xy: 1200,
  safe_z: 5.0,
  z_rough: -1.5
}

// ============================================================================
// Post Processor
// ============================================================================

export interface PostProcessor {
  id: string
  name: string
}

export const FALLBACK_POSTS: PostProcessor[] = [
  { id: 'GRBL', name: 'GRBL' },
  { id: 'Mach4', name: 'Mach4' },
  { id: 'LinuxCNC', name: 'LinuxCNC' },
  { id: 'PathPilot', name: 'PathPilot' },
  { id: 'MASSO', name: 'MASSO' }
]

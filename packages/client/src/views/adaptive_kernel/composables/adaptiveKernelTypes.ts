/**
 * AdaptiveKernelLab type definitions.
 */

// ============================================================================
// Preview Types
// ============================================================================

export interface PreviewLoop {
  pts: [number, number][]
}

export interface ToolpathSegment {
  pts: [number, number][]
  kind: 'rapid' | 'cut'
}

export interface ViewBox {
  x: number
  y: number
  w: number
  h: number
}

// ============================================================================
// Storage Keys
// ============================================================================

export const ADAPTIVE_PIPELINE_PRESET_KEY = 'ltb_pipeline_adaptive_preset_v1'

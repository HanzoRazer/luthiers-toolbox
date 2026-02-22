/**
 * AudioAnalyzer types for composables.
 */
import type { NormalizedPack, NormalizedFileEntry } from '@/evidence'

// Re-export for convenience
export type { NormalizedPack, NormalizedFileEntry }

// ============================================================================
// Selection Types
// ============================================================================

/**
 * GOVERNANCE NOTE — READ BEFORE MODIFYING
 *
 * SelectedPeak represents a user-controlled navigation cursor only.
 * It exists to coordinate highlighting and view alignment across renderers
 * without performing analysis, inference, ranking, filtering, or scoring.
 *
 * This object MUST NOT contain derived values, interpretations, risk scores,
 * recommendations, or cross-evidence aggregation. All fields must originate
 * directly from user actions or exported evidence artifacts.
 */
export interface SelectedPeak {
  pointId: string | null
  spectrumRelpath: string
  peaksRelpath: string
  peakIndex: number
  freq_hz: number
  label?: string
  raw: unknown
  rawPretty: string
}

export interface WsiRow {
  freq_hz?: number
  wsi?: number
  loc?: number
  grad?: number
  phase_disorder?: number
  coh_mean?: number
  admissible?: boolean
}

export type SelectionSource = 'spectrum' | 'wsi' | 'unknown'

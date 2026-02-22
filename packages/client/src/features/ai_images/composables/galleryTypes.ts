/**
 * Type definitions for AI Image Gallery.
 */
import type { VisionAsset, ProviderName } from '../api/visionApi'
import type { AdvisoryVariantSummary } from '@/sdk/rmos/runs'

// ============================================================================
// Run Summary
// ============================================================================

export interface RunSummary {
  run_id: string
  created_at_utc?: string
  event_type?: string
  status?: string
}

// ============================================================================
// Gallery State
// ============================================================================

export interface GalleryGenerationParams {
  prompt: string
  provider: ProviderName
  numImages: number
  size: string
  quality: string
}

export type BusyState = 'review' | 'promote' | null

// ============================================================================
// Re-exports for convenience
// ============================================================================

export type { VisionAsset, ProviderName, AdvisoryVariantSummary }

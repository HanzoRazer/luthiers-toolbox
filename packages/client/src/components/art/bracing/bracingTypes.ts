/**
 * Type definitions for bracing calculator.
 */
import type { BracingPreviewRequest, BracingPreviewResponse, BraceProfileType } from '@/api/art-studio'

// ============================================================================
// Brace Entry
// ============================================================================

export interface BraceEntry extends BracingPreviewRequest {
  id: number
  name: string
  x_mm: number
  y_mm: number
  angle_deg: number
  result?: BracingPreviewResponse
}

// ============================================================================
// Profile Type Info
// ============================================================================

export interface ProfileTypeInfo {
  value: BraceProfileType
  label: string
  desc: string
}

// ============================================================================
// Batch Result
// ============================================================================

export interface BatchResult {
  total_mass_grams: number
  total_stiffness: number
}

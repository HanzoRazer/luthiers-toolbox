/**
 * JobIntHistory types for composables.
 */
import type { JobIntLogEntry } from '@/api/job_int'

// Re-export for convenience
export type { JobIntLogEntry }

// ============================================================================
// Filter Types
// ============================================================================

export interface JobIntFilters {
  machine_id: string
  post_id: string
  helical_only: boolean
  favorites_only: boolean
}

// ============================================================================
// Clone Form Types
// ============================================================================

export interface CloneForm {
  name: string
  description: string
  kind: 'cam' | 'combo'
  tagsInput: string
  cam_params: Record<string, any>
}

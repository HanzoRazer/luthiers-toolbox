/**
 * JobIntHistory entry actions composable.
 */
import type { Ref } from 'vue'
import { updateJobIntFavorite } from '@/api/job_int'
import type { JobIntLogEntry } from './jobIntHistoryTypes'

// ============================================================================
// Types
// ============================================================================

export interface JobIntHistoryActionsReturn {
  selectEntry: (entry: JobIntLogEntry) => void
  toggleFavorite: (entry: JobIntLogEntry) => Promise<void>
}

// ============================================================================
// Composable
// ============================================================================

export function useJobIntHistoryActions(
  errorMessage: Ref<string | null>
): JobIntHistoryActionsReturn {
  function selectEntry(entry: JobIntLogEntry): void {
    console.log('Selected job:', entry.run_id)
    // TODO: Open detail modal or navigate to detail view
  }

  async function toggleFavorite(entry: JobIntLogEntry): Promise<void> {
    const target = !entry.favorite
    try {
      const detail = await updateJobIntFavorite(entry.run_id, target)
      // Prefer server's value, but fallback to requested target
      entry.favorite = detail.favorite ?? target
      errorMessage.value = null
    } catch (err: any) {
      console.error('Failed to update favorite', err)
      errorMessage.value =
        err?.message ?? 'Failed to update favorite flag for this job.'
    }
  }

  return {
    selectEntry,
    toggleFavorite
  }
}

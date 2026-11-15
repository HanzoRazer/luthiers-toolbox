/**
 * JobIntHistory load and pagination composable.
 */
import type { Ref, UnwrapNestedRefs } from 'vue'
import { fetchJobIntLog, type JobIntLogListResponse } from '@/api/job_int'
import type { JobIntLogEntry, JobIntFilters } from './jobIntHistoryTypes'

// ============================================================================
// Types
// ============================================================================

export interface JobIntHistoryLoadReturn {
  load: () => Promise<void>
  reload: () => void
  applyFilters: () => void
  resetFilters: () => void
  prevPage: () => void
  nextPage: () => void
}

// ============================================================================
// Composable
// ============================================================================

export function useJobIntHistoryLoad(
  items: Ref<JobIntLogEntry[]>,
  total: Ref<number>,
  loading: Ref<boolean>,
  errorMessage: Ref<string | null>,
  filters: UnwrapNestedRefs<JobIntFilters>,
  limit: Ref<number>,
  offset: Ref<number>
): JobIntHistoryLoadReturn {
  async function load(): Promise<void> {
    loading.value = true
    errorMessage.value = null

    try {
      const res: JobIntLogListResponse = await fetchJobIntLog({
        machine_id: filters.machine_id || undefined,
        post_id: filters.post_id || undefined,
        helical_only: filters.helical_only || undefined,
        favorites_only: filters.favorites_only || undefined,
        limit: limit.value,
        offset: offset.value
      })
      items.value = res.items
      total.value = res.total
    } catch (err: any) {
      console.error('JobIntHistory load error', err)
      errorMessage.value = err?.message ?? 'Failed to load job history.'
    } finally {
      loading.value = false
    }
  }

  function reload(): void {
    offset.value = 0
    load()
  }

  function applyFilters(): void {
    offset.value = 0
    load()
  }

  function resetFilters(): void {
    filters.machine_id = ''
    filters.post_id = ''
    filters.helical_only = false
    filters.favorites_only = false
    offset.value = 0
    load()
  }

  function prevPage(): void {
    if (offset.value >= limit.value) {
      offset.value -= limit.value
      load()
    }
  }

  function nextPage(): void {
    if (offset.value + limit.value < total.value) {
      offset.value += limit.value
      load()
    }
  }

  return {
    load,
    reload,
    applyFilters,
    resetFilters,
    prevPage,
    nextPage
  }
}

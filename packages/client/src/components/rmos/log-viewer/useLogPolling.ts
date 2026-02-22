/**
 * Composable for RMOS log polling and soft refresh.
 */
import { ref, type Ref, type ComputedRef } from 'vue'
import { fetchRecentLogs, checkForNewerRuns, getBackoffMs, type RunLogEntry } from '@/api/rmosLogsClient'
import type { FilterParams } from './useLogFilters'

// ============================================================================
// Types
// ============================================================================

export interface LogPollingState {
  newRunsCount: Ref<number>
  isPollingPaused: Ref<boolean>
  startPolling: () => void
  stopPolling: () => void
  pausePolling: () => void
  resumePolling: () => void
  resetNewRunsCount: () => void
}

export interface UseLogPollingOptions {
  filterParams: ComputedRef<FilterParams>
  softCapValue: Ref<number>
  newestTimestamp: Ref<string | null>
  overflowCount: Ref<number>
  loading: Ref<boolean>
  loadingMore: Ref<boolean>
  tableContainerRef: Ref<HTMLElement | null>
  prependEntries: (entries: RunLogEntry[]) => void
}

// ============================================================================
// Composable
// ============================================================================

export function useLogPolling(options: UseLogPollingOptions): LogPollingState {
  const {
    filterParams,
    softCapValue,
    newestTimestamp,
    overflowCount,
    loading,
    loadingMore,
    tableContainerRef,
    prependEntries
  } = options

  const newRunsCount = ref(0)
  const isPollingPaused = ref(false)
  let pollInterval: ReturnType<typeof setInterval> | null = null

  async function softRefresh(): Promise<void> {
    if (!newestTimestamp.value) return

    try {
      const result = await checkForNewerRuns(newestTimestamp.value, filterParams.value)

      if (result.count > 0) {
        const cap = softCapValue.value

        if (result.count <= cap) {
          // Prepend new runs
          const response = await fetchRecentLogs({
            limit: result.count,
            ...filterParams.value
          })

          // Filter to only truly newer entries
          const newEntries = response.entries.filter(
            (e) => e.created_at_utc > newestTimestamp.value!
          )

          if (newEntries.length > 0) {
            prependEntries(newEntries)
          }
        } else {
          // Cap exceeded, show overflow
          overflowCount.value = result.count - cap
          newRunsCount.value = result.count
        }
      }
    } catch {
      // Silent fail for background refresh
    }
  }

  function startPolling(): void {
    if (pollInterval) return

    pollInterval = setInterval(async () => {
      if (isPollingPaused.value || loading.value || loadingMore.value) return

      // Check for new runs
      if (newestTimestamp.value) {
        const result = await checkForNewerRuns(newestTimestamp.value, filterParams.value)
        if (result.count > 0) {
          // Check if at top of list
          const atTop = tableContainerRef.value?.scrollTop === 0

          if (atTop) {
            // Auto-prepend if at top
            await softRefresh()
          } else {
            // Show badge
            newRunsCount.value = result.count
          }
        }
      }
    }, getBackoffMs())
  }

  function stopPolling(): void {
    if (pollInterval) {
      clearInterval(pollInterval)
      pollInterval = null
    }
  }

  function pausePolling(): void {
    isPollingPaused.value = true
  }

  function resumePolling(): void {
    isPollingPaused.value = false
  }

  function resetNewRunsCount(): void {
    newRunsCount.value = 0
  }

  return {
    newRunsCount,
    isPollingPaused,
    startPolling,
    stopPolling,
    pausePolling,
    resumePolling,
    resetNewRunsCount
  }
}

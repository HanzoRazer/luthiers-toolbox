/**
 * Composable for RMOS log entries management.
 */
import { ref, type Ref, type ComputedRef } from 'vue'
import { fetchRecentLogs, type RunLogEntry } from '@/api/rmosLogsClient'
import type { FilterParams } from './useLogFilters'

// ============================================================================
// Types
// ============================================================================

export interface LogEntriesState {
  entries: Ref<RunLogEntry[]>
  loading: Ref<boolean>
  loadingMore: Ref<boolean>
  error: Ref<string | null>
  hasMore: Ref<boolean>
  nextCursor: Ref<string | null>
  newestTimestamp: Ref<string | null>
  overflowCount: Ref<number>
  refresh: () => Promise<void>
  loadMore: () => Promise<void>
  jumpToNewest: () => Promise<void>
  prependEntries: (newEntries: RunLogEntry[]) => void
}

export interface UseLogEntriesOptions {
  initialLimit: number
  filterParams: ComputedRef<FilterParams>
  tableContainerRef: Ref<HTMLElement | null>
  selectedRunId: Ref<string | null>
}

// ============================================================================
// Composable
// ============================================================================

export function useLogEntries(options: UseLogEntriesOptions): LogEntriesState {
  const { initialLimit, filterParams, tableContainerRef, selectedRunId } = options

  const entries = ref<RunLogEntry[]>([])
  const loading = ref(false)
  const loadingMore = ref(false)
  const error = ref<string | null>(null)

  const hasMore = ref(false)
  const nextCursor = ref<string | null>(null)

  const newestTimestamp = ref<string | null>(null)
  const overflowCount = ref(0)

  async function refresh(): Promise<void> {
    loading.value = true
    error.value = null
    overflowCount.value = 0

    try {
      const response = await fetchRecentLogs({
        limit: initialLimit,
        ...filterParams.value
      })

      entries.value = response.entries
      hasMore.value = response.has_more
      nextCursor.value = response.next_cursor

      if (response.entries.length > 0) {
        newestTimestamp.value = response.entries[0].created_at_utc
      }
    } catch (e: unknown) {
      const err = e as { message?: string }
      error.value = err?.message || 'Failed to load logs'
    } finally {
      loading.value = false
    }
  }

  async function loadMore(): Promise<void> {
    if (!hasMore.value || loadingMore.value || !nextCursor.value) return

    loadingMore.value = true

    // Remember selected ID for selection pinning
    const selectedId = selectedRunId.value

    try {
      const response = await fetchRecentLogs({
        limit: initialLimit,
        cursor: nextCursor.value,
        ...filterParams.value
      })

      entries.value = [...entries.value, ...response.entries]
      hasMore.value = response.has_more
      nextCursor.value = response.next_cursor

      // Selection pinning - scroll to keep selected item in view
      if (selectedId && tableContainerRef.value) {
        setTimeout(() => {
          const selectedRow = tableContainerRef.value?.querySelector(
            `tr[data-run-id="${selectedId}"]`
          ) as HTMLElement | null
          if (selectedRow) {
            const containerRect = tableContainerRef.value!.getBoundingClientRect()
            const rowRect = selectedRow.getBoundingClientRect()
            if (rowRect.bottom > containerRect.bottom || rowRect.top < containerRect.top) {
              selectedRow.scrollIntoView({ block: 'center', behavior: 'smooth' })
            }
          }
        }, 50)
      }
    } catch (e: unknown) {
      const err = e as { message?: string }
      error.value = err?.message || 'Failed to load more logs'
    } finally {
      loadingMore.value = false
    }
  }

  async function jumpToNewest(): Promise<void> {
    // Scroll to top
    if (tableContainerRef.value) {
      tableContainerRef.value.scrollTop = 0
    }

    // Reset and refresh
    overflowCount.value = 0
    await refresh()
  }

  function prependEntries(newEntries: RunLogEntry[]): void {
    if (newEntries.length > 0) {
      entries.value = [...newEntries, ...entries.value]
      newestTimestamp.value = newEntries[0].created_at_utc
    }
  }

  return {
    entries,
    loading,
    loadingMore,
    error,
    hasMore,
    nextCursor,
    newestTimestamp,
    overflowCount,
    refresh,
    loadMore,
    jumpToNewest,
    prependEntries
  }
}

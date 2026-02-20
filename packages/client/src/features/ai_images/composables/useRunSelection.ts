/**
 * Composable for run loading, selection, pagination, and creation.
 * Extracted from VisionAttachToRunWidget.vue
 */
import { ref, watch, type Ref } from 'vue'
import {
  listRecentRuns,
  queryRecentRuns,
  createRun,
  type RunSummary,
} from '../api/visionApi'

// =============================================================================
// Constants
// =============================================================================

const RECENT_RUNS_PAGE_SIZE = 10
const LS_SELECTED_RUN = 'tb.visionAttach.selectedRunId'
const DEFAULT_EVENT_TYPE = 'vision_image_review'

// =============================================================================
// Types
// =============================================================================

export interface RunSelectionState {
  /** List of runs */
  runs: Ref<RunSummary[]>
  /** Currently selected run ID */
  selectedRunId: Ref<string | null>
  /** Search query */
  runSearch: Ref<string>
  /** Pagination cursor */
  runsCursor: Ref<string | null>
  /** Whether more runs are available */
  runsHasMore: Ref<boolean>
  /** Whether runs are loading */
  isLoadingRuns: Ref<boolean>
  /** Load runs from API */
  loadRuns: () => Promise<{ error?: string }>
  /** Load more runs (pagination) */
  loadMoreRuns: () => Promise<{ error?: string }>
  /** Create a new run and select it */
  createAndSelectRun: () => Promise<{ runId?: string; error?: string }>
  /** Select a run by ID */
  selectRun: (runId: string) => void
}

// =============================================================================
// Composable
// =============================================================================

export function useRunSelection(
  initialRunId?: string | null,
  onError?: (msg: string) => void
): RunSelectionState {
  const runs = ref<RunSummary[]>([])
  const selectedRunId = ref<string | null>(initialRunId || null)
  const runSearch = ref<string>('')
  const runsCursor = ref<string | null>(null)
  const runsHasMore = ref<boolean>(false)
  const isLoadingRuns = ref(false)

  // ===========================================================================
  // Methods
  // ===========================================================================

  async function loadRuns(): Promise<{ error?: string }> {
    isLoadingRuns.value = true
    try {
      // Prefer cursor endpoint when available; fallback to legacy listRecentRuns()
      try {
        const res = await queryRecentRuns({
          cursor: null,
          limit: RECENT_RUNS_PAGE_SIZE,
          q: runSearch.value.trim() || null,
        })
        runs.value = res.items || []
        runsCursor.value = res.next_cursor ?? null
        runsHasMore.value = !!res.next_cursor
      } catch {
        const list = await listRecentRuns(20)
        runs.value = list.runs || []
        runsCursor.value = null
        runsHasMore.value = false
      }

      // Selection preference:
      // 1) explicit prop
      // 2) localStorage remembered selection (if present in list)
      // 3) newest (first)
      if (!selectedRunId.value && runs.value.length > 0) {
        const remembered = window.localStorage.getItem(LS_SELECTED_RUN)
        const inList = remembered && runs.value.some((r) => r.run_id === remembered)
        selectedRunId.value = inList ? remembered : runs.value[0].run_id
      }

      return {}
    } catch (e: any) {
      const msg = e?.message ?? 'Failed to load runs'
      onError?.(msg)
      return { error: msg }
    } finally {
      isLoadingRuns.value = false
    }
  }

  async function loadMoreRuns(): Promise<{ error?: string }> {
    if (isLoadingRuns.value) return {}
    if (!runsHasMore.value) return {}
    if (!runsCursor.value) return {}

    isLoadingRuns.value = true
    try {
      const res = await queryRecentRuns({
        cursor: runsCursor.value,
        limit: RECENT_RUNS_PAGE_SIZE,
        q: runSearch.value.trim() || null,
      })
      const nextItems = res.items || []
      // de-dupe by run_id
      const seen = new Set(runs.value.map((r) => r.run_id))
      for (const r of nextItems) {
        if (!seen.has(r.run_id)) runs.value.push(r)
      }
      runsCursor.value = res.next_cursor ?? null
      runsHasMore.value = !!res.next_cursor
      return {}
    } catch (e: any) {
      const msg = e?.message ?? 'Failed to load more runs'
      onError?.(msg)
      return { error: msg }
    } finally {
      isLoadingRuns.value = false
    }
  }

  async function createAndSelectRun(): Promise<{ runId?: string; error?: string }> {
    isLoadingRuns.value = true
    try {
      const res = await createRun({ event_type: DEFAULT_EVENT_TYPE })
      selectedRunId.value = res.run_id
      await loadRuns()
      return { runId: res.run_id }
    } catch (e: any) {
      const msg = e?.message ?? 'Failed to create run'
      onError?.(msg)
      return { error: msg }
    } finally {
      isLoadingRuns.value = false
    }
  }

  function selectRun(runId: string) {
    selectedRunId.value = runId
  }

  // ===========================================================================
  // Watchers
  // ===========================================================================

  // Persist selected run to localStorage
  watch(selectedRunId, (v) => {
    if (v) window.localStorage.setItem(LS_SELECTED_RUN, v)
  })

  return {
    runs,
    selectedRunId,
    runSearch,
    runsCursor,
    runsHasMore,
    isLoadingRuns,
    loadRuns,
    loadMoreRuns,
    createAndSelectRun,
    selectRun,
  }
}

/**
 * Composable for managing the Log Viewer drawer state.
 * Extracted from DesignFirstWorkflowPanel.vue (Bundle 32.7.4 + 32.7.5)
 */
import { ref, computed, type Ref, type ComputedRef } from 'vue'

export interface LogDrawerState {
  /** Whether the drawer is open */
  isOpen: Ref<boolean>
  /** Pinned run ID (keeps iframe stable across workflow changes) */
  pinnedRunId: Ref<string>
  /** Whether the drawer is pinned to a specific run */
  isPinned: ComputedRef<boolean>
  /** Drawer title (includes pin indicator if pinned) */
  drawerTitle: ComputedRef<string>
  /** The effective run ID to show (pinned or current) */
  effectiveRunId: ComputedRef<string>
  /** The URL for the log viewer iframe */
  logsUrl: ComputedRef<string>
  /** Open the drawer (optionally pin to a run ID) */
  openDrawer: (runId?: string) => void
  /** Close the drawer and clear pin */
  closeDrawer: () => void
  /** Toggle pin state */
  togglePin: () => void
  /** Open logs in a new tab */
  openLogsNewTab: () => void
}

/**
 * Build Log Viewer URL for a given session ID
 */
function buildLogViewerUrl(sessionId: string): string {
  const u = new URL(window.location.href)
  u.pathname = '/rmos/logs'
  u.searchParams.set('mode', 'art_studio')
  u.searchParams.set('run_id', sessionId)
  return u.toString()
}

export function useLogDrawer(
  getCurrentSessionId: () => string
): LogDrawerState {
  const isOpen = ref(false)
  const pinnedRunId = ref('')

  const effectiveRunId = computed(() => {
    // If pinned, use pinned; else follow current sessionId
    return pinnedRunId.value || getCurrentSessionId() || ''
  })

  const logsUrl = computed(() => {
    const id = effectiveRunId.value
    if (!id) return ''
    return buildLogViewerUrl(id)
  })

  const isPinned = computed(() => !!pinnedRunId.value)

  const drawerTitle = computed(() => {
    if (isPinned.value) {
      return `Log Viewer (pinned: ${pinnedRunId.value.slice(0, 8)}…)`
    }
    return 'Log Viewer'
  })

  function openDrawer(runId?: string) {
    if (runId) {
      pinnedRunId.value = runId
    }
    isOpen.value = true
  }

  function closeDrawer() {
    isOpen.value = false
    pinnedRunId.value = ''
  }

  function togglePin() {
    if (isPinned.value) {
      // Unpin: follow current session
      pinnedRunId.value = ''
    } else {
      // Pin to current effective run_id
      pinnedRunId.value = effectiveRunId.value
    }
  }

  function openLogsNewTab() {
    if (logsUrl.value) {
      window.open(logsUrl.value, '_blank')
    }
  }

  return {
    isOpen,
    pinnedRunId,
    isPinned,
    drawerTitle,
    effectiveRunId,
    logsUrl,
    openDrawer,
    closeDrawer,
    togglePin,
    openLogsNewTab,
  }
}

/**
 * Composable for RMOS log selection state.
 */
import { ref, type Ref } from 'vue'
import type { RunLogEntry } from '@/api/rmosLogsClient'

// ============================================================================
// Types
// ============================================================================

export interface LogSelectionState {
  selectedRunId: Ref<string | null>
  selectedEntry: Ref<RunLogEntry | null>
  selectRun: (entry: RunLogEntry) => void
  clearSelection: () => void
}

export interface UseLogSelectionOptions {
  onSelect?: (entry: RunLogEntry) => void
  onPausePolling?: () => void
}

// ============================================================================
// Composable
// ============================================================================

export function useLogSelection(options: UseLogSelectionOptions = {}): LogSelectionState {
  const { onSelect, onPausePolling } = options

  const selectedRunId = ref<string | null>(null)
  const selectedEntry = ref<RunLogEntry | null>(null)

  function selectRun(entry: RunLogEntry): void {
    selectedRunId.value = entry.run_id
    selectedEntry.value = entry
    onSelect?.(entry)

    // Pause polling when details open
    onPausePolling?.()
  }

  function clearSelection(): void {
    selectedRunId.value = null
    selectedEntry.value = null
  }

  return {
    selectedRunId,
    selectedEntry,
    selectRun,
    clearSelection
  }
}

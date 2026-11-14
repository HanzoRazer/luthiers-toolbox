/**
 * RosetteCompare helper functions composable.
 */
import type { Ref } from 'vue'

// ============================================================================
// Types
// ============================================================================

export interface RosetteCompareHelpersReturn {
  setStatus: (msg: string, isError?: boolean) => void
}

// ============================================================================
// Composable
// ============================================================================

export function useRosetteCompareHelpers(
  statusMessage: Ref<string>,
  statusIsError: Ref<boolean>
): RosetteCompareHelpersReturn {
  /**
   * Set status message with error flag.
   */
  function setStatus(msg: string, isError = false): void {
    statusMessage.value = msg
    statusIsError.value = isError
  }

  return {
    setStatus
  }
}

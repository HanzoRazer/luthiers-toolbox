/**
 * Composable for Compare AF Modes modal state and actions.
 * Handles opening the comparison modal and applying selected mode as default.
 */
import { ref, type Ref } from 'vue'

// ============================================================================
// Types
// ============================================================================

export interface CompareModalConfig {
  /** Post ID for saving presets */
  postId: Ref<string>
}

export interface CompareModalDeps {
  /** AF mode ref to update when making default */
  afMode: Ref<string>
  /** Function to save preset for current post */
  savePresetForPost: (postId: string) => void
}

export interface CompareModalState {
  /** Whether the compare modal is open */
  compareOpen: Ref<boolean>
  /** Open the compare modal */
  openCompare: () => void
  /** Handle making a mode the default */
  handleMakeDefault: (mode: string) => void
}

// ============================================================================
// Composable
// ============================================================================

export function useCompareModal(
  config: CompareModalConfig,
  deps: CompareModalDeps
): CompareModalState {
  // -------------------------------------------------------------------------
  // State
  // -------------------------------------------------------------------------

  const compareOpen = ref(false)

  // -------------------------------------------------------------------------
  // Methods
  // -------------------------------------------------------------------------

  function openCompare() {
    compareOpen.value = true
  }

  function handleMakeDefault(mode: string) {
    deps.afMode.value = mode as any
    // Persist for current post
    deps.savePresetForPost(config.postId.value)
    compareOpen.value = false
  }

  // -------------------------------------------------------------------------
  // Return
  // -------------------------------------------------------------------------

  return {
    compareOpen,
    openCompare,
    handleMakeDefault,
  }
}

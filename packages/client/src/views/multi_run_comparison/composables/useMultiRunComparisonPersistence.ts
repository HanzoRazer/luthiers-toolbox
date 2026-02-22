/**
 * MultiRunComparisonView localStorage persistence composable.
 */
import type { Ref } from 'vue'
import { STORAGE_KEYS, type ComparisonResult } from './multiRunComparisonTypes'

// ============================================================================
// Types
// ============================================================================

export interface MultiRunComparisonPersistenceReturn {
  loadPersistedState: () => void
  savePersistedState: () => void
  clearPersistedState: () => void
}

// ============================================================================
// Composable
// ============================================================================

export function useMultiRunComparisonPersistence(
  selectedPresetIds: Ref<string[]>,
  comparisonResult: Ref<ComparisonResult | null>
): MultiRunComparisonPersistenceReturn {
  /**
   * Load state from localStorage.
   */
  function loadPersistedState(): void {
    try {
      // Load selected preset IDs
      const savedSelection = localStorage.getItem(STORAGE_KEYS.SELECTED_PRESETS)
      if (savedSelection) {
        const parsed = JSON.parse(savedSelection)
        if (Array.isArray(parsed)) {
          selectedPresetIds.value = parsed
        }
      }

      // Load last comparison result (within 24 hours)
      const savedComparison = localStorage.getItem(STORAGE_KEYS.LAST_COMPARISON)
      const savedTimestamp = localStorage.getItem(STORAGE_KEYS.LAST_UPDATED)
      if (savedComparison && savedTimestamp) {
        const timestamp = parseInt(savedTimestamp, 10)
        const age = Date.now() - timestamp
        const maxAge = 24 * 60 * 60 * 1000 // 24 hours

        if (age < maxAge) {
          comparisonResult.value = JSON.parse(savedComparison)
        } else {
          // Clear stale data
          localStorage.removeItem(STORAGE_KEYS.LAST_COMPARISON)
          localStorage.removeItem(STORAGE_KEYS.LAST_UPDATED)
        }
      }
    } catch (error) {
      console.error('Failed to load persisted state:', error)
      // Clear corrupted data
      clearPersistedState()
    }
  }

  /**
   * Save state to localStorage.
   */
  function savePersistedState(): void {
    try {
      // Save selected preset IDs
      localStorage.setItem(
        STORAGE_KEYS.SELECTED_PRESETS,
        JSON.stringify(selectedPresetIds.value)
      )

      // Save comparison result (if exists)
      if (comparisonResult.value) {
        localStorage.setItem(
          STORAGE_KEYS.LAST_COMPARISON,
          JSON.stringify(comparisonResult.value)
        )
        localStorage.setItem(STORAGE_KEYS.LAST_UPDATED, Date.now().toString())
      }
    } catch (error) {
      console.error('Failed to save state:', error)
    }
  }

  /**
   * Clear all persisted state.
   */
  function clearPersistedState(): void {
    localStorage.removeItem(STORAGE_KEYS.SELECTED_PRESETS)
    localStorage.removeItem(STORAGE_KEYS.LAST_COMPARISON)
    localStorage.removeItem(STORAGE_KEYS.LAST_UPDATED)
  }

  return {
    loadPersistedState,
    savePersistedState,
    clearPersistedState
  }
}

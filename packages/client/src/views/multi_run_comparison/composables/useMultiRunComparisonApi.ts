/**
 * MultiRunComparisonView API composable.
 */
import type { Ref } from 'vue'
import { api } from '@/services/apiBase'
import type { Preset, ComparisonResult } from './multiRunComparisonTypes'

// ============================================================================
// Types
// ============================================================================

export interface MultiRunComparisonApiReturn {
  fetchPresets: () => Promise<void>
  runComparison: () => Promise<void>
}

// ============================================================================
// Composable
// ============================================================================

export function useMultiRunComparisonApi(
  allPresets: Ref<Preset[]>,
  selectedPresetIds: Ref<string[]>,
  loading: Ref<boolean>,
  errorMessage: Ref<string>,
  comparisonResult: Ref<ComparisonResult | null>,
  onComparisonSuccess: () => void
): MultiRunComparisonApiReturn {
  /**
   * Fetch all presets from API.
   */
  async function fetchPresets(): Promise<void> {
    try {
      const response = await api('/api/presets')
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      allPresets.value = await response.json()
    } catch (error) {
      console.error('Failed to fetch presets:', error)
      errorMessage.value = 'Failed to load presets. Check console for details.'
    }
  }

  /**
   * Run comparison for selected presets.
   */
  async function runComparison(): Promise<void> {
    if (selectedPresetIds.value.length < 2) {
      errorMessage.value = 'Please select at least 2 presets to compare'
      return
    }

    loading.value = true
    errorMessage.value = ''
    comparisonResult.value = null

    try {
      const response = await api('/api/presets/compare-runs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          preset_ids: selectedPresetIds.value,
          include_trends: true,
          include_recommendations: true
        })
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `HTTP ${response.status}`)
      }

      comparisonResult.value = await response.json()

      // Callback for persistence
      onComparisonSuccess()
    } catch (error: unknown) {
      console.error('Comparison failed:', error)
      const message = error instanceof Error ? error.message : 'Unknown error'
      errorMessage.value = `Comparison failed: ${message}`
    } finally {
      loading.value = false
    }
  }

  return {
    fetchPresets,
    runComparison
  }
}

/**
 * MultiRunComparisonView actions composable.
 */
import { computed, type Ref, type ComputedRef } from 'vue'
import { downloadCsvFile } from '@/utils/downloadBlob'
import type { Preset, ComparisonResult } from './multiRunComparisonTypes'

// ============================================================================
// Types
// ============================================================================

export interface MultiRunComparisonActionsReturn {
  presetsWithLineage: ComputedRef<Preset[]>
  resetComparison: () => void
  exportComparisonCSV: () => void
}

// ============================================================================
// Composable
// ============================================================================

export function useMultiRunComparisonActions(
  allPresets: Ref<Preset[]>,
  selectedPresetIds: Ref<string[]>,
  comparisonResult: Ref<ComparisonResult | null>,
  errorMessage: Ref<string>,
  destroyChart: () => void,
  clearPersistedState: () => void
): MultiRunComparisonActionsReturn {
  /**
   * Filter presets with job lineage (B19 cloned jobs).
   */
  const presetsWithLineage = computed(() => {
    return allPresets.value.filter((p) => p.job_source_id)
  })

  /**
   * Reset comparison and clear state.
   */
  function resetComparison(): void {
    comparisonResult.value = null
    selectedPresetIds.value = []
    errorMessage.value = ''
    destroyChart()
    clearPersistedState()
  }

  /**
   * Export comparison results as CSV.
   */
  function exportComparisonCSV(): void {
    if (!comparisonResult.value) return

    const headers = [
      'Preset Name',
      'Time (s)',
      'Energy (J)',
      'Moves',
      'Issues',
      'Strategy',
      'Feed XY',
      'Efficiency Score'
    ]
    const rows = comparisonResult.value.runs.map((run) => [
      run.preset_name,
      run.sim_time_s?.toFixed(2) || 'N/A',
      run.sim_energy_j?.toFixed(0) || 'N/A',
      run.sim_move_count || 'N/A',
      run.sim_issue_count || '0',
      run.strategy || 'N/A',
      run.feed_xy?.toFixed(0) || 'N/A',
      run.efficiency_score?.toFixed(0) || 'N/A'
    ])

    const csv = [headers.join(','), ...rows.map((row) => row.join(','))].join('\n')

    downloadCsvFile(csv, `multi-run-comparison-${Date.now()}.csv`)
  }

  return {
    presetsWithLineage,
    resetComparison,
    exportComparisonCSV
  }
}

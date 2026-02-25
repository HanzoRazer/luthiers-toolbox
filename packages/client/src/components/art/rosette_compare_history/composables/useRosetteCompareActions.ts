/**
 * RosetteCompareHistory actions composable.
 */
import axios from 'axios'
import type { Ref, ComputedRef } from 'vue'
import { csvEscape, downloadCsvFile } from '@/utils/downloadBlob'
import type { CompareHistoryEntry } from './rosetteCompareTypes'

export interface RosetteCompareActionsReturn {
  refresh: () => Promise<void>
  exportCsv: () => void
  formatTime: (ts: string) => string
}

export function useRosetteCompareActions(
  entries: Ref<CompareHistoryEntry[]>,
  lane: ComputedRef<string>,
  effectiveJobId: ComputedRef<string | null>
): RosetteCompareActionsReturn {
  /**
   * Refresh entries from API.
   */
  async function refresh(): Promise<void> {
    try {
      const params: any = { lane: lane.value }
      if (effectiveJobId.value) {
        params.job_id = effectiveJobId.value
      }
      const res = await axios.get<CompareHistoryEntry[]>('/api/compare/history', {
        params
      })
      entries.value = res.data
    } catch (err) {
      console.error('Failed to load compare history', err)
    }
  }

  /**
   * Export entries as CSV.
   */
  function exportCsv(): void {
    if (!entries.value.length) return

    const headers = [
      'ts',
      'job_id',
      'lane',
      'baseline_id',
      'baseline_path_count',
      'current_path_count',
      'added_paths',
      'removed_paths',
      'unchanged_paths',
      'preset'
    ]

    const rows = entries.value.map((e) =>
      [
        e.ts,
        e.job_id ?? '',
        e.lane,
        e.baseline_id,
        e.baseline_path_count,
        e.current_path_count,
        e.added_paths,
        e.removed_paths,
        e.unchanged_paths,
        e.preset ?? ''
      ]
        .map((val) => csvEscape(val))
        .join(',')
    )

    const csvContent = [headers.join(','), ...rows].join('\r\n')

    const stamp = new Date().toISOString().replace(/[:.]/g, '-')
    const nameParts = [
      'compare_history',
      lane.value,
      effectiveJobId.value || 'all',
      stamp
    ]
    const filename = nameParts.join('_') + '.csv'

    downloadCsvFile(csvContent, filename)
  }

  /**
   * Format timestamp for display.
   */
  function formatTime(ts: string): string {
    try {
      const d = new Date(ts)
      return d.toLocaleString()
    } catch {
      return ts
    }
  }

  return {
    refresh,
    exportCsv,
    formatTime
  }
}

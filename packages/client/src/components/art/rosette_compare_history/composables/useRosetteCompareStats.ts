/**
 * RosetteCompareHistory stats composable.
 */
import { computed, type Ref, type ComputedRef } from 'vue'
import type { CompareHistoryEntry } from './rosetteCompareTypes'

export interface RosetteCompareStatsReturn {
  avgAdded: ComputedRef<string>
  avgRemoved: ComputedRef<string>
  avgUnchanged: ComputedRef<string>
}

export function useRosetteCompareStats(
  entries: Ref<CompareHistoryEntry[]>
): RosetteCompareStatsReturn {
  const avgAdded = computed(() => {
    if (!entries.value.length) return '0'
    const sum = entries.value.reduce((acc, e) => acc + (e.added_paths || 0), 0)
    return (sum / entries.value.length).toFixed(1)
  })

  const avgRemoved = computed(() => {
    if (!entries.value.length) return '0'
    const sum = entries.value.reduce((acc, e) => acc + (e.removed_paths || 0), 0)
    return (sum / entries.value.length).toFixed(1)
  })

  const avgUnchanged = computed(() => {
    if (!entries.value.length) return '0'
    const sum = entries.value.reduce((acc, e) => acc + (e.unchanged_paths || 0), 0)
    return (sum / entries.value.length).toFixed(1)
  })

  return {
    avgAdded,
    avgRemoved,
    avgUnchanged
  }
}

/**
 * RosetteCompareHistory presets composable.
 */
import { computed, watch, type Ref, type ComputedRef } from 'vue'
import type { CompareHistoryEntry, PresetBucket, PairStats } from './rosetteCompareTypes'

export interface RosetteComparePresetsReturn {
  presetBuckets: ComputedRef<PresetBucket[]>
  presetCompareAEntries: ComputedRef<CompareHistoryEntry[]>
  presetCompareBEntries: ComputedRef<CompareHistoryEntry[]>
  pairStats: ComputedRef<PairStats | null>
  normalizePresetName: (e: CompareHistoryEntry) => string
  formatDelta: (delta: number) => string
}

/**
 * Normalize preset name for grouping.
 */
function normalizePresetName(e: CompareHistoryEntry): string {
  return (e.preset && e.preset.trim()) || '(none)'
}

/**
 * Format delta with sign.
 */
function formatDelta(delta: number): string {
  if (delta === 0) return '0.0'
  const s = delta.toFixed(1)
  return delta > 0 ? `+${s}` : s
}

/**
 * Calculate average metric from entries.
 */
function averageMetric(
  data: CompareHistoryEntry[],
  key: keyof CompareHistoryEntry
): number {
  if (!data.length) return 0
  const nums = data.map((e) => {
    const v = e[key]
    return typeof v === 'number' ? v : 0
  })
  const sum = nums.reduce((acc, v) => acc + v, 0)
  return sum / data.length
}

export function useRosetteComparePresets(
  entries: Ref<CompareHistoryEntry[]>,
  presetCompareA: Ref<string | null>,
  presetCompareB: Ref<string | null>
): RosetteComparePresetsReturn {
  /**
   * Group entries by preset name.
   */
  const presetBuckets = computed(() => {
    const map = new Map<string, CompareHistoryEntry[]>()
    for (const e of entries.value) {
      const key = normalizePresetName(e)
      if (!map.has(key)) {
        map.set(key, [])
      }
      map.get(key)!.push(e)
    }
    const sortedKeys = Array.from(map.keys()).sort()
    return sortedKeys.map((name) => ({
      name,
      entries: map.get(name)!
    }))
  })

  // Keep A/B in range when buckets change
  watch(
    () => presetBuckets.value,
    (buckets) => {
      if (!buckets.length) {
        presetCompareA.value = null
        presetCompareB.value = null
        return
      }
      const names = buckets.map((b) => b.name)
      if (!presetCompareA.value || !names.includes(presetCompareA.value)) {
        presetCompareA.value = names[0]
      }
      if (names.length > 1) {
        if (!presetCompareB.value || !names.includes(presetCompareB.value)) {
          presetCompareB.value = names[1]
        }
      } else {
        presetCompareB.value = null
      }
    },
    { immediate: true }
  )

  /**
   * Entries for preset A.
   */
  const presetCompareAEntries = computed(() => {
    if (!presetCompareA.value) return []
    return entries.value.filter(
      (e) => normalizePresetName(e) === presetCompareA.value
    )
  })

  /**
   * Entries for preset B.
   */
  const presetCompareBEntries = computed(() => {
    if (!presetCompareB.value) return []
    return entries.value.filter(
      (e) => normalizePresetName(e) === presetCompareB.value
    )
  })

  /**
   * Compute A/B comparison stats.
   */
  const pairStats = computed(() => {
    if (!presetCompareA.value || !presetCompareB.value) return null
    if (
      !presetCompareAEntries.value.length &&
      !presetCompareBEntries.value.length
    ) {
      return null
    }

    const aName = presetCompareA.value
    const bName = presetCompareB.value

    const aAdded = averageMetric(presetCompareAEntries.value, 'added_paths')
    const bAdded = averageMetric(presetCompareBEntries.value, 'added_paths')
    const deltaAdded = bAdded - aAdded

    const aRemoved = averageMetric(presetCompareAEntries.value, 'removed_paths')
    const bRemoved = averageMetric(presetCompareBEntries.value, 'removed_paths')
    const deltaRemoved = bRemoved - aRemoved

    const aUnchanged = averageMetric(
      presetCompareAEntries.value,
      'unchanged_paths'
    )
    const bUnchanged = averageMetric(
      presetCompareBEntries.value,
      'unchanged_paths'
    )
    const deltaUnchanged = bUnchanged - aUnchanged

    return {
      aName,
      bName,
      aAdded,
      bAdded,
      deltaAdded,
      aRemoved,
      bRemoved,
      deltaRemoved,
      aUnchanged,
      bUnchanged,
      deltaUnchanged
    }
  })

  return {
    presetBuckets,
    presetCompareAEntries,
    presetCompareBEntries,
    pairStats,
    normalizePresetName,
    formatDelta
  }
}

/**
 * JobIntHistory stats composable.
 */
import { computed } from 'vue'
import type { Ref, ComputedRef } from 'vue'
import type { JobIntLogEntry } from './jobIntHistoryTypes'

// ============================================================================
// Types
// ============================================================================

export interface JobIntHistoryStatsReturn {
  helicalCount: ComputedRef<number>
  nonHelicalCount: ComputedRef<number>
  helicalPct: ComputedRef<number>
  nonHelicalPct: ComputedRef<number>
  avgTimeSeconds: ComputedRef<number | null>
  avgTimeLabel: ComputedRef<string>
  avgMaxDevPct: ComputedRef<number | null>
}

// ============================================================================
// Composable
// ============================================================================

export function useJobIntHistoryStats(
  items: Ref<JobIntLogEntry[]>
): JobIntHistoryStatsReturn {
  const helicalCount = computed(() => {
    return items.value.filter((e) => e.use_helical).length
  })

  const nonHelicalCount = computed(() => {
    return items.value.filter((e) => !e.use_helical).length
  })

  const helicalPct = computed(() => {
    if (items.value.length === 0) return 0
    return (helicalCount.value / items.value.length) * 100
  })

  const nonHelicalPct = computed(() => {
    if (items.value.length === 0) return 0
    return (nonHelicalCount.value / items.value.length) * 100
  })

  const avgTimeSeconds = computed(() => {
    const vals = items.value
      .map((e) => e.sim_time_s)
      .filter((v): v is number => v != null && !Number.isNaN(v))
    if (vals.length === 0) return null
    const sum = vals.reduce((a, b) => a + b, 0)
    return sum / vals.length
  })

  const avgTimeLabel = computed(() => {
    const v = avgTimeSeconds.value
    if (v == null) return '—'
    if (v < 1) return `${(v * 1000).toFixed(0)} ms`
    if (v < 60) return `${v.toFixed(2)} s`
    const m = Math.floor(v / 60)
    const s = v - m * 60
    return `${m}m ${s.toFixed(0)}s`
  })

  const avgMaxDevPct = computed(() => {
    const vals = items.value
      .map((e) => e.sim_max_dev_pct)
      .filter((v): v is number => v != null && !Number.isNaN(v))
    if (vals.length === 0) return null
    const sum = vals.reduce((a, b) => a + b, 0)
    return sum / vals.length
  })

  return {
    helicalCount,
    nonHelicalCount,
    helicalPct,
    nonHelicalPct,
    avgTimeSeconds,
    avgTimeLabel,
    avgMaxDevPct
  }
}

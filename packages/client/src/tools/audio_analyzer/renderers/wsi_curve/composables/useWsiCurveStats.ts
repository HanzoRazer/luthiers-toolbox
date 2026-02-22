/**
 * WsiCurveRenderer stats composable.
 */
import { computed, type ComputedRef } from 'vue'
import type { WsiRow } from './wsiCurveTypes'

export interface WsiCurveStatsReturn {
  freqRange: ComputedRef<string | null>
  maxWsiHz: ComputedRef<number | null>
  maxWsi: ComputedRef<number>
  rawPreview: ComputedRef<string>
}

export function useWsiCurveStats(
  rows: ComputedRef<WsiRow[]>
): WsiCurveStatsReturn {
  const freqRange = computed(() => {
    if (rows.value.length === 0) return null
    const min = rows.value[0].freq_hz
    const max = rows.value[rows.value.length - 1].freq_hz
    return `${min.toFixed(0)}–${max.toFixed(0)} Hz`
  })

  const maxWsiHz = computed<number | null>(() => {
    if (rows.value.length === 0) return null
    let best = rows.value[0]
    for (const r of rows.value) if (r.wsi > best.wsi) best = r
    return best.freq_hz
  })

  const maxWsi = computed<number>(() => {
    if (rows.value.length === 0) return 0
    return Math.max(...rows.value.map((r) => r.wsi))
  })

  const rawPreview = computed(() => {
    const slice = rows.value.slice(0, 25)
    return JSON.stringify(slice, null, 2)
  })

  return {
    freqRange,
    maxWsiHz,
    maxWsi,
    rawPreview
  }
}

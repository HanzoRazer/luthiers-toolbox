/**
 * WsiCurveRenderer selection composable.
 */
import { computed, type ComputedRef } from 'vue'
import type { WsiRow } from './wsiCurveTypes'

export interface WsiCurveSelectionReturn {
  nearestRowByFreq: (freqHz: number) => WsiRow | null
  nearestRowByLabel: (label: any) => WsiRow | null
  selectedNearest: ComputedRef<WsiRow | null>
  boolText: (v: boolean) => string
}

export function useWsiCurveSelection(
  rows: ComputedRef<WsiRow[]>,
  selectedFreqHz: () => number | null | undefined
): WsiCurveSelectionReturn {
  /**
   * Find nearest row by frequency.
   */
  function nearestRowByFreq(freqHz: number): WsiRow | null {
    const r = rows.value
    if (r.length === 0) return null
    let best = r[0]
    let bestD = Math.abs(r[0].freq_hz - freqHz)
    for (const row of r) {
      const d = Math.abs(row.freq_hz - freqHz)
      if (d < bestD) {
        bestD = d
        best = row
      }
    }
    return best
  }

  /**
   * Find nearest row by label (for tooltip callbacks).
   */
  function nearestRowByLabel(label: any): WsiRow | null {
    const f = Number(label)
    if (!Number.isFinite(f)) return null
    return nearestRowByFreq(f)
  }

  /**
   * Get nearest row to selected frequency.
   */
  const selectedNearest = computed<WsiRow | null>(() => {
    const f = selectedFreqHz() ?? null
    if (!f || !Number.isFinite(f)) return null
    return nearestRowByFreq(f)
  })

  /**
   * Format boolean for display.
   */
  function boolText(v: boolean): string {
    return v ? 'true' : 'false'
  }

  return {
    nearestRowByFreq,
    nearestRowByLabel,
    selectedNearest,
    boolText
  }
}

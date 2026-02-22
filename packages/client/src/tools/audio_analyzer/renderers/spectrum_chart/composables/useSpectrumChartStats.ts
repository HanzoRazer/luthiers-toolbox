/**
 * SpectrumChartRenderer stats composable.
 */
import { computed, type ComputedRef } from 'vue'
import type { SpectrumRow } from './spectrumChartTypes'

// ============================================================================
// Types
// ============================================================================

export interface SpectrumChartStatsReturn {
  dataPoints: ComputedRef<number>
  peakFreq: ComputedRef<number | null>
  peakMag: ComputedRef<number>
  freqRange: ComputedRef<string | null>
  nearestMagAtFreq: (freqHz: number) => number
}

// ============================================================================
// Composable
// ============================================================================

export function useSpectrumChartStats(
  parsedData: ComputedRef<SpectrumRow[]>
): SpectrumChartStatsReturn {
  /**
   * Number of data points.
   */
  const dataPoints = computed(() => parsedData.value.length)

  /**
   * Peak frequency (frequency with highest magnitude).
   */
  const peakFreq = computed<number | null>(() => {
    if (parsedData.value.length === 0) return null
    let maxRow = parsedData.value[0]
    for (const row of parsedData.value) {
      if (row.H_mag > maxRow.H_mag) maxRow = row
    }
    return maxRow.freq_hz
  })

  /**
   * Peak magnitude.
   */
  const peakMag = computed<number>(() => {
    if (parsedData.value.length === 0) return 0
    return Math.max(...parsedData.value.map((r) => r.H_mag))
  })

  /**
   * Frequency range string.
   */
  const freqRange = computed<string | null>(() => {
    if (parsedData.value.length === 0) return null
    const freqs = parsedData.value.map((r) => r.freq_hz)
    const min = Math.min(...freqs)
    const max = Math.max(...freqs)
    return `${min.toFixed(0)}–${max.toFixed(0)} Hz`
  })

  /**
   * Find nearest magnitude at a given frequency.
   */
  function nearestMagAtFreq(freqHz: number): number {
    const rows = parsedData.value
    if (rows.length === 0) return 0
    let best = rows[0]
    let bestD = Math.abs(rows[0].freq_hz - freqHz)
    for (const r of rows) {
      const d = Math.abs(r.freq_hz - freqHz)
      if (d < bestD) {
        bestD = d
        best = r
      }
    }
    return best.H_mag
  }

  return {
    dataPoints,
    peakFreq,
    peakMag,
    freqRange,
    nearestMagAtFreq
  }
}

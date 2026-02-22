/**
 * TransferFunctionRenderer stats composable.
 */
import { computed, type Ref, type ComputedRef } from 'vue'
import type { ParsedODS, TransferFunctionPoint, PeakInfo } from './transferFunctionTypes'

export interface TransferFunctionStatsReturn {
  hasData: ComputedRef<boolean>
  dataPoints: ComputedRef<number>
  chartData: ComputedRef<TransferFunctionPoint[]>
  peakInfo: ComputedRef<PeakInfo | null>
  freqRange: ComputedRef<string | null>
  odsMetadata: ComputedRef<string | null>
  toDb: (linear: number) => number
}

/**
 * Convert linear magnitude to dB.
 */
function toDb(linear: number): number {
  if (linear <= 0) return -100  // Floor for log(0)
  return 20 * Math.log10(linear)
}

export function useTransferFunctionStats(
  parsedData: ComputedRef<ParsedODS>,
  dbScale: Ref<boolean>
): TransferFunctionStatsReturn {
  const hasData = computed(() => parsedData.value.points.length > 0)
  const dataPoints = computed(() => parsedData.value.points.length)

  /**
   * Chart data with optional dB conversion.
   */
  const chartData = computed(() => {
    const points = parsedData.value.points
    if (dbScale.value) {
      return points.map((p) => ({
        freq: p.freq,
        mag: toDb(p.mag),
        phase: p.phase
      }))
    }
    return points
  })

  /**
   * Peak frequency and magnitude.
   */
  const peakInfo = computed(() => {
    const data = chartData.value
    if (data.length === 0) return null

    let maxIdx = 0
    for (let i = 1; i < data.length; i++) {
      if (data[i].mag > data[maxIdx].mag) maxIdx = i
    }
    return { freq: data[maxIdx].freq, mag: data[maxIdx].mag }
  })

  /**
   * Frequency range string.
   */
  const freqRange = computed(() => {
    const points = parsedData.value.points
    if (points.length === 0) return null
    const min = points[0].freq
    const max = points[points.length - 1].freq
    return `${min.toFixed(0)}–${max.toFixed(0)} Hz`
  })

  /**
   * ODS metadata display string.
   */
  const odsMetadata = computed(() => {
    const meta = parsedData.value.metadata
    if (!meta) return null
    const parts: string[] = []
    if (meta.analysisType) parts.push(meta.analysisType)
    if (meta.nModes) parts.push(`${meta.nModes} modes`)
    return parts.length > 0 ? parts.join(' · ') : null
  })

  return {
    hasData,
    dataPoints,
    chartData,
    peakInfo,
    freqRange,
    odsMetadata,
    toDb
  }
}

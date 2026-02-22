/**
 * SpectrumChartRenderer parsing composable.
 */
import { computed, type Ref, type ComputedRef } from 'vue'
import type { SpectrumRow, PeakData } from './spectrumChartTypes'
import { MAX_CHART_POINTS } from './spectrumChartTypes'

// ============================================================================
// Types
// ============================================================================

export interface SpectrumChartParsingReturn {
  parsedData: ComputedRef<SpectrumRow[]>
  parsedPeaks: ComputedRef<PeakData[]>
  isDecimated: ComputedRef<boolean>
}

// ============================================================================
// Composable
// ============================================================================

export function useSpectrumChartParsing(
  bytes: () => Uint8Array,
  peaksBytes: () => Uint8Array | null | undefined,
  parseError: Ref<string | null>,
  originalRowCount: Ref<number>
): SpectrumChartParsingReturn {
  /**
   * Parse CSV data from bytes.
   */
  const parsedData = computed<SpectrumRow[]>(() => {
    parseError.value = null
    originalRowCount.value = 0
    try {
      const text = new TextDecoder('utf-8').decode(bytes())
      const lines = text.trim().split(/\r?\n/)
      if (lines.length < 2) {
        parseError.value = 'CSV has no data rows'
        return []
      }
      // Parse header
      const header = lines[0].toLowerCase().split(',').map((h) => h.trim())
      const freqIdx = header.findIndex((h) => h.includes('freq'))
      const magIdx = header.findIndex((h) => h.includes('mag') || h === 'h_mag')
      const cohIdx = header.findIndex((h) => h.includes('coh'))
      const phaseIdx = header.findIndex((h) => h.includes('phase'))

      if (freqIdx === -1 || magIdx === -1) {
        parseError.value = `Missing required columns. Found: ${header.join(', ')}`
        return []
      }

      // Parse data rows
      const rows: SpectrumRow[] = []
      for (let i = 1; i < lines.length; i++) {
        const cells = lines[i].split(',')
        const freq = parseFloat(cells[freqIdx])
        const mag = parseFloat(cells[magIdx])
        const coh = cohIdx >= 0 ? parseFloat(cells[cohIdx]) : 0
        const phase = phaseIdx >= 0 ? parseFloat(cells[phaseIdx]) : 0
        if (!isNaN(freq) && !isNaN(mag)) {
          rows.push({ freq_hz: freq, H_mag: mag, coherence: coh, phase_deg: phase })
        }
      }

      // Track original count before decimation
      originalRowCount.value = rows.length

      // Decimate if too large for smooth Chart.js rendering
      if (rows.length > MAX_CHART_POINTS) {
        const step = Math.ceil(rows.length / MAX_CHART_POINTS)
        return rows.filter((_, i) => i % step === 0)
      }

      return rows
    } catch (e) {
      parseError.value = e instanceof Error ? e.message : String(e)
      return []
    }
  })

  /**
   * Whether data was decimated.
   */
  const isDecimated = computed(() => originalRowCount.value > MAX_CHART_POINTS)

  /**
   * Parse peaks from sibling analysis.json (peaksBytes).
   */
  const parsedPeaks = computed<PeakData[]>(() => {
    const pb = peaksBytes()
    if (!pb || pb.length === 0) return []
    try {
      const text = new TextDecoder('utf-8').decode(pb)
      const json = JSON.parse(text)
      // Support various analysis.json structures:
      // 1. { peaks: [{ freq_hz, ... }] }
      // 2. { peaks: [{ frequency_hz, ... }] }
      // 3. [{ freq_hz, ... }] (direct array)
      const arr = Array.isArray(json) ? json : (json.peaks ?? [])
      return arr
        .filter((p: any) => typeof p.freq_hz === 'number' || typeof p.frequency_hz === 'number')
        .map((p: any, i: number) => ({
          freq_hz: p.freq_hz ?? p.frequency_hz,
          label: p.label ?? p.note ?? `P${i + 1}`,
          peakIndex: i,
          raw: p
        }))
    } catch {
      return []
    }
  })

  return {
    parsedData,
    parsedPeaks,
    isDecimated
  }
}

/**
 * WsiCurveRenderer CSV parsing composable.
 */
import { computed, type Ref, type ComputedRef } from 'vue'
import type { WsiRow } from './wsiCurveTypes'

export interface WsiCurveParsingReturn {
  rows: ComputedRef<WsiRow[]>
}

/**
 * Parse boolean from CSV string value.
 */
function parseBool(v: string): boolean {
  const s = (v ?? '').trim().toLowerCase()
  return s === 'true' || s === '1' || s === 'yes' || s === 'y'
}

export function useWsiCurveParsing(
  bytes: () => Uint8Array,
  parseError: Ref<string | null>
): WsiCurveParsingReturn {
  const rows = computed<WsiRow[]>(() => {
    parseError.value = null
    try {
      const text = new TextDecoder('utf-8').decode(bytes())
      const lines = text.trim().split(/\r?\n/)
      if (lines.length < 2) {
        parseError.value = 'CSV has no data rows'
        return []
      }

      const header = lines[0].split(',').map((h) => h.trim().toLowerCase())
      const idx = (name: string) => header.findIndex((h) => h === name)

      const freqIdx = idx('freq_hz')
      const wsiIdx = idx('wsi')
      const locIdx = idx('loc')
      const gradIdx = idx('grad')
      const phaseIdx = idx('phase_disorder')
      const cohIdx = idx('coh_mean')
      const admIdx = idx('admissible')

      // Only freq_hz and wsi are required for charting
      if (freqIdx === -1 || wsiIdx === -1) {
        parseError.value = `Missing required columns. Found: ${header.join(', ')}`
        return []
      }

      const out: WsiRow[] = []
      for (let i = 1; i < lines.length; i++) {
        const cells = lines[i].split(',')
        const freq = parseFloat(cells[freqIdx])
        const wsi = parseFloat(cells[wsiIdx])
        if (!Number.isFinite(freq) || !Number.isFinite(wsi)) continue

        const loc = locIdx >= 0 ? parseFloat(cells[locIdx]) : 0
        const grad = gradIdx >= 0 ? parseFloat(cells[gradIdx]) : 0
        const phase_disorder = phaseIdx >= 0 ? parseFloat(cells[phaseIdx]) : 0
        const coh_mean = cohIdx >= 0 ? parseFloat(cells[cohIdx]) : 0
        const admissible = admIdx >= 0 ? parseBool(cells[admIdx]) : false

        out.push({
          freq_hz: freq,
          wsi: wsi,
          loc: Number.isFinite(loc) ? loc : 0,
          grad: Number.isFinite(grad) ? grad : 0,
          phase_disorder: Number.isFinite(phase_disorder) ? phase_disorder : 0,
          coh_mean: Number.isFinite(coh_mean) ? coh_mean : 0,
          admissible
        })
      }

      // Ensure increasing freq for sane charting
      out.sort((a, b) => a.freq_hz - b.freq_hz)
      return out
    } catch (e: unknown) {
      parseError.value = e instanceof Error ? e.message : String(e)
      return []
    }
  })

  return { rows }
}

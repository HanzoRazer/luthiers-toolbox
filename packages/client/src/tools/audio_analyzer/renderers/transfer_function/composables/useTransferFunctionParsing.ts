/**
 * TransferFunctionRenderer parsing composable.
 */
import { computed, ref, type Ref, type ComputedRef } from 'vue'
import type { TransferFunctionPoint, ParsedODS, ParsedODSMetadata } from './transferFunctionTypes'

export interface TransferFunctionParsingReturn {
  parsedData: ComputedRef<ParsedODS>
  parseError: Ref<string | null>
}

/**
 * Parse transfer function from JSON object.
 * Handles multiple formats from tap_tone_pi.
 */
function parseTransferFunction(json: unknown): ParsedODS {
  if (!json || typeof json !== 'object') {
    throw new Error('Invalid JSON: expected object')
  }

  const obj = json as Record<string, unknown>
  let points: TransferFunctionPoint[] = []
  const metadata: ParsedODSMetadata = {}

  // ─── Format 1: Arrays (freq, mag, phase as parallel arrays) ───
  if (Array.isArray(obj.frequencies) || Array.isArray(obj.freq)) {
    const freqs = (obj.frequencies || obj.freq || obj.f) as number[]
    const mags = (obj.magnitude || obj.mag || obj.H_mag || obj.amplitude) as number[]
    const phases = (obj.phase || obj.phase_deg || obj.phi) as number[]

    if (!Array.isArray(freqs) || !Array.isArray(mags)) {
      throw new Error('Missing frequency or magnitude arrays')
    }

    points = freqs.map((freq, i) => ({
      freq,
      mag: mags[i] ?? 0,
      phase: phases?.[i] ?? 0
    }))
  }

  // ─── Format 2: Array of objects [{freq, mag, phase}, ...] ───
  else if (Array.isArray(obj.data) || Array.isArray(obj.points) || Array.isArray(obj.transfer_function)) {
    const arr = (obj.data || obj.points || obj.transfer_function) as Record<string, unknown>[]

    points = arr.map((item) => ({
      freq: Number(item.freq ?? item.frequency ?? item.f ?? 0),
      mag: Number(item.mag ?? item.magnitude ?? item.H_mag ?? item.amplitude ?? 0),
      phase: Number(item.phase ?? item.phase_deg ?? item.phi ?? 0)
    }))
  }

  // ─── Format 3: ODS snapshot with modes ───
  else if (obj.modes && Array.isArray(obj.modes)) {
    const modes = obj.modes as Record<string, unknown>[]
    points = modes.map((mode) => ({
      freq: Number(mode.freq ?? mode.frequency ?? 0),
      mag: Number(mode.amplitude ?? mode.mag ?? mode.H ?? 1),
      phase: Number(mode.phase ?? 0)
    }))

    metadata.analysisType = 'ODS Modal'
    metadata.nModes = modes.length
  }

  // ─── Format 4: FRF (Frequency Response Function) ───
  else if (obj.frf || obj.H) {
    const frf = (obj.frf || obj.H) as Record<string, unknown>
    if (Array.isArray(frf.real) && Array.isArray(frf.imag)) {
      const real = frf.real as number[]
      const imag = frf.imag as number[]
      const freqs = (frf.freq || obj.freq || obj.frequencies) as number[]

      if (!Array.isArray(freqs)) {
        throw new Error('FRF format requires frequencies array')
      }

      points = freqs.map((freq, i) => {
        const r = real[i] ?? 0
        const im = imag[i] ?? 0
        return {
          freq,
          mag: Math.sqrt(r * r + im * im),
          phase: Math.atan2(im, r) * (180 / Math.PI)
        }
      })
    }
  }

  // ─── Fallback: Try to find any array with freq-like data ───
  if (points.length === 0) {
    const keys = Object.keys(obj)
    for (const key of keys) {
      if (Array.isArray(obj[key]) && (obj[key] as unknown[]).length > 0) {
        const arr = obj[key] as unknown[]
        if (typeof arr[0] === 'object' && arr[0] !== null) {
          const first = arr[0] as Record<string, unknown>
          if ('freq' in first || 'frequency' in first || 'f' in first) {
            points = arr.map((item) => {
              const it = item as Record<string, unknown>
              return {
                freq: Number(it.freq ?? it.frequency ?? it.f ?? 0),
                mag: Number(it.mag ?? it.magnitude ?? it.H_mag ?? it.amplitude ?? 1),
                phase: Number(it.phase ?? it.phase_deg ?? 0)
              }
            })
            break
          }
        }
      }
    }
  }

  // Extract metadata if present
  if (obj.analysis_type) metadata.analysisType = String(obj.analysis_type)
  if (obj.n_modes) metadata.nModes = Number(obj.n_modes)
  if (obj.freq_min) metadata.freqMin = Number(obj.freq_min)
  if (obj.freq_max) metadata.freqMax = Number(obj.freq_max)

  // Filter out invalid points and sort by frequency
  points = points
    .filter((p) => !isNaN(p.freq) && !isNaN(p.mag) && p.freq > 0)
    .sort((a, b) => a.freq - b.freq)

  return { points, metadata }
}

export function useTransferFunctionParsing(
  bytes: () => Uint8Array
): TransferFunctionParsingReturn {
  const parseError = ref<string | null>(null)

  const parsedData = computed<ParsedODS>(() => {
    parseError.value = null
    try {
      const text = new TextDecoder('utf-8').decode(bytes())
      const json = JSON.parse(text)
      return parseTransferFunction(json)
    } catch (e) {
      parseError.value = e instanceof Error ? e.message : String(e)
      return { points: [] }
    }
  })

  return {
    parsedData,
    parseError
  }
}

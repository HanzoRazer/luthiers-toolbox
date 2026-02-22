/**
 * AudioAnalyzer peak selection composable.
 */
import { computed } from 'vue'
import type { Ref, ComputedRef } from 'vue'
import { findSiblingPeaksRelpath } from '@/tools/audio_analyzer/packHelpers'
import type { SelectedPeak, WsiRow, SelectionSource } from './audioAnalyzerTypes'

// ============================================================================
// Types
// ============================================================================

export interface AudioAnalyzerSelectionReturn {
  cursorFreqHz: ComputedRef<number | null>
  selectionSource: ComputedRef<SelectionSource>
  selectedWsiRow: ComputedRef<WsiRow | null>
  clearSelectedPeak: () => void
  clearCursorOnly: () => void
  onPeakSelected: (payload: any) => void
  fmtNum: (v: unknown) => string
  fmtBool: (v: unknown) => string
}

// ============================================================================
// Helpers
// ============================================================================

function pointIdFromSpectrumRelpath(relpath: string): string | null {
  // spectra/points/{POINT_ID}/spectrum.csv
  const m = relpath.match(/^spectra\/points\/([^/]+)\/spectrum\.csv$/)
  return m?.[1] ?? null
}

// ============================================================================
// Composable
// ============================================================================

export function useAudioAnalyzerSelection(
  selectedPeak: Ref<SelectedPeak | null>,
  activePath: Ref<string>,
  audioJumpError: Ref<string>,
  emitUserAction: (action: string, data: any) => void
): AudioAnalyzerSelectionReturn {
  // Wave 6A "linked cursor" pill should persist across file changes
  const cursorFreqHz = computed<number | null>(() => {
    const f = selectedPeak.value?.freq_hz
    return Number.isFinite(f) ? f! : null
  })

  const selectionSource = computed<SelectionSource>(() => {
    const rp = selectedPeak.value?.spectrumRelpath ?? ''
    if (rp.endsWith('/spectrum.csv')) return 'spectrum'
    if (rp === 'wolf/wsi_curve.csv') return 'wsi'
    return 'unknown'
  })

  const selectedWsiRow = computed<WsiRow | null>(() => {
    if (!selectedPeak.value) return null
    if (selectionSource.value !== 'wsi') return null
    const raw = selectedPeak.value.raw
    if (!raw || typeof raw !== 'object') return null
    return raw as WsiRow
  })

  function fmtNum(v: unknown): string {
    const n = Number(v)
    return Number.isFinite(n) ? n.toFixed(3) : '—'
  }

  function fmtBool(v: unknown): string {
    if (typeof v === 'boolean') return v ? 'true' : 'false'
    return '—'
  }

  function clearSelectedPeak(): void {
    selectedPeak.value = null
    audioJumpError.value = ''
  }

  function clearCursorOnly(): void {
    // Keep details panel context but clear the linked cursor frequency.
    if (!selectedPeak.value) return
    selectedPeak.value = { ...selectedPeak.value, freq_hz: NaN }
    // We treat NaN as "no cursor" in the renderer binding below by mapping to null.
  }

  function onPeakSelected(payload: any): void {
    audioJumpError.value = ''
    const spectrumRelpath =
      typeof payload?.spectrumRelpath === 'string' ? payload.spectrumRelpath : activePath.value
    const peaksRelpath = findSiblingPeaksRelpath(spectrumRelpath) ?? ''
    const pointId = pointIdFromSpectrumRelpath(spectrumRelpath)
    const freq_hz = Number(payload?.freq_hz)
    if (!Number.isFinite(freq_hz)) return

    // Agentic M1: emit peak selection
    emitUserAction('peak_selected', { freq_hz, spectrum: activePath.value })

    const raw = payload?.raw ?? payload
    let rawPretty = ''
    try {
      rawPretty = JSON.stringify(raw, null, 2)
    } catch {
      rawPretty = String(raw)
    }

    selectedPeak.value = {
      pointId,
      spectrumRelpath,
      peaksRelpath,
      peakIndex: Number(payload?.peakIndex ?? -1),
      freq_hz,
      label: typeof payload?.label === 'string' ? payload.label : undefined,
      raw,
      rawPretty
    }
  }

  return {
    cursorFreqHz,
    selectionSource,
    selectedWsiRow,
    clearSelectedPeak,
    clearCursorOnly,
    onPeakSelected,
    fmtNum,
    fmtBool
  }
}

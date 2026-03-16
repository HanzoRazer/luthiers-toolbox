/**
 * useTension — Core String Tension Physics Composable
 *
 * The Production Shop — String Tension Calculator
 *
 * Physics formula: T = UW × (2LF)² / 386.4
 *   T     = tension (lbs)
 *   UW    = unit weight (lbs/in)
 *   L     = scale length (in)
 *   F     = frequency (Hz)
 *   386.4 = gravitational acceleration (in/s²)
 *
 * Note convention: scientific pitch notation (A4 = 440 Hz)
 */

import { ref, computed, readonly } from 'vue'
import type { Ref } from 'vue'
import type {
  StringSpec,
  StringResult,
  SetAnalysis,
  TensionUnit,
  InstrumentType,
  NoteName,
} from './types'
import { INSTRUMENT_TYPES, CARRUTH_MIN_DEG, PRACTICAL_MIN_PROJECTION_MM, STEEP_MAX_DEG } from './types'
import { getUnitWeight } from './uwTable'
import { PRESETS } from './presets'
import type { StringSetPreset } from './types'

// ============================================================================
// CONSTANTS
// ============================================================================

const G = 386.4  // in/s² — gravitational acceleration

const NOTE_NAMES: NoteName[] = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

// ============================================================================
// PURE FUNCTIONS
// ============================================================================

/**
 * MIDI note number for a given note name and octave.
 * A4 = MIDI 69 = 440 Hz
 */
function noteToMidi(note: NoteName, octave: number): number {
  return NOTE_NAMES.indexOf(note) + (octave + 1) * 12
}

/**
 * Frequency (Hz) for a given note and octave.
 * Reference: A4 = 440 Hz, equal temperament.
 */
export function noteToFrequency(note: NoteName, octave: number): number {
  return 440 * Math.pow(2, (noteToMidi(note, octave) - 69) / 12)
}

/**
 * String tension (lbs) from unit weight, scale length, and frequency.
 * Formula: T = UW × (2 × L × F)² / G
 */
export function calcTension(unitWeightLbIn: number, scaleLengthIn: number, frequencyHz: number): number {
  return unitWeightLbIn * Math.pow(2 * scaleLengthIn * frequencyHz, 2) / G
}

/**
 * Balance score: 1.0 = perfectly matched set, 0.0 = wildly unbalanced.
 * Based on coefficient of variation, penalized at 2.5×.
 */
export function calcBalanceScore(tensionsLbs: number[]): number {
  if (tensionsLbs.length < 2) return 1.0
  const mean = tensionsLbs.reduce((a, b) => a + b, 0) / tensionsLbs.length
  if (mean === 0) return 0
  const cv = Math.sqrt(
    tensionsLbs.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / tensionsLbs.length
  ) / mean
  return Math.max(0, Math.min(1, 1 - cv * 2.5))
}

// ============================================================================
// COMPOSABLE
// ============================================================================

export function useTension() {

  // --------------------------------------------------------------------------
  // State
  // --------------------------------------------------------------------------

  const instrumentType = ref<InstrumentType>('acoustic_pin')
  const globalScaleLength = ref(25.5)     // inches
  const multiScale = ref(false)
  const unit = ref<TensionUnit>('lbs')

  /** Break angle used for topLoad calculation (degrees) */
  const breakAngleDeg = ref(20.0)
  /**
   * Whether breakAngleDeg was sourced from the API (computed)
   * or entered manually. Affects display only — not calculation.
   */
  const breakAngleIsComputed = ref(false)

  const activePresetId = ref<string>('g9')

  /** Current string set — always has sequential ids 0..n-1 */
  const strings = ref<StringSpec[]>(
    buildStringsFromPreset(PRESETS.find(p => p.id === 'g9')!)
  )

  // --------------------------------------------------------------------------
  // Derived instrument type info
  // --------------------------------------------------------------------------

  const instrumentTypeInfo = computed(() =>
    INSTRUMENT_TYPES.find(t => t.id === instrumentType.value)!
  )

  const useCarruthThresholds = computed(() => instrumentTypeInfo.value.useCarruthThresholds)

  // --------------------------------------------------------------------------
  // Per-string computation
  // --------------------------------------------------------------------------

  const results = computed<StringResult[]>(() =>
    strings.value.map(s => {
      const effectiveScale = multiScale.value ? s.scaleLength : globalScaleLength.value
      const freq = noteToFrequency(s.note, s.octave)
      const uw = s.uwOverride !== undefined ? s.uwOverride : getUnitWeight(s.gauge, s.material)
      const tensionLbs = calcTension(uw, effectiveScale, freq)

      return {
        id: s.id,
        tensionLbs,
        tensionN: tensionLbs * 4.44822,
        tensionKgf: tensionLbs * 0.453592,
        unitWeight: uw,
        isOverride: s.uwOverride !== undefined,
        frequency: freq,
        effectiveScaleLength: effectiveScale,
      }
    })
  )

  // --------------------------------------------------------------------------
  // Set-level analysis
  // --------------------------------------------------------------------------

  const setAnalysis = computed<SetAnalysis>(() => {
    const totalLbs = results.value.reduce((a, r) => a + r.tensionLbs, 0)
    const avgLbs = results.value.length > 0 ? totalLbs / results.value.length : 0
    const balance = calcBalanceScore(results.value.map(r => r.tensionLbs))
    const breakRad = (breakAngleDeg.value * Math.PI) / 180

    return {
      strings: results.value,
      totalTensionLbs: totalLbs,
      avgTensionLbs: avgLbs,
      balanceScore: balance,
      neckLoadLbs: totalLbs,
      topLoadLbs: totalLbs * Math.sin(breakRad),
    }
  })

  // --------------------------------------------------------------------------
  // Break angle adequacy (gated behind instrument type)
  // --------------------------------------------------------------------------

  const breakAngleAdequacy = computed(() => {
    if (!useCarruthThresholds.value) return null

    const deg = breakAngleDeg.value
    if (deg >= STEEP_MAX_DEG) return 'too_steep' as const
    if (deg < CARRUTH_MIN_DEG) return 'too_shallow' as const
    return 'adequate' as const
  })

  // --------------------------------------------------------------------------
  // Display formatting
  // --------------------------------------------------------------------------

  function formatTension(lbs: number): string {
    switch (unit.value) {
      case 'N':  return `${(lbs * 4.44822).toFixed(1)} N`
      case 'kg': return `${(lbs * 0.453592).toFixed(2)} kg`
      default:   return `${lbs.toFixed(2)} lb`
    }
  }

  function formatTensionAlt(lbs: number): string {
    switch (unit.value) {
      case 'lbs': return `${(lbs * 0.453592).toFixed(1)} kg`
      default:    return `${lbs.toFixed(2)} lb`
    }
  }

  // --------------------------------------------------------------------------
  // Preset loading
  // --------------------------------------------------------------------------

  function buildStringsFromPreset(preset: StringSetPreset): StringSpec[] {
    return preset.strings.map((s, i) => ({
      ...s,
      id: i,
      scaleLength: s.scaleLength ?? preset.scaleLength,
    }))
  }

  function loadPreset(presetId: string): void {
    const preset = PRESETS.find(p => p.id === presetId)
    if (!preset) return

    activePresetId.value = presetId
    globalScaleLength.value = preset.scaleLength
    multiScale.value = preset.multiScale ?? false
    strings.value = buildStringsFromPreset(preset)

    // Reset break angle to instrument type default when switching presets
    breakAngleIsComputed.value = false
    breakAngleDeg.value = instrumentTypeInfo.value.defaultBreakAngleDeg
  }

  // --------------------------------------------------------------------------
  // String editing
  // --------------------------------------------------------------------------

  function updateString(id: number, patch: Partial<Omit<StringSpec, 'id'>>): void {
    strings.value = strings.value.map(s => {
      if (s.id !== id) return s
      const updated = { ...s, ...patch }
      // Editing gauge or material clears the uwOverride (switches to calculated)
      if ('gauge' in patch || 'material' in patch) {
        delete updated.uwOverride
        delete updated.uwSource
      }
      return updated
    })
  }

  function addString(): void {
    const last = strings.value[strings.value.length - 1]
    strings.value = [
      ...strings.value,
      {
        id: strings.value.length,
        note: last?.note ?? 'E',
        octave: Math.max(0, (last?.octave ?? 2) - 1),
        gauge: Math.min(130, (last?.gauge ?? 42) + 10),
        material: last?.material ?? 'nickel_wound',
        scaleLength: globalScaleLength.value,
      },
    ]
  }

  function removeString(id: number): void {
    if (strings.value.length <= 1) return
    strings.value = strings.value
      .filter(s => s.id !== id)
      .map((s, i) => ({ ...s, id: i }))
  }

  // --------------------------------------------------------------------------
  // Break angle intake (called by useBreakAngle composable)
  // --------------------------------------------------------------------------

  function setBreakAngle(deg: number, fromApi: boolean): void {
    breakAngleDeg.value = deg
    breakAngleIsComputed.value = fromApi
  }

  // --------------------------------------------------------------------------
  // Expose
  // --------------------------------------------------------------------------

  return {
    // State
    instrumentType,
    globalScaleLength,
    multiScale,
    unit,
    breakAngleDeg,
    breakAngleIsComputed,
    activePresetId,
    strings,

    // Computed
    instrumentTypeInfo,
    useCarruthThresholds,
    results: readonly(results),
    setAnalysis: readonly(setAnalysis),
    breakAngleAdequacy,

    // Formatting
    formatTension,
    formatTensionAlt,

    // Actions
    loadPreset,
    updateString,
    addString,
    removeString,
    setBreakAngle,

    // Utilities (exposed for testing)
    noteToFrequency,
    calcTension,
    calcBalanceScore,

    // Data
    presets: PRESETS,
    noteNames: NOTE_NAMES,
  }
}

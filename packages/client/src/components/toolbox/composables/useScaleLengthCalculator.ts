/**
 * Composable for guitar scale length and string tension calculations.
 * Extracted from ScaleLengthDesigner.vue
 */
import { ref, computed } from 'vue'

export interface StringData {
  name: string
  note: string
  freq: number      // Hz
  gauge: number     // inches (e.g., 0.010)
}

export interface ScalePreset {
  name: string
  inches: number
  mm: number
}

export const SCALE_PRESETS: Record<string, ScalePreset> = {
  fender: { name: 'Fender', inches: 25.5, mm: 648 },
  gibson: { name: 'Gibson', inches: 24.75, mm: 629 },
  prs: { name: 'PRS', inches: 25.0, mm: 635 },
  short: { name: 'Short Scale', inches: 24.0, mm: 610 },
  baritone: { name: 'Baritone', inches: 27.0, mm: 686 },
  multiscale: { name: 'Multi-Scale (avg)', inches: 26.25, mm: 667 }
}

export const GAUGE_PRESETS: Record<string, number[]> = {
  light: [0.009, 0.011, 0.016, 0.024, 0.032, 0.042],
  regular: [0.010, 0.013, 0.017, 0.026, 0.036, 0.046],
  medium: [0.011, 0.014, 0.018, 0.028, 0.038, 0.049],
  heavy: [0.012, 0.016, 0.020, 0.032, 0.042, 0.053],
  baritone: [0.013, 0.017, 0.026, 0.036, 0.046, 0.062]
}

const DEFAULT_STRINGS: StringData[] = [
  { name: 'High E', note: 'E4', freq: 329.63, gauge: 0.010 },
  { name: 'B', note: 'B3', freq: 246.94, gauge: 0.013 },
  { name: 'G', note: 'G3', freq: 196.00, gauge: 0.017 },
  { name: 'D', note: 'D3', freq: 146.83, gauge: 0.026 },
  { name: 'A', note: 'A2', freq: 110.00, gauge: 0.036 },
  { name: 'Low E', note: 'E2', freq: 82.41, gauge: 0.046 }
]

/**
 * Calculate string tension using Mersenne's Law.
 * T = (μ × (2 × L × f)²) ÷ 4
 *
 * @param scaleInches - Scale length in inches
 * @param freq - String frequency in Hz
 * @param gauge - String gauge in inches
 * @returns Tension in pounds
 */
export function calculateStringTension(scaleInches: number, freq: number, gauge: number): number {
  // Linear mass density approximation for steel strings (empirical)
  // μ ≈ 0.00001294 × (gauge in inches)² lb/in
  const mu = 0.00001294 * Math.pow(gauge, 2)

  // Mersenne's Law: T = (μ × (2 × L × f)²) ÷ 4
  const tension = (mu * Math.pow(2 * scaleInches * freq, 2)) / 4

  return tension
}

export function useScaleLengthCalculator() {
  const customScale = ref(25.5)
  const scaleUnit = ref<'in' | 'mm'>('in')
  const strings = ref<StringData[]>(JSON.parse(JSON.stringify(DEFAULT_STRINGS)))

  // Convert scale to inches for calculations
  const scaleInches = computed(() => {
    return scaleUnit.value === 'mm' ? customScale.value / 25.4 : customScale.value
  })

  // Calculate tension for each string
  function getTension(stringIndex: number): number {
    const s = strings.value[stringIndex]
    if (!s) return 0
    return calculateStringTension(scaleInches.value, s.freq, s.gauge)
  }

  // Tension classification
  function getTensionClass(tension: number): 'low' | 'good' | 'high' {
    if (tension < 13) return 'low'
    if (tension > 18) return 'high'
    return 'good'
  }

  // Computed aggregates
  const tensions = computed(() => strings.value.map((_, idx) => getTension(idx)))

  const totalTension = computed(() => tensions.value.reduce((sum, t) => sum + t, 0))

  const averageTension = computed(() => {
    if (strings.value.length === 0) return 0
    return totalTension.value / strings.value.length
  })

  const tensionRange = computed(() => {
    if (tensions.value.length === 0) return 0
    return Math.max(...tensions.value) - Math.min(...tensions.value)
  })

  const tensionBalance = computed(() => {
    if (tensionRange.value < 2) return 'balanced'
    if (tensionRange.value < 4) return 'acceptable'
    return 'unbalanced'
  })

  // Apply a gauge preset
  function applyGaugeSet(preset: string) {
    const gauges = GAUGE_PRESETS[preset]
    if (gauges) {
      strings.value.forEach((s, idx) => {
        if (gauges[idx] !== undefined) {
          s.gauge = gauges[idx]
        }
      })
    }
  }

  // Apply a scale preset
  function applyScalePreset(presetKey: string) {
    const preset = SCALE_PRESETS[presetKey]
    if (preset) {
      customScale.value = preset.inches
      scaleUnit.value = 'in'
    }
  }

  // Reset to defaults
  function reset() {
    customScale.value = 25.5
    scaleUnit.value = 'in'
    strings.value = JSON.parse(JSON.stringify(DEFAULT_STRINGS))
  }

  return {
    // State
    customScale,
    scaleUnit,
    strings,

    // Computed
    scaleInches,
    tensions,
    totalTension,
    averageTension,
    tensionRange,
    tensionBalance,

    // Methods
    getTension,
    getTensionClass,
    applyGaugeSet,
    applyScalePreset,
    reset
  }
}

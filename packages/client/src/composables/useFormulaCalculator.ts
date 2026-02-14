/**
 * Generic composable for parameterised formula calculations with presets.
 * Wraps a set of named parameters, a user-supplied formula function,
 * preset configurations, and derived result classification.
 *
 * Extracted & genericized from useScaleLengthCalculator (Toolbox domain).
 */
import { ref, computed } from 'vue'

// ---- Public types ----

export interface FormulaParam {
  key: string
  label: string
  defaultValue: number
  unit?: string
}

export interface FormulaPreset {
  id: string
  label: string
  /** Overrides for parameter values. */
  values: Record<string, number>
}

export interface ThresholdRange {
  label: string
  min: number
  max: number
}

export interface UseFormulaCalculatorOptions {
  /** Parameter definitions. */
  params: FormulaParam[]
  /** Available presets. */
  presets?: FormulaPreset[]
  /** Compute a single result value from current params. */
  formula: (values: Record<string, number>) => number
  /** Optional classification thresholds for the result. */
  thresholds?: ThresholdRange[]
}

// ---- Composable ----

export function useFormulaCalculator(options: UseFormulaCalculatorOptions) {
  const { params, presets = [], formula, thresholds = [] } = options

  // Build default values
  const defaults: Record<string, number> = {}
  for (const p of params) {
    defaults[p.key] = p.defaultValue
  }

  const values = ref<Record<string, number>>({ ...defaults })
  const unit = ref<'primary' | 'secondary'>('primary')

  // --- Computed ---

  const result = computed(() => formula(values.value))

  const classification = computed(() => {
    const v = result.value
    for (const t of thresholds) {
      if (v >= t.min && v <= t.max) return t.label
    }
    return 'unknown'
  })

  const paramEntries = computed(() =>
    params.map((p) => ({ ...p, value: values.value[p.key] ?? 0 })),
  )

  // --- Actions ---

  function setValue(key: string, value: number) {
    if (key in values.value) {
      values.value[key] = value
    }
  }

  function applyPreset(presetId: string) {
    const preset = presets.find((p) => p.id === presetId)
    if (!preset) return
    for (const [k, v] of Object.entries(preset.values)) {
      if (k in values.value) {
        values.value[k] = v
      }
    }
  }

  function reset() {
    values.value = { ...defaults }
    unit.value = 'primary'
  }

  return {
    values,
    unit,
    result,
    classification,
    paramEntries,
    setValue,
    applyPreset,
    reset,
  }
}

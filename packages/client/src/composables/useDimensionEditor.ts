/**
 * Generic composable for managing a named-dimensions form with presets,
 * unit toggling (metric / imperial), validation, and export.
 *
 * Extracted & genericized from useGuitarDimensions (Toolbox domain).
 */
import { ref, computed } from 'vue'

// ---- Public types ----

export interface DimensionField {
  key: string
  label: string
  required?: boolean       // default true  — value must be > 0
}

export interface DimensionPreset {
  id: string
  label: string
  /** Values are always stored in mm (metric base). */
  values: Record<string, number>
}

export interface UseDimensionEditorOptions {
  /** Field definitions. */
  fields: DimensionField[]
  /** Available presets (values in mm). */
  presets?: DimensionPreset[]
  /** Default values in mm. */
  defaults: Record<string, number>
  /** mm ↔ inch conversion factor (default 25.4). */
  conversionFactor?: number
}

// ---- Composable ----

export function useDimensionEditor(options: UseDimensionEditorOptions) {
  const { fields, presets = [], defaults } = options
  const MM_PER_INCH = options.conversionFactor ?? 25.4
  const INCH_PER_MM = 1 / MM_PER_INCH

  const units = ref<'mm' | 'inch'>('mm')
  const values = ref<Record<string, number>>({ ...defaults })
  const selectedPreset = ref<string | null>(null)

  const currentUnitLabel = computed(() => (units.value === 'mm' ? 'mm' : 'in'))

  // --- Validation ---

  const hasValidDimensions = computed(() => {
    return fields
      .filter((f) => f.required !== false)
      .every((f) => (values.value[f.key] ?? 0) > 0)
  })

  // --- Unit toggling ---

  function toggleUnits(newUnit: 'mm' | 'inch') {
    if (newUnit === units.value) return
    const factor = newUnit === 'inch' ? INCH_PER_MM : MM_PER_INCH

    for (const f of fields) {
      const v = values.value[f.key]
      if (v !== undefined) {
        values.value[f.key] = parseFloat((v * factor).toFixed(2))
      }
    }
    units.value = newUnit
  }

  // --- Presets ---

  function loadPreset(presetId: string) {
    const preset = presets.find((p) => p.id === presetId)
    if (!preset) return

    const factor = units.value === 'inch' ? INCH_PER_MM : 1
    for (const [key, val] of Object.entries(preset.values)) {
      if (key in values.value) {
        values.value[key] = parseFloat((val * factor).toFixed(2))
      }
    }
    selectedPreset.value = presetId
  }

  // --- Export ---

  function exportAsObject() {
    return {
      preset: selectedPreset.value,
      units: units.value,
      dimensions: { ...values.value },
    }
  }

  function exportAsCSV(): string {
    const headers = ['Dimension', 'Value', 'Unit']
    const rows = Object.entries(values.value).map(([key, val]) => [
      key,
      String(val),
      currentUnitLabel.value,
    ])
    return [headers, ...rows].map((r) => r.join(',')).join('\n')
  }

  // --- Reset ---

  function reset() {
    units.value = 'mm'
    values.value = { ...defaults }
    selectedPreset.value = null
  }

  return {
    units,
    values,
    selectedPreset,
    currentUnitLabel,
    hasValidDimensions,
    toggleUnits,
    loadPreset,
    exportAsObject,
    exportAsCSV,
    reset,
  }
}

/**
 * Composable for guitar body dimensions state and operations.
 * Extracted from GuitarDimensionsForm.vue
 */
import { ref, computed } from 'vue'

export interface GuitarDimensions {
  bodyLength: number
  bodyWidthUpper: number
  bodyWidthLower: number
  waistWidth: number
  bodyDepth: number
  neckPocketLength: number
  neckPocketWidth: number
  scaleLength: number
}

export interface GuitarTypeInfo {
  id: string
  label: string
  icon: string
}

export const GUITAR_TYPES: GuitarTypeInfo[] = [
  { id: 'acoustic', label: 'Acoustic', icon: '🎸' },
  { id: 'electric', label: 'Electric', icon: '⚡' },
  { id: 'bass', label: 'Bass', icon: '🎵' },
  { id: 'classical', label: 'Classical', icon: '🎼' }
]

// Presets in mm
export const DIMENSION_PRESETS: Record<string, Partial<GuitarDimensions>> = {
  telecaster: {
    bodyLength: 400,
    bodyWidthUpper: 280,
    bodyWidthLower: 330,
    waistWidth: 280,
    bodyDepth: 45,
    neckPocketLength: 76,
    neckPocketWidth: 56,
    scaleLength: 648
  },
  stratocaster: {
    bodyLength: 400,
    bodyWidthUpper: 290,
    bodyWidthLower: 340,
    waistWidth: 260,
    bodyDepth: 45,
    neckPocketLength: 76,
    neckPocketWidth: 56,
    scaleLength: 648
  },
  lesPaul: {
    bodyLength: 440,
    bodyWidthUpper: 290,
    bodyWidthLower: 330,
    waistWidth: 260,
    bodyDepth: 50,
    neckPocketLength: 80,
    neckPocketWidth: 60,
    scaleLength: 629
  },
  dreadnought: {
    bodyLength: 508,
    bodyWidthUpper: 290,
    bodyWidthLower: 400,
    waistWidth: 280,
    bodyDepth: 100,
    neckPocketLength: 0,
    neckPocketWidth: 0,
    scaleLength: 648
  },
  om: {
    bodyLength: 495,
    bodyWidthUpper: 260,
    bodyWidthLower: 380,
    waistWidth: 230,
    bodyDepth: 100,
    neckPocketLength: 0,
    neckPocketWidth: 0,
    scaleLength: 632
  },
  parlor: {
    bodyLength: 450,
    bodyWidthUpper: 230,
    bodyWidthLower: 340,
    waistWidth: 200,
    bodyDepth: 90,
    neckPocketLength: 0,
    neckPocketWidth: 0,
    scaleLength: 610
  }
}

const DEFAULT_DIMENSIONS: GuitarDimensions = {
  bodyLength: 400,
  bodyWidthUpper: 290,
  bodyWidthLower: 340,
  waistWidth: 260,
  bodyDepth: 45,
  neckPocketLength: 76,
  neckPocketWidth: 56,
  scaleLength: 648
}

export function useGuitarDimensions() {
  const selectedType = ref('acoustic')
  const units = ref<'mm' | 'inch'>('mm')
  const dimensions = ref<GuitarDimensions>({ ...DEFAULT_DIMENSIONS })

  const currentUnitLabel = computed(() => units.value === 'mm' ? 'mm' : 'in')

  // Validation
  const hasValidDimensions = computed(() => {
    const d = dimensions.value
    return (
      d.bodyLength > 0 &&
      d.bodyWidthUpper > 0 &&
      d.bodyWidthLower > 0 &&
      d.waistWidth > 0 &&
      d.bodyDepth > 0 &&
      d.scaleLength > 0
    )
  })

  // Toggle units and convert values
  function toggleUnits(newUnit: 'mm' | 'inch') {
    if (newUnit === units.value) return

    const factor = newUnit === 'inch' ? 0.03937007874015748 : 25.4
    const keys: (keyof GuitarDimensions)[] = [
      'bodyLength', 'bodyWidthUpper', 'bodyWidthLower',
      'waistWidth', 'bodyDepth', 'neckPocketLength',
      'neckPocketWidth', 'scaleLength'
    ]

    for (const key of keys) {
      dimensions.value[key] = parseFloat((dimensions.value[key] * factor).toFixed(2))
    }

    units.value = newUnit
  }

  // Load a preset
  function loadPreset(presetId: string) {
    const preset = DIMENSION_PRESETS[presetId]
    if (!preset) return

    // Convert preset to current units if needed
    const factor = units.value === 'inch' ? 0.03937007874015748 : 1

    for (const [key, value] of Object.entries(preset)) {
      if (value !== undefined && key in dimensions.value) {
        (dimensions.value as Record<string, number>)[key] = parseFloat((value * factor).toFixed(2))
      }
    }
  }

  // Select guitar type
  function selectType(typeId: string) {
    selectedType.value = typeId
  }

  // Export as JSON object
  function exportAsObject() {
    return {
      type: selectedType.value,
      units: units.value,
      dimensions: { ...dimensions.value }
    }
  }

  // Export as CSV string
  function exportAsCSV(): string {
    const headers = ['Dimension', 'Value', 'Unit']
    const rows = Object.entries(dimensions.value).map(([key, value]) => [
      key,
      String(value),
      currentUnitLabel.value
    ])
    return [headers, ...rows].map(row => row.join(',')).join('\n')
  }

  // Reset to defaults
  function reset() {
    selectedType.value = 'acoustic'
    units.value = 'mm'
    dimensions.value = { ...DEFAULT_DIMENSIONS }
  }

  return {
    // State
    selectedType,
    units,
    dimensions,

    // Computed
    currentUnitLabel,
    hasValidDimensions,

    // Methods
    toggleUnits,
    loadPreset,
    selectType,
    exportAsObject,
    exportAsCSV,
    reset
  }
}

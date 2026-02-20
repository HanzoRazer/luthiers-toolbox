/**
 * useGuitarDimensions - Composable for guitar dimension state management
 *
 * Handles:
 * - Dimension data and validation
 * - Guitar types and presets
 * - Unit conversion (mm/inch)
 * - Query parameter loading from AI extraction
 * - Status messaging
 */
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'

export interface GuitarDimensions {
  bodyLength: number
  bodyWidthUpper: number
  bodyWidthLower: number
  waistWidth: number
  bodyDepth: number
  scaleLength: number
  nutWidth: number
  bridgeSpacing: number
  fretCount: number
  neckAngle: number
}

export interface GuitarTypeInfo {
  id: string
  label: string
  icon: string
}

export interface PresetInfo {
  id: string
  name: string
}

export const GUITAR_TYPES: GuitarTypeInfo[] = [
  { id: 'acoustic', label: 'Acoustic', icon: '🎻' },
  { id: 'electric', label: 'Electric', icon: '🎸' },
  { id: 'classical', label: 'Classical', icon: '🎼' },
  { id: 'bass', label: 'Bass', icon: '🎵' },
]

export const PRESETS: PresetInfo[] = [
  { id: 'dreadnought', name: 'Dreadnought' },
  { id: 'om', name: 'OM / 000' },
  { id: 'les_paul', name: 'Les Paul' },
  { id: 'stratocaster', name: 'Stratocaster' },
  { id: 'telecaster', name: 'Telecaster' },
  { id: 'jazz_bass', name: 'Jazz Bass' },
]

// Presets in mm (full dimensions)
export const DIMENSION_PRESETS: Record<string, Partial<GuitarDimensions>> = {
  dreadnought: {
    bodyLength: 505,
    bodyWidthUpper: 280,
    bodyWidthLower: 390,
    waistWidth: 270,
    bodyDepth: 120,
    scaleLength: 648,
    nutWidth: 43,
    bridgeSpacing: 56,
    fretCount: 20,
    neckAngle: 0,
  },
  om: {
    bodyLength: 495,
    bodyWidthUpper: 280,
    bodyWidthLower: 380,
    waistWidth: 260,
    bodyDepth: 110,
    scaleLength: 648,
    nutWidth: 43,
    bridgeSpacing: 54,
    fretCount: 20,
    neckAngle: 0,
  },
  les_paul: {
    bodyLength: 475,
    bodyWidthUpper: 330,
    bodyWidthLower: 330,
    waistWidth: 280,
    bodyDepth: 55,
    scaleLength: 628,
    nutWidth: 43,
    bridgeSpacing: 52,
    fretCount: 22,
    neckAngle: 4,
  },
  stratocaster: {
    bodyLength: 460,
    bodyWidthUpper: 320,
    bodyWidthLower: 320,
    waistWidth: 280,
    bodyDepth: 45,
    scaleLength: 648,
    nutWidth: 42,
    bridgeSpacing: 52,
    fretCount: 22,
    neckAngle: 0,
  },
  telecaster: {
    bodyLength: 470,
    bodyWidthUpper: 325,
    bodyWidthLower: 325,
    waistWidth: 320,
    bodyDepth: 45,
    scaleLength: 648,
    nutWidth: 42,
    bridgeSpacing: 54,
    fretCount: 22,
    neckAngle: 0,
  },
  jazz_bass: {
    bodyLength: 490,
    bodyWidthUpper: 330,
    bodyWidthLower: 355,
    waistWidth: 280,
    bodyDepth: 46,
    scaleLength: 864,
    nutWidth: 38,
    bridgeSpacing: 62,
    fretCount: 20,
    neckAngle: 0,
  },
}

const DEFAULT_DIMENSIONS: GuitarDimensions = {
  bodyLength: 0,
  bodyWidthUpper: 0,
  bodyWidthLower: 0,
  waistWidth: 0,
  bodyDepth: 0,
  scaleLength: 0,
  nutWidth: 0,
  bridgeSpacing: 0,
  fretCount: 22,
  neckAngle: 0,
}

export function useGuitarDimensions() {
  const route = useRoute()

  // State
  const selectedType = ref('acoustic')
  const units = ref<'mm' | 'inch'>('mm')
  const dimensions = ref<GuitarDimensions>({ ...DEFAULT_DIMENSIONS })
  const status = ref('')
  const statusType = ref<'success' | 'error' | 'info'>('info')

  // Computed
  const currentUnit = computed(() => (units.value === 'mm' ? 'mm' : 'in'))

  const hasValidDimensions = computed(() => {
    return dimensions.value.bodyLength > 0 && dimensions.value.bodyWidthLower > 0
  })

  // Load dimensions from query params (AI-extracted from Blueprint Lab)
  onMounted(() => {
    if (route.query.preset === 'ai-extracted') {
      const parseQueryNumber = (key: string): number => {
        const value = route.query[key]
        if (typeof value === 'string') {
          const parsed = parseFloat(value)
          return isNaN(parsed) ? 0 : parsed
        }
        return 0
      }

      dimensions.value = {
        bodyLength: parseQueryNumber('bodyLength'),
        bodyWidthUpper: parseQueryNumber('bodyWidthUpper'),
        bodyWidthLower: parseQueryNumber('bodyWidthLower'),
        waistWidth: parseQueryNumber('bodyWidthWaist'),
        bodyDepth: parseQueryNumber('bodyDepth'),
        scaleLength: parseQueryNumber('scaleLength'),
        nutWidth: parseQueryNumber('neckWidth'),
        bridgeSpacing: parseQueryNumber('bridgeSpacing'),
        fretCount: parseQueryNumber('fretCount') || 22,
        neckAngle: parseQueryNumber('neckAngle'),
      }

      status.value = '✅ Dimensions loaded from Blueprint AI analysis'
      statusType.value = 'success'
    }
  })

  // Toggle units and convert values
  function toggleUnits(newUnit: 'mm' | 'inch') {
    if (newUnit === units.value) return

    const factor = newUnit === 'inch' ? 0.03937007874015748 : 25.4
    const keys: (keyof GuitarDimensions)[] = [
      'bodyLength',
      'bodyWidthUpper',
      'bodyWidthLower',
      'waistWidth',
      'bodyDepth',
      'scaleLength',
      'nutWidth',
      'bridgeSpacing',
    ]

    for (const key of keys) {
      if (dimensions.value[key]) {
        dimensions.value[key] = parseFloat((dimensions.value[key] * factor).toFixed(3))
      }
    }

    units.value = newUnit
    status.value = `✅ Converted to ${newUnit === 'mm' ? 'millimeters' : 'inches'}`
    statusType.value = 'success'
  }

  // Load a preset
  function loadPreset(presetId: string) {
    const preset = DIMENSION_PRESETS[presetId]
    if (!preset) return

    // Convert preset to current units if needed
    const factor = units.value === 'inch' ? 0.03937007874015748 : 1

    for (const [key, value] of Object.entries(preset)) {
      if (value !== undefined && key in dimensions.value) {
        ;(dimensions.value as Record<string, number>)[key] = parseFloat((value * factor).toFixed(2))
      }
    }

    const presetName = PRESETS.find((p) => p.id === presetId)?.name
    status.value = `✅ Loaded ${presetName} preset`
    statusType.value = 'success'

    // Auto-select guitar type based on preset
    if (presetId.includes('bass')) {
      selectedType.value = 'bass'
    } else if (['dreadnought', 'om'].includes(presetId)) {
      selectedType.value = 'acoustic'
    } else {
      selectedType.value = 'electric'
    }
  }

  // Select guitar type
  function selectType(typeId: string) {
    selectedType.value = typeId
    const typeName = GUITAR_TYPES.find((t) => t.id === typeId)?.label
    status.value = `✅ Selected ${typeName} guitar type`
    statusType.value = 'success'
  }

  // Handle dimension change (clears status)
  function handleChange() {
    if (status.value) {
      status.value = ''
    }
  }

  // Clear all dimensions
  function clearAll() {
    if (confirm('Clear all dimensions? This cannot be undone.')) {
      Object.keys(dimensions.value).forEach((key) => {
        if (key === 'fretCount') {
          dimensions.value[key as keyof GuitarDimensions] = 22
        } else {
          dimensions.value[key as keyof GuitarDimensions] = 0
        }
      })
      status.value = '🗑️ All dimensions cleared'
      statusType.value = 'info'
    }
  }

  // Set status message
  function setStatus(message: string, type: 'success' | 'error' | 'info' = 'info') {
    status.value = message
    statusType.value = type
  }

  // Export as JSON object
  function exportAsObject() {
    return {
      type: selectedType.value,
      units: units.value,
      dimensions: { ...dimensions.value },
      timestamp: new Date().toISOString(),
    }
  }

  // Export as CSV string
  function exportAsCSV(): string {
    const headers = ['Dimension', 'Value', 'Unit']
    const rows = [
      ['Body Length', dimensions.value.bodyLength, currentUnit.value],
      ['Upper Bout Width', dimensions.value.bodyWidthUpper, currentUnit.value],
      ['Lower Bout Width', dimensions.value.bodyWidthLower, currentUnit.value],
      ['Waist Width', dimensions.value.waistWidth, currentUnit.value],
      ['Body Depth', dimensions.value.bodyDepth, currentUnit.value],
      ['Scale Length', dimensions.value.scaleLength, currentUnit.value],
      ['Nut Width', dimensions.value.nutWidth, currentUnit.value],
      ['Bridge Spacing', dimensions.value.bridgeSpacing, currentUnit.value],
      ['Fret Count', dimensions.value.fretCount, 'frets'],
      ['Neck Angle', dimensions.value.neckAngle, 'degrees'],
    ]
    return [headers, ...rows].map((row) => row.join(',')).join('\n')
  }

  // Reset to defaults
  function reset() {
    selectedType.value = 'acoustic'
    units.value = 'mm'
    dimensions.value = { ...DEFAULT_DIMENSIONS }
    status.value = ''
  }

  return {
    // Constants
    guitarTypes: GUITAR_TYPES,
    presets: PRESETS,

    // State
    selectedType,
    units,
    dimensions,
    status,
    statusType,

    // Computed
    currentUnit,
    hasValidDimensions,

    // Methods
    toggleUnits,
    loadPreset,
    selectType,
    handleChange,
    clearAll,
    setStatus,
    exportAsObject,
    exportAsCSV,
    reset,
  }
}

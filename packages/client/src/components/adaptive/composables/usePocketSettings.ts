/**
 * Composable for Adaptive Pocket settings state.
 * Extracted from AdaptivePocketLab.vue
 */
import { ref, computed, watch } from 'vue'

export interface PocketSettings {
  toolD: number
  stepoverPct: number
  stepdown: number
  margin: number
  strategy: 'Spiral' | 'Lanes'
  cornerRadiusMin: number
  slowdownFeedPct: number
  climb: boolean
  feedXY: number
  units: 'mm' | 'inch'
  feedZ: number
  plungeRate: number
  safeZ: number
  depth: number
  spindleRpm: number
}

export interface MachineProfile {
  id: string
  name: string
  maxFeedXY: number
  maxFeedZ: number
  maxRpm: number
  workEnvelope: {
    x: number
    y: number
    z: number
  }
}

const DEFAULT_SETTINGS: PocketSettings = {
  toolD: 6,
  stepoverPct: 40,
  stepdown: 2,
  margin: 0.5,
  strategy: 'Spiral',
  cornerRadiusMin: 3,
  slowdownFeedPct: 70,
  climb: true,
  feedXY: 1500,
  units: 'mm',
  feedZ: 500,
  plungeRate: 300,
  safeZ: 5,
  depth: 10,
  spindleRpm: 18000,
}

export function usePocketSettings() {
  // Core settings
  const toolD = ref(DEFAULT_SETTINGS.toolD)
  const stepoverPct = ref(DEFAULT_SETTINGS.stepoverPct)
  const stepdown = ref(DEFAULT_SETTINGS.stepdown)
  const margin = ref(DEFAULT_SETTINGS.margin)
  const strategy = ref<'Spiral' | 'Lanes'>(DEFAULT_SETTINGS.strategy)
  const cornerRadiusMin = ref(DEFAULT_SETTINGS.cornerRadiusMin)
  const slowdownFeedPct = ref(DEFAULT_SETTINGS.slowdownFeedPct)
  const climb = ref(DEFAULT_SETTINGS.climb)
  const feedXY = ref(DEFAULT_SETTINGS.feedXY)
  const units = ref<'mm' | 'inch'>(DEFAULT_SETTINGS.units)
  const feedZ = ref(DEFAULT_SETTINGS.feedZ)
  const plungeRate = ref(DEFAULT_SETTINGS.plungeRate)
  const safeZ = ref(DEFAULT_SETTINGS.safeZ)
  const depth = ref(DEFAULT_SETTINGS.depth)
  const spindleRpm = ref(DEFAULT_SETTINGS.spindleRpm)

  // Machine profile
  const selectedMachineId = ref<string | null>(null)
  const machineProfiles = ref<MachineProfile[]>([])

  // Computed values
  const stepoverMm = computed(() => (toolD.value * stepoverPct.value) / 100)

  const chipload = computed(() => {
    const flutes = 2 // Assume 2-flute for now
    if (spindleRpm.value === 0 || flutes === 0) return 0
    return feedXY.value / (spindleRpm.value * flutes)
  })

  const mrr = computed(() => {
    // Material Removal Rate in mm³/min
    return stepoverMm.value * stepdown.value * feedXY.value
  })

  // Validation
  const validationErrors = computed(() => {
    const errors: string[] = []

    if (toolD.value <= 0) errors.push('Tool diameter must be positive')
    if (stepoverPct.value < 5 || stepoverPct.value > 95) {
      errors.push('Step-over must be 5-95%')
    }
    if (stepdown.value <= 0) errors.push('Step-down must be positive')
    if (feedXY.value <= 0) errors.push('Feed rate must be positive')
    if (depth.value <= 0) errors.push('Depth must be positive')

    return errors
  })

  const isValid = computed(() => validationErrors.value.length === 0)

  // Export settings object
  const settingsObject = computed<PocketSettings>(() => ({
    toolD: toolD.value,
    stepoverPct: stepoverPct.value,
    stepdown: stepdown.value,
    margin: margin.value,
    strategy: strategy.value,
    cornerRadiusMin: cornerRadiusMin.value,
    slowdownFeedPct: slowdownFeedPct.value,
    climb: climb.value,
    feedXY: feedXY.value,
    units: units.value,
    feedZ: feedZ.value,
    plungeRate: plungeRate.value,
    safeZ: safeZ.value,
    depth: depth.value,
    spindleRpm: spindleRpm.value,
  }))

  // Load/save presets
  function loadSettings(settings: Partial<PocketSettings>) {
    if (settings.toolD !== undefined) toolD.value = settings.toolD
    if (settings.stepoverPct !== undefined) stepoverPct.value = settings.stepoverPct
    if (settings.stepdown !== undefined) stepdown.value = settings.stepdown
    if (settings.margin !== undefined) margin.value = settings.margin
    if (settings.strategy !== undefined) strategy.value = settings.strategy
    if (settings.cornerRadiusMin !== undefined) cornerRadiusMin.value = settings.cornerRadiusMin
    if (settings.slowdownFeedPct !== undefined) slowdownFeedPct.value = settings.slowdownFeedPct
    if (settings.climb !== undefined) climb.value = settings.climb
    if (settings.feedXY !== undefined) feedXY.value = settings.feedXY
    if (settings.units !== undefined) units.value = settings.units
    if (settings.feedZ !== undefined) feedZ.value = settings.feedZ
    if (settings.plungeRate !== undefined) plungeRate.value = settings.plungeRate
    if (settings.safeZ !== undefined) safeZ.value = settings.safeZ
    if (settings.depth !== undefined) depth.value = settings.depth
    if (settings.spindleRpm !== undefined) spindleRpm.value = settings.spindleRpm
  }

  function resetToDefaults() {
    loadSettings(DEFAULT_SETTINGS)
  }

  // Persist to localStorage
  const STORAGE_KEY = 'adaptive_pocket_settings'

  function saveToStorage() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(settingsObject.value))
    } catch {
      // ignore
    }
  }

  function loadFromStorage() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      if (raw) {
        loadSettings(JSON.parse(raw))
      }
    } catch {
      // ignore
    }
  }

  return {
    // State
    toolD,
    stepoverPct,
    stepdown,
    margin,
    strategy,
    cornerRadiusMin,
    slowdownFeedPct,
    climb,
    feedXY,
    units,
    feedZ,
    plungeRate,
    safeZ,
    depth,
    spindleRpm,
    selectedMachineId,
    machineProfiles,

    // Computed
    stepoverMm,
    chipload,
    mrr,
    validationErrors,
    isValid,
    settingsObject,

    // Methods
    loadSettings,
    resetToDefaults,
    saveToStorage,
    loadFromStorage,
  }
}

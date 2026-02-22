/**
 * Composable for L.3 Trochoid and Jerk-Aware settings.
 * Manages trochoid milling and jerk-aware motion parameters.
 */
import { ref, watch, type Ref } from 'vue'

// ============================================================================
// Types
// ============================================================================

export interface TrochoidSettingsState {
  // Trochoid settings
  useTrochoids: Ref<boolean>
  trochoidRadius: Ref<number>
  trochoidPitch: Ref<number>

  // Jerk-aware settings
  jerkAware: Ref<boolean>
  machineAccel: Ref<number>
  machineJerk: Ref<number>
  cornerTol: Ref<number>
}

export interface TrochoidSettingsConfig {
  /** Whether to persist settings to localStorage */
  persist?: boolean
  /** localStorage key prefix */
  storageKey?: string
}

// ============================================================================
// Constants
// ============================================================================

const STORAGE_KEY = 'toolbox.trochoid'

const DEFAULTS = {
  useTrochoids: false,
  trochoidRadius: 1.5,
  trochoidPitch: 3.0,
  jerkAware: false,
  machineAccel: 800,
  machineJerk: 2000,
  cornerTol: 0.2,
}

// ============================================================================
// Composable
// ============================================================================

export function useTrochoidSettings(
  config: TrochoidSettingsConfig = {}
): TrochoidSettingsState {
  const { persist = false, storageKey = STORAGE_KEY } = config

  // -------------------------------------------------------------------------
  // Load from storage
  // -------------------------------------------------------------------------

  function loadFromStorage<T>(key: string, defaultValue: T): T {
    if (!persist) return defaultValue
    try {
      const stored = localStorage.getItem(`${storageKey}.${key}`)
      if (stored === null) return defaultValue
      return JSON.parse(stored) as T
    } catch {
      return defaultValue
    }
  }

  // -------------------------------------------------------------------------
  // State
  // -------------------------------------------------------------------------

  // Trochoid settings
  const useTrochoids = ref(loadFromStorage('useTrochoids', DEFAULTS.useTrochoids))
  const trochoidRadius = ref(loadFromStorage('trochoidRadius', DEFAULTS.trochoidRadius))
  const trochoidPitch = ref(loadFromStorage('trochoidPitch', DEFAULTS.trochoidPitch))

  // Jerk-aware settings
  const jerkAware = ref(loadFromStorage('jerkAware', DEFAULTS.jerkAware))
  const machineAccel = ref(loadFromStorage('machineAccel', DEFAULTS.machineAccel))
  const machineJerk = ref(loadFromStorage('machineJerk', DEFAULTS.machineJerk))
  const cornerTol = ref(loadFromStorage('cornerTol', DEFAULTS.cornerTol))

  // -------------------------------------------------------------------------
  // Persistence
  // -------------------------------------------------------------------------

  if (persist) {
    const saveToStorage = (key: string, value: unknown) => {
      try {
        localStorage.setItem(`${storageKey}.${key}`, JSON.stringify(value))
      } catch {
        // Ignore storage errors
      }
    }

    watch(useTrochoids, (v) => saveToStorage('useTrochoids', v))
    watch(trochoidRadius, (v) => saveToStorage('trochoidRadius', v))
    watch(trochoidPitch, (v) => saveToStorage('trochoidPitch', v))
    watch(jerkAware, (v) => saveToStorage('jerkAware', v))
    watch(machineAccel, (v) => saveToStorage('machineAccel', v))
    watch(machineJerk, (v) => saveToStorage('machineJerk', v))
    watch(cornerTol, (v) => saveToStorage('cornerTol', v))
  }

  // -------------------------------------------------------------------------
  // Return
  // -------------------------------------------------------------------------

  return {
    useTrochoids,
    trochoidRadius,
    trochoidPitch,
    jerkAware,
    machineAccel,
    machineJerk,
    cornerTol,
  }
}

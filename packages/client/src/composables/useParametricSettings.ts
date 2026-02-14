/**
 * Generic composable for validated parametric settings.
 * Domain-agnostic — works with any flat settings object.
 *
 * Extracted & genericized from usePocketSettings (Adaptive domain).
 */
import { ref, computed } from 'vue'

// ---- Public types ----

export interface FieldSpec {
  key: string
  label: string
  type: 'number' | 'string' | 'boolean' | 'select'
  defaultValue: number | string | boolean
  options?: string[]          // for 'select' type
  min?: number                // for 'number' type
  max?: number
  unit?: string               // display hint (e.g. 'mm', '%')
}

export interface ValidationError {
  field: string
  message: string
}

export interface UseParametricSettingsOptions {
  /** Field specifications with defaults and constraints. */
  fields: FieldSpec[]
  /** localStorage key for persistence. */
  storageKey?: string
}

// ---- Composable ----

export function useParametricSettings(options: UseParametricSettingsOptions) {
  const { fields, storageKey } = options

  // Build default-values map
  const defaults: Record<string, number | string | boolean> = {}
  for (const f of fields) {
    defaults[f.key] = f.defaultValue
  }

  // Reactive settings store
  const settings = ref<Record<string, number | string | boolean>>({ ...defaults })

  // --- Computed helpers ---

  /** Derived numeric helper — returns setting as number (0 if non-numeric). */
  function getNumber(key: string): number {
    const v = settings.value[key]
    return typeof v === 'number' ? v : 0
  }

  /** Derived boolean helper. */
  function getBoolean(key: string): boolean {
    return !!settings.value[key]
  }

  // --- Validation ---

  const validationErrors = computed<ValidationError[]>(() => {
    const errors: ValidationError[] = []
    for (const f of fields) {
      const v = settings.value[f.key]
      if (f.type === 'number' && typeof v === 'number') {
        if (f.min !== undefined && v < f.min) {
          errors.push({ field: f.key, message: `${f.label} must be ≥ ${f.min}` })
        }
        if (f.max !== undefined && v > f.max) {
          errors.push({ field: f.key, message: `${f.label} must be ≤ ${f.max}` })
        }
      }
      if (f.type === 'select' && f.options && !f.options.includes(String(v))) {
        errors.push({ field: f.key, message: `${f.label} has an invalid value` })
      }
    }
    return errors
  })

  const isValid = computed(() => validationErrors.value.length === 0)

  // --- Snapshot / export ---

  const settingsSnapshot = computed(() => ({ ...settings.value }))

  // --- Load / save ---

  function loadSettings(partial: Record<string, number | string | boolean>) {
    for (const f of fields) {
      if (partial[f.key] !== undefined) {
        settings.value[f.key] = partial[f.key]
      }
    }
  }

  function resetToDefaults() {
    loadSettings(defaults)
  }

  function saveToStorage() {
    if (!storageKey) return
    try {
      localStorage.setItem(storageKey, JSON.stringify(settingsSnapshot.value))
    } catch {
      /* ignore */
    }
  }

  function loadFromStorage() {
    if (!storageKey) return
    try {
      const raw = localStorage.getItem(storageKey)
      if (raw) loadSettings(JSON.parse(raw))
    } catch {
      /* ignore */
    }
  }

  return {
    settings,
    validationErrors,
    isValid,
    settingsSnapshot,
    getNumber,
    getBoolean,
    loadSettings,
    resetToDefaults,
    saveToStorage,
    loadFromStorage,
  }
}

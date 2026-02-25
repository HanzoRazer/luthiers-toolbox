/**
 * useLocalStorageRef — Reactive ref persisted to localStorage.
 *
 * Replaces 12+ duplicated read/write/watch patterns found across
 * adaptive composables (useAdaptiveFeedPresets, usePocketSettings,
 * useTrochoidSettings, useToolpathExport, useMachineProfiles).
 *
 * @example
 * ```ts
 * const machineId = useLocalStorageRef('toolbox.machine', 'Mach4_Router_4x8')
 * const modes = useLocalStorageRef<ExportModes>('toolbox.af.modes', { comment: true }, { deep: true })
 * ```
 */
import { ref, watch, type Ref, type WatchOptions } from 'vue'

export interface UseLocalStorageRefOptions {
  /**
   * Use deep watcher for nested objects/arrays.
   * @default false
   */
  deep?: boolean

  /**
   * Serialize function (defaults to JSON.stringify).
   */
  serialize?: (value: unknown) => string

  /**
   * Deserialize function (defaults to JSON.parse).
   */
  deserialize?: (raw: string) => unknown
}

export function useLocalStorageRef<T>(
  key: string,
  defaultValue: T,
  options: UseLocalStorageRefOptions = {},
): Ref<T> {
  const {
    deep = false,
    serialize = JSON.stringify,
    deserialize = JSON.parse,
  } = options

  // Read initial value from localStorage
  let initial: T = defaultValue
  try {
    const stored = localStorage.getItem(key)
    if (stored !== null) {
      initial = deserialize(stored) as T
    }
  } catch {
    // Corrupt or missing — use default
  }

  const data = ref<T>(initial) as Ref<T>

  // Auto-save on change
  const watchOpts: WatchOptions = { deep }
  watch(
    data,
    (newVal) => {
      try {
        if (newVal === null || newVal === undefined) {
          localStorage.removeItem(key)
        } else {
          localStorage.setItem(key, serialize(newVal))
        }
      } catch {
        // Storage full or unavailable — silently ignore
      }
    },
    watchOpts,
  )

  return data
}

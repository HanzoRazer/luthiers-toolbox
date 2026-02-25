/**
 * useFormState — Generic reactive form state composable.
 *
 * Eliminates 30+ repeated patterns of initializing form/errors/touched refs,
 * building reset functions, and computing dirty state.
 *
 * @example
 * ```ts
 * const { form, errors, touched, isDirty, reset, setField } = useFormState({
 *   name: '',
 *   email: '',
 *   scale_length_mm: 650,
 * })
 *
 * // Type-safe field access
 * form.value.name = 'Fender Stratocaster'
 * setField('scale_length_mm', 647.7)
 *
 * // isDirty automatically tracks changes
 * console.log(isDirty.value) // true
 *
 * reset() // restores all defaults
 * ```
 */

import { ref, computed, type Ref, type ComputedRef } from 'vue'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface UseFormStateOptions {
  /**
   * Custom deep-clone function for default values.
   * Falls back to JSON.parse(JSON.stringify(defaults)).
   */
  clone?: <T>(value: T) => T
}

export interface UseFormStateReturn<T extends Record<string, unknown>> {
  /** Reactive form field values. */
  form: Ref<T>
  /** Per-field error messages (partial — only set for fields with errors). */
  errors: Ref<Partial<Record<keyof T, string>>>
  /** Per-field touched flags (set after first interaction). */
  touched: Ref<Partial<Record<keyof T, boolean>>>
  /** True when current values differ from defaults. */
  isDirty: ComputedRef<boolean>
  /** Reset form to defaults, clear errors and touched. */
  reset: () => void
  /** Set a single field value and mark it as touched. */
  setField: <K extends keyof T>(field: K, value: T[K]) => void
  /** Set a single field error. Pass `undefined` to clear. */
  setError: <K extends keyof T>(field: K, message: string | undefined) => void
  /** Clear all errors. */
  clearErrors: () => void
  /** Mark a field as touched. */
  touch: <K extends keyof T>(field: K) => void
}

// ---------------------------------------------------------------------------
// Implementation
// ---------------------------------------------------------------------------

function defaultClone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value))
}

export function useFormState<T extends Record<string, unknown>>(
  defaults: T,
  options: UseFormStateOptions = {},
): UseFormStateReturn<T> {
  const clone = options.clone ?? defaultClone

  // Snapshot defaults for reset/dirty comparison
  const _defaults = clone(defaults)

  const form = ref<T>(clone(defaults)) as Ref<T>
  const errors = ref<Partial<Record<keyof T, string>>>({}) as Ref<Partial<Record<keyof T, string>>>
  const touched = ref<Partial<Record<keyof T, boolean>>>({}) as Ref<Partial<Record<keyof T, boolean>>>

  const isDirty = computed(() => {
    const keys = Object.keys(_defaults) as Array<keyof T>
    return keys.some((key) => {
      const a = form.value[key]
      const b = _defaults[key]
      // Use JSON comparison for deep equality of nested objects
      if (typeof a === 'object' || typeof b === 'object') {
        return JSON.stringify(a) !== JSON.stringify(b)
      }
      return a !== b
    })
  })

  function reset(): void {
    form.value = clone(_defaults)
    errors.value = {}
    touched.value = {}
  }

  function setField<K extends keyof T>(field: K, value: T[K]): void {
    form.value[field] = value
    touched.value = { ...touched.value, [field]: true }
  }

  function setError<K extends keyof T>(field: K, message: string | undefined): void {
    if (message === undefined) {
      const { [field]: _, ...rest } = errors.value
      errors.value = rest as Partial<Record<keyof T, string>>
    } else {
      errors.value = { ...errors.value, [field]: message }
    }
  }

  function clearErrors(): void {
    errors.value = {}
  }

  function touch<K extends keyof T>(field: K): void {
    touched.value = { ...touched.value, [field]: true }
  }

  return {
    form,
    errors,
    touched,
    isDirty,
    reset,
    setField,
    setError,
    clearErrors,
    touch,
  }
}

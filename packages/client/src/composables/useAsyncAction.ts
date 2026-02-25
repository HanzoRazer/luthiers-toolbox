/**
 * useAsyncAction — Generic async action wrapper.
 *
 * Eliminates the repeated pattern:
 *   loading.value = true
 *   error.value = null
 *   try { ... } catch (e) { error.value = ... } finally { loading.value = false }
 *
 * Usage:
 *   const { data, error, loading, execute } = useAsyncAction(
 *     (id: string) => api(`/api/thing/${id}`).then(r => r.json())
 *   )
 *   await execute('abc')        // loading toggles automatically
 *   if (error.value) ...        // typed Error | null
 *
 * For composables that already expose their own loading/error refs, use
 * the `refs` option to bind to existing refs instead of creating new ones.
 */

import { ref, type Ref } from 'vue'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface UseAsyncActionOptions<T> {
  /**
   * Initial value for `data`. Defaults to `null`.
   */
  initialValue?: T | null

  /**
   * Called when the action throws. Return a string to override the default
   * `error.value` message, or `undefined` to use the default.
   */
  onError?: (err: Error) => string | undefined

  /**
   * Called after a successful execution with the result.
   */
  onSuccess?: (result: T) => void

  /**
   * Supply existing refs if you need to integrate with an existing store
   * that already exposes `loading` / `error`.
   */
  refs?: {
    loading?: Ref<boolean>
    error?: Ref<string | null>
  }
}

export interface UseAsyncActionReturn<T, TArgs extends unknown[]> {
  /** Last successful result (or initialValue). */
  data: Ref<T | null>
  /** Error message from the most recent failed execution, or null. */
  error: Ref<string | null>
  /** True while the action is in-flight. */
  loading: Ref<boolean>
  /** Run the wrapped action. Returns the result or null on failure. */
  execute: (...args: TArgs) => Promise<T | null>
  /** Reset data, error, loading to initial state. */
  reset: () => void
}

// ---------------------------------------------------------------------------
// Implementation
// ---------------------------------------------------------------------------

/**
 * Wraps an async function with reactive `loading`, `error`, and `data` refs.
 *
 * @param action  The async function to wrap.
 * @param options Optional configuration (initial value, callbacks, external refs).
 */
export function useAsyncAction<T, TArgs extends unknown[] = []>(
  action: (...args: TArgs) => Promise<T>,
  options: UseAsyncActionOptions<T> = {},
): UseAsyncActionReturn<T, TArgs> {
  const {
    initialValue = null,
    onError,
    onSuccess,
    refs: externalRefs,
  } = options

  const data = ref<T | null>(initialValue) as Ref<T | null>
  const error: Ref<string | null> = externalRefs?.error ?? ref<string | null>(null)
  const loading: Ref<boolean> = externalRefs?.loading ?? ref(false)

  async function execute(...args: TArgs): Promise<T | null> {
    loading.value = true
    error.value = null
    try {
      const result = await action(...args)
      data.value = result
      onSuccess?.(result)
      return result
    } catch (e: unknown) {
      const err = e instanceof Error ? e : new Error(String(e))
      const customMsg = onError?.(err)
      error.value = customMsg ?? err.message
      return null
    } finally {
      loading.value = false
    }
  }

  function reset(): void {
    data.value = initialValue ?? null
    error.value = null
    loading.value = false
  }

  return { data, error, loading, execute, reset }
}

/**
 * useFetchTransform — Generic composable for async fetch + transform patterns.
 *
 * Eliminates repeated try/catch/loading/error boilerplate found across 40+
 * stores and composables.  Wraps any async fetcher with reactive loading,
 * error, and data refs plus an idempotent `refresh()` method.
 *
 * @example
 * ```ts
 * const { data: runs, loading, error, refresh } = useFetchTransform(
 *   () => getDashboardRuns(10),
 *   (raw) => raw.filter(r => r.status === 'active'),
 * )
 * await refresh() // explicit first load
 * ```
 *
 * @example  With `immediate` option
 * ```ts
 * const { data, loading } = useFetchTransform(
 *   () => api('/api/machines').then(r => r.json()),
 *   (raw) => raw.machines,
 *   { immediate: true },
 * )
 * ```
 */

import { ref, type Ref } from 'vue'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface UseFetchTransformOptions {
  /**
   * Fire the fetcher immediately on creation.
   * @default false
   */
  immediate?: boolean

  /**
   * Called after a successful fetch + transform.
   */
  onSuccess?: () => void

  /**
   * Called when the fetch or transform throws.
   */
  onError?: (err: Error) => void

  /**
   * Optionally bind to external loading / error refs (shared-state pattern).
   */
  refs?: {
    loading?: Ref<boolean>
    error?: Ref<string | null>
  }
}

export interface UseFetchTransformReturn<TOut> {
  /** The transformed data (null until first successful fetch). */
  data: Ref<TOut | null>
  /** True while the fetcher is in-flight. */
  loading: Ref<boolean>
  /** Error message string, or null when ok. */
  error: Ref<string | null>
  /** Re-execute the fetch + transform pipeline. */
  refresh: () => Promise<void>
}

// ---------------------------------------------------------------------------
// Implementation
// ---------------------------------------------------------------------------

export function useFetchTransform<TRaw, TOut = TRaw>(
  fetcher: () => Promise<TRaw>,
  transform: (raw: TRaw) => TOut,
  options: UseFetchTransformOptions = {},
): UseFetchTransformReturn<TOut> {
  const {
    immediate = false,
    onSuccess,
    onError,
    refs: externalRefs,
  } = options

  const data = ref<TOut | null>(null) as Ref<TOut | null>
  const loading = externalRefs?.loading ?? ref(false)
  const error = externalRefs?.error ?? ref<string | null>(null)

  async function refresh(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const raw = await fetcher()
      data.value = transform(raw)
      onSuccess?.()
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : typeof err === 'string'
            ? err
            : 'Unknown error'
      error.value = msg
      onError?.(err instanceof Error ? err : new Error(msg))
    } finally {
      loading.value = false
    }
  }

  if (immediate) {
    refresh()
  }

  return { data, loading, error, refresh }
}

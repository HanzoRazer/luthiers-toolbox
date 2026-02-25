/**
 * Tests for useAsyncAction composable.
 *
 * Validates: loading lifecycle, error handling, data persistence,
 * reset, onSuccess/onError callbacks, and external-ref binding.
 */
import { describe, it, expect, vi } from 'vitest'
import { ref } from 'vue'
import { useAsyncAction } from '../useAsyncAction'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const delay = (ms: number) => new Promise(r => setTimeout(r, ms))

function makeAction<T>(result: T, delayMs = 0) {
  return vi.fn(async () => {
    if (delayMs > 0) await delay(delayMs)
    return result
  })
}

function makeFailingAction(message = 'boom') {
  return vi.fn(async () => {
    throw new Error(message)
  })
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('useAsyncAction', () => {
  // -------------------------------------------------------------------------
  // Initial state
  // -------------------------------------------------------------------------
  it('starts with null data, no error, not loading', () => {
    const { data, error, loading } = useAsyncAction(async () => 42)
    expect(data.value).toBeNull()
    expect(error.value).toBeNull()
    expect(loading.value).toBe(false)
  })

  it('respects initialValue option', () => {
    const { data } = useAsyncAction(async () => 99, { initialValue: 7 })
    expect(data.value).toBe(7)
  })

  // -------------------------------------------------------------------------
  // Successful execution
  // -------------------------------------------------------------------------
  it('sets data on success and returns the result', async () => {
    const action = makeAction('hello')
    const { data, error, loading, execute } = useAsyncAction(action)

    const result = await execute()

    expect(result).toBe('hello')
    expect(data.value).toBe('hello')
    expect(error.value).toBeNull()
    expect(loading.value).toBe(false)
    expect(action).toHaveBeenCalledOnce()
  })

  it('passes arguments through to the wrapped action', async () => {
    const action = vi.fn(async (a: number, b: string) => `${b}-${a}`)
    const { execute } = useAsyncAction(action)

    const result = await execute(42, 'test')

    expect(result).toBe('test-42')
    expect(action).toHaveBeenCalledWith(42, 'test')
  })

  it('toggles loading during execution', async () => {
    const loadingStates: boolean[] = []
    const action = vi.fn(async () => {
      // Capture mid-flight state — loading should be true here
      return 'done'
    })

    const { loading, execute } = useAsyncAction(action)

    expect(loading.value).toBe(false)

    const promise = execute()
    // loading is set synchronously before the await
    expect(loading.value).toBe(true)

    await promise
    expect(loading.value).toBe(false)
  })

  // -------------------------------------------------------------------------
  // Error handling
  // -------------------------------------------------------------------------
  it('captures error message on failure and returns null', async () => {
    const action = makeFailingAction('oops')
    const { data, error, loading, execute } = useAsyncAction(action)

    const result = await execute()

    expect(result).toBeNull()
    expect(data.value).toBeNull()
    expect(error.value).toBe('oops')
    expect(loading.value).toBe(false)
  })

  it('handles non-Error throws', async () => {
    const action = vi.fn(async () => {
      throw 'string error'
    })
    const { error, execute } = useAsyncAction(action)

    await execute()

    expect(error.value).toBe('string error')
  })

  it('clears previous error on re-execute', async () => {
    let shouldFail = true
    const action = vi.fn(async () => {
      if (shouldFail) throw new Error('fail')
      return 'ok'
    })

    const { data, error, execute } = useAsyncAction(action)

    await execute()
    expect(error.value).toBe('fail')

    shouldFail = false
    await execute()
    expect(error.value).toBeNull()
    expect(data.value).toBe('ok')
  })

  // -------------------------------------------------------------------------
  // Reset
  // -------------------------------------------------------------------------
  it('reset() restores initial state', async () => {
    const { data, error, loading, execute, reset } = useAsyncAction(
      async () => 42,
      { initialValue: 0 },
    )

    await execute()
    expect(data.value).toBe(42)

    reset()
    expect(data.value).toBe(0)
    expect(error.value).toBeNull()
    expect(loading.value).toBe(false)
  })

  // -------------------------------------------------------------------------
  // Callbacks
  // -------------------------------------------------------------------------
  it('calls onSuccess after successful execution', async () => {
    const onSuccess = vi.fn()
    const { execute } = useAsyncAction(async () => 'val', { onSuccess })

    await execute()

    expect(onSuccess).toHaveBeenCalledWith('val')
  })

  it('calls onError and uses custom message', async () => {
    const onError = vi.fn(() => 'custom msg')
    const { error, execute } = useAsyncAction(
      async () => { throw new Error('original') },
      { onError },
    )

    await execute()

    expect(onError).toHaveBeenCalledOnce()
    expect(error.value).toBe('custom msg')
  })

  it('uses default message when onError returns undefined', async () => {
    const onError = vi.fn(() => undefined)
    const { error, execute } = useAsyncAction(
      async () => { throw new Error('default msg') },
      { onError },
    )

    await execute()

    expect(error.value).toBe('default msg')
  })

  // -------------------------------------------------------------------------
  // External refs
  // -------------------------------------------------------------------------
  it('binds to external loading/error refs when provided', async () => {
    const externalLoading = ref(false)
    const externalError = ref<string | null>(null)

    const { loading, error, execute } = useAsyncAction(
      async () => { throw new Error('ext') },
      { refs: { loading: externalLoading, error: externalError } },
    )

    // References should be the same object
    expect(loading).toBe(externalLoading)
    expect(error).toBe(externalError)

    await execute()
    expect(externalError.value).toBe('ext')
    expect(externalLoading.value).toBe(false)
  })

  // -------------------------------------------------------------------------
  // Multiple sequential calls
  // -------------------------------------------------------------------------
  it('last call wins for data', async () => {
    let counter = 0
    const action = vi.fn(async () => ++counter)
    const { data, execute } = useAsyncAction(action)

    await execute()
    expect(data.value).toBe(1)

    await execute()
    expect(data.value).toBe(2)
  })
})

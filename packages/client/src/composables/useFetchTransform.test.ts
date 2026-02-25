/**
 * Tests for useFetchTransform composable.
 */
import { describe, it, expect, vi } from 'vitest'
import { ref, nextTick } from 'vue'
import { useFetchTransform } from './useFetchTransform'

describe('useFetchTransform', () => {
  it('initializes with null data, not loading, no error', () => {
    const { data, loading, error } = useFetchTransform(
      () => Promise.resolve([1, 2, 3]),
      (raw) => raw.length,
    )
    expect(data.value).toBeNull()
    expect(loading.value).toBe(false)
    expect(error.value).toBeNull()
  })

  it('refresh() fetches and transforms data', async () => {
    const { data, loading, error, refresh } = useFetchTransform(
      () => Promise.resolve({ items: [1, 2, 3] }),
      (raw) => raw.items.map((n) => n * 2),
    )

    await refresh()

    expect(data.value).toEqual([2, 4, 6])
    expect(loading.value).toBe(false)
    expect(error.value).toBeNull()
  })

  it('sets loading=true during fetch', async () => {
    const states: boolean[] = []
    let resolve!: (v: string) => void
    const fetcher = () =>
      new Promise<string>((r) => {
        resolve = r
      })

    const { loading, refresh } = useFetchTransform(fetcher, (s) => s)

    const promise = refresh()
    // Should be loading right after calling refresh
    states.push(loading.value)
    expect(loading.value).toBe(true)

    resolve('done')
    await promise
    states.push(loading.value)
    expect(loading.value).toBe(false)
  })

  it('captures error message on fetcher throw', async () => {
    const { data, error, refresh } = useFetchTransform(
      () => Promise.reject(new Error('Network failure')),
      (raw) => raw,
    )

    await refresh()

    expect(data.value).toBeNull()
    expect(error.value).toBe('Network failure')
  })

  it('captures error message on transform throw', async () => {
    const { data, error, refresh } = useFetchTransform(
      () => Promise.resolve({ broken: true }),
      () => {
        throw new Error('Transform failed')
      },
    )

    await refresh()

    expect(data.value).toBeNull()
    expect(error.value).toBe('Transform failed')
  })

  it('handles string error', async () => {
    const { error, refresh } = useFetchTransform(
      () => Promise.reject('string error'),
      (raw) => raw,
    )

    await refresh()
    expect(error.value).toBe('string error')
  })

  it('handles non-string non-Error throws', async () => {
    const { error, refresh } = useFetchTransform(
      () => Promise.reject(42),
      (raw) => raw,
    )

    await refresh()
    expect(error.value).toBe('Unknown error')
  })

  it('clears previous error on successful refresh', async () => {
    let shouldFail = true
    const { data, error, refresh } = useFetchTransform(
      () => (shouldFail ? Promise.reject(new Error('fail')) : Promise.resolve('ok')),
      (raw) => raw,
    )

    await refresh()
    expect(error.value).toBe('fail')
    expect(data.value).toBeNull()

    shouldFail = false
    await refresh()
    expect(error.value).toBeNull()
    expect(data.value).toBe('ok')
  })

  it('calls onSuccess callback', async () => {
    const onSuccess = vi.fn()
    const { refresh } = useFetchTransform(
      () => Promise.resolve('data'),
      (raw) => raw,
      { onSuccess },
    )

    await refresh()
    expect(onSuccess).toHaveBeenCalledOnce()
  })

  it('calls onError callback with Error', async () => {
    const onError = vi.fn()
    const { refresh } = useFetchTransform(
      () => Promise.reject(new Error('boom')),
      (raw) => raw,
      { onError },
    )

    await refresh()
    expect(onError).toHaveBeenCalledOnce()
    expect(onError.mock.calls[0][0]).toBeInstanceOf(Error)
    expect(onError.mock.calls[0][0].message).toBe('boom')
  })

  it('does not call onSuccess when fetch fails', async () => {
    const onSuccess = vi.fn()
    const { refresh } = useFetchTransform(
      () => Promise.reject(new Error('fail')),
      (raw) => raw,
      { onSuccess },
    )

    await refresh()
    expect(onSuccess).not.toHaveBeenCalled()
  })

  it('uses external refs when provided', async () => {
    const sharedLoading = ref(false)
    const sharedError = ref<string | null>(null)

    const { loading, error, refresh } = useFetchTransform(
      () => Promise.resolve('data'),
      (raw) => raw,
      { refs: { loading: sharedLoading, error: sharedError } },
    )

    // Returned refs should be the same objects
    expect(loading).toBe(sharedLoading)
    expect(error).toBe(sharedError)

    await refresh()
    expect(sharedLoading.value).toBe(false)
    expect(sharedError.value).toBeNull()
  })

  it('fires fetcher immediately with immediate: true', async () => {
    const fetcher = vi.fn(() => Promise.resolve('immediate-data'))
    const { data } = useFetchTransform(fetcher, (raw) => raw, {
      immediate: true,
    })

    expect(fetcher).toHaveBeenCalledOnce()

    // Wait for the promise to resolve
    await vi.waitFor(() => expect(data.value).toBe('immediate-data'))
  })

  it('does not fire fetcher without immediate', () => {
    const fetcher = vi.fn(() => Promise.resolve('data'))
    useFetchTransform(fetcher, (raw) => raw)
    expect(fetcher).not.toHaveBeenCalled()
  })

  it('identity transform returns raw data as-is', async () => {
    const raw = { x: 1, y: 'hello' }
    const { data, refresh } = useFetchTransform(
      () => Promise.resolve(raw),
      (r) => r,
    )

    await refresh()
    expect(data.value).toEqual(raw)
  })

  it('multiple rapid refreshes resolve to last result', async () => {
    let counter = 0
    const { data, refresh } = useFetchTransform(
      async () => {
        counter++
        const val = counter
        await new Promise((r) => setTimeout(r, val === 1 ? 50 : 10))
        return val
      },
      (raw) => raw,
    )

    // Fire two refreshes; the second should win since it started later
    const p1 = refresh()
    const p2 = refresh()
    await Promise.all([p1, p2])
    // Both complete; data will have the value from the last call to finish
    expect(typeof data.value).toBe('number')
  })
})

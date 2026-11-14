/**
 * Request contract and ordering tests for the canonical Rosette Compare client.
 * Axios stays mocked. Creating the composable must not touch the network.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import axios from 'axios'
import { useRosetteCompareApi, type DiffOut, type GeometryPayload } from '../useRosetteCompareApi'

vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

const callsAfterImport =
  vi.mocked(axios.get).mock.calls.length + vi.mocked(axios.post).mock.calls.length

const GEOMETRY: GeometryPayload = {
  paths: [{ points: [[0, 0], [10, 0], [10, 10]], meta: { color: 'green' } }],
}
const OTHER_GEOMETRY: GeometryPayload = {
  paths: [{ points: [[1, 1], [4, 1], [4, 4]], meta: { color: 'red' } }],
}
const BASELINE = {
  id: 'baseline-1',
  name: 'Herringbone',
  lane: 'rosette',
  created_at: '2026-02-01T12:00:00Z',
}
const STATS = {
  baseline_path_count: 2,
  current_path_count: 3,
  added_paths: 1,
  removed_paths: 0,
  unchanged_paths: 2,
}

function diffBody(overrides: Partial<DiffOut> = {}): DiffOut {
  return {
    baseline_id: 'baseline-1',
    lane: 'rosette',
    stats: STATS,
    baseline_geometry: OTHER_GEOMETRY,
    current_geometry: GEOMETRY,
    ...overrides,
  }
}

function deferred<T>(): {
  promise: Promise<T>
  resolve: (value: T) => void
  reject: (reason: unknown) => void
} {
  let resolvePromise: (value: T) => void = () => undefined
  let rejectPromise: (reason: unknown) => void = () => undefined
  const promise = new Promise<T>((resolve, reject) => {
    resolvePromise = resolve
    rejectPromise = reject
  })
  return { promise, resolve: resolvePromise, reject: rejectPromise }
}

function queueTwo<T>() {
  const older = deferred<T>()
  const newer = deferred<T>()
  return { older, newer }
}

describe('useRosetteCompareApi', () => {
  beforeEach(() => {
    vi.mocked(axios.get).mockReset()
    vi.mocked(axios.post).mockReset()
    vi.spyOn(console, 'error').mockImplementation(() => undefined)
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('issues no request when the module is imported or the composable is created', () => {
    expect(callsAfterImport).toBe(0)
    useRosetteCompareApi()
    expect(axios.get).not.toHaveBeenCalled()
    expect(axios.post).not.toHaveBeenCalled()
  })

  it('loads baselines with one GET for the rosette lane', async () => {
    vi.mocked(axios.get).mockResolvedValueOnce({ data: [BASELINE] })
    const api = useRosetteCompareApi()

    await api.loadBaselines()

    expect(axios.get).toHaveBeenCalledTimes(1)
    expect(axios.get).toHaveBeenCalledWith('/api/compare/baselines', {
      params: { lane: 'rosette' },
    })
    expect(api.baselines.value).toEqual([BASELINE])
    expect(api.loading.value).toBe(false)
    expect(api.error.value).toBe('')
  })

  it('saves the exact name, lane, and geometry, reloads, and returns the created id', async () => {
    vi.mocked(axios.post).mockResolvedValueOnce({ data: { id: 'created-9' } })
    vi.mocked(axios.get).mockResolvedValueOnce({ data: [{ ...BASELINE, id: 'created-9' }] })
    const api = useRosetteCompareApi()

    const id = await api.saveBaseline('  Herringbone  ', GEOMETRY)

    expect(id).toBe('created-9')
    expect(axios.post).toHaveBeenCalledTimes(1)
    expect(axios.post).toHaveBeenCalledWith('/api/compare/baselines', {
      name: '  Herringbone  ',
      lane: 'rosette',
      geometry: GEOMETRY,
    })
    expect(axios.get).toHaveBeenCalledTimes(1)
    expect(axios.get).toHaveBeenCalledWith('/api/compare/baselines', {
      params: { lane: 'rosette' },
    })
    expect(api.baselines.value).toEqual([{ ...BASELINE, id: 'created-9' }])
    expect(api.loading.value).toBe(false)
  })

  it('keeps loading true while saveBaseline reloads baselines', async () => {
    const reload = deferred<{ data: typeof BASELINE[] }>()
    const earlier = deferred<{ data: typeof BASELINE[] }>()
    vi.mocked(axios.get)
      .mockReturnValueOnce(earlier.promise)
      .mockReturnValueOnce(reload.promise)
    vi.mocked(axios.post).mockResolvedValueOnce({ data: { id: 'created-9' } })
    const api = useRosetteCompareApi()

    const listed = api.loadBaselines()
    const saved = api.saveBaseline('Saved', GEOMETRY)
    await vi.waitFor(() => expect(axios.get).toHaveBeenCalledTimes(2))
    expect(api.loading.value).toBe(true)

    reload.resolve({ data: [{ ...BASELINE, id: 'created-9' }] })
    await saved
    expect(api.loading.value).toBe(true)
    expect(api.baselines.value).toEqual([{ ...BASELINE, id: 'created-9' }])

    earlier.resolve({ data: [BASELINE] })
    await listed
    expect(api.baselines.value).toEqual([{ ...BASELINE, id: 'created-9' }])
    expect(api.loading.value).toBe(false)
    expect(api.error.value).toBe('')
  })

  it('does not request or clear baselines when the name or geometry is missing', async () => {
    vi.mocked(axios.get).mockResolvedValueOnce({ data: [BASELINE] })
    const api = useRosetteCompareApi()
    await api.loadBaselines()
    vi.mocked(axios.post).mockClear()
    vi.mocked(axios.get).mockClear()

    expect(await api.saveBaseline('', GEOMETRY)).toBeNull()
    expect(await api.saveBaseline('Name', null as unknown as GeometryPayload)).toBeNull()

    expect(axios.post).not.toHaveBeenCalled()
    expect(axios.get).not.toHaveBeenCalled()
    expect(api.baselines.value).toEqual([BASELINE])
    expect(api.loading.value).toBe(false)
  })

  it('loads one baseline from the encoded URL and stores its geometry', async () => {
    vi.mocked(axios.get).mockResolvedValueOnce({ data: { geometry: GEOMETRY } })
    const api = useRosetteCompareApi()

    const geometry = await api.loadBaselineGeometry('baseline/1 a')

    expect(geometry).toEqual(GEOMETRY)
    expect(api.baselineGeometry.value).toEqual(GEOMETRY)
    expect(axios.get).toHaveBeenCalledTimes(1)
    expect(axios.get).toHaveBeenCalledWith('/api/compare/baselines/baseline%2F1%20a')
  })

  it('posts the exact diff body and omits a blank job id or preset', async () => {
    vi.mocked(axios.post).mockResolvedValueOnce({ data: diffBody() })
    const api = useRosetteCompareApi()

    const result = await api.runDiff('baseline-1', GEOMETRY, {
      jobId: '   ',
      preset: '',
    })

    expect(result?.stats).toEqual(STATS)
    expect(api.diffStats.value).toEqual(STATS)
    expect(api.baselineGeometry.value).toEqual(OTHER_GEOMETRY)
    expect(axios.post).toHaveBeenCalledWith('/api/compare/diff', {
      baseline_id: 'baseline-1',
      lane: 'rosette',
      current_geometry: GEOMETRY,
    })
  })

  it('trims a nonblank job id and preset onto the diff body', async () => {
    vi.mocked(axios.post).mockResolvedValueOnce({ data: diffBody() })
    const api = useRosetteCompareApi()

    await api.runDiff('baseline-1', GEOMETRY, {
      jobId: '  rosette_job_001  ',
      preset: '  Safe  ',
    })

    expect(axios.post).toHaveBeenCalledWith('/api/compare/diff', {
      baseline_id: 'baseline-1',
      lane: 'rosette',
      current_geometry: GEOMETRY,
      job_id: 'rosette_job_001',
      preset: 'Safe',
    })
  })

  it('does not request a diff without a baseline id or current geometry', async () => {
    const api = useRosetteCompareApi()

    expect(await api.runDiff('', GEOMETRY)).toBeNull()
    expect(await api.runDiff('baseline-1', null as unknown as GeometryPayload)).toBeNull()

    expect(axios.post).not.toHaveBeenCalled()
    expect(api.loading.value).toBe(false)
  })

  it('keeps the last successful baselines, geometry, and diff when a later request fails', async () => {
    vi.mocked(axios.get)
      .mockResolvedValueOnce({ data: [BASELINE] })
      .mockResolvedValueOnce({ data: { geometry: GEOMETRY } })
    vi.mocked(axios.post).mockResolvedValueOnce({ data: diffBody() })
    const api = useRosetteCompareApi()
    await api.loadBaselines()
    await api.loadBaselineGeometry('baseline-1')
    await api.runDiff('baseline-1', GEOMETRY)

    vi.mocked(axios.get).mockRejectedValueOnce(new Error('list down'))
    vi.mocked(axios.post).mockRejectedValueOnce(new Error('diff down'))
    await api.loadBaselines()
    await api.runDiff('baseline-1', GEOMETRY)
    vi.mocked(axios.get).mockRejectedValueOnce(new Error('geometry down'))
    expect(await api.loadBaselineGeometry('baseline-1')).toBeNull()

    expect(api.baselines.value).toEqual([BASELINE])
    expect(api.baselineGeometry.value).toEqual(OTHER_GEOMETRY)
    expect(api.diffStats.value).toEqual(STATS)
    expect(api.error.value).toBe('Failed to load baseline geometry')
    expect(api.loading.value).toBe(false)
  })

  it('does not let an older geometry response replace a newer selection', async () => {
    const { older, newer } = queueTwo<{ data: { geometry: GeometryPayload } }>()
    vi.mocked(axios.get)
      .mockReturnValueOnce(older.promise)
      .mockReturnValueOnce(newer.promise)
    const api = useRosetteCompareApi()

    const first = api.loadBaselineGeometry('older-id')
    const second = api.loadBaselineGeometry('newer-id')
    newer.resolve({ data: { geometry: GEOMETRY } })
    await second
    older.resolve({ data: { geometry: OTHER_GEOMETRY } })
    expect(await first).toBeNull()

    expect(api.baselineGeometry.value).toEqual(GEOMETRY)
    expect(console.error).not.toHaveBeenCalled()
  })

  it('drops a geometry response that resolves after the selection is cleared', async () => {
    const gate = deferred<{ data: { geometry: GeometryPayload } }>()
    vi.mocked(axios.get).mockReturnValueOnce(gate.promise)
    const api = useRosetteCompareApi()

    const pending = api.loadBaselineGeometry('baseline-1')
    const cleared = api.loadBaselineGeometry('')
    expect(api.baselineGeometry.value).toBeNull()
    expect(axios.get).toHaveBeenCalledTimes(1)

    gate.resolve({ data: { geometry: GEOMETRY } })
    expect(await pending).toBeNull()
    expect(await cleared).toBeNull()
    expect(api.baselineGeometry.value).toBeNull()
    expect(console.error).not.toHaveBeenCalled()
  })

  it('does not let an older geometry failure replace a newer geometry', async () => {
    const { older, newer } = queueTwo<{ data: { geometry: GeometryPayload } }>()
    vi.mocked(axios.get)
      .mockReturnValueOnce(older.promise)
      .mockReturnValueOnce(newer.promise)
    const api = useRosetteCompareApi()

    const first = api.loadBaselineGeometry('older-id')
    const second = api.loadBaselineGeometry('newer-id')
    newer.resolve({ data: { geometry: GEOMETRY } })
    await second
    older.reject(new Error('late'))
    expect(await first).toBeNull()

    expect(api.baselineGeometry.value).toEqual(GEOMETRY)
    expect(api.error.value).toBe('')
    expect(console.error).not.toHaveBeenCalled()
  })

  it('does not let an older diff success replace a newer comparison', async () => {
    const olderBody = diffBody({
      baseline_id: 'older',
      stats: { ...STATS, added_paths: 9 },
      baseline_geometry: OTHER_GEOMETRY,
    })
    const newerBody = diffBody({
      baseline_id: 'newer',
      stats: { ...STATS, added_paths: 1 },
      baseline_geometry: GEOMETRY,
    })
    const { older, newer } = queueTwo<{ data: DiffOut }>()
    vi.mocked(axios.post)
      .mockReturnValueOnce(older.promise)
      .mockReturnValueOnce(newer.promise)
    const seen: DiffOut[] = []
    const api = useRosetteCompareApi({
      onDiffComplete: (result) => {
        seen.push(result)
      },
    })

    const first = api.runDiff('older', GEOMETRY)
    const second = api.runDiff('newer', OTHER_GEOMETRY)
    expect(api.loading.value).toBe(true)
    newer.resolve({ data: newerBody })
    await second
    expect(api.loading.value).toBe(true)
    older.resolve({ data: olderBody })
    expect(await first).toBeNull()

    expect(api.diffStats.value).toEqual(newerBody.stats)
    expect(api.baselineGeometry.value).toEqual(GEOMETRY)
    expect(seen).toEqual([newerBody])
    expect(api.loading.value).toBe(false)
    expect(api.error.value).toBe('')
  })

  it('does not let an older diff failure replace a newer error or loading flag', async () => {
    const { older, newer } = queueTwo<{ data: DiffOut }>()
    vi.mocked(axios.post)
      .mockReturnValueOnce(older.promise)
      .mockReturnValueOnce(newer.promise)
    const api = useRosetteCompareApi()
    api.diffStats.value = STATS

    const first = api.runDiff('older', GEOMETRY)
    const second = api.runDiff('newer', GEOMETRY)
    newer.reject(new Error('newer failed'))
    await second
    expect(api.error.value).toBe('Failed to run diff')
    expect(api.loading.value).toBe(true)
    expect(api.diffStats.value).toEqual(STATS)

    older.reject(new Error('older failed'))
    expect(await first).toBeNull()
    expect(api.error.value).toBe('Failed to run diff')
    expect(api.diffStats.value).toEqual(STATS)
    expect(api.loading.value).toBe(false)
    expect(console.error).toHaveBeenCalledTimes(1)
  })

  it('does not let an older diff success replace a newer failure', async () => {
    const { older, newer } = queueTwo<{ data: DiffOut }>()
    vi.mocked(axios.post)
      .mockReturnValueOnce(older.promise)
      .mockReturnValueOnce(newer.promise)
    const api = useRosetteCompareApi()

    const first = api.runDiff('older', GEOMETRY)
    const second = api.runDiff('newer', GEOMETRY)
    newer.reject(new Error('newer failed'))
    await second
    older.resolve({ data: diffBody() })
    expect(await first).toBeNull()

    expect(api.diffStats.value).toBeNull()
    expect(api.baselineGeometry.value).toBeNull()
    expect(api.error.value).toBe('Failed to run diff')
    expect(api.loading.value).toBe(false)
  })

  it('does not let a failed save erase the last baseline list', async () => {
    vi.mocked(axios.get).mockResolvedValueOnce({ data: [BASELINE] })
    const api = useRosetteCompareApi()
    await api.loadBaselines()
    vi.mocked(axios.post).mockRejectedValueOnce(new Error('save down'))
    vi.mocked(axios.get).mockClear()

    expect(await api.saveBaseline('Name', GEOMETRY)).toBeNull()

    expect(axios.get).not.toHaveBeenCalled()
    expect(api.baselines.value).toEqual([BASELINE])
    expect(api.error.value).toBe('Failed to save baseline')
    expect(api.loading.value).toBe(false)
  })
  it('drops a pending diff when the baseline changes and keeps the new baseline geometry', async () => {
    const diffGate = deferred<{ data: DiffOut }>()
    vi.mocked(axios.post).mockReturnValueOnce(diffGate.promise)
    vi.mocked(axios.get).mockResolvedValueOnce({ data: { geometry: GEOMETRY } })
    const seen: DiffOut[] = []
    const api = useRosetteCompareApi({ onDiffComplete: (result) => seen.push(result) })

    const pending = api.runDiff('baseline-a', GEOMETRY)
    expect(await api.loadBaselineGeometry('baseline-b')).toEqual(GEOMETRY)
    diffGate.resolve({ data: diffBody({ baseline_id: 'baseline-a' }) })

    expect(await pending).toBeNull()
    expect(api.diffStats.value).toBeNull()
    expect(api.baselineGeometry.value).toEqual(GEOMETRY)
    expect(seen).toEqual([])
    expect(api.loading.value).toBe(false)
    expect(api.error.value).toBe('')
  })

  it('drops a pending diff when the baseline is cleared', async () => {
    const diffGate = deferred<{ data: DiffOut }>()
    vi.mocked(axios.post).mockReturnValueOnce(diffGate.promise)
    const api = useRosetteCompareApi()

    const pending = api.runDiff('baseline-a', GEOMETRY)
    expect(await api.loadBaselineGeometry('')).toBeNull()
    diffGate.resolve({ data: diffBody({ baseline_id: 'baseline-a' }) })

    expect(await pending).toBeNull()
    expect(api.diffStats.value).toBeNull()
    expect(api.baselineGeometry.value).toBeNull()
    expect(api.loading.value).toBe(false)
  })

  it('drops a pending diff failure after the baseline changes', async () => {
    const diffGate = deferred<{ data: DiffOut }>()
    vi.mocked(axios.post).mockReturnValueOnce(diffGate.promise)
    vi.mocked(axios.get).mockResolvedValueOnce({ data: { geometry: GEOMETRY } })
    const api = useRosetteCompareApi()

    const pending = api.runDiff('baseline-a', GEOMETRY)
    await api.loadBaselineGeometry('baseline-b')
    diffGate.reject(new Error('late'))

    expect(await pending).toBeNull()
    expect(api.error.value).toBe('')
    expect(console.error).not.toHaveBeenCalled()
  })

  it('removes a shown diff as soon as another baseline is requested', async () => {
    vi.mocked(axios.post).mockResolvedValueOnce({ data: diffBody({ baseline_id: 'baseline-a' }) })
    const geometryGate = deferred<{ data: { geometry: GeometryPayload } }>()
    vi.mocked(axios.get).mockReturnValueOnce(geometryGate.promise)
    const api = useRosetteCompareApi()
    await api.runDiff('baseline-a', GEOMETRY)
    expect(api.diffStats.value).toEqual(STATS)

    const loading = api.loadBaselineGeometry('baseline-b')
    expect(api.diffStats.value).toBeNull()
    expect(api.baselineGeometry.value).toBeNull()

    geometryGate.reject(new Error('geometry down'))
    expect(await loading).toBeNull()
    expect(api.diffStats.value).toBeNull()
    expect(api.baselineGeometry.value).toBeNull()
  })

  it('drops a pending diff when clearDiff is called for a changed current geometry', async () => {
    const diffGate = deferred<{ data: DiffOut }>()
    vi.mocked(axios.get).mockResolvedValueOnce({ data: { geometry: GEOMETRY } })
    vi.mocked(axios.post).mockReturnValueOnce(diffGate.promise)
    const api = useRosetteCompareApi()
    await api.loadBaselineGeometry('baseline-1')

    const pending = api.runDiff('baseline-1', GEOMETRY)
    api.clearDiff()
    diffGate.resolve({ data: diffBody() })

    expect(await pending).toBeNull()
    expect(api.diffStats.value).toBeNull()
    expect(api.baselineGeometry.value).toEqual(GEOMETRY)
    expect(api.loading.value).toBe(false)
  })

  it('restores the plain baseline geometry when a shown diff is cleared', async () => {
    vi.mocked(axios.get).mockResolvedValueOnce({ data: { geometry: GEOMETRY } })
    vi.mocked(axios.post).mockResolvedValueOnce({ data: diffBody({ baseline_geometry: OTHER_GEOMETRY }) })
    const api = useRosetteCompareApi()
    await api.loadBaselineGeometry('baseline-1')
    await api.runDiff('baseline-1', GEOMETRY)
    expect(api.baselineGeometry.value).toEqual(OTHER_GEOMETRY)

    api.clearDiff()

    expect(api.diffStats.value).toBeNull()
    expect(api.baselineGeometry.value).toEqual(GEOMETRY)
  })

  it('keeps a diff that lands before the plain geometry of the same baseline', async () => {
    const geometryGate = deferred<{ data: { geometry: GeometryPayload } }>()
    vi.mocked(axios.get).mockReturnValueOnce(geometryGate.promise)
    vi.mocked(axios.post).mockResolvedValueOnce({ data: diffBody({ baseline_geometry: OTHER_GEOMETRY }) })
    const api = useRosetteCompareApi()

    const loading = api.loadBaselineGeometry('baseline-1')
    await api.runDiff('baseline-1', GEOMETRY)
    geometryGate.resolve({ data: { geometry: GEOMETRY } })

    expect(await loading).toBeNull()
    expect(api.diffStats.value).toEqual(STATS)
    expect(api.baselineGeometry.value).toEqual(OTHER_GEOMETRY)
    api.clearDiff()
    expect(api.baselineGeometry.value).toEqual(GEOMETRY)
  })

  it('keeps a save failure that resolves after a later geometry load started', async () => {
    const saveGate = deferred<{ data: { id: string } }>()
    vi.mocked(axios.post).mockReturnValueOnce(saveGate.promise)
    vi.mocked(axios.get).mockResolvedValueOnce({ data: { geometry: GEOMETRY } })
    const api = useRosetteCompareApi()

    const saving = api.saveBaseline('Name', GEOMETRY)
    await api.loadBaselineGeometry('baseline-1')
    saveGate.reject(new Error('save down'))

    expect(await saving).toBeNull()
    expect(api.error.value).toBe('Failed to save baseline')
    expect(console.error).toHaveBeenCalledTimes(1)
  })

  it('does not let a successful request of one kind erase a standing failure of another', async () => {
    vi.mocked(axios.get)
      .mockRejectedValueOnce(new Error('list down'))
      .mockResolvedValueOnce({ data: { geometry: GEOMETRY } })
    const api = useRosetteCompareApi()
    await api.loadBaselines()
    await api.loadBaselineGeometry('baseline-1')

    expect(api.error.value).toBe('Failed to load baselines')

    vi.mocked(axios.get).mockResolvedValueOnce({ data: [BASELINE] })
    await api.loadBaselines()
    expect(api.error.value).toBe('')
  })

  it('shows the most recent standing failure across operations', async () => {
    vi.mocked(axios.get)
      .mockRejectedValueOnce(new Error('list down'))
      .mockRejectedValueOnce(new Error('geometry down'))
    const api = useRosetteCompareApi()
    await api.loadBaselines()
    await api.loadBaselineGeometry('baseline-1')
    expect(api.error.value).toBe('Failed to load baseline geometry')

    vi.mocked(axios.get).mockResolvedValueOnce({ data: { geometry: GEOMETRY } })
    await api.loadBaselineGeometry('baseline-1')
    expect(api.error.value).toBe('Failed to load baselines')
  })
})

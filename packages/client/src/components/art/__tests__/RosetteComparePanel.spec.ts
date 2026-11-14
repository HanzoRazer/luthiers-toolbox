/**
 * UI integration for RosetteComparePanel. Axios is mocked at the network
 * boundary; the panel reaches it only through useRosetteCompareApi.
 * The panel stays off the router.
 */
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import axios from 'axios'
import RosetteComparePanel from '../RosetteComparePanel.vue'

vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

const callsAfterImport =
  vi.mocked(axios.get).mock.calls.length + vi.mocked(axios.post).mock.calls.length

const CURRENT = {
  paths: [{ points: [[0, 0], [12, 0], [12, 8]], meta: { color: 'gray' } }],
}
const NEXT_GEOMETRY = {
  paths: [{ points: [[1, 1], [6, 1], [6, 6]], meta: { color: 'gray' } }],
}
const BASELINES = [
  { id: 'base-a', name: 'Alpha', lane: 'rosette', created_at: '2026-02-01T12:00:00Z' },
  { id: 'base-b', name: 'Beta', lane: 'rosette', created_at: '2026-02-02T12:00:00Z' },
]
const GEOM_A = {
  paths: [{ points: [[0, 0], [5, 0], [5, 5]], meta: { color: 'green' } }],
}
const GEOM_B = {
  paths: [{ points: [[0, 0], [8, 0], [8, 3]], meta: { color: 'red' } }],
}
const DIFF_CURRENT = {
  paths: [{ points: [[0, 0], [9, 0], [9, 9]], meta: { color: 'green' } }],
}
const DIFF_STATS = {
  baseline_path_count: 4,
  current_path_count: 5,
  added_paths: 2,
  removed_paths: 1,
  unchanged_paths: 3,
}
const JOB_KEY = 'ltb:compare:lastJobId'

const strokes: string[] = []
const ctx = {
  clearRect: vi.fn(),
  save: vi.fn(),
  restore: vi.fn(),
  fillRect: vi.fn(),
  beginPath: vi.fn(),
  moveTo: vi.fn(),
  lineTo: vi.fn(),
  closePath: vi.fn(),
  stroke: vi.fn(() => {
    strokes.push(ctx.strokeStyle)
  }),
  translate: vi.fn(),
  scale: vi.fn(),
  fillStyle: '',
  strokeStyle: '',
  lineWidth: 1,
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

function listPayload(includeCreated = false) {
  if (!includeCreated) return BASELINES
  return [
    {
      id: 'created-1',
      name: 'Saved rosette',
      lane: 'rosette',
      created_at: '2026-03-01T12:00:00Z',
    },
    ...BASELINES,
  ]
}

let saved = false

function installNetwork() {
  saved = false
  vi.mocked(axios.get).mockImplementation(async (url: string) => {
    if (url === '/api/compare/baselines') return { data: listPayload(saved) }
    if (url === '/api/compare/baselines/base-a') return { data: { geometry: GEOM_A } }
    if (url === '/api/compare/baselines/base-b') return { data: { geometry: GEOM_B } }
    if (url === '/api/compare/baselines/created-1') return { data: { geometry: GEOM_A } }
    throw new Error(`unexpected GET ${url}`)
  })
  vi.mocked(axios.post).mockImplementation(async (url: string, body?: unknown) => {
    if (url === '/api/compare/baselines') {
      saved = true
      return { data: { id: 'created-1' } }
    }
    if (url === '/api/compare/diff') {
      const payload = body as { baseline_id: string }
      return {
        data: {
          baseline_id: payload.baseline_id,
          lane: 'rosette',
          stats: DIFF_STATS,
          baseline_geometry: GEOM_B,
          current_geometry: DIFF_CURRENT,
        },
      }
    }
    throw new Error(`unexpected POST ${url}`)
  })
}

function installCanvas() {
  strokes.length = 0
  HTMLCanvasElement.prototype.getContext = vi.fn(function (this: HTMLCanvasElement) {
    if (!this.width) this.width = 200
    if (!this.height) this.height = 200
    return ctx as unknown as CanvasRenderingContext2D
  }) as unknown as typeof HTMLCanvasElement.prototype.getContext
}

async function mountPanel(currentGeometry: typeof CURRENT | null = CURRENT): Promise<VueWrapper> {
  const wrapper = mount(RosetteComparePanel, {
    props: { currentGeometry, jobId: null },
  })
  await flushPromises()
  return wrapper
}

function button(wrapper: VueWrapper, label: string) {
  const found = wrapper.findAll('button').find((item) => item.text() === label)
  if (!found) throw new Error(`missing button ${label}`)
  return found
}

function inputs(wrapper: VueWrapper) {
  const fields = wrapper.findAll('input')
  return {
    name: fields[0],
    job: fields[1],
    preset: fields[2],
  }
}

async function chooseBaseline(wrapper: VueWrapper, id: string) {
  await wrapper.get('select').setValue(id)
  await flushPromises()
}

describe('RosetteComparePanel', () => {
  beforeEach(() => {
    localStorage.clear()
    installCanvas()
    installNetwork()
    vi.spyOn(console, 'error').mockImplementation(() => undefined)
  })

  afterEach(() => {
    vi.restoreAllMocks()
    localStorage.clear()
  })

  it('does not import axios and does not request while the module is imported', () => {
    const source = readFileSync(
      resolve(process.cwd(), 'src/components/art/RosetteComparePanel.vue'),
      'utf8',
    )
    expect(source).not.toMatch(/from ['"]axios['"]/)
    expect(source).not.toMatch(/axios\./)
    expect(source).toContain('useRosetteCompareApi')
    expect(callsAfterImport).toBe(0)
  })

  it('loads baselines once on mount', async () => {
    const wrapper = await mountPanel()
    const listCalls = vi.mocked(axios.get).mock.calls.filter((call) => call[0] === '/api/compare/baselines')
    expect(listCalls).toEqual([['/api/compare/baselines', { params: { lane: 'rosette' } }]])
    expect(axios.post).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('Alpha')
    expect(wrapper.text()).toContain('Beta')
    wrapper.unmount()
  })

  it('selects the id returned by a successful save', async () => {
    const wrapper = await mountPanel()
    await inputs(wrapper).name.setValue('Saved rosette')
    await button(wrapper, 'Save baseline').trigger('click')
    await flushPromises()

    expect(axios.post).toHaveBeenCalledWith('/api/compare/baselines', {
      name: 'Saved rosette',
      lane: 'rosette',
      geometry: CURRENT,
    })
    expect((wrapper.get('select').element as HTMLSelectElement).value).toBe('created-1')
    expect(axios.get).toHaveBeenCalledWith('/api/compare/baselines/created-1')
    wrapper.unmount()
  })

  it('loads and draws a selected baseline', async () => {
    const wrapper = await mountPanel()
    const before = strokes.length
    await chooseBaseline(wrapper, 'base-a')

    expect(axios.get).toHaveBeenCalledWith('/api/compare/baselines/base-a')
    expect(strokes.slice(before)).toContain('#22c55e')
    expect(wrapper.text()).toContain('Alpha')
    wrapper.unmount()
  })

  it('updates statistics and both canvases after compare', async () => {
    const wrapper = await mountPanel()
    await chooseBaseline(wrapper, 'base-a')
    const before = strokes.length
    await button(wrapper, 'Compare').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toMatch(/Baseline paths:\s*4/)
    expect(wrapper.text()).toMatch(/Current paths:\s*5/)
    expect(wrapper.text()).toMatch(/Added:\s*2/)
    expect(wrapper.text()).toMatch(/Removed:\s*1/)
    expect(wrapper.text()).toMatch(/Unchanged:\s*3/)
    const drawn = strokes.slice(before)
    expect(drawn).toContain('#ef4444')
    expect(drawn).toContain('#22c55e')
    wrapper.unmount()
  })

  it('stores the trimmed job id and emits it when a comparison is requested', async () => {
    const wrapper = await mountPanel()
    await chooseBaseline(wrapper, 'base-a')
    await inputs(wrapper).job.setValue('  job-9  ')
    await inputs(wrapper).preset.setValue('  Safe  ')
    await button(wrapper, 'Compare').trigger('click')
    await flushPromises()

    expect(localStorage.getItem(JOB_KEY)).toBe('job-9')
    expect(wrapper.emitted('update:job-id')).toContainEqual(['job-9'])
    expect(axios.post).toHaveBeenCalledWith('/api/compare/diff', {
      baseline_id: 'base-a',
      lane: 'rosette',
      current_geometry: CURRENT,
      job_id: 'job-9',
      preset: 'Safe',
    })
    wrapper.unmount()
  })

  it('emits the job id from the input before a comparison is requested', async () => {
    const wrapper = await mountPanel()
    await inputs(wrapper).job.setValue('typed-job')

    expect(wrapper.emitted('update:job-id')).toEqual([['typed-job']])
    expect(axios.post).not.toHaveBeenCalled()
    wrapper.unmount()
  })

  it('omits a blank job id and preset from the comparison', async () => {
    const wrapper = await mountPanel()
    await chooseBaseline(wrapper, 'base-b')
    await inputs(wrapper).job.setValue('   ')
    await inputs(wrapper).preset.setValue('   ')
    await button(wrapper, 'Compare').trigger('click')
    await flushPromises()

    expect(localStorage.getItem(JOB_KEY)).toBeNull()
    expect(axios.post).toHaveBeenCalledWith('/api/compare/diff', {
      baseline_id: 'base-b',
      lane: 'rosette',
      current_geometry: CURRENT,
    })
    wrapper.unmount()
  })

  it('restores the stored job id on mount and emits it', async () => {
    localStorage.setItem(JOB_KEY, 'stored-job')
    const wrapper = await mountPanel()

    expect((inputs(wrapper).job.element as HTMLInputElement).value).toBe('stored-job')
    expect(wrapper.emitted('update:job-id')).toContainEqual(['stored-job'])
    wrapper.unmount()
  })

  it('redraws a changed current geometry without another request', async () => {
    const wrapper = await mountPanel()
    const gets = vi.mocked(axios.get).mock.calls.length
    const posts = vi.mocked(axios.post).mock.calls.length
    const before = strokes.length

    await wrapper.setProps({ currentGeometry: NEXT_GEOMETRY })
    await flushPromises()

    expect(vi.mocked(axios.get).mock.calls.length).toBe(gets)
    expect(vi.mocked(axios.post).mock.calls.length).toBe(posts)
    expect(strokes.length).toBeGreaterThan(before)
    wrapper.unmount()
  })

  it('blocks save when the name is blank or the geometry is missing', async () => {
    const named = await mountPanel()
    expect((button(named, 'Save baseline').element as HTMLButtonElement).disabled).toBe(true)
    await button(named, 'Save baseline').trigger('click')
    expect(axios.post).not.toHaveBeenCalled()
    named.unmount()

    const empty = await mountPanel(null)
    expect((button(empty, 'Save baseline').element as HTMLButtonElement).disabled).toBe(true)
    await inputs(empty).name.setValue('Named')
    expect((button(empty, 'Save baseline').element as HTMLButtonElement).disabled).toBe(true)
    await button(empty, 'Save baseline').trigger('click')
    expect(axios.post).not.toHaveBeenCalled()
    empty.unmount()
  })

  it('blocks compare when the selection or the geometry is missing', async () => {
    const wrapper = await mountPanel()
    expect((button(wrapper, 'Compare').element as HTMLButtonElement).disabled).toBe(true)
    await button(wrapper, 'Compare').trigger('click')
    expect(axios.post).not.toHaveBeenCalled()
    wrapper.unmount()

    const empty = await mountPanel(null)
    await chooseBaseline(empty, 'base-a')
    expect((button(empty, 'Compare').element as HTMLButtonElement).disabled).toBe(true)
    await button(empty, 'Compare').trigger('click')
    expect(axios.post).not.toHaveBeenCalled()
    empty.unmount()
  })

  it('keeps the last comparison on screen when a later compare fails', async () => {
    const wrapper = await mountPanel()
    await chooseBaseline(wrapper, 'base-a')
    await button(wrapper, 'Compare').trigger('click')
    await flushPromises()
    vi.mocked(axios.post).mockRejectedValueOnce(new Error('diff down'))

    await button(wrapper, 'Compare').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toMatch(/Baseline paths:\s*4/)
    expect(wrapper.text()).toMatch(/Added:\s*2/)
    wrapper.unmount()
  })

  it('does not draw an older baseline over a newer selection', async () => {
    const older = deferred<{ data: { geometry: typeof GEOM_A } }>()
    const newer = deferred<{ data: { geometry: typeof GEOM_B } }>()
    vi.mocked(axios.get).mockImplementation((url: string) => {
      if (url === '/api/compare/baselines') return Promise.resolve({ data: BASELINES })
      if (url === '/api/compare/baselines/base-a') return older.promise
      if (url === '/api/compare/baselines/base-b') return newer.promise
      return Promise.reject(new Error(`unexpected GET ${url}`))
    })
    const wrapper = await mountPanel()
    await wrapper.get('select').setValue('base-a')
    await wrapper.get('select').setValue('base-b')
    const before = strokes.length

    older.resolve({ data: { geometry: GEOM_A } })
    await flushPromises()
    expect(strokes.slice(before)).not.toContain('#22c55e')

    newer.resolve({ data: { geometry: GEOM_B } })
    await flushPromises()
    expect(strokes.slice(before)).toContain('#ef4444')
    expect(strokes.slice(before)).not.toContain('#22c55e')
    wrapper.unmount()
  })

  it('does not draw a baseline that resolves after the selection is cleared', async () => {
    const gate = deferred<{ data: { geometry: typeof GEOM_A } }>()
    vi.mocked(axios.get).mockImplementation((url: string) => {
      if (url === '/api/compare/baselines') return Promise.resolve({ data: BASELINES })
      if (url === '/api/compare/baselines/base-a') return gate.promise
      return Promise.reject(new Error(`unexpected GET ${url}`))
    })
    const wrapper = await mountPanel()
    await wrapper.get('select').setValue('base-a')
    await wrapper.get('select').setValue('')
    const before = strokes.length

    gate.resolve({ data: { geometry: GEOM_A } })
    await flushPromises()

    expect(strokes.slice(before)).not.toContain('#22c55e')
    expect((wrapper.get('select').element as HTMLSelectElement).value).toBe('')
    wrapper.unmount()
  })
  function gateDiff() {
    const gate = deferred<{ data: unknown }>()
    vi.mocked(axios.post).mockImplementationOnce(() => gate.promise as never)
    return gate
  }

  const STALE_DIFF = {
    data: {
      baseline_id: 'base-a',
      lane: 'rosette',
      stats: DIFF_STATS,
      baseline_geometry: GEOM_B,
      current_geometry: DIFF_CURRENT,
    },
  }

  it('does not show a pending comparison after the baseline changes', async () => {
    const wrapper = await mountPanel()
    await chooseBaseline(wrapper, 'base-a')
    const gate = gateDiff()
    await button(wrapper, 'Compare').trigger('click')
    await chooseBaseline(wrapper, 'base-b')
    const before = strokes.length

    gate.resolve(STALE_DIFF)
    await flushPromises()

    expect(wrapper.text()).not.toMatch(/Baseline paths:/)
    expect(strokes.slice(before)).toEqual([])
    // Any later redraw shows Beta's own geometry, not the stale comparison.
    await wrapper.setProps({ currentGeometry: NEXT_GEOMETRY })
    await flushPromises()
    expect(wrapper.text()).not.toMatch(/Baseline paths:/)
    expect(strokes.slice(before)).toContain('#ef4444')
    expect(strokes.slice(before)).not.toContain('#22c55e')
    wrapper.unmount()
  })

  it('does not show a pending comparison after the baseline is cleared', async () => {
    const wrapper = await mountPanel()
    await chooseBaseline(wrapper, 'base-a')
    const gate = gateDiff()
    await button(wrapper, 'Compare').trigger('click')
    await chooseBaseline(wrapper, '')
    const before = strokes.length

    gate.resolve(STALE_DIFF)
    await flushPromises()

    expect(wrapper.text()).not.toMatch(/Baseline paths:/)
    expect(strokes.slice(before)).toEqual([])
    wrapper.unmount()
  })

  it('removes shown statistics when the baseline changes', async () => {
    const wrapper = await mountPanel()
    await chooseBaseline(wrapper, 'base-a')
    await button(wrapper, 'Compare').trigger('click')
    await flushPromises()
    expect(wrapper.text()).toMatch(/Baseline paths:\s*4/)

    await chooseBaseline(wrapper, 'base-b')

    expect(wrapper.text()).not.toMatch(/Baseline paths:/)
    wrapper.unmount()
  })

  it('does not show a pending comparison after the current geometry changes', async () => {
    const wrapper = await mountPanel()
    await chooseBaseline(wrapper, 'base-a')
    const gate = gateDiff()
    await button(wrapper, 'Compare').trigger('click')
    await wrapper.setProps({ currentGeometry: NEXT_GEOMETRY })
    await flushPromises()
    const before = strokes.length

    gate.resolve(STALE_DIFF)
    await flushPromises()

    expect(wrapper.text()).not.toMatch(/Baseline paths:/)
    expect(strokes.slice(before)).toEqual([])
    wrapper.unmount()
  })

  it('removes shown statistics when the current geometry changes', async () => {
    const wrapper = await mountPanel()
    await chooseBaseline(wrapper, 'base-a')
    await button(wrapper, 'Compare').trigger('click')
    await flushPromises()
    expect(wrapper.text()).toMatch(/Baseline paths:\s*4/)
    const before = strokes.length

    await wrapper.setProps({ currentGeometry: NEXT_GEOMETRY })
    await flushPromises()

    expect(wrapper.text()).not.toMatch(/Baseline paths:/)
    // The baseline canvas returns to Alpha's own geometry, not the diff coloring.
    expect(strokes.slice(before)).toContain('#22c55e')
    expect(strokes.slice(before)).not.toContain('#ef4444')
    wrapper.unmount()
  })

  it('blanks the baseline canvas when the selection is cleared', async () => {
    const wrapper = await mountPanel()
    await chooseBaseline(wrapper, 'base-a')
    const baselineCanvas = wrapper.findAll('canvas')[0].element
    const cleared: HTMLCanvasElement[] = []
    HTMLCanvasElement.prototype.getContext = vi.fn(function (this: HTMLCanvasElement) {
      return {
        ...ctx,
        clearRect: () => {
          cleared.push(this)
        },
      } as unknown as CanvasRenderingContext2D
    }) as unknown as typeof HTMLCanvasElement.prototype.getContext

    await chooseBaseline(wrapper, '')

    expect(cleared).toContain(baselineCanvas)
    wrapper.unmount()
  })
})

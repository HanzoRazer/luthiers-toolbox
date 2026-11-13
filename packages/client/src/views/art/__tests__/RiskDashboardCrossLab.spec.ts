/**
 * Interaction tests for the canonical Risk Dashboard view.
 * Axios is mocked. The view stays off the router.
 */
import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter, type Router } from 'vue-router'
import type { VueWrapper } from '@vue/test-utils'
import axios from 'axios'
import RiskDashboardCrossLab from '../RiskDashboardCrossLab.vue'

vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
  },
}))

vi.mock('@/utils/downloadBlob', async () => {
  const actual = await vi.importActual<typeof import('@/utils/downloadBlob')>(
    '@/utils/downloadBlob',
  )
  return {
    ...actual,
    downloadBlob: vi.fn(),
  }
})

const callsAfterImport = vi.mocked(axios.get).mock.calls.length
const AGGREGATE_URL = '/api/compare/risk_aggregate'
const VIEWS_KEY = 'ltb_crosslab_risk_views'

const AGGREGATE_ROW = {
  lane: 'Rosette',
  preset: 'Safe',
  count: 2,
  avg_added: 1,
  avg_removed: 0,
  avg_unchanged: 3,
  risk_score: 0.2,
  risk_label: 'Low',
  added_series: [],
  removed_series: [],
}

function aggregateCalls(): number {
  return vi.mocked(axios.get).mock.calls.filter((call) => call[0] === AGGREGATE_URL).length
}

function viewRecord(
  name: string,
  filters: Record<string, string>,
  isDefault = false,
): Record<string, unknown> {
  return {
    id: `view_${name}`,
    name,
    filters,
    createdAt: '2026-02-22T06:01:32.000Z',
    isDefault,
    version: 2,
  }
}

async function mountDashboard(options?: {
  query?: Record<string, string>
  views?: Record<string, unknown>[]
}): Promise<{ wrapper: VueWrapper; router: Router }> {
  localStorage.clear()
  if (options?.views) {
    localStorage.setItem(VIEWS_KEY, JSON.stringify(options.views))
  }
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: '/', component: { template: '<div />' } }],
  })
  await router.push({ path: '/', query: options?.query ?? {} })
  await router.isReady()
  const wrapper = mount(RiskDashboardCrossLab, {
    global: { plugins: [router] },
  })
  await flushPromises()
  return { wrapper, router }
}

async function openDetails(wrapper: VueWrapper): Promise<void> {
  const button = wrapper.findAll('button').find((item) => item.text() === 'Details')
  if (!button) throw new Error('missing Details button')
  await button.trigger('click')
  await flushPromises()
}

async function clickLabel(wrapper: VueWrapper, label: string): Promise<void> {
  const button = wrapper.findAll('button').find((item) => item.text().includes(label))
  if (!button) throw new Error(`missing button ${label}`)
  await button.trigger('click')
  await flushPromises()
}

describe('Risk dashboard import', () => {
  it('does not request during module import', () => {
    expect(callsAfterImport).toBe(0)
  })
})

function installDashboardHarness(): void {
  beforeEach(() => {
    vi.mocked(axios.get).mockReset()
    vi.mocked(axios.get).mockImplementation((url: string) => {
      if (url === '/api/compare/risk_bucket_detail') {
        return Promise.resolve({
          data: [{
            ts: '2026-02-01T00:00:00Z',
            job_id: 'job-7',
            lane: 'Rosette',
            preset: 'Safe',
            baseline_id: 'base-1',
            baseline_path_count: 1,
            current_path_count: 1,
            added_paths: 0,
            removed_paths: 0,
            unchanged_paths: 1,
          }],
        })
      }
      return Promise.resolve({ data: [AGGREGATE_ROW] })
    })
    vi.spyOn(console, 'error').mockImplementation(() => undefined)
  })

  afterEach(() => {
    localStorage.clear()
    vi.restoreAllMocks()
  })
}

describe('canonical Risk dashboard mount', () => {
  installDashboardHarness()

  it('makes one aggregate request on mount without a saved default', async () => {
    const mounted = await mountDashboard()
    expect(aggregateCalls()).toBe(1)
    mounted.wrapper.unmount()
  })

  it('makes one aggregate request when the URL already has dates', async () => {
    const mounted = await mountDashboard({
      query: { since: '2026-01-01', until: '2026-02-01' },
    })
    expect(aggregateCalls()).toBe(1)
    expect(vi.mocked(axios.get).mock.calls[0]).toEqual([
      AGGREGATE_URL,
      { params: { since: '2026-01-01', until: '2026-02-01' } },
    ])
    mounted.wrapper.unmount()
  })

  it('makes one aggregate request when the default saved view changes the window', async () => {
    const mounted = await mountDashboard({
      views: [viewRecord('Default dated', {
        lane: 'Rosette',
        preset: 'Safe',
        jobHint: '',
        since: '2026-03-01',
        until: '2026-03-31',
      }, true)],
    })
    expect(aggregateCalls()).toBe(1)
    expect(vi.mocked(axios.get).mock.calls[0]).toEqual([
      AGGREGATE_URL,
      { params: { since: '2026-03-01', until: '2026-03-31' } },
    ])
    mounted.wrapper.unmount()
  })
})

describe('canonical Risk dashboard selection filters', () => {
  installDashboardHarness()

  it('closes details without an aggregate request when lane, preset, or job changes', async () => {
    const mounted = await mountDashboard()
    await openDetails(mounted.wrapper)
    expect(mounted.wrapper.text()).toContain('Bucket Details')
    const before = aggregateCalls()

    await mounted.wrapper.findAll('select')[0].setValue('Rosette')
    await flushPromises()
    expect(mounted.wrapper.text()).not.toContain('Bucket Details')
    expect(aggregateCalls()).toBe(before)

    await openDetails(mounted.wrapper)
    await mounted.wrapper.findAll('select')[1].setValue('Safe')
    await flushPromises()
    expect(mounted.wrapper.text()).not.toContain('Bucket Details')
    expect(aggregateCalls()).toBe(before)

    await openDetails(mounted.wrapper)
    await mounted.wrapper.get('input[placeholder="rosette_, neck_pocket..."]').setValue('job-7')
    await flushPromises()
    expect(mounted.wrapper.text()).not.toContain('Bucket Details')
    expect(aggregateCalls()).toBe(before)
    mounted.wrapper.unmount()
  })
})

describe('canonical Risk dashboard date window', () => {
  installDashboardHarness()

  it('closes details and reloads once when since or until changes', async () => {
    const mounted = await mountDashboard()
    await openDetails(mounted.wrapper)
    const dates = mounted.wrapper.findAll('input[type="date"]')
    const before = aggregateCalls()
    await dates[0].setValue('2026-01-15')
    await flushPromises()
    expect(mounted.wrapper.text()).not.toContain('Bucket Details')
    expect(aggregateCalls()).toBe(before + 1)
    const calls = vi.mocked(axios.get).mock.calls
    expect(calls[calls.length - 1]).toEqual([
      AGGREGATE_URL,
      { params: expect.objectContaining({ since: '2026-01-15' }) },
    ])

    await openDetails(mounted.wrapper)
    await dates[1].setValue('2026-02-01')
    await flushPromises()
    expect(aggregateCalls()).toBe(before + 2)
    mounted.wrapper.unmount()
  })

  it('reloads once for a quick range and once for a lane preset', async () => {
    const mounted = await mountDashboard()
    const before = aggregateCalls()
    await clickLabel(mounted.wrapper, 'Last 7d')
    expect(aggregateCalls()).toBe(before + 1)
    await clickLabel(mounted.wrapper, 'Rosette · Safe (30d)')
    expect(aggregateCalls()).toBe(before + 2)
    mounted.wrapper.unmount()
  })

  it('reloads once when clearing an active date window and not when dates are empty', async () => {
    const dated = await mountDashboard()
    await dated.wrapper.findAll('input[type="date"]')[0].setValue('2026-01-15')
    await flushPromises()
    const beforeClear = aggregateCalls()
    await clickLabel(dated.wrapper, 'Clear filters')
    expect(aggregateCalls()).toBe(beforeClear + 1)
    dated.wrapper.unmount()

    const laneOnly = await mountDashboard()
    await openDetails(laneOnly.wrapper)
    await laneOnly.wrapper.findAll('select')[0].setValue('Rosette')
    await flushPromises()
    const before = aggregateCalls()
    await clickLabel(laneOnly.wrapper, 'Clear filters')
    expect(aggregateCalls()).toBe(before)
    expect(laneOnly.wrapper.text()).not.toContain('Bucket Details')
    laneOnly.wrapper.unmount()
  })
})

describe('canonical Risk dashboard saved views', () => {
  installDashboardHarness()

  it('applies a saved view with one request only when the date window changes', async () => {
    const mounted = await mountDashboard({
      views: [
        viewRecord('Lane only', {
          lane: 'Rosette',
          preset: '',
          jobHint: '',
          since: '',
          until: '',
        }),
        viewRecord('Dated', {
          lane: 'Rosette',
          preset: 'Safe',
          jobHint: '',
          since: '2026-04-01',
          until: '2026-04-30',
        }),
      ],
    })
    await openDetails(mounted.wrapper)
    const before = aggregateCalls()
    await clickLabel(mounted.wrapper, 'Lane only')
    expect(aggregateCalls()).toBe(before)
    expect(mounted.wrapper.text()).not.toContain('Bucket Details')
    await clickLabel(mounted.wrapper, 'Dated')
    expect(aggregateCalls()).toBe(before + 1)
    mounted.wrapper.unmount()
  })
})

describe('canonical Risk dashboard refresh and query text', () => {
  installDashboardHarness()

  it('clears details and reloads once from the Refresh button', async () => {
    const mounted = await mountDashboard()
    await openDetails(mounted.wrapper)
    const before = aggregateCalls()
    await clickLabel(mounted.wrapper, 'Refresh')
    expect(mounted.wrapper.text()).not.toContain('Bucket Details')
    expect(aggregateCalls()).toBe(before + 1)
    mounted.wrapper.unmount()
  })

  it('omits a whitespace-only job hint from the URL and does not reload', async () => {
    const mounted = await mountDashboard()
    await openDetails(mounted.wrapper)
    const before = aggregateCalls()
    const job = mounted.wrapper.get('input[placeholder="rosette_, neck_pocket..."]')
    await job.setValue('   ')
    await flushPromises()
    expect(mounted.router.currentRoute.value.query.job_hint).toBeUndefined()
    expect(aggregateCalls()).toBe(before)
    await job.setValue('  job-7  ')
    await flushPromises()
    expect(mounted.router.currentRoute.value.query.job_hint).toBe('job-7')
    expect(aggregateCalls()).toBe(before)
    mounted.wrapper.unmount()
  })
})

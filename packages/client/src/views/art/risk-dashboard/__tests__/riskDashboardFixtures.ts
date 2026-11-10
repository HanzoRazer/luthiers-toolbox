/**
 * Shared fixtures for the February 19 and February 22 risk-dashboard clusters.
 * Specs mock Axios. Nothing in this module issues a network request.
 */
import { expect } from 'vitest'
import { createApp, defineComponent, nextTick, type App } from 'vue'
import { createMemoryHistory, createRouter, type Router } from 'vue-router'

export const FROZEN_ISO = '2026-02-22T06:01:32.000Z'
export const FROZEN_STAMP = '2026-02-22T06-01-32-000Z'

export const WINDOW_SINCE = '2026-01-01'
export const WINDOW_UNTIL = '2026-02-01'
export const JOB_HINT = 'job-7'

/** Client-built aggregate CSV. The lane cell contains a comma, quotes, and a newline. */
export const CLIENT_CSV_BUCKET = {
  key: 'Rosette::Safe',
  lane: 'Rosette, "north"\nbench',
  preset: 'Safe',
  count: 2,
  avgAdded: 1.5,
  avgRemoved: 0,
  avgUnchanged: 3,
  riskScore: 4,
  riskLabel: 'High',
  addedSeries: [] as number[],
  removedSeries: [] as number[],
  addedPath: '',
  removedPath: '',
}

export const CLIENT_CSV_TEXT =
  'lane,preset,count,avg_added,avg_removed,avg_unchanged,risk_score,risk_label\r\n' +
  '"Rosette, ""north""\nbench",Safe,2,1.5,0,3,4,High'

export const SERVER_CSV =
  'lane,preset\r\n"a,b","say ""hi""\nnext"\r\n'

export const REPORT_BODY = {
  bucket: 'Rosette',
  note: 'line1\n"quoted"',
  rows: [1],
}

export const REPORT_TEXT = JSON.stringify(REPORT_BODY, null, 2)

export const DETAIL_ROWS = [
  {
    ts: '2026-02-01T00:00:00Z',
    job_id: 'job-7',
    lane: 'Rosette',
    preset: 'Safe',
    baseline_id: 'base-1',
    baseline_path_count: 4,
    current_path_count: 5,
    added_paths: 1,
    removed_paths: 0,
    unchanged_paths: 4,
  },
]

/**
 * Three aggregate rows:
 * - numeric label fallback and mixed series
 * - string score, single-point sparkline, empty preset
 * - explicit label kept, empty lane
 */
export const AGGREGATE_SUCCESS: Array<Record<string, unknown>> = [
  {
    lane: 'Rosette',
    preset: 'Safe',
    count: 3,
    avg_added: 1.5,
    avg_removed: 0.25,
    avg_unchanged: 8,
    risk_score: 4,
    added_series: ['1', null, 2],
    removed_series: 'not-an-array',
  },
  {
    lane: 'Adaptive',
    preset: '',
    count: 1,
    avg_added: 0,
    avg_removed: 0,
    avg_unchanged: 1,
    risk_score: '0.4',
    risk_label: '',
    added_series: [7],
    removed_series: [],
  },
  {
    lane: '',
    preset: 'Beta',
    count: 2,
    avg_added: 9,
    avg_removed: 1,
    avg_unchanged: 0,
    risk_score: 9,
    risk_label: 'Kept',
    added_series: [],
    removed_series: [],
  },
]

export const EXPECTED_ADDED_PATH = '0.0,10.0 30.0,19.0 60.0,1.0'
export const EXPECTED_SINGLE_POINT_PATH = '0,10 60,10'

export const HTTP_404 = {
  response: { status: 404, data: { detail: 'missing bucket' } },
}

export const HTTP_422 = {
  response: {
    status: 422,
    data: { detail: [{ loc: ['query', 'lane'], msg: 'field required' }] },
  },
}

export const NETWORK_ERROR = new Error('Network Error')

export interface MappedBucket {
  key: string
  lane: string
  preset: string
  count: number
  avgAdded: number
  avgRemoved: number
  avgUnchanged: number
  riskScore: number
  riskLabel: string
  addedSeries: number[]
  removedSeries: number[]
  addedPath: string
  removedPath: string
}

export function assertAggregateMapping(buckets: MappedBucket[]): void {
  expect(buckets).toHaveLength(3)
  expect(buckets[0]).toMatchObject({
    key: 'Rosette::Safe',
    lane: 'Rosette',
    preset: 'Safe',
    count: 3,
    avgAdded: 1.5,
    avgRemoved: 0.25,
    avgUnchanged: 8,
    riskScore: 4,
    riskLabel: 'High',
    addedSeries: [1, 0, 2],
    removedSeries: [],
    addedPath: EXPECTED_ADDED_PATH,
    removedPath: '',
  })
  expect(buckets[1]).toMatchObject({
    key: 'Adaptive::',
    lane: 'Adaptive',
    preset: '',
    riskScore: 0.4,
    riskLabel: 'Low',
    addedSeries: [7],
    addedPath: EXPECTED_SINGLE_POINT_PATH,
    removedPath: '',
  })
  expect(buckets[2]).toMatchObject({
    key: '::Beta',
    lane: '',
    preset: 'Beta',
    riskScore: 9,
    riskLabel: 'Kept',
    addedPath: '',
    removedPath: '',
  })
}

export function plainBucket(overrides: Partial<MappedBucket> = {}): MappedBucket {
  return {
    key: 'Rosette::Safe',
    lane: 'Rosette',
    preset: 'Safe',
    count: 1,
    avgAdded: 0,
    avgRemoved: 0,
    avgUnchanged: 1,
    riskScore: 0.2,
    riskLabel: 'Low',
    addedSeries: [],
    removedSeries: [],
    addedPath: '',
    removedPath: '',
    ...overrides,
  }
}

export function deferred<T>(): {
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

export async function mountWithRouter<T>(setupFn: () => T): Promise<{
  result: T
  router: Router
  app: App
}> {
  let result: T | undefined
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: { template: '<div />' } },
      { path: '/art-studio', component: { template: '<div />' } },
      { path: '/lab/adaptive', component: { template: '<div />' } },
      { path: '/lab/relief', component: { template: '<div />' } },
      { path: '/lab/pipeline', component: { template: '<div />' } },
      { path: '/lab/risk-dashboard', component: { template: '<div />' } },
    ],
  })
  const app = createApp(defineComponent({
    setup() {
      result = setupFn()
      return () => null
    },
  }))
  app.use(router)
  const host = document.createElement('div')
  app.mount(host)
  await router.isReady()
  if (result === undefined) {
    throw new Error('composable setup did not run')
  }
  return { result, router, app }
}

export async function settleNavigation(): Promise<void> {
  await new Promise((resolve) => {
    setTimeout(resolve, 0)
  })
  await nextTick()
}

export async function blobText(blob: Blob): Promise<string> {
  return blob.text()
}

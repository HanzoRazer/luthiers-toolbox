/**
 * Request-order tests for the canonical Risk Dashboard composables.
 * Each test holds Axios responses in unresolved promises and settles them out of order,
 * so an older request finishes after a newer one or after the selection is cleared.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ref, type Ref } from 'vue'
import axios from 'axios'
import { downloadBlob } from '@/utils/downloadBlob'
import { useRiskBucketDetails } from '../useRiskBucketDetails'
import { useRiskBuckets } from '../useRiskBuckets'
import { useRiskExports } from '../useRiskExports'
import {
  AGGREGATE_SUCCESS,
  CLIENT_CSV_BUCKET,
  DETAIL_ROWS,
  FROZEN_ISO,
  FROZEN_STAMP,
  HTTP_404,
  HTTP_422,
  JOB_HINT,
  NETWORK_ERROR,
  REPORT_BODY,
  SERVER_CSV,
  WINDOW_SINCE,
  WINDOW_UNTIL,
  deferred,
  mountWithRouter,
  plainBucket,
  type MappedBucket,
} from './riskDashboardFixtures'

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

type AggregateReply = { data: typeof AGGREGATE_SUCCESS }
type DetailReply = { data: typeof DETAIL_ROWS }

const NEWER_AGGREGATE = [{ ...AGGREGATE_SUCCESS[0], lane: 'Adaptive', preset: 'Newer' }]
const BUCKET_B = { key: 'Adaptive::Fast', lane: 'Adaptive', preset: 'Fast' }

function bindFilters(since = '', until = '') {
  return {
    laneFilter: ref(''),
    presetFilter: ref(''),
    since: ref(since),
    until: ref(until),
    jobFilter: ref(''),
  }
}

function installClockAndMocks(): void {
  beforeEach(() => {
    vi.useFakeTimers({ toFake: ['Date'] })
    vi.setSystemTime(new Date(FROZEN_ISO))
    vi.mocked(axios.get).mockReset()
    vi.mocked(downloadBlob).mockReset()
    vi.spyOn(console, 'error').mockImplementation(() => undefined)
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })
}

/** Queue two pending Axios responses: the first call gets `older`, the second `newer`. */
function queueTwo<T>() {
  const older = deferred<T>()
  const newer = deferred<T>()
  vi.mocked(axios.get).mockReturnValueOnce(older.promise).mockReturnValueOnce(newer.promise)
  return { older, newer }
}

describe('aggregate refresh ordering', () => {
  installClockAndMocks()

  it('keeps the newer aggregate when an older refresh resolves last', async () => {
    const filters = bindFilters(WINDOW_SINCE, WINDOW_UNTIL)
    const mounted = await mountWithRouter(() => useRiskBuckets(filters))
    const { older, newer } = queueTwo<AggregateReply>()

    const first = mounted.result.refresh()
    filters.since.value = '2026-01-15'
    const second = mounted.result.refresh()

    newer.resolve({ data: NEWER_AGGREGATE })
    await second
    expect(mounted.result.bucketsRaw.value.map((b) => b.key)).toEqual(['Adaptive::Newer'])

    older.resolve({ data: AGGREGATE_SUCCESS })
    await first
    expect(mounted.result.bucketsRaw.value.map((b) => b.key)).toEqual(['Adaptive::Newer'])
    mounted.app.unmount()
  })

  it('does not clear the newer aggregate when an older refresh fails last', async () => {
    const mounted = await mountWithRouter(() => useRiskBuckets(bindFilters()))
    const { older, newer } = queueTwo<AggregateReply>()

    const first = mounted.result.refresh()
    const second = mounted.result.refresh()
    newer.resolve({ data: NEWER_AGGREGATE })
    await second
    older.reject(NETWORK_ERROR)
    await first

    expect(mounted.result.bucketsRaw.value.map((b) => b.key)).toEqual(['Adaptive::Newer'])
    expect(console.error).not.toHaveBeenCalled()
    mounted.app.unmount()
  })

  it('keeps a newer failure when an older refresh resolves after it', async () => {
    const mounted = await mountWithRouter(() => useRiskBuckets(bindFilters()))
    const { older, newer } = queueTwo<AggregateReply>()

    const first = mounted.result.refresh()
    const second = mounted.result.refresh()
    newer.reject(HTTP_422)
    await second
    older.resolve({ data: AGGREGATE_SUCCESS })
    await first

    expect(mounted.result.bucketsRaw.value).toEqual([])
    expect(console.error).toHaveBeenCalledTimes(1)
    mounted.app.unmount()
  })
})

describe('bucket detail ordering', () => {
  installClockAndMocks()

  async function mountDetails() {
    return mountWithRouter(() => useRiskBucketDetails({ jobFilter: ref('') }))
  }

  it('keeps details empty when a detail request resolves after clearBucketDetails()', async () => {
    const mounted = await mountDetails()
    const gate = deferred<DetailReply>()
    vi.mocked(axios.get).mockReturnValueOnce(gate.promise)

    const pending = mounted.result.loadBucketDetails(plainBucket())
    mounted.result.clearBucketDetails()
    gate.resolve({ data: DETAIL_ROWS })
    await pending

    expect(mounted.result.selectedBucket.value).toBeNull()
    expect(mounted.result.bucketEntries.value).toEqual([])
    expect(mounted.result.bucketEntriesError.value).toBeNull()
    expect(mounted.result.bucketEntriesLoading.value).toBe(false)
    mounted.app.unmount()
  })

  it('ignores a detail failure that arrives after clearBucketDetails()', async () => {
    const mounted = await mountDetails()
    const gate = deferred<DetailReply>()
    vi.mocked(axios.get).mockReturnValueOnce(gate.promise)

    const pending = mounted.result.loadBucketDetails(plainBucket())
    mounted.result.clearBucketDetails()
    gate.reject(HTTP_404)
    await pending

    expect(mounted.result.selectedBucket.value).toBeNull()
    expect(mounted.result.bucketEntriesError.value).toBeNull()
    expect(mounted.result.bucketEntriesLoading.value).toBe(false)
    expect(console.error).not.toHaveBeenCalled()
    mounted.app.unmount()
  })

  it('keeps bucket B displayed when bucket A resolves last', async () => {
    const mounted = await mountDetails()
    const bucketB = plainBucket(BUCKET_B)
    const rowsB = DETAIL_ROWS.map((row) => ({ ...row, lane: 'Adaptive', preset: 'Fast' }))
    const { older: gateA, newer: gateB } = queueTwo<DetailReply>()

    const pendingA = mounted.result.loadBucketDetails(plainBucket())
    const pendingB = mounted.result.loadBucketDetails(bucketB)
    gateB.resolve({ data: rowsB })
    await pendingB
    gateA.resolve({ data: DETAIL_ROWS })
    await pendingA

    expect(mounted.result.selectedBucket.value).toEqual(bucketB)
    expect(mounted.result.bucketEntries.value).toEqual(rowsB)
    expect(mounted.result.bucketEntriesLoading.value).toBe(false)
    mounted.app.unmount()
  })

  it('does not let an obsolete detail failure set an error or end the newer loading state', async () => {
    const mounted = await mountDetails()
    const bucketB = plainBucket(BUCKET_B)
    const { older: gateA, newer: gateB } = queueTwo<DetailReply>()

    const pendingA = mounted.result.loadBucketDetails(plainBucket())
    const pendingB = mounted.result.loadBucketDetails(bucketB)
    gateA.reject(NETWORK_ERROR)
    await pendingA

    expect(mounted.result.selectedBucket.value).toEqual(bucketB)
    expect(mounted.result.bucketEntriesError.value).toBeNull()
    expect(mounted.result.bucketEntriesLoading.value).toBe(true)

    gateB.resolve({ data: DETAIL_ROWS })
    await pendingB
    expect(mounted.result.bucketEntries.value).toEqual(DETAIL_ROWS)
    expect(mounted.result.bucketEntriesLoading.value).toBe(false)
    mounted.app.unmount()
  })
})

describe('bucket exports across a selection change', () => {
  installClockAndMocks()

  function exportsFor(
    selectedBucket: Ref<MappedBucket | null>,
    filters: ReturnType<typeof bindFilters>,
    errors: string[] = [],
  ) {
    return useRiskExports({
      filteredBuckets: ref([CLIENT_CSV_BUCKET]),
      selectedBucket,
      bucketEntries: ref([]),
      jobFilter: filters.jobFilter,
      since: filters.since,
      until: filters.until,
      setError: (message) => {
        errors.push(message)
      },
    })
  }

  it('names the bucket CSV from the requested bucket after the selection clears', async () => {
    const selectedBucket = ref<MappedBucket | null>(plainBucket())
    const exportsApi = exportsFor(selectedBucket, bindFilters())
    const gate = deferred<{ data: Blob }>()
    vi.mocked(axios.get).mockReturnValueOnce(gate.promise)

    const pending = exportsApi.exportBucketCsv()
    selectedBucket.value = null
    gate.resolve({ data: new Blob([SERVER_CSV]) })
    await pending

    expect(console.error).not.toHaveBeenCalled()
    expect(vi.mocked(downloadBlob)).toHaveBeenCalledTimes(1)
    expect(vi.mocked(downloadBlob).mock.calls[0][1]).toBe('risk_bucket_Rosette_Safe.csv')
  })

  it('names the bucket report from the hint and window the request used', async () => {
    const filters = bindFilters(WINDOW_SINCE, WINDOW_UNTIL)
    filters.jobFilter.value = JOB_HINT
    const exportsApi = exportsFor(ref<MappedBucket | null>(plainBucket()), filters)
    const gate = deferred<{ data: typeof REPORT_BODY }>()
    vi.mocked(axios.get).mockReturnValueOnce(gate.promise)

    const pending = exportsApi.downloadBucketJson()
    filters.jobFilter.value = 'job-other'
    filters.since.value = ''
    gate.resolve({ data: REPORT_BODY })
    await pending

    expect(vi.mocked(axios.get).mock.calls[0][1]).toEqual({
      params: { lane: 'Rosette', preset: 'Safe', job_hint: JOB_HINT },
      responseType: 'json',
    })
    expect(vi.mocked(downloadBlob).mock.calls[0][1]).toBe(
      `bucket_report_Rosette_Safe_hint-${JOB_HINT}_from-${WINDOW_SINCE}_to-${WINDOW_UNTIL}_${FROZEN_STAMP}.json`,
    )
  })

  it('does not attach an obsolete report failure to a replaced selection', async () => {
    const selectedBucket = ref<MappedBucket | null>(plainBucket())
    const errors: string[] = []
    const exportsApi = exportsFor(selectedBucket, bindFilters(), errors)
    const gate = deferred<{ data: typeof REPORT_BODY }>()
    vi.mocked(axios.get).mockReturnValueOnce(gate.promise)

    const pending = exportsApi.downloadBucketJson()
    selectedBucket.value = plainBucket(BUCKET_B)
    gate.reject(HTTP_422)
    await pending

    expect(errors).toEqual([])
    expect(console.error).toHaveBeenCalledWith(
      'Failed to download bucket JSON report',
      expect.anything(),
    )
  })
})

/**
 * Characterization of the February 22 risk cluster.
 * These tests pin what the current modules do. They do not declare it canonical.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick, ref } from 'vue'
import axios from 'axios'
import { downloadBlob } from '@/utils/downloadBlob'
import { useRiskBucketDetails } from '../useRiskBucketDetails'
import { useRiskBuckets } from '../useRiskBuckets'
import { useRiskExports } from '../useRiskExports'
import { useRiskFilters } from '../useRiskFilters'
import { useRiskNavigation } from '../useRiskNavigation'
import {
  AGGREGATE_SUCCESS,
  CLIENT_CSV_BUCKET,
  CLIENT_CSV_TEXT,
  DETAIL_ROWS,
  FROZEN_ISO,
  FROZEN_STAMP,
  HTTP_404,
  HTTP_422,
  JOB_HINT,
  NETWORK_ERROR,
  REPORT_BODY,
  REPORT_TEXT,
  SERVER_CSV,
  WINDOW_SINCE,
  WINDOW_UNTIL,
  assertAggregateMapping,
  blobText,
  deferred,
  mountWithRouter,
  plainBucket,
  settleNavigation,
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

const callsAfterImport = vi.mocked(axios.get).mock.calls.length

function bindFilters(lane = '', preset = '', since = '', until = '') {
  return {
    laneFilter: ref(lane),
    presetFilter: ref(preset),
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

describe('February 22 import and aggregate', () => {
  installClockAndMocks()

  it('does not request during module import', () => {
    expect(callsAfterImport).toBe(0)
  })

  it('returns the split buckets, details, exports, and navigation interface', async () => {
    const filters = bindFilters()
    const mounted = await mountWithRouter(() => {
      const buckets = useRiskBuckets(filters)
      const details = useRiskBucketDetails({ jobFilter: filters.jobFilter })
      const navigation = useRiskNavigation({ jobFilter: filters.jobFilter })
      const setError = vi.fn()
      const exportsApi = useRiskExports({
        filteredBuckets: buckets.filteredBuckets,
        selectedBucket: details.selectedBucket,
        bucketEntries: details.bucketEntries,
        jobFilter: filters.jobFilter,
        since: filters.since,
        until: filters.until,
        setError,
      })
      return { buckets, details, navigation, exportsApi }
    })
    expect(Object.keys(mounted.result.buckets).sort()).toEqual([
      'allLanes',
      'allPresets',
      'bucketsRaw',
      'filteredBuckets',
      'filteredEntriesCount',
      'refresh',
    ])
    expect(Object.keys(mounted.result.details).sort()).toEqual([
      'bucketEntries',
      'bucketEntriesError',
      'bucketEntriesLoading',
      'clearBucketDetails',
      'loadBucketDetails',
      'selectedBucket',
    ])
    expect(Object.keys(mounted.result.exportsApi).sort()).toEqual([
      'downloadBucketJson',
      'downloadSnapshotJson',
      'exportBucketCsv',
      'exportBucketJson',
      'exportCsv',
    ])
    expect(Object.keys(mounted.result.navigation)).toEqual(['goToLab'])
    expect(typeof mounted.result.buckets.filteredBuckets).not.toBe('function')
    mounted.app.unmount()
  })

  it('GET /api/compare/risk_aggregate once per refresh, reading since and until from refs', async () => {
    const filters = bindFilters('', '', WINDOW_SINCE, WINDOW_UNTIL)
    const mounted = await mountWithRouter(() => useRiskBuckets(filters))
    vi.mocked(axios.get).mockResolvedValue({ data: AGGREGATE_SUCCESS })
    await mounted.result.refresh()
    expect(vi.mocked(axios.get)).toHaveBeenCalledTimes(1)
    expect(vi.mocked(axios.get).mock.calls[0]).toEqual([
      '/api/compare/risk_aggregate',
      { params: { since: WINDOW_SINCE, until: WINDOW_UNTIL } },
    ])
    filters.since.value = ''
    filters.until.value = ''
    vi.mocked(axios.get).mockClear()
    await mounted.result.refresh()
    expect(vi.mocked(axios.get).mock.calls[0]).toEqual([
      '/api/compare/risk_aggregate',
      { params: {} },
    ])
    mounted.app.unmount()
  })

})

describe('February 22 aggregate mapping', () => {
  installClockAndMocks()

  it('maps a successful bucket list with the same predicate as the earlier cluster', async () => {
    const filters = bindFilters()
    const mounted = await mountWithRouter(() => useRiskBuckets(filters))
    vi.mocked(axios.get).mockResolvedValue({ data: AGGREGATE_SUCCESS })
    await mounted.result.refresh()
    assertAggregateMapping(mounted.result.bucketsRaw.value as MappedBucket[])
    expect(mounted.result.allLanes.value).toEqual(['Adaptive', 'Rosette'])
    expect(mounted.result.allPresets.value).toEqual(['(none)', 'Beta', 'Safe'])
    expect(mounted.result.filteredBuckets.value.map((bucket) => bucket.key)).toEqual([
      'Rosette::Safe',
      'Adaptive::',
      '::Beta',
    ])
    filters.laneFilter.value = 'Rosette'
    await nextTick()
    expect(mounted.result.filteredBuckets.value.map((bucket) => bucket.key)).toEqual([
      'Rosette::Safe',
    ])
    filters.laneFilter.value = ''
    filters.presetFilter.value = '(none)'
    await nextTick()
    expect(mounted.result.filteredBuckets.value).toEqual([])
    filters.presetFilter.value = 'Safe'
    await nextTick()
    expect(mounted.result.filteredEntriesCount.value).toBe(3)
    mounted.app.unmount()
  })

  it('clears buckets on an empty payload and on 404, 422, and network failure', async () => {
    const mounted = await mountWithRouter(() => useRiskBuckets(bindFilters()))
    vi.mocked(axios.get).mockResolvedValue({ data: [] })
    await mounted.result.refresh()
    expect(mounted.result.bucketsRaw.value).toEqual([])

    vi.mocked(axios.get).mockResolvedValue({ data: AGGREGATE_SUCCESS })
    await mounted.result.refresh()
    for (const failure of [HTTP_404, HTTP_422, NETWORK_ERROR]) {
      vi.mocked(axios.get).mockReset()
      vi.mocked(axios.get).mockRejectedValue(failure)
      await expect(mounted.result.refresh()).resolves.toBeUndefined()
      expect(mounted.result.bucketsRaw.value).toEqual([])
      expect(vi.mocked(axios.get)).toHaveBeenCalledTimes(1)
    }
    vi.mocked(axios.get).mockResolvedValue({ data: null })
    await mounted.result.refresh()
    expect(mounted.result.bucketsRaw.value).toEqual([])
    expect(console.error).toHaveBeenCalledWith(
      'Failed to load risk aggregates',
      expect.anything(),
    )
    mounted.app.unmount()
  })

})

describe('February 22 bucket details', () => {
  installClockAndMocks()

  it('loads one selected bucket and keeps that selection when the detail request fails', async () => {
    const jobFilter = ref(JOB_HINT)
    const mounted = await mountWithRouter(() => useRiskBucketDetails({ jobFilter }))
    const bucket = plainBucket()
    const gate = deferred<{ data: typeof DETAIL_ROWS }>()
    vi.mocked(axios.get).mockReturnValueOnce(gate.promise)
    const pending = mounted.result.loadBucketDetails(bucket)
    expect(mounted.result.selectedBucket.value).toEqual(bucket)
    expect(mounted.result.bucketEntriesLoading.value).toBe(true)
    expect(mounted.result.bucketEntries.value).toEqual([])
    gate.resolve({ data: DETAIL_ROWS })
    await pending
    expect(vi.mocked(axios.get).mock.calls[0]).toEqual([
      '/api/compare/risk_bucket_detail',
      { params: { lane: 'Rosette', preset: 'Safe', job_hint: JOB_HINT } },
    ])
    expect(mounted.result.bucketEntries.value).toEqual(DETAIL_ROWS)

    jobFilter.value = ''
    vi.mocked(axios.get).mockClear()
    await mounted.result.loadBucketDetails(bucket)
    expect(vi.mocked(axios.get).mock.calls[0]).toEqual([
      '/api/compare/risk_bucket_detail',
      { params: { lane: 'Rosette', preset: 'Safe' } },
    ])

    for (const failure of [HTTP_404, HTTP_422, NETWORK_ERROR]) {
      vi.mocked(axios.get).mockReset()
      vi.mocked(axios.get).mockRejectedValue(failure)
      await mounted.result.loadBucketDetails(bucket)
      expect(mounted.result.selectedBucket.value).toEqual(bucket)
      expect(mounted.result.bucketEntries.value).toEqual([])
      expect(mounted.result.bucketEntriesError.value).toBe('Failed to load bucket entries.')
      expect(mounted.result.bucketEntriesLoading.value).toBe(false)
    }
    mounted.app.unmount()
  })

})

describe('February 22 exports', () => {
  installClockAndMocks()

  it('writes the same CSV and JSON bytes and filenames as the earlier cluster', async () => {
    const filters = bindFilters()
    filters.since.value = WINDOW_SINCE
    filters.until.value = WINDOW_UNTIL
    filters.jobFilter.value = JOB_HINT
    const selected = ref<MappedBucket | null>(plainBucket())
    const entries = ref(DETAIL_ROWS)
    const filtered = ref([CLIENT_CSV_BUCKET])
    const errors: string[] = []
    const exportsApi = useRiskExports({
      filteredBuckets: filtered,
      selectedBucket: selected,
      bucketEntries: entries,
      jobFilter: filters.jobFilter,
      since: filters.since,
      until: filters.until,
      setError: (message) => {
        errors.push(message)
      },
    })

    filtered.value = []
    exportsApi.exportCsv()
    expect(downloadBlob).not.toHaveBeenCalled()
    filtered.value = [CLIENT_CSV_BUCKET]
    exportsApi.exportCsv()
    const [csvBlob, csvName] = vi.mocked(downloadBlob).mock.calls[0]
    expect(csvBlob.type).toBe('text/csv;charset=utf-8;')
    expect(await blobText(csvBlob)).toBe(CLIENT_CSV_TEXT)
    expect(csvName).toBe(
      `crosslab_risk_aggregate_from-${WINDOW_SINCE}_to-${WINDOW_UNTIL}_${FROZEN_STAMP}.csv`,
    )

    selected.value = null
    await exportsApi.exportBucketCsv()
    await exportsApi.exportBucketJson()
    await exportsApi.downloadBucketJson()
    expect(axios.get).not.toHaveBeenCalled()
    expect(errors).toEqual([])

    selected.value = plainBucket()
    vi.mocked(axios.get).mockResolvedValue({ data: new Blob([SERVER_CSV]) })
    await exportsApi.exportBucketCsv()
    expect(vi.mocked(axios.get).mock.calls[0]).toEqual([
      '/api/compare/risk_bucket_export',
      {
        params: { lane: 'Rosette', preset: 'Safe', format: 'csv' },
        responseType: 'blob',
      },
    ])
    expect(await blobText(vi.mocked(downloadBlob).mock.calls[1][0])).toBe(SERVER_CSV)
    expect(vi.mocked(downloadBlob).mock.calls[1][1]).toBe('risk_bucket_Rosette_Safe.csv')

    vi.mocked(axios.get).mockClear()
    await exportsApi.exportBucketJson()
    expect(vi.mocked(axios.get).mock.calls[0][1]).toEqual({
      params: { lane: 'Rosette', preset: 'Safe', format: 'json' },
      responseType: 'blob',
    })

    vi.mocked(axios.get).mockResolvedValue({ data: REPORT_BODY })
    await exportsApi.downloadBucketJson()
    const reportCalls = vi.mocked(downloadBlob).mock.calls
    const reportCall = reportCalls[reportCalls.length - 1]
    expect(await blobText(reportCall[0])).toBe(REPORT_TEXT)
    expect(reportCall[1]).toBe(
      `bucket_report_Rosette_Safe_hint-${JOB_HINT}_from-${WINDOW_SINCE}_to-${WINDOW_UNTIL}_${FROZEN_STAMP}.json`,
    )

    vi.mocked(axios.get).mockClear()
    vi.mocked(downloadBlob).mockClear()
    await exportsApi.downloadSnapshotJson()
    expect(vi.mocked(axios.get).mock.calls[0]).toEqual([
      '/api/compare/risk_snapshot',
      {
        params: { since: WINDOW_SINCE, until: WINDOW_UNTIL },
        responseType: 'json',
      },
    ])
    expect(vi.mocked(downloadBlob).mock.calls[0][1]).toBe(
      `risk_snapshot_from-${WINDOW_SINCE}_to-${WINDOW_UNTIL}_${FROZEN_STAMP}.json`,
    )
  })

})

describe('February 22 export errors', () => {
  installClockAndMocks()

  it('assigns the bucket-report error through setError after 404, 422, and network failure', async () => {
    const filters = bindFilters()
    const errors: string[] = []
    const exportsApi = useRiskExports({
      filteredBuckets: ref([CLIENT_CSV_BUCKET]),
      selectedBucket: ref(plainBucket()),
      bucketEntries: ref([]),
      jobFilter: filters.jobFilter,
      since: filters.since,
      until: filters.until,
      setError: (message) => {
        errors.push(message)
      },
    })
    for (const failure of [HTTP_404, HTTP_422, NETWORK_ERROR]) {
      vi.mocked(axios.get).mockReset()
      vi.mocked(axios.get).mockRejectedValue(failure)
      await exportsApi.downloadBucketJson()
    }
    expect(errors).toEqual([
      'Failed to download bucket JSON report.',
      'Failed to download bucket JSON report.',
      'Failed to download bucket JSON report.',
    ])
    expect(console.error).toHaveBeenCalledWith(
      'Failed to download bucket JSON report',
      expect.anything(),
    )
    vi.mocked(axios.get).mockRejectedValue(HTTP_422)
    await exportsApi.exportBucketCsv()
    await exportsApi.downloadSnapshotJson()
    expect(console.error).toHaveBeenCalledWith('Failed to export bucket CSV', expect.anything())
    expect(console.error).toHaveBeenCalledWith(
      'Failed to download global risk snapshot',
      expect.anything(),
    )
    expect(errors).toHaveLength(3)
  })

})

describe('February 22 navigation and filters', () => {
  installClockAndMocks()

  it('navigates by lane prefix from useRiskNavigation', async () => {
    const jobFilter = ref(JOB_HINT)
    const mounted = await mountWithRouter(() => useRiskNavigation({ jobFilter }))
    const cases: Array<[string, string, string]> = [
      ['Rosette', '/art-studio', 'compare'],
      ['Adaptive', '/lab/adaptive', ''],
      ['Relief', '/lab/relief', ''],
      ['Pipeline', '/lab/pipeline', ''],
      ['Other', '/lab/risk-dashboard', ''],
    ]
    for (const [lane, path, tab] of cases) {
      mounted.result.goToLab(plainBucket({ lane, preset: 'Safe' }))
      await settleNavigation()
      expect(mounted.router.currentRoute.value.path).toBe(path)
      expect(mounted.router.currentRoute.value.query.lane).toBe(lane.toLowerCase())
      expect(mounted.router.currentRoute.value.query.preset).toBe('Safe')
      expect(mounted.router.currentRoute.value.query.job_hint).toBe(JOB_HINT)
      if (tab) {
        expect(mounted.router.currentRoute.value.query.tab).toBe(tab)
      }
    }
    jobFilter.value = ''
    mounted.result.goToLab(plainBucket({ preset: '(none)' }))
    await settleNavigation()
    expect(mounted.router.currentRoute.value.query.preset).toBeUndefined()
    expect(mounted.router.currentRoute.value.query.job_hint).toBeUndefined()
    expect(axios.get).not.toHaveBeenCalled()
    mounted.app.unmount()
  })

  it('writes untrimmed query values and does not clear or refresh on filter edits', async () => {
    const mounted = await mountWithRouter(() => {
      const filters = useRiskFilters()
      const details = useRiskBucketDetails({ jobFilter: filters.jobFilter })
      const buckets = useRiskBuckets({
        laneFilter: filters.laneFilter,
        presetFilter: filters.presetFilter,
        since: filters.since,
        until: filters.until,
      })
      return { filters, details, buckets }
    })
    vi.mocked(axios.get).mockResolvedValue({ data: DETAIL_ROWS })
    await mounted.result.details.loadBucketDetails(plainBucket())
    const callsAfterDetails = vi.mocked(axios.get).mock.calls.length

    mounted.result.filters.laneFilter.value = '  Rosette  '
    mounted.result.filters.presetFilter.value = '   '
    mounted.result.filters.jobFilter.value = ' job-7 '
    await settleNavigation()
    expect(mounted.router.currentRoute.value.query).toEqual({
      lane: '  Rosette  ',
      preset: '   ',
      job_hint: ' job-7 ',
    })
    expect(mounted.result.details.selectedBucket.value).toEqual(plainBucket())
    expect(vi.mocked(axios.get).mock.calls.length).toBe(callsAfterDetails)

    mounted.result.filters.since.value = ` ${WINDOW_SINCE} `
    mounted.result.filters.until.value = ''
    await settleNavigation()
    expect(mounted.router.currentRoute.value.query.since).toBe(` ${WINDOW_SINCE} `)
    expect(mounted.result.details.selectedBucket.value).not.toBeNull()
    expect(vi.mocked(axios.get).mock.calls.map((call) => call[0])).not.toContain(
      '/api/compare/risk_aggregate',
    )
    mounted.app.unmount()
  })
})

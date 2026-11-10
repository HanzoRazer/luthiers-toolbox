/**
 * Characterization of the February 19 risk cluster.
 * These tests pin what the current modules do. They do not declare it canonical.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import axios from 'axios'
import { downloadBlob } from '@/utils/downloadBlob'
import { useRiskBuckets } from '../useRiskBuckets'
import { useRiskExport } from '../useRiskExport'
import { useRiskFilters } from '../useRiskFilters'
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
} from '../../risk-dashboard/__tests__/riskDashboardFixtures'

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

async function setupBuckets() {
  return mountWithRouter(() => useRiskBuckets())
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

describe('February 19 import and aggregate', () => {
  installClockAndMocks()

  it('does not request during module import', () => {
    expect(callsAfterImport).toBe(0)
  })

  it('returns the February 19 buckets and export interface', async () => {
    const mounted = await setupBuckets()
    const buckets = mounted.result
    const exportsApi = useRiskExport()
    expect(Object.keys(buckets).sort()).toEqual([
      'allLanes',
      'allPresets',
      'bucketEntries',
      'bucketEntriesError',
      'bucketEntriesLoading',
      'bucketsRaw',
      'clearBucketDetails',
      'filteredBuckets',
      'filteredEntriesCount',
      'goToLab',
      'loadBucketDetails',
      'refresh',
      'selectedBucket',
    ])
    expect(Object.keys(exportsApi).sort()).toEqual([
      'downloadBucketJson',
      'downloadSnapshotJson',
      'exportBucketCsv',
      'exportBucketJson',
      'exportCsv',
    ])
    expect(typeof buckets.filteredBuckets).toBe('function')
    mounted.app.unmount()
  })

  it('GET /api/compare/risk_aggregate once per refresh, with since and until only when set', async () => {
    const mounted = await setupBuckets()
    vi.mocked(axios.get).mockResolvedValue({ data: AGGREGATE_SUCCESS })
    await mounted.result.refresh(WINDOW_SINCE, WINDOW_UNTIL)
    expect(vi.mocked(axios.get)).toHaveBeenCalledTimes(1)
    expect(vi.mocked(axios.get).mock.calls[0]).toEqual([
      '/api/compare/risk_aggregate',
      { params: { since: WINDOW_SINCE, until: WINDOW_UNTIL } },
    ])
    vi.mocked(axios.get).mockClear()
    await mounted.result.refresh('', '')
    expect(vi.mocked(axios.get).mock.calls[0]).toEqual([
      '/api/compare/risk_aggregate',
      { params: {} },
    ])
    mounted.app.unmount()
  })

  it('maps a successful bucket list and filters with the same predicate as the later cluster', async () => {
    const mounted = await setupBuckets()
    vi.mocked(axios.get).mockResolvedValue({ data: AGGREGATE_SUCCESS })
    await mounted.result.refresh('', '')
    const buckets = mounted.result.bucketsRaw.value as MappedBucket[]
    assertAggregateMapping(buckets)
    expect(mounted.result.allLanes.value).toEqual(['Adaptive', 'Rosette'])
    expect(mounted.result.allPresets.value).toEqual(['(none)', 'Beta', 'Safe'])
    expect(mounted.result.filteredBuckets('Rosette', '').map((bucket) => bucket.key)).toEqual([
      'Rosette::Safe',
    ])
    expect(mounted.result.filteredBuckets('', '(none)')).toEqual([])
    expect(mounted.result.filteredEntriesCount('Rosette', 'Safe')).toBe(3)
    expect(mounted.result.filteredEntriesCount('', '')).toBe(6)
    mounted.app.unmount()
  })

  it('clears buckets on an empty payload and on 404, 422, and network failure', async () => {
    const mounted = await setupBuckets()
    vi.mocked(axios.get).mockResolvedValue({ data: AGGREGATE_SUCCESS })
    await mounted.result.refresh('', '')
    vi.mocked(axios.get).mockResolvedValue({ data: [] })
    await mounted.result.refresh('', '')
    expect(mounted.result.bucketsRaw.value).toEqual([])

    vi.mocked(axios.get).mockResolvedValue({ data: AGGREGATE_SUCCESS })
    await mounted.result.refresh('', '')
    for (const failure of [HTTP_404, HTTP_422, NETWORK_ERROR, { data: null }]) {
      vi.mocked(axios.get).mockReset()
      if (failure && typeof failure === 'object' && 'data' in failure && !('response' in failure)) {
        vi.mocked(axios.get).mockResolvedValue(failure)
      } else {
        vi.mocked(axios.get).mockRejectedValue(failure)
      }
      await expect(mounted.result.refresh('', '')).resolves.toBeUndefined()
      expect(mounted.result.bucketsRaw.value).toEqual([])
      expect(vi.mocked(axios.get)).toHaveBeenCalledTimes(1)
    }
    expect(console.error).toHaveBeenCalledWith(
      'Failed to load risk aggregates',
      expect.anything(),
    )
    mounted.app.unmount()
  })

})

describe('February 19 bucket details', () => {
  installClockAndMocks()

  it('loads one selected bucket and keeps that selection when the detail request fails', async () => {
    const mounted = await setupBuckets()
    const bucket = plainBucket()
    const gate = deferred<{ data: typeof DETAIL_ROWS }>()
    vi.mocked(axios.get).mockReturnValueOnce(gate.promise)
    const pending = mounted.result.loadBucketDetails(bucket, JOB_HINT)
    expect(mounted.result.selectedBucket.value).toEqual(bucket)
    expect(mounted.result.bucketEntriesLoading.value).toBe(true)
    expect(mounted.result.bucketEntries.value).toEqual([])
    expect(mounted.result.bucketEntriesError.value).toBeNull()
    gate.resolve({ data: DETAIL_ROWS })
    await pending
    expect(vi.mocked(axios.get).mock.calls[0]).toEqual([
      '/api/compare/risk_bucket_detail',
      { params: { lane: 'Rosette', preset: 'Safe', job_hint: JOB_HINT } },
    ])
    expect(mounted.result.bucketEntries.value).toEqual(DETAIL_ROWS)
    expect(mounted.result.bucketEntriesLoading.value).toBe(false)

    vi.mocked(axios.get).mockClear()
    await mounted.result.loadBucketDetails(bucket, '')
    expect(vi.mocked(axios.get).mock.calls[0]).toEqual([
      '/api/compare/risk_bucket_detail',
      { params: { lane: 'Rosette', preset: 'Safe' } },
    ])

    for (const failure of [HTTP_404, HTTP_422, NETWORK_ERROR]) {
      vi.mocked(axios.get).mockReset()
      vi.mocked(axios.get).mockRejectedValue(failure)
      await mounted.result.loadBucketDetails(bucket, '')
      expect(mounted.result.selectedBucket.value).toEqual(bucket)
      expect(mounted.result.bucketEntries.value).toEqual([])
      expect(mounted.result.bucketEntriesError.value).toBe('Failed to load bucket entries.')
      expect(mounted.result.bucketEntriesLoading.value).toBe(false)
    }
    expect(console.error).toHaveBeenCalledWith(
      'Failed to load bucket entries',
      expect.anything(),
    )
    mounted.app.unmount()
  })

  it('clears the selected bucket without a request', async () => {
    const mounted = await setupBuckets()
    vi.mocked(axios.get).mockResolvedValue({ data: DETAIL_ROWS })
    await mounted.result.loadBucketDetails(plainBucket(), '')
    const calls = vi.mocked(axios.get).mock.calls.length
    mounted.result.clearBucketDetails()
    expect(mounted.result.selectedBucket.value).toBeNull()
    expect(mounted.result.bucketEntries.value).toEqual([])
    expect(mounted.result.bucketEntriesError.value).toBeNull()
    expect(mounted.result.bucketEntriesLoading.value).toBe(false)
    expect(vi.mocked(axios.get).mock.calls.length).toBe(calls)
    mounted.app.unmount()
  })

})

describe('February 19 exports', () => {
  installClockAndMocks()

  it('writes the client CSV with escaped commas, quotes, and newlines', async () => {
    const exportsApi = useRiskExport()
    exportsApi.exportCsv([], WINDOW_SINCE, WINDOW_UNTIL)
    expect(downloadBlob).not.toHaveBeenCalled()

    exportsApi.exportCsv([CLIENT_CSV_BUCKET], WINDOW_SINCE, WINDOW_UNTIL)
    expect(downloadBlob).toHaveBeenCalledTimes(1)
    const [blob, filename] = vi.mocked(downloadBlob).mock.calls[0]
    expect(blob.type).toBe('text/csv;charset=utf-8;')
    expect(await blobText(blob)).toBe(CLIENT_CSV_TEXT)
    expect(filename).toBe(
      `crosslab_risk_aggregate_from-${WINDOW_SINCE}_to-${WINDOW_UNTIL}_${FROZEN_STAMP}.csv`,
    )

    vi.mocked(downloadBlob).mockClear()
    exportsApi.exportCsv([CLIENT_CSV_BUCKET], '', '')
    expect(vi.mocked(downloadBlob).mock.calls[0][1]).toBe(
      `crosslab_risk_aggregate_${FROZEN_STAMP}.csv`,
    )
  })

  it('downloads the server CSV blob and the JSON report without re-encoding', async () => {
    const exportsApi = useRiskExport()
    const bucket = plainBucket()
    await exportsApi.exportBucketCsv(null)
    await exportsApi.exportBucketJson(null)
    await exportsApi.downloadBucketJson(null, [], '', '', '')
    expect(axios.get).not.toHaveBeenCalled()

    vi.mocked(axios.get).mockResolvedValue({ data: new Blob([SERVER_CSV]) })
    await exportsApi.exportBucketCsv(bucket)
    expect(vi.mocked(axios.get).mock.calls[0]).toEqual([
      '/api/compare/risk_bucket_export',
      {
        params: { lane: 'Rosette', preset: 'Safe', format: 'csv' },
        responseType: 'blob',
      },
    ])
    const [csvBlob, csvName] = vi.mocked(downloadBlob).mock.calls[0]
    expect(await blobText(csvBlob)).toBe(SERVER_CSV)
    expect(csvName).toBe('risk_bucket_Rosette_Safe.csv')

    vi.mocked(axios.get).mockClear()
    vi.mocked(downloadBlob).mockClear()
    await exportsApi.exportBucketJson(bucket)
    expect(vi.mocked(axios.get).mock.calls[0][1]).toEqual({
      params: { lane: 'Rosette', preset: 'Safe', format: 'json' },
      responseType: 'blob',
    })
    expect(vi.mocked(downloadBlob).mock.calls[0][1]).toBe('risk_bucket_Rosette_Safe.json')

    vi.mocked(axios.get).mockClear()
    vi.mocked(downloadBlob).mockClear()
    vi.mocked(axios.get).mockResolvedValue({ data: REPORT_BODY })
    await exportsApi.downloadBucketJson(
      bucket,
      DETAIL_ROWS,
      JOB_HINT,
      WINDOW_SINCE,
      WINDOW_UNTIL,
    )
    expect(vi.mocked(axios.get)).toHaveBeenCalledTimes(1)
    expect(vi.mocked(axios.get).mock.calls[0]).toEqual([
      '/api/compare/risk_bucket_report',
      {
        params: { lane: 'Rosette', preset: 'Safe', job_hint: JOB_HINT },
        responseType: 'json',
      },
    ])
    const [reportBlob, reportName] = vi.mocked(downloadBlob).mock.calls[0]
    expect(reportBlob.type).toBe('application/json')
    expect(await blobText(reportBlob)).toBe(REPORT_TEXT)
    expect(reportName).toBe(
      `bucket_report_Rosette_Safe_hint-${JOB_HINT}_from-${WINDOW_SINCE}_to-${WINDOW_UNTIL}_${FROZEN_STAMP}.json`,
    )
  })

})

describe('February 19 snapshot export', () => {
  installClockAndMocks()

  it('downloads the snapshot JSON and only console.errors on failure', async () => {
    const exportsApi = useRiskExport()
    vi.mocked(axios.get).mockResolvedValue({ data: REPORT_BODY })
    await exportsApi.downloadSnapshotJson(WINDOW_SINCE, WINDOW_UNTIL)
    expect(vi.mocked(axios.get).mock.calls[0]).toEqual([
      '/api/compare/risk_snapshot',
      {
        params: { since: WINDOW_SINCE, until: WINDOW_UNTIL },
        responseType: 'json',
      },
    ])
    const [blob, filename] = vi.mocked(downloadBlob).mock.calls[0]
    expect(await blobText(blob)).toBe(REPORT_TEXT)
    expect(filename).toBe(
      `risk_snapshot_from-${WINDOW_SINCE}_to-${WINDOW_UNTIL}_${FROZEN_STAMP}.json`,
    )

    vi.mocked(axios.get).mockReset()
    vi.mocked(downloadBlob).mockClear()
    vi.mocked(axios.get).mockRejectedValue(HTTP_404)
    await expect(exportsApi.downloadBucketJson(plainBucket(), [], '', '', '')).resolves.toBeUndefined()
    expect(downloadBlob).not.toHaveBeenCalled()
    expect(console.error).toHaveBeenCalledWith(
      'Failed to download bucket JSON report',
      expect.anything(),
    )
    vi.mocked(axios.get).mockRejectedValue(NETWORK_ERROR)
    await exportsApi.downloadSnapshotJson('', '')
    const snapshotCalls = vi.mocked(axios.get).mock.calls
    expect(snapshotCalls[snapshotCalls.length - 1]).toEqual([
      '/api/compare/risk_snapshot',
      { params: {}, responseType: 'json' },
    ])
    expect(console.error).toHaveBeenCalledWith(
      'Failed to download global risk snapshot',
      expect.anything(),
    )
  })

})

describe('February 19 navigation and filters', () => {
  installClockAndMocks()

  it('navigates by lane prefix and omits an empty job hint and the (none) preset', async () => {
    const mounted = await setupBuckets()
    const cases: Array<[string, string, string]> = [
      ['Rosette', '/art-studio', 'compare'],
      ['Adaptive', '/lab/adaptive', ''],
      ['Relief', '/lab/relief', ''],
      ['Pipeline', '/lab/pipeline', ''],
      ['Other', '/lab/risk-dashboard', ''],
    ]
    for (const [lane, path, tab] of cases) {
      mounted.result.goToLab(plainBucket({ lane, preset: 'Safe' }), JOB_HINT)
      await settleNavigation()
      expect(mounted.router.currentRoute.value.path).toBe(path)
      expect(mounted.router.currentRoute.value.query.lane).toBe(lane.toLowerCase())
      expect(mounted.router.currentRoute.value.query.preset).toBe('Safe')
      expect(mounted.router.currentRoute.value.query.job_hint).toBe(JOB_HINT)
      if (tab) {
        expect(mounted.router.currentRoute.value.query.tab).toBe(tab)
      } else {
        expect(mounted.router.currentRoute.value.query.tab).toBeUndefined()
      }
    }
    mounted.result.goToLab(plainBucket({ preset: '(none)' }), '')
    await settleNavigation()
    expect(mounted.router.currentRoute.value.query.preset).toBeUndefined()
    expect(mounted.router.currentRoute.value.query.job_hint).toBeUndefined()
    expect(axios.get).not.toHaveBeenCalled()
    mounted.app.unmount()
  })

  it('trims URL query values and does not watch filter refs inside the composable', async () => {
    const mounted = await mountWithRouter(() => useRiskFilters())
    const filters = mounted.result
    filters.laneFilter.value = '  Rosette  '
    filters.presetFilter.value = '   '
    filters.jobFilter.value = ' job-7 '
    filters.since.value = ' 2026-01-01 '
    filters.until.value = ''
    await settleNavigation()
    expect(mounted.router.currentRoute.value.query.lane).toBeUndefined()
    filters.syncFiltersToQuery()
    await settleNavigation()
    expect(mounted.router.currentRoute.value.query).toEqual({
      lane: 'Rosette',
      job_hint: 'job-7',
      since: '2026-01-01',
    })
    expect(axios.get).not.toHaveBeenCalled()
    mounted.app.unmount()
  })
})

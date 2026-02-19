/**
 * Composable for risk bucket management.
 * Handles bucket API calls, loading, selection, and computed properties.
 */
import { ref, computed, type Ref, type ComputedRef } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'

export interface Bucket {
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

export interface BucketEntry {
  ts: string
  job_id: string | null
  lane: string
  preset: string | null
  baseline_id: string
  baseline_path_count: number
  current_path_count: number
  added_paths: number
  removed_paths: number
  unchanged_paths: number
}

interface RiskAggregateBucketResponse {
  lane: string
  preset: string
  count: number
  avg_added: number
  avg_removed: number
  avg_unchanged: number
  risk_score: number
  risk_label: string
  added_series: number[]
  removed_series: number[]
}

export interface RiskBucketsState {
  bucketsRaw: Ref<Bucket[]>
  selectedBucket: Ref<Bucket | null>
  bucketEntries: Ref<BucketEntry[]>
  bucketEntriesLoading: Ref<boolean>
  bucketEntriesError: Ref<string | null>
  allLanes: ComputedRef<string[]>
  allPresets: ComputedRef<string[]>
  filteredBuckets: (laneFilter: string, presetFilter: string) => Bucket[]
  filteredEntriesCount: (laneFilter: string, presetFilter: string) => number
  refresh: (since: string, until: string) => Promise<void>
  loadBucketDetails: (bucket: Bucket, jobFilter: string) => Promise<void>
  clearBucketDetails: () => void
  goToLab: (bucket: Bucket, jobFilter: string) => void
}

const SPARK_WIDTH = 60
const SPARK_HEIGHT = 20

function computeRiskScoreLabel(score: number): string {
  if (score < 1) return 'Low'
  if (score < 3) return 'Medium'
  if (score < 6) return 'High'
  return 'Extreme'
}

function buildSparklineFromSeries(values: number[], width: number, height: number): string {
  if (!values.length) return ''

  const maxVal = Math.max(...values, 1)
  const n = values.length

  if (n === 1) {
    const y = height / 2
    return `0,${y} ${width},${y}`
  }

  const stepX = width / (n - 1)
  const points: string[] = []

  for (let i = 0; i < n; i++) {
    const x = stepX * i
    const v = values[i] ?? 0
    const norm = maxVal > 0 ? v / maxVal : 0
    const y = height - norm * (height - 2) - 1
    points.push(`${x.toFixed(1)},${y.toFixed(1)}`)
  }

  return points.join(' ')
}

export function useRiskBuckets(): RiskBucketsState {
  const router = useRouter()

  const bucketsRaw = ref<Bucket[]>([])
  const selectedBucket = ref<Bucket | null>(null)
  const bucketEntries = ref<BucketEntry[]>([])
  const bucketEntriesLoading = ref(false)
  const bucketEntriesError = ref<string | null>(null)

  const allLanes = computed(() => {
    const set = new Set<string>()
    for (const b of bucketsRaw.value) {
      if (b.lane) set.add(b.lane)
    }
    return Array.from(set).sort()
  })

  const allPresets = computed(() => {
    const set = new Set<string>()
    for (const b of bucketsRaw.value) {
      set.add(b.preset || '(none)')
    }
    return Array.from(set).sort()
  })

  function filteredBuckets(laneFilter: string, presetFilter: string): Bucket[] {
    return bucketsRaw.value.filter((b) => {
      if (laneFilter && b.lane !== laneFilter) return false
      if (presetFilter && b.preset !== presetFilter) return false
      return true
    })
  }

  function filteredEntriesCount(laneFilter: string, presetFilter: string): number {
    return filteredBuckets(laneFilter, presetFilter).reduce((acc, b) => acc + b.count, 0)
  }

  async function refresh(since: string, until: string) {
    try {
      const params: Record<string, string> = {}
      if (since) params.since = since
      if (until) params.until = until

      const res = await axios.get<RiskAggregateBucketResponse[]>('/api/compare/risk_aggregate', { params })
      const data = res.data || []

      bucketsRaw.value = data.map((row) => {
        const addedSeries = Array.isArray(row.added_series) ? row.added_series.map((v) => Number(v) || 0) : []
        const removedSeries = Array.isArray(row.removed_series) ? row.removed_series.map((v) => Number(v) || 0) : []
        const riskScore = Number(row.risk_score) || 0
        const riskLabel = row.risk_label || computeRiskScoreLabel(riskScore)

        return {
          key: `${row.lane}::${row.preset}`,
          lane: row.lane,
          preset: row.preset,
          count: row.count,
          avgAdded: row.avg_added,
          avgRemoved: row.avg_removed,
          avgUnchanged: row.avg_unchanged,
          riskScore,
          riskLabel,
          addedSeries,
          removedSeries,
          addedPath: buildSparklineFromSeries(addedSeries, SPARK_WIDTH, SPARK_HEIGHT),
          removedPath: buildSparklineFromSeries(removedSeries, SPARK_WIDTH, SPARK_HEIGHT),
        }
      })
    } catch (err) {
      console.error('Failed to load risk aggregates', err)
      bucketsRaw.value = []
    }
  }

  async function loadBucketDetails(bucket: Bucket, jobFilter: string) {
    selectedBucket.value = bucket
    bucketEntriesLoading.value = true
    bucketEntriesError.value = null
    bucketEntries.value = []

    try {
      const params: Record<string, string> = {
        lane: bucket.lane,
        preset: bucket.preset,
      }
      if (jobFilter) params.job_hint = jobFilter

      const res = await axios.get<BucketEntry[]>('/api/compare/risk_bucket_detail', { params })
      bucketEntries.value = res.data || []
    } catch (err) {
      console.error('Failed to load bucket entries', err)
      bucketEntriesError.value = 'Failed to load bucket entries.'
    } finally {
      bucketEntriesLoading.value = false
    }
  }

  function clearBucketDetails() {
    selectedBucket.value = null
    bucketEntries.value = []
    bucketEntriesError.value = null
    bucketEntriesLoading.value = false
  }

  function goToLab(bucket: Bucket, jobFilter: string) {
    const lane = bucket.lane.toLowerCase()
    const preset = bucket.preset
    const query: Record<string, string> = {}

    if (preset && preset !== '(none)') query.preset = preset
    if (lane) query.lane = lane
    if (jobFilter) query.job_hint = jobFilter

    if (lane.startsWith('rosette')) {
      router.push({ path: '/art-studio', query: { tab: 'compare', ...query } })
    } else if (lane.startsWith('adaptive')) {
      router.push({ path: '/lab/adaptive', query })
    } else if (lane.startsWith('relief')) {
      router.push({ path: '/lab/relief', query })
    } else if (lane.startsWith('pipeline')) {
      router.push({ path: '/lab/pipeline', query })
    } else {
      router.push({ path: '/lab/risk-dashboard', query })
    }
  }

  return {
    bucketsRaw,
    selectedBucket,
    bucketEntries,
    bucketEntriesLoading,
    bucketEntriesError,
    allLanes,
    allPresets,
    filteredBuckets,
    filteredEntriesCount,
    refresh,
    loadBucketDetails,
    clearBucketDetails,
    goToLab,
  }
}

/**
 * Composable for RiskDashboard buckets data management.
 */
import { ref, computed, type Ref, type ComputedRef } from 'vue'
import axios from 'axios'
import { computeRiskScoreLabel, buildSparklineFromSeries } from './riskFormatters'
import type { Bucket } from '@/components/dashboard'

// ============================================================================
// Types
// ============================================================================

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
  filteredBuckets: ComputedRef<Bucket[]>
  filteredEntriesCount: ComputedRef<number>
  allLanes: ComputedRef<string[]>
  allPresets: ComputedRef<string[]>
  refresh: () => Promise<void>
}

export interface UseRiskBucketsOptions {
  laneFilter: Ref<string>
  presetFilter: Ref<string>
  since: Ref<string>
  until: Ref<string>
}

// ============================================================================
// Constants
// ============================================================================

const SPARK_WIDTH = 60
const SPARK_HEIGHT = 20

// ============================================================================
// Composable
// ============================================================================

export function useRiskBuckets(options: UseRiskBucketsOptions): RiskBucketsState {
  const { laneFilter, presetFilter, since, until } = options

  const bucketsRaw = ref<Bucket[]>([])

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

  const filteredBuckets = computed<Bucket[]>(() => {
    return bucketsRaw.value.filter((b) => {
      if (laneFilter.value && b.lane !== laneFilter.value) return false
      if (presetFilter.value && b.preset !== presetFilter.value) return false
      return true
    })
  })

  const filteredEntriesCount = computed(() => {
    return filteredBuckets.value.reduce((acc, b) => acc + b.count, 0)
  })

  async function refresh(): Promise<void> {
    try {
      const params: Record<string, string> = {}
      if (since.value) params.since = since.value
      if (until.value) params.until = until.value

      const res = await axios.get<RiskAggregateBucketResponse[]>(
        '/api/compare/risk_aggregate',
        { params }
      )
      const data = res.data || []

      bucketsRaw.value = data.map((row) => {
        const addedSeries = Array.isArray(row.added_series)
          ? row.added_series.map((v) => Number(v) || 0)
          : []
        const removedSeries = Array.isArray(row.removed_series)
          ? row.removed_series.map((v) => Number(v) || 0)
          : []
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
          removedPath: buildSparklineFromSeries(removedSeries, SPARK_WIDTH, SPARK_HEIGHT)
        }
      })
    } catch (err) {
      console.error('Failed to load risk aggregates', err)
      bucketsRaw.value = []
    }
  }

  return {
    bucketsRaw,
    filteredBuckets,
    filteredEntriesCount,
    allLanes,
    allPresets,
    refresh
  }
}

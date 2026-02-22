/**
 * SnapshotComparePanel comparison logic composable.
 */
import { computed, ref, watch, type Ref, type ComputedRef } from 'vue'
import { artSnapshotsClient } from '@/api/artSnapshotsClient'
import { useToastStore } from '@/stores/toastStore'
import {
  computeConfidence,
  computeConfidenceTrend,
  getConfidenceTooltipText,
  type ConfLevel,
  type ConfTrend
} from '@/utils/rmosConfidence'
import type { AnySnap, RingRow, DeltaRow } from './snapshotCompareTypes'

export interface SnapshotCompareLogicReturn {
  deltaRows: ComputedRef<DeltaRow[]>
  scoreDelta: ComputedRef<number | null>
  warningDelta: ComputedRef<number>
  confidenceLevel: ComputedRef<ConfLevel>
  confidenceTrend: ComputedRef<ConfTrend>
  confidenceTooltip: ComputedRef<string>
  loadSnapshotsForCompare: () => Promise<void>
  ringRows: (snapshot: AnySnap | null) => RingRow[]
}

export function useSnapshotCompareLogic(
  leftId: Ref<string>,
  rightId: Ref<string>,
  left: Ref<AnySnap | null>,
  right: Ref<AnySnap | null>,
  loading: Ref<boolean>,
  error: Ref<string>,
  canCompare: ComputedRef<boolean>
): SnapshotCompareLogicReturn {
  const toast = useToastStore()
  const previousConfidence = ref<ConfLevel | null>(null)

  /**
   * Extract ring rows from a snapshot.
   */
  function ringRows(snapshot: AnySnap | null): RingRow[] {
    const rings = snapshot?.spec?.ring_params || snapshot?.spec?.ringParams || []
    return (rings || []).map((r: any, idx: number) => ({
      idx,
      width_mm: Number(r.width_mm ?? r.widthMm ?? 0),
      pattern: String(r.pattern_key ?? r.patternKey ?? r.pattern_type ?? r.patternType ?? '')
    }))
  }

  /**
   * Compute delta rows between left and right snapshots.
   */
  const deltaRows = computed(() => {
    const a = ringRows(left.value)
    const b = ringRows(right.value)
    const n = Math.max(a.length, b.length)

    const rows: DeltaRow[] = []
    for (let i = 0; i < n; i++) {
      const aw = a[i]?.width_mm ?? 0
      const bw = b[i]?.width_mm ?? 0
      rows.push({
        ring: i + 1,
        aWidth: aw,
        bWidth: bw,
        delta: bw - aw,
        aPattern: a[i]?.pattern ?? '',
        bPattern: b[i]?.pattern ?? ''
      })
    }
    return rows
  })

  /**
   * Score delta between snapshots.
   */
  const scoreDelta = computed(() => {
    const a = left.value?.feasibility?.overall_score ?? left.value?.feasibility?.overallScore ?? null
    const b = right.value?.feasibility?.overall_score ?? right.value?.feasibility?.overallScore ?? null
    if (a == null || b == null) return null
    return Number(b) - Number(a)
  })

  /**
   * Warning count delta.
   */
  const warningDelta = computed(() => {
    const a = left.value?.feasibility?.warnings?.length ?? 0
    const b = right.value?.feasibility?.warnings?.length ?? 0
    return b - a
  })

  /**
   * Confidence level using centralized heuristic.
   */
  const confidenceLevel = computed<ConfLevel>(() => {
    if (!left.value || !right.value) return 'LOW'

    const hotRings = deltaRows.value.filter((r) => Math.abs(r.delta) >= 0.15).length
    const patternChanges = deltaRows.value.filter(
      (r) => r.aPattern !== r.bPattern && (r.aPattern || r.bPattern)
    ).length

    return computeConfidence({ hotRings, patternChanges, warningDelta: warningDelta.value })
  })

  /**
   * Confidence trend arrow.
   */
  const confidenceTrend = computed(() =>
    computeConfidenceTrend(confidenceLevel.value, previousConfidence.value)
  )

  /**
   * Tooltip explaining confidence.
   */
  const confidenceTooltip = computed(() => getConfidenceTooltipText())

  /**
   * Load snapshots for comparison.
   */
  async function loadSnapshotsForCompare(): Promise<void> {
    error.value = ''
    left.value = null
    right.value = null

    if (!canCompare.value) return

    loading.value = true
    try {
      const [a, b] = await Promise.all([
        artSnapshotsClient.get(leftId.value),
        artSnapshotsClient.get(rightId.value)
      ])
      left.value = a as AnySnap
      right.value = b as AnySnap
    } catch (e: any) {
      error.value = e?.message || String(e)
      toast.error(error.value)
    } finally {
      loading.value = false
    }
  }

  // Track previous confidence when compare results change
  watch(
    () => [left.value, right.value] as const,
    ([newLeft, newRight], [oldLeft, oldRight]) => {
      if (!newLeft || !newRight) return

      if (oldLeft && oldRight) {
        previousConfidence.value = confidenceLevel.value
        return
      }

      previousConfidence.value = null
    }
  )

  return {
    deltaRows,
    scoreDelta,
    warningDelta,
    confidenceLevel,
    confidenceTrend,
    confidenceTooltip,
    loadSnapshotsForCompare,
    ringRows
  }
}

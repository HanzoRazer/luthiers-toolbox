/**
 * RosetteCompareHistory sparklines composable.
 */
import { computed, type Ref, type ComputedRef } from 'vue'
import type {
  CompareHistoryEntry,
  PresetBucket,
  PresetSparklineData,
  OverlayPaths
} from './rosetteCompareTypes'
import { SPARK_WIDTH, SPARK_HEIGHT } from './rosetteCompareTypes'

export interface RosetteCompareSparklinesReturn {
  sparkWidth: number
  sparkHeight: number
  addedSparkPath: ComputedRef<string>
  removedSparkPath: ComputedRef<string>
  presetSparklines: ComputedRef<PresetSparklineData[]>
  pairAddedOverlay: ComputedRef<OverlayPaths>
  pairRemovedOverlay: ComputedRef<OverlayPaths>
  buildSparkline: (
    data: CompareHistoryEntry[],
    key: keyof CompareHistoryEntry,
    width: number,
    height: number
  ) => string
}

/**
 * Build a simple polyline "x,y x,y ..." for a sparkline.
 */
function buildSparkline(
  data: CompareHistoryEntry[],
  key: keyof CompareHistoryEntry,
  width: number,
  height: number
): string {
  if (!data.length) return ''

  const values: number[] = data.map((e) => {
    const v = e[key]
    return typeof v === 'number' ? v : 0
  })

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
    const v = values[i]
    const norm = maxVal > 0 ? v / maxVal : 0
    const y = height - norm * (height - 2) - 1
    points.push(`${x.toFixed(1)},${y.toFixed(1)}`)
  }

  return points.join(' ')
}

/**
 * Build overlay sparkline paths for A and B sharing the same scale.
 */
function buildOverlaySparkline(
  dataA: CompareHistoryEntry[],
  dataB: CompareHistoryEntry[],
  key: keyof CompareHistoryEntry,
  width: number,
  height: number
): OverlayPaths {
  const empty = { a: '', b: '' }
  if (!dataA.length && !dataB.length) return empty

  const toValues = (data: CompareHistoryEntry[]) =>
    data.map((e) => {
      const v = e[key]
      return typeof v === 'number' ? v : 0
    })

  const valuesA = toValues(dataA)
  const valuesB = toValues(dataB)
  const allVals = [...valuesA, ...valuesB]
  const maxVal = Math.max(...allVals, 1)

  const buildForSeries = (values: number[]): string => {
    if (!values.length) return ''
    const n = values.length
    if (n === 1) {
      const y = height / 2
      return `0,${y} ${width},${y}`
    }
    const stepX = width / (n - 1)
    const points: string[] = []
    for (let i = 0; i < n; i++) {
      const x = stepX * i
      const v = values[i]
      const norm = maxVal > 0 ? v / maxVal : 0
      const y = height - norm * (height - 2) - 1
      points.push(`${x.toFixed(1)},${y.toFixed(1)}`)
    }
    return points.join(' ')
  }

  return {
    a: buildForSeries(valuesA),
    b: buildForSeries(valuesB)
  }
}

export function useRosetteCompareSparklines(
  entries: Ref<CompareHistoryEntry[]>,
  presetBuckets: ComputedRef<PresetBucket[]>,
  presetCompareAEntries: ComputedRef<CompareHistoryEntry[]>,
  presetCompareBEntries: ComputedRef<CompareHistoryEntry[]>
): RosetteCompareSparklinesReturn {
  const addedSparkPath = computed(() =>
    buildSparkline(entries.value, 'added_paths', SPARK_WIDTH, SPARK_HEIGHT)
  )

  const removedSparkPath = computed(() =>
    buildSparkline(entries.value, 'removed_paths', SPARK_WIDTH, SPARK_HEIGHT)
  )

  const presetSparklines = computed(() =>
    presetBuckets.value.map((bucket) => ({
      name: bucket.name,
      addedPath: buildSparkline(
        bucket.entries,
        'added_paths',
        SPARK_WIDTH,
        SPARK_HEIGHT
      ),
      removedPath: buildSparkline(
        bucket.entries,
        'removed_paths',
        SPARK_WIDTH,
        SPARK_HEIGHT
      )
    }))
  )

  const pairAddedOverlay = computed(() =>
    buildOverlaySparkline(
      presetCompareAEntries.value,
      presetCompareBEntries.value,
      'added_paths',
      SPARK_WIDTH,
      SPARK_HEIGHT
    )
  )

  const pairRemovedOverlay = computed(() =>
    buildOverlaySparkline(
      presetCompareAEntries.value,
      presetCompareBEntries.value,
      'removed_paths',
      SPARK_WIDTH,
      SPARK_HEIGHT
    )
  )

  return {
    sparkWidth: SPARK_WIDTH,
    sparkHeight: SPARK_HEIGHT,
    addedSparkPath,
    removedSparkPath,
    presetSparklines,
    pairAddedOverlay,
    pairRemovedOverlay,
    buildSparkline
  }
}

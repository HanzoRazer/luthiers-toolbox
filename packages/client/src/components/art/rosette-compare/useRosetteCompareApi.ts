/**
 * useRosetteCompareApi.ts - canonical Rosette baseline and diff client.
 * RosetteComparePanel.vue is the only presentation caller. The four requests
 * keep the panel's methods, URLs, payloads, trimming, and response fields.
 */
import { ref } from 'vue'
import axios from 'axios'

export interface GeometryPayload {
  [key: string]: any
  paths?: any[]
  loops?: any[]
}

export interface BaselineSummary {
  id: string
  name: string
  lane: string
  created_at: string
}

export interface DiffStats {
  baseline_path_count: number
  current_path_count: number
  added_paths: number
  removed_paths: number
  unchanged_paths: number
}

export interface DiffOut {
  baseline_id: string
  lane: string
  stats: DiffStats
  baseline_geometry?: GeometryPayload
  current_geometry?: GeometryPayload
}

export interface UseRosetteCompareApiOptions {
  lane?: string
  onDiffComplete?: (result: DiffOut) => void
}

const BASELINES_URL = '/api/compare/baselines'
const DIFF_URL = '/api/compare/diff'

export function useRosetteCompareApi(options: UseRosetteCompareApiOptions = {}) {
  const lane = options.lane || 'rosette'

  const baselines = ref<BaselineSummary[]>([])
  const diffStats = ref<DiffStats | null>(null)
  const baselineGeometry = ref<GeometryPayload | null>(null)
  const loading = ref(false)
  const error = ref('')

  // Overlapping calls, including saveBaseline's nested reload, share one depth
  // so an inner finally cannot report loading as finished while the outer call
  // is still running. Each list, geometry, and diff call also takes a generation.
  // Only the newest generation for that operation may write its state or error.
  let loadingDepth = 0
  let listGeneration = 0
  let geometryGeneration = 0
  let diffGeneration = 0
  let errorGeneration = 0

  function beginLoading(): void {
    loadingDepth += 1
    loading.value = true
  }

  function endLoading(): void {
    loadingDepth = Math.max(0, loadingDepth - 1)
    loading.value = loadingDepth > 0
  }

  async function loadBaselines(): Promise<void> {
    const listGen = ++listGeneration
    const errorGen = ++errorGeneration
    beginLoading()
    error.value = ''
    try {
      const res = await axios.get<BaselineSummary[]>(BASELINES_URL, {
        params: { lane }
      })
      if (listGen !== listGeneration) return
      baselines.value = res.data
    } catch (err) {
      if (listGen !== listGeneration || errorGen !== errorGeneration) return
      console.error('Failed to load baselines', err)
      error.value = 'Failed to load baselines'
    } finally {
      endLoading()
    }
  }

  async function saveBaseline(name: string, geometry: GeometryPayload): Promise<string | null> {
    if (!name || !geometry) return null

    const errorGen = ++errorGeneration
    beginLoading()
    error.value = ''
    try {
      const payload = {
        name,
        lane,
        geometry
      }
      const res = await axios.post<{ id?: string }>(BASELINES_URL, payload)
      await loadBaselines()
      return res.data?.id ?? null
    } catch (err) {
      if (errorGen !== errorGeneration) return null
      console.error('Failed to save baseline', err)
      error.value = 'Failed to save baseline'
      return null
    } finally {
      endLoading()
    }
  }

  async function loadBaselineGeometry(baselineId: string): Promise<GeometryPayload | null> {
    const geometryGen = ++geometryGeneration
    if (!baselineId) {
      baselineGeometry.value = null
      return null
    }

    const errorGen = ++errorGeneration
    error.value = ''
    try {
      const res = await axios.get<{ geometry?: GeometryPayload | null }>(
        `${BASELINES_URL}/${encodeURIComponent(baselineId)}`
      )
      if (geometryGen !== geometryGeneration) return null
      const geometry = res.data.geometry ?? null
      baselineGeometry.value = geometry
      return geometry
    } catch (err) {
      if (geometryGen !== geometryGeneration || errorGen !== errorGeneration) return null
      console.error('Failed to load baseline geometry', err)
      error.value = 'Failed to load baseline geometry'
      return null
    }
  }

  async function runDiff(
    baselineId: string,
    currentGeometry: GeometryPayload,
    opts: { jobId?: string; preset?: string } = {}
  ): Promise<DiffOut | null> {
    if (!baselineId || !currentGeometry) return null

    const diffGen = ++diffGeneration
    const errorGen = ++errorGeneration
    beginLoading()
    error.value = ''
    try {
      const payload: {
        baseline_id: string
        lane: string
        current_geometry: GeometryPayload
        job_id?: string
        preset?: string
      } = {
        baseline_id: baselineId,
        lane,
        current_geometry: currentGeometry
      }

      if (opts.jobId?.trim()) {
        payload.job_id = opts.jobId.trim()
      }

      if (opts.preset?.trim()) {
        payload.preset = opts.preset.trim()
      }

      const res = await axios.post<DiffOut>(DIFF_URL, payload)
      if (diffGen !== diffGeneration) return null
      diffStats.value = res.data.stats
      baselineGeometry.value = res.data.baseline_geometry || null

      if (options.onDiffComplete) {
        options.onDiffComplete(res.data)
      }

      return res.data
    } catch (err) {
      if (diffGen !== diffGeneration || errorGen !== errorGeneration) return null
      console.error('Failed to run diff', err)
      error.value = 'Failed to run diff'
      return null
    } finally {
      endLoading()
    }
  }

  return {
    baselines,
    diffStats,
    baselineGeometry,
    loading,
    error,
    loadBaselines,
    saveBaseline,
    loadBaselineGeometry,
    runDiff
  }
}

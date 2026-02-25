/**
 * useRosetteCompareApi.ts - API composable for rosette comparison
 * Extracted from RosetteComparePanel.vue
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

export function useRosetteCompareApi(options: UseRosetteCompareApiOptions = {}) {
  const lane = options.lane || 'rosette'

  const baselines = ref<BaselineSummary[]>([])
  const diffStats = ref<DiffStats | null>(null)
  const baselineGeometry = ref<GeometryPayload | null>(null)
  const loading = ref(false)
  const error = ref('')

  async function loadBaselines() {
    loading.value = true
    error.value = ''
    try {
      const res = await axios.get<BaselineSummary[]>('/api/compare/baselines', {
        params: { lane }
      })
      baselines.value = res.data
    } catch (err) {
      console.error('Failed to load baselines', err)
      error.value = 'Failed to load baselines'
    } finally {
      loading.value = false
    }
  }

  async function saveBaseline(name: string, geometry: GeometryPayload): Promise<string | null> {
    if (!name || !geometry) return null

    loading.value = true
    error.value = ''
    try {
      const payload = {
        name,
        lane,
        geometry
      }
      const res = await axios.post('/api/compare/baselines', payload)
      await loadBaselines()
      return res.data.id
    } catch (err) {
      console.error('Failed to save baseline', err)
      error.value = 'Failed to save baseline'
      return null
    } finally {
      loading.value = false
    }
  }

  async function loadBaselineGeometry(baselineId: string): Promise<GeometryPayload | null> {
    if (!baselineId) {
      baselineGeometry.value = null
      return null
    }

    try {
      const res = await axios.get('/api/compare/baselines/' + baselineId)
      baselineGeometry.value = res.data.geometry
      return res.data.geometry
    } catch (err) {
      console.error('Failed to load baseline geometry', err)
      return null
    }
  }

  async function runDiff(
    baselineId: string,
    currentGeometry: GeometryPayload,
    opts: { jobId?: string; preset?: string } = {}
  ): Promise<DiffOut | null> {
    if (!baselineId || !currentGeometry) return null

    loading.value = true
    error.value = ''
    try {
      const payload: Record<string, any> = {
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

      const res = await axios.post<DiffOut>('/api/compare/diff', payload)
      diffStats.value = res.data.stats
      baselineGeometry.value = res.data.baseline_geometry || null

      if (options.onDiffComplete) {
        options.onDiffComplete(res.data)
      }

      return res.data
    } catch (err) {
      console.error('Failed to run diff', err)
      error.value = 'Failed to run diff'
      return null
    } finally {
      loading.value = false
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

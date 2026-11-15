/**
 * useRosetteCompareApi.ts - canonical Rosette baseline and diff client.
 * RosetteComparePanel.vue is the only presentation caller. The four requests
 * keep the panel's methods, URLs, payloads, trimming, and response fields.
 */
import { computed, reactive, ref } from 'vue'
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

type Operation = 'list' | 'save' | 'geometry' | 'diff'

export function useRosetteCompareApi(options: UseRosetteCompareApiOptions = {}) {
  const lane = options.lane || 'rosette'

  const baselines = ref<BaselineSummary[]>([])
  const diffStats = ref<DiffStats | null>(null)
  const baselineGeometry = ref<GeometryPayload | null>(null)
  const loading = ref(false)

  // Errors are owned per operation. Starting an operation clears only its own
  // error, and a stale request is judged only by its own operation's generation,
  // so a newer request of one kind can neither erase nor suppress the failure of
  // another kind. `error` shows the most recent failure that is still standing.
  const errors = reactive<Record<Operation, { message: string; seq: number }>>({
    list: { message: '', seq: 0 },
    save: { message: '', seq: 0 },
    geometry: { message: '', seq: 0 },
    diff: { message: '', seq: 0 }
  })
  let errorSeq = 0
  const error = computed(() => {
    let latest = { message: '', seq: 0 }
    for (const entry of Object.values(errors)) {
      if (entry.message && entry.seq > latest.seq) latest = entry
    }
    return latest.message
  })

  function setError(op: Operation, message: string): void {
    errors[op].message = message
    errors[op].seq = message ? ++errorSeq : 0
  }

  // Overlapping calls, including saveBaseline's nested reload, share one depth
  // so an inner finally cannot report loading as finished while the outer call
  // is still running. Each operation also takes a generation. Only the newest
  // generation for that operation may write its state or error.
  let loadingDepth = 0
  let listGeneration = 0
  let saveGeneration = 0
  let geometryGeneration = 0
  let diffGeneration = 0

  // A diff result describes one baseline and one current geometry. Once either
  // changes, the pending request must be dropped and the shown result removed.
  let pendingDiffBaselineId: string | null = null
  let shownDiffBaselineId: string | null = null
  let diffCommits = 0
  // Which baseline baselineGeometry currently shows, and the last plain (not
  // diff-colored) geometry loaded, so clearing a comparison can restore it.
  let displayedBaselineId: string | null = null
  let plainBaseline: { id: string; geometry: GeometryPayload | null } | null = null

  function beginLoading(): void {
    loadingDepth += 1
    loading.value = true
  }

  function endLoading(): void {
    loadingDepth = Math.max(0, loadingDepth - 1)
    loading.value = loadingDepth > 0
  }

  /**
   * Drop any pending comparison and remove the shown one. Call this whenever the
   * current geometry changes; loadBaselineGeometry calls it when the baseline
   * changes. A diff-colored baseline geometry is replaced by the plain geometry
   * of the same baseline when it is known, otherwise by null.
   */
  function clearDiff(): void {
    diffGeneration += 1
    pendingDiffBaselineId = null
    diffStats.value = null
    setError('diff', '')
    if (shownDiffBaselineId !== null) {
      const id = shownDiffBaselineId
      shownDiffBaselineId = null
      if (displayedBaselineId === id) {
        baselineGeometry.value = plainBaseline?.id === id ? plainBaseline.geometry : null
      }
    }
  }

  async function loadBaselines(): Promise<void> {
    const listGen = ++listGeneration
    beginLoading()
    setError('list', '')
    try {
      const res = await axios.get<BaselineSummary[]>(BASELINES_URL, {
        params: { lane }
      })
      if (listGen !== listGeneration) return
      baselines.value = res.data
    } catch (err) {
      if (listGen !== listGeneration) return
      console.error('Failed to load baselines', err)
      setError('list', 'Failed to load baselines')
    } finally {
      endLoading()
    }
  }

  async function saveBaseline(name: string, geometry: GeometryPayload): Promise<string | null> {
    if (!name || !geometry) return null

    const saveGen = ++saveGeneration
    beginLoading()
    setError('save', '')
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
      if (saveGen !== saveGeneration) return null
      console.error('Failed to save baseline', err)
      setError('save', 'Failed to save baseline')
      return null
    } finally {
      endLoading()
    }
  }

  async function loadBaselineGeometry(baselineId: string): Promise<GeometryPayload | null> {
    const geometryGen = ++geometryGeneration
    setError('geometry', '')

    // A comparison against any other baseline no longer matches the selection.
    if (
      (pendingDiffBaselineId !== null && pendingDiffBaselineId !== baselineId) ||
      (shownDiffBaselineId !== null && shownDiffBaselineId !== baselineId)
    ) {
      clearDiff()
    }
    // Never leave another baseline's geometry under this selection while it
    // loads, or after it fails to load.
    if (displayedBaselineId !== baselineId) {
      baselineGeometry.value = null
      displayedBaselineId = null
    }
    if (!baselineId) return null

    const commitsAtStart = diffCommits
    try {
      const res = await axios.get<{ geometry?: GeometryPayload | null }>(
        `${BASELINES_URL}/${encodeURIComponent(baselineId)}`
      )
      if (geometryGen !== geometryGeneration) return null
      const geometry = res.data.geometry ?? null
      plainBaseline = { id: baselineId, geometry }
      // A comparison for this baseline landed while the plain geometry was in
      // flight. Its colored geometry is newer, so it stays on screen.
      if (diffCommits !== commitsAtStart && shownDiffBaselineId === baselineId) return null
      baselineGeometry.value = geometry
      displayedBaselineId = baselineId
      return geometry
    } catch (err) {
      if (geometryGen !== geometryGeneration) return null
      console.error('Failed to load baseline geometry', err)
      setError('geometry', 'Failed to load baseline geometry')
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
    pendingDiffBaselineId = baselineId
    beginLoading()
    setError('diff', '')
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
      pendingDiffBaselineId = null
      shownDiffBaselineId = baselineId
      displayedBaselineId = baselineId
      diffCommits += 1
      diffStats.value = res.data.stats
      baselineGeometry.value = res.data.baseline_geometry || null

      if (options.onDiffComplete) {
        options.onDiffComplete(res.data)
      }

      return res.data
    } catch (err) {
      if (diffGen !== diffGeneration) return null
      pendingDiffBaselineId = null
      console.error('Failed to run diff', err)
      setError('diff', 'Failed to run diff')
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
    runDiff,
    clearDiff
  }
}

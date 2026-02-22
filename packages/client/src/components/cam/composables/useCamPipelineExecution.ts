/**
 * CamPipeline execution composable.
 */
import type { Ref } from 'vue'
import { api } from '@/services/apiBase'
import type {
  PipelineOpResult,
  PipelineResponse,
  NormalizationEntry,
  CamPipelineEmits
} from './camPipelineTypes'

// ============================================================================
// Types
// ============================================================================

export interface CamPipelineExecutionReturn {
  buildPipelineSpec: () => Record<string, any>
  runPipeline: () => Promise<void>
}

// ============================================================================
// Composable
// ============================================================================

export function useCamPipelineExecution(
  file: Ref<File | null>,
  loading: Ref<boolean>,
  error: Ref<string | null>,
  results: Ref<PipelineOpResult[] | null>,
  summary: Ref<Record<string, any> | null>,
  openPayloadIndex: Ref<number | null>,
  toolDia: Ref<number>,
  units: Ref<'mm' | 'inch'>,
  bridgeProfile: Ref<boolean>,
  machineId: Ref<string | null>,
  postId: Ref<string | null>,
  strictNormalize: Ref<boolean>,
  normalizationIssues: Ref<NormalizationEntry[]>,
  normalizePipelineSpecDeep: (spec: any) => Promise<{
    normalized: any
    issues: NormalizationEntry[]
  }>,
  emit: CamPipelineEmits
): CamPipelineExecutionReturn {
  /**
   * Build the pipeline specification from current state.
   */
  function buildPipelineSpec(): Record<string, any> {
    const ops: any[] = []

    ops.push({
      kind: 'dxf_preflight',
      params: {
        profile: bridgeProfile.value ? 'bridge' : null,
        cam_layer_prefix: 'CAM_',
        debug: true
      }
    })

    ops.push({ kind: 'adaptive_plan', params: {} })
    ops.push({ kind: 'adaptive_plan_run', params: {} })

    ops.push({
      kind: 'export_post',
      params: {
        endpoint: '/cam/roughing_gcode',
        post_id: postId.value ?? undefined,
        units: units.value
      }
    })

    ops.push({
      kind: 'simulate_gcode',
      params: {
        machine_id: machineId.value ?? undefined
      }
    })

    return {
      ops,
      tool_d: toolDia.value || 6.0,
      units: units.value,
      geometry_layer: null,
      auto_scale: true,
      cam_layer_prefix: 'CAM_',
      machine_id: machineId.value ?? undefined,
      post_id: postId.value ?? undefined
    }
  }

  /**
   * Execute the full pipeline.
   */
  async function runPipeline(): Promise<void> {
    if (!file.value) return
    loading.value = true
    error.value = null
    results.value = null
    summary.value = null
    openPayloadIndex.value = null
    normalizationIssues.value = []

    try {
      const form = new FormData()
      form.append('file', file.value)

      // H7.2: normalize CamIntent(s) inside the pipeline before submit
      const pipelineDraft = buildPipelineSpec()
      const { normalized: pipelineNormalized, issues } =
        await normalizePipelineSpecDeep(pipelineDraft)
      normalizationIssues.value = issues

      if (strictNormalize.value && issues.length > 0) {
        // strict mode: fail early (non-breaking because default strict=false)
        const msg =
          issues
            .slice(0, 10)
            .map(x => `${x.path}: ${x.issues.map(i => i.message).join('; ')}`)
            .join(' | ') + (issues.length > 10 ? ' | ...' : '')
        throw new Error(`CAM intent normalization failed (strict): ${msg}`)
      }

      form.append('pipeline', JSON.stringify(pipelineNormalized))

      const resp = await api('/api/cam/pipeline/run', {
        method: 'POST',
        body: form
      })

      if (!resp.ok) {
        const text = await resp.text()
        throw new Error(text || `HTTP ${resp.status}`)
      }

      const data = (await resp.json()) as PipelineResponse
      results.value = data.ops
      summary.value = data.summary ?? {}

      // Emit adaptive-plan-ready event for backplot
      const lastAdaptive = [...(data.ops || [])]
        .reverse()
        .find(op => op.kind === 'adaptive_plan_run' && op.ok && op.payload)
      if (lastAdaptive && lastAdaptive.payload) {
        const moves = lastAdaptive.payload.moves ?? []
        const stats = lastAdaptive.payload.stats ?? {}
        const overlays = lastAdaptive.payload.overlays ?? []
        emit('adaptive-plan-ready', { moves, stats, overlays })
      }

      // Emit sim-result-ready event for backplot severity coloring
      const lastSim = [...(data.ops || [])]
        .reverse()
        .find(op => op.kind === 'simulate_gcode' && op.ok && op.payload)
      if (lastSim && lastSim.payload) {
        const issues = lastSim.payload.issues ?? []
        const moves = lastSim.payload.moves ?? []
        const summarySim = lastSim.payload.summary ?? {}
        emit('sim-result-ready', { issues, moves, summary: summarySim })
      }
    } catch (e: any) {
      error.value = e?.message ?? String(e)
    } finally {
      loading.value = false
    }
  }

  return {
    buildPipelineSpec,
    runPipeline
  }
}

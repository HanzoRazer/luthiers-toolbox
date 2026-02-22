/**
 * Composable for pipeline spec building and execution.
 */
import { api } from '@/services/apiBase'
import type {
  PipelineOpResult,
  PipelineResponse,
  AdaptivePlanReadyPayload,
  SimResultReadyPayload,
  NormalizationEntry
} from './pipelineTypes'

// ============================================================================
// Types
// ============================================================================

export interface PipelineSpec {
  ops: any[]
  tool_d: number
  units: 'mm' | 'inch'
  geometry_layer: null
  auto_scale: boolean
  cam_layer_prefix: string
  machine_id?: string
  post_id?: string
}

export interface BuildPipelineOptions {
  toolDia: number
  units: 'mm' | 'inch'
  bridgeProfile: boolean
  machineId: string | null
  postId: string | null
}

export interface RunPipelineOptions {
  file: File
  spec: PipelineSpec
  strictNormalize: boolean
  normalizePipelineSpec: (spec: any) => Promise<{
    normalized: any
    issues: NormalizationEntry[]
  }>
  onNormalizationIssues: (issues: NormalizationEntry[]) => void
  onAdaptivePlanReady: (payload: AdaptivePlanReadyPayload) => void
  onSimResultReady: (payload: SimResultReadyPayload) => void
}

export interface RunPipelineResult {
  results: PipelineOpResult[]
  summary: Record<string, any>
}

// ============================================================================
// Functions
// ============================================================================

/**
 * Build a pipeline specification from control options.
 */
export function buildPipelineSpec(options: BuildPipelineOptions): PipelineSpec {
  const ops: any[] = []

  ops.push({
    kind: 'dxf_preflight',
    params: {
      profile: options.bridgeProfile ? 'bridge' : null,
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
      post_id: options.postId ?? undefined,
      units: options.units
    }
  })

  ops.push({
    kind: 'simulate_gcode',
    params: {
      machine_id: options.machineId ?? undefined
    }
  })

  return {
    ops,
    tool_d: options.toolDia || 6.0,
    units: options.units,
    geometry_layer: null,
    auto_scale: true,
    cam_layer_prefix: 'CAM_',
    machine_id: options.machineId ?? undefined,
    post_id: options.postId ?? undefined
  }
}

/**
 * Execute the pipeline with normalization and event emission.
 */
export async function runPipeline(options: RunPipelineOptions): Promise<RunPipelineResult> {
  const form = new FormData()
  form.append('file', options.file)

  // H7.2: normalize CamIntent(s) inside the pipeline before submit
  const { normalized: pipelineNormalized, issues } = await options.normalizePipelineSpec(
    options.spec
  )
  options.onNormalizationIssues(issues)

  if (options.strictNormalize && issues.length > 0) {
    // strict mode: fail early
    const msg =
      issues
        .slice(0, 10)
        .map((x) => `${x.path}: ${x.issues.map((i) => i.message).join('; ')}`)
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

  const data = await resp.json() as PipelineResponse
  const results = data.ops
  const summary = data.summary ?? {}

  // Emit adaptive-plan-ready event for backplot
  const lastAdaptive = [...(results || [])].reverse()
    .find(op => op.kind === 'adaptive_plan_run' && op.ok && op.payload)
  if (lastAdaptive && lastAdaptive.payload) {
    const moves = lastAdaptive.payload.moves ?? []
    const stats = lastAdaptive.payload.stats ?? {}
    const overlays = lastAdaptive.payload.overlays ?? []
    options.onAdaptivePlanReady({ moves, stats, overlays })
  }

  // Emit sim-result-ready event for backplot severity coloring
  const lastSim = [...(results || [])].reverse()
    .find(op => op.kind === 'simulate_gcode' && op.ok && op.payload)
  if (lastSim && lastSim.payload) {
    const issues = lastSim.payload.issues ?? []
    const moves = lastSim.payload.moves ?? []
    const summarySim = lastSim.payload.summary ?? {}
    options.onSimResultReady({ issues, moves, summary: summarySim })
  }

  return { results, summary }
}

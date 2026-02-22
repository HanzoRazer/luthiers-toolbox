/**
 * AdaptiveKernelLab pipeline export composable.
 */
import { computed, type Ref, type ComputedRef } from 'vue'
import type { AdaptivePlanIn } from '@/api/adaptive'
import { ADAPTIVE_PIPELINE_PRESET_KEY } from './adaptiveKernelTypes'

// ============================================================================
// Types
// ============================================================================

export interface AdaptiveKernelPipelineReturn {
  pipelineSnippet: ComputedRef<string>
  sendToPipelineLab: () => void
}

// ============================================================================
// Composable
// ============================================================================

export function useAdaptiveKernelPipeline(
  buildPayload: () => AdaptivePlanIn,
  sentToPipeline: Ref<boolean>,
  errorMsg: Ref<string | null>
): AdaptiveKernelPipelineReturn {
  /**
   * Generate pipeline snippet from current params.
   */
  const pipelineSnippet = computed<string>(() => {
    try {
      const plan = buildPayload()

      // Strip loops for pipeline input (loops come from DXF in pipeline world)
      const {
        loops, // eslint-disable-line @typescript-eslint/no-unused-vars
        ...inputForPipeline
      } = plan as any

      const skeleton = {
        design: {
          source: 'dxf',
          dxf_path: 'workspace/bodies/body01.dxf', // change per job
          units: plan.units
        },
        context: {
          machine_profile_id: 'GUITAR_CNC_01',
          post_preset: 'GRBL',
          workspace_id: 'body01_session'
        },
        ops: [
          {
            id: 'body_adaptive_pocket',
            op: 'AdaptivePocket',
            from_layer: 'GEOMETRY',
            input: {
              tool_d: inputForPipeline.tool_d,
              stepover: inputForPipeline.stepover,
              stepdown: inputForPipeline.stepdown,
              margin: inputForPipeline.margin,
              strategy: inputForPipeline.strategy,
              smoothing: inputForPipeline.smoothing,
              climb: inputForPipeline.climb,
              feed_xy: inputForPipeline.feed_xy,
              safe_z: inputForPipeline.safe_z,
              z_rough: inputForPipeline.z_rough,
              corner_radius_min: inputForPipeline.corner_radius_min,
              target_stepover: inputForPipeline.target_stepover,
              slowdown_feed_pct: inputForPipeline.slowdown_feed_pct,
              use_trochoids: inputForPipeline.use_trochoids,
              trochoid_radius: inputForPipeline.trochoid_radius,
              trochoid_pitch: inputForPipeline.trochoid_pitch,
              jerk_aware: inputForPipeline.jerk_aware,
              machine_feed_xy: inputForPipeline.machine_feed_xy,
              machine_rapid: inputForPipeline.machine_rapid,
              machine_accel: inputForPipeline.machine_accel,
              machine_jerk: inputForPipeline.machine_jerk,
              corner_tol_mm: inputForPipeline.corner_tol_mm,
              machine_profile_id: inputForPipeline.machine_profile_id,
              adopt_overrides: inputForPipeline.adopt_overrides,
              session_override_factor: inputForPipeline.session_override_factor
            }
          }
        ]
      }

      return JSON.stringify(skeleton, null, 2)
    } catch (e: any) {
      return (
        '// Unable to build pipeline snippet.\n' +
        '// Fix loops JSON or parameters first.\n' +
        '// Error: ' +
        (e?.message || String(e))
      )
    }
  })

  /**
   * Send pipeline snippet to localStorage for PipelineLab.
   */
  function sendToPipelineLab(): void {
    const snippet = pipelineSnippet.value
    if (!snippet || snippet.startsWith('// Unable to build')) {
      sentToPipeline.value = false
      errorMsg.value =
        'Cannot send to PipelineLab: fix loops / params so the pipeline snippet is valid first.'
      return
    }
    try {
      localStorage.setItem(ADAPTIVE_PIPELINE_PRESET_KEY, snippet)
      sentToPipeline.value = true
    } catch (e: any) {
      sentToPipeline.value = false
      errorMsg.value =
        'Failed to store preset in localStorage: ' + (e?.message || String(e))
    }
  }

  return {
    pipelineSnippet,
    sendToPipelineLab
  }
}

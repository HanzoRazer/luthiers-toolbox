/**
 * AdaptiveKernelLab payload building and execution composable.
 */
import type { Ref } from 'vue'
import {
  planAdaptive,
  type AdaptivePlanIn,
  type AdaptivePlanOut,
  type Loop
} from '@/api/adaptive'

// ============================================================================
// Types
// ============================================================================

export interface AdaptiveKernelPayloadReturn {
  loadDemoLoops: () => void
  buildPayload: () => AdaptivePlanIn
  runAdaptive: () => Promise<void>
}

// ============================================================================
// Composable
// ============================================================================

export function useAdaptiveKernelPayload(
  loopsText: Ref<string>,
  units: Ref<'mm' | 'inch'>,
  toolD: Ref<number>,
  stepover: Ref<number>,
  stepdown: Ref<number>,
  margin: Ref<number>,
  strategy: Ref<'Spiral' | 'Lanes'>,
  feedXY: Ref<number>,
  safeZ: Ref<number>,
  zRough: Ref<number>,
  cornerRadiusMin: Ref<number>,
  targetStepover: Ref<number>,
  slowdownFeedPct: Ref<number>,
  useTrochoids: Ref<boolean>,
  trochoidRadius: Ref<number>,
  trochoidPitch: Ref<number>,
  lastRequest: Ref<AdaptivePlanIn | null>,
  result: Ref<AdaptivePlanOut | null>,
  errorMsg: Ref<string | null>,
  busy: Ref<boolean>
): AdaptiveKernelPayloadReturn {
  /**
   * Load demo rectangle loop (100x60 with one island).
   */
  function loadDemoLoops(): void {
    const demo: Loop[] = [
      {
        pts: [
          [0, 0],
          [100, 0],
          [100, 60],
          [0, 60]
        ]
      },
      {
        pts: [
          [30, 15],
          [70, 15],
          [70, 45],
          [30, 45]
        ]
      }
    ]
    loopsText.value = JSON.stringify(demo, null, 2)
  }

  /**
   * Build payload from current state.
   */
  function buildPayload(): AdaptivePlanIn {
    let loops: Loop[]
    try {
      const parsed = JSON.parse(loopsText.value || '[]')
      if (!Array.isArray(parsed)) throw new Error('loops must be an array')
      loops = parsed
    } catch (e: any) {
      throw new Error(
        'Invalid loops JSON. It must be an array like: [{"pts": [[0,0],[100,0],...]}]\n' +
          (e?.message || String(e))
      )
    }

    if (!loops.length) {
      throw new Error('At least one loop is required.')
    }

    return {
      loops,
      units: units.value,
      tool_d: toolD.value,
      stepover: stepover.value,
      stepdown: stepdown.value,
      margin: margin.value,
      strategy: strategy.value,
      smoothing: 0.5,
      climb: true,
      feed_xy: feedXY.value,
      safe_z: safeZ.value,
      z_rough: zRough.value,
      corner_radius_min: cornerRadiusMin.value,
      target_stepover: targetStepover.value,
      slowdown_feed_pct: slowdownFeedPct.value,
      use_trochoids: useTrochoids.value,
      trochoid_radius: trochoidRadius.value,
      trochoid_pitch: trochoidPitch.value,
      jerk_aware: false,
      machine_feed_xy: feedXY.value,
      machine_rapid: 3000,
      machine_accel: 800,
      machine_jerk: 2000,
      corner_tol_mm: 0.2,
      machine_profile_id: null,
      adopt_overrides: false,
      session_override_factor: null
    }
  }

  /**
   * Run adaptive kernel.
   */
  async function runAdaptive(): Promise<void> {
    errorMsg.value = null
    busy.value = true
    result.value = null
    try {
      const payload = buildPayload()
      lastRequest.value = payload
      const res = await planAdaptive(payload)
      result.value = res
    } catch (e: any) {
      errorMsg.value = e?.message || String(e)
    } finally {
      busy.value = false
    }
  }

  return {
    loadDemoLoops,
    buildPayload,
    runAdaptive
  }
}

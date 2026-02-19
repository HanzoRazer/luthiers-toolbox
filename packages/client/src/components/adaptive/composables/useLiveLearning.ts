/**
 * Composable for live learning and run logging.
 * Handles session override factors, run logging, and feed override training.
 */
import { ref, type Ref } from 'vue'
import { api } from '@/services/apiBase'
import type { Move } from './useToolpathRenderer'

// Live learn clamps (safety)
const LL_MIN = 0.8 // -20%
const LL_MAX = 1.25 // +25%

export interface PlanStats {
  time_s_jerk?: number
  time_s_classic?: number
}

export interface LiveLearningState {
  adoptOverrides: Ref<boolean>
  sessionOverrideFactor: Ref<number | null>
  liveLearnApplied: Ref<boolean>
  measuredSeconds: Ref<number | null>
  computeLiveLearnFactor: (estimatedSeconds: number, actualSeconds: number) => number | null
  patchBodyWithSessionOverride: <T extends Record<string, unknown>>(body: T) => T
  logCurrentRun: (
    moves: Move[],
    stats: PlanStats | null,
    profileId: string,
    materialId: string,
    toolD: number,
    stepoverPct: number,
    stepdown: number,
    feedXY: number,
    actualSeconds?: number
  ) => Promise<void>
  trainOverrides: (profileId: string) => Promise<void>
  resetLiveLearning: () => void
}

export function useLiveLearning(): LiveLearningState {
  const adoptOverrides = ref(true)
  const sessionOverrideFactor = ref<number | null>(null)
  const liveLearnApplied = ref(false)
  const measuredSeconds = ref<number | null>(null)

  function computeLiveLearnFactor(estimatedSeconds: number, actualSeconds: number): number | null {
    if (!estimatedSeconds || !actualSeconds) return null
    // time ~ 1 / feed ⇒ feed scale ≈ actual / estimated
    const raw = actualSeconds / estimatedSeconds
    const clamped = Math.max(LL_MIN, Math.min(LL_MAX, raw))
    return Number(clamped.toFixed(3))
  }

  function patchBodyWithSessionOverride<T extends Record<string, unknown>>(body: T): T {
    if (liveLearnApplied.value && sessionOverrideFactor.value) {
      ;(body as Record<string, unknown>).session_override_factor = sessionOverrideFactor.value
    }
    if (adoptOverrides.value) {
      ;(body as Record<string, unknown>).adopt_overrides = true
    }
    return body
  }

  async function logCurrentRun(
    moves: Move[],
    stats: PlanStats | null,
    profileId: string,
    materialId: string,
    toolD: number,
    stepoverPct: number,
    stepdown: number,
    feedXY: number,
    actualSeconds?: number
  ) {
    if (!moves.length) {
      alert('No moves available to log')
      return
    }

    try {
      const segs = moves.map((m, i) => ({
        idx: i,
        code: m.code,
        x: m.x,
        y: m.y,
        len_mm: m._len_mm || 0,
        limit: m.meta?.limit || null,
        slowdown: m.meta?.slowdown ?? null,
        trochoid: !!m.meta?.trochoid,
        radius_mm: m.meta?.radius_mm ?? null,
        feed_f: m.f ?? null,
      }))

      const run = {
        job_name: 'pocket',
        machine_id: profileId || 'Mach4_Router_4x8',
        material_id: materialId || 'maple_hard',
        tool_d: toolD,
        stepover: stepoverPct / 100,
        stepdown,
        post_id: null,
        feed_xy: feedXY || undefined,
        rpm: undefined,
        est_time_s: stats?.time_s_jerk ?? stats?.time_s_classic ?? null,
        act_time_s: actualSeconds ?? null,
        notes: null,
      }

      const r = await api('/api/cam/logs/write', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ run, segments: segs }),
      })

      if (!r.ok) {
        throw new Error(await r.text())
      }

      const data = await r.json()

      // Live learn: compute session factor if actual time provided
      const est = stats?.time_s_jerk ?? stats?.time_s_classic
      if (actualSeconds && est) {
        const f = computeLiveLearnFactor(est, actualSeconds)
        if (f) {
          sessionOverrideFactor.value = f
          liveLearnApplied.value = true
          console.info(`Live learn: session feed scale set to ×${f}`)
        }
      }

      alert(
        `Logged run ${data.run_id} successfully` +
          (sessionOverrideFactor.value ? `\nLive learn: ×${sessionOverrideFactor.value}` : '')
      )
    } catch (e: unknown) {
      alert('Log run failed: ' + e)
    }
  }

  async function trainOverrides(profileId: string) {
    if (!profileId) {
      alert('Select machine profile first')
      return
    }

    try {
      const r = await api('/api/cam/learn/train', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ machine_profile: profileId, r_min_mm: 5 }),
      })

      if (!r.ok) {
        throw new Error(await r.text())
      }

      const out = await r.json()
      alert(
        `Learned rules for ${out.machine_profile || out.machine_id}:\n` +
          JSON.stringify(out.rules, null, 2)
      )
    } catch (e: unknown) {
      alert('Train overrides failed: ' + e)
    }
  }

  function resetLiveLearning() {
    liveLearnApplied.value = false
    sessionOverrideFactor.value = null
    measuredSeconds.value = null
  }

  return {
    adoptOverrides,
    sessionOverrideFactor,
    liveLearnApplied,
    measuredSeconds,
    computeLiveLearnFactor,
    patchBodyWithSessionOverride,
    logCurrentRun,
    trainOverrides,
    resetLiveLearning,
  }
}

/**
 * Composable for M.4 Run Logging functionality.
 * Handles logging toolpath runs to database and training feed overrides.
 */
import { computed, type Ref, type ComputedRef } from 'vue'
import { api } from '@/services/apiBase'
import type { Move } from './useToolpathRenderer'
import type { PocketStats } from './usePocketPlanning'

// ============================================================================
// Types
// ============================================================================

export interface RunLoggingConfig {
  // From usePocketSettings
  toolD: Ref<number>
  stepoverPct: Ref<number>
  stepdown: Ref<number>
  feedXY: Ref<number>

  // Machine ID (for profileId)
  machineId: Ref<string>
}

export interface RunLoggingDeps {
  // From usePocketPlanning
  moves: Ref<Move[]>
  stats: Ref<PocketStats | null>
  plan: () => Promise<void>

  // From useEnergyMetrics
  materialId: Ref<string>

  // From useLiveLearning
  computeLiveLearnFactor: (est: number, act: number) => number | null
  sessionOverrideFactor: Ref<number | null>
  liveLearnApplied: Ref<boolean>
}

export interface RunLoggingState {
  logCurrentRun: (actualSeconds?: number) => Promise<void>
  trainOverrides: () => Promise<void>
}

// ============================================================================
// Composable
// ============================================================================

export function useRunLogging(
  config: RunLoggingConfig,
  deps: RunLoggingDeps
): RunLoggingState {
  // -------------------------------------------------------------------------
  // Computed
  // -------------------------------------------------------------------------

  const profileId = computed(() => config.machineId.value)

  const planOut = computed(() => ({
    moves: deps.moves.value,
    stats: deps.stats.value
  }))

  // -------------------------------------------------------------------------
  // Methods
  // -------------------------------------------------------------------------

  async function logCurrentRun(actualSeconds?: number) {
    if (!planOut.value?.moves?.length) {
      await deps.plan()
    }

    try {
      const segs = planOut.value.moves.map((m: any, i: number) => ({
        idx: i,
        code: m.code,
        x: m.x,
        y: m.y,
        len_mm: m._len_mm || 0,
        limit: m.meta?.limit || null,
        slowdown: m.meta?.slowdown ?? null,
        trochoid: !!m.meta?.trochoid,
        radius_mm: m.meta?.radius_mm ?? null,
        feed_f: m.f ?? null
      }))

      const run = {
        job_name: 'pocket',
        machine_id: profileId.value || 'Mach4_Router_4x8',
        material_id: deps.materialId.value || 'maple_hard',
        tool_d: config.toolD.value,
        stepover: config.stepoverPct.value / 100,
        stepdown: config.stepdown.value,
        post_id: null,
        feed_xy: config.feedXY.value || undefined,
        rpm: undefined,
        est_time_s: planOut.value.stats?.time_s_jerk ?? planOut.value.stats?.time_s_classic ?? null,
        act_time_s: actualSeconds ?? null,
        notes: null
      }

      const r = await api('/api/cam/logs/write', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ run, segments: segs })
      })

      if (!r.ok) {
        throw new Error(await r.text())
      }

      const data = await r.json()

      // Live learn: compute session factor if actual time provided
      const est = planOut.value.stats?.time_s_jerk ?? planOut.value.stats?.time_s_classic
      if (actualSeconds && est) {
        const f = deps.computeLiveLearnFactor(est, actualSeconds)
        if (f) {
          deps.sessionOverrideFactor.value = f
          deps.liveLearnApplied.value = true
          console.info(`Live learn: session feed scale set to ×${f}`)
        }
      }

      alert(
        `Logged run ${data.run_id} successfully` +
        (deps.sessionOverrideFactor.value ? `\nLive learn: ×${deps.sessionOverrideFactor.value}` : '')
      )
    } catch (e: any) {
      alert('Log run failed: ' + e)
    }
  }

  async function trainOverrides() {
    if (!profileId.value) {
      alert('Select machine profile first')
      return
    }

    try {
      const r = await api('/api/cam/learn/train', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ machine_profile: profileId.value, r_min_mm: 5 })
      })

      if (!r.ok) {
        throw new Error(await r.text())
      }

      const out = await r.json()
      alert(
        `Learned rules for ${out.machine_profile || out.machine_id}:\n` +
        JSON.stringify(out.rules, null, 2)
      )
    } catch (e: any) {
      alert('Train overrides failed: ' + e)
    }
  }

  // -------------------------------------------------------------------------
  // Return
  // -------------------------------------------------------------------------

  return {
    logCurrentRun,
    trainOverrides,
  }
}

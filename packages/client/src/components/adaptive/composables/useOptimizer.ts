/**
 * Composable for M.2 What-If Optimizer functionality.
 * Handles parameter grid search, recommendations, and settings comparison.
 */
import { ref, reactive, type Ref } from 'vue'
import { api } from '@/services/apiBase'
import type { Move } from './useToolpathRenderer'

// ============================================================================
// Types
// ============================================================================

export interface OptimizerConfig {
  // From usePocketSettings
  toolD: Ref<number>
  stepoverPct: Ref<number>
  stepdown: Ref<number>
  feedXY: Ref<number>
  units: Ref<'mm' | 'inch'>
  cornerRadiusMin: Ref<number>
  slowdownFeedPct: Ref<number>
  margin: Ref<number>
  strategy: Ref<'Spiral' | 'Lanes'>
  climb: Ref<boolean>

  // Trochoid/jerk settings
  useTrochoids: Ref<boolean>
  trochoidRadius: Ref<number>
  trochoidPitch: Ref<number>
  jerkAware: Ref<boolean>
  machineAccel: Ref<number>
  machineJerk: Ref<number>
  cornerTol: Ref<number>

  // Post & machine
  postId: Ref<string>
  machineId: Ref<string>

  // Job name
  jobName: Ref<string>
}

export interface OptimizerDeps {
  // From usePocketPlanning
  moves: Ref<Move[]>
  loops: Ref<{ pts: number[][] }[]>
  plan: () => Promise<void>

  // From useAdaptiveFeedPresets
  buildAdaptiveOverride: () => any
}

export interface CompareData {
  baselineNc: string
  optNc: string
  tb: number
  topt: number
}

export interface OptimizerState {
  // Optimizer bounds
  optFeedLo: Ref<number>
  optFeedHi: Ref<number>
  optStpLo: Ref<number>
  optStpHi: Ref<number>
  optRpmLo: Ref<number>
  optRpmHi: Ref<number>
  optFlutes: Ref<number>
  optChip: Ref<number>
  optGridF: Ref<number>
  optGridS: Ref<number>
  optOut: Ref<any>

  // Chipload enforcement
  enforceChip: Ref<boolean>
  chipTol: Ref<number>

  // Compare modal
  compareSettingsOpen: Ref<boolean>
  compareData: CompareData

  // Methods
  runWhatIf: () => Promise<void>
  applyRecommendation: () => void
  openCompareSettings: () => Promise<void>
}

// ============================================================================
// Composable
// ============================================================================

export function useOptimizer(
  config: OptimizerConfig,
  deps: OptimizerDeps
): OptimizerState {
  // -------------------------------------------------------------------------
  // State
  // -------------------------------------------------------------------------

  // Optimizer bounds
  const optFeedLo = ref(600)
  const optFeedHi = ref(9000)
  const optStpLo = ref(0.25)
  const optStpHi = ref(0.85)
  const optRpmLo = ref(8000)
  const optRpmHi = ref(24000)
  const optFlutes = ref(2)
  const optChip = ref(0.05)
  const optGridF = ref(6)
  const optGridS = ref(6)
  const optOut = ref<any>(null)

  // Chipload enforcement
  const enforceChip = ref(true)
  const chipTol = ref(0.02)

  // Compare modal
  const compareSettingsOpen = ref(false)
  const compareData = reactive<CompareData>({
    baselineNc: '',
    optNc: '',
    tb: 0,
    topt: 0
  })

  // -------------------------------------------------------------------------
  // Methods
  // -------------------------------------------------------------------------

  async function runWhatIf() {
    // Ensure we have planned moves
    if (!deps.moves.value?.length) {
      await deps.plan()
    }

    if (!deps.moves.value?.length) {
      alert('No moves available. Plan a pocket first.')
      return
    }

    if (!config.machineId.value) {
      alert('Select a machine profile first.')
      return
    }

    try {
      const body: Record<string, any> = {
        moves: deps.moves.value,
        machine_profile_id: config.machineId.value,
        z_total: -config.stepdown.value,
        stepdown: config.stepdown.value,
        safe_z: 5,
        bounds: {
          feed: [optFeedLo.value, optFeedHi.value],
          stepover: [optStpLo.value, optStpHi.value],
          rpm: [optRpmLo.value, optRpmHi.value]
        },
        tool: {
          flutes: optFlutes.value,
          chipload_target_mm: optChip.value
        },
        grid: [optGridF.value, optGridS.value]
      }

      // Add chipload enforcement tolerance if enabled
      if (enforceChip.value) {
        body.tolerance_chip_mm = chipTol.value
      }

      const r = await api('/api/cam/opt/what_if', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      })

      if (!r.ok) {
        const err = await r.text()
        throw new Error(err)
      }

      optOut.value = await r.json()
    } catch (e) {
      console.error('What-if optimization failed:', e)
      alert('Optimization failed: ' + e)
    }
  }

  function applyRecommendation() {
    if (!optOut.value?.opt?.best) {
      return
    }

    const b = optOut.value.opt.best

    // Apply stepover (best.stepover is 0..1, UI expects %)
    config.stepoverPct.value = Math.round(b.stepover * 100)

    // Apply feed (update the feed_xy ref)
    config.feedXY.value = Math.round(b.feed_mm_min)

    // Note: RPM can be displayed or used in spindle control later
    alert(
      `Applied: Feed ${b.feed_mm_min} mm/min, Stepover ${(b.stepover * 100).toFixed(1)}%\n` +
      `Recommended RPM: ${b.rpm}\nRe-plan to see updated toolpath.`
    )
  }

  async function openCompareSettings() {
    try {
      if (!optOut.value?.opt?.best) {
        alert('Run What-If optimizer first')
        return
      }

      // Build baseline request body (current UI settings)
      const baseBody: any = {
        loops: deps.loops.value,
        units: config.units.value,
        tool_d: config.toolD.value,
        stepover: config.stepoverPct.value / 100.0,
        stepdown: config.stepdown.value,
        corner_radius_min: config.cornerRadiusMin.value,
        target_stepover: config.stepoverPct.value / 100.0,
        slowdown_feed_pct: config.slowdownFeedPct.value,
        margin: config.margin.value,
        strategy: config.strategy.value,
        smoothing: 0.8,
        climb: config.climb.value,
        feed_xy: config.feedXY.value,
        safe_z: 5,
        z_rough: -config.stepdown.value,
        post_id: config.postId.value,
        use_trochoids: config.useTrochoids.value,
        trochoid_radius: config.trochoidRadius.value,
        trochoid_pitch: config.trochoidPitch.value,
        jerk_aware: config.jerkAware.value,
        machine_feed_xy: config.feedXY.value,
        machine_rapid: 3000.0,
        machine_accel: config.machineAccel.value,
        machine_jerk: config.machineJerk.value,
        corner_tol_mm: config.cornerTol.value,
        adaptive_feed_override: deps.buildAdaptiveOverride(),
        job_name: config.jobName.value || undefined
      }

      // Build recommendation request body (apply optimizer results)
      const best = optOut.value.opt.best
      const recBody: any = {
        ...baseBody,
        stepover: best.stepover,
        feed_xy: best.feed_mm_min,
        target_stepover: best.stepover
      }

      // Fetch baseline NC and plan
      const [baselineNc, baselinePlan] = await Promise.all([
        api('/api/cam/pocket/adaptive/gcode', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(baseBody)
        }).then(r => r.text()),
        api('/api/cam/pocket/adaptive/plan', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(baseBody)
        }).then(r => r.json())
      ])

      // Fetch recommendation NC and plan
      const [optNc, optPlan] = await Promise.all([
        api('/api/cam/pocket/adaptive/gcode', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(recBody)
        }).then(r => r.text()),
        api('/api/cam/pocket/adaptive/plan', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(recBody)
        }).then(r => r.json())
      ])

      // Populate compare data
      compareData.baselineNc = baselineNc
      compareData.optNc = optNc
      compareData.tb = baselinePlan.stats?.time_s_jerk || baselinePlan.stats?.time_s_classic || 0
      compareData.topt = optPlan.stats?.time_s_jerk || optPlan.stats?.time_s_classic || 0

      // Open modal
      compareSettingsOpen.value = true
    } catch (e: any) {
      alert('Compare settings failed: ' + e)
    }
  }

  // -------------------------------------------------------------------------
  // Return
  // -------------------------------------------------------------------------

  return {
    // State
    optFeedLo,
    optFeedHi,
    optStpLo,
    optStpHi,
    optRpmLo,
    optRpmHi,
    optFlutes,
    optChip,
    optGridF,
    optGridS,
    optOut,
    enforceChip,
    chipTol,
    compareSettingsOpen,
    compareData,

    // Methods
    runWhatIf,
    applyRecommendation,
    openCompareSettings,
  }
}

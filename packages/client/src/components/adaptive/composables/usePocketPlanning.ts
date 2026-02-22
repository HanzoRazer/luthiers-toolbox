/**
 * Composable for Adaptive Pocket planning and export operations.
 * Extracted from AdaptivePocketLab.vue
 *
 * Handles: plan(), previewNc(), exportProgram(), batchExport()
 */
import { ref, type Ref, type ComputedRef } from 'vue'
import { api } from '@/services/apiBase'
// Re-use types from other composables to avoid duplicate exports
import type { Move, Overlay } from './useToolpathRenderer'

// ============================================================================
// Types
// ============================================================================

/** Stats returned from the planning API - allows arbitrary fields */
export interface PocketStats {
  time_s_classic?: number
  time_s_jerk?: number
  total_length_mm?: number
  [key: string]: unknown  // Allow additional API fields
}

export interface Loop {
  pts: number[][]
}

export interface PocketPlanningConfig {
  // From usePocketSettings
  toolD: Ref<number>
  stepoverPct: Ref<number>
  stepdown: Ref<number>
  margin: Ref<number>
  strategy: Ref<'Spiral' | 'Lanes'>
  cornerRadiusMin: Ref<number>
  slowdownFeedPct: Ref<number>
  climb: Ref<boolean>
  feedXY: Ref<number>
  units: Ref<'mm' | 'inch'>

  // Local trochoid/jerk settings
  useTrochoids: Ref<boolean>
  trochoidRadius: Ref<number>
  trochoidPitch: Ref<number>
  jerkAware: Ref<boolean>
  machineAccel: Ref<number>
  machineJerk: Ref<number>
  cornerTol: Ref<number>

  // Post processor
  postId: Ref<string>

  // Machine
  machineId: Ref<string>

  // Job name (from useToolpathExport)
  jobName: Ref<string>
}

export interface PocketPlanningDeps {
  // From useAdaptiveFeedPresets
  buildAdaptiveOverride: () => any

  // From useLiveLearning
  patchBodyWithSessionOverride: (body: any) => any

  // From useToolpathExport
  ncText: Ref<string>
  ncOpen: Ref<boolean>
  selectedModes: () => string[]

  // From useToolpathRenderer - shared ref for overlays
  overlays: Ref<Overlay[]>

  // Callback to redraw canvas after planning
  onPlanComplete?: () => void
}

// ============================================================================
// Composable
// ============================================================================

export function usePocketPlanning(
  config: PocketPlanningConfig,
  deps: PocketPlanningDeps
) {
  // -------------------------------------------------------------------------
  // Local State
  // -------------------------------------------------------------------------

  // Demo outer rectangle - can be replaced with real geometry from upload
  const loops = ref<Loop[]>([
    { pts: [[0, 0], [100, 0], [100, 60], [0, 60]] }
  ])

  const moves = ref<Move[]>([])
  const stats = ref<PocketStats | null>(null)
  // Note: overlays is injected via deps (owned by useToolpathRenderer)

  // -------------------------------------------------------------------------
  // Helper: Build base export body
  // -------------------------------------------------------------------------

  function buildBaseExportBody() {
    return {
      loops: loops.value,
      units: config.units.value,
      tool_d: config.toolD.value,
      stepover: config.stepoverPct.value / 100.0,
      stepdown: config.stepdown.value,
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
      machine_feed_xy: 1200,
      machine_rapid: 3000,
      machine_accel: config.machineAccel.value,
      machine_jerk: config.machineJerk.value,
      corner_tol_mm: config.cornerTol.value,
    }
  }

  // -------------------------------------------------------------------------
  // API: Plan pocket
  // -------------------------------------------------------------------------

  async function plan() {
    const baseBody = {
      loops: loops.value,
      units: config.units.value,
      tool_d: config.toolD.value,
      stepover: config.stepoverPct.value / 100.0,
      stepdown: config.stepdown.value,
      margin: config.margin.value,
      strategy: config.strategy.value,
      smoothing: 0.8,
      climb: config.climb.value,
      feed_xy: config.feedXY.value,
      safe_z: 5,
      z_rough: -config.stepdown.value,
      corner_radius_min: config.cornerRadiusMin.value,
      target_stepover: config.stepoverPct.value / 100.0,
      slowdown_feed_pct: config.slowdownFeedPct.value,
      // L.3 parameters
      use_trochoids: config.useTrochoids.value,
      trochoid_radius: config.trochoidRadius.value,
      trochoid_pitch: config.trochoidPitch.value,
      jerk_aware: config.jerkAware.value,
      machine_feed_xy: config.feedXY.value,
      machine_rapid: 3000.0,
      machine_accel: config.machineAccel.value,
      machine_jerk: config.machineJerk.value,
      corner_tol_mm: config.cornerTol.value,
      // M.1 parameters
      machine_profile_id: config.machineId.value || undefined,
    }

    // M.4: Apply session override and learned rules
    const body = deps.patchBodyWithSessionOverride(baseBody)

    try {
      const r = await api('/api/cam/pocket/adaptive/plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      const out = await r.json()
      moves.value = out.moves || []
      stats.value = out.stats || null
      deps.overlays.value = out.overlays || []

      // Callback to redraw canvas
      if (deps.onPlanComplete) {
        deps.onPlanComplete()
      }
    } catch (err) {
      console.error('Plan failed:', err)
      alert('Failed to plan pocket: ' + err)
    }
  }

  // -------------------------------------------------------------------------
  // API: Preview NC (G-code)
  // -------------------------------------------------------------------------

  async function previewNc() {
    const baseBody = {
      loops: loops.value,
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
      // L.3 parameters
      use_trochoids: config.useTrochoids.value,
      trochoid_radius: config.trochoidRadius.value,
      trochoid_pitch: config.trochoidPitch.value,
      jerk_aware: config.jerkAware.value,
      machine_feed_xy: config.feedXY.value,
      machine_rapid: 3000.0,
      machine_accel: config.machineAccel.value,
      machine_jerk: config.machineJerk.value,
      corner_tol_mm: config.cornerTol.value,
      // Adaptive feed override
      adaptive_feed_override: deps.buildAdaptiveOverride(),
    }
    const body = deps.patchBodyWithSessionOverride(baseBody)

    try {
      const r = await api('/api/cam/pocket/adaptive/gcode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      deps.ncText.value = await r.text()
      deps.ncOpen.value = true
    } catch (err) {
      console.error('Preview failed:', err)
      alert('Failed to preview NC: ' + err)
    }
  }

  // -------------------------------------------------------------------------
  // API: Export single program
  // -------------------------------------------------------------------------

  async function exportProgram() {
    const baseBody: any = {
      loops: loops.value,
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
      // L.3 parameters
      use_trochoids: config.useTrochoids.value,
      trochoid_radius: config.trochoidRadius.value,
      trochoid_pitch: config.trochoidPitch.value,
      jerk_aware: config.jerkAware.value,
      machine_feed_xy: config.feedXY.value,
      machine_rapid: 3000.0,
      machine_accel: config.machineAccel.value,
      machine_jerk: config.machineJerk.value,
      corner_tol_mm: config.cornerTol.value,
      // Adaptive feed override
      adaptive_feed_override: deps.buildAdaptiveOverride(),
      // Job name for filename
      job_name: config.jobName.value || undefined,
    }
    const body = deps.patchBodyWithSessionOverride(baseBody)

    try {
      const r = await api('/api/cam/pocket/adaptive/gcode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      const blob = await r.blob()
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)

      // Use job_name if provided, else fallback to strategy_post pattern
      const stem =
        config.jobName.value && config.jobName.value.trim()
          ? config.jobName.value.trim().replace(/\s+/g, '_')
          : `pocket_${config.strategy.value.toLowerCase()}_${config.postId.value.toLowerCase()}`
      a.download = `${stem}.nc`

      a.click()
      URL.revokeObjectURL(a.href)
    } catch (err) {
      console.error('Export failed:', err)
      alert('Failed to export G-code: ' + err)
    }
  }

  // -------------------------------------------------------------------------
  // API: Batch export (multiple modes)
  // -------------------------------------------------------------------------

  async function batchExport() {
    const base = buildBaseExportBody()
    const body: any = {
      ...base,
      post_id: config.postId.value,
      modes: deps.selectedModes(),
      job_name: config.jobName.value || undefined,
    }

    try {
      const r = await api('/api/cam/pocket/adaptive/batch_export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      const blob = await r.blob()
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)

      // Use job_name if provided, else fallback to mode-based name
      const stem =
        config.jobName.value && config.jobName.value.trim()
          ? config.jobName.value.trim().replace(/\s+/g, '_')
          : `ToolBox_MultiMode_${deps.selectedModes().join('-') || 'all'}`
      a.download = `${stem}.zip`

      a.click()
      URL.revokeObjectURL(a.href)
    } catch (err) {
      console.error('Batch export failed:', err)
      alert('Failed to batch export: ' + err)
    }
  }

  // -------------------------------------------------------------------------
  // Return
  // -------------------------------------------------------------------------

  return {
    // State
    loops,
    moves,
    stats,
    // Note: overlays is not returned here - it's managed by deps (useToolpathRenderer)

    // Methods
    buildBaseExportBody,
    plan,
    previewNc,
    exportProgram,
    batchExport,
  }
}

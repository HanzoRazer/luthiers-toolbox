// packages/client/src/instrument-workspace/acoustic/bridge/useBridgeWorkspace.ts
/**
 * useBridgeWorkspace (BRIDGE-002/003/004)
 *
 * Bounded workspace composable for Bridge Lab.
 *
 * This is the template for all future bounded workspaces (Neck Lab, Body Lab, Bracing Lab).
 * Pattern:
 *   1. Load project BridgeState on entry (BRIDGE-002)
 *   2. Edit LOCAL state (never auto-commit)
 *   3. Derive break angle from Geometry Engine API (BRIDGE-004/005)
 *   4. Commit to project on explicit "Apply Bridge Geometry" (BRIDGE-003)
 *
 * Architecture rules:
 *   - No geometry formulas here. All math via /api/cam/bridge/break-angle
 *   - Break angle uses v2 corrected model (Carruth 6° empirical minimum)
 *   - Never writes to project state automatically
 *   - BridgeCalculatorPanel handles DXF/SVG export — this handles project state
 *
 * See docs/PLATFORM_ARCHITECTURE.md — Layer 2 / Bridge Lab.
 * See docs/BRIDGE_BREAK_ANGLE_DERIVATION.md — v2 geometry corrections.
 */

import { ref, computed, watch } from 'vue'
import { api } from '@/services/apiBase'
import { useInstrumentProject } from '@/instrument-workspace/shared-state/useInstrumentProject'
import type { BridgeState } from '@/api/projects'

// ---------------------------------------------------------------------------
// Break angle engine response (mirrors backend BreakAngleResult)
// ---------------------------------------------------------------------------

export interface BreakAngleResult {
  break_angle_deg: number
  rating: 'adequate' | 'too_shallow' | 'too_steep'
  effective_distance_mm: number
  saddle_projection_mm: number
  energy_coupling: 'adequate' | 'inadequate'
  risk_flags: Array<{ code: string; severity: string; message: string }>
  recommendation: string | null
}

// ---------------------------------------------------------------------------
// Local editing state (separate from committed project state)
// ---------------------------------------------------------------------------

export interface BridgeWorkspaceState {
  // Saddle location
  saddle_line_from_nut_mm: number | null
  // String spacing
  string_spread_mm: number
  // Compensation
  compensation_treble_mm: number
  compensation_bass_mm: number
  // Saddle geometry — inputs to break angle engine
  saddle_slot_width_mm: number
  saddle_slot_depth_mm: number
  saddle_projection_mm: number
  pin_to_saddle_center_mm: number
  slot_offset_mm: number
  // Preset ID (informational)
  preset_id: string | null
}

const DEFAULT_STATE: BridgeWorkspaceState = {
  saddle_line_from_nut_mm: null,
  string_spread_mm: 54.0,
  compensation_treble_mm: 2.0,
  compensation_bass_mm: 4.0,
  saddle_slot_width_mm: 3.2,
  saddle_slot_depth_mm: 10.0,
  saddle_projection_mm: 2.5,
  pin_to_saddle_center_mm: 5.5,
  slot_offset_mm: 1.2,
  preset_id: null,
}

// ---------------------------------------------------------------------------
// Composable
// ---------------------------------------------------------------------------

export function useBridgeWorkspace() {
  const {
    bridgeState,
    spec,
    isSaving,
    saveError,
    commitBridgeState,
    markDirty,
    isLoaded,
  } = useInstrumentProject()

  // --- Local editing buffer ---
  const local = ref<BridgeWorkspaceState>({ ...DEFAULT_STATE })
  const isDirty = ref(false)

  // --- Break angle derived state ---
  const breakAngleResult = ref<BreakAngleResult | null>(null)
  const isComputingAngle = ref(false)
  const angleError = ref<string | null>(null)

  // --- Load project state into local buffer on entry (BRIDGE-002) ---
  watch(isLoaded, (loaded) => {
    if (loaded) syncFromProject()
  }, { immediate: true })

  watch(bridgeState, (bs) => {
    if (bs && !isDirty.value) syncFromProject()
  })

  function syncFromProject(): void {
    const bs = bridgeState.value
    if (bs) {
      local.value = {
        saddle_line_from_nut_mm:   bs.saddle_line_from_nut_mm ?? null,
        string_spread_mm:          bs.string_spread_mm,
        compensation_treble_mm:    bs.compensation_treble_mm,
        compensation_bass_mm:      bs.compensation_bass_mm,
        saddle_slot_width_mm:      bs.saddle_slot_width_mm,
        saddle_slot_depth_mm:      bs.saddle_slot_depth_mm,
        saddle_projection_mm:      bs.saddle_projection_mm,
        pin_to_saddle_center_mm:   bs.pin_to_saddle_center_mm,
        slot_offset_mm:            bs.slot_offset_mm,
        preset_id:                 bs.preset_id ?? null,
      }
    } else if (spec.value) {
      // Seed saddle line from scale length when no bridge state exists yet
      const avgComp = 3.0  // typical average compensation mm
      local.value = {
        ...DEFAULT_STATE,
        saddle_line_from_nut_mm: spec.value.scale_length_mm + avgComp,
      }
    }
    isDirty.value = false
    // Compute break angle for loaded values
    computeBreakAngle()
  }

  // --- Update a single field ---
  function update<K extends keyof BridgeWorkspaceState>(
    field: K,
    value: BridgeWorkspaceState[K],
  ): void {
    local.value = { ...local.value, [field]: value }
    isDirty.value = true
    markDirty()
  }

  // Batch update (used when preset is applied)
  function applyPreset(preset: Partial<BridgeWorkspaceState>): void {
    local.value = { ...local.value, ...preset }
    isDirty.value = true
    markDirty()
  }

  // --- Derive break angle from Geometry Engine (BRIDGE-004/005) ---
  // Only the three inputs that matter for break angle are sent.
  // No formula inline here — engine only.
  async function computeBreakAngle(): Promise<void> {
    const { saddle_projection_mm, pin_to_saddle_center_mm, slot_offset_mm, saddle_slot_depth_mm } = local.value
    if (!saddle_projection_mm || !pin_to_saddle_center_mm) return

    isComputingAngle.value = true
    angleError.value = null

    try {
      const response = await api('/api/cam/bridge/break-angle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          pin_to_saddle_center_mm,
          slot_offset_mm,
          saddle_projection_mm,
          saddle_slot_depth_mm,
          saddle_blank_height_mm: 12.0,  // standard bone blank
        }),
      })
      if (!response.ok) throw new Error(`Break angle API: HTTP ${response.status}`)
      breakAngleResult.value = await response.json()
    } catch (err) {
      angleError.value = err instanceof Error ? err.message : 'Break angle calculation failed'
      breakAngleResult.value = null
    } finally {
      isComputingAngle.value = false
    }
  }

  // Auto-recompute when geometry inputs change (debounced via watch)
  let _angleTimer: ReturnType<typeof setTimeout> | null = null
  watch(
    () => [
      local.value.saddle_projection_mm,
      local.value.pin_to_saddle_center_mm,
      local.value.slot_offset_mm,
      local.value.saddle_slot_depth_mm,
    ],
    () => {
      if (_angleTimer) clearTimeout(_angleTimer)
      _angleTimer = setTimeout(computeBreakAngle, 400)
    },
  )

  // --- Commit to project on explicit user action (BRIDGE-003) ---
  async function applyBridgeGeometry(): Promise<boolean> {
    const state: BridgeState = {
      saddle_line_from_nut_mm:   local.value.saddle_line_from_nut_mm,
      string_spread_mm:          local.value.string_spread_mm,
      compensation_treble_mm:    local.value.compensation_treble_mm,
      compensation_bass_mm:      local.value.compensation_bass_mm,
      saddle_slot_width_mm:      local.value.saddle_slot_width_mm,
      saddle_slot_depth_mm:      local.value.saddle_slot_depth_mm,
      saddle_projection_mm:      local.value.saddle_projection_mm,
      pin_to_saddle_center_mm:   local.value.pin_to_saddle_center_mm,
      slot_offset_mm:            local.value.slot_offset_mm,
      preset_id:                 local.value.preset_id,
    }
    const ok = await commitBridgeState(state)
    if (ok) isDirty.value = false
    return ok
  }

  // --- Reset to last committed state ---
  function discardChanges(): void {
    syncFromProject()
  }

  // --- Computed helpers for UI ---

  const breakAngleDeg = computed(() => breakAngleResult.value?.break_angle_deg ?? null)
  const breakAngleRating = computed(() => breakAngleResult.value?.rating ?? null)
  const breakAngleIsAdequate = computed(() => breakAngleRating.value === 'adequate')
  const breakAngleColor = computed(() => {
    switch (breakAngleRating.value) {
      case 'adequate':    return '#1D9E75'
      case 'too_shallow': return '#D85A30'
      case 'too_steep':   return '#BA7517'
      default:            return '#6B7280'
    }
  })

  const saddleLineLabel = computed(() => {
    const line = local.value.saddle_line_from_nut_mm
    if (!line) return '—'
    const inches = (line / 25.4).toFixed(3)
    return `${line.toFixed(1)} mm (${inches}")`
  })

  const effectiveDistanceMm = computed(() =>
    local.value.pin_to_saddle_center_mm - local.value.slot_offset_mm
  )

  const hasProjectBridgeState = computed(() => bridgeState.value !== null)
  const hasSaddleLine = computed(() => local.value.saddle_line_from_nut_mm !== null)

  return {
    // Local editing state (use update() to change)
    local,
    isDirty,

    // Break angle engine result
    breakAngleResult,
    breakAngleDeg,
    breakAngleRating,
    breakAngleIsAdequate,
    breakAngleColor,
    isComputingAngle,
    angleError,

    // Computed helpers
    saddleLineLabel,
    effectiveDistanceMm,
    hasProjectBridgeState,
    hasSaddleLine,

    // Saving state (from useInstrumentProject)
    isSaving,
    saveError,

    // Actions
    update,
    applyPreset,
    computeBreakAngle,
    applyBridgeGeometry,   // BRIDGE-003: explicit commit
    discardChanges,
  }
}

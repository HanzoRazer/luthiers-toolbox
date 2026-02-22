/**
 * ArtStudioRelief preset management composable.
 */
import type { Ref } from 'vue'
import type { PipelineOp } from '@/api/pipeline'
import type { ReliefPresetConfig } from './artStudioReliefTypes'

// ============================================================================
// Types
// ============================================================================

export interface LocalPresetPayload {
  name: string
  config: {
    scallop_height?: number
    stepdown?: number
    min_floor_thickness?: number
    high_load_index?: number
  }
}

export interface ArtStudioReliefPresetsReturn {
  loadReliefPresetFromStorage: (showToast?: boolean) => void
  applyLocalPreset: (payload: LocalPresetPayload) => void
  reloadLabPreset: () => void
}

// ============================================================================
// Composable
// ============================================================================

export function useArtStudioReliefPresets(
  activePresetName: Ref<string | null>,
  activePresetConfig: Ref<ReliefPresetConfig | null>,
  reliefOps: PipelineOp[]
): ArtStudioReliefPresetsReturn {
  /**
   * Load preset from localStorage.
   */
  function loadReliefPresetFromStorage(showToast = false): void {
    try {
      const raw = localStorage.getItem('relief_artstudio_default_preset')
      if (!raw) {
        if (showToast) {
          alert('No Lab preset has been promoted yet.')
        }
        return
      }
      const parsed = JSON.parse(raw)
      if (!parsed || typeof parsed !== 'object') return

      activePresetConfig.value = parsed
      activePresetName.value = parsed.name || null

      // Apply finishing defaults to reliefOps finishing input
      const finishOp = reliefOps.find((op) => op.id === 'relief_finish')
      if (finishOp && (finishOp as any).input) {
        const input = (finishOp as any).input
        if (parsed.finishing?.scallop_height != null) {
          input.scallop_height = parsed.finishing.scallop_height
        }
        if (parsed.finishing?.stepdown != null) {
          input.stepdown = parsed.finishing.stepdown
        }
        if (parsed.finishing?.use_dynamic_scallop != null) {
          input.use_dynamic_scallop = parsed.finishing.use_dynamic_scallop
        }
        if (parsed.finishing?.tool_d != null) {
          input.tool_d = parsed.finishing.tool_d
        }
      }

      if (showToast) {
        alert(`Loaded preset "${activePresetName.value}" from Relief Lab.`)
      }
    } catch (err) {
      console.warn('Failed to load Art Studio relief preset:', err)
      if (showToast) {
        alert('Failed to load Lab preset from localStorage.')
      }
    }
  }

  /**
   * Apply a local preset configuration.
   */
  function applyLocalPreset(payload: LocalPresetPayload): void {
    const cfg = payload.config || {}
    activePresetName.value = `Local:${payload.name}`
    activePresetConfig.value = {
      name: activePresetName.value,
      finishing: {
        scallop_height: cfg.scallop_height,
        stepdown: cfg.stepdown,
        use_dynamic_scallop: true
      },
      sim_thresholds: {
        min_floor_thickness: cfg.min_floor_thickness,
        high_load_index: cfg.high_load_index,
        med_load_index: 1.0
      }
    }

    // Immediately apply to the finishing op
    const finishOp = reliefOps.find((op) => op.id === 'relief_finish')
    if (finishOp && (finishOp as any).input) {
      const input = (finishOp as any).input
      if (cfg.scallop_height != null) {
        input.scallop_height = cfg.scallop_height
      }
      if (cfg.stepdown != null) {
        input.stepdown = cfg.stepdown
      }
      input.use_dynamic_scallop = true
    }
  }

  /**
   * Reload Lab preset from storage.
   */
  function reloadLabPreset(): void {
    loadReliefPresetFromStorage(true)
  }

  return {
    loadReliefPresetFromStorage,
    applyLocalPreset,
    reloadLabPreset
  }
}

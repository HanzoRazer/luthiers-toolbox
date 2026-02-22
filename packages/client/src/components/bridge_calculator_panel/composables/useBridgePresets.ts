/**
 * BridgeCalculatorPanel preset handling composable.
 */
import type { Ref, ComputedRef } from 'vue'
import { api } from '@/services/apiBase'
import type { UnitMode, UiFieldKey, FamilyPreset, AdjustmentPreset } from './bridgeCalculatorTypes'

export interface BridgePresetsReturn {
  loadPresets: () => Promise<void>
  applyFamilyPreset: (id: string) => void
  applyPresets: () => void
}

export function useBridgePresets(
  familyPresets: Ref<FamilyPreset[]>,
  gaugePresets: Ref<AdjustmentPreset[]>,
  actionPresets: Ref<AdjustmentPreset[]>,
  presetFamily: Ref<string>,
  gaugePresetId: Ref<string>,
  actionPresetId: Ref<string>,
  presetsLoading: Ref<boolean>,
  presetError: Ref<string | null>,
  unitMode: ComputedRef<UnitMode>,
  ui: Record<UiFieldKey, number>
): BridgePresetsReturn {
  /**
   * Convert mm to inches.
   */
  function mmToIn(value: number): number {
    return value / 25.4
  }

  /**
   * Load presets from API (silently fall back to defaults on error).
   */
  async function loadPresets(): Promise<void> {
    try {
      presetsLoading.value = true
      presetError.value = null
      const response = await api('/api/cam/bridge/presets')
      if (response.ok) {
        const data = await response.json()
        if (Array.isArray(data?.families) && data.families.length) {
          familyPresets.value = data.families
        }
        if (Array.isArray(data?.gauges) && data.gauges.length) {
          gaugePresets.value = data.gauges
        }
        if (Array.isArray(data?.actions) && data.actions.length) {
          actionPresets.value = data.actions
        }
      }
      // Non-2xx response silently uses fallbacks
    } catch {
      console.debug('Bridge presets API unavailable, using fallback presets')
    } finally {
      presetsLoading.value = false
    }
  }

  /**
   * Apply a family preset to the UI.
   */
  function applyFamilyPreset(id: string): void {
    const preset = familyPresets.value.find((f) => f.id === id) ?? familyPresets.value[0]
    if (!preset) return
    if (unitMode.value === 'mm') {
      ui.scale = preset.scaleLength
      ui.spread = preset.stringSpread
      ui.compTreble = preset.compTreble
      ui.compBass = preset.compBass
      ui.slotWidth = preset.slotWidth
      ui.slotLength = preset.slotLength
    } else {
      ui.scale = mmToIn(preset.scaleLength)
      ui.spread = mmToIn(preset.stringSpread)
      ui.compTreble = mmToIn(preset.compTreble)
      ui.compBass = mmToIn(preset.compBass)
      ui.slotWidth = mmToIn(preset.slotWidth)
      ui.slotLength = mmToIn(preset.slotLength)
    }
  }

  /**
   * Get adjustment values from a preset.
   */
  function getPresetAdjust(presets: AdjustmentPreset[], id: string): { treble: number; bass: number } {
    const preset = presets.find((p) => p.id === id)
    return {
      treble: preset?.trebleAdjust ?? preset?.compAdjust ?? 0,
      bass: preset?.bassAdjust ?? preset?.compAdjust ?? 0
    }
  }

  /**
   * Apply all selected presets (family + gauge + action).
   */
  function applyPresets(): void {
    applyFamilyPreset(presetFamily.value)
    const gauge = getPresetAdjust(gaugePresets.value, gaugePresetId.value)
    const action = getPresetAdjust(actionPresets.value, actionPresetId.value)
    const trebleDelta = gauge.treble + action.treble
    const bassDelta = gauge.bass + action.bass
    const factor = unitMode.value === 'mm' ? 1 : 1 / 25.4
    ui.compTreble += trebleDelta * factor
    ui.compBass += bassDelta * factor
  }

  return {
    loadPresets,
    applyFamilyPreset,
    applyPresets
  }
}

/**
 * ArtStudioInlay preset handling composable.
 */
import type { Ref } from 'vue'
import { listInlayPresets, getInlayPreset } from '@/api/art-studio'
import type { InlayPatternType, InlayPresetInfo } from './artStudioInlayTypes'

export interface InlayPresetsReturn {
  loadPresets: () => Promise<void>
  applyPreset: () => Promise<void>
}

export function useInlayPresets(
  presets: Ref<InlayPresetInfo[]>,
  selectedPreset: Ref<string | null>,
  error: Ref<string | null>,
  // Form refs to update when applying preset
  patternType: Ref<InlayPatternType>,
  selectedFrets: Ref<number[]>,
  scaleLength: Ref<number>,
  fretboardWidthNut: Ref<number>,
  fretboardWidthBody: Ref<number>,
  numFrets: Ref<number>,
  inlaySize: Ref<number>,
  doubleAt12: Ref<boolean>,
  doubleSpacing: Ref<number>,
  // Callback to refresh preview after applying
  onPresetApplied?: () => void
): InlayPresetsReturn {
  /**
   * Load available presets from API.
   */
  async function loadPresets(): Promise<void> {
    try {
      presets.value = await listInlayPresets()
    } catch (e: any) {
      console.warn('Failed to load presets:', e)
    }
  }

  /**
   * Apply selected preset to form.
   */
  async function applyPreset(): Promise<void> {
    if (!selectedPreset.value) return
    try {
      const preset = await getInlayPreset(selectedPreset.value)
      patternType.value = preset.pattern_type
      selectedFrets.value = [...preset.fret_positions]
      scaleLength.value = preset.scale_length_mm
      fretboardWidthNut.value = preset.fretboard_width_nut_mm
      fretboardWidthBody.value = preset.fretboard_width_body_mm
      numFrets.value = preset.num_frets
      inlaySize.value = preset.inlay_size_mm
      doubleAt12.value = preset.double_at_12
      doubleSpacing.value = preset.double_spacing_mm
      onPresetApplied?.()
    } catch (e: any) {
      error.value = `Failed to load preset: ${e.message}`
    }
  }

  return {
    loadPresets,
    applyPreset
  }
}

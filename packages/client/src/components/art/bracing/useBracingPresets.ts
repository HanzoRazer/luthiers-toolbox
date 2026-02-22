/**
 * Composable for bracing preset management.
 */
import { ref, type Ref } from 'vue'
import { listBracingPresets, COMMON_WOODS, type BracingPresetInfo, type BraceProfileType } from '@/api/art-studio'

// ============================================================================
// Types
// ============================================================================

export interface BracingPresetsState {
  presets: Ref<BracingPresetInfo[]>
  loadPresets: () => Promise<void>
  applyPreset: (preset: BracingPresetInfo) => void
}

// ============================================================================
// Composable
// ============================================================================

export function useBracingPresets(
  profileType: Ref<BraceProfileType>,
  density: Ref<number>
): BracingPresetsState {
  const presets = ref<BracingPresetInfo[]>([])

  async function loadPresets(): Promise<void> {
    try {
      presets.value = await listBracingPresets()
    } catch (e: any) {
      console.warn('Failed to load presets:', e)
    }
  }

  function applyPreset(preset: BracingPresetInfo): void {
    profileType.value = preset.profile_type
    const wood = COMMON_WOODS.find((w) =>
      w.name.toLowerCase().includes(preset.typical_wood.toLowerCase())
    )
    if (wood) density.value = wood.density
  }

  return {
    presets,
    loadPresets,
    applyPreset
  }
}

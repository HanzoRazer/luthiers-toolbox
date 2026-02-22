/**
 * Composable for single brace preview calculations.
 */
import { ref, computed, type Ref, type ComputedRef } from 'vue'
import {
  previewBracing,
  COMMON_WOODS,
  type BracingPreviewResponse,
  type BraceProfileType
} from '@/api/art-studio'
import {
  DEFAULT_WIDTH,
  DEFAULT_HEIGHT,
  DEFAULT_LENGTH,
  DEFAULT_DENSITY
} from './bracingConstants'

// ============================================================================
// Types
// ============================================================================

export interface SingleBraceState {
  profileType: Ref<BraceProfileType>
  width: Ref<number>
  height: Ref<number>
  length: Ref<number>
  density: Ref<number>
  singleResult: Ref<BracingPreviewResponse | null>
  selectedWood: ComputedRef<string | null>
  setSelectedWood: (name: string | null) => void
  previewSingle: () => Promise<void>
}

// ============================================================================
// Composable
// ============================================================================

export function useSingleBrace(
  loading: Ref<boolean>,
  error: Ref<string | null>
): SingleBraceState {
  const profileType = ref<BraceProfileType>('parabolic')
  const width = ref(DEFAULT_WIDTH)
  const height = ref(DEFAULT_HEIGHT)
  const length = ref(DEFAULT_LENGTH)
  const density = ref(DEFAULT_DENSITY)
  const singleResult = ref<BracingPreviewResponse | null>(null)

  const selectedWood = computed(() => {
    const found = COMMON_WOODS.find(
      (w) => Math.abs(w.density - density.value) < 5
    )
    return found?.name || null
  })

  function setSelectedWood(name: string | null) {
    const found = COMMON_WOODS.find((w) => w.name === name)
    if (found) density.value = found.density
  }

  async function previewSingle(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      singleResult.value = await previewBracing({
        profile_type: profileType.value,
        width_mm: width.value,
        height_mm: height.value,
        length_mm: length.value,
        density_kg_m3: density.value
      })
    } catch (e: any) {
      error.value = e.message || 'Preview failed'
    } finally {
      loading.value = false
    }
  }

  return {
    profileType,
    width,
    height,
    length,
    density,
    singleResult,
    selectedWood,
    setSelectedWood,
    previewSingle
  }
}

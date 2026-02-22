/**
 * Composable for AI image generation.
 */
import type { Ref, ComputedRef } from 'vue'
import { generateImages, type VisionAsset, type ProviderName } from '../api/visionApi'

// ============================================================================
// Types
// ============================================================================

export interface ImageGenerationReturn {
  doGenerate: () => Promise<void>
}

// ============================================================================
// Composable
// ============================================================================

export function useImageGeneration(
  prompt: Ref<string>,
  provider: Ref<ProviderName>,
  numImages: Ref<number>,
  size: Ref<string>,
  quality: Ref<string>,
  generatedAssets: Ref<VisionAsset[]>,
  isGenerating: Ref<boolean>,
  canGenerate: ComputedRef<boolean>,
  selectedRunId: Ref<string | null>,
  refreshVariants: () => Promise<void>,
  toastOk: (msg: string) => void,
  toastErr: (msg: string) => void
): ImageGenerationReturn {
  async function doGenerate(): Promise<void> {
    if (!canGenerate.value) return

    isGenerating.value = true
    try {
      const req = {
        prompt: prompt.value,
        provider: provider.value,
        num_images: numImages.value,
        size: size.value,
        quality: quality.value
      }
      const res = await generateImages(req as any)
      generatedAssets.value = res.assets ?? []
      toastOk(`Generated ${generatedAssets.value.length} asset(s).`)

      // If a run is selected, refresh so state-aware buttons work immediately
      if (selectedRunId.value) await refreshVariants()
    } catch (e: any) {
      toastErr(e?.message || 'Generate failed.')
    } finally {
      isGenerating.value = false
    }
  }

  return {
    doGenerate
  }
}

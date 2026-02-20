/**
 * Composable for image generation via Vision API.
 * Extracted from VisionAttachToRunWidget.vue
 */
import { ref, computed, type Ref, type ComputedRef } from 'vue'
import {
  generateImages,
  type VisionAsset,
  type VisionGenerateRequest,
  type ProviderName,
} from '../api/visionApi'

// =============================================================================
// Types
// =============================================================================

export interface GenerationParams {
  prompt: string
  provider: ProviderName
  numImages: number
  size: string
  quality: string
}

export interface VisionGenerationState {
  /** Current prompt text */
  prompt: Ref<string>
  /** Number of images to generate */
  numImages: Ref<number>
  /** Image size (e.g., "1024x1024") */
  size: Ref<string>
  /** Quality setting (standard, hd) */
  quality: Ref<string>
  /** Generated assets */
  generatedAssets: Ref<VisionAsset[]>
  /** SHA of selected asset */
  selectedAssetSha: Ref<string | null>
  /** Whether generation is in progress */
  isGenerating: Ref<boolean>
  /** Whether generation can proceed */
  canGenerate: ComputedRef<boolean>
  /** Currently selected asset object */
  selectedAsset: ComputedRef<VisionAsset | null>
  /** Generate images */
  generate: () => Promise<{ success: boolean; count?: number; error?: string }>
  /** Select an asset by SHA */
  selectAsset: (sha: string) => void
  /** Clear all generated assets */
  clearAssets: () => void
}

// =============================================================================
// Composable
// =============================================================================

export function useVisionGeneration(
  getProvider: () => ProviderName,
  initialPrompt?: string
): VisionGenerationState {
  const prompt = ref(initialPrompt || '')
  const numImages = ref(1)
  const size = ref('1024x1024')
  const quality = ref('standard')
  const generatedAssets = ref<VisionAsset[]>([])
  const selectedAssetSha = ref<string | null>(null)
  const isGenerating = ref(false)

  // ===========================================================================
  // Computed
  // ===========================================================================

  const canGenerate = computed(() => {
    return prompt.value.trim().length > 0 && !isGenerating.value
  })

  const selectedAsset = computed(() => {
    if (!selectedAssetSha.value) return null
    return generatedAssets.value.find((a) => a.sha256 === selectedAssetSha.value) || null
  })

  // ===========================================================================
  // Methods
  // ===========================================================================

  async function generate(): Promise<{ success: boolean; count?: number; error?: string }> {
    if (!canGenerate.value) {
      return { success: false, error: 'Cannot generate' }
    }

    isGenerating.value = true

    try {
      const request: VisionGenerateRequest = {
        prompt: prompt.value.trim(),
        provider: getProvider(),
        num_images: numImages.value,
        size: size.value,
        quality: quality.value,
      }

      const res = await generateImages(request)
      generatedAssets.value = [...res.assets, ...generatedAssets.value]

      // Auto-select first generated asset
      if (res.assets.length > 0) {
        selectedAssetSha.value = res.assets[0].sha256
      }

      return { success: true, count: res.assets.length }
    } catch (e: any) {
      return { success: false, error: e.message || 'Failed to generate images' }
    } finally {
      isGenerating.value = false
    }
  }

  function selectAsset(sha: string) {
    selectedAssetSha.value = sha
  }

  function clearAssets() {
    generatedAssets.value = []
    selectedAssetSha.value = null
  }

  return {
    prompt,
    numImages,
    size,
    quality,
    generatedAssets,
    selectedAssetSha,
    isGenerating,
    canGenerate,
    selectedAsset,
    generate,
    selectAsset,
    clearAssets,
  }
}

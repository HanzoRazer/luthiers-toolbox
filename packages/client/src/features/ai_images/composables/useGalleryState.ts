/**
 * Composable for AI Image Gallery state management.
 */
import { ref, computed, type Ref, type ComputedRef } from 'vue'
import type {
  VisionAsset,
  ProviderName,
  RunSummary,
  AdvisoryVariantSummary,
  BusyState
} from './galleryTypes'

// ============================================================================
// Types
// ============================================================================

export interface GalleryStateReturn {
  // Generation params
  prompt: Ref<string>
  provider: Ref<ProviderName>
  numImages: Ref<number>
  size: Ref<string>
  quality: Ref<string>

  // Assets and runs
  generatedAssets: Ref<VisionAsset[]>
  selectedRunId: Ref<string | null>
  runs: Ref<RunSummary[]>
  providers: Ref<any[]>

  // Loading states
  isGenerating: Ref<boolean>
  isAttaching: Ref<string | null>
  isPromoting: Ref<string | null>
  error: Ref<string | null>
  success: Ref<string | null>

  // Review panel
  openReviewFor: Ref<string | null>

  // Variant tracking
  variantById: Ref<Record<string, AdvisoryVariantSummary>>
  advisoryIdByAssetSha: Ref<Record<string, string>>
  busyByAdvisoryId: Ref<Record<string, BusyState>>
  lastAttachedRunId: Ref<string | null>

  // Computed
  canGenerate: ComputedRef<boolean>
}

// ============================================================================
// Composable
// ============================================================================

export function useGalleryState(): GalleryStateReturn {
  // Generation params
  const prompt = ref('')
  const provider = ref<ProviderName>('openai')
  const numImages = ref(2)
  const size = ref('1024x1024')
  const quality = ref('standard')

  // Assets and runs
  const generatedAssets = ref<VisionAsset[]>([])
  const selectedRunId = ref<string | null>(null)
  const runs = ref<RunSummary[]>([])
  const providers = ref<any[]>([])

  // Loading states
  const isGenerating = ref(false)
  const isAttaching = ref<string | null>(null)
  const isPromoting = ref<string | null>(null)
  const error = ref<string | null>(null)
  const success = ref<string | null>(null)

  // Review panel
  const openReviewFor = ref<string | null>(null)

  // Variant tracking
  const variantById = ref<Record<string, AdvisoryVariantSummary>>({})
  const advisoryIdByAssetSha = ref<Record<string, string>>({})
  const busyByAdvisoryId = ref<Record<string, BusyState>>({})
  const lastAttachedRunId = ref<string | null>(null)

  // Computed
  const canGenerate = computed(() => prompt.value.trim().length > 0 && !isGenerating.value)

  return {
    prompt,
    provider,
    numImages,
    size,
    quality,
    generatedAssets,
    selectedRunId,
    runs,
    providers,
    isGenerating,
    isAttaching,
    isPromoting,
    error,
    success,
    openReviewFor,
    variantById,
    advisoryIdByAssetSha,
    busyByAdvisoryId,
    lastAttachedRunId,
    canGenerate
  }
}
